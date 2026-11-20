"""The common data format: one parquet file per release, value columns plus code columns.

See planning/missing_codes_design.md and STANDARD.md §8.

For each variable, the value column (`abany`) holds valid answers and is null
wherever the answer is missing or unresolved. When a variable has any codes,
a code column (`abany__code`) holds them as text, exactly as written in the
metadata (".d", "98", "."), and is null where the answer is valid.

A dataset repo supplies only a reader that returns a "raw" frame: every cell is
either a value or, for the publisher's own missing tokens (Stata's ".d", "."),
a `Code`. Ordinary values that the metadata lists as missing or unresolved
(the ANES's 98) are recognized here, from the release's records, by type and
value: a number matches only a numeric code, a string only a string code.

The file's metadata records which code texts were `Code` tokens, so rebuild()
can restore every cell exactly without guessing.
"""

import hashlib
import json
import math
import warnings

try:
    import numpy as np
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError as e:                               # the `data` extra isn't installed
    raise ImportError(
        f"pdt.data reads and writes the common-format parquet files, and needs pandas, numpy "
        f"and pyarrow ({e.name} is missing). Install them with: "
        f"pip install \"publicdatatoolkit[data]\"") from e

from . import __version__
from .common_format import CODE_SUFFIX, ROW, as_float, code_text, is_number  # noqa: F401  (re-exported)

META_KEY = b"pdt"
REQUIRED_IDENTITY = ("dataset", "release", "metadata_sha256")
INT64_MAX = 2**63 - 1


class Code(str):
    """A publisher's missing-value token that isn't an ordinary value, e.g. Stata's '.d'."""


class MetadataMismatch(UserWarning):
    """The metadata given doesn't match the metadata the data file was built with."""


class UnresolvedCodes(UserWarning):
    """A variable has codes whose meaning the documentation doesn't give, or isn't documented."""


class InferredClassification(UserWarning):
    """Codes were classified (as missing, and by type) only because of an `inferred` correction (STANDARD.md §5.3)."""


# ------------------------------------------------------------------ codes


def nonvalid_codes(record):
    """({float value: text} for numeric codes, {text} for string codes), missing and unresolved only."""
    numeric, strings = {}, set()
    for v in record.get("values", []):
        if v["kind"] == "valid":
            continue
        if isinstance(v["code"], str):
            strings.add(v["code"])
        else:
            numeric[float(v["code"])] = code_text(v["code"])
    return numeric, strings


def is_null(cell):
    if cell is None or cell is pd.NA:
        return True
    return isinstance(cell, float) and math.isnan(cell)


# ------------------------------------------------------------------ split


def _value_dtype(name, record, values):
    kind = (record or {}).get("storage_type")
    present = [v for v in values if not is_null(v)]
    if kind == "integer":
        if not all(is_number(v) and as_float(v).is_integer() for v in present):
            raise ValueError(f"{name}: storage_type is integer, but some values aren't whole numbers")
        return "Int64" if all(abs(as_float(v)) <= INT64_MAX for v in present) else "Float64"
    if kind == "float":
        return "Float64"
    if kind == "string":
        return "string"
    if not present:
        return "object"
    if all(isinstance(v, (bool, np.bool_)) for v in present):
        return "boolean"
    if all(is_number(v) for v in present):
        whole = all(as_float(v).is_integer() and abs(as_float(v)) <= INT64_MAX for v in present)
        return "Int64" if whole else "Float64"
    if all(isinstance(v, str) for v in present):
        return "string"
    raise ValueError(f"{name}: values of mixed types; give its record a storage_type")


def split(raw, records=None):
    """Split a raw frame into value and code columns.

    records: {name: variable record} for the release. Variables without a record
    get code columns only for `Code` cells. The result's attrs["pdt_tokens"]
    lists, per variable, the code texts that were `Code` tokens.
    """
    records = records or {}
    out = {ROW: pd.Series(range(len(raw)), index=raw.index, dtype="int64")}
    tokens = {}
    for name in raw.columns:
        if name.endswith(CODE_SUFFIX) or name == ROW:
            raise ValueError(f"variable name {name!r} is reserved by the common format")
        numeric, strings = nonvalid_codes(records.get(name, {}))
        cells = raw[name].tolist()
        codes, values, token_texts, value_texts = [], [], set(), set()
        for cell in cells:
            code = None
            if isinstance(cell, Code):
                code = str(cell)
                token_texts.add(code)
            elif is_number(cell) and not is_null(cell) and as_float(cell) in numeric:
                code = numeric[as_float(cell)]
                value_texts.add(code)
            elif isinstance(cell, str) and cell in strings:
                code = cell
                value_texts.add(code)
            codes.append(code)
            values.append(None if code is not None or is_null(cell) else cell)
        both = token_texts & value_texts
        if both:
            raise ValueError(f"{name}: code text {sorted(both)} comes from both a publisher token and an "
                             "ordinary value; the common format can't tell them apart")
        out[name] = pd.Series(values, index=raw.index, dtype=object).astype(
            _value_dtype(name, records.get(name), values))
        if any(c is not None for c in codes):
            out[name + CODE_SUFFIX] = pd.Series(codes, index=raw.index, dtype=object).astype("category")
        if token_texts:
            tokens[name] = sorted(token_texts)
    table = pd.DataFrame(out, index=raw.index)
    table.attrs["pdt_tokens"] = tokens
    return table


# ---------------------------------------------------------------- rebuild


def rebuild(table, records=None, tokens=None):
    """Rebuild the raw frame from value and code columns (the inverse of split).

    tokens: {name: [code texts that were Code tokens]}, from the file's metadata
    (identity_of(path)["tokens"]) or table.attrs; read from table.attrs if omitted.
    """
    records = records or {}
    tokens = tokens if tokens is not None else table.attrs.get("pdt_tokens", {})
    raw = {}
    for name in table.columns:
        if name == ROW or name.endswith(CODE_SUFFIX):
            continue
        values = [None if is_null(v) else v for v in table[name].tolist()]
        if name + CODE_SUFFIX not in table:
            raw[name] = pd.Series(values, index=table.index, dtype=object)
            continue
        numeric = {code_text(v["code"]): v["code"] for v in records.get(name, {}).get("values", [])
                   if not isinstance(v["code"], str)}
        token_texts = set(tokens.get(name, []))

        def from_code(text):
            if text in token_texts:
                return Code(text)
            if text in numeric:
                return numeric[text]
            return str(text)

        codes = table[name + CODE_SUFFIX].astype(object).tolist()
        cells = [v if is_null(c) else from_code(c) for v, c in zip(values, codes)]
        raw[name] = pd.Series(cells, index=table.index, dtype=object)
    return pd.DataFrame(raw, index=table.index)


def same_cells(a, b):
    """True if two raw frames hold the same cells, Codes included.

    Numbers are compared by value (98 == 98.0) and all kinds of null (None,
    NaN, pd.NA) count as the same, as they do in parquet. A Code and a plain
    string with the same text are different cells.
    """
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        return False

    def norm(cell):
        if isinstance(cell, Code):
            return ("code", str(cell))
        if is_null(cell):
            return ("null",)
        if isinstance(cell, (bool, np.bool_)):
            return ("bool", bool(cell))
        if is_number(cell):
            return ("num", as_float(cell))
        return ("val", cell)

    return all([norm(x) for x in a[c].tolist()] == [norm(x) for x in b[c].tolist()] for c in a.columns)


# ------------------------------------------------------------ file identity


def metadata_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(table, path, identity):
    """Write a split table as parquet, with identity and the token lists in the file metadata.

    identity must include dataset, release and metadata_sha256 (of the
    variables.jsonl the table was split with).
    """
    missing = [k for k in REQUIRED_IDENTITY if not identity.get(k)]
    if missing:
        raise ValueError(f"identity is missing {missing}")
    arrow = pa.Table.from_pandas(table, preserve_index=False)
    meta = dict(arrow.schema.metadata or {})
    meta[META_KEY] = json.dumps({**identity, "tokens": table.attrs.get("pdt_tokens", {}),
                                 "pdt_version": __version__}).encode()
    pq.write_table(arrow.replace_schema_metadata(meta), path)


def identity_of(path):
    meta = pq.read_schema(path).metadata or {}
    return json.loads(meta[META_KEY]) if META_KEY in meta else {}


def read(path, columns=None):
    """Read a common-format file; the token lists go in attrs so rebuild() works."""
    table = pd.read_parquet(path, columns=columns)
    table.attrs["pdt_tokens"] = identity_of(path).get("tokens", {})
    return table


def check_identity(path, dataset, release, variables_sha256):
    """Warn if the file was built for another dataset, another release, or other metadata."""
    ident = identity_of(path)
    if not ident:
        warnings.warn(f"{path} has no PublicDataToolkit identity", MetadataMismatch)
    elif ident.get("dataset") != dataset or ident.get("release") != release:
        warnings.warn(f"{path} is {ident.get('dataset')} release {ident.get('release')}, "
                      f"not {dataset} release {release}", MetadataMismatch)
    elif not variables_sha256 or ident.get("metadata_sha256") != variables_sha256:
        warnings.warn(f"{path} was built with different metadata for release {release}; "
                      "codes may be classified differently", MetadataMismatch)
    return ident


# ------------------------------------------------------------------ recode


def _same(a, b):
    return a == b or (isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b))


def _wave_key(w):
    """A wave as text, so 2021, 2021.0 and "2021" match."""
    if is_null(w):
        return None
    return code_text(w) if is_number(w) else str(w)


def recode(table, record, unresolved=None, inferred=None, not_asked_from_availability=False, waves=None,
           **by_type):
    """Values with missing codes replaced by type, e.g. recode(t, rec, dk="DK", refused="DK").

    A code is replaced only when every one of its missing types is given, with
    the same replacement: GSS ".m" ("dk, na, iap") is replaced only if dk,
    no_answer and inap are all given and agree, because ".m" alone doesn't say
    which applies. Other codes stay null.

    not_asked_from_availability (off by default): a missing code whose types include
    not_asked, such as YRBSS's blank ("no_answer, uncodeable, not_asked"), is split by the
    record's `availability`. In a row whose wave isn't in it, the question wasn't asked, so
    the code counts as not_asked only; in a row whose wave is, it counts as its other types.
    `waves` gives each row's wave: a column of table, or a sequence as long as it. Rows
    with no wave keep all the code's types. The result's attrs["not_asked_split"] counts
    the cells read each way: {"not_asked": n outside availability, "other": n inside}.

    Unresolved codes, and codes the record doesn't list, are never replaced by
    type: pass unresolved= to handle them; otherwise they stay null and a
    warning says how many there are.

    inferred: {code text: [correction ids]} for codes whose kind and types come
    from an `inferred` correction (record should be the corrected record). When
    any of them occur, an InferredClassification warning says how many cells,
    which corrections, and what was done with them (STANDARD.md §5.3).
    """
    name = record["name"]
    values = [None if is_null(v) else v for v in table[name].tolist()]
    code_col = name + CODE_SUFFIX
    if code_col not in table:
        return pd.Series(values, index=table.index, dtype=object)
    documented = {code_text(v["code"]): v for v in record.get("values", []) if v["kind"] != "valid"}

    def replace(types):
        """(True, replacement) if every type is given, with one replacement; else (False, None)."""
        if types and all(t in by_type for t in types):
            given = [by_type[t] for t in types]
            if all(_same(g, given[0]) for g in given):
                return True, given[0]
        return False, None

    replacement = {}
    split = {}       # code text -> (outside availability, inside it): each (replaced?, replacement)
    for text, v in documented.items():
        if v["kind"] == "unresolved":
            continue
        types = v.get("missing_types", [])
        ok, value = replace(types)
        if ok:
            replacement[text] = value
        if not_asked_from_availability and "not_asked" in types:
            split[text] = (replace(["not_asked"]), replace([t for t in types if t != "not_asked"] or types))
    row_waves = None
    if not_asked_from_availability:
        if waves is None:
            raise ValueError(f"{name}: not_asked_from_availability needs each row's wave (waves=)")
        row_waves = (table[waves] if isinstance(waves, str) else pd.Series(list(waves), index=table.index)).tolist()
        if len(row_waves) != len(table):
            raise ValueError(f"{name}: waves has {len(row_waves)} entries for {len(table)} rows")
        available = {_wave_key(a["wave"]) for a in record.get("availability", [])}
    codes = table[code_col].astype(object).tolist()
    unknown = [c for c in codes if isinstance(c, str)
               and (c not in documented or documented[c]["kind"] == "unresolved")]
    if unknown and unresolved is None:
        undocumented = sorted({c for c in unknown if c not in documented})
        detail = f"; not in its metadata: {undocumented}" if undocumented else ""
        warnings.warn(f"{name}: {len(unknown)} values have unresolved or undocumented codes, left null{detail}",
                      UnresolvedCodes)
    cells = []
    counts = {"not_asked": 0, "other": 0}
    for i, (v, c) in enumerate(zip(values, codes)):
        if not isinstance(c, str):
            cells.append(v)
        elif c in split and _wave_key(row_waves[i]) is not None:
            outside = _wave_key(row_waves[i]) not in available
            counts["not_asked" if outside else "other"] += 1
            ok, value = split[c][0 if outside else 1]
            cells.append(value if ok else None)
        elif c in replacement:
            cells.append(replacement[c])
        elif (c not in documented or documented[c]["kind"] == "unresolved") and unresolved is not None:
            cells.append(unresolved)
        else:
            cells.append(None)
    for text, ids in sorted((inferred or {}).items()):
        n = sum(1 for c in codes if c == text)
        if not n or text not in documented:
            continue
        v = documented[text]
        what = (f"replaced with {replacement[text]!r}" if text in replacement
                else f"left null as {', '.join(v.get('missing_types', [])) or v['kind']}")
        warnings.warn(f"{name}: code {text} ({n} values) is {v['kind']} only because of inferred correction(s) "
                      f"{', '.join(ids)}; {what}", InferredClassification)
    out = pd.Series(cells, index=table.index, dtype=object)
    if not_asked_from_availability:
        out.attrs["not_asked_split"] = counts
    return out

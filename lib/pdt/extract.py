"""Build an extract from a release in the common format (STANDARD.md §8).

The user names the variables, the waves, and what to do with each missing type;
the extract has no analysis choices of its own. A dataset repo's
`scripts/extract.py` calls `main`; code can call `extract`.

    extract(root, release, variables, table=None, missing=None, unresolved=None,
            waves=None, codes=False) -> Extract(frame, report)

- Reads `data/processed/<dataset>-<release>[-<table>].parquet` (`make data` writes it)
  and warns if it was built from other records or other corrections.
- Every variable is recoded with `pdt.data.recode`, using the corrected record
  (variables.jsonl with corrections.jsonl applied, as the file was split).
  `missing` maps missing types to replacements ({"dk": "DK", "refused": "DK"});
  a missing value whose types aren't all given stays null. Unresolved codes stay
  null unless `unresolved` is given.
- `waves` keeps the rows whose wave is listed, using the dataset's wave column
  (`dimensions.wave.column` in dataset.yaml: GSS `year`, ANES `VCF0004`). A
  dataset whose waves are its releases (the NSFG) has no wave column; pick the
  release instead.
- `codes=True` keeps each variable's code column (`<name>__code`) beside it.

The report says what the extract relied on, and in particular every inferred
correction (STANDARD.md §5.3): a code classified as missing only because of one
(ANES 2024 -1 -> inap), and a code made a valid value by one (ANES VCF0878's
2024 code 2). Warnings from recode go into the report as well as to the caller.
"""

import argparse
import re
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from . import data
from .check import Repo
from .release import PROCESSED, file_name, variables_path
from .search import apply_corrections


@dataclass
class Extract:
    frame: pd.DataFrame
    report: list = field(default_factory=list)


def _find(records, name):
    """The record for name: exact, or ignoring case when that's unambiguous."""
    if name in records:
        return name
    hits = [n for n in records if n.lower() == name.lower()]
    if len(hits) == 1:
        return hits[0]
    raise KeyError(f"no variable {name!r}" + (f"; did you mean one of {hits}?" if hits else ""))


def corrected(repo, release, table):
    """{name: corrected record}, and {name: [applied corrections]} with id, field and confidence."""
    records, applied = {}, {}
    for r in repo.tables[release][table]:
        records[r["name"]], applied[r["name"]] = apply_corrections(r, release, table, repo.corrections)
    return records, applied


def inferred_codes(record, applied):
    """{code text: [correction ids]} for codes whose entry in `values` an inferred correction set."""
    out = {}
    for a in applied:
        m = re.fullmatch(r"/values/(\d+)(?:/.*)?", a["field"])
        if a["confidence"] == "inferred" and m and int(m.group(1)) < len(record.get("values", [])):
            text = data.code_text(record["values"][int(m.group(1))]["code"])
            out.setdefault(text, []).append(a["id"])
    return out


def _typed(series, like):
    """Back to the value column's dtype when the recoded column holds only nulls and numbers
    (a text replacement, such as "DK", keeps it as objects)."""
    present = [x for x in series.tolist() if not data.is_null(x)]
    if not all(data.is_number(x) for x in present):
        return series
    try:
        if str(like.dtype) in {"Int64", "int64"}:
            whole = all(data.as_float(x).is_integer() for x in present)
            return series.astype("Int64" if whole else "Float64")
        if str(like.dtype) in {"Float64", "float64"}:
            return series.astype("Float64")
        return series.astype(like.dtype)
    except (TypeError, ValueError):
        return series


def extract(root, release, variables, table=None, missing=None, unresolved=None, waves=None, codes=False):
    """The extract asked for, and a report of what it relied on (see the module docstring)."""
    root = Path(root)
    repo = Repo.load(root)
    if release not in repo.tables:
        raise KeyError(f"no release {release!r}; releases: {list(repo.tables)}")
    if table not in repo.tables[release]:
        raise KeyError(f"release {release} has tables {[t for t in repo.tables[release] if t]}; name one with table=")
    missing = dict(missing or {})
    report = []
    path = root / PROCESSED / file_name(repo.dataset["id"], release, table)
    if not path.exists():
        raise FileNotFoundError(f"{path} doesn't exist; run `make data` in {root}")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ident = data.check_identity(path, repo.dataset["id"], release,
                                    data.metadata_sha256(variables_path(root, release, table)))
        corr = root / "metadata" / "corrections.jsonl"
        if ident and ident.get("corrections_sha256") != (data.metadata_sha256(corr) if corr.exists() else None):
            warnings.warn(f"{path.name} was built with other corrections; rebuild it with `make data`",
                          data.MetadataMismatch)

        records, applied = corrected(repo, release, table)
        names = [_find(records, n) for n in variables]
        wave_col = (repo.dataset.get("dimensions", {}).get("wave") or {}).get("column")
        if waves is not None and not wave_col:
            raise ValueError(f"{repo.dataset['id']} has no wave column; its waves are its releases")
        wave_name = _find(records, wave_col) if waves is not None else None
        cols = list(dict.fromkeys(names + ([wave_name] if wave_name else [])))
        read_cols = [c for n in cols for c in (n, n + data.CODE_SUFFIX)]
        available = set(pq.read_schema(path).names)
        frame = data.read(path, columns=[c for c in read_cols if c in available])
        missing_cols = [n for n in cols if n not in available]
        if missing_cols:
            raise KeyError(f"{path.name} has no column(s) {missing_cols}; rebuild it with `make data`")

        if waves is not None:
            wanted = {float(w) for w in waves}
            keep = frame[wave_name].map(lambda w: not data.is_null(w) and float(w) in wanted)
            frame = frame[keep.astype(bool)]
            present = sorted({data.as_float(w) for w in frame[wave_name] if not data.is_null(w)})
            shown = ", ".join(str(int(w)) if w.is_integer() else str(w) for w in present)
            report.append(f"waves: {len(frame):,} rows, {wave_name} in {len(present)} of the {len(set(waves))} "
                          f"asked for: {shown}")

        out = {}
        for name in names:
            rec, done = records[name], applied[name]
            series = data.recode(frame, rec, unresolved=unresolved, inferred=inferred_codes(rec, done), **missing)
            out[name] = _typed(series, frame[name])
            if codes and name + data.CODE_SUFFIX in frame:
                out[name + data.CODE_SUFFIX] = frame[name + data.CODE_SUFFIX]
            for a in done:
                if a["confidence"] == "inferred" and not re.fullmatch(r"/values/\d+(?:/.*)?", a["field"]):
                    report.append(f"{name}: {a['field']} comes from inferred correction {a['id']}")
            for a in done:
                m = re.fullmatch(r"/values/(\d+)", a["field"])
                if a["confidence"] == "inferred" and m:
                    v = rec["values"][int(m.group(1))]
                    if v["kind"] == "valid":
                        n = int((frame[name].map(lambda x, c=v["code"]: not data.is_null(x) and x == c)).sum())
                        report.append(f"{name}: value {data.code_text(v['code'])} ({n} values) is valid, "
                                      f"labeled {v.get('label')!r}, only because of inferred correction {a['id']}")
    for w in caught:
        report.append(f"{w.category.__name__}: {w.message}")
        warnings.warn_explicit(w.message, w.category, w.filename, w.lineno)

    result = pd.DataFrame(out, index=frame.index).reset_index(drop=True)
    report.insert(0, f"{repo.dataset['id']} {release}" + (f"/{table}" if table else "")
                  + f": {len(result):,} rows, {len(names)} variables, from {path.name}")
    if missing:
        report.insert(1, "missing types replaced: " + ", ".join(f"{k}={v!r}" for k, v in missing.items())
                      + "; every other missing value is null")
    else:
        report.insert(1, "every missing value is null")
    return Extract(result, report)


# ------------------------------------------------------------------- CLI


def _value(text):
    """A replacement from the command line: null, a number, or text."""
    if text.lower() in {"null", "none", "na", "nan"}:
        return None
    try:
        number = float(text)
        return int(number) if number.is_integer() else number
    except ValueError:
        return text


def _waves(text):
    out = []
    for part in text.split(","):
        if re.fullmatch(r"\d+-\d+", part.strip()):
            lo, hi = map(int, part.split("-"))
            out += list(range(lo, hi + 1))
        else:
            out.append(_value(part.strip()))
    return out


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="extract.py",
        description="Write an extract from a release in the common format (run `make data` first).")
    p.add_argument("root", help="the dataset repo")
    p.add_argument("--release", required=True)
    p.add_argument("--table", help="the table, for a release with several")
    p.add_argument("--vars", required=True, help="comma-separated variable names, or @file with one per line")
    p.add_argument("--missing", nargs="*", default=[], metavar="TYPE=VALUE",
                   help="replace a missing type, e.g. dk=DK refused=DK inap=null; others become null")
    p.add_argument("--unresolved", help="a value for unresolved and undocumented codes (default: null)")
    p.add_argument("--waves", help="e.g. 2000-2024 or 1972,1974; uses the dataset's wave column")
    p.add_argument("--codes", action="store_true", help="keep each variable's code column")
    p.add_argument("--out", required=True, help="output file: .parquet or .csv")
    args = p.parse_args(argv)

    names = (Path(args.vars[1:]).read_text().split() if args.vars.startswith("@")
             else [n.strip() for n in args.vars.split(",") if n.strip()])
    missing = {}
    for item in args.missing:
        key, _, value = item.partition("=")
        missing[key.strip()] = _value(value)
    result = extract(args.root, args.release, names, table=args.table, missing=missing,
                     unresolved=_value(args.unresolved) if args.unresolved is not None else None,
                     waves=_waves(args.waves) if args.waves else None, codes=args.codes)
    out = Path(args.out)
    if out.suffix == ".csv":
        result.frame.to_csv(out, index=False)
    else:
        result.frame.to_parquet(out, index=False)
    for line in result.report:
        print(line, file=sys.stderr)
    print(f"wrote {out}", file=sys.stderr)
    return 0

"""Readers for common publisher formats, returning raw frames for `pdt.release`.

A raw frame holds, in every cell, either a value or a `pdt.data.Code` for the
publisher's own missing tokens (STANDARD.md §8). Each reader reads only the
columns asked for, since the files are often much wider than a repo's records.

    read_stata(path, columns)              Stata .dta or .dta.gz (pyreadstat, only the columns asked for);
                                           extended missing (.d, .i, .) -> Code
    read_sas(path, columns)                SAS .sas7bdat; system missing -> Code(".")
    read_csv_zip(path, member, columns)    a CSV inside a zip; empty cells stay null
    read_stata_dictionary(dat, dct, columns)   fixed-width text described by a Stata .dct;
                                           a blank numeric field is Stata's missing -> Code(".")
    read_sas_input(dat, input_sas, columns)    fixed-width text laid out by a SAS input program;
                                           `$` columns stay text (blanks too), numeric "." or blank -> Code(".")
    read_sas_xport(path, columns)          SAS transport (.xpt, also inside a zip); from pdt.xport (Task 67)
    read_sav(path, columns, rows=None)     SPSS .sav (pyreadstat); user-missing codes stay numbers,
                                           system missing -> Code(".")
"""

import io
import re
import zipfile
from pathlib import Path

import pandas as pd

from .data import Code
from .xport import read_sas_xport  # noqa: E402,F401  (re-exported; Task 67)


def _pick(available, columns, path):
    missing = [c for c in columns if c not in available]
    if missing:
        raise KeyError(f"{path}: no column(s) {missing}")
    return list(columns)


_DECOMPRESSED = {}   # (path, size, mtime) -> uncompressed temporary copy, reused across batches


def _uncompressed(path):
    """A .gz file's uncompressed copy in a temporary directory, made once per file and process
    (pyreadstat can't read compressed files); any other path as it is."""
    import atexit
    import gzip
    import shutil
    import tempfile
    path = Path(path)
    if path.suffix != ".gz":
        return path
    stat = path.stat()
    key = (str(path.resolve()), stat.st_size, stat.st_mtime)
    if key not in _DECOMPRESSED:
        tmp = Path(tempfile.mkdtemp(prefix="pdt-stata-"))
        atexit.register(shutil.rmtree, tmp, True)
        out = tmp / path.stem
        with gzip.open(path, "rb") as src, open(out, "wb") as dst:
            shutil.copyfileobj(src, dst, 1 << 24)
        _DECOMPRESSED[key] = out
    return _DECOMPRESSED[key]


def _read_dta(path, **kwargs):
    """pyreadstat.read_dta, in the file's own encoding, else latin-1 (as pandas falls back)."""
    import pyreadstat
    try:
        return pyreadstat.read_dta(str(path), **kwargs)
    except UnicodeDecodeError:
        return pyreadstat.read_dta(str(path), encoding="latin1", **kwargs)


def read_stata(path, columns):
    """Stata file as a raw frame. Extended missing values (.a-.z) and system missing (.) become Codes.

    pyreadstat reads only the columns asked for, so memory follows the batch, not the file:
    300 of the GSS's 6,943 columns take 0.5 GB (pandas.read_stata parsed the whole file, 2.9 GB).
    The cells are the same as pandas.read_stata(convert_missing=True) gave: numbers in an
    integer storage type are ints, extended missing .x is Code(".x"), system missing is
    Code("."), and string variables keep their text.
    """
    plain = _uncompressed(path)
    _, meta = _read_dta(plain, metadataonly=True)
    columns = _pick(meta.column_names, columns, path)
    frame, meta = _read_dta(plain, usecols=columns, user_missing=True)
    types = meta.readstat_variable_types
    out = {}
    for name in columns:
        kind = types[name]
        numeric = kind in ("int8", "int16", "int32", "float", "double")
        integer = kind.startswith("int")
        cells = []
        for c in frame[name].tolist():
            if numeric and isinstance(c, str):
                c = Code("." + c)                      # extended missing value, e.g. "d" -> .d
            elif numeric and isinstance(c, float) and c != c:
                c = Code(".")                          # system missing
            elif integer and isinstance(c, float):
                c = int(c)                             # read as float only because of missing values
            cells.append(c)
        out[name] = pd.Series(cells, dtype=object)
    return pd.DataFrame(out)


def read_sas(path, columns, encoding="latin-1"):
    """SAS file as a raw frame; SAS's missing value (NaN once read) becomes Code(".")."""
    frame = pd.read_sas(path, format="sas7bdat", encoding=encoding)
    columns = _pick(frame.columns, columns, path)
    frame = frame[columns]
    # Built column by column: DataFrame.where() would turn Code(".") into a plain "." (Task 58,
    # found by purple on the Household Pulse Survey's INCOME).
    return pd.DataFrame({c: pd.Series([Code(".") if v != v else v for v in frame[c].tolist()], dtype=object)
                         for c in columns})


def zip_member(path, pattern):
    """The one member of a zip whose name matches pattern (a regex, case-insensitive)."""
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if re.search(pattern, n, re.IGNORECASE)]
    if len(names) != 1:
        raise KeyError(f"{path}: {len(names)} members match {pattern!r}: {names[:5]}")
    return names[0]


def read_csv_zip(path, member, columns, encoding="latin-1"):
    """A CSV inside a zip as a raw frame. Numbers stay numbers; empty cells are null."""
    with zipfile.ZipFile(path) as z, z.open(member) as f:
        text = io.TextIOWrapper(f, encoding=encoding)
        header = pd.read_csv(text, nrows=0).columns
    columns = _pick(header, columns, f"{path}:{member}")
    with zipfile.ZipFile(path) as z, z.open(member) as f:
        frame = pd.read_csv(io.TextIOWrapper(f, encoding=encoding), usecols=columns,
                            low_memory=False)[columns]
    return frame.astype(object).where(frame.notna(), None)


DCT_LINE = re.compile(r'_column\((\d+)\)\s+(\S+)\s+(\S+)\s+%(\d+)(?:\.\d+)?([a-z])', re.IGNORECASE)


def parse_dct(path):
    """[(name, start (0-based), width, stata type)] from a Stata dictionary's _column lines."""
    out = []
    for line in open(path, encoding="latin-1"):
        m = DCT_LINE.search(line)
        if m:
            out.append((m.group(3), int(m.group(1)) - 1, int(m.group(4)), m.group(2).lower()))
    return out


def _number(text):
    try:
        return int(text)
    except ValueError:
        return float(text)


def read_stata_dictionary(dat, dct, columns, encoding="latin-1"):
    """Fixed-width data described by a Stata .dct, as a raw frame.

    Names match case-insensitively (the NSFG's .dct writes caseid; records may write
    CASEID), and the frame uses the names asked for. Numeric fields are int or float;
    a blank numeric field is Stata's system missing, Code("."). String fields stay text.
    """
    layout = {name.lower(): (start, width, kind) for name, start, width, kind in parse_dct(dct)}
    missing = [c for c in columns if c.lower() not in layout]
    if missing:
        raise KeyError(f"{dct}: no column(s) {missing}")
    specs = [layout[c.lower()] for c in columns]
    frame = pd.read_fwf(dat, colspecs=[(start, start + width) for start, width, _ in specs],
                        names=list(columns), dtype=str, header=None, encoding=encoding,
                        keep_default_na=False, delimiter="\n")
    out = {}
    for name, (_, _, kind) in zip(columns, specs):
        cells = frame[name].tolist()
        if kind.startswith("str"):
            out[name] = pd.Series(cells, dtype=object)
        else:
            out[name] = pd.Series([Code(".") if not c.strip() else _number(c.strip()) for c in cells],
                                  dtype=object)
    return pd.DataFrame(out)


SAS_INPUT_LINE = re.compile(r"^\s*(\w+)\s+(\$)?\s*(\d+)\s*-\s*(\d+)\s*$", re.MULTILINE)
SAS_LABEL_LINE = re.compile(r'^\s*(\w+)\s*=\s*"([^"]*)"\s*$', re.MULTILINE)
SAS_LENGTH_TEXT = re.compile(r"^\s*(\w+)\s+\$\s*\d+\s*$", re.MULTILINE)


def _sas_statement(text, keyword):
    """The body of the statement that starts with `keyword` alone on a line, up to its ';'."""
    m = re.search(rf"^\s*{keyword}\s*$(.*?);", text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else ""


def parse_sas_input(path):
    """{name: (start (0-based), end (exclusive), is_text, label or None)} from a SAS input program.

    Reads the column ranges of its `input` statement (`q26 $ 281-281`, `weight 125-134`)
    and the labels of its `label` statement, as CDC's YRBSS and BRFSS programs write them.
    A column is text when the input statement marks it `$`, or when a `length` statement
    does (`CNT $3`), as the OECD's PISA 2012 program does. A label is matched by name, or
    ignoring case when that's unambiguous (PISA 2012 labels `STIDSTD` for input `StIDStd`).
    """
    text = open(path, encoding="latin-1").read()
    labels = dict(SAS_LABEL_LINE.findall(_sas_statement(text, "label")))
    by_upper = {}
    for name, label in labels.items():
        by_upper.setdefault(name.upper(), []).append(label)
    texts = {m.group(1).upper() for m in SAS_LENGTH_TEXT.finditer(_sas_statement(text, "length"))}
    out = {}
    for name, dollar, first, last in SAS_INPUT_LINE.findall(_sas_statement(text, "input")):
        label = labels.get(name)
        if label is None and len(by_upper.get(name.upper(), [])) == 1:
            label = by_upper[name.upper()][0]
        out[name] = (int(first) - 1, int(last), bool(dollar) or name.upper() in texts, label)
    if not out:
        raise ValueError(f"{path}: no column ranges in an input statement")
    return out


def read_sas_input(dat, input_sas, columns, encoding="latin-1"):
    """Fixed-width text laid out by a SAS input program, as a raw frame.

    Names match exactly, as in the program. A character (`$`) column keeps its text
    exactly, blanks included: CDC's formats label " " as "Missing", so " " is a code the
    records list. A numeric column holds int or float; SAS reads "." and a blank field
    as its missing value, and both become Code("."), as in read_sas.
    """
    layout = parse_sas_input(input_sas)
    missing = [c for c in columns if c not in layout]
    if missing:
        raise KeyError(f"{input_sas}: no column(s) {missing}")
    specs = [layout[c] for c in columns]
    frame = pd.read_fwf(dat, colspecs=[(start, end) for start, end, _, _ in specs], names=list(columns),
                        dtype=str, header=None, encoding=encoding, keep_default_na=False, delimiter="\n")
    out = {}
    for name, (_, _, is_text, _) in zip(columns, specs):
        cells = frame[name].tolist()
        if is_text:
            out[name] = pd.Series(cells, dtype=object)
        else:
            out[name] = pd.Series([Code(".") if c.strip() in ("", ".") else _number(c.strip()) for c in cells],
                                  dtype=object)
    return pd.DataFrame(out)


def read_sav(path, columns, rows=None):
    """An SPSS .sav file's columns as a raw frame (needs pyreadstat).

    User-missing values (PISA's 95-99, an SPSS missing range) stay numbers: they're codes
    the records list as missing, with the data file as their origin when nothing else marks
    them. System missing is a token, Code("."). Whole numbers come back as int, others as
    float; string columns as text.

    rows: {column: [values]} keeps only the rows whose column holds one of the values
    (PISA's countries, `data_rows` in dataset.yaml). The column needn't be one asked for.
    """
    import pyreadstat
    rows = rows or {}
    use = list(dict.fromkeys(list(columns) + list(rows)))
    frame, meta = pyreadstat.read_sav(str(path), usecols=use, user_missing=True)
    missing = [c for c in columns if c not in frame.columns]
    if missing:
        raise KeyError(f"{path}: no column(s) {missing}")
    for col, keep in rows.items():
        frame = frame[frame[col].isin(keep)]
    frame = frame.reset_index(drop=True)
    out = {}
    for name in columns:
        if meta.readstat_variable_types.get(name) == "string":
            out[name] = pd.Series(frame[name].tolist(), dtype=object)
        else:
            out[name] = pd.Series([Code(".") if v != v else (int(v) if float(v).is_integer() else float(v))
                                   for v in frame[name].tolist()], dtype=object)
    return pd.DataFrame(out)

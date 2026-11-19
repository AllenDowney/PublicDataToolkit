"""Readers for common publisher formats, returning raw frames for `pdt.release`.

A raw frame holds, in every cell, either a value or a `pdt.data.Code` for the
publisher's own missing tokens (STANDARD.md §8). Each reader reads only the
columns asked for, since the files are often much wider than a repo's records.

    read_stata(path, columns)              Stata .dta or .dta.gz; extended missing (.d, .i, .) -> Code
    read_sas(path, columns)                SAS .sas7bdat; system missing -> Code(".")
    read_csv_zip(path, member, columns)    a CSV inside a zip; empty cells stay null
"""

import io
import re
import zipfile

import pandas as pd

from .data import Code


def _pick(available, columns, path):
    missing = [c for c in columns if c not in available]
    if missing:
        raise KeyError(f"{path}: no column(s) {missing}")
    return list(columns)


def read_stata(path, columns):
    """Stata file as a raw frame. Extended missing values (.a-.z) and system missing (.) become Codes."""
    with pd.io.stata.StataReader(path, compression="infer") as reader:
        available = list(reader.variable_labels())
    columns = _pick(available, columns, path)
    frame = pd.read_stata(path, columns=columns, convert_missing=True, convert_categoricals=False,
                          compression="infer")
    out = {}
    for name in columns:
        cells = frame[name].tolist()
        out[name] = pd.Series(
            [Code(str(c)) if isinstance(c, pd.io.stata.StataMissingValue) else c for c in cells],
            dtype=object)
    return pd.DataFrame(out)


def read_sas(path, columns, encoding="latin-1"):
    """SAS file as a raw frame; SAS's missing value (NaN once read) becomes Code(".")."""
    frame = pd.read_sas(path, format="sas7bdat", encoding=encoding)
    columns = _pick(frame.columns, columns, path)
    frame = frame[columns]
    return frame.astype(object).where(frame.notna(), Code("."))


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

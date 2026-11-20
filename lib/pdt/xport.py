"""SAS transport (XPORT version 5) files, keeping SAS's missing-value codes.

pandas reads XPORT too, but turns every missing value into NaN, so system missing `.`
and the special missing values `.A`-`.Z` and `._` can't be told apart. This reader keeps
them: a missing numeric cell becomes `pdt.data.Code(".")`, `Code(".D")` and so on, as SAS
prints them. Like the readers in `pdt.readers`, it returns a raw frame for `pdt.release`
and decodes only the columns asked for. It reads the file in chunks, straight from a zip
when the publisher ships one (CDC's BRFSS and NHANES), so memory stays near the size of
the columns read.

    read_sas_xport(path, columns, member=None)    a raw frame
    xport_variables(path, member=None)            [{"name", "label", "numeric", "length"}]

`path` is an .xpt file or a zip holding one; `member` is a regular expression picking it
from the zip, by default the only member ending in .xpt (CDC's names can end in a space:
"LLCP2014.XPT "). One member per file; XPORT version 8 isn't supported.
From pdt-brfss's build (Task 30), moved here in Task 67.
"""

import re
import struct
import zipfile

import numpy as np
import pandas as pd

from .data import Code

RECORD = 80
CHUNK_ROWS = 50_000
MISSING_BYTES = {0x2E: "."} | {c: "." + chr(c) for c in range(0x41, 0x5B)} | {0x5F: "._"}


def _open(path, member=None):
    path = str(path)
    if zipfile.is_zipfile(path):
        z = zipfile.ZipFile(path)
        names = [n for n in z.namelist() if re.search(member or r"\.xpt\s*$", n, re.I)]
        if len(names) != 1:
            raise KeyError(f"{path}: {len(names)} members match {member or '.xpt'}: {names[:5]}")
        return z.open(names[0])
    return open(path, "rb")


def _header(f):
    """Read the headers; return the variables as (name, label, numeric, length, position)."""
    if not f.read(3 * RECORD).startswith(b"HEADER RECORD*******LIBRARY HEADER RECORD!!!!!!!"):
        raise ValueError("not a SAS XPORT version 5 file")
    member = f.read(RECORD)
    if b"MEMBER  HEADER RECORD" not in member:
        raise ValueError("no member header")
    namestr_len = int(member[74:78])
    f.read(RECORD)            # descriptor header
    f.read(2 * RECORD)        # member descriptor: name, dates, label
    namestr_hdr = f.read(RECORD)
    if b"NAMESTR HEADER RECORD" not in namestr_hdr:
        raise ValueError("no NAMESTR header")
    nvars = int(namestr_hdr[54:58])
    raw = f.read(nvars * namestr_len)
    f.read((-nvars * namestr_len) % RECORD)
    if b"OBS     HEADER RECORD" not in f.read(RECORD):
        raise ValueError("no OBS header (several members, or XPORT version 8, aren't supported)")
    out = []
    for i in range(nvars):
        ns = raw[i * namestr_len:(i + 1) * namestr_len]
        ntype, _, length = struct.unpack(">hhh", ns[0:6])
        name = ns[8:16].decode("latin-1").strip()
        label = ns[16:56].decode("latin-1").strip()
        position = struct.unpack(">i", ns[84:88])[0]
        out.append((name, label, ntype == 1, length, position))
    return out


def _ibm_floats(cells):
    """(n, length) uint8 cells holding big-endian IBM floats -> (float64 values, missing codes or None)."""
    n, length = cells.shape
    b = np.zeros((n, 8), dtype=np.uint8)
    b[:, :length] = cells
    rest_zero = (b[:, 1:] == 0).all(axis=1)
    first = b[:, 0]
    sign = np.where(first & 0x80, -1.0, 1.0)
    exponent = (first & 0x7F).astype(np.int64) - 64
    mantissa = np.zeros(n)
    for k in range(1, 8):
        mantissa = mantissa * 256.0 + b[:, k]
    values = sign * mantissa / 2.0 ** 56 * np.power(16.0, exponent)
    values[(first == 0) & rest_zero] = 0.0
    codes = np.full(n, None, dtype=object)
    for byte, code in MISSING_BYTES.items():
        codes[rest_zero & (first == byte)] = code
    return values, codes


def read_sas_xport(path, columns, member=None):
    """The columns asked for, as a raw frame: numbers as floats, text as str, missing as Code."""
    with _open(path, member) as f:
        variables = _header(f)
        by_name = {v[0].upper(): v for v in variables}
        absent = [c for c in columns if c.upper() not in by_name]
        if absent:
            raise KeyError(f"{path}: no column(s) {absent}")
        wanted = [by_name[c.upper()] for c in columns]
        row_len = sum(v[3] for v in variables)
        parts = {v[0]: [] for v in wanted}
        # The file is padded with blanks to a whole 80-byte record, which makes whole blank
        # rows when a row is shorter than a record. So the last few rows of a chunk wait for
        # the next one until the end of the file, where trailing blank rows are dropped.
        pad_rows = (RECORD - 1) // row_len
        tail = b""
        while True:
            block = f.read(CHUNK_ROWS * row_len)
            last = not block
            data = tail + block
            nrows = len(data) // row_len
            if not last:
                nrows = max(nrows - pad_rows, 0)
            tail = data[nrows * row_len:]
            rows = np.frombuffer(data[:nrows * row_len], dtype=np.uint8).reshape(nrows, row_len)
            if last:
                blank = pad_rows
                while blank and len(rows) and (rows[-1] == 0x20).all():
                    rows, blank = rows[:-1], blank - 1
            for name, _, numeric, length, pos in wanted:
                cells = rows[:, pos:pos + length]
                if numeric:
                    values, codes = _ibm_floats(cells)
                    col = values.astype(object)
                    has = np.array([c is not None for c in codes], dtype=bool)
                    col[has] = [Code(c) for c in codes[has]]
                else:
                    col = np.array([bytes(r).decode("latin-1").rstrip() for r in cells], dtype=object)
                parts[name].append(col)
            if last:
                break
    return pd.DataFrame({v[0]: np.concatenate(parts[v[0]]) if parts[v[0]] else np.array([], dtype=object)
                         for v in wanted}, columns=[v[0] for v in wanted])


def xport_variables(path, member=None):
    """Every variable in the file, in order: name, label, whether numeric, and length in bytes."""
    with _open(path, member) as f:
        return [{"name": n, "label": lab, "numeric": num, "length": ln} for n, lab, num, ln, _ in _header(f)]

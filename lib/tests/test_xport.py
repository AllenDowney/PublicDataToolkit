"""pdt.xport: SAS transport files, keeping SAS's missing values (Task 67)."""

import math
import zipfile

import numpy as np
import pandas as pd
import pytest

pyreadstat = pytest.importorskip("pyreadstat")

from pdt import xport  # noqa: E402
from pdt.data import Code  # noqa: E402

SENTINELS = {-1111.0: ".A", -2222.0: ".Z", -3333.0: "._"}


def ibm(x):
    """x as an 8-byte big-endian IBM float (the test's own encoder, to find sentinel cells)."""
    if x == 0:
        return bytes(8)
    sign = 0x80 if x < 0 else 0
    m, e = abs(x), 64
    while m >= 1:
        m, e = m / 16, e + 1
    while m < 1 / 16:
        m, e = m * 16, e - 1
    return bytes([sign | e]) + int(m * 2 ** 56).to_bytes(7, "big")


def write(path, frame, labels=None):
    """An XPORT v5 file from frame; NaN is SAS's ".", and SENTINELS become special missing values."""
    pyreadstat.write_xport(frame, str(path), file_format_version=5, column_labels=labels)
    data = path.read_bytes()
    for value, code in SENTINELS.items():
        data = data.replace(ibm(value), code[1].encode() + bytes(7))
    path.write_bytes(data)
    return path


def frame():
    return pd.DataFrame({
        "SEX": [1.0, 2.0, np.nan, 1.0, 2.0, 1.0, 2.0],
        "WT": [2552.12, 0.5, 13.0, -3.25, 0.0, 1e6, 7.0],
        "AGE": [-1111.0, 45.0, -2222.0, 30.0, -3333.0, 60.0, 18.0],
        "NAME": ["ab", "", "c d", "x", "yy", "zzz", "q"],
    })


def test_values_and_missing_codes(tmp_path):
    path = write(tmp_path / "t.xpt", frame(), {"SEX": "Sex of respondent", "WT": "Final weight"})
    got = xport.read_sas_xport(path, ["sex", "WT", "AGE", "NAME"])
    assert list(got.columns) == ["SEX", "WT", "AGE", "NAME"]
    assert got["SEX"].tolist()[:2] == [1.0, 2.0] and got["SEX"][2] == Code(".")
    assert got["WT"].tolist() == pytest.approx(frame()["WT"].tolist())
    assert [str(x) for x in got["AGE"]] == [".A", "45.0", ".Z", "30.0", "._", "60.0", "18.0"]
    assert all(isinstance(got["AGE"][i], Code) for i in (0, 2, 4))
    assert got["NAME"].tolist() == ["ab", "", "c d", "x", "yy", "zzz", "q"]
    # pandas agrees on every value it can represent
    ref = pd.read_sas(path, format="xport", encoding="latin-1")
    assert len(ref) == len(got)
    for col in ("SEX", "WT", "AGE"):
        for mine, theirs in zip(got[col], ref[col]):
            assert (isinstance(mine, Code) and math.isnan(theirs)) or mine == pytest.approx(theirs)
    names = [v["name"] for v in xport.xport_variables(path)]
    assert names == ["SEX", "WT", "AGE", "NAME"]
    assert xport.xport_variables(path)[0]["label"] == "Sex of respondent"


def test_selected_columns_from_a_zip_in_chunks(tmp_path, monkeypatch):
    path = write(tmp_path / "LLCP2014.XPT", frame())
    zpath = tmp_path / "LLCP2014XPT.zip"
    with zipfile.ZipFile(zpath, "w") as z:
        z.write(path, "LLCP2014.XPT ")              # CDC's member name ends in a space
    monkeypatch.setattr(xport, "CHUNK_ROWS", 2)
    got = xport.read_sas_xport(zpath, ["AGE"])
    assert list(got.columns) == ["AGE"] and len(got) == 7
    assert str(got["AGE"][4]) == "._" and got["AGE"][6] == 18.0
    with pytest.raises(KeyError):
        xport.read_sas_xport(zpath, ["NOPE"])
    with pytest.raises(KeyError):
        xport.read_sas_xport(zpath, ["AGE"], member=r"\.csv$")


def test_short_rows_ignore_the_final_padding(tmp_path):
    # One 8-byte column: 3 rows leave 56 blank bytes in the last record, 7 rows' worth.
    path = write(tmp_path / "one.xpt", pd.DataFrame({"X": [1.0, np.nan, 3.0]}))
    got = xport.read_sas_xport(path, ["X"])
    assert len(got) == 3 and got["X"][1] == Code(".")


def test_ibm_encoder_round_trip():
    cells = np.frombuffer(b"".join(ibm(x) for x in (1.0, -2.5, 1e-3, 123456.75)), dtype=np.uint8).reshape(4, 8)
    values, codes = xport._ibm_floats(cells)
    assert values.tolist() == pytest.approx([1.0, -2.5, 1e-3, 123456.75]) and all(c is None for c in codes)

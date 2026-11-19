"""Tests for the common data format (pdt.data)."""

import warnings

import pandas as pd
import pytest

import numpy as np

from pdt.data import (CODE_SUFFIX, Code, MetadataMismatch, UnresolvedCodes, check_identity, identity_of,
                      read, rebuild, recode, same_cells, split, write)

ORIGIN = {"origin": "publisher", "source": "cb"}


def missing(code, label, *types):
    return {"code": code, "label": label, "kind": "missing", "missing_types": list(types), "origin": ORIGIN}


# A small release with every case the design covers:
# - Stata extended missing values (Code(".d")) and system missing (Code("."))
# - a publisher's numeric missing codes (98, 99)
# - a DK-like code the publisher lists as valid (9)
# - an undocumented code, recorded as unresolved (-1)
# - a code with several missing types (".m")
# - a dimension column with missing codes (ballot ".i" before ballots existed)
# - a string variable whose missing code is a string
RECORDS = {
    "year": {"name": "year", "storage_type": "integer"},
    "ballot": {"name": "ballot", "storage_type": "integer",
               "values": [{"code": 1, "label": "ballot a", "kind": "valid"}, missing(".i", "iap", "inap")]},
    "scale": {"name": "scale", "storage_type": "integer",
              "values": [{"code": 1, "label": "low", "kind": "valid"}, {"code": 7, "label": "high", "kind": "valid"},
                         {"code": 9, "label": "DK; haven't thought much", "kind": "valid"},
                         missing(98, "DK", "dk"), missing(99, "NA", "no_answer"),
                         {"code": -1, "label": "", "kind": "unresolved", "origin": ORIGIN}]},
    "item": {"name": "item", "storage_type": "integer",
             "values": [{"code": 1, "label": "yes", "kind": "valid"}, {"code": 2, "label": "no", "kind": "valid"},
                        missing(".d", "don't know", "dk"), missing(".m", "dk, na, iap", "dk", "no_answer", "inap"),
                        missing(".", "INAP. question not used", "not_asked")]},
    "comment": {"name": "comment", "storage_type": "string",
                "values": [missing("NA", "no answer", "no_answer")]},
}
RAW = pd.DataFrame({
    "year": [1972, 1972, 1988, 1988, 2024, 2024],
    "ballot": [Code(".i"), Code(".i"), 1, 1, 1, 1],
    "scale": [1, 98, 9, 99, -1, 7],
    "item": [1, Code(".d"), 2, Code(".m"), Code("."), 1],
    "comment": ["fine", "NA", "", "ok", "NA", "x"],
}, dtype=object)


def test_split_values_and_codes():
    t = split(RAW, RECORDS)
    assert t["scale"].isna().tolist() == [False, True, False, True, True, False]
    assert t["scale"].dropna().tolist() == [1, 9, 7]           # publisher-valid DK code 9 stays a value
    assert t["scale__code"].dropna().tolist() == ["98", "99", "-1"]  # unresolved -1 is a code, not a value
    assert t["item__code"].dropna().tolist() == [".d", ".m", "."]
    assert t["ballot__code"].dropna().tolist() == [".i", ".i"]  # dimension columns get code columns too
    assert "year" + CODE_SUFFIX not in t                        # no codes, no code column
    assert t["comment__code"].dropna().tolist() == ["NA", "NA"]
    assert t["comment"].tolist()[2] == ""                       # an empty string is a value, not null


def test_round_trip_is_exact():
    assert same_cells(RAW, rebuild(split(RAW, RECORDS), RECORDS))


def test_round_trip_through_parquet(tmp_path):
    path = tmp_path / "toy.parquet"
    write(split(RAW, RECORDS), path, {"dataset": "toy", "release": "r1", "metadata_sha256": "abc"})
    back = read(path)
    assert same_cells(RAW, rebuild(back, RECORDS))
    assert identity_of(path)["release"] == "r1"


def test_reserved_names():
    with pytest.raises(ValueError):
        split(pd.DataFrame({"x__code": [1]}, dtype=object))


def test_recode_by_type():
    t = split(RAW, RECORDS)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UnresolvedCodes)
        out = recode(t, RECORDS["scale"], dk="DK")
    assert out.tolist() == [1, "DK", 9, None, None, 7]


def test_recode_never_treats_unresolved_as_missing():
    t = split(RAW, RECORDS)
    with pytest.warns(UnresolvedCodes):
        out = recode(t, RECORDS["scale"], dk="DK", no_answer="NA")
    assert out.tolist()[4] is None
    assert recode(t, RECORDS["scale"], unresolved="?").tolist()[4] == "?"


def test_recode_multi_type_code():
    """.m ("dk, na, iap") is replaced only when all its types are given and agree."""
    t = split(RAW, RECORDS)
    assert recode(t, RECORDS["item"], dk="DK").tolist()[3] is None
    assert recode(t, RECORDS["item"], dk="DK", inap="IAP", no_answer="NA").tolist()[3] is None
    assert recode(t, RECORDS["item"], dk="X", inap="X", no_answer="X").tolist()[3] == "X"
    nan = float("nan")
    out = recode(t, RECORDS["item"], dk=nan, inap=nan, no_answer=nan)
    assert isinstance(out.tolist()[3], float) and np.isnan(out.tolist()[3])


def test_metadata_evolution(tmp_path):
    """A file built with release r1's metadata keeps r1's classification, and newer metadata is detected."""
    r1 = RECORDS
    r2 = {**RECORDS, "scale": {**RECORDS["scale"], "values": [
        v if v["code"] != 9 else missing(9, "DK; haven't thought much", "dk") for v in RECORDS["scale"]["values"]]}}
    path = tmp_path / "r1.parquet"
    write(split(RAW, r1), path, {"dataset": "toy", "release": "r1", "metadata_sha256": "sha-r1"})
    table = read(path)

    # Read with its own metadata: 9 is still a valid value, and the round trip is exact.
    assert 9 in table["scale"].dropna().tolist()
    assert same_cells(RAW, rebuild(table, r1))
    with warnings.catch_warnings():
        warnings.simplefilter("error", MetadataMismatch)
        check_identity(path, "toy", "r1", "sha-r1")

    # Newer metadata reclassifies 9 as DK; using it with the old file is flagged.
    with pytest.warns(MetadataMismatch):
        check_identity(path, "toy", "r1", "sha-r2")
    with pytest.warns(MetadataMismatch):
        check_identity(path, "other", "r1", "sha-r1")
    # Splitting the same raw data with the newer metadata moves 9 to the code column.
    assert "9" in split(RAW, r2)["scale__code"].dropna().tolist()


def test_recode_warns_on_codes_missing_from_metadata():
    t = split(RAW, RECORDS)
    stale = {**RECORDS["item"], "values": [v for v in RECORDS["item"]["values"] if v["code"] != ".m"]}
    with pytest.warns(UnresolvedCodes):
        out = recode(t, stale, dk="DK")
    assert out.tolist()[3] is None


def test_write_requires_identity(tmp_path):
    with pytest.raises(ValueError):
        write(split(RAW, RECORDS), tmp_path / "x.parquet", {"dataset": "toy", "release": "r1"})


# Regression tests for bugs found in review (2026-11-19).

def missing_rec(name, code, storage=None):
    rec = {"name": name, "values": [missing(code, "x", "dk")]}
    if storage:
        rec["storage_type"] = storage
    return rec


def round_trips(raw, records, tmp_path=None):
    table = split(raw, records)
    if tmp_path is not None:
        write(table, tmp_path / "t.parquet", {"dataset": "t", "release": "r", "metadata_sha256": "s"})
        table = read(tmp_path / "t.parquet")
    return same_cells(raw, rebuild(table, records))


def test_string_variable_keeps_code_tokens(tmp_path):
    raw = pd.DataFrame({"s": pd.Series(["a", Code(".d")], dtype=object)})
    assert round_trips(raw, {"s": missing_rec("s", ".d", "string")}, tmp_path)


def test_string_variable_without_storage_type_keeps_plain_strings(tmp_path):
    raw = pd.DataFrame({"s": pd.Series(["a", "NA"], dtype=object)})
    assert round_trips(raw, {"s": missing_rec("s", "NA")}, tmp_path)


def test_codes_match_by_type_not_text(tmp_path):
    # a string "98" in a string variable isn't the numeric code 98
    raw = pd.DataFrame({"s": pd.Series(["98", "x"], dtype=object)})
    t = split(raw, {"s": missing_rec("s", 98)})
    assert CODE_SUFFIX not in "".join(t.columns) and round_trips(raw, {"s": missing_rec("s", 98)}, tmp_path)
    # a number 98 isn't the string code "98"
    raw = pd.DataFrame({"x": pd.Series([98, 1], dtype=object)})
    assert "x__code" not in split(raw, {"x": missing_rec("x", "98")})
    # a publisher token Code("98") stays a token even if 98 is a numeric code...
    raw = pd.DataFrame({"x": pd.Series([Code("98"), 1], dtype=object)})
    assert round_trips(raw, {"x": missing_rec("x", 98)}, tmp_path)
    # ...but both in one variable would be ambiguous, so split refuses
    raw = pd.DataFrame({"x": pd.Series([Code("98"), 98, 1], dtype=object)})
    with pytest.raises(ValueError, match="can't tell them apart"):
        split(raw, {"x": missing_rec("x", 98)})
    # True isn't the code 1
    raw = pd.DataFrame({"b": pd.Series([True, False], dtype=object)})
    assert "b__code" not in split(raw, {"b": missing_rec("b", 1)})


def test_float32_codes_match():
    raw = pd.DataFrame({"x": pd.Series(list(np.array([1, 0.1], dtype="float32")), dtype=object)})
    t = split(raw, {"x": missing_rec("x", 0.1)})
    assert t["x__code"].tolist()[1] == "0.1" and t["x"].isna().tolist() == [False, True]


def test_dtype_inference_edge_cases(tmp_path):
    raw = pd.DataFrame({"x": pd.Series([1e20, 98.0], dtype=object)})
    assert split(raw)["x"].dtype == "Float64"
    with pytest.raises(ValueError, match="x: storage_type is integer"):
        split(pd.DataFrame({"x": pd.Series([1, 1.5], dtype=object)}), {"x": {"name": "x", "storage_type": "integer"}})
    with pytest.raises(ValueError, match="mixed types"):
        split(pd.DataFrame({"x": pd.Series([1, "a"], dtype=object)}))

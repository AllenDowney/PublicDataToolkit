"""Tests for the extract builder (pdt.extract) and recode's report of inferred classifications."""

import json
import warnings

import pandas as pd
import pytest
import yaml

from pdt import data
from pdt.data import Code, InferredClassification, UnresolvedCodes, recode, split
from pdt.extract import extract, inferred_codes, main
from pdt.release import write_release

ORIGIN = {"origin": "publisher", "source": "cb"}


def cells(series):
    """A column's cells, with every kind of null (None, NaN, pd.NA) as None."""
    return [None if data.is_null(x) else x for x in series.astype(object).tolist()]


def missing(code, label, *types):
    return {"code": code, "label": label, "kind": "missing", "missing_types": list(types), "origin": ORIGIN}


def unresolved(code):
    return {"code": code, "label": "", "kind": "unresolved", "origin": {"origin": "data_file", "source": "dat"}}


# A small ANES-like release: year is the wave column; therm has DK 98 and an
# undocumented -8 that an inferred correction types as dk; adopt has 1/5 and a
# code 2 that an inferred correction makes a valid "No"; sex has nothing unusual.
RECORDS = [
    {"dataset": "toy", "release": "r1", "name": "year", "storage_type": "integer",
     "provenance": {"record": ORIGIN}},
    {"dataset": "toy", "release": "r1", "name": "therm", "storage_type": "integer",
     "values": [missing(98, "DK", "dk"), missing(99, "NA", "no_answer"), unresolved(-8)],
     "provenance": {"record": ORIGIN}},
    {"dataset": "toy", "release": "r1", "name": "adopt", "storage_type": "integer",
     "values": [{"code": 1, "label": "Yes", "kind": "valid"}, {"code": 5, "label": "No", "kind": "valid"},
                missing(".", "INAP", "inap"), unresolved(2)],
     "provenance": {"record": ORIGIN}},
    {"dataset": "toy", "release": "r1", "name": "Sex", "storage_type": "integer",
     "values": [{"code": 1, "label": "Male", "kind": "valid"}, {"code": 2, "label": "Female", "kind": "valid"}],
     "provenance": {"record": ORIGIN}},
]
CORRECTIONS = [
    {"id": "therm-minus8", "target": {"name": "therm", "field": "/values/2"},
     "original": unresolved(-8), "corrected": missing(-8, "DK (2024)", "dk"),
     "problem": "-8 isn't in the codebook.", "evidence": [{"citation": "x"}], "confidence": "inferred",
     "upstream": {"status": "not_filed"}, "author": "t", "date": "2026-11-19"},
    {"id": "adopt-2", "target": {"name": "adopt", "field": "/values/3"},
     "original": unresolved(2), "corrected": {"code": 2, "label": "No (2024)", "kind": "valid"},
     "problem": "2 isn't in the codebook.", "evidence": [{"citation": "x"}], "confidence": "inferred",
     "upstream": {"status": "not_filed"}, "author": "t", "date": "2026-11-19"},
]
RAW = pd.DataFrame({
    "year": [2020, 2020, 2024, 2024, 2024],
    "therm": [50, 98, -8, 99, 70],
    "adopt": [1, 5, 2, Code("."), 1],
    "Sex": [1, 2, 1, 2, 2],
}, dtype=object)


def make_repo(root, corrections=CORRECTIONS):
    (root / "metadata" / "releases" / "r1").mkdir(parents=True)
    (root / "dataset.yaml").write_text(yaml.safe_dump({
        "id": "toy", "standard_version": "0.1",
        "terms": {"data": "ship", "documentation": "ship", "metadata": "ship"},
        "dimensions": {"wave": {"label": "year", "column": "year"}},
        "releases": [{"id": "r1", "status": "current", "sources": ["dat"]}]}))
    (root / "sources.yaml").write_text(yaml.safe_dump({"sources": [
        {"id": "dat", "kind": "data", "redistribution": "ship", "acquisition": "manual"}]}))
    (root / "metadata" / "releases" / "r1" / "variables.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in RECORDS))
    (root / "metadata" / "corrections.jsonl").write_text("".join(json.dumps(c) + "\n" for c in corrections))
    write_release(root, lambda rel, tab, names: (RAW[names], "dat"), log=lambda *a: None)
    return root


def test_extract_recodes_and_reports_inferred(tmp_path):
    root = make_repo(tmp_path)
    with pytest.warns(InferredClassification, match="therm: code -8 \\(1 values\\).*therm-minus8.*replaced with 'DK'"):
        r = extract(root, "r1", ["year", "therm", "adopt"], missing={"dk": "DK"})
    assert cells(r.frame["therm"]) == [50, "DK", "DK", None, 70]
    # code 2 is a value in the file, because it was split with the corrected records
    assert cells(r.frame["adopt"]) == [1, 5, 2, None, 1]
    text = "\n".join(r.report)
    assert "adopt: value 2 (1 values) is valid, labeled 'No (2024)', only because of inferred correction adopt-2" in text
    assert "InferredClassification: therm: code -8" in text


def test_inferred_code_left_null_is_reported(tmp_path):
    root = make_repo(tmp_path)
    with pytest.warns(InferredClassification, match="left null as dk"):
        r = extract(root, "r1", ["therm"])
    assert cells(r.frame["therm"]) == [50, None, None, None, 70]
    assert str(r.frame["therm"].dtype) == "Int64"


def test_no_inferred_report_without_inferred_corrections(tmp_path):
    root = make_repo(tmp_path, corrections=[])
    with warnings.catch_warnings():
        warnings.simplefilter("error", InferredClassification)
        warnings.simplefilter("ignore", UnresolvedCodes)
        r = extract(root, "r1", ["therm", "adopt"])
    assert cells(r.frame["adopt"]) == [1, 5, None, None, 1]  # 2 is unresolved, so null


def test_waves_and_case_insensitive_names(tmp_path):
    root = make_repo(tmp_path)
    r = extract(root, "r1", ["sex"], waves=[2024])
    assert list(r.frame.columns) == ["Sex"]
    assert cells(r.frame["Sex"]) == [1, 2, 2]


def test_codes_column_kept_on_request(tmp_path):
    root = make_repo(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InferredClassification)
        r = extract(root, "r1", ["therm"], codes=True)
    assert cells(r.frame["therm__code"]) == [None, "98", "-8", "99", None]


def test_stale_corrections_warn(tmp_path):
    root = make_repo(tmp_path)
    (root / "metadata" / "corrections.jsonl").write_text("")
    with pytest.warns(data.MetadataMismatch, match="other corrections"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UnresolvedCodes)
            extract(root, "r1", ["therm"])


def test_unknown_variable(tmp_path):
    root = make_repo(tmp_path)
    with pytest.raises(KeyError, match="no variable"):
        extract(root, "r1", ["nope"])


def test_cli_writes_csv(tmp_path, capsys):
    root = make_repo(tmp_path / "repo")
    out = tmp_path / "x.csv"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InferredClassification)
        assert main([str(root), "--release", "r1", "--vars", "year,therm", "--missing", "dk=-1",
                     "no_answer=null", "--waves", "2020-2024", "--out", str(out)]) == 0
    frame = pd.read_csv(out)
    assert frame["therm"].tolist()[:3] == [50, -1, -1]
    assert "InferredClassification" in capsys.readouterr().err


def test_recode_inferred_argument():
    records = {r["name"]: r for r in RECORDS}
    fixed = dict(records["therm"], values=[missing(98, "DK", "dk"), missing(99, "NA", "no_answer"),
                                           missing(-8, "DK (2024)", "dk")])
    t = split(RAW[["therm"]], {"therm": fixed})
    with pytest.warns(InferredClassification, match="code -8"):
        out = recode(t, fixed, inferred={"-8": ["therm-minus8"]}, dk="DK")
    assert out.tolist() == [50, "DK", "DK", None, 70]


def test_inferred_codes_reads_value_pointers():
    rec = {"values": [missing(98, "DK", "dk"), missing(-1, "INAP (2024)", "inap")]}
    applied = [{"id": "a", "field": "/values/1", "confidence": "inferred"},
               {"id": "b", "field": "/values/0", "confidence": "verified"},
               {"id": "c", "field": "/label", "confidence": "inferred"}]
    assert inferred_codes(rec, applied) == {"-1": ["a"]}

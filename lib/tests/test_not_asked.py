"""recode's and extract's not_asked_from_availability: one missing code, split by availability.

The YRBSS combined datasets use one blank for "no answer, invalid, not asked": q26 (sad or
hopeless) was first asked in 1999, so a blank in 1991 means not asked, and one in 1999 doesn't.
"""

import json

import pandas as pd
import pytest
import yaml

from pdt import data
from pdt.extract import extract
from pdt.release import write_release

ORIGIN = {"origin": "publisher", "source": "cb"}
BLANK = {"code": " ", "label": "Missing", "kind": "missing",
         "missing_types": ["no_answer", "uncodeable", "not_asked"], "origin": ORIGIN}
Q26 = {"dataset": "toy", "release": "r1", "name": "q26", "storage_type": "string",
       "values": [BLANK, {"code": "1", "label": "Yes", "kind": "valid"}, {"code": "2", "label": "No", "kind": "valid"}],
       "availability": [{"wave": 1999}, {"wave": 2001}], "provenance": {"record": ORIGIN}}
YEAR = {"dataset": "toy", "release": "r1", "name": "year", "storage_type": "integer", "provenance": {"record": ORIGIN}}
RAW = pd.DataFrame({"year": [1991, 1991, 1999, 1999, 2001],
                    "q26": [" ", " ", " ", "1", "2"]}, dtype=object)


def cells(series):
    return [None if data.is_null(x) else x for x in series.astype(object).tolist()]


def table():
    return data.split(RAW, {"q26": Q26, "year": YEAR})


def test_off_by_default_needs_every_type():
    t = table()
    assert cells(data.recode(t, Q26, not_asked="NA")) == [None, None, None, "1", "2"]
    assert cells(data.recode(t, Q26, not_asked="NA", no_answer="M", uncodeable="M")) == [None, None, None, "1", "2"]
    assert "not_asked_split" not in data.recode(t, Q26).attrs


def test_split_by_availability():
    t = table()
    out = data.recode(t, Q26, not_asked_from_availability=True, waves="year", not_asked="NA")
    assert cells(out) == ["NA", "NA", None, "1", "2"]             # 1999's blank isn't not_asked
    assert out.attrs["not_asked_split"] == {"not_asked": 2, "other": 1}
    out = data.recode(t, Q26, not_asked_from_availability=True, waves=t["year"].tolist(),
                      not_asked="NA", no_answer="M", uncodeable="M")
    assert cells(out) == ["NA", "NA", "M", "1", "2"]
    # The other types must all be given, as without the option.
    out = data.recode(t, Q26, not_asked_from_availability=True, waves="year", no_answer="M")
    assert cells(out) == [None, None, None, "1", "2"]


def test_rows_without_a_wave_keep_every_type_and_waves_are_required():
    t = table()
    out = data.recode(t, Q26, not_asked_from_availability=True, waves=[None, 1991, None, None, None],
                      not_asked="X", no_answer="X", uncodeable="X")
    assert cells(out) == ["X", "X", "X", "1", "2"]                # no wave: all three types, all given
    with pytest.raises(ValueError, match="waves"):
        data.recode(t, Q26, not_asked_from_availability=True)


def test_text_and_number_waves_match():
    t = table()
    rec = dict(Q26, availability=[{"wave": "1999"}, {"wave": "2001"}])
    out = data.recode(t, rec, not_asked_from_availability=True, waves=[1991.0, 1991, 1999.0, 1999, 2001],
                      not_asked="NA")
    assert cells(out) == ["NA", "NA", None, "1", "2"]


def test_extract_option_and_report(tmp_path):
    root = tmp_path
    (root / "metadata" / "releases" / "r1").mkdir(parents=True)
    (root / "dataset.yaml").write_text(yaml.safe_dump({
        "id": "toy", "standard_version": "0.1",
        "terms": {"data": "ship", "documentation": "ship", "metadata": "ship"},
        "dimensions": {"wave": {"label": "year", "column": "year"}},
        "releases": [{"id": "r1", "status": "current", "sources": ["dat"]}]}))
    (root / "sources.yaml").write_text(yaml.safe_dump({"sources": [
        {"id": "dat", "kind": "data", "redistribution": "ship", "acquisition": "manual"}]}))
    (root / "metadata" / "releases" / "r1" / "variables.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in [YEAR, Q26]))
    write_release(root, lambda rel, tab, names: (RAW[names], "dat"), log=lambda *a: None)

    plain = extract(root, "r1", ["q26"], missing={"not_asked": "NA"})
    assert cells(plain.frame["q26"]) == [None, None, None, "1", "2"]
    r = extract(root, "r1", ["q26"], missing={"not_asked": "NA"}, not_asked_from_availability=True)
    assert list(r.frame.columns) == ["q26"]
    assert cells(r.frame["q26"]) == ["NA", "NA", None, "1", "2"]
    assert any("2 missing values in waves outside its availability read as not_asked, 1 inside" in line
               for line in r.report)

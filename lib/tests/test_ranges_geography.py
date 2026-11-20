"""Task 67: several valid ranges, the geography dimension, per-code notes and the label lint."""

import pytest
import yaml

from pdt import diff, export, site, views
from pdt.check import Repo, run
from pdt.derived import scale_signature
from pdt.lint import label_problem, label_problems
from pdt.ranges import comparable, in_valid_range, range_text, span, valid_ranges, without_notes
from pdt.search import Index, search
from test_check import DATASET, VARIABLES, make_repo, write_jsonl

PUB = {"origin": "publisher", "source": "cb"}
# BRFSS ALCDAY5: two ranges with different meanings
TWO = [{"min": 101, "max": 107, "label": "Days per week"},
       {"min": 201, "max": 230, "label": "Days in past 30 days"}]


def alcday(release="r1", ranges=TWO, **extra):
    return {"dataset": "toy", "release": release, "name": "alcday", "label": "Days in past 30 had alcoholic beverage",
            "questions": [{"text": "During the past 30 days, how many days per week or per month did you have at least one drink?"}],
            "values": [{"code": 888, "label": "No drinks in past 30 days", "kind": "valid",
                        "note": "Coded as zero days"},
                       {"code": 777, "label": "Don't know/Not sure", "kind": "missing", "missing_types": ["dk"],
                        "origin": PUB}],
            "valid_range": ranges, "measure": "count", "storage_type": "integer",
            "provenance": {"record": PUB}, **extra}


def test_ranges_helpers():
    one = {"valid_range": {"min": 0, "max": 100, "note": "0-100 Degrees"}}
    two = {"valid_range": TWO}
    assert valid_ranges({}) == [] and len(valid_ranges(one)) == 1 and len(valid_ranges(two)) == 2
    assert in_valid_range(two, 105) and in_valid_range(two, 230) and not in_valid_range(two, 150)
    assert in_valid_range(one, 50.5)
    assert not in_valid_range(two, "abc") and not in_valid_range({}, 1)
    assert span(two) == (101, 230) and span({}) is None
    assert without_notes(one) == {"min": 0, "max": 100} and without_notes(two) == TWO
    assert comparable(two)[0][:3] == (101, 107, "Days per week")
    assert range_text(TWO[0]) == "101–107 (Days per week)"
    assert range_text({"min": 18, "max": 85, "top_coded": True}) == "18–85, top-coded"


def test_schema_accepts_a_list_and_geography(tmp_path):
    dataset = dict(DATASET, dimensions={"wave": {"label": "survey year"},
                                        "geography": {"label": "state (FIPS code)"}})
    rec = alcday(availability=[{"wave": 1988, "geography": "25", "n": 10}])
    root = make_repo(tmp_path, dataset=dataset, variables=[rec], groups=[], corrections=[])
    result = run(root, views=False)
    assert result.ok, result.failures


def test_derived_thermometer_from_any_range_note():
    rec = {"values": [], "valid_range": [{"min": 0, "max": 50, "label": "a", "note": "0-50 degrees"},
                                         {"min": 51, "max": 100, "label": "b"}]}
    assert scale_signature(rec) == "thermometer"


def test_diff_compares_lists(tmp_path):
    dataset = dict(DATASET, releases=[
        {"id": "r1", "label": "R1", "status": "superseded", "sources": ["cb"]},
        {"id": "r2", "label": "R2", "status": "current", "sources": ["cb"]}])
    narrowed = [TWO[0], dict(TWO[1], max=229)]
    root = make_repo(tmp_path, dataset=dataset, variables=[], groups=[], corrections=[])
    write_jsonl(root / "metadata" / "releases" / "r1" / "variables.jsonl",
                [alcday("r1"), dict(alcday("r1"), name="same"), dict(alcday("r1"), name="one")])
    write_jsonl(root / "metadata" / "releases" / "r2" / "variables.jsonl",
                [alcday("r2", narrowed), dict(alcday("r2"), name="same"),
                 dict(alcday("r2", {"min": 101, "max": 230}), name="one")])
    result = diff.diff(Repo.load(root), "r1", "r2")
    entries = {x["from"]: x for x in result["tables"][0]["in_both"]}
    assert entries["alcday"]["changes"]["valid_range"]["to"][1]["max"] == 229
    assert "valid_range" not in entries["same"]["changes"]
    assert entries["one"]["changes"]["valid_range"]["how"] == "documented"    # two ranges became one


def test_site_shows_ranges_notes_and_geography(tmp_path):
    dataset = dict(DATASET, dimensions={"geography": {"label": "state"}})
    rec = alcday(availability=[{"wave": 1988, "geography": "25", "n": 10},
                               {"wave": 1988, "geography": "06", "n": 7}])
    root = make_repo(tmp_path, dataset=dataset, variables=[rec, VARIABLES[0]], groups=[], corrections=[])
    site.build(root)
    page = (root / "docs" / "variables" / "alcday.html").read_text()
    assert "Valid ranges" in page and "101–107 (Days per week)" in page and "201–230" in page
    assert "Note: Coded as zero days" in page
    assert "state 25" in page and "state 06" in page


def test_views_and_search_by_geography(tmp_path):
    rec = alcday(availability=[{"wave": 1988, "geography": "25"}, {"wave": 1989, "geography": "25"}])
    everywhere = dict(VARIABLES[0], availability=[{"wave": 1988}])
    elsewhere = dict(alcday(), name="other", availability=[{"wave": 1988, "geography": "06"}])
    assert views.compact_availability(rec["availability"], [1988, 1989]) == {"geography 25": "1988-1989"}
    root = make_repo(tmp_path, variables=[rec, everywhere, elsewhere], groups=[], corrections=[])
    idx = Index.from_repo(Repo.load(root))
    found = search(idx, {"available": {"wave": 1988, "geography": "25"}})
    assert sorted(rec["name"] for _, _, rec in found.matches) == ["alcday", "q1"]   # q1: everywhere
    assert found.label == "complete"
    both = search(idx, {"available": {"wave": 1988, "geography": "25"}, "name": "alcday"})
    assert [rec["name"] for _, _, rec in both.matches] == ["alcday"]
    with pytest.raises(ValueError):
        search(idx, {"available": {"wave": 1988, "county": "1"}})


def test_export_spans_several_ranges(tmp_path):
    root = make_repo(tmp_path, variables=[alcday()], groups=[], corrections=[])
    export.build(root)
    doc = yaml.safe_load((root / "export" / "data-dict" / "r1.yaml").read_text())
    col = {c["name"]: c for c in doc["tables"][0]["columns"]}["alcday"]
    assert col["range"] == [101, 230]
    assert "several valid ranges" in (root / "export" / "data-dict" / "LOSSES.md").read_text()


@pytest.mark.parametrize("label, code, why", [
    ("126", ".", "a number other than its code"),             # BRFSS _RACEGR2 2011: the count as label
    ("1,234", None, "a number other than its code"),
    ("Refused   1,234   0.12", 7, "a frequency and percentages"),
    ("Volunteer Activities                     Volunteer activities", 1, "a column gap"),
    ("Male\xad--Go to Section 08", 1, "a soft hyphen"),
    ("Yes  Notes: SMOKE100 = 1", 1, "a codebook keyword"),
    ("0", 1, None),                                            # GSS: code 1 is "0" times
    ("10", 10, None),
    ("Don't know/Not sure", 7, None),
    ("101 - 107 Days per week", None, None),
])
def test_label_lint(label, code, why):
    assert label_problem(label, code) == why


def test_label_lint_in_check(tmp_path):
    bad = dict(VARIABLES[0], values=[{"code": 1, "label": "yes", "kind": "valid"},
                                     {"code": ".", "label": "126", "kind": "valid"}])
    root = make_repo(tmp_path, variables=[bad, VARIABLES[1]], groups=[], corrections=[])
    assert label_problems(Repo.load(root).records) == [("r1/q1 code .", "126", "a number other than its code")]
    result = run(root, views=False)
    assert result.ok                                           # a report, never a failure
    assert any("1 labels look like a parser's leftovers" in r and "r1/q1 code ." in r for r in result.reports)

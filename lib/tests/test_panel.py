"""pdt.panel: a panel's answers placed in time, and named policies (PublicDataToolkit Task 69)."""

import copy

import pandas as pd
import pytest
import yaml

from pdt.panel import Answer, NoAnswer, Panel, pick
from test_check import DATASET, make_repo, write_jsonl

PUB = {"origin": "publisher"}
YEARS = [2009, 2010, 2011, 2013]
# Person 1 is interviewed every round; person 2 misses 2010; person 3 is never interviewed in 2011 or 2013.
# Months count from January 1980 = 1 (month_zero = December 1979): 2009-11 = 359, 2010-11 = 371, ...
MONTH = {(1, 2009): 359, (1, 2010): 371, (1, 2011): 383, (1, 2013): 407,
         (2, 2009): 360, (2, 2010): -5, (2, 2011): 384, (2, 2013): 408,
         (3, 2009): 361, (3, 2010): 373, (3, 2011): -5, (3, 2013): -5}
AGE = {(1, 2009): 24, (1, 2010): 25, (1, 2011): 26, (1, 2013): 28,
       (2, 2009): 25, (2, 2010): -5, (2, 2011): 26, (2, 2013): 28,
       (3, 2009): 27, (3, 2010): 28, (3, 2011): -5, (3, 2013): -5}
SMOKED = {(1, 2009): 0, (1, 2010): 1, (1, 2011): 1, (1, 2013): 0,
          (2, 2009): 0, (2, 2010): -5, (2, 2011): 1, (2, 2013): 1,
          (3, 2009): 1, (3, 2010): 1, (3, 2011): -5, (3, 2013): -5}
STATUS = {k: (1 if k[0] == 1 and k[1] >= 2011 else 0) if MONTH[k] > 0 else -5 for k in MONTH}


def rec(name, **kw):
    return dict({"dataset": "toy", "release": "r1", "table": "py", "name": name, "label": name,
                 "provenance": {"record": PUB}}, **kw)


VALUES = [{"code": 0, "label": "No", "kind": "valid"}, {"code": 1, "label": "Yes", "kind": "valid"},
          {"code": -5, "label": "Non-interview", "kind": "missing", "missing_types": ["not_asked"], "origin": PUB}]
RECORDS = [rec("ID"), rec("YEAR"), rec("MONTH"), rec("AGE"), rec("RNI"),
           rec("SMOKED", values=VALUES, questions=[
               {"text": "Smoked since the last interview?", "waves": [2009, 2010, 2011], "reference_period": "since_last_interview"},
               {"text": "Smoked in the past twelve months?", "waves": [2013], "reference_period": "past_months", "months": 12}]),
           rec("STATUS", values=VALUES, questions=[{"text": "Married as of the interview?", "reference_period": "as_of_interview"}])]


@pytest.fixture
def panel(tmp_path):
    ds = copy.deepcopy(DATASET)
    ds["releases"][0]["tables"] = [{"id": "py", "label": "person-year", "key": ["ID", "YEAR"]}]
    ds["panel"] = {"id": "ID", "interview_date": ["MONTH"], "age_at_interview": "AGE", "noninterview": "RNI"}
    ds["dimensions"] = {"wave": {"label": "year", "column": "YEAR"}}
    root = make_repo(tmp_path, dataset=ds, variables=[], groups=[], corrections=[])
    write_jsonl(root / "metadata" / "releases" / "r1" / "py" / "variables.jsonl", RECORDS)
    keys = sorted(MONTH)
    frame = pd.DataFrame({"ID": [k[0] for k in keys], "YEAR": [k[1] for k in keys],
                          "MONTH": [MONTH[k] for k in keys], "AGE": [AGE[k] for k in keys],
                          "RNI": [60 if MONTH[k] > 0 else 96 for k in keys],
                          "SMOKED": [SMOKED[k] for k in keys], "STATUS": [STATUS[k] for k in keys]})
    return Panel(root, month_zero=(1979, 12), data=frame)


def test_since_last_interview_periods_and_overlap(panel):
    out = panel.answers("SMOKED", 1, year=2010)
    assert [(a.wave, a.period, a.overlap_months) for a in out] == [(2010, (360, 371), 11), (2011, (372, 383), 1)]
    assert all(isinstance(a, Answer) and a.period_kind == "since_last_interview" for a in out)


def test_a_missed_round_stretches_the_next_period(panel):
    out = panel.answers("SMOKED", 2, year=2010)
    # 2010 was missed, so the 2011 answer covers December 2009 to December 2010 and beyond
    assert [(a.wave, a.period) for a in out] == [(2011, (361, 384))]
    out = panel.answers("SMOKED", 3, year=2012)       # person 3 left after 2010: only reasons
    assert out and all(isinstance(a, NoAnswer) for a in out) and any("not interviewed" in a.reason for a in out)


def test_past_twelve_months_leaves_a_gap_year(panel):
    out = panel.answers("SMOKED", 1, year=2012)
    assert [(a.wave, a.period) for a in out] == [(2013, (396, 407))]       # Dec 2012 to Nov 2013 only
    assert out[0].overlap_months == 1


def test_age_candidates_sorted_by_distance_and_never_picked(panel):
    out = panel.answers("STATUS", 1, age=25)
    assert [(a.wave, a.distance_years) for a in out] == [(2010, 0), (2009, -1), (2011, 1), (2013, 3)]
    assert pick(out, "exact").answer.wave == 2010
    assert pick(out, "latest").answer.wave == 2013


def test_nearest_reports_a_disagreeing_tie(panel):
    out = panel.answers("STATUS", 3, age=26)           # ages 27 (2009) and 28 (2010) only: nearest is 27
    assert pick(out, "nearest").answer.wave == 2009
    tied = [Answer("STATUS", 9, 2001, 0, distance_years=-1), Answer("STATUS", 9, 2003, 1, distance_years=1)]
    result = pick(tied, "nearest")
    assert result.answer is None and "disagree" in result.note and len(result.candidates) == 2


def test_no_answer_reasons(panel):
    out = panel.answers("SMOKED", 3, year=2013)
    assert all(isinstance(a, NoAnswer) for a in out)
    assert pick(out, "most_overlap").answer is None
    with pytest.raises(ValueError):
        panel.answers("SMOKED", 1)
    with pytest.raises(ValueError):
        pick(out, "whatever")


def test_month_zero_from_the_panel_block(tmp_path):
    ds = copy.deepcopy(DATASET)
    ds["releases"][0]["tables"] = [{"id": "py", "label": "person-year", "key": ["ID", "YEAR"]}]
    ds["panel"] = {"id": "ID", "interview_date": ["MONTH"], "age_at_interview": "AGE", "month_zero": "1979-12"}
    ds["dimensions"] = {"wave": {"label": "year", "column": "YEAR"}}
    root = make_repo(tmp_path, dataset=ds, variables=[], groups=[], corrections=[])
    write_jsonl(root / "metadata" / "releases" / "r1" / "py" / "variables.jsonl", RECORDS)
    keys = sorted(MONTH)
    frame = pd.DataFrame({"ID": [k[0] for k in keys], "YEAR": [k[1] for k in keys], "MONTH": [MONTH[k] for k in keys],
                          "AGE": [AGE[k] for k in keys], "SMOKED": [SMOKED[k] for k in keys]})
    p = Panel(root, data=frame)
    assert p.month_zero == (1979, 12) and p.year_months(2010) == (361, 372)
    assert Panel(root, data=frame, month_zero=(1980, 1)).year_months(2010) == (360, 371)

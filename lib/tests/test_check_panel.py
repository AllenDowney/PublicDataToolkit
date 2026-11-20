"""C2 for panel (STANDARD.md §2.1) and questions[].reference_period past_months (§4.1)."""

from test_check import DATASET, VARIABLES, make_repo, run
from test_code_lists import failures


def test_panel_names_need_records(tmp_path):
    ok, bad = tmp_path / "ok", tmp_path / "bad"
    ok.mkdir(), bad.mkdir()
    assert not failures(run(make_repo(ok, dataset=dict(DATASET, panel={"id": "q1", "interview_date": ["q2"]}))), "C2")
    result = run(make_repo(bad, dataset=dict(DATASET, panel={"id": "q1", "age_at_interview": "AGE"})))
    assert any("panel names AGE" in f for f in failures(result, "C2"))


def test_past_months_needs_months(tmp_path):
    rec = dict(VARIABLES[1], questions=[{"text": "In the past twelve months?", "reference_period": "past_months"}])
    result = run(make_repo(tmp_path, variables=[VARIABLES[0], rec]))
    assert any("past_months but no months" in f for f in failures(result, "C2"))
    good = tmp_path / "good"
    good.mkdir()
    rec2 = dict(rec, questions=[dict(rec["questions"][0], months=12)])
    assert not failures(run(make_repo(good, variables=[VARIABLES[0], rec2])), "C2")

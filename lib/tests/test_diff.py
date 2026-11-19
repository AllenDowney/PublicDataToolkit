"""Tests for `pdt diff`, the release comparison."""

import json

import pytest

from pdt import diff
from pdt.check import Repo
from pdt.cli import main
from test_check import DATASET, VARIABLES, make_repo, write_jsonl

PUB = {"origin": "publisher", "source": "cb"}


def rec(release, name, label, values=(), question=None, universe=None, waves=()):
    r = {"dataset": "toy", "release": release, "name": name, "label": label,
         "values": [dict(v) for v in values], "provenance": {"record": PUB},
         "availability": [{"wave": w} for w in waves]}
    if question:
        r["questions"] = [{"text": question}]
    if universe:
        r["universe"] = universe
    return r


V = lambda code, label, kind="valid", **kw: {"code": code, "label": label, "kind": kind, **kw}
MISSING = {"missing_types": ["dk"], "origin": PUB}


@pytest.fixture
def repo(tmp_path):
    dataset = dict(DATASET, releases=[
        {"id": "r1", "label": "R1", "status": "superseded", "sources": ["cb"]},
        {"id": "r2", "label": "R2", "status": "current", "sources": ["cb"]}])
    a = [rec("r1", "same", "Same", [V(1, "Yes"), V(2, "No")], "Agree?", waves=[2017]),
         rec("r1", "light", "Light", [V(1, "Daylight"), V(9, "Unknown", "missing", **MISSING)], waves=[2017]),
         rec("r1", "weather", "Weather", [V(1, "Clear"), V(9, "Unknown", "missing", **MISSING)], waves=[2017]),
         rec("r1", "dash", "Dash", [V(2, "Dark - Not Lighted")], waves=[2017]),
         rec("r1", "item", "IC-9 Importance", [V(1, "Very")], "IC-9 How important?", waves=[2017]),
         rec("r1", "kind", "Kind", [V(8, "Other"), V(9, "Unknown", "unresolved", origin=PUB)], waves=[2017]),
         rec("r1", "Wgt2017", "Final weight for 2017", [], waves=[2017]),
         rec("r1", "gone", "Dropped", [V(1, "x")], waves=[2017])]
    b = [rec("r2", "same", "Same", [V(1, "Yes"), V(2, "No")], "Agree?", waves=[2024]),
         rec("r2", "light", "Light", [V(1, "Daylight"), V(9, "Reported as Unknown", "missing", **MISSING)],
             waves=[2024]),
         rec("r2", "weather", "Weather", [V(1, "Clear"), V(99, "Unknown", "missing", **MISSING)], waves=[2024]),
         rec("r2", "dash", "Dash", [V(2, "Dark – Not Lighted")], waves=[2024]),
         rec("r2", "item", "IC-7 Importance", [V(1, "Very")], "IC-7 How important?", "All", waves=[2024]),
         rec("r2", "KIND", "Kind", [V(8, "Other"), V(9, "Unknown", "missing", **MISSING)], waves=[2024]),
         rec("r2", "Wgt2024", "Final weight for 2024", [], waves=[2024]),
         rec("r2", "new", "Added", [V(1, "y")], waves=[2024])]
    root = make_repo(tmp_path, dataset=dataset, variables=[], groups=[], corrections=[])
    write_jsonl(root / "metadata" / "releases" / "r1" / "variables.jsonl", a)
    write_jsonl(root / "metadata" / "releases" / "r2" / "variables.jsonl", b)
    return root


def entries(result):
    return {e["from"]: e for e in result["tables"][0]["in_both"]}


def test_compare_text():
    assert diff.compare_text("a", "a") == "same"
    assert diff.compare_text("Dark - Not Lighted", "dark – not lighted") == "text_only"
    assert diff.compare_text("IC-9 How important", "IC-7 How important") == "reference_only"
    assert diff.compare_text("R's age", "R's age (FC A-2b)") == "reference_only"
    assert diff.compare_text("Ever married", "Ever married to an opposite-sex spouse") == "changed"


def test_diff_categories(repo):
    result = diff.diff(Repo.load(repo), "r1", "r2")
    t = result["tables"][0]
    e = entries(result)
    assert e["same"]["relations"] == ["same_item"] and e["same"]["changes"] == {}
    assert e["light"]["relations"] == ["labels_changed"]
    assert e["light"]["changes"]["codes"]["relabeled"] == [{"code": 9, "from": "Unknown", "to": "Reported as Unknown"}]
    assert e["weather"]["relations"] == ["codes_changed"]
    assert [c["code"] for c in e["weather"]["changes"]["codes"]["added"]] == [99]
    assert e["dash"]["relations"] == ["same_item"]
    assert e["dash"]["changes"]["codes"]["relabeled_text_only"][0]["code"] == 2
    assert e["item"]["relations"] == ["universe_changed"]           # label and question: reference only
    assert e["item"]["changes"]["label"]["how"] == "reference_only"
    assert e["kind"]["name_case_changed"] and e["kind"]["relations"] == ["codes_changed"]
    assert e["kind"]["changes"]["codes"]["kind_changed"][0]["from"][0] == "unresolved"
    assert t["only_in_from"] == ["Wgt2017", "gone"] and t["only_in_to"] == ["Wgt2024", "new"]
    assert [(c["from"], c["to"]) for c in t["rename_candidates"]] == [("Wgt2017", "Wgt2024")]   # not gone -> new


def test_proposals(repo, tmp_path):
    r = Repo.load(repo)
    result = diff.diff(r, "r1", "r2")
    n_links, n_hist = diff.write_proposals(r, result, tmp_path / "out")
    links = [json.loads(l) for l in (tmp_path / "out" / "links.jsonl").read_text().splitlines()]
    assert n_links == len(links) == 6
    assert all(l["origin"]["rule"] == "release_diff" for l in links)
    hists = {h["name"]: h for h in map(json.loads, (tmp_path / "out" / "histories.jsonl").read_text().splitlines())}
    assert sorted(hists) == ["light", "weather"]
    assert hists["weather"]["attributes"] == [{"label": "Clear", "codes": [1, 1]},
                                              {"label": "Unknown", "codes": [9, 99]}]      # same answer, new code
    assert hists["light"]["attributes"][1:] == [{"label": "Unknown", "codes": [9, None]},
                                                {"label": "Reported as Unknown", "codes": [None, 9]}]
    assert hists["light"]["periods"] == [{"from": 2017, "to": 2017}, {"from": 2024, "to": 2024}]


def test_never_writes_metadata(repo):
    r = Repo.load(repo)
    with pytest.raises(SystemExit):
        diff.write_proposals(r, diff.diff(r, "r1", "r2"), repo / "metadata" / "proposals")


def test_cli(repo, capsys):
    assert main(["diff", str(repo), "r1", "r2"]) == 0
    out = capsys.readouterr().out
    assert "toy: r1 -> r2" in out and "rename candidate: Wgt2017 -> Wgt2024" in out
    assert "codes relabeled: 9 'Unknown' -> 'Reported as Unknown'" in out
    with pytest.raises(SystemExit):
        main(["diff", str(repo), "r1", "nope"])


def test_merge_candidate(tmp_path):
    dataset = dict(DATASET, releases=[
        {"id": "r1", "label": "R1", "status": "superseded", "sources": ["cb"]},
        {"id": "r2", "label": "R2", "status": "current", "sources": ["cb"]}])
    codes = [V(1, "Very biased"), V(2, "Somewhat"), V(3, "Not biased")]
    root = make_repo(tmp_path, dataset=dataset, variables=[], groups=[], corrections=[])
    write_jsonl(root / "metadata" / "releases" / "r1" / "variables.jsonl",
                [rec("r1", "strvbias", "Bias", codes), rec("r1", "strvbiasy", "Bias (year)", codes)])
    write_jsonl(root / "metadata" / "releases" / "r2" / "variables.jsonl", [rec("r2", "strvbias", "Bias", codes)])
    t = diff.diff(Repo.load(root), "r1", "r2")["tables"][0]
    assert t["merge_split_candidates"] == [{"kind": "merge", "from": "strvbiasy", "to": "strvbias",
                                            "score": t["merge_split_candidates"][0]["score"]}]

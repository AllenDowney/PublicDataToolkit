"""Tests for the agent view (`pdt views`) and labeled search (`pdt search`)."""

import json
from pathlib import Path

import pytest

from pdt import views
from pdt.check import Repo
from pdt.cli import main
from pdt.search import Index, search
from test_check import DATASET, GROUPS, VARIABLES, make_repo, write_jsonl

UPSTREAM = {"origin": "upstream_package", "source": "cb"}
SUBJECT = {"id": "subject-opinion", "kind": "subject", "label": "Opinion", "ordered": False,
           "members": [{"name": "q1"}, {"name": "q2"}], "origin": UPSTREAM}
TOPICS = [
    {"target": {"variable": "q1"}, "kind": "topic", "value": "Views", "origin": UPSTREAM},
    {"target": {"variable": "q2"}, "kind": "topic", "value": "Mood",
     "origin": {"origin": "model", "model": "m", "date": "2026-11-19", "reviewed": False}},
]
DERIVED = [{"target": {"variable": "q1"}, "property": "scale_signature", "value": "yes_no",
            "rule": "sig", "rule_version": "0.1"}]


@pytest.fixture
def repo_dir(tmp_path):
    root = make_repo(tmp_path, groups=GROUPS + [SUBJECT])
    write_jsonl(root / "metadata" / "annotations" / "topics.jsonl", TOPICS)
    write_jsonl(root / "metadata" / "derived" / "scale_signature.jsonl", DERIVED)
    return root


def index_of(root):
    return Index.from_repo(Repo.load(root))


def names(result):
    return [rec["name"] for _, _, rec in result.matches]


@pytest.mark.parametrize("filt, label, expected", [
    ({}, "complete", ["q1", "q2"]),
    ({"release": "r1"}, "complete", ["q1", "q2"]),
    ({"name": "Q1"}, "complete", ["q1"]),
    ({"group": "battery-q1"}, "complete_by_rule", ["q1", "q2"]),
    ({"subject": "opinion"}, "complete", ["q1", "q2"]),
    ({"group": "subject-opinion"}, "complete", ["q1", "q2"]),
    ({"topic": "views"}, "approximate", ["q1"]),
    ({"topic": "Mood"}, "approximate", ["q2"]),
    ({"derived": {"scale_signature": "yes_no"}}, "complete_by_rule", ["q1"]),
    ({"field": {"pointer": "/label", "equals": "Question two"}}, "complete", ["q2"]),
    ({"text": "agree"}, "approximate", ["q1"]),
    ({"subject": "Opinion", "text": "this"}, "approximate", ["q2"]),
])
def test_search_labels(repo_dir, filt, label, expected):
    result = search(index_of(repo_dir), filt)
    assert result.label == label
    assert names(result) == expected
    assert result.n_in_scope == 2
    assert result.releases == ["r1"]


def test_search_records_rule_versions(repo_dir):
    result = search(index_of(repo_dir), {"derived": {"scale_signature": "yes_no"}})
    assert result.rule_versions == {"sig": "0.1"}


def test_field_made_by_rule_is_complete_by_rule(tmp_path):
    variables = [dict(VARIABLES[0], provenance={
        "record": {"origin": "publisher", "source": "cb"},
        "fields": {"measure": {"origin": "rule", "rule": "m", "rule_version": "1"}}})]
    root = make_repo(tmp_path, variables=variables, groups=[], corrections=[])
    result = search(index_of(root), {"field": {"pointer": "/measure", "equals": "x"}})
    assert result.label == "complete_by_rule"


def test_unknown_filter_key(repo_dir):
    with pytest.raises(ValueError):
        search(index_of(repo_dir), {"topics": "x"})
    with pytest.raises(ValueError):
        search(index_of(repo_dir), {"subject": "no such subject"})


def test_search_sees_corrected_text(repo_dir):
    assert names(search(index_of(repo_dir), {"text": "this one"})) == ["q2"]


def test_build_writes_index_skill_and_shards(repo_dir):
    manifest = views.build(repo_dir)
    agent = repo_dir / "agent"
    assert (agent / "index.md").exists() and (agent / "SKILL.md").exists()
    kinds = {s["kind"] for s in manifest["shards"]}
    assert kinds == {"table", "group", "scale", "subject", "topic"}
    index = (agent / "index.md").read_text()
    assert "Do not edit" in index and manifest["inputs_sha256"] in index
    assert "[Subject: Opinion](shards/subject/opinion.txt)" in index


def test_shards_rerun_to_the_same_set(repo_dir):
    """Every shard is a filter result: rerunning its filter gives the same variables and label."""
    manifest = views.build(repo_dir)
    idx = index_of(repo_dir)
    for shard in manifest["shards"]:
        result = search(idx, shard["filter"])
        assert result.label == shard["completeness"]
        for f in shard["files"]:
            lines = (repo_dir / "agent" / f["path"]).read_text().splitlines()
            if f["form"] == "jsonl":
                head = json.loads(lines[0])["shard"]
                assert head["filter"] == shard["filter"]
                assert [json.loads(line)["name"] for line in lines[1:]] == names(result)
            else:
                body = [line for line in lines if line and not line.startswith("#")]
                assert [line.split(" | ")[0].rstrip("*") for line in body] == names(result)


def test_corrections_applied_and_marked(repo_dir):
    views.build(repo_dir)
    shard = repo_dir / "agent" / "shards" / "table" / "r1"
    records = [json.loads(line) for line in shard.with_suffix(".jsonl").read_text().splitlines()[1:]]
    q2 = records[1]
    assert q2["questions"][0]["text"] == "And this one?"
    assert q2["view"]["corrected"][0]["original"] == "And this?"
    assert "q2* |" in shard.with_suffix(".txt").read_text()
    assert "q2-text" not in (repo_dir / "metadata" / "releases" / "r1" / "variables.jsonl").read_text()
    assert "Corrections applied" in (repo_dir / "agent" / "index.md").read_text()


def test_correction_skipped_when_original_is_gone(tmp_path):
    variables = [VARIABLES[0], dict(VARIABLES[1], questions=[{"text": "Fixed upstream"}])]
    root = make_repo(tmp_path, variables=variables)
    assert index_of(root).corrected == {}


def test_large_shards_split_into_parts(repo_dir, monkeypatch):
    many = [dict(VARIABLES[1], name=f"v{i}", label="x" * 400) for i in range(30)]
    make_repo(repo_dir, variables=many, groups=[], corrections=[])
    monkeypatch.setattr(views, "MAX_TOKENS", 1500)
    manifest = views.build(repo_dir)
    table = next(s for s in manifest["shards"] if s["kind"] == "table")
    parts = [f for f in table["files"] if f["form"] == "jsonl"]
    assert len(parts) > 1
    assert all(f["tokens"] <= 1500 for f in parts)
    assert sum(f["variables"] for f in parts) == 30


def test_is_current(repo_dir):
    assert not views.is_current(repo_dir)
    views.build(repo_dir)
    assert views.is_current(repo_dir)
    write_jsonl(repo_dir / "metadata" / "groups.jsonl", [])
    assert not views.is_current(repo_dir)


def test_build_refuses_a_hand_made_agent_dir(repo_dir):
    (repo_dir / "agent").mkdir()
    (repo_dir / "agent" / "notes.md").write_text("mine")
    with pytest.raises(FileExistsError):
        views.build(repo_dir)


def test_tables_and_waves(tmp_path):
    dataset = dict(DATASET, releases=[{"id": "r1", "label": "R1", "status": "current", "sources": ["cb"],
                                       "tables": [{"id": "a", "label": "A", "sources": ["cb"]},
                                                  {"id": "b", "label": "B", "sources": ["cb"]}]}])
    root = make_repo(tmp_path, dataset=dataset, variables=[], groups=[], corrections=[])
    avail = [{"wave": w} for w in (2000, 2002, 2004, 2008)]
    write_jsonl(root / "metadata" / "releases" / "r1" / "a" / "variables.jsonl",
                [dict(VARIABLES[0], availability=avail + [{"wave": 2010, "form": "X"}])])
    write_jsonl(root / "metadata" / "releases" / "r1" / "b" / "variables.jsonl",
                [dict(VARIABLES[0], availability=[{"wave": 2006}])])
    views.build(root)
    a = (root / "agent" / "shards" / "table" / "r1-a.txt").read_text()
    assert "a.q1 | 2000-2004,2008-2010; forms X | yes_no" not in a   # no derived here
    assert "a.q1 | 2000-2004,2008-2010; forms X | - |" in a
    b = (root / "agent" / "shards" / "table" / "r1-b.txt").read_text()
    assert "b.q1 | 2006 |" in b


def test_wave_summary_all():
    rec = {"availability": [{"wave": 1}, {"wave": 2}]}
    assert views.wave_summary(rec, [1, 2]) == "1-2 (all)"
    assert views.wave_summary({}, [1, 2]) == "-"


def test_cli(repo_dir, capsys):
    assert main(["views", str(repo_dir)]) == 0
    assert main(["search", str(repo_dir), "--filter", '{"subject": "Opinion"}']) == 0
    out = capsys.readouterr().out
    result = json.loads(out[out.index("{"):])
    assert result["completeness"] == "complete" and result["count"] == 2


GSS = Path(__file__).resolve().parents[3] / "pdt-gss"


@pytest.mark.skipif(not (GSS / "dataset.yaml").exists(), reason="pdt-gss not checked out")
def test_gss_abortion_items_are_complete():
    result = search(index_of(GSS), {"subject": "Abortion"})
    assert result.label == "complete"
    assert set(names(result)) >= {"abany", "abdefect", "abnomore", "abhlth", "abpoor", "abrape", "absingle"}


def test_line_falls_back_to_notes():
    assert views.line_question({"notes": "Coded from the police report."}) == "[notes] Coded from the police report."
    assert views.line_question({}) == ""


def test_line_prefers_description_to_notes():
    rec = {"description": "The year of the crash.", "notes": "Additional information."}
    assert views.line_question(rec) == "[description] The year of the crash."


def test_compact_availability_by_form():
    avail = [{"wave": 1986, "n": 5}, {"wave": 1987}, {"wave": 1988, "form": "A"},
             {"wave": 1989, "form": "A"}, {"wave": 1989, "form": "C"}]
    assert views.compact_availability(avail, [1986, 1987, 1988, 1989]) == {
        "all": "1986-1987", "form A": "1988-1989", "form C": "1989"}


def test_codes_fall_back_to_provenance_codes():
    rule = {"origin": "rule", "rule": "ext_missing", "rule_version": "0.2", "note": "long"}
    values = [{"code": 1, "label": "yes", "kind": "valid"},
              {"code": ".d", "label": "dk", "kind": "missing", "missing_types": ["dk"]},
              {"code": ".i", "label": "iap", "kind": "missing", "missing_types": ["inap"]}]
    out, shared = views.compact_values(values, rule)
    assert shared == "rule:ext_missing@0.2"
    assert all("origin" not in v for v in out)
    values[2]["origin"] = {"origin": "hand", "author": "Tester", "date": "2026-11-19"}
    out, shared = views.compact_values(values, rule)
    assert shared is None
    assert [v.get("origin") for v in out] == [None, "rule:ext_missing@0.2", "hand:Tester"]


def test_jsonl_records_are_compact(repo_dir):
    views.build(repo_dir)
    lines = (repo_dir / "agent" / "shards" / "table" / "r1.jsonl").read_text().splitlines()
    head = json.loads(lines[0])["shard"]
    assert head["full_records"] == ["metadata/releases/r1/variables.jsonl"]
    q1 = json.loads(lines[1])
    assert "provenance" not in q1
    assert q1["origins"] == {"record": "publisher:cb", "codes": "publisher:cb"}
    assert all("origin" not in v for v in q1["values"])

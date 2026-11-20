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
    assert "a.q1 | all 2000-2004,2008; form X 2010 (not 2006) | - |" in a
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


def test_wave_summary_names_gaps_and_forms():
    waves = [1985, 1986, 1987, 1988, 1989]
    rec = {"availability": [{"wave": 1985}, {"wave": 1987}, {"wave": 1988, "form": "A"},
                            {"wave": 1988, "form": "C"}, {"wave": 1989, "form": "A"},
                            {"wave": 1989, "form": "C"}]}
    assert views.wave_summary(rec, waves) == "all 1985,1987; form A,C 1988-1989 (not 1986)"
    rec = {"availability": [{"wave": w} for w in (1985, 1987)]}
    assert views.wave_summary(rec, waves) == "1985,1987 (not 1986)"


def test_available_filter(tmp_path):
    rule_avail = {"origin": "rule", "rule": "avail_rule", "rule_version": "2"}
    variables = [
        dict(VARIABLES[0], availability=[{"wave": 1987}, {"wave": 1988, "form": "A"}]),
        dict(VARIABLES[1], availability=[{"wave": 1988, "form": "B"}]),
        dict(VARIABLES[0], name="q3", availability=[{"wave": 1988}]),
        dict(VARIABLES[0], name="q4", availability=[{"wave": 1988, "form": "A"}],
             provenance={"record": {"origin": "publisher", "source": "cb"},
                         "fields": {"availability": rule_avail}}),
    ]
    root = make_repo(tmp_path, variables=variables, groups=[], corrections=[])
    idx = index_of(root)
    full = search(idx, {"available": {"wave": 1988, "form": "A"}})
    assert names(full) == ["q1", "q3", "q4"]          # q3: no form, so everyone in 1988
    assert full.label == "complete_by_rule" and full.rule_versions == {"avail_rule": "2"}
    only = search(idx, {"available": {"wave": 1988, "form": "A"}, "name": "q1"})
    assert only.label == "complete_by_rule"           # the label covers the whole scope
    (tmp_path / "b").mkdir()
    no_rule = make_repo(tmp_path / "b", variables=variables[:3], groups=[], corrections=[])
    result = search(index_of(no_rule), {"available": {"wave": 1988}})
    assert names(result) == ["q1", "q2", "q3"] and result.label == "complete"
    with pytest.raises(ValueError):
        search(idx, {"available": {"form": "A"}})


EVAL_KEYS = Path(__file__).resolve().parents[2] / "eval" / "keys"


def key_check(repo, key_file, filt, label):
    """The filter finds every hit in the key, and nothing the key marks as a miss.

    The repo can cover more than the key (the full GSS against a 50-variable key), so
    names the key doesn't mention are ignored, and the search is scoped to its release.
    """
    import yaml
    key = yaml.safe_load((EVAL_KEYS / key_file).read_text())
    hits = {i["name"] for i in key["items"] if i["status"] == "hit"}
    allowed = hits | {i["name"] for i in key["items"] if i["status"] == "neutral"}
    known = {i["name"] for i in key["items"]}
    release = next(iter(key["scope"].values()))["release"]
    result = search(index_of(repo), {"release": str(release), **filt})
    found = set(names(result))
    assert hits <= found
    assert found & known <= allowed
    assert result.label == label


@pytest.mark.skipif(not (EVAL_KEYS / "gss_ballot_a_1988.yaml").exists() or not (GSS / "dataset.yaml").exists(),
                    reason="eval keys or pdt-gss missing")
def test_gss_ballot_a_1988_matches_eval_key():
    key_check(GSS, "gss_ballot_a_1988.yaml", {"available": {"wave": 1988, "form": "A"}}, "complete")


ANES = GSS.parent / "pdt-anes-cdf"


@pytest.mark.skipif(not (EVAL_KEYS / "anes_therm_1978.yaml").exists() or not (ANES / "dataset.yaml").exists(),
                    reason="eval keys or pdt-anes-cdf missing")
def test_anes_thermometers_1978_matches_eval_key():
    key_check(ANES, "anes_therm_1978.yaml",
              {"derived": {"scale_signature": "thermometer"}, "available": {"wave": 1978}},
              "complete_by_rule")


def test_release_order_and_scoped_shards(tmp_path):
    dataset = dict(DATASET, releases=[
        {"id": "new", "label": "New", "status": "current", "sources": ["cb"]},
        {"id": "old", "label": "Old", "status": "superseded", "sources": ["cb"]}])
    assert views.release_order(dataset) == ["old", "new"]
    root = make_repo(tmp_path, dataset=dataset, variables=[], groups=GROUPS, corrections=[])
    for rel in ("new", "old"):
        write_jsonl(root / "metadata" / "releases" / rel / "variables.jsonl",
                    [dict(v, release=rel) for v in VARIABLES])
    manifest = views.build(root)
    group = next(s for s in manifest["shards"] if s["kind"] == "group")
    assert group["filter"] == {"release": "new", "group": "battery-q1"}
    assert group["count"] == 2 and "current release (new)" in group["basis"]
    tables = [s for s in manifest["shards"] if s["kind"] == "table"]
    assert [s["filter"] for s in tables] == [{"release": "new"}, {"release": "old"}]


def test_release_order_natural():
    rel = lambda i, s="current": {"id": i, "label": i, "status": s, "sources": ["cb"]}
    assert views.release_order({"releases": [rel("2024"), rel("2017")]}) == ["2017", "2024"]
    assert views.release_order({"releases": [rel("r10"), rel("r2")]}) == ["r2", "r10"]
    assert views.release_order({"releases": [rel("7224r3a"), rel("7224r3", "superseded")]}) == ["7224r3", "7224r3a"]


def c8(result):
    return [f for f in result.failures if f.startswith("C8")]


def test_c8_views_current(repo_dir):
    from pdt.check import run as check
    from pdt import site, export as dd
    assert len(c8(check(repo_dir))) == 2                           # agent/ and export/; docs/ absent is fine
    views.build(repo_dir)
    site.build(repo_dir)
    dd.build(repo_dir)
    assert c8(check(repo_dir)) == []
    write_jsonl(repo_dir / "metadata" / "derived" / "scale_signature.jsonl", [])
    stale = c8(check(repo_dir))
    assert len(stale) == 3 and all("out of date" in f for f in stale)
    views.build(repo_dir)
    site.build(repo_dir)
    dd.build(repo_dir)
    (repo_dir / "docs" / "variables" / "q1.html").unlink()
    assert c8(check(repo_dir)) == ["C8: docs/ is missing 1 generated file(s), e.g. variables/q1.html; "
                                   "run `make views`"]


def test_across_releases_file(tmp_path):
    dataset = dict(DATASET, releases=[
        {"id": "r1", "label": "R1", "status": "superseded", "sources": ["cb"]},
        {"id": "r2", "label": "R2", "status": "current", "sources": ["cb"]}])
    root = make_repo(tmp_path, dataset=dataset, variables=[], groups=[], corrections=[])
    write_jsonl(root / "metadata" / "releases" / "r1" / "variables.jsonl", [dict(VARIABLES[0], release="r1")])
    write_jsonl(root / "metadata" / "releases" / "r2" / "variables.jsonl",
                [dict(VARIABLES[0], release="r2", name="q1new")])
    write_jsonl(root / "metadata" / "links.jsonl", [
        {"from": {"release": "r1", "name": "q1"}, "to": {"release": "r2", "name": "q1new"},
         "relations": ["same_item", "renamed"], "origin": {"origin": "publisher", "source": "cb"}}])
    manifest = views.build(root)
    assert manifest["across_releases"] == [{"path": "variables.txt", "variables": 1,
                                            "tokens": manifest["across_releases"][0]["tokens"]}]
    text = (root / "agent" / "variables.txt").read_text()
    assert "q1 r1 → q1new r2 | " in text
    assert "## Across releases" in (root / "agent" / "index.md").read_text()
    from pdt.check import run
    (root / "agent" / "variables.txt").unlink()
    assert any("C8" in f and "agent/" in f for f in run(root).failures)


def test_runs_of_range_waves():
    assert views.runs({"2017-2019", "2022-2023"}, ["2017-2019", "2022-2023"]) == "2017-2019 to 2022-2023"
    assert views.runs({1, 2}, [1, 2]) == "1-2"


def test_c8_docs_only_where_it_exists(repo_dir):
    import shutil
    from pdt.check import run as check
    from pdt import site, export as dd
    views.build(repo_dir)
    dd.build(repo_dir)
    r = check(repo_dir)
    assert c8(r) == [] and any("docs/ doesn't exist here" in x for x in r.reports)
    (repo_dir / ".gitignore").write_text("data/\ndocs/\n")
    r = check(repo_dir)
    assert c8(r) == [] and any("docs/ is in .gitignore" in x and "not built here" in x for x in r.reports)
    site.build(repo_dir)
    write_jsonl(repo_dir / "metadata" / "derived" / "scale_signature.jsonl", [])
    views.build(repo_dir)
    dd.build(repo_dir)
    assert [f for f in c8(check(repo_dir)) if "docs/" in f]                  # present, so checked, and stale
    shutil.rmtree(repo_dir / "docs")
    assert c8(check(repo_dir)) == []

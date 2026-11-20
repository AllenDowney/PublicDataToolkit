"""Tests for the scorer and the answer keys. Run: pytest eval/"""

import json
import sys
from pathlib import Path

import yaml

EVAL = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL))
import score  # noqa: E402


def test_score_items_counts_neutral_as_neither():
    key = [{"dataset": "gss", "table": None, "name": "relig", "status": "hit"},
           {"dataset": "gss", "table": None, "name": "attend", "status": "hit"},
           {"dataset": "gss", "table": None, "name": "year", "status": "neutral"}]
    reported = {("gss", None, "relig"), ("gss", None, "year"), ("gss", None, "abany")}
    s = score.score_items(key, reported)
    assert s["recall"] == 0.5
    assert s["precision"] == 0.5            # relig of {relig, abany}; year ignored
    assert s["misses"] == ["gss/attend"]
    assert s["false_positives"] == ["gss/abany"]


def test_key_of_ignores_case_and_keeps_tables():
    assert score.key_of({"dataset": "nsfg", "table": "Male", "name": "RELIGION"}) == \
        ("nsfg", "male", "religion")
    assert score.key_of({"dataset": "GSS", "name": "Relig"}) == ("gss", None, "relig")


def test_keys_are_well_formed():
    for path in (EVAL / "keys").rglob("*.yaml"):
        if path.stem.endswith("_decisions"):
            continue  # an agent's or reader's decisions, the input to a key (Task 57)
        key = yaml.safe_load(path.read_text())
        stem = path.stem
        if stem.rsplit("_v", 1)[-1].isdigit():       # an earlier version: <question>_v<N>.yaml
            stem, version = stem.rsplit("_v", 1)
            assert key.get("version", 1) == int(version), path.name
        assert key["question"] == stem or stem.endswith("_" + key["question"])
        assert key["expected_label"] in {"complete", "complete_by_rule", "approximate"}
        seen = set()
        for item in key["items"]:
            assert item["status"] in {"hit", "neutral"}
            k = score.key_of(item)
            assert k not in seen, k
            seen.add(k)


def test_keys_name_real_variables():
    """Every key item is a variable in the dataset repo next to this one, when it's there."""
    repos = {"gss": "pdt-gss", "anes-cdf": "pdt-anes-cdf", "nsfg": "pdt-nsfg"}
    base = EVAL.parents[1]
    names = {}
    for ds, repo in repos.items():
        for f in (base / repo / "metadata/releases").rglob("variables.jsonl"):
            table = f.parent.name if ds == "nsfg" else None
            for line in f.read_text().splitlines():
                names.setdefault(ds, set()).add((ds, table, json.loads(line)["name"].lower()))
    for path in (EVAL / "keys").glob("*.yaml"):
        for item in yaml.safe_load(path.read_text())["items"]:
            if item["dataset"] in names:
                assert score.key_of(item) in names[item["dataset"]], (path.name, item)


def test_runs_are_scored_against_their_key_version():
    """A run set up before keys had versions is scored against version 1; a run that records
    key_version against that version (catalog_sadness: v1 in catalog_sadness_v1.yaml, v2 in
    catalog_sadness.yaml)."""
    v1, v2 = score.load_key("catalog_sadness"), score.load_key("catalog_sadness", 2)
    assert v1.get("version", 1) == 1 and v2["version"] == 2
    assert {i["dataset"] for i in v1["items"]} <= {"gss", "yrbss", "brfss"}
    assert "nhis" in {i["dataset"] for i in v2["items"]} and "gss" not in v2["covers"]
    assert score.load_key("religion_full").get("version", 1) == 1

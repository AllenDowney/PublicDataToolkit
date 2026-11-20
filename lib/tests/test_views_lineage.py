"""Agent views for a dataset with many releases: table shards across releases, one line per lineage."""

import json

from pdt import views
from test_check import DATASET, VARIABLES, make_repo, write_jsonl


def many_releases(root, n=4):
    ids = [f"r{i}" for i in range(1, n + 1)]
    dataset = dict(DATASET, releases=[{"id": r, "label": r, "status": "superseded" if r != ids[-1] else "current",
                                       "sources": ["cb"]} for r in ids])
    make_repo(root, dataset=dataset, variables=[dict(VARIABLES[0], release="r1")], groups=[], corrections=[])
    for r in ids[1:]:
        q1 = dict(VARIABLES[0], release=r)
        if r in ids[2:]:
            q1["values"] = [{"code": 1, "label": "yes", "kind": "valid"}]
        write_jsonl(root / "metadata" / "releases" / r / "variables.jsonl", [q1])
    write_jsonl(root / "metadata" / "links.jsonl", [
        {"from": {"release": a, "name": "q1"}, "to": {"release": b, "name": "q1"},
         "relations": ["same_item", "codes_changed"] if b == "r3" else ["same_item"],
         "origin": {"origin": "rule", "rule": "r", "source": "cb"}} for a, b in zip(ids, ids[1:])])
    return root


def test_across_releases_when_there_are_many(tmp_path):
    root = many_releases(tmp_path)
    manifest = views.build(root, release_shards=2)
    tables = [s for s in manifest["shards"] if s["kind"] == "table"]
    assert len(tables) == 1 and tables[0]["filter"] == {"table": None, "release": "all"}
    txt = (root / "agent" / "shards" / "table" / "all.txt").read_text()
    assert "q1 | r1–r2: q1 → [codes_changed, same_item] r3–r4: q1 | Question one" in txt
    entry = json.loads((root / "agent" / "shards" / "table" / "all.jsonl").read_text().splitlines()[1])
    assert [r["releases"] for r in entry["runs"]] == ["r1–r2", "r3–r4"] and entry["changes"][0]["at"] == "r3"
    index = (root / "agent" / "index.md").read_text()
    assert "more than 2 (the views option `--release-shards`)" in index
    assert all(f["tokens"] < views.MAX_TOKENS for s in tables for f in s["files"])


def test_per_release_shards_by_default(tmp_path):
    root = many_releases(tmp_path)
    manifest = views.build(root)
    assert sorted(s["filter"]["release"] for s in manifest["shards"] if s["kind"] == "table") == ["r1", "r2", "r3", "r4"]
    assert "--release-shards" not in (root / "agent" / "index.md").read_text()

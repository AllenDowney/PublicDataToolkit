"""Tests for pdt search's scope, names and paging, the `waves` filter, and waves in the catalog (Task 53)."""

import json

import pytest

from pdt import catalog
from pdt.cli import main
from pdt.search import default_releases, page, wave_matcher
from test_catalog import PUB, var
from test_check import DATASET, make_repo, write_jsonl


def two_release_repo(root, ident="g"):
    """Releases old (superseded) and new (current), both holding q1..q5; q5 asked in 2024 only."""
    root.mkdir()
    ds = dict(DATASET, id=ident, releases=[
        {"id": "old", "label": "old", "status": "superseded", "sources": ["cb"]},
        {"id": "new", "label": "new", "status": "current", "sources": ["cb"]}])
    make_repo(root, dataset=ds, variables=[], groups=[], corrections=[])
    for rel in ("old", "new"):
        recs = [dict(var(f"q{i}", f"Question {i}", waves=(2022,) if i < 5 else (2024,)), dataset=ident, release=rel)
                for i in range(1, 6)]
        write_jsonl(root / "metadata" / "releases" / rel / "variables.jsonl", recs)
    (root / "metadata" / "releases" / "r1" / "variables.jsonl").unlink()
    (root / "metadata" / "releases" / "r1").rmdir()
    return root


def run_cli(capsys, *args):
    assert main(["search", *args]) == 0
    return json.loads(capsys.readouterr().out)


def test_default_releases():
    assert default_releases({"releases": [{"id": "a", "status": "superseded"}, {"id": "b", "status": "current"}]}) == ["b"]
    assert default_releases({"releases": [{"id": "a"}, {"id": "b"}]}) == ["a", "b"]


def test_cli_defaults_to_the_current_release(tmp_path, capsys):
    root = two_release_repo(tmp_path / "pdt-g")
    out = run_cli(capsys, str(root), "--filter", '{"text": "question"}')
    assert out["releases"] == ["new"] and out["count"] == 5 and out["n_in_scope"] == 5
    assert any("--release all" in n for n in out["notes"])
    everything = run_cli(capsys, str(root), "--filter", '{"text": "question"}', "--release", "all")
    assert everything["releases"] == ["new", "old"] and everything["count"] == 10
    old = run_cli(capsys, str(root), "--filter", '{"text": "question"}', "--release", "old")
    assert old["releases"] == ["old"] and old["count"] == 5


def test_cli_release_in_filter_and_option_conflict(tmp_path):
    root = two_release_repo(tmp_path / "pdt-g")
    with pytest.raises(SystemExit):
        main(["search", str(root), "--filter", '{"release": "old"}', "--release", "new"])


def test_names_and_paging(tmp_path, capsys):
    root = two_release_repo(tmp_path / "pdt-g")
    out = run_cli(capsys, str(root), "--filter", '{"text": "question"}', "--names")
    assert out["names"] == ["q1", "q2", "q3", "q4", "q5"] and "results" not in out
    assert out["completeness"] == "approximate" and out["count"] == 5
    pg = run_cli(capsys, str(root), "--filter", '{"text": "question"}', "--names", "--limit", "2", "--offset", "3")
    assert pg["names"] == ["q4", "q5"] and pg["count"] == 5
    assert pg["page"] == {"offset": 3, "limit": 2, "returned": 2, "more": False}
    both = run_cli(capsys, str(root), "--filter", '{"name": "q1"}', "--names", "--release", "all")
    assert sorted(both["names"]) == ["new:q1", "old:q1"]


def test_names_print_on_one_line(tmp_path, capsys):
    root = two_release_repo(tmp_path / "pdt-g")
    main(["search", str(root), "--filter", '{"text": "question"}', "--names"])
    text = capsys.readouterr().out
    assert ' "names": ["q1", "q2", "q3", "q4", "q5"]' in text


def test_waves_filter(tmp_path, capsys):
    root = two_release_repo(tmp_path / "pdt-g")
    out = run_cli(capsys, str(root), "--filter", '{"waves": 2024}', "--names")
    assert out["names"] == ["q5"] and out["completeness"] == "complete"
    out = run_cli(capsys, str(root), "--filter", '{"waves": {"from": 2020, "to": 2023}}', "--names")
    assert out["names"] == ["q1", "q2", "q3", "q4"]
    out = run_cli(capsys, str(root), "--filter", '{"waves": [2023, 2024]}', "--names")
    assert out["names"] == ["q5"]
    with pytest.raises(ValueError):
        wave_matcher({"since": 2020})


def test_page():
    assert page(list(range(5)), 2, 1) == ([1, 2], {"offset": 1, "limit": 2, "returned": 2, "more": True})
    assert page(list(range(5)))[0] == [0, 1, 2, 3, 4]


def test_catalog_carries_and_filters_waves(tmp_path):
    a = tmp_path / "pdt-a"
    a.mkdir()
    make_repo(a, dataset=dict(DATASET, id="a"), groups=[], corrections=[],
              variables=[dict(var("sad", "Felt sad?", waves=(1996,)), dataset="a"),
                         dict(var("sadnow", "Felt sad now?", waves=(2016, 2018)), dataset="a")])
    r = catalog.search_catalog([tmp_path], {"text": "sad"})
    assert {v["names"]: v["waves"] for v in r["variables"]} == {"sad": [1996], "sadnow": [2016, 2018]}
    assert r["datasets"][0]["waves"] == [1996, 2016, 2018]
    assert {x["name"]: x["waves"] for x in r["results"]} == {"sad": [1996], "sadnow": [2016, 2018]}
    r = catalog.search_catalog([tmp_path], {"text": "sad", "waves": {"from": 2000}}, names=True)
    # Runs are over the dataset's own waves (1996, 2016, 2018 here), as in the catalog's lines.
    assert r["names"] == ["a:sadnow 2016-2018"] and r["count"] == 1
    r = catalog.search_catalog([tmp_path], {"text": "sad"}, limit=1)
    assert r["variable_count"] == 2 and len(r["variables"]) == 1 and r["page"]["more"]

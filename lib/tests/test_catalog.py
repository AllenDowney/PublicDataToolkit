"""Tests for pdt catalog and pdt search --catalog."""

import json

import pytest
import yaml

from pdt import catalog
from pdt.cli import main
from test_check import DATASET, VARIABLES, make_repo, write_jsonl

PUB = {"origin": "publisher", "source": "cb"}


def repo(root, ident, variables, metadata="ship", groups=()):
    root.mkdir()
    ds = dict(DATASET, id=ident, title=ident.upper(), terms=dict(DATASET["terms"], metadata=metadata))
    make_repo(root, dataset=ds, variables=[dict(v, dataset=ident) for v in variables], groups=list(groups),
              corrections=[])
    return root


def var(name, label, question=None, waves=(2020,)):
    r = {"dataset": "x", "release": "r1", "name": name, "label": label, "provenance": {"record": PUB},
         "availability": [{"wave": w} for w in waves]}
    if question:
        r["questions"] = [{"text": question}]
    return r


@pytest.fixture
def home(tmp_path):
    repo(tmp_path / "pdt-a", "a", [var("sad", "Felt sad?", waves=(2018, 2020)),
                                   var("povcol", "Give college aid", "Aid for the disadvantaged?"),
                                   var("marital", "Marital status")],
         groups=[{"id": "subject-mood", "kind": "subject", "label": "Mood", "members": [{"name": "sad"}],
                  "origin": PUB}])
    repo(tmp_path / "pdt-b", "b", [var("DEPRESS", "Ever told you had a depressive disorder")])
    repo(tmp_path / "pdt-c", "c", [var("q1", "Sad or hopeless")], metadata="unknown")
    (tmp_path / "pdt-private").mkdir()
    (tmp_path / "pdt-private" / "secret.txt").write_text("not for the catalog")
    (tmp_path / "other").mkdir()
    return tmp_path


def test_build(home, tmp_path):
    out = tmp_path / "catalog-out"
    m = catalog.build([home], out)
    assert [d["id"] for d in m["datasets"]] == ["a", "b"]
    reasons = {x["path"].rsplit("/", 1)[1]: x["reason"] for x in m["left_out"]}
    assert "terms.metadata is 'unknown'" in reasons["pdt-c"] and "no dataset.yaml" in reasons["pdt-private"]
    assert "other" not in reasons
    lines = (out / "agent" / "a.txt").read_text()
    assert "r1.sad | 2018-2020 (all) | Felt sad? | -" in lines
    rows = [json.loads(l) for l in (out / "catalog.jsonl").read_text().splitlines()]
    assert {(r["dataset"], r["name"]) for r in rows} == {("a", "sad"), ("a", "povcol"), ("a", "marital"),
                                                         ("b", "DEPRESS")}
    index = (out / "agent" / "index.md").read_text()
    assert "## Left out" in index and "pdt-c" in index
    assert "secret" not in (out / "index.html").read_text() and "<h2>Left out</h2>" in (out / "index.html").read_text()


def test_build_refuses_a_foreign_directory(home, tmp_path):
    out = tmp_path / "taken"
    out.mkdir()
    (out / "notes.md").write_text("mine")
    with pytest.raises(SystemExit):
        catalog.build([home], out)


def names(result):
    return sorted((r["dataset"], r["name"]) for r in result["results"])


def test_search_text(home):
    r = catalog.search_catalog([home], {"text": ["sad", "depress"]})
    assert names(r) == [("a", "sad"), ("b", "DEPRESS")]            # not povcol's "disadvantaged"
    assert r["completeness"] == "approximate"
    assert all(x["dataset"] != "c" for x in r["results"])          # left out: terms
    r = catalog.search_catalog([home], {"text": "marital", "text_in": ["label"]})
    assert names(r) == [("a", "marital")]
    with pytest.raises(ValueError):
        catalog.search_catalog([home], {"text": "x", "text_in": ["values"]})


def test_search_subject_labels(home):
    r = catalog.search_catalog([home], {"subject": "Mood"})
    assert names(r) == [("a", "sad")] and r["completeness"] == "complete"
    assert any(n.startswith("b:") and "no match there" in n for n in r["notes"])


def test_cli(home, tmp_path, capsys):
    assert main(["catalog", str(home), "--out", str(tmp_path / "out")]) == 0
    assert main(["search", "--catalog", str(home), "--filter", '{"text": "sad"}']) == 0
    out = capsys.readouterr().out
    result = json.loads(out[out.index("{"):])
    assert result["count"] == 1 and result["completeness"] == "approximate"
    with pytest.raises(SystemExit):
        main(["search", str(home / "pdt-a"), str(home / "pdt-b"), "--filter", "{}"])


def test_output_directory_isnt_a_repo(home):
    m = catalog.build([home], home / "pdt-catalog")
    m = catalog.build([home], home / "pdt-catalog")                  # again, with its manifest in place
    assert not any(x["path"].endswith("pdt-catalog") for x in m["left_out"])

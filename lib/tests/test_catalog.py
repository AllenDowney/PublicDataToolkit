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
    assert "\nsad | 2018-2020 (all) | Felt sad? | -" in lines
    rows = [json.loads(l) for l in (out / "catalog.jsonl").read_text().splitlines()]
    assert {(r["dataset"], r["members"][0]["name"]) for r in rows} == {
        ("a", "sad"), ("a", "povcol"), ("a", "marital"), ("b", "DEPRESS")}
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


def test_chains_across_releases(tmp_path):
    """Same-meaning links join lines; a change of meaning keeps them apart, the later one under the earlier."""
    root = tmp_path / "pdt-s"
    ds = dict(DATASET, id="s", releases=[{"id": y, "label": y, "status": "current", "sources": ["cb"]}
                                         for y in ("2011", "2012", "2013")])
    root.mkdir()
    make_repo(root, dataset=ds, variables=[], groups=[], corrections=[])
    def v(rel, name, label):
        return dict(var(name, label, waves=(int(rel),)), dataset="s", release=rel)
    write_jsonl(root / "metadata" / "releases" / "2011" / "variables.jsonl", [v("2011", "DEP2", "Depressive"),
                                                                              v("2011", "ROLL", "Rollover")])
    write_jsonl(root / "metadata" / "releases" / "2012" / "variables.jsonl", [v("2012", "DEP2", "Depressive"),
                                                                              v("2012", "ROLL", "Rollover")])
    write_jsonl(root / "metadata" / "releases" / "2013" / "variables.jsonl", [v("2013", "DEP3", "Depressive"),
                                                                              v("2013", "ROLL", "Rollover type")])
    link = lambda a, an, b, bn, rels: {"from": {"release": a, "name": an}, "to": {"release": b, "name": bn},
                                       "relations": rels, "origin": PUB}
    write_jsonl(root / "metadata" / "links.jsonl", [
        link("2011", "DEP2", "2012", "DEP2", ["same_item"]), link("2012", "DEP2", "2013", "DEP3", ["renamed"]),
        link("2011", "ROLL", "2012", "ROLL", ["same_item"]), link("2012", "ROLL", "2013", "ROLL", ["codes_changed"])])
    catalog.build([root], tmp_path / "out")
    lines = [l for l in (tmp_path / "out" / "agent" / "s.txt").read_text().splitlines() if not l.startswith("#")]
    assert lines[0].startswith("DEP2 2011\u20132012 \u2192 DEP3 2013 | 2011-2013 (all) | Depressive")
    assert lines[1].startswith("ROLL 2011\u20132012 | 2011-2012 | Rollover")
    assert lines[2].startswith("  \u21b3 codes_changed: ROLL 2013 | 2013 | Rollover type")
    r = catalog.search_catalog([root], {"text": "depressive"})
    assert r["count"] == 3 and r["variable_count"] == 1
    assert r["variables"][0]["names"] == "DEP2 2011\u20132012 \u2192 DEP3 2013"
    roll = catalog.search_catalog([root], {"text": "rollover"})["variables"]
    assert [v["names"] for v in roll] == ["ROLL 2011\u20132012", "ROLL 2013"]
    assert roll[0]["related"] == [{"relations": ["codes_changed"], "direction": "to", "names": "ROLL 2013",
                                   "id": "ROLL@2013"}]


def test_metadata_tools_import_without_the_data_extra():
    """pdt views, check, search, diff, catalog and export import with pandas, numpy and pyarrow absent;
    pdt.data says what to install."""
    import subprocess, sys, textwrap
    code = textwrap.dedent("""
        import sys
        for m in ("pandas", "numpy", "pyarrow", "pyarrow.parquet"):
            sys.modules[m] = None
        import pdt.views, pdt.site, pdt.export, pdt.check, pdt.search, pdt.diff, pdt.catalog, pdt.chains
        try:
            import pdt.data
        except ImportError as e:
            assert 'publicdatatoolkit[data]' in str(e), str(e)
            print("ok")
    """)
    from pathlib import Path
    lib = Path(__file__).resolve().parents[1]
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env={"PYTHONPATH": str(lib)})
    assert out.stdout.strip() == "ok", out.stderr

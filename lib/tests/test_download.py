"""Tests for `pdt download` (sources.yaml) and `pdt.release` (the common-format data release)."""

import hashlib

import pandas as pd
import pytest
import yaml

from pdt import data, download, export, release
from test_check import DATASET, VARIABLES, make_repo


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "repo").mkdir()
    root = make_repo(tmp_path / "repo")
    remote = tmp_path / "remote"
    remote.mkdir()
    (remote / "data.csv").write_text("a,b\n1,2\n")
    (remote / "codebook.pdf").write_text("pdf bytes")
    sources = {"sources": [
        {"id": "data", "kind": "data", "url": (remote / "data.csv").as_uri(), "path": "data/raw/data.csv",
         "redistribution": "ship", "acquisition": "automated", "sha256": sha("a,b\n1,2\n")},
        {"id": "cb", "kind": "codebook", "url": (remote / "codebook.pdf").as_uri(),
         "path": "data/raw/codebook.txt", "redistribution": "ship", "acquisition": "automated"},
        {"id": "portal", "kind": "data", "redistribution": "ship", "acquisition": "manual",
         "manual_steps": "Log in and click Download.", "path": "data/raw/portal.zip"},
    ]}
    (root / "sources.yaml").write_text(yaml.safe_dump(sources))
    return root


def test_refuses_without_terms(repo, capsys):
    assert download.main([str(repo)]) == 2
    err = capsys.readouterr().err
    assert "https://example.org/terms" in err and "--accept-terms" in err
    assert not (repo / "data" / "raw" / "data.csv").exists()


def test_check_reports_without_network(repo, capsys):
    assert download.main([str(repo), "--check"]) == 1
    out = capsys.readouterr().out
    assert "missing    data" in out and "manual     portal" in out and "Log in" in out
    assert "3 source(s): 3 missing (1 to fetch by hand), 0 mismatched" in out


def test_fetch_verify_and_convert(repo, capsys, monkeypatch):
    monkeypatch.setattr(download, "pdftotext", lambda pdf, txt: txt.write_text("text of " + pdf.read_text()))
    assert download.main([str(repo), "--accept-terms"]) == 0
    out = capsys.readouterr().out
    assert (repo / "data" / "raw" / "data.csv").read_text() == "a,b\n1,2\n"
    assert (repo / "data" / "raw" / "codebook.txt").read_text() == "text of pdf bytes"
    assert "record sha256: " + sha("text of pdf bytes") in out          # no checksum recorded for cb
    assert "Log in and click Download." in out
    assert download.main([str(repo), "--check", "--source", "data"]) == 0


def test_mismatch_is_kept_aside(repo, capsys):
    (repo / "data" / "raw").mkdir(parents=True)
    (repo / "data" / "raw" / "data.csv").write_text("changed\n")
    assert download.main([str(repo), "--accept-terms", "--source", "data"]) == 1
    assert "not overwritten" in capsys.readouterr().out
    assert (repo / "data" / "raw" / "data.csv").read_text() == "changed\n"
    sources = yaml.safe_load((repo / "sources.yaml").read_text())
    sources["sources"][0]["sha256"] = "0" * 64
    (repo / "sources.yaml").write_text(yaml.safe_dump(sources))
    assert download.main([str(repo), "--accept-terms", "--source", "data", "--force"]) == 1
    assert (repo / "data" / "raw" / "data.csv.new").exists()
    assert (repo / "data" / "raw" / "data.csv").read_text() == "changed\n"


def test_unknown_source(repo):
    with pytest.raises(SystemExit):
        download.main([str(repo), "--check", "--source", "nope"])


def raw_frame():
    return pd.DataFrame({"q1": [1, 9, data.Code("."), 1], "q2": ["x", None, "y", "z"],
                         "extra": [5, 6, 7, 8]}, dtype=object)


def test_write_release_round_trip(tmp_path):
    root = make_repo(tmp_path)
    paths = release.write_release(root, lambda rel, tab, names: (raw_frame(), "cb"), log=lambda *a: None)
    assert [p.name for p in paths] == ["toy-r1.parquet"]
    ident = data.identity_of(paths[0])
    assert ident["dataset"] == "toy" and ident["release"] == "r1" and ident["source"] == "cb"
    assert ident["tokens"] == {"q1": ["."]}
    table = data.read(paths[0])
    assert "extra" not in table.columns                   # only variables with records
    codes = table["q1__code"].astype(object).tolist()
    assert data.is_null(codes[0]) and codes[1:3] == ["9", "."]


def test_write_release_needs_every_recorded_variable(tmp_path):
    root = make_repo(tmp_path)
    with pytest.raises(ValueError, match="not in the data"):
        release.write_release(root, lambda rel, tab, names: (raw_frame()[["q1"]], "cb"))


def test_export_names_the_release_files(tmp_path):
    root = make_repo(tmp_path)
    export.build(root)
    doc = yaml.safe_load((root / "export" / "data-dict" / "r1.yaml").read_text())
    assert doc["tables"][0]["source"] == {"parquet": "../../data/processed/toy-r1.parquet"}
    assert release.release_files(DATASET) == {("r1", None): "toy-r1.parquet"}


def test_read_stata_codes(tmp_path):
    from pdt import readers
    path = tmp_path / "t.dta"
    pd.DataFrame({"a": [1.0, None, 3.0], "b": [5, 6, 7], "c": [0, 0, 0]}).to_stata(path, write_index=False)
    raw = readers.read_stata(path, ["a", "b"])
    assert list(raw.columns) == ["a", "b"]
    assert raw["a"].tolist()[0] == 1 and isinstance(raw["a"].tolist()[1], data.Code)
    assert str(raw["a"].tolist()[1]) == "."
    with pytest.raises(KeyError):
        readers.read_stata(path, ["nope"])


def test_read_csv_zip(tmp_path):
    import zipfile
    from pdt import readers
    path = tmp_path / "f.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("FARS/ACCIDENT.CSV", "ST_CASE,STATE,NAME\n10001,1,Alabama\n10002,,x\n")
        z.writestr("FARS/person.csv", "ST_CASE\n1\n")
    member = readers.zip_member(path, r"(^|/)accident\.csv$")
    raw = readers.read_csv_zip(path, member, ["STATE", "ST_CASE"])
    assert list(raw.columns) == ["STATE", "ST_CASE"]
    assert raw["STATE"].tolist() == [1, None]
    with pytest.raises(KeyError):
        readers.zip_member(path, r"\.csv$")


def test_data_source(tmp_path):
    root = make_repo(tmp_path)
    sources = yaml.safe_load((root / "sources.yaml").read_text())
    sources["sources"].append({"id": "dta", "kind": "data", "format": "stata", "redistribution": "ship",
                               "acquisition": "manual", "path": "data/raw/x.dta"})
    (root / "sources.yaml").write_text(yaml.safe_dump(sources))
    ds = yaml.safe_load((root / "dataset.yaml").read_text())
    ds["releases"][0]["sources"] = ["cb", "dta"]
    (root / "dataset.yaml").write_text(yaml.safe_dump(ds))
    assert release.data_source(root, "r1")["id"] == "dta"
    with pytest.raises(ValueError):
        release.data_source(root, "r1", format="sas7bdat")


def test_release_splits_with_corrected_records(tmp_path):
    """A correction that makes an unresolved code valid moves it into the value column."""
    variables = [dict(VARIABLES[0], values=[{"code": 1, "label": "yes", "kind": "valid"},
                                            {"code": 2, "label": "", "kind": "unresolved",
                                             "origin": {"origin": "data_file", "source": "cb"}}]),
                 VARIABLES[1]]
    fix = {"id": "q1-code-2", "target": {"name": "q1", "field": "/values/1"},
           "original": variables[0]["values"][1],
           "corrected": {"code": 2, "label": "no", "kind": "valid"},
           "problem": "Code 2 is undocumented.", "evidence": [{"citation": "Data"}], "confidence": "inferred",
           "upstream": {"status": "not_filed"}, "author": "Tester", "date": "2026-11-19"}
    root = make_repo(tmp_path, variables=variables, corrections=[fix])
    raw = pd.DataFrame({"q1": [1, 2, 2], "q2": ["a", "b", "c"]}, dtype=object)
    path, = release.write_release(root, lambda rel, tab, names: (raw, "cb"), log=lambda *a: None)
    table = data.read(path)
    assert table["q1"].tolist() == [1, 2, 2] and "q1__code" not in table.columns
    ident = data.identity_of(path)
    assert ident["corrections"] == [{"id": "q1-code-2", "confidence": "inferred", "variable": "q1"}]
    assert len(ident["corrections_sha256"]) == 64


@pytest.mark.parametrize("terms, redistribution", [("unknown", "ship"), ("ship", "build-only")])
def test_release_refuses_unless_ship(tmp_path, terms, redistribution):
    root = make_repo(tmp_path, dataset=dict(DATASET, terms=dict(DATASET["terms"], data=terms)))
    sources = yaml.safe_load((root / "sources.yaml").read_text())
    sources["sources"][0]["redistribution"] = redistribution
    (root / "sources.yaml").write_text(yaml.safe_dump(sources))
    reader = lambda rel, tab, names: (raw_frame(), "cb")
    with pytest.raises(ValueError, match="ship"):
        release.write_release(root, reader, log=lambda *a: None)
    assert not (root / "data" / "processed").exists() or not any((root / "data" / "processed").iterdir())
    path, = release.write_release(root, reader, log=lambda *a: None, local=True)
    assert "ship" in data.identity_of(path)["local_only"]

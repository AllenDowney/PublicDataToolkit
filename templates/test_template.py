"""Render the template and check the result. Run: pytest templates/

Needs the `copier` command (set $COPIER, or have it on PATH); skipped without it.
pdt check runs with this interpreter, which needs the library's dependencies.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

TEMPLATES = Path(__file__).resolve().parent
TOOLKIT = TEMPLATES.parent          # copier.yml is at the toolkit's root
LIB = TOOLKIT / "lib"
COPIER = os.environ.get("COPIER") or shutil.which("copier")

ANSWERS = {
    "dataset_id": "testdata", "title": "Test Data: A Survey", "publisher_name": "Example Agency",
    "publisher_url": "https://example.org", "dataset_url": "https://example.org/testdata",
    "terms_url": "https://example.org/terms", "release_id": "2024", "release_label": "Test Data 2024",
    "form_label": "ballot",
}

pytestmark = pytest.mark.skipif(not COPIER, reason="copier not installed")


def render(dest, **extra):
    # --vcs-ref HEAD: the working tree, uncommitted changes included. Without it, Copier
    # copies the latest tag, which would test the last release instead of this code.
    args = [COPIER, "copy", "--defaults", "--quiet", "--vcs-ref", "HEAD"]
    for k, v in {**ANSWERS, **extra}.items():
        args += ["-d", f"{k}={v}"]
    subprocess.run(args + [str(TOOLKIT), str(dest)], check=True, capture_output=True)
    return dest


def run(cmd, cwd):
    env = dict(os.environ, PYTHONPATH=str(LIB))
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)


def pdt_check(repo):
    return run([sys.executable, "-m", "pdt", "check", "."], repo)


def test_fresh_repo_fails_only_on_the_unfetched_source(tmp_path):
    repo = render(tmp_path / "pdt-testdata")
    assert run([sys.executable, "build/build_records.py"], repo).returncode == 0
    out = pdt_check(repo).stdout
    failures = [line for line in out.splitlines() if line.startswith("FAIL")]
    # C8 (Task 31): a fresh repo has no generated views yet. docs/ may be built for Pages
    # instead of committed (Task 47), so a missing docs/ is reported, not failed.
    assert failures == ["FAIL   C6: source testdata-codebook has no sha256 or fetched_on",
                        "FAIL   C8: agent/ hasn't been generated; run `make views`",
                        "FAIL   C8: export/data-dict/ hasn't been generated; run `make views`"], out
    dataset = yaml.safe_load((repo / "dataset.yaml").read_text())
    assert dataset["title"] == "Test Data: A Survey"          # quoted, despite the colon
    assert {dataset["terms"][k] for k in ("data", "documentation", "metadata")} == {"unknown"}


def test_repo_passes_once_source_is_fetched_and_terms_decided(tmp_path):
    repo = render(tmp_path / "pdt-testdata")
    run([sys.executable, "build/build_records.py"], repo)
    sources = yaml.safe_load((repo / "sources.yaml").read_text())
    sources["sources"][0].update(path="data/raw/codebook.txt", fetched_on="2026-11-19",
                                 sha256="0" * 64, bytes=1, redistribution="ship")
    (repo / "sources.yaml").write_text(yaml.safe_dump(sources, sort_keys=False))
    dataset = yaml.safe_load((repo / "dataset.yaml").read_text())
    dataset["terms"].update(data="ship", documentation="ship", metadata="ship",
                            llm_processing="allowed", reviewed_by="Test", reviewed_on="2026-11-19")
    (repo / "dataset.yaml").write_text(yaml.safe_dump(dataset, sort_keys=False))
    assert run([sys.executable, "-m", "pdt", "views", "."], repo).returncode == 0     # C8
    result = pdt_check(repo)
    assert result.returncode == 0, result.stdout


def test_source_id_follows_kind_and_url_sets_acquisition(tmp_path):
    repo = render(tmp_path / "pdt-testdata", source_kind="data", source_format="stata",
                  source_url="https://example.org/f.dta")
    src = yaml.safe_load((repo / "sources.yaml").read_text())["sources"][0]
    assert src["id"] == "testdata-data"
    assert src["acquisition"] == "automated" and src["url"] == "https://example.org/f.dta"
    assert "documents" not in src                              # a data file documents nothing


def test_download_check_runs_without_network(tmp_path):
    repo = render(tmp_path / "pdt-testdata")
    result = run([sys.executable, "scripts/download.py", "--check"], repo)
    # It runs and reports the source. Its exit status (0, or 1 when a source is missing) is
    # pdt.download's business, not the template's.
    assert result.returncode in (0, 1) and "Traceback" not in result.stderr, result.stderr
    assert "testdata-codebook" in result.stdout


def test_hand_facts_need_a_real_author(tmp_path):
    """slice.yaml starts with author empty (Task 46: one copied author named Allen on 599 facts
    agents made); the build stops before writing a hand fact without one."""
    import importlib.util
    repo = render(tmp_path / "pdt-testdata")
    spec = yaml.safe_load((repo / "build" / "slice.yaml").read_text())
    assert spec["author"] is None and spec["date"] is None
    assert "Claude (PublicDataToolkit Task 35)" in (repo / "build" / "slice.yaml").read_text()
    assert run([sys.executable, "build/build_records.py"], repo).returncode == 0   # no hand facts yet
    module = importlib.util.spec_from_file_location("build_records", repo / "build" / "build_records.py")
    build = importlib.util.module_from_spec(module)
    module.loader.exec_module(build)
    with pytest.raises(SystemExit, match="fill in `author`"):
        build.hand_origin(spec)
    filled = dict(spec, author="Claude (PublicDataToolkit Task 99)", date="2026-11-19")
    assert build.hand_origin(filled) == {"origin": "hand", "author": "Claude (PublicDataToolkit Task 99)",
                                         "date": "2026-11-19"}
    record = build.build_variable("q1", {"measure": "ordinal"}, {}, "2024", filled)
    assert record["provenance"]["fields"]["measure"]["author"] == "Claude (PublicDataToolkit Task 99)"


def test_make_data_runs_the_build_and_skips_a_release_without_data(tmp_path):
    # `data` is a target (and phony, since data/ exists): it runs scripts/build_data.py, which
    # skips a release whose data source isn't there yet instead of failing.
    repo = render(tmp_path / "pdt-testdata")
    run([sys.executable, "build/build_records.py"], repo)
    record = {"dataset": "testdata", "release": "2024", "name": "x",
              "provenance": {"record": {"origin": "hand", "author": "Test", "date": "2026-11-20"}}}
    (repo / "metadata" / "releases" / "2024" / "variables.jsonl").write_text(json.dumps(record) + "\n")
    (repo / "data").mkdir(exist_ok=True)
    dry = run(["make", "-n", "data", f"PYTHON={sys.executable}"], repo)
    assert "scripts/build_data.py" in dry.stdout, dry.stdout + dry.stderr
    result = run([sys.executable, "scripts/build_data.py"], repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "skipped 2024" in result.stdout, result.stdout


def test_extract_refuses_without_data_and_extracts_with_it(tmp_path):
    # scripts/extract.py (Task 19's wrapper, generalized): it reads dataset.yaml's releases,
    # refuses with the fix before reading anything, then hands off to pdt.extract.
    pd = pytest.importorskip("pandas")
    pytest.importorskip("pyarrow")
    repo = render(tmp_path / "pdt-testdata")
    run([sys.executable, "build/build_records.py"], repo)
    record = {"dataset": "testdata", "release": "2024", "name": "x", "storage_type": "integer",
              "values": [{"code": 1, "label": "Yes", "kind": "valid"}, {"code": 2, "label": "No", "kind": "valid"},
                         {"code": 8, "label": "Don't know", "kind": "missing", "missing_types": ["dk"]}],
              "provenance": {"record": {"origin": "hand", "author": "Test", "date": "2026-11-20"}}}
    (repo / "metadata" / "releases" / "2024" / "variables.jsonl").write_text(json.dumps(record) + "\n")
    extract = [sys.executable, "scripts/extract.py"]

    result = run(extract + ["--release", "2024", "--vars", "x", "--out", "x.csv"], repo)
    assert result.returncode != 0 and "data/processed/ has no data files" in result.stderr, result.stderr

    sys.path.insert(0, str(LIB))
    from pdt.check import Repo
    from pdt.release import write_one
    write_one(repo, Repo.load(repo), "2024", None, pd.DataFrame({"x": [1, 2, 8, 1]}), "testdata-codebook",
              log=lambda *a: None)
    result = run(extract + ["--release", "1999", "--vars", "x", "--out", "x.csv"], repo)
    assert result.returncode != 0 and "No release '1999'" in result.stderr and "2024" in result.stderr
    result = run(extract + ["--vars", "x", "--out", "x.csv"], repo)
    assert result.returncode != 0 and "Name a release" in result.stderr
    result = run(extract + ["--release", "2024", "--table", "person", "--vars", "x", "--out", "x.csv"], repo)
    assert result.returncode != 0 and "has no table 'person'" in result.stderr

    result = run(extract + ["--release", "2024", "--vars", "x", "--missing", "dk=DK", "--codes",
                            "--out", "x.csv"], repo)
    assert result.returncode == 0, result.stdout + result.stderr
    out = pd.read_csv(repo / "x.csv", dtype=str, keep_default_na=False)
    assert out["x"].tolist() == ["1", "2", "DK", "1"], out
    assert "x__code" in out.columns
    help_out = run(extract + ["--help"], repo)
    assert help_out.returncode == 0 and "Releases in dataset.yaml" in help_out.stdout and "--vars" in help_out.stdout

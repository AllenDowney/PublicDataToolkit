"""Render the template and check the result. Run: pytest templates/

Needs the `copier` command (set $COPIER, or have it on PATH); skipped without it.
pdt check runs with this interpreter, which needs the library's dependencies.
"""

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
    assert failures == ["FAIL   C6: source testdata-codebook has no sha256 or fetched_on"], out
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

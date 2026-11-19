"""Tests for `pdt check`: a small valid repo passes, and each kind of breakage is caught."""

import json
import subprocess

import pytest
import yaml

from pdt.check import run
from pdt.cli import main

PUBLISHER = {"origin": "publisher", "source": "cb"}

DATASET = {
    "standard_version": "0.1", "id": "toy", "title": "Toy Survey",
    "publisher": {"name": "Toy Publisher"}, "url": "https://example.org/",
    "terms": {"url": "https://example.org/terms", "summary": "Test.", "data": "ship",
              "documentation": "ship", "metadata": "ship", "llm_processing": "allowed"},
    "releases": [{"id": "r1", "label": "Release 1", "status": "current", "sources": ["cb"]}],
}
SOURCES = {"sources": [{"id": "cb", "kind": "codebook", "url": "https://example.org/cb.pdf",
                        "redistribution": "ship", "acquisition": "automated",
                        "fetched_on": "2026-11-19", "sha256": "0" * 64}]}
VARIABLES = [
    {"dataset": "toy", "release": "r1", "name": "q1", "label": "Question one",
     "questions": [{"text": "Do you agree?"}],
     "values": [{"code": 1, "label": "yes", "kind": "valid"},
                {"code": 9, "label": "DK", "kind": "missing", "missing_types": ["dk"], "origin": PUBLISHER}],
     "provenance": {"record": PUBLISHER}},
    {"dataset": "toy", "release": "r1", "name": "q2", "label": "Question two",
     "questions": [{"text": "And this?"}],
     "provenance": {"record": PUBLISHER}},
]
GROUPS = [{"id": "battery-q1", "kind": "battery", "members": [{"name": "q1"}, {"name": "q2"}],
           "origin": {"origin": "rule", "rule": "shared_stem"}}]
CORRECTIONS = [{"id": "q2-text", "target": {"name": "q2", "field": "/questions/0/text"},
                "original": "And this?", "corrected": "And this one?", "problem": "Truncated.",
                "evidence": [{"citation": "Questionnaire"}], "confidence": "verified",
                "upstream": {"status": "not_filed"}, "author": "Tester", "date": "2026-11-19"}]
README = "# toy\n\n## Terms of use\n\n## How to get the data\n\n## The metadata\n\n## How to cite\n\n## How to rebuild\n"


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records))


def make_repo(root, dataset=DATASET, sources=SOURCES, variables=VARIABLES, groups=GROUPS,
              corrections=CORRECTIONS, readme=README, extensions="# Extensions\n"):
    (root / "dataset.yaml").write_text(yaml.safe_dump(dataset))
    (root / "sources.yaml").write_text(yaml.safe_dump(sources))
    write_jsonl(root / "metadata" / "releases" / "r1" / "variables.jsonl", variables)
    write_jsonl(root / "metadata" / "groups.jsonl", groups)
    write_jsonl(root / "metadata" / "corrections.jsonl", corrections)
    (root / "README.md").write_text(readme)
    (root / "CLAUDE.md").write_text("# toy\n")
    (root / "EXTENSIONS.md").write_text(extensions)
    return root


def failed(result, check):
    return [f for f in result.failures if f.startswith(check)]


def edited(records, i, **changes):
    out = [dict(r) for r in records]
    out[i].update(changes)
    return out


def test_valid_repo_passes(tmp_path):
    result = run(make_repo(tmp_path))
    assert result.ok, result.failures


def test_cli_exit_codes(tmp_path, capsys):
    assert main(["check", str(make_repo(tmp_path))]) == 0
    (tmp_path / "CLAUDE.md").unlink()
    assert main(["check", str(tmp_path)]) == 1


def test_c1_schema_violation(tmp_path):
    bad = edited(VARIABLES, 0, values=[{"code": 9, "label": "DK", "kind": "missing", "missing_types": ["dk"]}])
    assert failed(run(make_repo(tmp_path, variables=bad)), "C1")


def test_c2_duplicate_name(tmp_path):
    assert failed(run(make_repo(tmp_path, variables=VARIABLES + [VARIABLES[0]])), "C2")


def test_c2_group_member_without_record(tmp_path):
    groups = [dict(GROUPS[0], members=[{"name": "q1"}, {"name": "q3"}])]
    assert failed(run(make_repo(tmp_path, groups=groups)), "C2")


def test_c2_unknown_source(tmp_path):
    bad = edited(VARIABLES, 1, provenance={"record": {"origin": "publisher", "source": "nowhere"}})
    assert failed(run(make_repo(tmp_path, variables=bad)), "C2")


def test_c6_source_without_checksum(tmp_path):
    sources = {"sources": [{k: v for k, v in SOURCES["sources"][0].items() if k != "sha256"}]}
    assert failed(run(make_repo(tmp_path, sources=sources)), "C6")


def test_c6_reports_unreviewed_model_output(tmp_path):
    model = {"origin": "model", "model": "m", "date": "2026-11-19", "reviewed": False}
    bad = edited(VARIABLES, 1, provenance={"record": PUBLISHER, "fields": {"questions": model}})
    result = run(make_repo(tmp_path, variables=bad))
    assert result.ok
    assert "C6: 1 unreviewed model-made facts" in result.reports


def test_c7_stale_correction(tmp_path):
    corrections = [dict(CORRECTIONS[0], original="And that?")]
    assert failed(run(make_repo(tmp_path, corrections=corrections)), "C7")


def test_c9_model_output_without_llm_permission(tmp_path):
    terms = dict(DATASET["terms"], llm_processing="not_allowed")
    model = {"origin": "model", "model": "m", "date": "2026-11-19", "reviewed": True}
    bad = edited(VARIABLES, 1, provenance={"record": model})
    assert failed(run(make_repo(tmp_path, dataset=dict(DATASET, terms=terms), variables=bad)), "C9")


def test_c9_build_only_file_tracked(tmp_path):
    sources = {"sources": SOURCES["sources"] + [
        {"id": "raw", "kind": "data", "path": "data/raw/toy.csv", "redistribution": "build-only",
         "acquisition": "manual", "manual_steps": "Ask."}]}
    root = make_repo(tmp_path, sources=sources)
    (root / "data" / "raw").mkdir(parents=True)
    (root / "data" / "raw" / "toy.csv").write_text("x\n")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    assert failed(run(root), "C9")


def test_c10_undocumented_extension(tmp_path):
    bad = edited(VARIABLES, 1, extensions={"toy": {"module": "Core"}})
    assert failed(run(make_repo(tmp_path, variables=bad)), "C10")
    assert run(make_repo(tmp_path, variables=bad, extensions="| `toy.module` | ... |\n")).ok


@pytest.mark.parametrize("section", ["Terms of use", "How to cite"])
def test_c11_missing_readme_section(tmp_path, section):
    assert failed(run(make_repo(tmp_path, readme=README.replace(f"## {section}\n", ""))), "C11")


def test_c2_reserved_name(tmp_path):
    bad = edited(VARIABLES, 1, name="q2__code")
    corrections = [dict(CORRECTIONS[0], target={"name": "q1", "field": "/questions/0/text"}, original="Do you agree?")]
    assert failed(run(make_repo(tmp_path, variables=bad, groups=[], corrections=corrections)), "C2")


# ------------------------------------------------------------------ tables

def tabled(table, name, text="Q?"):
    return {"dataset": "toy", "release": "r1", "table": table, "name": name, "label": name,
            "questions": [{"text": text}], "provenance": {"record": PUBLISHER}}


TABLED_DATASET = dict(DATASET, releases=[{
    "id": "r1", "label": "Release 1", "status": "current", "sources": ["cb"],
    "tables": [{"id": "female", "label": "Female respondents", "key": ["CASEID"]},
               {"id": "male", "label": "Male respondents", "key": ["CASEID"]},
               {"id": "preg", "label": "Pregnancies", "key": ["CASEID", "PREGORDR"],
                "references": [{"columns": ["CASEID"], "table": "female"}]}]}])
TABLED = {
    "female": [tabled("female", "CASEID"), tabled("female", "MARSTAT", "Married?")],
    "male": [tabled("male", "CASEID"), tabled("male", "MARSTAT", "Married?")],
    "preg": [tabled("preg", "CASEID"), tabled("preg", "PREGORDR")],
}


def make_tabled_repo(root, dataset=TABLED_DATASET, tables=TABLED, groups=(), corrections=()):
    make_repo(root, dataset=dataset, variables=[], groups=list(groups), corrections=list(corrections))
    for table, records in tables.items():
        write_jsonl(root / "metadata" / "releases" / "r1" / table / "variables.jsonl", records)
    return root


def test_tables_valid_repo_passes(tmp_path):
    assert run(make_tabled_repo(tmp_path)).ok


def test_tables_same_name_in_two_tables_is_fine(tmp_path):
    result = run(make_tabled_repo(tmp_path, groups=[
        {"id": "g", "kind": "other", "members": [{"name": "MARSTAT", "table": "female"}],
         "origin": {"origin": "rule", "rule": "r"}}]))
    assert result.ok, result.failures


def test_tables_ambiguous_reference_fails(tmp_path):
    groups = [{"id": "g", "kind": "other", "members": [{"name": "MARSTAT"}], "origin": {"origin": "rule", "rule": "r"}}]
    assert any("name the table" in f for f in failed(run(make_tabled_repo(tmp_path, groups=groups)), "C2"))


def test_tables_record_in_wrong_table_fails(tmp_path):
    tables = dict(TABLED, male=[tabled("female", "CASEID")])
    assert failed(run(make_tabled_repo(tmp_path, tables=tables)), "C2")


def test_tables_bad_key_and_reference_fail(tmp_path):
    rel = dict(TABLED_DATASET["releases"][0])
    rel["tables"] = [dict(t) for t in rel["tables"]]
    rel["tables"][2]["references"] = [{"columns": ["CASEID"], "table": "nowhere"}]
    rel["tables"][0]["key"] = ["NOPE"]
    result = run(make_tabled_repo(tmp_path, dataset=dict(TABLED_DATASET, releases=[rel])))
    assert any("unknown table" in f for f in result.failures)
    assert any("key column NOPE" in f for f in result.failures)


def test_tables_correction_with_table(tmp_path):
    good = {"id": "c", "target": {"name": "MARSTAT", "table": "male", "field": "/questions/0/text"},
            "original": "Married?", "corrected": "Are you married?", "problem": "Short.",
            "evidence": [{"citation": "Questionnaire"}], "confidence": "verified",
            "upstream": {"status": "not_filed"}, "author": "Tester", "date": "2026-11-19"}
    assert run(make_tabled_repo(tmp_path, corrections=[good])).ok
    stale = dict(good, original="Married now?")
    assert failed(run(make_tabled_repo(tmp_path, corrections=[stale])), "C7")

"""Tests for `pdt check`: a small valid repo passes, and each kind of breakage is caught."""

import json
import subprocess

import pytest
import yaml

from pdt.check import run as run_all
from pdt.cli import main

PUBLISHER = {"origin": "publisher", "source": "cb"}


def run(root):
    """Every check but C8: these repos have no generated views (C8's tests are in test_views.py)."""
    return run_all(root, views=False)

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
    root = make_repo(tmp_path)
    assert main(["check", str(root)]) == 1                       # C8: no views generated yet
    assert main(["views", str(root)]) == 0
    assert main(["check", str(root)]) == 0
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


def repo_with_build_only_file(tmp_path, remote=False):
    sources = {"sources": SOURCES["sources"] + [
        {"id": "raw", "kind": "data", "path": "data/raw/toy.csv", "redistribution": "build-only",
         "acquisition": "manual", "manual_steps": "Ask."}]}
    root = make_repo(tmp_path, sources=sources)
    (root / "data" / "raw").mkdir(parents=True)
    (root / "data" / "raw" / "toy.csv").write_text("x\n")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    if remote:
        subprocess.run(["git", "remote", "add", "origin", "https://example.org/toy.git"], cwd=root, check=True)
    return root


def test_c9_build_only_file_tracked_without_remote_is_reported(tmp_path):
    result = run(repo_with_build_only_file(tmp_path))
    assert not failed(result, "C9")
    assert any(r.startswith("C9: data/raw/toy.csv is build-only") for r in result.reports)


def test_c9_build_only_file_tracked_with_remote_fails(tmp_path):
    assert failed(run(repo_with_build_only_file(tmp_path, remote=True)), "C9")


def test_c9_metadata_tracked_with_unknown_terms(tmp_path):
    terms = dict(DATASET["terms"], metadata="unknown")
    root = make_repo(tmp_path, dataset=dict(DATASET, terms=terms))
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    result = run(root)
    assert not failed(result, "C9")
    assert any("terms.metadata is unknown" in r and "no git remote" in r for r in result.reports)
    subprocess.run(["git", "remote", "add", "origin", "https://example.org/toy.git"], cwd=root, check=True)
    assert failed(run(root), "C9")


def test_c9_model_output_fails_without_remote(tmp_path):
    terms = dict(DATASET["terms"], llm_processing="not_allowed")
    model = {"origin": "model", "model": "m", "date": "2026-11-19", "reviewed": True}
    root = make_repo(tmp_path, dataset=dict(DATASET, terms=terms),
                     variables=edited(VARIABLES, 1, provenance={"record": model}))
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    assert failed(run(root), "C9")


def subdir(tmp_path, name):
    path = tmp_path / name
    path.mkdir()
    return path


def test_c6_questions_expected_only_of_surveys(tmp_path):
    no_questions = [{k: v for k, v in r.items() if k != "questions"} for r in VARIABLES]
    result = run(make_repo(tmp_path, variables=no_questions))
    assert "C6: 2 of 2 records have no questions" in result.reports          # no kind: a survey
    result = run(make_repo(subdir(tmp_path, "b"), dataset=dict(DATASET, kind="administrative"), variables=no_questions))
    assert not any("questions" in r for r in result.reports)
    assert "C6: 2 of 2 records have no description" in result.reports


NOTICE = "This site provides applications using data that has been modified for use from its original source."


def test_c11_terms_notice_in_readme(tmp_path):
    dataset = dict(DATASET, terms=dict(DATASET["terms"], notice=NOTICE))
    assert any("terms.notice" in f for f in run(make_repo(tmp_path, dataset=dataset)).failures)
    # Wrapped and quoted in the terms section, it matches.
    quoted = "> This site provides applications using data that has been\n> modified for use from its original source."
    readme = README.replace("## Terms of use\n", "## Terms of use\n\n" + quoted + "\n")
    assert not run(make_repo(subdir(tmp_path, "b"), dataset=dataset, readme=readme)).failures
    # In another section, it doesn't.
    readme = README.replace("## How to cite\n", "## How to cite\n\n" + NOTICE + "\n")
    assert any("terms.notice" in f for f in run(make_repo(subdir(tmp_path, "c"), dataset=dataset, readme=readme)).failures)


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


# ------------------------------------------------------- Task 25 rules

def test_missing_code_needs_an_origin(tmp_path):
    bare = [{"code": 9, "label": "DK", "kind": "missing", "missing_types": ["dk"]}]
    bad = edited(VARIABLES, 1, values=bare)
    assert failed(run(make_repo(tmp_path, variables=bad)), "C1")
    with_default = edited(VARIABLES, 1, values=bare, provenance={"record": PUBLISHER, "codes": PUBLISHER})
    assert run(make_repo(tmp_path, variables=with_default)).ok


def test_unresolved_code_needs_an_origin(tmp_path):
    bad = edited(VARIABLES, 1, values=[{"code": -7, "kind": "unresolved"}])
    assert failed(run(make_repo(tmp_path, variables=bad)), "C1")


def test_new_fields_and_missing_types(tmp_path):
    good = edited(VARIABLES, 1, description="What it measures.", variable_type="recode",
                  values=[{"code": 99, "label": "Reported as Unknown", "kind": "missing", "missing_types": ["unknown"],
                           "origin": PUBLISHER},
                          {"code": ".z", "label": "see codebook", "kind": "missing", "missing_types": ["unspecified"],
                           "origin": PUBLISHER}])
    assert run(make_repo(tmp_path, variables=good)).ok


def test_conditional_reference(tmp_path):
    rel = dict(TABLED_DATASET["releases"][0])
    rel["tables"] = [dict(t) for t in rel["tables"]]
    rel["tables"][2]["references"] = [{"columns": ["CASEID"], "table": "female", "when": {"column": "PREGORDR", "in": [1]}}]
    assert run(make_tabled_repo(tmp_path, dataset=dict(TABLED_DATASET, releases=[rel]))).ok
    rel["tables"][2]["references"] = [{"columns": ["CASEID"], "table": "female", "when": {"column": "NOPE", "in": [1]}}]
    assert any("condition column NOPE" in f for f in run(make_tabled_repo(tmp_path, dataset=dict(TABLED_DATASET, releases=[rel]))).failures)


# ------------------------------------------------------------- histories

HISTORY = {"id": "q1", "name": "q1", "names": [{"name": "q1", "waves": {"from": 1975}}],
           "periods": [{"from": 1975, "to": 2017}, {"from": 2018}],
           "attributes": [{"label": "Unknown", "codes": [9, None]},
                          {"label": "Reported as Unknown", "codes": [None, 9]}],
           "origin": {"origin": "publisher", "source": "cb", "location": "p. 78"}}


def test_history_valid(tmp_path):
    root = make_repo(tmp_path)
    write_jsonl(root / "metadata" / "histories.jsonl", [HISTORY])
    assert run(root).ok


def test_history_codes_must_match_periods(tmp_path):
    root = make_repo(tmp_path)
    bad = dict(HISTORY, attributes=[{"label": "Unknown", "codes": [9]}])
    write_jsonl(root / "metadata" / "histories.jsonl", [bad, HISTORY])
    assert any("1 codes for 2 periods" in f for f in failed(run(root), "C1"))


def test_history_ids_unique(tmp_path):
    root = make_repo(tmp_path)
    write_jsonl(root / "metadata" / "histories.jsonl", [HISTORY, HISTORY])
    assert any("duplicate id" in f for f in failed(run(root), "C1"))



def renumbered_repo(root, links):
    """Two releases that renumber their items, as the YRBSS combined datasets do."""
    root.mkdir(parents=True, exist_ok=True)
    dataset = dict(DATASET, releases=[dict(DATASET["releases"][0], id="r1"),
                                      dict(DATASET["releases"][0], id="r2", label="Release 2")])
    def rec(release, name, text):
        return {"dataset": "toy", "release": release, "name": name, "questions": [{"text": text}],
                "provenance": {"record": PUBLISHER}}
    make_repo(root, dataset=dataset, variables=[rec("r1", "q25", "Sad?"), rec("r1", "q26", "Suicide?"),
                                                 rec("r1", "q1", "Agree?"), rec("r1", "q2", "And this?")],
              groups=[], corrections=[])
    write_jsonl(root / "metadata" / "releases" / "r2" / "variables.jsonl",
                [rec("r2", "q26", "Sad?"), rec("r2", "q27", "Suicide?")])
    rule = {"origin": "rule", "rule": "crosswalk", "source": "cb"}
    write_jsonl(root / "metadata" / "links.jsonl",
                [{"from": {"release": "r1", "name": a}, "to": {"release": "r2", "name": b},
                  "relations": ["same_item", "renamed"] if a != b else ["same_item"], "origin": rule}
                 for a, b in links])
    return root


def name_reuse(result):
    return [r for r in result.reports if r.startswith("C2: warning")]


def test_c2_warns_on_name_reuse_across_releases(tmp_path):
    result = run(renumbered_repo(tmp_path, [("q25", "q26"), ("q26", "q27")]))
    assert result.ok, result.failures
    assert name_reuse(result) == [
        "C2: warning: q26 is in r1 and r2, but the two aren't linked; r1/q26 is linked to r2/q27, "
        "so the name may mean a different item in each release"]


def test_c2_no_warning_when_the_name_is_linked_or_nothing_is(tmp_path):
    assert not name_reuse(run(renumbered_repo(tmp_path / "a", [("q26", "q26")])))
    assert not name_reuse(run(renumbered_repo(tmp_path / "b", [])))       # no links: nothing to compare
    # Only one direction linked elsewhere is enough: r2's q26 is linked from r1's q25.
    assert len(name_reuse(run(renumbered_repo(tmp_path / "c", [("q25", "q26")])))) == 1

"""Tests for the DAAF data-source skill export (`pdt export daaf`, export/daaf/)."""

import json
import re

import pytest
import yaml

from pdt import daaf
from pdt.check import run
from pdt.cli import main
from test_check import CORRECTIONS, DATASET, GROUPS, VARIABLES, make_repo, write_jsonl

SKILL = "test-data-source-toy"

# DAAF's canonical order (agent_reference/DATA_SOURCE_SKILL_TEMPLATE.md), with our Terms of Use
# after the Value Encoding blockquote and the optional sections between 10 and 11.
ORDER = ["# TOY Data Source Reference", "> **CRITICAL: Value Encoding**", "## Terms of Use",
         "## What is the Toy Survey?", "## Reference File Structure", "## Decision Trees",
         "## Quick Reference:", "## Data Access", "## Common Pitfalls", "## Related Data Sources",
         "## Topic Index"]


@pytest.fixture
def repo_dir(tmp_path):
    return make_repo(tmp_path, groups=GROUPS + [{"id": "subject-health", "kind": "subject", "label": "Health",
                                                  "members": [{"name": "q1"}],
                                                  "origin": {"origin": "publisher", "source": "cb"}}])


def export(root, **kw):
    kw.setdefault("today", "2026-11-20")
    return daaf.build(root, "test", **kw)


def skill_text(root):
    return (root / "export" / "daaf" / SKILL / "SKILL.md").read_text()


def frontmatter(text):
    assert text.startswith("---\n")
    return yaml.safe_load(text.split("---\n")[1])


def test_sections_in_daaf_order(repo_dir):
    export(repo_dir)
    text = skill_text(repo_dir)
    positions = [text.index(h) for h in ORDER]
    assert positions == sorted(positions)
    assert text.count("\n") <= daaf.SKILL_MAX_LINES
    pitfalls = text.split("## Common Pitfalls")[1].split("\n## ")[0]
    assert "| Pitfall | Issue | Solution |" in pitfalls
    assert "Corrected documentation" in pitfalls and "Missing codes read as answers" in pitfalls
    assert "`q1` null; `q1__code` = `\"9\"`" in text


def test_frontmatter_follows_daaf(repo_dir):
    export(repo_dir)
    fm = frontmatter(skill_text(repo_dir))
    assert set(fm) == {"name", "description", "metadata"}        # DAAF's allowed fields
    assert fm["name"] == SKILL and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fm["name"])
    assert 0 < len(fm["description"]) <= 1024 and not re.search("[<>]", fm["description"])
    m = fm["metadata"]
    assert all(isinstance(v, str) for v in m.values())             # DAAF: string values only
    assert m["audience"] == "any-agent" and m["domain"] == "data-source"
    assert m["skill-authored"] == m["skill-last-updated"] == "2026-11-20"
    assert m["data-provenance"] == "real" and m["pdt-license"].startswith("CC-BY-4.0")
    assert "llm_processing allowed" in m["pdt-terms"]


def test_description_fits_with_many_topics(tmp_path):
    groups = [{"id": f"subject-{i}", "kind": "subject", "label": "A long subject name " * 8 + str(i),
               "members": [{"name": "q1"}], "origin": {"origin": "publisher", "source": "cb"}} for i in range(9)]
    root = make_repo(tmp_path, groups=groups)
    export(root)
    d = frontmatter(skill_text(root))["description"]
    assert len(d) <= 1024 and "it makes no analysis decisions" in d


@pytest.mark.parametrize("term,value", [("metadata", "build-only"), ("documentation", "unknown"),
                                        ("llm_processing", "not_allowed")])
def test_refuses_when_terms_dont_allow(tmp_path, term, value):
    dataset = json.loads(json.dumps(DATASET))
    dataset["terms"][term] = value
    root = make_repo(tmp_path, dataset=dataset)
    with pytest.raises(daaf.TermsError, match=f"terms.{term} is {value}"):
        export(root)
    assert not (root / "export" / "daaf").exists()
    assert main(["export", "daaf", str(root), "--domain", "test"]) == 1


def test_notice_heads_every_file(tmp_path):
    dataset = json.loads(json.dumps(DATASET))
    dataset["terms"]["notice"] = "Source: Toy Publisher. Not endorsed."
    root = make_repo(tmp_path, dataset=dataset)
    m = export(root)
    for f in m["files"]:
        if f.endswith(".md") and "/agent/" not in f:
            assert "Source: Toy Publisher. Not endorsed." in (root / "export" / "daaf" / f).read_text(), f


def test_advice_lines():
    assert daaf.advice_lines("Analysts should drop code 9.") == ["Analysts should drop code 9."]
    assert daaf.advice_lines("> Users should not identify anyone.") == []     # quoted publisher text
    assert daaf.advice_lines('The label is "Should not be used".') == []
    assert daaf.advice_lines("The records state each code's kind.") == []
    assert daaf.advice_lines("| `x` | Should only minorities teach |") == []         # a label in a table
    assert daaf.advice_lines("## Common Pitfalls\n| Codes | Analysts should recode | x |") != []


def test_no_advice_in_generated_text(repo_dir):
    """Generated text states what the records say; it makes no analysis decisions. The copy
    of agent/ is the views' own text, tested with them."""
    m = export(repo_dir)
    for f in m["files"]:
        if f.endswith(".md") and "/agent/" not in f:
            text = (repo_dir / "export" / "daaf" / f).read_text()
            assert daaf.advice_lines(text) == [], f


def test_agent_copy_and_budget(repo_dir, monkeypatch):
    m = export(repo_dir)
    assert m["agent_copy"] == "all"
    base = repo_dir / "export" / "daaf" / SKILL / "references" / "agent"
    assert (base / "index.md").exists() and (base / "agent-guide.md").exists()
    assert not (base / "SKILL.md").exists()          # one SKILL.md per skill directory
    monkeypatch.setattr(daaf, "AGENT_BUDGET", 1)
    m = export(repo_dir)
    assert m["agent_copy"] == "part"
    assert "Part of the repository's agent views" in skill_text(repo_dir)


def test_skill_authored_is_kept(repo_dir):
    export(repo_dir, today="2026-11-20")
    export(repo_dir, today="2026-12-01")
    meta = frontmatter(skill_text(repo_dir))["metadata"]
    assert meta["skill-authored"] == "2026-11-20" and meta["skill-last-updated"] == "2026-12-01"


def daaf_failures(root):
    return [f for f in run(root).failures if "export/daaf/" in f]


def test_c8_checks_the_export_only_where_it_exists(repo_dir):
    assert daaf_failures(repo_dir) == []              # not exported: not checked
    export(repo_dir)
    assert daaf_failures(repo_dir) == [] and daaf.is_current(repo_dir)
    records = [dict(r) for r in VARIABLES]
    records[0]["label"] = "Question one, relabeled"
    write_jsonl(repo_dir / "metadata" / "releases" / "r1" / "variables.jsonl", records)
    failures = daaf_failures(repo_dir)
    assert failures and "pdt export daaf" in failures[0]
    export(repo_dir)
    (repo_dir / "export" / "daaf" / SKILL / "references" / "columns.md").unlink()
    assert any("missing 1 generated file" in f for f in daaf_failures(repo_dir))


def test_refuses_to_overwrite_hand_made(repo_dir):
    (repo_dir / "export" / "daaf").mkdir(parents=True)
    (repo_dir / "export" / "daaf" / "notes.md").write_text("mine")
    with pytest.raises(FileExistsError):
        export(repo_dir)


def test_cli(repo_dir, capsys):
    assert main(["export", "daaf", str(repo_dir), "--domain", "test", "--date", "2026-11-20"]) == 0
    assert f"{SKILL}/" in capsys.readouterr().out
    assert main(["export", "daaf", str(repo_dir), "--domain", "Bad_Domain"]) == 1


def test_corrections_and_changes_in_references(repo_dir):
    export(repo_dir)
    refs = repo_dir / "export" / "daaf" / SKILL / "references"
    dq = (refs / "data-quality.md").read_text()
    assert CORRECTIONS[0]["problem"] in dq and "And this one?" in dq
    vd = (refs / "variable-definitions.md").read_text()
    assert "battery-q1" in vd and "Health" in vd

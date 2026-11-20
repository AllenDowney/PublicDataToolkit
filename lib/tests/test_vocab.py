"""pdt.vocab matches STANDARD.md's tables and the schemas' enums, word for word."""

import json
import re
from pathlib import Path

import pytest

from pdt import vocab

ROOT = Path(__file__).resolve().parents[2]
STANDARD = ROOT / "STANDARD.md"
SCHEMA = ROOT / "schema"

pytestmark = pytest.mark.skipif(not STANDARD.exists(), reason="needs the toolkit checkout's STANDARD.md")


def table_after(header):
    """The rows of the markdown table whose header line is `header`: lists of cells."""
    lines = STANDARD.read_text().splitlines()
    i = lines.index(header)
    rows = []
    for line in lines[i + 2:]:
        if not line.startswith("|"):
            break
        rows.append([c.strip() for c in line.strip().strip("|").split(" | ")])
    return rows


def terms(cell):
    """`split_from`, `merged_into` -> ["split_from", "merged_into"]."""
    return re.findall(r"`([^`]+)`", cell)


def expand(rows):
    out = []
    for row in rows:
        for term in terms(row[0]):
            out.append((term, *row[1:]))
    return out


def test_origins():
    rows = expand(table_after("| `origin` | Meaning | Required with it |"))
    assert [(t, m) for t, m, _ in rows] == vocab.ORIGINS


def test_missing_types():
    assert expand(table_after("| Type | Meaning | Examples |")) == vocab.MISSING_TYPES


def test_completeness():
    assert expand(table_after("| Label | The result is | Allowed in the filter |")) == vocab.COMPLETENESS


def test_relations():
    assert expand(table_after("| Relation | Meaning |")) == vocab.RELATIONS


def test_enums_match_the_schemas():
    common = json.loads((SCHEMA / "common.schema.json").read_text())["$defs"]
    assert [t for t, *_ in vocab.MISSING_TYPES] == common["missing_type"]["enum"]
    assert [t for t, _ in vocab.ORIGINS] == common["origin_kind"]["enum"]
    link = (SCHEMA / "link.schema.json").read_text()
    relations = json.loads(link)["properties"]["relations"]["items"]["enum"]
    assert sorted(t for t, _ in vocab.RELATIONS) == sorted(relations)
    variable = (SCHEMA / "variable.schema.json").read_text()
    assert all(f'"{k}"' in variable for k, _ in vocab.KINDS)

"""Task 72: pdt check's speedups give the same results as before.

- The validators inline each schema's $refs (pdt.schemas.inline_refs). They must report the same
  errors, at the same paths, as validators that resolve the refs through the registry, on the
  schema examples and on broken copies of them.
- Repo.resolve looks names up in an index instead of scanning every record. It must return what
  the scan did, in the same order, and see changes to the tables.
"""

import copy
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from pdt.check import Repo
from pdt.schemas import errors, inline_refs, schema_dir, validators

EXAMPLES = Path(__file__).resolve().parents[2] / "schema" / "examples"
SCHEMA_FOR = {"dataset.yaml": "dataset.schema.json", "sources.yaml": "sources.schema.json",
              "variables.jsonl": "variable.schema.json", "groups.jsonl": "group.schema.json",
              "links.jsonl": "link.schema.json", "corrections.jsonl": "correction.schema.json",
              "annotations.jsonl": "annotation.schema.json", "derived.jsonl": "derived.schema.json",
              "histories.jsonl": "history.schema.json", "code_lists.jsonl": "code_list.schema.json"}


def registry_validators():
    """The validators as they were: refs resolved through the registry at each use."""
    schemas = {p.name: json.loads(p.read_text()) for p in schema_dir().glob("*.schema.json")}
    registry = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in schemas.values()])
    return {n: Draft202012Validator(s, registry=registry, format_checker=FormatChecker()) for n, s in schemas.items()}


def example_records():
    for path in sorted(EXAMPLES.rglob("*")):
        schema = SCHEMA_FOR.get(path.name)
        if not schema:
            continue
        if path.suffix == ".yaml":
            yield schema, yaml.safe_load(path.read_text())
        else:
            for line in path.read_text().splitlines():
                if line.strip():
                    yield schema, json.loads(line)


def broken(record):
    """Copies of a record with one thing wrong at each level: a wrong type, an unknown key, a
    bad enum value, a missing required key, and the same inside nested objects and lists."""
    out = []
    def walk(node, path):
        if isinstance(node, dict):
            for key in list(node):
                for bad in (12345, "not-an-enum-value", None, [], {"x": 1}):
                    c = copy.deepcopy(record)
                    target = c
                    for p in path:
                        target = target[p]
                    target[key] = bad
                    out.append(c)
                c = copy.deepcopy(record)
                target = c
                for p in path:
                    target = target[p]
                del target[key]
                out.append(c)
                walk(node[key], path + [key])
            c = copy.deepcopy(record)
            target = c
            for p in path:
                target = target[p]
            target["unexpected_key"] = 1
            out.append(c)
        elif isinstance(node, list) and node:
            walk(node[0], path + [0])
    walk(record, [])
    return out


def as_list(validator, record):
    return [(list(e.absolute_path), e.message) for e in errors(validator, record)]


def test_inlined_validators_report_the_same_errors():
    new, old = validators(), registry_validators()
    checked = 0
    for schema, record in example_records():
        assert as_list(new[schema], record) == as_list(old[schema], record)
        for bad in broken(record)[:400]:
            assert as_list(new[schema], bad) == as_list(old[schema], bad), (schema, bad)
            checked += 1
    assert checked > 1000


def test_inline_refs_leaves_no_refs_and_keeps_property_names():
    schemas = {p.name: json.loads(p.read_text()) for p in schema_dir().glob("*.schema.json")}
    for name in schemas:
        flat = inline_refs(schemas, name)
        assert "$ref" not in json.dumps(flat)
    flat = inline_refs(schemas, "variable.schema.json")
    assert set(flat["properties"]) == set(schemas["variable.schema.json"]["properties"])


def test_recursive_refs_raise():
    schemas = {"a.json": {"$defs": {"node": {"type": "object", "properties": {"next": {"$ref": "#/$defs/node"}}}},
                          "$ref": "#/$defs/node"}}
    with pytest.raises(RecursionError):
        inline_refs(schemas, "a.json")


def scan(repo, name, release=None, table=None):
    """Repo.resolve as it was: a scan of every record."""
    out = []
    for rel, ts in repo.tables.items():
        if release is not None and rel != release:
            continue
        for tab, recs in ts.items():
            if table is not None and tab != table:
                continue
            out += [(rel, tab, r) for r in recs if r["name"] == name]
    return out


def toy_repo():
    def rec(rel, tab, name):
        return {"release": rel, "table": tab, "name": name}
    tables = {"r1": {"a": [rec("r1", "a", "x"), rec("r1", "a", "y")], "b": [rec("r1", "b", "x")]},
              "r2": {None: [rec("r2", None, "x"), rec("r2", None, "z")]}}
    return Repo(root=Path("."), dataset={}, sources={}, variables={}, tables=tables, groups=[], links=[],
                corrections=[], histories=[], annotations=[], derived=[])


def test_resolve_matches_a_scan_in_order():
    repo = toy_repo()
    for name in ("x", "y", "z", "nope"):
        for release in (None, "r1", "r2", "r3"):
            for table in (None, "a", "b"):
                assert repo.resolve(name, release, table) == scan(repo, name, release, table)


def test_resolve_sees_changes_to_the_tables():
    repo = toy_repo()
    assert repo.resolve("w") == []
    repo.tables["r1"]["a"].append({"release": "r1", "table": "a", "name": "w"})
    assert repo.resolve("w") == scan(repo, "w")
    repo.tables = {"r9": {None: [{"release": "r9", "name": "x"}]}}
    assert repo.resolve("x") == scan(repo, "x")

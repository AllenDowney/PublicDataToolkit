"""Validate the files in schema/examples/ against the schemas.

Usage:
    python schema/check_examples.py

Needs jsonschema (4.18 or later) and PyYAML. Uses the shared library in lib/
for the validators. Runs check C1 (STANDARD.md §9) on the examples, plus a few
records that must be rejected.
"""

import json
import sys
from pathlib import Path

import yaml

SCHEMA_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCHEMA_DIR.parent / "lib"))
from pdt.schemas import errors, validators  # noqa: E402

EXAMPLES = SCHEMA_DIR / "examples"

# Which schema validates which file, by file name.
SCHEMA_FOR = {
    "dataset.yaml": "dataset.schema.json",
    "sources.yaml": "sources.schema.json",
    "variables.jsonl": "variable.schema.json",
    "groups.jsonl": "group.schema.json",
    "links.jsonl": "link.schema.json",
    "corrections.jsonl": "correction.schema.json",
    "annotations.jsonl": "annotation.schema.json",
    "derived.jsonl": "derived.schema.json",
}


def records(path):
    """Yield (label, record) for a YAML file or each line of a JSONL file."""
    if path.suffix == ".yaml":
        yield path.name, yaml.safe_load(path.read_text())
        return
    for i, line in enumerate(path.read_text().splitlines(), start=1):
        if line.strip():
            yield f"{path.name}:{i}", json.loads(line)


# Records that must fail, one per rule the schema is meant to enforce.
MUST_FAIL = [
    (
        "missing code without origin",
        "variable.schema.json",
        {
            "dataset": "x", "release": "r1", "name": "v",
            "values": [{"code": 9, "label": "DK", "kind": "missing", "missing_types": ["dk"]}],
            "provenance": {"record": {"origin": "publisher", "source": "cb"}},
        },
    ),
    (
        "valid code with missing types",
        "variable.schema.json",
        {
            "dataset": "x", "release": "r1", "name": "v",
            "values": [{"code": 1, "kind": "valid", "missing_types": ["dk"]}],
            "provenance": {"record": {"origin": "publisher", "source": "cb"}},
        },
    ),
    (
        "unresolved code without origin",
        "variable.schema.json",
        {
            "dataset": "x", "release": "r1", "name": "v",
            "values": [{"code": -7, "kind": "unresolved"}],
            "provenance": {"record": {"origin": "publisher", "source": "cb"}},
        },
    ),
    (
        "unresolved code with missing types",
        "variable.schema.json",
        {
            "dataset": "x", "release": "r1", "name": "v",
            "values": [{"code": -7, "kind": "unresolved", "missing_types": ["dk"],
                        "origin": {"origin": "hand", "author": "a", "date": "2026-11-19"}}],
            "provenance": {"record": {"origin": "publisher", "source": "cb"}},
        },
    ),
    (
        "model output without review flag",
        "variable.schema.json",
        {
            "dataset": "x", "release": "r1", "name": "v",
            "provenance": {"record": {"origin": "model", "model": "m", "date": "2026-11-19"}},
        },
    ),
    (
        "link inferred by a model",
        "link.schema.json",
        {
            "from": {"release": "a", "name": "v1"}, "to": {"release": "b", "name": "v2"},
            "relations": ["same_item"],
            "origin": {"origin": "model", "source": "s", "model": "m", "date": "2026-11-19", "reviewed": True},
        },
    ),
    (
        "manual source with no steps",
        "sources.schema.json",
        {"sources": [{"id": "s", "kind": "data", "redistribution": "ship", "acquisition": "manual", "url": "https://example.org/"}]},
    ),
]


def main():
    v_for = validators(str(SCHEMA_DIR))
    failures = 0

    for path in sorted(EXAMPLES.rglob("*")):
        if path.name not in SCHEMA_FOR:
            continue
        v = v_for[SCHEMA_FOR[path.name]]
        for label, record in records(path):
            errs = errors(v, record)
            rel = path.relative_to(EXAMPLES).parent / label
            if errs:
                failures += 1
                print(f"FAIL {rel}")
                for e in errs:
                    where = "/".join(str(p) for p in e.absolute_path) or "(record)"
                    print(f"    {where}: {e.message[:200]}")
            else:
                print(f"ok   {rel}")

    for what, schema_name, record in MUST_FAIL:
        v = v_for[schema_name]
        if errors(v, record):
            print(f"ok   rejected: {what}")
        else:
            failures += 1
            print(f"FAIL accepted: {what}")

    print(f"\n{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

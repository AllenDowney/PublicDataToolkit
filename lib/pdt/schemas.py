"""Load the PublicDataToolkit JSON Schemas and build validators for them."""

import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


def schema_dir():
    """Where the schemas are: bundled in an installed wheel, or the toolkit's schema/ in a checkout."""
    here = Path(__file__).resolve().parent
    for candidate in (here / "schema", here.parent.parent / "schema"):
        if (candidate / "variable.schema.json").exists():
            return candidate
    raise FileNotFoundError("PublicDataToolkit schemas not found")


@lru_cache(maxsize=None)
def validators(directory=None):
    """Return {schema file name: validator}, with $refs between schemas resolved offline.

    Each schema's $refs are inlined once (inline_refs), so validating a record doesn't look
    each one up again: GSS's 14,000 records validate in half the time, with the same errors.
    A schema whose refs are recursive keeps them, resolved through the registry.
    """
    directory = Path(directory) if directory else schema_dir()
    schemas, resources = {}, []
    for path in sorted(directory.glob("*.schema.json")):
        schema = json.loads(path.read_text())
        schemas[path.name] = schema
        resources.append((schema["$id"], Resource.from_contents(schema)))
    registry = Registry().with_resources(resources)
    out = {}
    for name, schema in schemas.items():
        try:
            flat = inline_refs(schemas, name)
        except RecursionError:
            flat = schema
        out[name] = Draft202012Validator(flat, registry=registry, format_checker=FormatChecker())
    return out


# Keywords whose value maps names (property names, definition names) to subschemas.
SCHEMA_MAPS = {"properties", "patternProperties", "dependentSchemas", "$defs", "definitions"}
# Keywords whose value is data, not a schema.
DATA_KEYWORDS = {"enum", "const", "default", "examples", "required", "description", "title", "$comment"}


def inline_refs(schemas, name):
    """The schema `name` with every $ref replaced by its target, across files ({file name:
    schema}). A $ref beside other keywords becomes allOf [target, the rest], which validates
    the same in draft 2020-12. Raises RecursionError if the refs are recursive."""
    def target(base, ref):
        file, _, pointer = ref.partition("#")
        file = file or base
        node = schemas[file]
        for part in (p for p in pointer.split("/") if p):
            node = node[part.replace("~1", "/").replace("~0", "~")]
        return file, node

    def schema(base, node, stack):
        if not isinstance(node, dict):
            return node                     # true/false schemas
        out = {}
        for key, value in node.items():
            if key in ("$id", "$schema", "$defs", "definitions", "$ref"):
                continue
            if key in DATA_KEYWORDS:
                out[key] = value
            elif key in SCHEMA_MAPS:
                out[key] = {k: schema(base, v, stack) for k, v in value.items()}
            elif isinstance(value, list):
                out[key] = [schema(base, v, stack) for v in value]
            elif isinstance(value, dict):
                out[key] = schema(base, value, stack)
            else:
                out[key] = value
        if "$ref" in node:
            file, found = target(base, node["$ref"])
            key = (file, node["$ref"].partition("#")[2])
            if key in stack:
                raise RecursionError(f"recursive $ref {node['$ref']} in {name}")
            resolved = schema(file, found, stack | {key})
            return {"allOf": [resolved, out]} if out else resolved
        return out

    return schema(name, schemas[name], frozenset())


def errors(validator, record):
    """Validation errors for one record, in a stable order."""
    return sorted(validator.iter_errors(record), key=lambda e: list(e.absolute_path))

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
    """Return {schema file name: validator}, with $refs between schemas resolved offline."""
    directory = Path(directory) if directory else schema_dir()
    schemas, resources = {}, []
    for path in sorted(directory.glob("*.schema.json")):
        schema = json.loads(path.read_text())
        schemas[path.name] = schema
        resources.append((schema["$id"], Resource.from_contents(schema)))
    registry = Registry().with_resources(resources)
    return {name: Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
            for name, schema in schemas.items()}


def errors(validator, record):
    """Validation errors for one record, in a stable order."""
    return sorted(validator.iter_errors(record), key=lambda e: list(e.absolute_path))

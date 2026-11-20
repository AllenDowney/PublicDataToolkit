"""Export a dataset repo's records to data-dict (https://data-dict.tidyverse.org/), spec 0.1.0.

    export/data-dict/<release>.yaml   one dictionary per release; a release's tables are its tables
    export/data-dict/LOSSES.md        what the export can't carry, counted per release
    export/data-dict/manifest.json    library version, input hash and files, as agent/ and docs/

The dictionary describes the common data format (STANDARD.md §8): for each variable, a
value column holding valid answers and, when the variable has missing or unresolved
codes, a `<name>__code` column holding them as text. So the export validates against the
release's parquet file, which each table names as its `source`
(`data/processed/<dataset>-<release>[-<table>].parquet`, written by `pdt.release`).

Mapping, and why:
- data-dict's `enum` is a string column, and our value columns hold numbers, so numeric
  codes can't be an enum: `validate-meta` fails with M01. Numeric codes become
  `number(ordinal)` (measure ordinal, with the valid codes' range) or `number(id)` (with the
  codes as examples), and their labels go in `details`. String codes are an `enum`.
- A `__code` column holds text, so it is an `enum` whose labels say the missing types.
- Measures continuous, count and weight are `number(quantity)`, with `valid_range` as the
  range or open bounds; identifiers are `number(id)` or `string`; text without examples,
  and anything else the records can't type, is listed by name only.
- Question text (corrected) is the `description`; other wordings, universe, notes,
  availability, corrections and the publisher's page go in `details`.
- Table references become `relationships`; a reference's `when` condition goes in its
  description, since a join can't carry it.
"""

import json
import shutil
from pathlib import Path

import yaml

from . import __version__
from .check import Repo
from .common_format import CODE_SUFFIX, PROCESSED, ROW, code_text, file_name
from .search import Index
from .views import inputs_hash, origin_text, sort_key, wave_summary, when_text

DIRECTORY = Path("export") / "data-dict"
SPEC_VERSION = "0.1.0"
LEARN_MORE = "https://data-dict.tidyverse.org/"
EXAMPLES = 5

MISSING_TYPES = {
    "dk": "The respondent didn't know or couldn't choose.",
    "refused": "The respondent refused.",
    "no_answer": "No answer recorded, reason unknown.",
    "inap": "Not applicable: outside the universe or skipped by design.",
    "skipped": "The respondent skipped it (self-administered modes).",
    "not_asked": "Not asked of this respondent's wave, form or interview.",
    "not_available": "Asked, but not released in this file.",
    "uncodeable": "Answered, but couldn't be coded or imputed.",
    "unknown": "The source records the value as unknown, as a police report can.",
    "unspecified": "Missing, with no reason given.",
    "other": "Any other reason; the code's label says what.",
}
QUANTITY = {"continuous", "count", "weight"}


class Literal(str):
    """A string written as a YAML block scalar."""


def _literal(dumper, value):
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="|")


class Dumper(yaml.SafeDumper):
    """No anchors or aliases: data-dict reads a repeated list as null."""

    def ignore_aliases(self, data):
        return True


Dumper.add_representer(Literal, _literal)


def code_label(value):
    """A code's label, with "(retired)" when the publisher retired it (STANDARD.md §4.2)."""
    label = value.get("label") or ""
    return f"{label} (retired)".strip() if value.get("retired") else label


def block(text):
    text = text.rstrip()
    return Literal(text + "\n") if "\n" in text else text


def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def spread(items, n=EXAMPLES):
    """Up to n items, evenly spaced, first and last included."""
    if len(items) <= n:
        return list(items)
    step = (len(items) - 1) / (n - 1)
    return [items[round(i * step)] for i in range(n)]


class Losses:
    """Counts of what the export drops or flattens, per release."""

    LABELS = {
        "variables": "variables exported",
        "numeric_code_labels": "variables whose numeric code labels went to `details` (no labeled numeric codes)",
        "missing_codes": "missing or unresolved codes, typed only in the `__code` column's labels",
        "untyped": "variables listed by name only (no type the records can support)",
        "open_ranges": "quantities exported with open range bounds (no valid range recorded)",
        "wordings": "variables with several wordings, flattened into `details`",
        "availability": "availability entries (wave by form, with n), summarized as one line of text",
        "corrections": "corrections applied; only the corrected text is exported",
        "provenance_fields": "field origins (publisher, data file, rule, hand, model) not exported",
        "conditional_references": "table references whose `when` condition is only in a description, "
                                  "and whose columns aren't marked foreign_key",
        "external_references": "references to another dataset's table, not exported",
        "groups": "groups (batteries, subjects, sections), not exported",
        "links": "links between releases, not exported",
        "annotations": "annotations (topics, aliases), not exported",
        "derived": "derived properties (scale signatures), not exported",
        "histories": "code histories, not exported",
        "release_version": "release id not expressible as data-dict `version` (needs semver or a date)",
    }

    def __init__(self):
        self.counts = {}

    def add(self, release, key, n=1):
        self.counts.setdefault(release, {}).setdefault(key, 0)
        self.counts[release][key] += n


class Exporter:
    def __init__(self, root, out):
        self.root = Path(root)
        self.out = Path(out)
        self.repo = Repo.load(self.root)
        self.index = Index.from_repo(self.repo)
        self.digest = inputs_hash(self.root)
        self.ds = self.repo.dataset
        self.losses = Losses()
        self.waves = {}
        for rel, ts in self.repo.tables.items():
            found = {a["wave"] for recs in ts.values() for rec in recs
                     for a in rec.get("availability") or [] if "wave" in a}
            self.waves[rel] = sorted(found, key=sort_key)
        hist = self.root / "metadata" / "histories.jsonl"
        self.n_histories = len([l for l in hist.read_text().splitlines() if l.strip()]) if hist.exists() else 0

    def build(self):
        if self.out.exists():
            if any(self.out.iterdir()) and not (self.out / "manifest.json").exists():
                raise FileExistsError(f"{self.out} exists and wasn't generated by pdt; not overwriting")
            shutil.rmtree(self.out)
        self.out.mkdir(parents=True)
        files = []
        for r in self.ds.get("releases", []):
            doc = self.dictionary(r)
            path = self.out / f"{r['id']}.yaml"
            header = (f"# Generated by pdt {__version__} from inputs sha256:{self.digest}.\n"
                      f"# Do not edit; run `make views`. The records in metadata/ are canonical.\n")
            path.write_text(header + yaml.dump(doc, Dumper=Dumper, sort_keys=False,
                                               allow_unicode=True, width=100))
            files.append(path.name)
        (self.out / "LOSSES.md").write_text(self.losses_md())
        files.append("LOSSES.md")
        manifest = {"pdt_version": __version__, "inputs_sha256": self.digest,
                    "dataset": self.ds.get("id"), "spec": SPEC_VERSION, "files": files,
                    "losses": self.losses.counts}
        (self.out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
        return manifest

    # ------------------------------------------------------------ dictionary

    def dictionary(self, r):
        rel = r["id"]
        ds = self.ds
        details = []
        pub = ds.get("publisher", {})
        if pub.get("name"):
            details.append(f"Publisher: {pub['name']}" + (f" ({pub['url']})" if pub.get("url") else ""))
        details.append(f"Release `{rel}`: {r.get('label', '')} ({r.get('status', '')})")
        terms = ds.get("terms", {})
        if terms.get("url"):
            details.append(f"Terms of use: {terms['url']}")
        if ds.get("citation"):
            details.append("Citation: " + " ".join(ds["citation"].split()))
        details.append(f"Exported by the PublicDataToolkit library {__version__} from this repository's "
                       "records (`metadata/`), which are canonical and hold what data-dict can't: "
                       "missing-code types, availability, wording by wave, corrections, provenance, "
                       "groups and links. See LOSSES.md.")
        doc = {"$version": SPEC_VERSION, "$learn_more": LEARN_MORE,
               "name": ds.get("id"), "label": ds.get("title")}
        if ds.get("description"):
            doc["description"] = " ".join(ds["description"].split())
        doc["details"] = block("\n\n".join(details))
        doc["origin"] = "../../build"
        self.losses.add(rel, "release_version")

        tables = r.get("tables") or [None]
        doc["tables"] = [self.table(r, t) for t in tables]
        rels = self.relationships(r)
        if rels:
            doc["relationships"] = rels
        used = sorted({t for recs in self.repo.tables[rel].values() for rec in recs
                       for v in rec.get("values") or [] for t in v.get("missing_types") or []})
        if used:
            doc["glossary"] = {f"missing type {t}": MISSING_TYPES.get(t, t) for t in used}

        for key, n in (("groups", len(self.repo.groups)), ("links", len(self.repo.links)),
                       ("annotations", len(self.repo.annotations)), ("derived", len(self.repo.derived)),
                       ("histories", self.n_histories)):
            if n:
                self.losses.add(rel, key, n)
        return doc

    def table(self, r, t):
        rel = r["id"]
        tab = t["id"] if t else None
        recs = [rec for x, y, rec in self.index.entries if x == rel and y == tab]
        out = {"name": tab or self.ds.get("id")}
        out["source"] = {"parquet": "../../" + (PROCESSED / file_name(self.ds["id"], rel, tab)).as_posix()}
        if t:
            out["label"] = t.get("label", tab)
            if t.get("description"):
                out["description"] = " ".join(t["description"].split())
        columns = [{"name": ROW, "label": "Row number",
                    "description": "The row's position in the publisher's file, from 0.",
                    "type": "number(id)", "examples": [0, 1, 2, 3, 4]}]
        key = set(t.get("key") or []) if t else set()
        # data-dict checks every foreign key against the referenced key, and can't make that
        # conditional, so a column used only in `when` references isn't marked foreign_key.
        foreign = {c for ref in (t.get("references") or []) if t and not ref.get("dataset")
                   and not ref.get("when") for c in ref["columns"]} if t else set()
        for rec in recs:
            constraints = (["primary_key"] if rec["name"] in key else []) + \
                          (["foreign_key"] if rec["name"] in foreign else [])
            columns += self.columns(rel, tab, rec, constraints)
        out["columns"] = columns
        return out

    def relationships(self, r):
        out = []
        for t in r.get("tables") or []:
            for ref in t.get("references") or []:
                if ref.get("dataset"):
                    self.losses.add(r["id"], "external_references")
                    continue
                join = " AND ".join(f"{t['id']}.{c} = {ref['table']}.{c}" for c in ref["columns"])
                rel = {"join": join, "cardinality": "many-to-one"}
                if ref.get("when"):
                    rel["description"] = f"Only for rows where {when_text(ref['when'])}."
                    self.losses.add(r["id"], "conditional_references")
                out.append(rel)
        return out

    # ------------------------------------------------------------ columns

    def columns(self, rel, tab, rec, constraints):
        name = rec["name"]
        self.losses.add(rel, "variables")
        values = rec.get("values") or []
        valid = [v for v in values if v.get("kind") == "valid"]
        nonvalid = [v for v in values if v.get("kind") != "valid"]
        col = {"name": name}
        if rec.get("label"):
            col["label"] = " ".join(rec["label"].split())
        questions = rec.get("questions") or []
        description = questions[0].get("text") if questions else rec.get("description")
        if description:
            col["description"] = block(description)

        details = []
        typed = self.value_type(rel, rec, valid)
        col.update(typed)
        if valid and typed.get("type") != "enum":
            details.append("Codes: " + "; ".join(f"{code_text(v['code'])} = {code_label(v)}" for v in valid))
            self.losses.add(rel, "numeric_code_labels")
        if len(questions) > 1:
            self.losses.add(rel, "wordings")
            for i, q in enumerate(questions[1:], 2):
                where = "; ".join(f"{k} {', '.join(map(str, q[k]))}" for k in ("waves", "forms", "modes") if q.get(k))
                details.append(f"Wording {i}" + (f" ({where})" if where else "") + f": {q.get('text', '')}")
        if questions and rec.get("description"):
            details.append(f"Description: {rec['description']}")
        for field in ("universe", "notes"):
            value = rec.get(field)
            if value:
                value = " ".join(value) if isinstance(value, list) else value
                details.append(f"{field.capitalize()}: {value}")
        if rec.get("availability"):
            details.append("Available: " + wave_summary(rec, self.waves[rel]))
            self.losses.add(rel, "availability", len(rec["availability"]))
        for a in self.index.corrected.get((rel, tab, name), []):
            details.append(f"Corrected {a['field']} ({a['confidence']}): {a['problem']}")
            self.losses.add(rel, "corrections")
        loc = rec.get("source_location") or {}
        if loc.get("url"):
            details.append(f"Publisher's documentation: {loc['url']}")
        prov = rec.get("provenance") or {}
        self.losses.add(rel, "provenance_fields", 1 + len(prov.get("fields") or {}))
        if details:
            col["details"] = block("\n\n".join(details))
        if constraints:
            col["constraints"] = constraints

        out = [col]
        if nonvalid:
            default = prov.get("codes")
            labels = {}
            for v in nonvalid:
                types = v.get("missing_types") or []
                kind = v.get("kind")
                note = ", ".join(types) if types else kind
                labels[code_text(v["code"])] = f"{v.get('label') or ''} [{note}]".strip()
                self.losses.add(rel, "missing_codes")
            classified = {origin_text(v.get("origin") or default) for v in nonvalid if v.get("origin") or default}
            code = {"name": name + CODE_SUFFIX,
                    "label": f"{col.get('label', name)}: missing code",
                    "description": (f"Why `{name}` is missing for this row: the code as published, "
                                    "as text. Null where the answer is valid. Labels end with the "
                                    "missing types in brackets."),
                    "type": "enum", "values": labels}
            if classified:
                code["details"] = "Codes classified by " + ", ".join(sorted(classified)) + "."
            out.append(code)
        return out

    def value_type(self, rel, rec, valid):
        """data-dict type keys for a value column, from its records."""
        measure = rec.get("measure")
        storage = rec.get("storage_type")
        vr = rec.get("valid_range") or {}
        numeric_codes = [v["code"] for v in valid if is_number(v["code"])]
        string_codes = [v["code"] for v in valid if isinstance(v["code"], str)]

        if string_codes and not numeric_codes and storage in (None, "string"):
            return {"type": "enum", "values": {c: code_label(v) or c for c, v in
                                               ((v["code"], v) for v in valid)}}
        rng = None
        if is_number(vr.get("min")) and is_number(vr.get("max")):
            rng = [vr["min"], vr["max"]]
        if measure in QUANTITY:
            out = {"type": "number(quantity)"}
            if rng is None and numeric_codes and len(numeric_codes) == len(valid) and len(valid) > 1:
                rng = [min(numeric_codes), max(numeric_codes)]
            if rng is None:
                rng = [float("-inf"), float("inf")]
                self.losses.add(rel, "open_ranges")
            out["range"] = rng
            if rec.get("units"):
                out["units"] = rec["units"]
            return out
        if numeric_codes and measure in ("ordinal", "categorical", None, "identifier"):
            if measure == "ordinal":
                return {"type": "number(ordinal)", "range": rng or [min(numeric_codes), max(numeric_codes)]}
            return {"type": "number(id)", "examples": spread(sorted(numeric_codes))}
        if measure == "ordinal" and rng:
            return {"type": "number(ordinal)", "range": rng}
        if rng and storage in ("integer", "float", None):
            return {"type": "number", "range": rng, "examples": rng}
        if measure == "identifier" and rng:
            return {"type": "number(id)", "examples": rng}
        self.losses.add(rel, "untyped")
        return {}

    # ------------------------------------------------------------ losses

    def losses_md(self):
        lines = [f"<!-- Generated by pdt {__version__} from inputs sha256:{self.digest}. Do not edit. -->", "",
                 f"# What the data-dict export loses: {self.ds.get('title', self.ds.get('id'))}", "",
                 f"The YAML files here follow data-dict spec {SPEC_VERSION}. They describe the common "
                 "data format, so they validate against its parquet files. The records in `metadata/` "
                 "remain canonical. This table counts what the export drops or flattens into text.", ""]
        releases = [r["id"] for r in self.ds.get("releases", [])]
        lines.append("| | " + " | ".join(f"`{r}`" for r in releases) + " |")
        lines.append("|---|" + "---|" * len(releases))
        for key, label in Losses.LABELS.items():
            row = [self.losses.counts.get(r, {}).get(key, 0) for r in releases]
            if any(row):
                lines.append(f"| {label} | " + " | ".join(f"{n:,}" for n in row) + " |")
        lines.append("")
        return "\n".join(lines)


def build(root, out=None):
    root = Path(root)
    return Exporter(root, Path(out) if out else root / DIRECTORY).build()


def is_current(root):
    path = Path(root) / DIRECTORY / "manifest.json"
    if not path.exists():
        return False
    m = json.loads(path.read_text())
    return m.get("pdt_version") == __version__ and m.get("inputs_sha256") == inputs_hash(root)

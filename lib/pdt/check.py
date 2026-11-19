"""`pdt check`: check a dataset repository against the standard (STANDARD.md §9).

Implemented: C1, C2, C6, C7, C9, C10, C11.
Not yet: C3-C5 (need the data; dataset repos run them in their build for now)
and C8 (needs the generated views).
"""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .schemas import errors, validators

README_SECTIONS = ["terms", "get the data", "metadata", "cite", "rebuild"]


@dataclass
class Result:
    failures: list = field(default_factory=list)
    reports: list = field(default_factory=list)

    def fail(self, check, message):
        self.failures.append(f"{check}: {message}")

    def report(self, check, message):
        self.reports.append(f"{check}: {message}")

    @property
    def ok(self):
        return not self.failures


@dataclass
class Repo:
    """The records of one dataset repository, loaded from disk."""
    root: Path
    dataset: dict
    sources: dict
    variables: dict      # release id -> list of records (all tables)
    tables: dict         # release id -> {table id or None: list of records}
    groups: list
    links: list
    corrections: list
    annotations: list
    derived: list

    @classmethod
    def load(cls, root):
        root = Path(root)
        meta = root / "metadata"
        dataset = yaml.safe_load((root / "dataset.yaml").read_text())
        tables = {}
        for r in dataset.get("releases", []):
            base = meta / "releases" / r["id"]
            if r.get("tables"):
                tables[r["id"]] = {t["id"]: read_jsonl(base / t["id"] / "variables.jsonl") for t in r["tables"]}
            else:
                tables[r["id"]] = {None: read_jsonl(base / "variables.jsonl")}
        return cls(
            root=root,
            dataset=dataset,
            sources=yaml.safe_load((root / "sources.yaml").read_text()),
            variables={rel: [rec for recs in ts.values() for rec in recs] for rel, ts in tables.items()},
            tables=tables,
            groups=read_jsonl(meta / "groups.jsonl"),
            links=read_jsonl(meta / "links.jsonl"),
            corrections=read_jsonl(meta / "corrections.jsonl"),
            annotations=[a for p in sorted((meta / "annotations").glob("*.jsonl")) for a in read_jsonl(p)],
            derived=[d for p in sorted((meta / "derived").glob("*.jsonl")) for d in read_jsonl(p)],
        )

    def resolve(self, name, release=None, table=None):
        """Records matching a reference: [(release, table, record)]."""
        out = []
        for rel, ts in self.tables.items():
            if release is not None and rel != release:
                continue
            for tab, recs in ts.items():
                if table is not None and tab != table:
                    continue
                out += [(rel, tab, r) for r in recs if r["name"] == name]
        return out

    @property
    def records(self):
        return [r for recs in self.variables.values() for r in recs]


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def walk(obj):
    """Yield every dict nested anywhere in obj."""
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def origins(obj):
    """Yield every origin object (a dict with an 'origin' key naming its kind)."""
    for d in walk(obj):
        if isinstance(d.get("origin"), str):
            yield d


def resolve_pointer(record, pointer):
    node = record
    for part in pointer.strip("/").split("/"):
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


# ------------------------------------------------------------------ checks


def check_schemas(repo, result):
    """C1: every file validates against its schema."""
    v = validators()
    files = [("dataset.yaml", "dataset.schema.json", [repo.dataset]),
             ("sources.yaml", "sources.schema.json", [repo.sources]),
             ("groups.jsonl", "group.schema.json", repo.groups),
             ("links.jsonl", "link.schema.json", repo.links),
             ("corrections.jsonl", "correction.schema.json", repo.corrections),
             ("annotations", "annotation.schema.json", repo.annotations),
             ("derived", "derived.schema.json", repo.derived)]
    files += [(f"releases/{rel}" + (f"/{tab}" if tab else ""), "variable.schema.json", recs)
              for rel, ts in repo.tables.items() for tab, recs in ts.items()]
    for label, schema, records in files:
        for i, record in enumerate(records):
            for e in errors(v[schema], record):
                where = "/".join(map(str, e.absolute_path)) or "(record)"
                name = record.get("name") or record.get("id") or i
                result.fail("C1", f"{label} {name}: {where}: {e.message[:200]}")


def check_ref(repo, result, what, name, release=None, table=None):
    """Fail if a reference matches no record, or matches records in several tables without naming one."""
    hits = repo.resolve(name, release, table)
    if not hits:
        where = "/".join(x for x in (release, table) if x)
        result.fail("C2", f"{what}: no variable {name}" + (f" in {where}" if where else ""))
    elif table is None and len({(rel, tab) for rel, tab, _ in hits if rel == hits[0][0]}) > 1:
        result.fail("C2", f"{what}: {name} is in several tables of release {hits[0][0]}; name the table")


def check_references(repo, result):
    """C2: unique ids and references that resolve."""
    dataset_id = repo.dataset.get("id")
    for release, ts in repo.tables.items():
        declared = any(tab is not None for tab in ts)
        for tab, recs in ts.items():
            where = f"release {release}" + (f", table {tab}" if tab else "")
            seen = [r["name"] for r in recs]
            dupes = sorted({n for n in seen if seen.count(n) > 1})
            if dupes:
                result.fail("C2", f"duplicate names in {where}: {dupes}")
            reserved = sorted(n for n in seen if n.endswith("__code") or n == "_row")
            if reserved:
                result.fail("C2", f"names reserved by the common data format in {where}: {reserved}")
            for r in recs:
                if r.get("release") != release or r.get("dataset") != dataset_id:
                    result.fail("C2", f"{r['name']}: dataset or release doesn't match its file")
                if declared and r.get("table") != tab:
                    result.fail("C2", f"{r['name']}: table {r.get('table')!r} doesn't match its file ({tab})")
                if not declared and "table" in r:
                    result.fail("C2", f"{r['name']}: has a table, but release {release} declares none")

    for kind, items in [("group", repo.groups), ("correction", repo.corrections)]:
        ids = [x["id"] for x in items]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            result.fail("C2", f"duplicate {kind} ids: {dupes}")

    group_ids = {g["id"] for g in repo.groups}
    for g in repo.groups:
        for m in g["members"]:
            check_ref(repo, result, f"group {g['id']} member", m["name"], m.get("release"), m.get("table"))
        if "parent" in g and g["parent"] not in group_ids:
            result.fail("C2", f"group {g['id']}: parent {g['parent']} doesn't exist")
    for link in repo.links:
        for end in ("from", "to"):
            ref = link[end]
            if ref.get("dataset", dataset_id) == dataset_id:
                check_ref(repo, result, f"link {end}", ref["name"], ref["release"], ref.get("table"))
    for c in repo.corrections:
        check_ref(repo, result, f"correction {c['id']}", c["target"]["name"], None, c["target"].get("table"))
        for rel in c["target"].get("releases", []):
            if rel not in repo.variables:
                result.fail("C2", f"correction {c['id']}: unknown release {rel}")
    for item in repo.annotations + repo.derived:
        t = item["target"]
        if "variable" in t:
            check_ref(repo, result, "annotation or derived property", t["variable"], t.get("release"), t.get("table"))
        if "group" in t and t["group"] not in group_ids:
            result.fail("C2", f"annotation or derived property targets unknown group {t['group']}")

    source_ids = {s["id"] for s in repo.sources.get("sources", [])}
    for r in repo.dataset.get("releases", []):
        for s in r.get("sources", []):
            if s not in source_ids:
                result.fail("C2", f"release {r['id']}: unknown source {s}")
        table_ids = {t["id"] for t in r.get("tables", [])}
        for t in r.get("tables", []):
            for s in t.get("sources", []):
                if s not in source_ids:
                    result.fail("C2", f"table {r['id']}/{t['id']}: unknown source {s}")
            names_here = {rec["name"] for rec in repo.tables[r["id"]].get(t["id"], [])}
            for col in t.get("key", []):
                if names_here and col not in names_here:
                    result.fail("C2", f"table {r['id']}/{t['id']}: key column {col} has no record")
            for ref in t.get("references", []):
                same = ref.get("dataset", repo.dataset.get("id")) == repo.dataset.get("id") and \
                    ref.get("release", r["id"]) == r["id"]
                if same and ref["table"] not in table_ids:
                    result.fail("C2", f"table {r['id']}/{t['id']}: references unknown table {ref['table']}")
                for col in ref["columns"]:
                    if names_here and col not in names_here:
                        result.fail("C2", f"table {r['id']}/{t['id']}: reference column {col} has no record")
    used = {d["source"] for d in walk([repo.records, repo.groups, repo.links, repo.annotations])
            if isinstance(d.get("source"), str)}
    for s in sorted(used - source_ids):
        result.fail("C2", f"provenance names unknown source {s}")


def check_provenance(repo, result):
    """C6: sources are pinned; report gaps in the records."""
    used = {s for r in repo.dataset.get("releases", []) for s in r.get("sources", [])}
    for s in repo.sources.get("sources", []):
        if s["id"] in used and not (s.get("sha256") and s.get("fetched_on")):
            result.fail("C6", f"source {s['id']} has no sha256 or fetched_on")
        if s["kind"] == "upstream_package" and not s.get("version"):
            result.report("C6", f"upstream package {s['id']} has no pinned version")
    recs = repo.records
    for name in ["label", "questions", "values"]:
        missing = sum(name not in r for r in recs)
        if missing:
            result.report("C6", f"{missing} of {len(recs)} records have no {name}")
    unresolved = sum(v["kind"] == "unresolved" for r in recs for v in r.get("values", []))
    result.report("C6", f"{unresolved} unresolved codes")
    everything = [recs, repo.groups, repo.links, repo.annotations]
    unreviewed = sum(1 for o in origins(everything) if o["origin"] == "model" and not o.get("reviewed"))
    result.report("C6", f"{unreviewed} unreviewed model-made facts")


def check_corrections(repo, result):
    """C7: each correction's original value still appears in its target."""
    for c in repo.corrections:
        t = c["target"]
        releases = t.get("releases") or list(repo.tables)
        for rel, tab, record in repo.resolve(t["name"], None, t.get("table")):
            if rel not in releases:
                continue
            where = rel + (f"/{tab}" if tab else "")
            try:
                current = resolve_pointer(record, t["field"])
            except (KeyError, IndexError, ValueError, TypeError):
                result.fail("C7", f"{c['id']}: field {t['field']} not found in {where}")
                continue
            if current != c["original"]:
                result.fail("C7", f"{c['id']}: original no longer matches in {where} (fixed upstream?)")


def tracked_files(root):
    proc = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True)
    return proc.stdout.split() if proc.returncode == 0 else None


def check_terms(repo, result):
    """C9: nothing restricted is published; no model output when LLM processing isn't allowed."""
    terms = repo.dataset.get("terms", {})
    everything = [repo.records, repo.groups, repo.links, repo.annotations]
    if terms.get("llm_processing") != "allowed" and any(o["origin"] == "model" for o in origins(everything)):
        result.fail("C9", "records have origin model, but llm_processing isn't allowed")
    for kind in ("data", "documentation", "metadata"):
        if terms.get(kind) != "ship":
            result.report("C9", f"terms.{kind} is {terms.get(kind)}")
    tracked = tracked_files(repo.root)
    if tracked is None:
        result.report("C9", "not a git repository; tracked files not checked")
        return
    for s in repo.sources.get("sources", []):
        path = s.get("path")
        if path and s["redistribution"] != "ship" and any(t == path or t.startswith(path.rstrip("/") + "/")
                                                          for t in tracked):
            result.fail("C9", f"{path} is {s['redistribution']} but tracked in git")
    if terms.get("metadata") != "ship" and any(t.startswith("metadata/") for t in tracked):
        result.fail("C9", f"metadata is tracked in git, but terms.metadata is {terms.get('metadata')}")


def check_extensions(repo, result):
    """C10: every extension key is listed in EXTENSIONS.md."""
    path = repo.root / "EXTENSIONS.md"
    doc = path.read_text() if path.exists() else ""
    keys = {f"{ns}.{k}" for r in repo.records for ns, d in r.get("extensions", {}).items() for k in d}
    for key in sorted(keys):
        if f"`{key}`" not in doc:
            result.fail("C10", f"extension {key} isn't listed in EXTENSIONS.md")


def check_docs(repo, result):
    """C11: README has the required sections; CLAUDE.md exists."""
    readme = repo.root / "README.md"
    if not readme.exists():
        result.fail("C11", "no README.md")
    else:
        headings = [line.lower() for line in readme.read_text().splitlines() if line.startswith("## ")]
        for section in README_SECTIONS:
            if not any(section in h for h in headings):
                result.fail("C11", f"README.md has no section about '{section}'")
    if not (repo.root / "CLAUDE.md").exists():
        result.fail("C11", "no CLAUDE.md")


CHECKS = [check_schemas, check_references, check_provenance, check_corrections,
          check_terms, check_extensions, check_docs]


def run(root):
    """Run every implemented check on the repo at root; return a Result."""
    result = Result()
    repo = Repo.load(root)
    for check in CHECKS:
        check(repo, result)
    result.report("--", "not yet implemented: C3-C5 (need the data), C8 (generated views)")
    return result

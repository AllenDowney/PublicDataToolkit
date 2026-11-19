"""`pdt check`: check a dataset repository against the standard (STANDARD.md §9).

Implemented: C1-C12. C3-C5 and C12 read the common-format files in
data/processed/ (written by the repo's `make data`) and are skipped, with a
notice, when they're absent or were built from other records. C8 compares each
generated view's manifest with the current records.
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
    histories: list
    annotations: list
    derived: list
    code_lists: list = field(default_factory=list)
    stored: dict = field(default_factory=dict)   # tables as on disk, before code lists are expanded

    @classmethod
    def load(cls, root):
        root = Path(root)
        meta = root / "metadata"
        dataset = yaml.safe_load((root / "dataset.yaml").read_text())
        stored = {}
        for r in dataset.get("releases", []):
            base = meta / "releases" / r["id"]
            if r.get("tables"):
                stored[r["id"]] = {t["id"]: read_jsonl(base / t["id"] / "variables.jsonl") for t in r["tables"]}
            else:
                stored[r["id"]] = {None: read_jsonl(base / "variables.jsonl")}
        code_lists = read_jsonl(meta / "code_lists.jsonl")
        tables = expand_code_lists(stored, code_lists)
        return cls(
            root=root,
            dataset=dataset,
            sources=yaml.safe_load((root / "sources.yaml").read_text()),
            variables={rel: [rec for recs in ts.values() for rec in recs] for rel, ts in tables.items()},
            tables=tables,
            groups=read_jsonl(meta / "groups.jsonl"),
            links=read_jsonl(meta / "links.jsonl"),
            corrections=read_jsonl(meta / "corrections.jsonl"),
            histories=read_jsonl(meta / "histories.jsonl"),
            annotations=[a for p in sorted((meta / "annotations").glob("*.jsonl")) for a in read_jsonl(p)],
            derived=[d for p in sorted((meta / "derived").glob("*.jsonl")) for d in read_jsonl(p)],
            code_lists=code_lists,
            stored=stored,
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


def expand_code_lists(stored, code_lists):
    """Tables with each record's shared code list (STANDARD.md §4.5) expanded: the list's codes,
    then the record's own values. A record whose list doesn't exist is left as it is (C2 fails it)."""
    lists = {cl["id"]: cl for cl in code_lists}
    out = {}
    for rel, ts in stored.items():
        out[rel] = {}
        for tab, recs in ts.items():
            expanded = []
            for r in recs:
                cl = lists.get(r.get("code_list"))
                if cl is not None:
                    r = {**r, "values": [dict(c) for c in cl["codes"]] + list(r.get("values") or [])}
                expanded.append(r)
            out[rel][tab] = expanded
    return out


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
             ("histories.jsonl", "history.schema.json", repo.histories),
             ("code_lists.jsonl", "code_list.schema.json", repo.code_lists),
             ("annotations", "annotation.schema.json", repo.annotations),
             ("derived", "derived.schema.json", repo.derived)]
    files += [(f"releases/{rel}" + (f"/{tab}" if tab else ""), "variable.schema.json", recs)
              for rel, ts in (repo.stored or repo.tables).items() for tab, recs in ts.items()]
    for label, schema, records in files:
        for i, record in enumerate(records):
            for e in errors(v[schema], record):
                where = "/".join(map(str, e.absolute_path)) or "(record)"
                name = record.get("name") or record.get("id") or i
                result.fail("C1", f"{label} {name}: {where}: {e.message[:200]}")
    # Rules for histories the schema can't express: unique ids, one code per period.
    ids = [h.get("id") for h in repo.histories]
    for dupe in sorted({i for i in ids if ids.count(i) > 1}):
        result.fail("C1", f"histories.jsonl: duplicate id {dupe}")
    for h in repo.histories:
        n = len(h.get("periods", []))
        for a in h.get("attributes", []):
            if len(a.get("codes", [])) != n:
                result.fail("C1", f"histories.jsonl {h.get('id')}: attribute {a.get('label')!r} has "
                                  f"{len(a.get('codes', []))} codes for {n} periods")
    # A rule the schema can't express: every missing or unresolved code has an origin,
    # its own or the record's provenance.codes default.
    for rel, ts in repo.tables.items():
        for tab, recs in ts.items():
            for r in recs:
                default = r.get("provenance", {}).get("codes")
                for v in r.get("values", []):
                    if v.get("kind") in ("missing", "unresolved") and "origin" not in v and default is None:
                        where = rel + (f"/{tab}" if tab else "")
                        result.fail("C1", f"{where} {r['name']}: code {v['code']} is {v['kind']} but has no origin "
                                          "and the record has no provenance.codes default")


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
        if "code_list" in c["target"]:
            if c["target"]["code_list"] not in {cl["id"] for cl in repo.code_lists}:
                result.fail("C2", f"correction {c['id']}: unknown code list {c['target']['code_list']}")
        else:
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
                when = ref.get("when", {}).get("column")
                if when and names_here and when not in names_here:
                    result.fail("C2", f"table {r['id']}/{t['id']}: reference condition column {when} has no record")
                same = ref.get("dataset", repo.dataset.get("id")) == repo.dataset.get("id") and \
                    ref.get("release", r["id"]) == r["id"]
                if same and ref["table"] not in table_ids:
                    result.fail("C2", f"table {r['id']}/{t['id']}: references unknown table {ref['table']}")
                for col in ref["columns"]:
                    if names_here and col not in names_here:
                        result.fail("C2", f"table {r['id']}/{t['id']}: reference column {col} has no record")
                if "target_columns" in ref and len(ref["target_columns"]) != len(ref["columns"]):
                    result.fail("C2", f"table {r['id']}/{t['id']}: reference to {ref['table']} has "
                                      f"{len(ref['columns'])} columns but {len(ref['target_columns'])} target_columns")
                target_names = {rec["name"] for rec in repo.tables[r["id"]].get(ref["table"], [])} if same else set()
                for col in ref.get("target_columns", []):
                    if target_names and col not in target_names:
                        result.fail("C2", f"table {r['id']}/{t['id']}: target column {col} has no record "
                                          f"in table {ref['table']}")
    check_name_reuse(repo, result)
    used = {d["source"] for d in walk([repo.records, repo.groups, repo.links, repo.annotations])
            if isinstance(d.get("source"), str)}
    for s in sorted(used - source_ids):
        result.fail("C2", f"provenance names unknown source {s}")


def check_name_reuse(repo, result):
    """C2 (warns): a name in two releases whose records aren't linked to each other, while one of
    them is linked to a different name in the other release.

    In a dataset that renumbers its variables in each release (the YRBSS combined datasets:
    q26 is "Considered suicide" in sadc-2021 and "Sad or hopeless" in sadc-2023), the same
    name can mean different items, and a user who matches by name gets the wrong one.
    """
    dataset_id = repo.dataset.get("id")

    def end(ref):
        return ref["release"], ref.get("table"), ref["name"]

    pairs = set()
    for link in repo.links:
        a, b = link["from"], link["to"]
        if a.get("dataset", dataset_id) != dataset_id or b.get("dataset", dataset_id) != dataset_id:
            continue
        if a["release"] != b["release"]:
            pairs.add((end(a), end(b)))
            pairs.add((end(b), end(a)))
    partners = {}
    for x, y in pairs:
        partners.setdefault((x, y[0]), set()).add(y)            # (record, other release) -> linked records
    where = {}
    for rel, ts in repo.tables.items():
        for tab, recs in ts.items():
            for r in recs:
                where.setdefault((tab, r["name"]), []).append(rel)
    for (tab, name), rels in sorted(where.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
        for i, ra in enumerate(rels):
            for rb in rels[i + 1:]:
                a, b = (ra, tab, name), (rb, tab, name)
                if (a, b) in pairs:
                    continue
                others = [(x, y) for x, y in ((a, partners.get((a, rb), set())), (b, partners.get((b, ra), set())))
                          if any(p[2] != name for p in y)]
                if others:
                    x, y = others[0]
                    to = sorted(f"{p[0]}/{p[2]}" for p in y)
                    label = f"{tab}/{name}" if tab else name
                    result.report("C2", f"warning: {label} is in {ra} and {rb}, but the two aren't linked; "
                                        f"{x[0]}/{name} is linked to {', '.join(to)}, so the name may mean "
                                        "a different item in each release")


def check_provenance(repo, result):
    """C6: sources are pinned; report gaps in the records."""
    used = {s for r in repo.dataset.get("releases", []) for s in r.get("sources", [])}
    for s in repo.sources.get("sources", []):
        if s["id"] in used and not (s.get("sha256") and s.get("fetched_on")):
            result.fail("C6", f"source {s['id']} has no sha256 or fetched_on")
        if s["kind"] == "upstream_package" and not s.get("version"):
            result.report("C6", f"upstream package {s['id']} has no pinned version")
    recs = repo.records
    # Question text is expected only of surveys (STANDARD.md §2.1, `kind`); other data has a
    # description instead. No kind means a survey, as before kind existed.
    survey = repo.dataset.get("kind", "survey") == "survey"
    for name in ["label", "questions" if survey else "description", "values"]:
        missing = sum(name not in r for r in recs)
        if missing:
            result.report("C6", f"{missing} of {len(recs)} records have no {name}")
    unresolved = sum(v["kind"] == "unresolved" for r in recs for v in r.get("values", []))
    result.report("C6", f"{unresolved} unresolved codes")
    everything = [recs, repo.groups, repo.links, repo.annotations]
    unreviewed = sum(1 for o in origins(everything) if o["origin"] == "model" and not o.get("reviewed"))
    result.report("C6", f"{unreviewed} unreviewed model-made facts")


def check_code_lists(repo, result):
    """C2 for shared code lists (STANDARD.md §4.5): unique ids, codes unique within a list, every
    record's list exists, and no code both in a record's list and in its own values."""
    from .data import code_text
    ids = [cl["id"] for cl in repo.code_lists]
    for dupe in sorted({i for i in ids if ids.count(i) > 1}):
        result.fail("C2", f"duplicate code list id {dupe}")
    lists = {cl["id"]: cl for cl in repo.code_lists}
    for cl in repo.code_lists:
        codes = [code_text(c["code"]) for c in cl.get("codes", [])]
        if dupes := sorted({c for c in codes if codes.count(c) > 1}):
            result.fail("C2", f"code list {cl['id']}: duplicate codes {listed(dupes)}")
    for rel, ts in repo.stored.items():
        for tab, recs in ts.items():
            for r in recs:
                if "code_list" not in r:
                    continue
                where = f"{rel}/" + (f"{tab}/" if tab else "") + r["name"]
                cl = lists.get(r["code_list"])
                if cl is None:
                    result.fail("C2", f"{where}: unknown code list {r['code_list']}")
                    continue
                in_list = {code_text(c["code"]) for c in cl["codes"]}
                if both := sorted(in_list & {code_text(v["code"]) for v in r.get("values") or []}):
                    result.fail("C2", f"{where}: codes both in list {cl['id']} and in values: {listed(both)}")


def check_corrections(repo, result):
    """C7: each correction's original value still appears in its target."""
    lists = {cl["id"]: cl for cl in repo.code_lists}
    for c in repo.corrections:
        t = c["target"]
        if "code_list" in t:
            cl = lists.get(t["code_list"])
            if cl is None:
                continue  # C2 reports it
            try:
                current = resolve_pointer(cl, t["field"])
            except (KeyError, IndexError, ValueError, TypeError):
                result.fail("C7", f"{c['id']}: field {t['field']} not found in code list {cl['id']}")
                continue
            if current != c["original"]:
                result.fail("C7", f"{c['id']}: original no longer matches in code list {cl['id']} (fixed upstream?)")
            continue
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


def has_remote(root):
    """Whether the git repository at root has any remote (`git remote` lists one)."""
    proc = subprocess.run(["git", "remote"], cwd=root, capture_output=True, text=True)
    return proc.returncode == 0 and bool(proc.stdout.strip())


def check_terms(repo, result):
    """C9: nothing restricted is published; no model output when LLM processing isn't allowed.

    Publishing means pushing to a git remote or putting files in a data release
    (STANDARD.md §9). A repo with no remote may commit restricted files locally:
    they're reported, and fail once a remote is added. Model output without
    permission for LLM processing fails either way.
    """
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
    problems = []
    for s in repo.sources.get("sources", []):
        path = s.get("path")
        if path and s["redistribution"] != "ship" and any(t == path or t.startswith(path.rstrip("/") + "/")
                                                          for t in tracked):
            problems.append(f"{path} is {s['redistribution']} but tracked in git")
    if terms.get("metadata") != "ship" and any(t.startswith("metadata/") for t in tracked):
        problems.append(f"metadata is tracked in git, but terms.metadata is {terms.get('metadata')}")
    if has_remote(repo.root):
        for p in problems:
            result.fail("C9", p)
    else:
        for p in problems:
            result.report("C9", f"{p} (no git remote, so not published; this fails once a remote is added)")


def check_extensions(repo, result):
    """C10: every extension key is listed in EXTENSIONS.md."""
    path = repo.root / "EXTENSIONS.md"
    doc = path.read_text() if path.exists() else ""
    keys = {f"{ns}.{k}" for r in repo.records for ns, d in r.get("extensions", {}).items() for k in d}
    for key in sorted(keys):
        if f"`{key}`" not in doc:
            result.fail("C10", f"extension {key} isn't listed in EXTENSIONS.md")


def normalized(text):
    """Text with blockquote markers and runs of whitespace removed, so a wrapped or quoted
    notice still matches."""
    return " ".join(word for line in text.splitlines() for word in line.lstrip().lstrip(">").split())


def section_text(markdown, word):
    """The text of the first `## ` section whose heading contains word (any case)."""
    out, inside = [], False
    for line in markdown.splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = word in line.lower()
        elif inside:
            out.append(line)
    return "\n".join(out)


def check_docs(repo, result):
    """C11: README has the required sections; CLAUDE.md exists."""
    readme = repo.root / "README.md"
    if not readme.exists():
        result.fail("C11", "no README.md")
    else:
        text = readme.read_text()
        headings = [line.lower() for line in text.splitlines() if line.startswith("## ")]
        for section in README_SECTIONS:
            if not any(section in h for h in headings):
                result.fail("C11", f"README.md has no section about '{section}'")
        notice = (repo.dataset.get("terms") or {}).get("notice")
        if notice and normalized(notice) not in normalized(section_text(text, "terms")):
            result.fail("C11", "README.md's terms section doesn't include terms.notice verbatim")
    if not (repo.root / "CLAUDE.md").exists():
        result.fail("C11", "no CLAUDE.md")


# ------------------------------------------------------------ data checks

PROCESSED = Path("data") / "processed"
MAX_LISTED = 5  # examples listed per message


def processed_name(dataset, release, table=None):
    """The common-format file for a release or table; the same name pdt.release writes."""
    return f"{dataset}-{release}" + (f"-{table}" if table else "") + ".parquet"


def listed(items):
    items = list(items)
    more = f", and {len(items) - MAX_LISTED} more" if len(items) > MAX_LISTED else ""
    return ", ".join(str(i) for i in items[:MAX_LISTED]) + more


def same_value(a, b):
    """A data cell and a metadata value are equal: numbers by value, anything else as text."""
    from .data import is_number
    if is_number(a) and is_number(b):
        return float(a) == float(b)
    return str(a) == str(b)


def load_data(repo, result):
    """{(release, table): (frame, records)} for the files that exist and match the current records.

    The records are the corrected ones (corrections.jsonl applied), as pdt.release
    splits the data with them: a code an inferred correction makes valid is in the
    value column, not the code column.
    """
    from . import data
    from .search import apply_corrections
    corrections_file = repo.root / "metadata" / "corrections.jsonl"
    corrections_sha = data.metadata_sha256(corrections_file) if corrections_file.exists() else None
    lists_file = repo.root / "metadata" / "code_lists.jsonl"
    lists_sha = data.metadata_sha256(lists_file) if lists_file.exists() else None
    frames, missing = {}, []
    for release, ts in repo.tables.items():
        for table, records in ts.items():
            name = processed_name(repo.dataset.get("id"), release, table)
            path = repo.root / PROCESSED / name
            if not path.exists():
                missing.append(name)
                continue
            variables = repo.root / "metadata" / "releases" / release / (table or "") / "variables.jsonl"
            ident = data.identity_of(path)
            if ident.get("metadata_sha256") != data.metadata_sha256(variables) or \
                    ("corrections_sha256" in ident and ident["corrections_sha256"] != corrections_sha) or \
                    ("code_lists_sha256" in ident and ident["code_lists_sha256"] != lists_sha):
                result.report("C3-C5, C12", f"skipped {name}: built from other records, corrections or code lists; "
                                            "rebuild it (make data)")
                continue
            fixed = [apply_corrections(r, release, table, repo.corrections)[0] for r in records]
            frames[(release, table)] = (data.read(path), fixed)
    if missing:
        result.report("C3-C5, C12", f"skipped, no data file in {PROCESSED}/ (make data): {listed(missing)}")
    return frames


def value_columns(frame):
    from .data import CODE_SUFFIX, ROW
    return [c for c in frame.columns if c != ROW and not c.endswith(CODE_SUFFIX)]


def check_coverage(name, frame, records, result):
    """C3: every record has a column and every column a record (in the repo's data file, which
    holds the variables it has records for)."""
    names, columns = [r["name"] for r in records], value_columns(frame)
    if missing := [n for n in names if n not in columns]:
        result.fail("C3", f"{name}: records without a column: {listed(missing)}")
    if extra := [c for c in columns if c not in names]:
        result.fail("C3", f"{name}: columns without a record: {listed(extra)}")


def check_codes(name, frame, records, result):
    """C4: every code in a code column is in the record's values. Valid values of a categorical
    variable that aren't listed (and aren't in valid_range) are reported."""
    from .data import CODE_SUFFIX, code_text
    for r in records:
        documented = {code_text(v["code"]) for v in r.get("values", [])}
        col = r["name"] + CODE_SUFFIX
        if col in frame:
            counts = frame[col].dropna().value_counts()
            if bad := [f"{c} ({n:,} rows)" for c, n in counts.items() if c not in documented]:
                result.fail("C4", f"{name}/{r['name']}: codes not in values: {listed(bad)}")
        valid = [v["code"] for v in r.get("values", []) if v["kind"] == "valid"]
        if r.get("measure") in ("categorical", "ordinal") and valid and r["name"] in frame:
            rng = r.get("valid_range") or {}
            seen = frame[r["name"]].dropna().unique()
            extra = [x for x in seen if not any(same_value(x, v) for v in valid)
                     and not ("min" in rng and rng["min"] <= x <= rng.get("max", rng["min"]))]
            if extra:
                result.report("C4", f"{name}/{r['name']}: valid values not listed in values: "
                                    f"{listed(sorted(code_text(x) for x in extra))}")


def check_availability(name, frame, records, wave_column, result, data_waves=None):
    """C5 (warns): the waves in each record's availability are the waves with non-missing values.

    With data_waves (the file holds only those waves; STANDARD.md §2.1), availability is
    checked only for them.
    """
    def kept(availability):
        waves = {str(a["wave"]) for a in availability}
        return waves if data_waves is None else waves & data_waves
    declared_all = {w for r in records for w in kept(r.get("availability", []))}
    if wave_column in frame:
        from .data import code_text
        waves = frame[wave_column].map(lambda w: None if w is None or w != w else code_text(w))
    elif len(declared_all) == 1:
        waves = None  # one wave per file: the release (NSFG cycle, FARS data year)
    else:
        if declared_all:
            result.report("C5", f"{name}: skipped, no wave column ({wave_column}) and several waves declared")
        return
    for r in records:
        if not r.get("availability") or r["name"] not in frame:
            continue
        has = frame[r["name"]].notna()
        in_data = set(waves[has].dropna()) if waves is not None else (declared_all if has.any() else set())
        declared = kept(r["availability"])
        if empty := sorted(declared - in_data):
            result.report("C5", f"warning: {name}/{r['name']}: waves in availability with no non-missing "
                                f"values: {listed(empty)}")
        if undeclared := sorted(in_data - declared):
            result.report("C5", f"warning: {name}/{r['name']}: waves with non-missing values not in "
                                f"availability: {listed(undeclared)}")


def check_keys_in_data(release, tables, frames, result):
    """C12: each table's key is unique and non-blank; each reference finds its target, for the
    rows its `when` selects."""
    for t in tables:
        if (release, t["id"]) not in frames:
            continue
        frame, _ = frames[(release, t["id"])]
        name = f"{release}/{t['id']}"
        key = t.get("key", [])
        if key:
            if absent := [c for c in key if c not in frame]:
                result.report("C12", f"{name}: skipped key, columns not in the data file: {listed(absent)}")
            else:
                if blank := int(frame[key].isna().any(axis=1).sum()):
                    result.fail("C12", f"{name}: {blank:,} rows with a blank key ({', '.join(key)})")
                if dupes := int(frame.duplicated(key).sum()):
                    result.fail("C12", f"{name}: {dupes:,} duplicate keys ({', '.join(key)})")
        for ref in t.get("references", []):
            if ref.get("dataset") or ref.get("release", release) != release:
                continue  # another dataset or release; not checked here
            if (release, ref["table"]) not in frames:
                result.report("C12", f"{name} -> {ref['table']}: skipped, no data file for {ref['table']}")
                continue
            target, _ = frames[(release, ref["table"])]
            cols, when = ref["columns"], ref.get("when")
            tcols = ref.get("target_columns", cols)   # the target's names, when they differ (CPS FH_SEQ -> H_SEQ)
            needed = cols + ([when["column"]] if when else [])
            if absent := [c for c in needed if c not in frame] + [c for c in tcols if c not in target]:
                result.report("C12", f"{name} -> {ref['table']}: skipped, columns not in the data: {listed(absent)}")
                continue
            rows = frame
            if when:
                rows = frame[frame[when["column"]].map(lambda x: any(same_value(x, v) for v in when["in"]))]
            have = set(map(tuple, target[tcols].dropna().astype(object).itertuples(index=False)))
            unmatched = sum(tuple(k) not in have for k in rows[cols].astype(object).itertuples(index=False))
            if unmatched:
                cond = f" when {when['column']} in {when['in']}" if when else ""
                result.fail("C12", f"{name} ({', '.join(cols)}) -> {ref['table']}{cond}: "
                                   f"{unmatched:,} of {len(rows):,} rows without a match")


def data_waves(repo, release, table):
    """The waves a release's (or table's) data file holds, as text, or None for all."""
    r = next((r for r in repo.dataset.get("releases", []) if r["id"] == release), {})
    t = next((t for t in r.get("tables") or [] if t["id"] == table), {})
    waves = t.get("data_waves") or r.get("data_waves")
    return {str(w) for w in waves} if waves else None


def check_data(repo, result):
    """C3, C4, C5 and C12, on the common-format files in data/processed/."""
    frames = load_data(repo, result)
    wave_column = ((repo.dataset.get("dimensions") or {}).get("wave") or {}).get("column")
    for (release, table), (frame, records) in frames.items():
        name = release + (f"/{table}" if table else "")
        check_coverage(name, frame, records, result)
        check_codes(name, frame, records, result)
        check_availability(name, frame, records, wave_column, result, data_waves(repo, release, table))
    for r in repo.dataset.get("releases", []):
        check_keys_in_data(r["id"], r.get("tables") or [], frames, result)


VIEWS = [("agent/", "agent/manifest.json"), ("docs/", "docs/manifest.json"),
         ("export/data-dict/", "export/data-dict/manifest.json")]


def view_files(manifest):
    """The files a view's manifest lists, relative to the view's directory."""
    if "files" in manifest:
        return manifest["files"]
    return [f["path"] for s in manifest.get("shards", []) for f in s["files"]] + ["index.md", "SKILL.md"]


def check_views(repo, result):
    """C8: agent/, docs/ and export/ were generated from the current records.

    Each generator writes a manifest with the library version and a SHA-256 of
    dataset.yaml and everything under metadata/ (pdt.views.inputs_hash). A view is
    current when that hash matches the records now and every file it lists exists.
    A different library version is reported, not failed: regenerating after a toolkit
    upgrade is step 2 of STANDARD.md §2.4.
    """
    from . import __version__
    from .views import inputs_hash
    current = inputs_hash(repo.root)
    for directory, manifest_path in VIEWS:
        path = repo.root / manifest_path
        if not path.exists():
            result.fail("C8", f"{directory} hasn't been generated; run `make views`")
            continue
        manifest = json.loads(path.read_text())
        if manifest.get("inputs_sha256") != current:
            result.fail("C8", f"{directory} is out of date with the records (dataset.yaml or metadata/ "
                              "changed since it was generated); run `make views`")
        base = path.parent
        gone = [f for f in view_files(manifest) if not (base / f).exists()]
        if gone:
            result.fail("C8", f"{directory} is missing {len(gone)} generated file(s), e.g. {gone[0]}; "
                              "run `make views`")
        if manifest.get("pdt_version") != __version__:
            result.report("C8", f"{directory} was generated by pdt {manifest.get('pdt_version')}; "
                                f"this is {__version__}")


CHECKS = [check_schemas, check_references, check_code_lists, check_provenance, check_corrections,
          check_terms, check_extensions, check_docs, check_data, check_views]


def run(root, views=True):
    """Run every check on the repo at root; return a Result.

    views=False skips C8, for tests of the other checks on repos without generated views.
    """
    result = Result()
    repo = Repo.load(root)
    for check in CHECKS:
        if check is check_views and not views:
            continue
        check(repo, result)
    return result

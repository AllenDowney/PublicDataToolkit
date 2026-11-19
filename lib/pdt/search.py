"""Search a dataset repo's records with a filter, and label the result (STANDARD.md §7).

A filter is a dict; every key given must match (AND):

    release          a release id, or a list of them (scope)
    table            a table id (scope)
    name             a variable name, case-insensitive
    group            a group id: members of that group
    subject          a subject group's label, case-insensitive (groups of kind subject)
    topic            a topic annotation value, case-insensitive
    derived          {property: value}, e.g. {"scale_signature": "yes_no"}
    available        {"wave": W, "form": F}, form optional: an availability entry for wave W
                     with form F or with no form (no form means everyone in that wave)
    field            {"pointer": "/measure", "equals": "categorical"}
    text             a substring of the name, label or question text, case-insensitive

The search assigns the completeness label from what the filter used; the caller
doesn't choose it:

    complete          only publisher, upstream_package, data_file or hand facts
    complete_by_rule  also derived properties or rule-made groups (rule versions listed)
    approximate       text search, annotations, or model-made facts

A publisher's subject lists are groups of kind `subject` (STANDARD.md §5.1), so a
subject filter is `complete` with respect to the publisher's list and the records in
scope. Topic annotations are never more than `approximate`.
"""

from dataclasses import dataclass, field

LABELS = ["complete", "complete_by_rule", "approximate"]
SOURCE_ORIGINS = {"publisher", "upstream_package", "data_file", "hand"}


def worst(*labels):
    return max(labels, key=LABELS.index) if labels else "complete"


@dataclass
class Index:
    """The records of a repo, with corrections applied, and lookups for filtering."""
    entries: list                 # [(release, table, record)], records corrected
    groups: dict                  # group id -> group
    topics: list                  # topic annotations
    derived: list                 # derived property records
    corrected: dict = field(default_factory=dict)   # key -> [correction summary]

    @classmethod
    def from_repo(cls, repo):
        corrections_by_key = {}
        entries = []
        for rel, ts in repo.tables.items():
            for tab, recs in ts.items():
                for rec in recs:
                    rec, applied = apply_corrections(rec, rel, tab, repo.corrections)
                    entries.append((rel, tab, rec))
                    if applied:
                        corrections_by_key[(rel, tab, rec["name"])] = applied
        return cls(
            entries=entries,
            groups={g["id"]: g for g in repo.groups},
            topics=[a for a in repo.annotations if a.get("kind") == "topic"],
            derived=repo.derived,
            corrected=corrections_by_key,
        )


def apply_corrections(record, release, table, corrections):
    """Return (record with corrections applied, [summary of each one applied]).

    A correction applies when its name and table match, its releases (if given)
    include this release, and the field still holds the original value.
    """
    applied = []
    out = record
    for c in corrections:
        t = c["target"]
        if t["name"] != record["name"] or t.get("table") not in (None, table):
            continue
        if t.get("releases") and release not in t["releases"]:
            continue
        parts = [int(p) if p.isdigit() else p for p in t["field"].strip("/").split("/")]
        try:
            current = get_path(out, parts)
        except (KeyError, IndexError, TypeError):
            continue
        if current != c["original"]:
            continue
        if out is record:
            out = deep_copy(record)
        set_path(out, parts, c["corrected"])
        applied.append({"id": c["id"], "field": t["field"], "original": c["original"],
                        "confidence": c["confidence"], "problem": c["problem"]})
    return out, applied


def get_path(obj, parts):
    for p in parts:
        obj = obj[p]
    return obj


def set_path(obj, parts, value):
    get_path(obj, parts[:-1])[parts[-1]] = value


def deep_copy(obj):
    if isinstance(obj, dict):
        return {k: deep_copy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_copy(v) for v in obj]
    return obj


def target_matches(target, release, table, name):
    return (target.get("variable") == name
            and target.get("release") in (None, release)
            and target.get("table") in (None, table))


def member_matches(member, release, table, name):
    return (member.get("name") == name
            and member.get("release") in (None, release)
            and member.get("table") in (None, table))


def group_applies(group, release):
    return not group.get("releases") or release in group["releases"]


def field_origin(record, pointer):
    """The origin kind of the top-level field a pointer names."""
    top = pointer.strip("/").split("/")[0]
    prov = record.get("provenance", {})
    origin = prov.get("fields", {}).get(top) or prov.get("record") or {}
    return origin


def origin_label(origin):
    """The label a filter on a field with this origin supports, and {rule: version} if any."""
    kind = origin.get("origin")
    if kind in SOURCE_ORIGINS:
        return "complete", {}
    if kind == "rule":
        return "complete_by_rule", {origin["rule"]: origin.get("rule_version")}
    return "approximate", {}


def available_matches(entry, want):
    """An availability entry for the wanted wave, with the wanted form or no form at all."""
    if str(entry.get("wave")) != str(want["wave"]):
        return False
    if "form" not in want or "form" not in entry:
        return True
    return str(entry["form"]) == str(want["form"])


def question_text(record):
    return " ".join(q.get("text", "") for q in record.get("questions", []))


@dataclass
class Result:
    label: str
    filter: dict
    releases: list
    tables: list
    n_in_scope: int
    rule_versions: dict
    notes: list
    matches: list           # [(release, table, record)]

    def to_dict(self):
        return {
            "completeness": self.label,
            "filter": self.filter,
            "releases": self.releases,
            "tables": self.tables,
            "n_in_scope": self.n_in_scope,
            "rule_versions": self.rule_versions,
            "notes": self.notes,
            "count": len(self.matches),
            "results": [{"release": r, "table": t, "name": rec["name"], "label": rec.get("label")}
                        for r, t, rec in self.matches],
        }


def search(index, filt):
    """Apply a filter to an Index and return a labeled Result."""
    unknown = set(filt) - {"release", "table", "name", "group", "subject", "topic", "derived",
                         "available", "field", "text"}
    if unknown:
        raise ValueError(f"unknown filter keys: {sorted(unknown)}")

    releases = filt.get("release")
    if isinstance(releases, str):
        releases = [releases]
    scope = [(r, t, rec) for r, t, rec in index.entries
             if (releases is None or r in releases)
             and ("table" not in filt or t == filt["table"])]

    labels, rules, notes = ["complete"], {}, []
    preds = []

    if "name" in filt:
        want = filt["name"].lower()
        preds.append(lambda r, t, rec: rec["name"].lower() == want)

    for key in ("group", "subject"):
        if key not in filt:
            continue
        if key == "group":
            group = index.groups.get(filt["group"])
        else:
            want = filt["subject"].lower()
            group = next((g for g in index.groups.values() if g["kind"] == "subject"
                          and (g.get("label") or g["id"]).lower() == want), None)
        if group is None:
            raise ValueError(f"no {key} {filt[key]!r}")
        origin = group["origin"]
        kind = origin["origin"]
        if kind in SOURCE_ORIGINS:
            labels.append("complete")
        elif kind == "rule":
            labels.append("complete_by_rule")
            rules[origin["rule"]] = origin.get("rule_version")
        else:
            labels.append("approximate")
            notes.append(f"group {group['id']} has origin {kind}")
        preds.append(lambda r, t, rec, g=group: group_applies(g, r) and any(
            member_matches(m, r, t, rec["name"]) for m in g["members"]))

    if "topic" in filt:
        want = filt["topic"].lower()
        tags = [a for a in index.topics if a["value"].lower() == want]
        labels.append("approximate")
        notes.append("topic tags are annotations; a publisher's subjects are `subject` groups")
        preds.append(lambda r, t, rec, tags=tags: any(
            target_matches(a["target"], r, t, rec["name"]) for a in tags))

    for prop, value in (filt.get("derived") or {}).items():
        rows = [d for d in index.derived if d["property"] == prop and d["value"] == value]
        labels.append("complete_by_rule")
        for d in index.derived:
            if d["property"] == prop:
                rules[d["rule"]] = d["rule_version"]
        preds.append(lambda r, t, rec, rows=rows: any(
            target_matches(d["target"], r, t, rec["name"]) for d in rows))

    if "available" in filt:
        want = filt["available"]
        if "wave" not in want or set(want) - {"wave", "form"}:
            raise ValueError('available takes {"wave": W} or {"wave": W, "form": F}')
        for r, t, rec in scope:
            label, rule = origin_label(field_origin(rec, "/availability"))
            labels.append(label)
            if rule:
                rules.update(rule)

        def available_pred(r, t, rec, want=want):
            return any(available_matches(a, want) for a in rec.get("availability") or [])
        preds.append(available_pred)

    if "field" in filt:
        pointer, value = filt["field"]["pointer"], filt["field"]["equals"]
        parts = [int(p) if p.isdigit() else p for p in pointer.strip("/").split("/")]
        for r, t, rec in scope:
            origin = field_origin(rec, pointer)
            kind = origin.get("origin")
            if kind == "rule":
                labels.append("complete_by_rule")
                rules[origin["rule"]] = origin.get("rule_version")
            elif kind not in SOURCE_ORIGINS:
                labels.append("approximate")

        def field_pred(r, t, rec):
            try:
                return get_path(rec, parts) == value
            except (KeyError, IndexError, TypeError):
                return False
        preds.append(field_pred)

    if "text" in filt:
        want = filt["text"].lower()
        labels.append("approximate")
        notes.append("text search")
        preds.append(lambda r, t, rec: want in " ".join(
            [rec["name"], rec.get("label") or "", question_text(rec)]).lower())

    matches = [(r, t, rec) for r, t, rec in scope if all(p(r, t, rec) for p in preds)]
    return Result(
        label=worst(*labels),
        filter=filt,
        releases=sorted({r for r, _, _ in scope}),
        tables=sorted({t for _, t, _ in scope if t is not None}),
        n_in_scope=len(scope),
        rule_versions=rules,
        notes=notes,
        matches=matches,
    )

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
                     with form F or with no form (no form means everyone in that wave).
                     sample, mode, phase and geography work the same way:
                     {"wave": 2022, "geography": "25"} is asked in that state, or everywhere
    waves            W, [W, ...] or {"from": A, "to": B}: an availability entry for any of
                     those waves (any form); labeled like `available`
    field            {"pointer": "/measure", "equals": "categorical"}
    text             a substring of the name, label or question text, case-insensitive

The search assigns the completeness label from what the filter used; the caller
doesn't choose it:

    complete          only publisher, upstream_package, data_file or hand facts
    complete_by_rule  also derived properties or rule-made groups (rule versions listed)
    approximate       text search, annotations, or model-made facts

`pdt search` on the command line scopes a filter without `release` to the dataset's
current releases (default_releases), so a superseded release doesn't double every
result; `--release all` searches every release. `--names`, `--limit` and `--offset`
shorten the output (Result.to_dict); the total count is always given.

A publisher's subject lists are groups of kind `subject` (STANDARD.md §5.1), so a
subject filter is `complete` with respect to the publisher's list and the records in
scope. Topic annotations are never more than `approximate`.
"""

from dataclasses import dataclass, field

LABELS = ["complete", "complete_by_rule", "approximate"]
SOURCE_ORIGINS = {"publisher", "upstream_package", "data_file", "hand"}


def default_releases(dataset):
    """The releases a search covers when the filter names none: the current ones, else all."""
    releases = dataset.get("releases", [])
    current = [r["id"] for r in releases if r.get("status") == "current"]
    return current or [r["id"] for r in releases]


def wave_matcher(spec):
    """A predicate on a wave for the `waves` filter: W, [W, ...] or {"from": A, "to": B}."""
    if isinstance(spec, dict):
        if set(spec) - {"from", "to"} or not spec:
            raise ValueError('waves takes W, [W, ...] or {"from": A, "to": B}')
        lo, hi = spec.get("from"), spec.get("to")

        def in_range(w):
            try:
                x = float(str(w)[:4]) if not isinstance(w, (int, float)) else float(w)
            except ValueError:
                return False
            return (lo is None or x >= float(lo)) and (hi is None or x <= float(hi))
        return in_range
    wanted = {str(w) for w in (spec if isinstance(spec, list) else [spec])}
    return lambda w: str(w) in wanted


def page(items, limit=None, offset=0):
    """items[offset:offset+limit], and a description of the page for the output."""
    offset = max(offset or 0, 0)
    shown = items[offset:offset + limit] if limit is not None else items[offset:]
    return shown, {"offset": offset, "limit": limit, "returned": len(shown),
                   "more": offset + len(shown) < len(items)}


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
        if "code_list" in t:
            # A correction to a shared code list (STANDARD.md §4.5) applies to every record that
            # uses the list. The list's codes come first in the expanded values, so /codes/N is
            # /values/N.
            if record.get("code_list") != t["code_list"] or not t["field"].startswith("/codes/"):
                continue
            field = "/values/" + t["field"][len("/codes/"):]
        elif t["name"] != record["name"] or t.get("table") not in (None, table):
            continue
        else:
            field = t["field"]
        if t.get("releases") and release not in t["releases"]:
            continue
        parts = [int(p) if p.isdigit() else p for p in field.strip("/").split("/")]
        try:
            current = get_path(out, parts)
        except (KeyError, IndexError, TypeError):
            continue
        if current != c["original"]:
            continue
        if out is record:
            out = deep_copy(record)
        set_path(out, parts, c["corrected"])
        applied.append({"id": c["id"], "field": field, "original": c["original"],
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


AVAILABLE_DIMS = ("form", "sample", "mode", "phase", "geography")


def available_matches(entry, want):
    """An availability entry for the wanted wave whose other dimensions match the wanted ones.

    An entry without a dimension covers all of it (no form: everyone in the wave; no
    geography: every place), so it matches any wanted value of that dimension."""
    if str(entry.get("wave")) != str(want["wave"]):
        return False
    return all(d not in entry or str(entry[d]) == str(want[d]) for d in AVAILABLE_DIMS if d in want)


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

    def to_dict(self, names=False, limit=None, offset=0, scope_note=None):
        """The result as JSON. names: just the variable names; limit/offset: one page.

        `count` is always the total number of matches, whatever is shown.
        """
        rows = self.matches
        shown, pg = page(rows, limit, offset)
        out = {
            "completeness": self.label,
            "filter": self.filter,
            "releases": self.releases,
            "tables": self.tables,
            "n_in_scope": self.n_in_scope,
            "rule_versions": self.rule_versions,
            "notes": self.notes + ([scope_note] if scope_note else []),
            "count": len(rows),
        }
        if limit is not None or offset:
            out["page"] = pg
        if names:
            several = len(self.releases) > 1
            out["names"] = [(f"{r}:" if several else "") + (f"{t}." if t else "") + rec["name"]
                            for r, t, rec in shown]
            return out
        out["results"] = [{"release": r, "table": t, "name": rec["name"], "label": rec.get("label")}
                          for r, t, rec in shown]
        return out


def search(index, filt):
    """Apply a filter to an Index and return a labeled Result."""
    unknown = set(filt) - {"release", "table", "name", "group", "subject", "topic", "derived",
                         "available", "waves", "field", "text"}
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
        preds.append(lambda r, t, rec, want=want: rec["name"].lower() == want)

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
        if "wave" not in want or set(want) - {"wave", *AVAILABLE_DIMS}:
            raise ValueError('available takes {"wave": W}, with optional ' + ", ".join(AVAILABLE_DIMS)
                             + ', e.g. {"wave": W, "form": F}')
        for r, t, rec in scope:
            label, rule = origin_label(field_origin(rec, "/availability"))
            labels.append(label)
            if rule:
                rules.update(rule)

        def available_pred(r, t, rec, want=want):
            return any(available_matches(a, want) for a in rec.get("availability") or [])
        preds.append(available_pred)

    if "waves" in filt:
        in_waves = wave_matcher(filt["waves"])
        for r, t, rec in scope:
            label, rule = origin_label(field_origin(rec, "/availability"))
            labels.append(label)
            if rule:
                rules.update(rule)
        preds.append(lambda r, t, rec: any(in_waves(a.get("wave")) for a in rec.get("availability") or []))

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
        preds.append(lambda r, t, rec, want=want: want in " ".join(
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

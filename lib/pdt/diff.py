"""Compare two releases' records: `pdt diff <repo> <release-a> <release-b> [--table T]`.

Pairing: the links between the two releases (links.jsonl) pair variables first, and
names pair the rest. A release that renumbers its items (YRBSS: 2021 q26 "Considered
suicide" is 2023 q27) is then compared item by item, not number by number. A name present
in both releases whose links pair it elsewhere is listed under `name_conflicts`. Links
that aren't one-to-one (derived_from, split_from, merged_into) don't pair.

What it reports, per table (or for the release, when it has none):
- variables only in A, only in B, and rename candidates among them, ranked by similarity
  of label, question text and codes (candidates only: a link needs the publisher's word);
- merge and split candidates: a variable only in A that resembles a variable present in
  both (GSS strvbiasy, merged into strvbias in 7224r3a), or one only in B that resembles one
  in A;
- for each name in both: label, question-text and universe changes;
- code changes: codes added or dropped, relabeled, or moved between kinds (valid,
  missing, unresolved) or missing types.

A text difference that disappears after normalizing case, whitespace and dashes is
reported as `text_only`, separately from a real change: the FARS records write
"Dark - Not Lighted" where the manual has "Dark – Not Lighted". One that disappears
once questionnaire item references are removed ("IC-9" vs "IC-7", "(FC A-2b)") is
`reference_only`. Neither counts as a change in the proposed relations.

With --proposals DIR it also writes, for review:
- links.jsonl: one link per name in both releases, with relations read off the records
  (same_item, labels_changed, codes_changed, wording_changed, universe_changed) and
  `origin: rule` (release_diff). STANDARD.md §5.2 says links record continuity the
  publisher asserts, so these are proposals: keep one only when the publisher's naming
  convention or notes back it, and cite that source instead.
- histories.jsonl: a two-period code history (STANDARD.md §5.4) for each variable whose
  codes changed. Rows pair by label first, so a code that changes for the same answer
  (WEATHER's Unknown, 9 to 99) is one row, and a code whose meaning changes (LGT_COND 9,
  Unknown to Reported as Unknown) is two.

Codes on one side only are explained, when the records allow, instead of counted as
changes: a code inside the other release's valid_range (NSFG 2017-2019 prints AGE_R
49 and 50 as a range row, "49-50") is `in_other_range`. When the release missing the code is
documented by a source with `lists_only_occurring_codes: true` in sources.yaml (the NSFG's
codebooks), a code on one side only is `no_cases_in_other` if its absence is plausible as
chance (pdt.compare.absent_by_chance: n scaled to the other release, under 5).
--omitted-codes-have-no-cases forces this for every source.
PREGORDR 15 (1 case) passes; MARSTAT 6 "Never been married" (2,820 cases in 2017-2019,
gone from 2022-2023's coding) doesn't, so a recoding still reads as codes changed.
Added and dropped codes show their `n` (cases, as the codebook prints them) when the
records have it.

It reads the source records as published (corrections are listed, not applied) and
never writes into metadata/.
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

from . import __version__
from .check import Repo
from .compare import absent_by_chance, compare_text, norm, total_cases
from .ranges import bounds, comparable as comparable_ranges, in_valid_range, valid_ranges, without_notes

RULE = "release_diff"
RULE_VERSION = "0.1"
RENAME_THRESHOLD = 0.6


def question(rec):
    return " / ".join(q.get("text", "") for q in rec.get("questions") or [])


def code_key(code):
    """Codes compared by type and value: 1 == 1.0, '1' is not 1."""
    if isinstance(code, str):
        return ("s", code)
    return ("n", float(code))


def in_range(code, record):
    return not isinstance(code, str) and in_valid_range(record, code)


def code_entry(v):
    out = {"code": v["code"], "label": v.get("label"), "kind": v.get("kind")}
    if "n" in v:
        out["n"] = v["n"]
    return out


def code_changes(a, b, omits=(False, False), ignore=()):
    """Differences between two value lists, as a dict of lists.

    omits: whether a's and b's documentation lists only codes that occur.
    ignore: formatting markers to ignore in labels (pdt.compare)."""
    va = {code_key(v["code"]): v for v in a.get("values") or []}
    vb = {code_key(v["code"]): v for v in b.get("values") or []}
    out = {"added": [], "dropped": [], "in_other_range": [], "no_cases_in_other": [],
           "relabeled": [], "relabeled_text_only": [], "kind_changed": []}
    totals = (total_cases(a), total_cases(b))

    def plausibly_absent(v, side):
        """The release lacking the code lists only occurring codes, and zero there is chance."""
        if side == "added":                          # missing from a
            return omits[0] and absent_by_chance(v.get("n"), totals[1], totals[0])
        return omits[1] and absent_by_chance(v.get("n"), totals[0], totals[1])
    for k in sorted(set(va) | set(vb), key=lambda k: (k[0], k[1])):
        x, y = va.get(k), vb.get(k)
        if x is None or y is None:
            v, other, side = (y, a, "added") if x is None else (x, b, "dropped")
            entry = code_entry(v)
            if in_range(v["code"], other):
                out["in_other_range"].append({**entry, "side": side})
            elif plausibly_absent(v, side):
                out["no_cases_in_other"].append({**entry, "side": side})
            else:
                out[side].append(entry)
        else:
            how = compare_text(x.get("label"), y.get("label"), ignore)
            if how != "same":
                out["relabeled" if how == "changed" else "relabeled_text_only"].append(
                    {"code": y["code"], "from": x.get("label"), "to": y.get("label")})
            if x.get("kind") != y.get("kind") or sorted(x.get("missing_types") or []) != sorted(
                    y.get("missing_types") or []):
                out["kind_changed"].append({"code": y["code"],
                                            "from": [x.get("kind"), x.get("missing_types") or []],
                                            "to": [y.get("kind"), y.get("missing_types") or []]})
    return {k: v for k, v in out.items() if v}


def numeric_codes(record):
    return [v["code"] for v in record.get("values") or []
            if v.get("kind") == "valid" and isinstance(v["code"], (int, float)) and not isinstance(v["code"], bool)]


def range_origin(record):
    prov = record.get("provenance") or {}
    return ((prov.get("fields") or {}).get("valid_range") or prov.get("record") or {}).get("origin")


def range_changed(a, b):
    """How the valid range changed: "documented", "observed", or None.

    "documented" is a moved range (FPOVCUT's documented cap went from 60000 to 99999), and so is
    any change in top or bottom coding: the link relation `range_changed` (STANDARD.md §5.2). "observed" is a range read from each
    release's data (origin data_file: FARS MOD_YEAR 1927-2018 vs 1929-2025), reported but
    not a change. Identifiers aren't compared: their range is which ids a release used.

    Both state a range: compare min and max. Only one does: a change only if the other
    release's valid codes fall outside it (NSFG 2017-2019 gives AGE_R as 15-50, 2022-2023
    lists 15 to 50 one by one: no change)."""
    if "identifier" in (a.get("measure"), b.get("measure")):
        return None
    va, vb = valid_ranges(a), valid_ranges(b)
    if va and vb:
        ca, cb = comparable_ranges(a), comparable_ranges(b)
        if [c[3:] for c in ca] != [c[3:] for c in cb] or len(ca) != len(cb):
            return "documented"      # top/bottom coding, or the number of ranges, changed
        if [c[:2] for c in ca] == [c[:2] for c in cb]:
            return None
    elif va or vb:
        stated, other = (a, b) if va else (b, a)
        if not any(bounds(r) for r in valid_ranges(stated)) or all(
                in_valid_range(stated, c) for c in numeric_codes(other)):
            return None
    else:
        return None
    observed = all(range_origin(r) == "data_file" for r in (a, b) if r.get("valid_range"))
    return "observed" if observed else "documented"


def compare_pair(a, b, omits=(False, False), ignore=()):
    """Every difference between two records of the same variable.

    ignore: a dataset's formatting markers, as regular expressions (pdt.compare)."""
    out = {}
    for field, getter in (("label", lambda r: r.get("label")), ("question", question),
                          ("universe", lambda r: r.get("universe")),
                          ("description", lambda r: r.get("description"))):
        how = compare_text(getter(a), getter(b), ignore)
        if how != "same":
            out[field] = {"how": how, "from": getter(a), "to": getter(b)}
    codes = code_changes(a, b, omits, ignore)
    if codes:
        out["codes"] = codes
    how = range_changed(a, b)
    if how:
        out["valid_range"] = {"how": how,
                              "from": without_notes(a), "to": without_notes(b)}
    if a.get("implied_decimals") != b.get("implied_decimals"):
        out["implied_decimals"] = {"from": a.get("implied_decimals"), "to": b.get("implied_decimals")}
    if a.get("flag_for") != b.get("flag_for"):
        out["flag_for"] = {"from": a.get("flag_for"), "to": b.get("flag_for")}
    numbers = lambda r: [q.get("number") for q in r.get("questions") or []]
    if any(numbers(a)) or any(numbers(b)):
        if numbers(a) != numbers(b):
            out["question_number"] = {"how": "reference_only", "from": numbers(a), "to": numbers(b)}
    if a.get("measure") != b.get("measure"):
        out["measure"] = {"from": a.get("measure"), "to": b.get("measure")}
    return out


def relations(changes):
    """Link relations read off the differences (STANDARD.md §5.2)."""
    rel = []
    codes = changes.get("codes", {})
    if (codes.get("added") or codes.get("dropped") or codes.get("kind_changed")
            or "implied_decimals" in changes):
        rel.append("codes_changed")
    if changes.get("valid_range", {}).get("how") == "documented":
        rel.append("range_changed")      # the range or top code moved; the codes kept their meaning
    if codes.get("relabeled") or changes.get("label", {}).get("how") == "changed":
        rel.append("labels_changed")
    if changes.get("question", {}).get("how") == "changed":
        rel.append("wording_changed")
    if changes.get("universe", {}).get("how") == "changed":
        rel.append("universe_changed")
    return rel or ["same_item"]


def similarity(a, b):
    """0..1: how alike two records are, for rename candidates."""
    def ratio(x, y):
        x, y = norm(x), norm(y)
        if not x and not y:
            return None
        return difflib.SequenceMatcher(None, x, y).ratio()
    parts = [r for r in (ratio(a.get("label"), b.get("label")), ratio(question(a), question(b))) if r is not None]
    ca = {(code_key(v["code"]), norm(v.get("label"))) for v in a.get("values") or []}
    cb = {(code_key(v["code"]), norm(v.get("label"))) for v in b.get("values") or []}
    if ca or cb:
        parts.append(len(ca & cb) / len(ca | cb))
    return sum(parts) / len(parts) if parts else 0.0


def rename_candidates(only_a, only_b, threshold=RENAME_THRESHOLD):
    """Greedy one-to-one pairs of (A record, B record, score), best first."""
    scored = sorted(((similarity(a, b), a["name"], b["name"], a, b) for a in only_a for b in only_b),
                    key=lambda t: (-t[0], t[1], t[2]))
    used_a, used_b, out = set(), set(), []
    for score, na, nb, a, b in scored:
        if score < threshold or na in used_a or nb in used_b:
            continue
        used_a.add(na)
        used_b.add(nb)
        out.append({"from": na, "to": nb, "score": round(score, 3)})
    return out


def merge_split_candidates(only_a, only_b, ra, rb, renamed, threshold=RENAME_THRESHOLD):
    """Unpaired variables that resemble a variable on the other side that's already paired."""
    out = []
    taken_a = {c["from"] for c in renamed}
    taken_b = {c["to"] for c in renamed}
    for a in only_a:
        if a["name"] in taken_a:
            continue
        best = max(((similarity(a, b), b["name"]) for b in rb.values()), default=(0, None))
        if best[0] >= threshold:
            out.append({"kind": "merge", "from": a["name"], "to": best[1], "score": round(best[0], 3)})
    for b in only_b:
        if b["name"] in taken_b:
            continue
        best = max(((similarity(a, b), a["name"]) for a in ra.values()), default=(0, None))
        if best[0] >= threshold:
            out.append({"kind": "split", "from": best[1], "to": b["name"], "score": round(best[0], 3)})
    return out


PAIRING = {"same_item", "renamed", "wording_changed", "codes_changed", "labels_changed", "range_changed",
           "universe_changed", "data_revised"}


class Linked(dict):
    """{name in A: name in B} from links, with each pair's relations in .relations."""

    def __init__(self):
        super().__init__()
        self.relations = {}


def linked_pairs(repo, rel_a, rel_b, table, ra, rb, table_b=...):
    """One-to-one pairs from the links between two releases, for one table in A and its
    counterpart in B (the same table unless table_b is given: NHIS samadult -> adult)."""
    if table_b is ...:
        table_b = table
    out = Linked()
    for link in repo.links:
        f, t = link["from"], link["to"]
        if not PAIRING & set(link["relations"]):
            continue
        if (f.get("release"), t.get("release")) == (rel_a, rel_b):
            a, b = f, t
        elif (f.get("release"), t.get("release")) == (rel_b, rel_a):
            a, b = t, f
        else:
            continue
        if a.get("table") != table or b.get("table") != table_b:
            continue
        if a["name"] in ra and b["name"] in rb and a["name"] not in out and b["name"] not in out.values():
            out[a["name"]] = b["name"]
            out.relations[(a["name"], b["name"])] = link["relations"]
    return out


def comparable(rels):
    """Relations as the records can show them: without renamed, and without same_item beside others."""
    out = set(rels) - {"renamed", "data_revised"}
    if len(out) > 1:
        out.discard("same_item")
    return out or {"same_item"}


NO_TABLE = object()        # "no counterpart"; a release without tables has the table id None


def table_pairs(repo, rel_a, rel_b, table_map=None):
    """[(table in A, table in B)]: which table continues which; NO_TABLE where there's none.

    In order: table_map (e.g. {"samadult": "adult"}); then the same id (None for a release
    without tables); then the table in B that most of the table's one-to-one links go to.
    Several tables can continue as one (NHIS 2018 -> 2019: samadult, person and family
    became adult): table_map may repeat a target, and links may vote for a table already used."""
    ta, tb = list(repo.tables.get(rel_a, {})), list(repo.tables.get(rel_b, {}))
    table_map = dict(table_map or {})
    out, used = {}, set()
    for t in ta:
        if t in table_map:
            if table_map[t] not in tb:
                raise SystemExit(f"--table-map: {rel_b} has no table {table_map[t]!r}; tables: {tb}")
            out[t] = table_map[t]
            used.add(table_map[t])
    for t in ta:
        if t not in out and t in tb and t not in used:
            out[t] = t
            used.add(t)
    for t in ta:
        if t in out:
            continue
        votes = {}
        for link in repo.links:
            if not PAIRING & set(link["relations"]):
                continue
            ends = [(e.get("release"), e.get("table")) for e in (link["from"], link["to"])]
            if (rel_a, t) in ends:
                for r, x in ends:
                    if r == rel_b and x in tb:
                        votes[x] = votes.get(x, 0) + 1
        if votes:
            target = max(sorted(votes, key=str), key=lambda x: votes[x])
            out[t] = target
            used.add(target)
    pairs = [(t, out.get(t, NO_TABLE)) for t in ta]
    pairs += [(NO_TABLE, x) for x in tb if x not in used]
    return pairs


def lists_only_occurring(repo, record):
    """Whether the source documenting a record's codes lists only codes that occur."""
    sources = {s["id"]: s for s in (repo.sources or {}).get("sources", [])}
    prov = record.get("provenance") or {}
    ids = [(record.get("source_location") or {}).get("source"),
           ((prov.get("fields") or {}).get("values") or {}).get("source"),
           (prov.get("record") or {}).get("source")]
    return any(sources.get(i, {}).get("lists_only_occurring_codes") for i in ids if i)


def waves_span(records):
    waves = sorted({a["wave"] for r in records for a in r.get("availability") or [] if "wave" in a
                    and isinstance(a["wave"], int)})
    return {"from": waves[0], "to": waves[-1]} if waves else None


def code_list_changes(repo, rel_a, rel_b):
    """Shared code lists (STANDARD.md §4.5) compared once, not per variable: for each variable
    that names a list in either release, the list in each; then each pair of different lists,
    with the codes added, dropped, relabeled and newly retired. The same content under another
    id isn't a change."""
    lists = {cl["id"]: cl for cl in repo.code_lists}
    used = {}
    for rel in (rel_a, rel_b):
        for tab, recs in repo.stored.get(rel, {}).items():
            for r in recs:
                if r.get("code_list"):
                    used.setdefault((tab, r["name"]), {})[rel] = r["code_list"]
    pairs = sorted({(u.get(rel_a), u.get(rel_b)) for u in used.values() if u.get(rel_a) != u.get(rel_b)},
                   key=lambda p: (str(p[0]), str(p[1])))
    out = []
    for a, b in pairs:
        ca = {code_key(c["code"]): c for c in (lists.get(a) or {}).get("codes", [])}
        cb = {code_key(c["code"]): c for c in (lists.get(b) or {}).get("codes", [])}
        change = {"from": a, "to": b,
                  "variables": sorted(f"{t + '/' if t else ''}{n}" for (t, n), u in used.items()
                                      if (u.get(rel_a), u.get(rel_b)) == (a, b)),
                  "added": [cb[k]["code"] for k in sorted(set(cb) - set(ca))],
                  "dropped": [ca[k]["code"] for k in sorted(set(ca) - set(cb))],
                  "relabeled": [cb[k]["code"] for k in sorted(set(ca) & set(cb)) if ca[k].get("label") != cb[k].get("label")],
                  "retired": [cb[k]["code"] for k in sorted(set(ca) & set(cb))
                              if cb[k].get("retired") and not ca[k].get("retired")]}
        change["same_content"] = a is not None and b is not None and not any(
            change[k] for k in ("added", "dropped", "relabeled", "retired"))
        out.append(change)
    return out


def diff(repo, rel_a, rel_b, table=None, omitted_codes_have_no_cases=False, ignore=(), table_map=None):
    """The full comparison, as a dict that serializes to JSON.

    Tables are paired by table_pairs (same id, links, or table_map), so a redesign that
    renames tables (NHIS samadult -> adult) is compared variable by variable."""
    for rel in (rel_a, rel_b):
        if rel not in repo.tables:
            raise SystemExit(f"no release {rel!r}; releases: {sorted(repo.tables)}")
    pairs_of_tables = table_pairs(repo, rel_a, rel_b, table_map)
    if table is not None:
        pairs_of_tables = [(x, y) for x, y in pairs_of_tables if table in (x, y)]
    periods = {r["id"]: r.get("reference_period") for r in repo.dataset.get("releases", [])}
    result = {"dataset": repo.dataset.get("id"), "from": rel_a, "to": rel_b, "tables": [],
              "reference_periods": {rel_a: periods.get(rel_a), rel_b: periods.get(rel_b)},
              "corrections": [c["id"] for c in repo.corrections],
              "rule": RULE, "rule_version": RULE_VERSION, "pdt_version": __version__,
              "omitted_codes_have_no_cases": omitted_codes_have_no_cases,
              "code_lists": code_list_changes(repo, rel_a, rel_b),
              "ignore": [getattr(p, "pattern", p) for p in ignore]}
    # First pass: pair variables within each table pair (links, then names). In a merge (several
    # tables in A continuing as one in B), B's variables are claimed across all its pairs.
    work, claimed = [], {}
    for tab_a, tab_b in pairs_of_tables:
        ra = {r["name"]: r for r in repo.tables[rel_a].get(tab_a, [])} if tab_a is not NO_TABLE else {}
        rb = {r["name"]: r for r in repo.tables[rel_b].get(tab_b, [])} if tab_b is not NO_TABLE else {}
        taken = claimed.setdefault(tab_b, set()) if tab_b is not NO_TABLE else set()
        linked = linked_pairs(repo, rel_a, rel_b, tab_a, ra, rb, tab_b)
        pairs = [(a, b) for a, b in linked.items() if b not in taken]
        paired_a, paired_b = {p[0] for p in pairs}, {p[1] for p in pairs} | taken
        # then names, among the variables no link pairs; names that differ only in case match
        lower_b = {n.lower(): n for n in rb if n not in paired_b}
        for n in ra:
            if n in paired_a:
                continue
            m = n if (n in rb and n not in paired_b) else lower_b.get(n.lower())
            if m is not None and m not in paired_b:
                pairs.append((n, m))
                paired_a.add(n)
                paired_b.add(m)
        conflicts = []
        for n in sorted(set(ra) & set(rb)):
            if linked.get(n) != n and (n in linked or n in set(linked.values())):
                conflicts.append({"name": n,
                                  "from_linked_to": linked.get(n) if n in linked else None,
                                  "to_linked_from": next((a for a, b in linked.items() if b == n), None)})
        taken |= {b for _, b in pairs}
        work.append((tab_a, tab_b, ra, rb, linked, pairs, conflicts))
    # Second pass: B's leftovers, listed once per B table (with its first pair)
    listed = set()
    for tab_a, tab_b, ra, rb, linked, pairs, conflicts in work:
        tab = tab_b if tab_b is not NO_TABLE else tab_a
        paired_a = {p[0] for p in pairs}
        only_a = [ra[n] for n in ra if n not in paired_a]
        if tab_b is not NO_TABLE and tab_b not in listed:
            only_b = [rb[n] for n in rb if n not in claimed.get(tab_b, set())]
            listed.add(tab_b)
        else:
            only_b = []
        both = []
        for na, nb in pairs:
            omits = (omitted_codes_have_no_cases or lists_only_occurring(repo, ra[na]),
                     omitted_codes_have_no_cases or lists_only_occurring(repo, rb[nb]))
            changes = compare_pair(ra[na], rb[nb], omits, ignore)
            entry = {"from": na, "to": nb, "paired_by": "link" if (na, nb) in linked.items() else "name",
                     "relations": relations(changes), "changes": changes}
            if entry["paired_by"] == "link":
                entry["link_relations"] = linked.relations[(na, nb)]
                entry["link_agrees"] = comparable(entry["relations"]) == comparable(entry["link_relations"])
            if na != nb and na.lower() == nb.lower():
                entry["name_case_changed"] = True
            both.append(entry)
        leftover_b = [rb[n] for n in rb if n not in claimed.get(tab_b, set())] if tab_b is not NO_TABLE else []
        result["tables"].append({
            "table": tab,
            "from_table": tab_a if tab_a is not NO_TABLE else None,
            "only_table": ("from" if tab_b is NO_TABLE else "to" if tab_a is NO_TABLE else None),
            "only_in_from": [r["name"] for r in only_a],
            "only_in_to": [r["name"] for r in only_b],
            "rename_candidates": (renamed := rename_candidates(only_a, leftover_b)),
            "merge_split_candidates": merge_split_candidates(only_a, leftover_b, ra, rb, renamed),
            "name_conflicts": conflicts,
            "in_both": both,
            "spans": {"from": waves_span(ra.values()), "to": waves_span(rb.values())},
        })
    return result


# ---------------------------------------------------------------- over gaps

def gaps(repo, releases=None, ignore=(), table_map=None, omitted_codes_have_no_cases=False):
    """Each variable compared with the next release it appears in, where that skips releases.

    Rotating content (NHIS: PHQ and GAD in 2019 and 2022, K6 in 2021 and 2024) is missed by
    diffs of consecutive releases. A variable's next appearance is found by a one-to-one link
    to a later release, else by the same name in the counterpart table (table_pairs) of the
    nearest later release that has it. Pairs in consecutive releases are left to diff().
    Returns [{from_release, to_release, skipped, table, from, to, paired_by, relations,
    changes, link_relations?, link_agrees?}]."""
    from .views import release_order
    order = [r for r in release_order(repo.dataset) if releases is None or r in releases]
    pos = {r: i for i, r in enumerate(order)}
    records = {(rel, tab, rec["name"]): rec for rel in order for tab, recs in repo.tables.get(rel, {}).items()
               for rec in recs}
    nxt = {}                                      # node -> (later node, relations or None)
    for link in repo.links:
        if not PAIRING & set(link["relations"]):
            continue
        a = (link["from"].get("release"), link["from"].get("table"), link["from"]["name"])
        b = (link["to"].get("release"), link["to"].get("table"), link["to"]["name"])
        if a not in records or b not in records or a[0] == b[0]:
            continue
        a, b = (a, b) if pos[a[0]] < pos[b[0]] else (b, a)
        if a not in nxt or pos[b[0]] < pos[nxt[a][0][0]]:
            nxt[a] = (b, link["relations"])
    linked_to = {b for b, _ in nxt.values()}
    maps = {}
    for i, rel in enumerate(order):
        for later in order[i + 1:]:
            maps[(rel, later)] = {x: y for x, y in table_pairs(repo, rel, later, table_map)
                                  if x is not NO_TABLE and y is not NO_TABLE}
    for node in records:
        if node in nxt:
            continue
        rel, tab, name = node
        for later in order[pos[rel] + 1:]:
            target_tab = maps[(rel, later)].get(tab, NO_TABLE)
            cand = (later, target_tab, name)
            if target_tab is not NO_TABLE and cand in records:
                if cand not in linked_to:
                    nxt[node] = (cand, None)
                break
    out = []
    for a, (b, link_rel) in sorted(nxt.items(), key=lambda kv: (pos[kv[0][0]], str(kv[0][1]), kv[0][2])):
        if pos[b[0]] - pos[a[0]] < 2:
            continue
        omits = (omitted_codes_have_no_cases or lists_only_occurring(repo, records[a]),
                 omitted_codes_have_no_cases or lists_only_occurring(repo, records[b]))
        changes = compare_pair(records[a], records[b], omits, ignore)
        entry = {"from_release": a[0], "to_release": b[0], "skipped": order[pos[a[0]] + 1:pos[b[0]]],
                 "from_table": a[1], "table": b[1], "from": a[2], "to": b[2],
                 "paired_by": "link" if link_rel else "name", "relations": relations(changes), "changes": changes}
        if link_rel:
            entry["link_relations"] = link_rel
            entry["link_agrees"] = comparable(entry["relations"]) == comparable(link_rel)
        out.append(entry)
    return out


def gaps_summary(dataset, entries):
    lines = [f"{dataset}: variables whose next appearance skips releases ({len(entries)})"]
    for e in entries:
        where = (f"{e['from_table']}." if e["from_table"] else "") + e["from"]
        to = (f"{e['table']}." if e["table"] else "") + e["to"]
        link = (f"  [link: {', '.join(e['link_relations'])}{'' if e['link_agrees'] else '; differs'}]"
                if e["paired_by"] == "link" else "  [by name]")
        lines.append(f"  {where} {e['from_release']} \u2192 {to} {e['to_release']} (skips {', '.join(e['skipped'])}): "
                     f"{', '.join(e['relations'])}{link}")
        for field, v in e["changes"].items():
            if field == "codes":
                kinds = [k for k in v if k not in ("relabeled_text_only",)]
                if kinds:
                    lines.append(f"      codes: {', '.join(kinds)}")
            elif isinstance(v, dict) and "how" in v and v["how"] != "changed":
                continue
            else:
                lines.append(f"      {field}")
    return "\n".join(lines)


# ---------------------------------------------------------------- proposals

def proposed_links(result):
    out = []
    for t in result["tables"]:
        for e in t["in_both"]:
            def ref(rel, name, tab):
                return {"release": rel, **({"table": tab} if tab else {}), "name": name}
            what = "; ".join(f"{k}: {v['how'] if isinstance(v, dict) and 'how' in v else ', '.join(v)}"
                             for k, v in e["changes"].items()) or "no differences in the records"
            out.append({"from": ref(result["from"], e["from"], t.get("from_table", t["table"])),
                        "to": ref(result["to"], e["to"], t["table"]),
                        "relations": e["relations"],
                        "origin": {"origin": "rule", "rule": RULE, "rule_version": RULE_VERSION,
                                   "note": f"Proposed by pdt diff from the two releases' records ({what}). "
                                           "Keep it only if the publisher's notes or naming convention "
                                           "say the variable continues; cite that source."}})
    return out


def proposed_history(table, name_a, name_b, rec_a, rec_b, span_a, span_b, release_a, release_b):
    """A two-period history: rows pair by label, then by code."""
    va = list(rec_a.get("values") or [])
    vb = list(rec_b.get("values") or [])
    rows, used_b = [], set()
    by_label = {}
    for i, v in enumerate(vb):
        by_label.setdefault(norm(v.get("label")), []).append(i)
    for v in va:
        cand = [i for i in by_label.get(norm(v.get("label")), []) if i not in used_b]
        if cand:
            used_b.add(cand[0])
            rows.append({"label": v.get("label") or "", "codes": [v["code"], vb[cand[0]]["code"]]})
        else:
            rows.append({"label": v.get("label") or "", "codes": [v["code"], None]})
    for i, v in enumerate(vb):
        if i not in used_b:
            rows.append({"label": v.get("label") or "", "codes": [None, v["code"]]})
    period = lambda span, rel: span or {"from": rel}
    names = [{"name": name_a, "waves": period(span_a, release_a)}]
    if name_b != name_a:
        names.append({"name": name_b, "waves": period(span_b, release_b)})
    return {"id": f"{table}/{name_b}" if table else name_b, **({"table": table} if table else {}),
            "name": name_b, "label": rec_b.get("label") or "", "names": names,
            "periods": [period(span_a, release_a), period(span_b, release_b)], "attributes": rows,
            "origin": {"origin": "rule", "rule": RULE, "rule_version": RULE_VERSION,
                       "note": f"Proposed by pdt diff from the {release_a} and {release_b} records. Rows pair "
                               "by label (case, spacing and dashes ignored), then stand alone; labels are "
                               f"{release_a}'s where they pair. A publisher's matrix, if there is one, is "
                               "the source to use instead."}}


def proposed_histories(repo, result):
    out = []
    for t in result["tables"]:
        ra = {r["name"]: r for r in repo.tables[result["from"]].get(t.get("from_table", t["table"]), [])}
        rb = {r["name"]: r for r in repo.tables[result["to"]].get(t["table"], [])}
        for e in t["in_both"]:
            codes = e["changes"].get("codes", {})
            if codes.get("added") or codes.get("dropped") or codes.get("relabeled"):
                out.append(proposed_history(t["table"], e["from"], e["to"], ra[e["from"]], rb[e["to"]],
                                            t["spans"]["from"], t["spans"]["to"], result["from"], result["to"]))
    return out


def write_proposals(repo, result, directory):
    directory = Path(directory).resolve()
    meta = (repo.root / "metadata").resolve()
    if directory == meta or meta in directory.parents:
        raise SystemExit("pdt diff never writes into metadata/; give a directory for review")
    directory.mkdir(parents=True, exist_ok=True)
    links, hists = proposed_links(result), proposed_histories(repo, result)
    for name, rows in (("links.jsonl", links), ("histories.jsonl", hists)):
        (directory / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    return len(links), len(hists)


# ---------------------------------------------------------------- report

def summary(result):
    lines = [f"{result['dataset']}: {result['from']} -> {result['to']}"]
    rp = result.get("reference_periods") or {}
    if any(rp.values()):
        lines.append(f"  reference periods: {result['from']} {rp.get(result['from'])}; "
                     f"{result['to']} {rp.get(result['to'])}")
    for c in result.get("code_lists") or []:
        if c["from"] is None or c["to"] is None:
            what = f"starts using {c['to']}" if c["from"] is None else f"stops using {c['from']}"
        elif c["same_content"]:
            what = f"{c['from']} -> {c['to']}: same codes and labels"
        else:
            what = f"{c['from']} -> {c['to']}: " + "; ".join(
                f"{len(c[k])} {k}" for k in ("added", "dropped", "relabeled", "retired") if c[k])
        lines.append(f"  code list: {what} ({len(c['variables'])} variables: {', '.join(c['variables'][:5])}"
                     + (", ..." if len(c["variables"]) > 5 else "") + ")")
    for t in result["tables"]:
        both = t["in_both"]
        rel_counts = {}
        for e in both:
            key = ", ".join(e["relations"])
            rel_counts[key] = rel_counts.get(key, 0) + 1
        ta, tb = t.get("from_table", t["table"]), t["table"]
        if t.get("only_table") == "from":
            head = f"\n[{ta}: only in {result['from']}]"
        elif t.get("only_table") == "to":
            head = f"\n[{tb}: only in {result['to']}]"
        elif ta != tb:
            head = f"\n[{ta} \u2192 {tb}]"
        else:
            head = f"\n[{tb}]" if tb else ""
        by_link = [e for e in both if e["paired_by"] == "link"]
        disagree = [e for e in by_link if not e["link_agrees"]]
        lines.append(f"{head}\n  paired by link: {len(by_link)}  by name: {len(both) - len(by_link)}"
                     + (f"  (links whose relations the records don't match: {len(disagree)})" if by_link else ""))
        lines.append(f"  in both: {len(both)}  only in {result['from']}: {len(t['only_in_from'])}  "
                     f"only in {result['to']}: {len(t['only_in_to'])}  rename candidates: "
                     f"{len(t['rename_candidates'])}")
        for k, n in sorted(rel_counts.items()):
            lines.append(f"    {n:4}  {k}")
        for e in both:
            if e["relations"] == ["same_item"] and not e["changes"]:
                continue
            via = f" (linked from {e['from']})" if e["paired_by"] == "link" and e["from"] != e["to"] else ""
            linked_as = (f"  [link: {', '.join(e['link_relations'])}{'' if e['link_agrees'] else '; differs'}]"
                         if e["paired_by"] == "link" else "")
            lines.append(f"  {e['to']}{via}: {', '.join(e['relations'])}{linked_as}")
            for field, v in e["changes"].items():
                if field == "codes":
                    for kind, items in v.items():
                        def show(i):
                            if "from" in i:
                                return f"{i['code']} {i['from']!r} -> {i['to']!r}"
                            text = f"{i['code']} {i.get('label') or ''}".strip()
                            if "n" in i:
                                text += f" (n={i['n']})"
                            return text + (f" [{i['side']}]" if "side" in i else "")
                        shown = "; ".join(show(i) for i in items[:6])
                        more = f" (+{len(items) - 6})" if len(items) > 6 else ""
                        lines.append(f"      codes {kind}: {shown}{more}")
                elif field == "valid_range":
                    lines.append(f"      valid_range ({v['how']}): {v['from']} -> {v['to']}")
                elif field in ("measure", "implied_decimals", "flag_for"):
                    lines.append(f"      {field}: {v['from']} -> {v['to']}")
                elif field == "question_number":
                    lines.append(f"      question number (reference_only): {v['from']} -> {v['to']}")
                else:
                    lines.append(f"      {field} ({v['how']})")
        for c in t["rename_candidates"]:
            lines.append(f"  rename candidate: {c['from']} -> {c['to']} (similarity {c['score']})")
        for c in t["name_conflicts"]:
            lines.append(f"  name conflict: {c['name']} is in both releases, but links pair "
                         + "; ".join(x for x in (
                             f"{result['from']} {c['name']} with {result['to']} {c['from_linked_to']}"
                             if c["from_linked_to"] else None,
                             f"{result['to']} {c['name']} with {result['from']} {c['to_linked_from']}"
                             if c["to_linked_from"] else None) if x))
        for c in t["merge_split_candidates"]:
            lines.append(f"  {c['kind']} candidate: {c['from']} -> {c['to']} (similarity {c['score']})")
        if t["only_in_from"]:
            lines.append(f"  only in {result['from']}: {', '.join(t['only_in_from'][:20])}"
                         + (" ..." if len(t["only_in_from"]) > 20 else ""))
        if t["only_in_to"]:
            lines.append(f"  only in {result['to']}: {', '.join(t['only_in_to'][:20])}"
                         + (" ..." if len(t["only_in_to"]) > 20 else ""))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pdt diff", description="Compare two releases' records.")
    parser.add_argument("path", help="the dataset repo")
    parser.add_argument("release_a", nargs="?")
    parser.add_argument("release_b", nargs="?")
    parser.add_argument("--table", help="only this table (and its counterpart)")
    parser.add_argument("--table-map", action="append", default=[], metavar="A=B",
                        help="table A in the first release continues as table B (repeatable)")
    parser.add_argument("--ignore", action="append", default=[], metavar="REGEX",
                        help="a formatting marker to ignore in texts, e.g. '(?:^|(?<=\\s))\\*\\s' (repeatable)")
    parser.add_argument("--gaps", action="store_true",
                        help="compare each variable with the next release it appears in, where that skips "
                             "releases (rotating content); no release arguments")
    parser.add_argument("--releases", nargs="+", help="with --gaps: only these releases")
    parser.add_argument("--json", action="store_true", help="print the full comparison as JSON")
    parser.add_argument("--omitted-codes-have-no-cases", action="store_true",
                        help="treat every source as listing only codes that occur (overrides sources.yaml's "
                             "lists_only_occurring_codes)")
    parser.add_argument("--proposals", metavar="DIR",
                        help="write proposed links.jsonl and histories.jsonl here, for review")
    args = parser.parse_args(argv)
    repo = Repo.load(args.path)
    table_map = {}
    for item in args.table_map:
        if "=" not in item:
            parser.error(f"--table-map takes A=B, not {item!r}")
        a, b = item.split("=", 1)
        table_map[a] = b
    ignore = [re.compile(p) for p in args.ignore]
    if args.gaps:
        if args.release_a or args.release_b:
            parser.error("--gaps compares across all releases; use --releases to limit them")
        entries = gaps(repo, args.releases, ignore, table_map, args.omitted_codes_have_no_cases)
        print(json.dumps(entries, indent=1, ensure_ascii=False) if args.json
              else gaps_summary(repo.dataset.get("id"), entries))
        return 0
    if not (args.release_a and args.release_b):
        parser.error("give two releases, or --gaps")
    result = diff(repo, args.release_a, args.release_b, args.table, args.omitted_codes_have_no_cases,
                  ignore, table_map)
    print(json.dumps(result, indent=1, ensure_ascii=False) if args.json else summary(result))
    if args.proposals:
        n_links, n_hist = write_proposals(repo, result, args.proposals)
        print(f"\nwrote {n_links} proposed links and {n_hist} proposed histories to {args.proposals} "
              "(origin rule release_diff; for review, not for metadata/ as they are)", file=sys.stderr)
    return 0

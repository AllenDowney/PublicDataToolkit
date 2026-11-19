"""Compare two releases' records: `pdt diff <repo> <release-a> <release-b> [--table T]`.

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

It reads the source records as published (corrections are listed, not applied) and
never writes into metadata/.
"""

import argparse
import difflib
import json
import sys
from pathlib import Path

from . import __version__
from .check import Repo
from .compare import compare_text, norm

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


def code_changes(a, b):
    """Differences between two value lists, as a dict of lists."""
    va = {code_key(v["code"]): v for v in a.get("values") or []}
    vb = {code_key(v["code"]): v for v in b.get("values") or []}
    out = {"added": [], "dropped": [], "relabeled": [], "relabeled_text_only": [], "kind_changed": []}
    for k in sorted(set(va) | set(vb), key=lambda k: (k[0], k[1])):
        x, y = va.get(k), vb.get(k)
        if x is None:
            out["added"].append({"code": y["code"], "label": y.get("label"), "kind": y.get("kind")})
        elif y is None:
            out["dropped"].append({"code": x["code"], "label": x.get("label"), "kind": x.get("kind")})
        else:
            how = compare_text(x.get("label"), y.get("label"))
            if how != "same":
                out["relabeled" if how == "changed" else "relabeled_text_only"].append(
                    {"code": y["code"], "from": x.get("label"), "to": y.get("label")})
            if x.get("kind") != y.get("kind") or sorted(x.get("missing_types") or []) != sorted(
                    y.get("missing_types") or []):
                out["kind_changed"].append({"code": y["code"],
                                            "from": [x.get("kind"), x.get("missing_types") or []],
                                            "to": [y.get("kind"), y.get("missing_types") or []]})
    return {k: v for k, v in out.items() if v}


def compare_pair(a, b):
    """Every difference between two records of the same variable."""
    out = {}
    for field, getter in (("label", lambda r: r.get("label")), ("question", question),
                          ("universe", lambda r: r.get("universe")),
                          ("description", lambda r: r.get("description"))):
        how = compare_text(getter(a), getter(b))
        if how != "same":
            out[field] = {"how": how, "from": getter(a), "to": getter(b)}
    codes = code_changes(a, b)
    if codes:
        out["codes"] = codes
    if a.get("measure") != b.get("measure"):
        out["measure"] = {"from": a.get("measure"), "to": b.get("measure")}
    return out


def relations(changes):
    """Link relations read off the differences (STANDARD.md §5.2)."""
    rel = []
    codes = changes.get("codes", {})
    if codes.get("added") or codes.get("dropped") or codes.get("kind_changed"):
        rel.append("codes_changed")
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


def waves_span(records):
    waves = sorted({a["wave"] for r in records for a in r.get("availability") or [] if "wave" in a
                    and isinstance(a["wave"], int)})
    return {"from": waves[0], "to": waves[-1]} if waves else None


def diff(repo, rel_a, rel_b, table=None):
    """The full comparison, as a dict that serializes to JSON."""
    for rel in (rel_a, rel_b):
        if rel not in repo.tables:
            raise SystemExit(f"no release {rel!r}; releases: {sorted(repo.tables)}")
    tables = sorted(set(repo.tables[rel_a]) | set(repo.tables[rel_b]), key=str)
    if table is not None:
        tables = [table]
    result = {"dataset": repo.dataset.get("id"), "from": rel_a, "to": rel_b, "tables": [],
              "corrections": [c["id"] for c in repo.corrections],
              "rule": RULE, "rule_version": RULE_VERSION, "pdt_version": __version__}
    for tab in tables:
        ra = {r["name"]: r for r in repo.tables[rel_a].get(tab, [])}
        rb = {r["name"]: r for r in repo.tables[rel_b].get(tab, [])}
        # names that differ only in case are the same variable
        lower_b = {n.lower(): n for n in rb}
        pairs = []
        for n in ra:
            m = n if n in rb else lower_b.get(n.lower())
            if m is not None:
                pairs.append((n, m))
        paired_a, paired_b = {p[0] for p in pairs}, {p[1] for p in pairs}
        only_a = [ra[n] for n in ra if n not in paired_a]
        only_b = [rb[n] for n in rb if n not in paired_b]
        both = []
        for na, nb in pairs:
            changes = compare_pair(ra[na], rb[nb])
            entry = {"from": na, "to": nb, "relations": relations(changes), "changes": changes}
            if na != nb:
                entry["name_case_changed"] = True
            both.append(entry)
        result["tables"].append({
            "table": tab,
            "only_in_from": [r["name"] for r in only_a],
            "only_in_to": [r["name"] for r in only_b],
            "rename_candidates": (renamed := rename_candidates(only_a, only_b)),
            "merge_split_candidates": merge_split_candidates(only_a, only_b, ra, rb, renamed),
            "in_both": both,
            "spans": {"from": waves_span(ra.values()), "to": waves_span(rb.values())},
        })
    return result


# ---------------------------------------------------------------- proposals

def proposed_links(result):
    out = []
    for t in result["tables"]:
        for e in t["in_both"]:
            ref = lambda rel, name: {"release": rel, **({"table": t["table"]} if t["table"] else {}), "name": name}
            what = "; ".join(f"{k}: {v['how'] if isinstance(v, dict) and 'how' in v else ', '.join(v)}"
                             for k, v in e["changes"].items()) or "no differences in the records"
            out.append({"from": ref(result["from"], e["from"]), "to": ref(result["to"], e["to"]),
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
        ra = {r["name"]: r for r in repo.tables[result["from"]].get(t["table"], [])}
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
    for t in result["tables"]:
        both = t["in_both"]
        rel_counts = {}
        for e in both:
            key = ", ".join(e["relations"])
            rel_counts[key] = rel_counts.get(key, 0) + 1
        head = f"\n[{t['table']}]" if t["table"] else ""
        lines.append(f"{head}\n  in both: {len(both)}  only in {result['from']}: {len(t['only_in_from'])}  "
                     f"only in {result['to']}: {len(t['only_in_to'])}  rename candidates: "
                     f"{len(t['rename_candidates'])}")
        for k, n in sorted(rel_counts.items()):
            lines.append(f"    {n:4}  {k}")
        for e in both:
            if e["relations"] == ["same_item"] and not e["changes"]:
                continue
            lines.append(f"  {e['to']}: {', '.join(e['relations'])}")
            for field, v in e["changes"].items():
                if field == "codes":
                    for kind, items in v.items():
                        shown = "; ".join(
                            f"{i['code']} {i.get('label') or ''}".strip() if kind in ("added", "dropped")
                            else f"{i['code']} {i['from']!r} -> {i['to']!r}" for i in items[:6])
                        more = f" (+{len(items) - 6})" if len(items) > 6 else ""
                        lines.append(f"      codes {kind}: {shown}{more}")
                elif field == "measure":
                    lines.append(f"      measure: {v['from']} -> {v['to']}")
                else:
                    lines.append(f"      {field} ({v['how']})")
        for c in t["rename_candidates"]:
            lines.append(f"  rename candidate: {c['from']} -> {c['to']} (similarity {c['score']})")
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
    parser.add_argument("release_a")
    parser.add_argument("release_b")
    parser.add_argument("--table", help="only this table")
    parser.add_argument("--json", action="store_true", help="print the full comparison as JSON")
    parser.add_argument("--proposals", metavar="DIR",
                        help="write proposed links.jsonl and histories.jsonl here, for review")
    args = parser.parse_args(argv)
    repo = Repo.load(args.path)
    result = diff(repo, args.release_a, args.release_b, args.table)
    print(json.dumps(result, indent=1, ensure_ascii=False) if args.json else summary(result))
    if args.proposals:
        n_links, n_hist = write_proposals(repo, result, args.proposals)
        print(f"\nwrote {n_links} proposed links and {n_hist} proposed histories to {args.proposals} "
              "(origin rule release_diff; for review, not for metadata/ as they are)", file=sys.stderr)
    return 0

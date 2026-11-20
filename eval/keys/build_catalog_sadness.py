"""Build the catalog_sadness answer key for the datasets in a catalog snapshot.

Usage: python eval/keys/build_catalog_sadness.py SNAPSHOT_DIR

SNAPSHOT_DIR holds `git archive HEAD` copies of pdt-catalog and of every repo its manifest
includes, with their commits in SNAPSHOT_DIR/COMMITS: the copies the runs use. Writes
catalog_sadness.yaml next to this script.

Versions (PROTOCOL.md, "catalog_sadness key versions"):
- 1 (catalog_sadness_v1.yaml, built by build_task51.py): the 8 datasets of pdt-catalog 2522621.
- 2 (this script, VERSION 2): the 17 datasets of pdt-catalog 39a13b0, every dataset whose
  metadata ships except GSS, which rejoins after its rebuild (Task 58), and NCVS, unpublished.
A catalog with other datasets needs a new version: change VERSION and COVERS, and decide the
new candidates. The script stops if the catalog's datasets aren't COVERS or a candidate is
undecided, so the version always says which datasets a key covers.

Candidates and rule are version 1's (build_task51.py): every variable in a current release
whose label, description or question text matches CANDIDATES. A hit asks whether or how often
the respondent felt sad, depressed, down or blue, or hopeless. Neutral: on the topic but not
that (diagnoses, days of poor mental health, help-seeking and treatment, worthlessness,
derived scores and episode classifications). Anything else the pattern caught is out.
Decisions for version 2's new datasets by Claude (PublicDataToolkit, blue), 2026-11-20,
before any run against this catalog.

Items match on (dataset, name), as score.py compares them: case-insensitively, so NSDUH's
ADDPREV (2023) and addprev (2024) are one item, with the waves of both.
"""

import json
import sys
from pathlib import Path

import yaml

from build_task51 import CANDIDATES, OUT as OUT_V1, SADNESS as SADNESS_V1, commits, records

HERE = Path(__file__).resolve().parent
AUTHOR = "Claude (PublicDataToolkit, blue)"
VERSION = 2
COVERS = ["anes-cdf", "atus", "brfss", "ces", "chicago-crimes", "cps-asec", "fars", "hints", "meps",
          "nhanes", "nhis", "nlsy97", "nsduh", "nsfg", "pisa", "pulse", "yrbss"]

# Decisions for the datasets version 1 didn't cover. Keys are (dataset, lowercased name).
SADNESS_V2 = {
    ("hints", "hopeless"): ("hit", "bothered by feeling down, depressed or hopeless, past 2 weeks (PHQ-4)"),
    ("meps", "adhope42"): ("hit", "how often felt hopeless, past 30 days"),
    ("meps", "addprs42"): ("hit", "felt down, depressed or hopeless, past 2 weeks (PHQ-2)"),
    ("nhanes", "dpq020"): ("hit", "feeling down, depressed or hopeless, past 2 weeks (PHQ-9)"),
    ("nhis", "asisad"): ("hit", "so sad nothing could cheer you up, past 30 days"),
    ("nhis", "asihopls"): ("hit", "felt hopeless, past 30 days"),
    ("nhis", "sad_a"): ("hit", "so sad nothing could cheer you up, past 30 days"),
    ("nhis", "hopeless_a"): ("hit", "felt hopeless, past 30 days"),
    ("nhis", "dep_1"): ("hit", "how often feel depressed"),
    ("nhis", "depfreq_a"): ("hit", "how often feel depressed"),
    ("nlsy97", "ysaq-282e"): ("hit", "felt downhearted and blue, past month"),
    ("nlsy97", "ysaq-282g"): ("hit", "so down in the dumps nothing could cheer you up, past month"),
    ("nsduh", "dsthop30"): ("hit", "how often felt hopeless, past 30 days"),
    ("nsduh", "dstchr30"): ("hit", "so sad or depressed nothing could cheer you up, past 30 days"),
    ("nsduh", "addprev"): ("hit", "ever had several days or longer feeling sad, empty or depressed"),
    ("pulse", "down"): ("hit", "bothered by feeling down, depressed or hopeless, past 7 days"),
    ("hints", "medconditions_depression"): ("neutral", "a diagnosis (depression or anxiety disorder)"),
    ("hints", "phq4"): ("neutral", "a derived score (PHQ-4 total)"),
    ("nhis", "asiwthls"): ("neutral", "worthless, not sad or hopeless"),
    ("nhis", "worthless_a"): ("neutral", "worthless, not sad or hopeless"),
    ("nhis", "phqcat_a"): ("neutral", "a derived score (PHQ severity category)"),
    ("nsduh", "dstngd30"): ("neutral", "down on yourself, no good or worthless: worthlessness"),
    ("nsduh", "amdeyr"): ("neutral", "a derived classification (past-year major depressive episode)"),
    ("nsduh", "iramdeyr"): ("neutral", "a derived classification (past-year major depressive episode)"),
    ("nsduh", "ymdeyr"): ("neutral", "a derived classification (past-year major depressive episode)"),
}
# Version 1's decisions, which still hold for its datasets (GSS's apply once GSS rejoins).
DECIDED = {(d, n.lower()): v for (d, n), v in SADNESS_V1.items()} | SADNESS_V2
OUT = {(d, n.lower()) for d, n in OUT_V1}


def main():
    base = Path(sys.argv[1]).resolve()
    cm = commits(base)
    manifest = json.loads((base / "pdt-catalog" / "manifest.json").read_text())
    datasets = sorted(d["id"] for d in manifest["datasets"])
    assert datasets == sorted(COVERS), f"the catalog's datasets aren't version {VERSION}'s: {datasets}"
    seen, candidates = {}, set()
    for d in manifest["datasets"]:
        repo = base / d["path"]
        ds = yaml.safe_load((repo / "dataset.yaml").read_text())
        for rel in [r["id"] for r in ds["releases"] if r.get("status", "current") == "current"]:
            for f in sorted((repo / "metadata/releases" / rel).rglob("variables.jsonl")):
                for r in records(f):
                    text = " ".join([r.get("label") or "", r.get("description") or ""]
                                    + [q.get("text", "") for q in r.get("questions", [])])
                    if not CANDIDATES.search(text):
                        continue
                    k = (ds["id"], r["name"].lower())
                    candidates.add(k)
                    assert k in DECIDED or k in OUT, f"undecided candidate {k}: {r.get('label')}"
                    if k in DECIDED:
                        it = seen.setdefault(k, {"name": r["name"], "table": r.get("table"), "waves": set()})
                        it["waves"] |= {a["wave"] for a in r.get("availability", [])}
    covered = set(COVERS)
    stale = {k for k in set(DECIDED) | OUT if k[0] in covered} - candidates
    assert not stale, f"decisions for names that aren't candidates: {stale}"
    items = [{"dataset": d, "table": seen[(d, n)]["table"], "name": seen[(d, n)]["name"], "status": status,
              "why": why, "waves": sorted(seen[(d, n)]["waves"], key=str)}
             for (d, n), (status, why) in sorted(DECIDED.items()) if (d, n) in seen]
    key = {
        "question": "catalog_sadness",
        "version": VERSION,
        "covers": COVERS,
        "expected_label": "approximate",
        "label_reason": "A text concept across datasets; text search is always approximate.",
        "match_on": ["dataset", "name"],
        "scope": {"catalog": cm.get("pdt-catalog"), "repos": cm},
        "built_by": "eval/keys/build_catalog_sadness.py; candidates by keyword, decisions by hand "
                    "(version 1's, plus SADNESS_V2 for the new datasets)",
        "author": AUTHOR,
        "candidates": len(candidates),
        "items": items,
    }
    out = HERE / "catalog_sadness.yaml"
    out.write_text(f"# Sadness or hopelessness across the catalog, version {VERSION} ({len(COVERS)} datasets). "
                   "Generated by build_catalog_sadness.py.\n" + yaml.safe_dump(key, sort_keys=False, allow_unicode=True))
    hits = sum(i["status"] == "hit" for i in items)
    print(f"version {VERSION}: {len(candidates)} candidates, {hits} hits, {len(items) - hits} neutral")


if __name__ == "__main__":
    main()

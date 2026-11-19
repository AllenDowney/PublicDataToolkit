"""Score agent runs against the answer keys, as PROTOCOL.md defines.

Usage: python eval/score.py RUN_DIR [RUN_DIR ...] [--markdown]

Each RUN_DIR holds config.json, log.jsonl and answer.json (see harness/setup_run.py).
Writes score.json into each run directory and prints a summary table.
"""

import json
import sys
from pathlib import Path

import yaml

EVAL = Path(__file__).resolve().parent


def key_of(item):
    table = item.get("table")
    return (item["dataset"].lower(), (table or "").lower() or None, item["name"].lower())


def load_key(question):
    with open(EVAL / "keys" / f"{question}.yaml") as f:
        return yaml.safe_load(f)


def ratio(num, den):
    return round(num / den, 3) if den else None


def score_items(key_items, reported):
    hits = {key_of(i) for i in key_items if i["status"] == "hit"}
    neutral = {key_of(i) for i in key_items if i["status"] == "neutral"}
    found = reported & hits
    counted = reported - neutral
    return {
        "key_hits": len(hits),
        "reported": len(reported),
        "found": len(found),
        "recall": ratio(len(found), len(hits)),
        "precision": ratio(len(found), len(counted)),
        "misses": sorted("/".join(filter(None, k)) for k in hits - reported),
        "false_positives": sorted("/".join(filter(None, k)) for k in counted - hits),
    }


def score_run(run):
    cfg = json.loads((run / "config.json").read_text())
    key = load_key(cfg["question"])
    log = [json.loads(line) for line in (run / "log.jsonl").read_text().splitlines()] \
        if (run / "log.jsonl").exists() else []
    answer_path = run / "answer.json"
    answer = json.loads(answer_path.read_text()) if answer_path.exists() else {"items": []}
    reported = {key_of(i) for i in answer.get("items", [])}

    result = {"run": cfg["run_id"], "question": cfg["question"], "answered": answer_path.exists()}
    result.update(score_items(key["items"], reported))
    if len(reported) != len(answer.get("items", [])):
        result["duplicates"] = len(answer["items"]) - len(reported)

    read = sum(e["tokens"] for e in log if e["printed"])
    corpus = sum(cfg["corpus_tokens"].values())
    result.update({
        "tokens_read": read,
        "corpus_tokens": corpus,
        "effort": ratio(read, corpus),
        "calls": len(log),
        "searches": sum(e["call"] == "search" for e in log),
        "refused": sum(not e["printed"] for e in log),
        "label": answer.get("label"),
        "expected_label": key["expected_label"],
        "label_ok": answer.get("label") == key["expected_label"],
    })
    datasets = sorted({i["dataset"] for i in key["items"]})
    if len(datasets) > 1:
        result["by_dataset"] = {}
        for ds in datasets:
            sub = score_items([i for i in key["items"] if i["dataset"] == ds],
                              {k for k in reported if k[0] == ds})
            result["by_dataset"][ds] = {k: sub[k] for k in ("recall", "precision", "found", "key_hits")}
    (run / "score.json").write_text(json.dumps(result, indent=1) + "\n")
    return result


def table(results):
    head = "| Run | Question | Recall | Precision | Tokens read | Effort | Calls | Label | Label ok |"
    rows = [head, "|" + "---|" * 9]
    for r in results:
        rows.append(f"| {r['run']} | {r['question']} | {r['recall']} | {r['precision']} | "
                    f"{r['tokens_read']:,} | {r['effort']} | {r['calls']} | {r['label']} | "
                    f"{'yes' if r['label_ok'] else 'no'} |")
    return "\n".join(rows)


def main():
    runs = [Path(a) for a in sys.argv[1:] if not a.startswith("--")]
    results = [score_run(r) for r in runs]
    print(table(results))
    for r in results:
        if r["misses"] or r["false_positives"]:
            print(f"\n{r['run']}: misses {r['misses']}; false positives {r['false_positives']}")


if __name__ == "__main__":
    main()

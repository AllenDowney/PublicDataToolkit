"""Tag GSS variables with topics by model, for Task 57 (planning/topic_annotation_design.md).

Usage (under the memory cap, with the Anthropic SDK importable):
    python eval/harness/annotate_topics.py RECORDS_JSONL OUT_DIR [--batch 100] [--cap 2000000]
    python eval/harness/annotate_topics.py RECORDS_JSONL OUT_DIR --assemble ANNOTATIONS_JSONL

RECORDS_JSONL is the blind records file (one variable per line: name, label, description,
question, values, subjects, modules). Each call tags one batch of BATCH variables with the
topics in TOPICS, under the fixed prompt PROMPT_VERSION. OUT_DIR keeps one file per batch
(the raw response, its usage, and the parsed tags), so a run resumes where it stopped, and
log.jsonl, with each call's tokens. The run stops before a call that could pass CAP input
tokens in all.

--assemble writes the tags as annotations (schema/annotation.schema.json): one line per
(variable, topic), origin model, with the model id, the prompt version, the date, and
reviewed: false.
"""

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

import anthropic

MODEL = "claude-haiku-5-5"
PROMPT_VERSION = "topics-0.1"
TOPICS = ["religion", "mental_health"]
QUESTION_CHARS = 400
MAX_VALUES = 12

SYSTEM = """You tag survey variables with topics. For each variable, list every topic below that the variable is about. A variable is about a topic if it asks the respondent about it, or records something about it. Use only these topics; give an empty list if none applies.
- religion: religious affiliation or preference, attendance at services, the importance of religion to the respondent, prayer, religious belief (for example, views about the Bible), religious experience, and attitudes about religion, religious groups or clergy.
- mental_health: feelings such as sadness, depression, anxiety, stress or loneliness, mental-health diagnoses, days of poor mental health, treatment or help for emotional problems, and attitudes about mental illness.
Give the tags for every variable in the batch, by its name."""

SCHEMA = {
    "type": "object",
    "properties": {
        "tags": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "topics": {"type": "array", "items": {"type": "string", "enum": TOPICS}},
                },
                "required": ["name", "topics"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["tags"],
    "additionalProperties": False,
}


def block(rec):
    """One variable as the model sees it."""
    lines = [f"name: {rec['name']}", f"label: {rec.get('label') or '-'}"]
    q = " ".join((rec.get("question") or rec.get("description") or "").split())
    if q:
        lines.append(f"question: {q[:QUESTION_CHARS]}" + ("..." if len(q) > QUESTION_CHARS else ""))
    vals = rec.get("values") or []
    if vals:
        lines.append("values: " + " / ".join(vals[:MAX_VALUES]))
    return "\n".join(lines)


def batches(records, size):
    for i in range(0, len(records), size):
        yield i // size, records[i:i + size]


def spent(log):
    if not log.exists():
        return 0, 0
    rows = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
    total = sum(r["input_tokens"] for r in rows)
    biggest = max((r["input_tokens"] for r in rows), default=0)
    return total, biggest


def run(records, out, size, cap):
    client = anthropic.Anthropic()
    log = out / "log.jsonl"
    for n, batch in batches(records, size):
        path = out / f"batch-{n:03d}.json"
        if path.exists():
            continue
        total, biggest = spent(log)
        # Stop before a call that could pass the cap: assume it's no smaller than the largest so far,
        # or, for the first call, a generous estimate.
        estimate = biggest or 30_000
        if total + estimate > cap:
            print(f"stopping before batch {n}: {total:,} input tokens spent, cap {cap:,}")
            return 1
        names = [r["name"] for r in batch]
        user = "\n\n".join(block(r) for r in batch)
        t = time.time()
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
            system=SYSTEM,
            messages=[{"role": "user", "content": user}],
        )
        usage = response.usage
        entry = {"batch": n, "variables": len(batch), "input_tokens": usage.input_tokens,
                 "output_tokens": usage.output_tokens, "stop_reason": response.stop_reason,
                 "seconds": round(time.time() - t, 1), "request_id": response._request_id}
        result = {"batch": n, "names": names, "stop_reason": response.stop_reason,
                  "usage": {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens}}
        if response.stop_reason == "end_turn":
            text = next(b.text for b in response.content if b.type == "text")
            tags = {t["name"]: t["topics"] for t in json.loads(text)["tags"]}
            result["raw"] = text
            result["tags"] = {nm: tags.get(nm) for nm in names}
            result["missing"] = [nm for nm in names if nm not in tags]
            result["extra"] = sorted(set(tags) - set(names))
            entry["missing"] = len(result["missing"])
        else:
            # A refusal or a cut-off answer: keep it on record; the batch is reported as untagged.
            result["stop_details"] = getattr(response, "stop_details", None) and response.stop_details.to_dict()
            entry["untagged"] = True
        path.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
        with open(log, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"batch {n}: {usage.input_tokens:,} in, {usage.output_tokens:,} out, {response.stop_reason}")
    total, _ = spent(log)
    print(f"done: {total:,} input tokens")
    return 0


def assemble(out, dest, date):
    lines, untagged, missing = [], [], []
    for path in sorted(out.glob("batch-*.json")):
        res = json.loads(path.read_text())
        if "tags" not in res:
            untagged += res["names"]
            continue
        missing += res["missing"]
        for name, topics in res["tags"].items():
            for topic in sorted(set(topics or [])):
                lines.append({"target": {"variable": name}, "kind": "topic", "value": topic,
                              "origin": {"origin": "model", "model": MODEL, "prompt_version": PROMPT_VERSION,
                                         "date": date, "reviewed": False}})
    Path(dest).write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in lines))
    print(f"{len(lines)} annotations; untagged (refused or cut off): {len(untagged)}; "
          f"missing from answers: {len(missing)}")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("records")
    p.add_argument("out")
    p.add_argument("--batch", type=int, default=100)
    p.add_argument("--cap", type=int, default=2_000_000)
    p.add_argument("--assemble", help="write annotations JSONL here from the batch files")
    p.add_argument("--date", default=datetime.date.today().isoformat())
    a = p.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.assemble:
        return assemble(out, a.assemble, a.date)
    records = [json.loads(l) for l in Path(a.records).read_text().splitlines() if l.strip()]
    return run(records, out, a.batch, a.cap)


if __name__ == "__main__":
    sys.exit(main())

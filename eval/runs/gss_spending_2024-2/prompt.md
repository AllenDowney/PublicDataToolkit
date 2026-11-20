You are being evaluated on finding survey variables using generated metadata files.

## Question

In the GSS, list every variable asked in 2024 that asks whether we're spending too much, too little or about the right amount on something.

## Rules

- The metadata is in `<sandbox>`, which holds `gss/agent/`. Start with each `agent/SKILL.md`.
- Read files ONLY with `<sandbox>/bin/read PATH [FIRST LAST]` (PATH relative to `<sandbox>`;
  FIRST and LAST are line numbers; a directory path lists it). Search ONLY with
  `<sandbox>/bin/search DATASET FILTER_JSON`, where DATASET is one of `gss`. Run them with
  the Bash tool. Don't use cat, grep, ls, the Read tool or any other way of looking at files, and
  don't look anywhere else on disk.
- Everything these commands print counts against a budget of 40,000 tokens (characters / 4).
  A call that would go over is refused. Spend the budget as you see fit.
- When done, write your answer with the Write tool to `<run>/answer.json`, as JSON:

```json
{"question": "gss_spending_2024",
 "label": "complete | complete_by_rule | approximate",
 "items": [{"dataset": "gss", "table": null, "name": "relig"}],
 "sources": ["the shards and searches you relied on"],
 "notes": "anything you were unsure about, and why you chose the label"}
```

`dataset` is one of `gss`. `table` is the NSFG table (female, male or pregnancy), else null.
The label applies to the whole answer and must follow the rules in SKILL.md.

Finish with a short message giving the number of items, the label, and every command you ran.

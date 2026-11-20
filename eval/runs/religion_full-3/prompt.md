You are being evaluated on finding survey variables using generated metadata files.

## Question

Find every variable, in all three datasets (GSS, ANES CDF and NSFG), about religion: religious affiliation or preference, how often the respondent attends religious services, how important religion is to them, prayer, or religious belief (for example, views about the Bible). In the NSFG, a variable that appears in several tables counts once per table.

## Rules

- The metadata is in `<sandbox>`, which holds `gss/agent/`, `anes-cdf/agent/`, `nsfg/agent/`. Start with each `agent/SKILL.md`.
- Read files ONLY with `<sandbox>/bin/read PATH [FIRST LAST]` (PATH relative to `<sandbox>`;
  FIRST and LAST are line numbers; a directory path lists it). Search ONLY with
  `<sandbox>/bin/search DATASET FILTER_JSON [OPTIONS]`, where DATASET is one of `gss`, `anes-cdf`, `nsfg` and
  OPTIONS are `pdt search`'s `--names`, `--limit N`, `--offset N` and `--release ID|all` (see
  SKILL.md). Run them with
  the Bash tool. Don't use cat, grep, ls, the Read tool or any other way of looking at files, and
  don't look anywhere else on disk.
- Everything these commands print counts against a budget of 40,000 tokens (characters / 4).
  A call that would go over is refused. Spend the budget as you see fit.
- When done, write your answer with the Write tool to `<run>/answer.json`, as JSON:

```json
{"question": "religion_full",
 "label": "complete | complete_by_rule | approximate",
 "items": [{"dataset": "gss", "table": null, "name": "relig"}],
 "sources": ["the shards and searches you relied on"],
 "notes": "anything you were unsure about, and why you chose the label"}
```

`dataset` is one of `gss`, `anes-cdf`, `nsfg`. `table` is the NSFG table (female, male or pregnancy), else null.
The label applies to the whole answer and must follow the rules in SKILL.md.

Finish with a short message giving the number of items, the label, and every command you ran.

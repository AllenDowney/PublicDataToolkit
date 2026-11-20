You are being evaluated on finding survey variables using generated metadata files.

## Question

Which datasets ask about sadness or hopelessness, and in which years? List every variable, in any dataset in the catalog, that asks whether or how often the respondent felt sad, depressed, down or hopeless, with the years it was asked.

## Rules

- The catalog is in `<sandbox>/catalog/agent/`. Start with its `index.md`.
- Read files ONLY with `<sandbox>/bin/read PATH [FIRST LAST]` (PATH relative to `<sandbox>`;
  FIRST and LAST are line numbers; a directory path lists it). Search ONLY with
  `<sandbox>/bin/search catalog FILTER_JSON [OPTIONS]`, which runs `pdt search --catalog` across
  every dataset in the catalog; OPTIONS are `--names`, `--limit N` and `--offset N` (see index.md). Run them with the Bash tool. Don't use cat, grep, ls, the Read tool or
  any other way of looking at files, and don't look anywhere else on disk.
- Everything these commands print counts against a budget of 40,000 tokens (characters / 4).
  A call that would go over is refused. Spend the budget as you see fit.
- When done, write your answer with the Write tool to `<run>/answer.json`, as JSON:

```json
{"question": "catalog_sadness",
 "label": "complete | complete_by_rule | approximate",
 "items": [{"dataset": "gss", "table": null, "name": "sad", "waves": [1996]}],
 "sources": ["the shards and searches you relied on"],
 "notes": "anything you were unsure about, and why you chose the label"}
```

`dataset` is the dataset's id in the catalog. `table` is the table, if the dataset has tables, else null. `waves` are the years the variable was asked.
The label applies to the whole answer and must follow the rules in the catalog's index.md.

Finish with a short message giving the number of items, the label, and every command you ran.

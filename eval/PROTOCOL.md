# Evaluation protocol: agent search over `agent/`

Task 23. Written and committed before any agent was run, as [plan §7.5](../planning/survey_metadata_packages_plan.md#75-measuring-recall) requires. Changes after the first run are listed at the end, with the reason, and scores are reported under both versions.

## What is tested

Can an agent that sees only a dataset repo's `agent/` directory, plus `pdt search`, find every variable a question asks for, label the result correctly, and read much less than the whole metadata?

In scope are the three survey slices as they stood on 2026-11-19:

| Repo | Release, tables | Variables |
|---|---|---|
| `../pdt-gss` | `7224r3a` | 50 |
| `../pdt-anes-cdf` | `20260205` | 37 |
| `../pdt-nsfg` | `2022-2023`: female, male, pregnancy | 23 + 17 + 12 |

FARS is left out: it has no religion items and its structure is still changing (Task 13).

## Questions

Each question is given to a fresh agent, in these words.

| Id | Kind | Question |
|---|---|---|
| `religion` | topic | Find every variable, in all three datasets (GSS, ANES CDF and NSFG), about religion: religious affiliation or preference, how often the respondent attends religious services, how important religion is to them, prayer, or religious belief (for example, views about the Bible). In the NSFG, a variable that appears in several tables counts once per table. |
| `gss_ballot_a_1988` | structural | In the GSS, list every variable that was asked of (or has a value for) respondents who got ballot A in 1988. |
| `anes_therm_1978` | structural | In the ANES CDF, list every feeling thermometer that was asked in 1978. |

For every question, the agent must also give the completeness label of its answer (`complete`, `complete_by_rule` or `approximate`), the shards and filters it used, and anything it was unsure about.

## Answer keys

Keys are in [`keys/`](keys/), one YAML file per question. Each item is a `(dataset, table, name)` with a status:

- `hit`: must be found;
- `neutral`: reasonable either way; ignored in recall and precision.

Each key gives the label a correct answer should carry under the rules in each repo's `SKILL.md` and STANDARD.md §7.

- **`religion`** was built by reading every line of the three release shards and the publisher subject lists, with CultureWar's [`religion_inventory.md`](../../CultureWar/notebooks/inventories/religion_inventory.md) as a check on the GSS names.
- **The two structural keys** are computed from the canonical records in each repo's `metadata/` by [`keys/build_structural.py`](keys/build_structural.py), and were checked by eye against the line forms. They measure whether the agent reads availability correctly, not whether the availability is right (that is C5 in `pdt check`).

Names compare case-insensitively. NSFG items compare on `(table, name)`; the GSS and ANES have no tables.

## Tools and budget

The agent works in a sandbox that holds a copy of each repo's `agent/` directory:

```
<sandbox>/gss/agent/  <sandbox>/anes-cdf/agent/  <sandbox>/nsfg/agent/
```

It may use only two commands, both in [`harness/`](harness/):

| Command | Does |
|---|---|
| `read PATH [FIRST LAST]` | prints a file under the sandbox, or lines FIRST to LAST; `read DIR` lists a directory |
| `search DATASET FILTER` | runs `pdt search` on that dataset's repo and prints the labeled result |

Both log every call, with the characters printed, to a JSONL log. **Budget: 40,000 tokens printed per question**, counted as characters / 4, the estimate `pdt views` uses for shard sizes. A call that would pass the budget is refused, and the refusal is logged. The agent may write its answer file and nothing else.

The model is Sonnet, as in the Task 14 blind tests. Each question runs twice, in fresh agents, to show the spread.

## Answer format

The agent writes `answer.json`:

```json
{"question": "religion",
 "label": "approximate",
 "items": [{"dataset": "gss", "table": null, "name": "relig"}],
 "sources": ["gss/agent/shards/subject/religion.txt"],
 "notes": "anything it was unsure about"}
```

## Scores

[`score.py`](score.py) computes, for each run:

| Score | Definition |
|---|---|
| Recall | key hits found / key hits |
| Precision | key hits found / items reported that aren't neutral |
| Tokens read | sum of tokens printed by `read` and `search`, from the log |
| Effort | tokens read / tokens in every file of the `agent/` directories in scope |
| Label | whether the reported label equals the key's expected label |

It also lists misses and false positives. Every false positive is checked by hand. If it turns out to belong in the key, the key is changed in a separate commit that says why, and both scores are reported, as §7.5 says ("some will be real misses from our original sweeps").

Recall and precision are reported per dataset as well as overall for `religion`.

## What would count as success

From the spike's success criterion (plan §13): the structural queries are answered exactly, and the topic query reaches high recall while reading far less than the full metadata. For this run, "high" means recall of at least 0.95 with effort under 0.25.

## Not tested here

- Annotations and embeddings: the slices have no topic annotations, and no embeddings exist. The with/without comparisons in §7.5 wait until they do.
- Full releases: the repos hold slices. Full-file answer keys are in [`keys/full/`](keys/full/) for when they hold more.
- The three-way comparison of flat, discovered and explicit structure (§7.5, optional extension).

## Changes after the first run

None yet.

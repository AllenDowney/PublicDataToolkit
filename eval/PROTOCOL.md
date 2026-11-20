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

- **2026-11-19, after runs 1-2: expected labels of the structural keys.** The first runs showed that `pdt search` couldn't select on availability (finding 2 in [`RESULTS.md`](RESULTS.md)). The views thread added an `available` filter (df13f6f), so the expected labels changed from `approximate` to `complete` (`gss_ballot_a_1988`) and `complete_by_rule` (`anes_therm_1978`). The items didn't change. Runs 1-2 keep the scores they had, against `approximate`, in their `score.json`; runs 3-4 are scored against the new labels. An agent that picks by reading and says `approximate` is still following the rules, so the scores report the label it gave as well as whether it matches.

## Task 51: the full GSS release (written before any Task 51 run)

**Scope.** Each run uses copies of the repos made with `git archive HEAD`: pdt-gss `cf22b43` (all 6,943 variables of `7224r3a`, plus `7224r3`), pdt-anes-cdf `4027ba5` and pdt-nsfg `2f794be` (still slices), and, for the catalog question, every repo in red's catalog (pdt-catalog `2522621`; pdt-brfss has no git, so it's copied from its working tree). `setup_run.py --repos DIR` points a run at the copies and records the commits in `config.json`. That way, work in progress in a repo can't leak into a run.

**Questions.** Two are reruns, word for word, against the full GSS:
- `religion_full`: the `religion` question;
- `gss_ballot_a_1988_full`: the ballot question.

Two are new:

| Id | Kind | Question |
|---|---|---|
| `gss_spending_2024` | structural | In the GSS, list every variable asked in 2024 that asks whether we're spending too much, too little or about the right amount on something. |
| `catalog_sadness` | topic, across datasets | Which datasets ask about sadness or hopelessness, and in which years? List every variable, in any dataset in the catalog, that asks whether or how often the respondent felt sad, depressed, down or hopeless, with the years it was asked. |

`anes_therm_1978` isn't rerun: the ANES CDF repo is unchanged apart from two variables that aren't thermometers.

**Keys.** All four are built by [`keys/build_task51.py`](keys/build_task51.py) from the same copies.

| Key | How it's built | Hits | Neutral | Expected label |
|---|---|---|---|---|
| `religion_full` | GSS part: [`keys/full/gss_religion.yaml`](keys/full/gss_religion.yaml), rebuilt from the 0.9 records. One new candidate among the 40 names gssrdoc 0.8.2 lacked, `reltrad16`, is added as a hit. ANES and NSFG parts: as in `religion` | 256 | 327 | `approximate` |
| `gss_ballot_a_1988_full` | Same rule as before. The year, id, ballot and the design variables in `dataset.yaml` are neutral | 635 | 7 | `complete` |
| `gss_spending_2024` | Scale signature `spending_3` and availability in 2024 | 27 | 0 | `complete_by_rule` |
| `catalog_sadness` | Candidates by keyword; decisions by hand by Claude (PublicDataToolkit Task 51), listed in the script. Items match on (dataset, name), ignoring tables | 11 | 33 | `approximate` |

**Scoring.**
- Names are scored within the current release, `7224r3a`. An answer names variables, not releases, so a variable that is also in `7224r3` counts once.
- For `catalog_sadness`, `score.py` also reports `waves_exact`: the share of hits found whose reported years equal the key's.

**Unchanged.** Sonnet, two fresh agents per question, the 40,000-token budget, and the `read` and `search` commands.

**Expected difficulty.**
- The ballot question's line form alone is over 30,000 tokens, so an agent has to rely on `search`.
- The catalog's own `index.md` uses "sad" and "depress" as its search example. That makes the catalog question easier than a cold one, as with the SKILL.md caveat in RESULTS.md.

## Task 53: after the search fixes (written before any Task 53 run)

**What changed.** Everything else is as in Task 51: the same Sonnet agents, two per question, the same budget and the same keys. The changes come from the Task 51 findings:
- **Library.** PublicDataToolkit `3310e55`:
  - `pdt search` defaults to the current release, with `--release all|ID`, `--names`, `--limit` and `--offset`;
  - a `waves` filter;
  - catalog search returns and filters waves;
  - SKILL.md says to search first, gives index.md's size, and names the scale signatures.
- **The copies.** Records are at the same commits as Task 51 (pdt-gss `cf22b43` and the rest). `agent/` in pdt-gss, pdt-anes-cdf and pdt-nsfg, and the catalog, are regenerated with `3310e55`. The copies' `COMMITS` file says so.
- **The harness.** `search` passes `--names`, `--limit N`, `--offset N` and `--release ID|all` through to `pdt search`. The prompt's `search` line names them and points to SKILL.md, or to the catalog's index.md.

**Questions.** `religion_full`, `gss_ballot_a_1988_full` and `catalog_sadness`, two runs each (`-3`, `-4`). The keys are those of `280dd86`, with `catalog_sadness` as fixed in `58e55f6`. `gss_spending_2024` isn't rerun.

**Expected effects of the fixes:**
- **Ballot:** the `available` search with `--names` is about 2,200 tokens, so a complete answer fits the budget.
- **Religion:** a `subject` search for Religion is 405 rows in the current release.
- **Catalog:** search now returns years.

The key's hit/neutral boundary still decides recall for religion.

**Addendum (2026-11-20, before the runs): `gss_spending_2024` rerun.** At the coordinator's request, `gss_spending_2024` is also rerun, as `-3` and `-4`, under this section's setup: the same copies, library, harness and key. The question is whether agents now find the `spending_3` signature that SKILL.md names, and report `complete_by_rule`.

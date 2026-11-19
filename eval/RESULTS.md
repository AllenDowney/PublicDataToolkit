# Results

Run on 2026-11-19 under [`PROTOCOL.md`](PROTOCOL.md) as committed in 8ef0d59, before any agent ran. Model: Sonnet, in fresh agents, two per question. Budget: 40,000 tokens per run.

## Scores

| Run | Recall | Precision | Tokens read | Effort | Calls | Label | Expected | Label ok |
|---|---|---|---|---|---|---|---|---|
| `religion-1` | 1.0 | 1.0 | 9,095 | 0.047 | 10 | `approximate` | `approximate` | yes |
| `religion-2` | 1.0 | 1.0 | 10,721 | 0.056 | 9 | `approximate` | `approximate` | yes |
| `gss_ballot_a_1988-1` | 1.0 | 1.0 | 5,141 | 0.035 | 3 | `approximate` | `approximate` | yes |
| `gss_ballot_a_1988-2` | 1.0 | 1.0 | 5,141 | 0.035 | 3 | `approximate` | `approximate` | yes |
| `anes_therm_1978-1` | 1.0 | 1.0 | 4,029 | 0.156 | 5 | `approximate` | `approximate` | yes |
| `anes_therm_1978-2` | 1.0 | 1.0 | 4,017 | 0.155 | 4 | `complete_by_rule` | `approximate` | no |

Effort is tokens read over every file in the `agent/` directories in scope (193k tokens for `religion`, 146k for the GSS, 26k for the ANES). Each run's directory in [`runs/`](runs/) has the prompt, the log of every call, the answer and `score.json`. No false positives, so the keys are unchanged.

## Findings

1. **The slices are too small to test search.** Each release shard's line form is 2,000 to 2,600 tokens, so every agent read the whole release, apart from one GSS lookup through the subject shard, and picked by eye. Recall of 1.0 at 5% effort says the line form is cheap to read, not that the shards or labels help find things. The test only discriminates when reading everything costs more than the budget: the full GSS, 6,904 variables at about 50 tokens a line, would be about 350,000 tokens in line form. The full-release keys in [`keys/full/`](keys/full/) are for that run.
2. **`pdt search` can't express a structural query on availability.** "Every item on ballot A in 1988" and "every thermometer asked in 1978" have exact answers, but no filter selects on wave or form, so an agent has to read waves by form and pick, which `SKILL.md` labels `approximate`. STANDARD.md §7 gives "every item on ballot A in 1985" as an example of a `complete` result, and plan §13's success criterion needs one structural query to be complete by construction. One agent tried `{"wave": 1978}` and got "unknown filter key". Proposal: an `available` filter, e.g. `{"available": {"wave": 1988, "form": "A"}}`, matching an availability entry for that wave with that form or with no form; it would be `complete` when availability's origin is `data_file` or `publisher`.
3. **Labels after pruning are fragile.** One of the two thermometer agents took the `complete_by_rule` scale shard, dropped eight variables by reading their waves, and kept `complete_by_rule`, although its own notes said `approximate` was "arguably the stricter label". `SKILL.md` says this case is `approximate`. Finding 2 would remove the need to prune.
4. **Agents rarely used `pdt search`.** One search in six runs worked (the GSS subject "Religion"). With shards this small, reading was easier.
5. **Measurement.** Tokens read counts what `read` and `search` printed. Two agents piped output through `grep`, `head` or `cut`, so they saw less than was counted; the numbers are an upper bound. Agents also wrote `answer.json` through the shell instead of the Write tool, which doesn't affect the scores.

## Next

- Rerun when a repo holds a full release, or a large part of one, with the keys in [`keys/full/`](keys/full/).
- Add the structural questions to `pdt search`'s tests once it has an availability filter, and rerun them expecting `complete`.

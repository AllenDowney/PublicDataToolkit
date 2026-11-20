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

## Reruns of the structural questions with the `available` filter

The views thread added `{"available": {"wave": W, "form": F}}` to `pdt search` (df13f6f) after finding 2, and SKILL.md now tells agents to use it. The expected labels changed to `complete` and `complete_by_rule` ([PROTOCOL.md](PROTOCOL.md#changes-after-the-first-run)). Same prompts, fresh agents, regenerated `agent/`.

| Run | Recall | Precision | Tokens read | Effort | Calls | Label | Label ok |
|---|---|---|---|---|---|---|---|
| `gss_ballot_a_1988-3` | 1.0 | 1.0 | 2,289 | 0.016 | 2 | `complete` | yes |
| `gss_ballot_a_1988-4` | 1.0 | 1.0 | 2,289 | 0.016 | 2 | `complete` | yes |
| `anes_therm_1978-3` | 1.0 | 1.0 | 1,140 | 0.040 | 2 | `complete_by_rule` | yes |
| `anes_therm_1978-4` | 1.0 | 1.0 | 1,272 | 0.045 | 3 | `complete_by_rule` | yes |

Every agent read SKILL.md and ran one search; one also cross-checked with a text search. Tokens read fell by half to two thirds, and all four labels are now right, including the thermometer case that went wrong in run 2. This meets plan §13's criterion for structural queries: complete by construction and checked against a hand list.

**Caveat:** SKILL.md's examples for `available` are these two queries, word for word. The reruns show that agents use the filter and report its label; they don't show that an agent would compose the right filter for a question SKILL.md doesn't spell out. The next structural test should use a query that isn't an example, e.g. every favor/oppose item asked in 2024.

## Next

- Rerun when a repo holds a full release, or a large part of one, with the keys in [`keys/full/`](keys/full/).
- A structural question that isn't one of SKILL.md's examples.
- A second reader for a sample of the GSS full key, to show how stable the hit/neutral boundary is.

## Task 51: the full GSS release

Run on 2026-11-20 under PROTOCOL.md's Task 51 section, committed in `280dd86` before any run. A first attempt on 2026-11-19 was interrupted by a shutdown, and its runs were deleted unscored. Every run used `git archive` copies of the repos at the commits in its `config.json`: pdt-gss `cf22b43`, the full 7224r3a (6,943 variables) plus 7224r3. Model: Sonnet, two fresh agents per question, a 40,000-token budget. Effort is tiny everywhere because the full GSS `agent/` is about 14.6 million tokens.

| Run | Recall | Precision | Found / hits | Tokens read | Calls | Label | Expected | Label ok |
|---|---|---|---|---|---|---|---|---|
| `religion_full-1` | 0.027 | 1.0 | 7 / 256 | 39,875 | 15 | `approximate` | `approximate` | yes |
| `religion_full-2` | 0.109 | 1.0 | 28 / 256 | 34,663 | 8 | `approximate` | `approximate` | yes |
| `gss_ballot_a_1988_full-1` | 0.020 | 1.0 | 13 / 635 | 39,582 | 4 | `approximate` | `complete` | no |
| `gss_ballot_a_1988_full-2` | 0.072 | 1.0 | 46 / 635 | 39,582 | 4 | `approximate` | `complete` | no |
| `gss_spending_2024-1` | 1.0 | 1.0 | 27 / 27 | 39,616 | 7 | `approximate` | `complete_by_rule` | no |
| `gss_spending_2024-2` | 1.0 | 1.0 | 27 / 27 | 3,706 | 3 | `approximate` | `complete_by_rule` | no |
| `catalog_sadness-1` | 0.833 | 1.0 | 10 / 12 | 34,598 | 84 | `approximate` | `approximate` | yes |
| `catalog_sadness-2` | 1.0 | 1.0 | 12 / 12 | 32,851 | 33 | `approximate` | `approximate` | yes |

**By dataset, religion.**

| Run | GSS | ANES | NSFG |
|---|---|---|---|
| `religion_full-1` | 1 / 242 | 5 / 5 | 1 / 9 |
| `religion_full-2` | 15 / 242 | 4 / 5 | 9 / 9 |

Six of run 2's 15 GSS hits (`relig`, `relig16`, `denom`, `fund`, `reliten`, `attend`) were, by its own account, "added from memory" without being seen. Without them, its GSS recall is 9 / 242.

**Key change.**
- `catalog_sadness-2` reported `gss/shakeblu`, "felt that you couldn't shake the blues", from the 1996 feelings list. That was a false positive against the first key.
- Checked by hand, it's a hit: the key's candidate pattern had `\bblue\b`, which misses "blues". The key was changed in a separate commit, `58e55f6`.
- Scores against the first key (11 hits): run 1, recall 0.909 and precision 1.0; run 2, recall 1.0 and precision 0.917. The table above uses the changed key (12 hits).

**Years** (`waves_exact`, the share of hits found whose years match the key's): run 1, 0.5; run 2, 0.17. Both agents found the YRBSS years. Run 1 found four GSS items' years; run 2 found none. Both ran out of budget before reading the other GSS items' lines, and the catalog search can't filter or return by year.

### Findings

1. **The full release breaks reading, as predicted: recall fell from 1.0 on the slices to 0.03–0.11 for religion.**
   - Three of four religion agents spent most of the budget on one call: reading the full GSS `agent/index.md`, about 31,000 tokens. Nothing in SKILL.md warned them.
   - The subject search (`{"subject": "Religion"}`) would have found most of the key, but by then it was refused for budget.
2. **`pdt search` returns every release, so structural results double.**
   - The ballot filter, `{"available": {"wave": 1988, "form": "A"}}`, is the right query, and both agents used it straight away. It returned 1,282 rows (7224r3 and 7224r3a) instead of 642, about 32,000 tokens.
   - No agent could see the whole list, so recall was 0.02–0.07 and the labels fell to `approximate`.
   - Search should default to the current release, as the catalog does (`--all-releases`). It also needs a compact or names-only form for large exact results.
3. **A structural question SKILL.md doesn't spell out: perfect lists, wrong labels.**
   - Both spending agents found all 27 items with text searches ("too much", "too little") and the `available` filter, but labeled them `approximate`.
   - Neither found the `spending_3` scale signature, which gives the same set as `complete_by_rule`.
   - This answers RESULTS.md's earlier caveat: agents compose the `available` filter, but don't discover derived properties they aren't told about by name.
4. **The catalog works for cross-dataset discovery and is weak on years.**
   - Text search across 8 datasets found every hit in run 2 and 10 of 12 in run 1, with no false positives once the key was fixed.
   - Years are the gap: the catalog lines carry them, but finding a GSS line in a 16-part file costs reads, and search can't return them. One agent probed `waves` and `year` filter keys, which don't exist.
   - The catalog's index uses "sad" and "depress" as its own example, so this question was easier than a cold one would be.
5. **Agents bend the read-only rules under budget pressure.**
   - Most runs piped `read` or `search` output through `head`, `grep`, `cut` or `tr`, and several wrote `answer.json` from a Python heredoc.
   - One saved search output to a scratch file. One tried `cat` on the search script, which the permission classifier denied.
   - Tokens read are still counted at the source, so they're an upper bound on what agents saw. The answers are scored as written.

### Next

- In `pdt search`, default to the current release and add a names-only or paged output (red, views).
- Warn in GSS SKILL.md that `index.md` is large, and point to `subject` searches and scale signatures first. Or split the index.
- Let catalog search return years, or filter on them.
- Rerun these four questions after those changes, as a protocol change, with the same keys.

## Task 53: after the search fixes

Run on 2026-11-20 under PROTOCOL.md's Task 53 section, committed in `ba40c25` before any run. The records are the same as in Task 51 (pdt-gss `cf22b43`). What changed is the library (`3310e55`), the regenerated `agent/` and catalog, and the harness's search options. Same model, budget and keys.

| Run | Recall | Precision | Found / hits | Tokens read | Calls | Label | Expected | Label ok |
|---|---|---|---|---|---|---|---|---|
| `religion_full-3` | 0.855 | 1.0 | 219 / 256 | 9,689 | 11 | `approximate` | `approximate` | yes |
| `religion_full-4` | 0.184 | 1.0 | 47 / 256 | 6,360 | 19 | `approximate` | `approximate` | yes |
| `gss_ballot_a_1988_full-3` | 1.0 | 1.0 | 635 / 635 | 5,044 | 3 | `complete` | `complete` | yes |
| `gss_ballot_a_1988_full-4` | 1.0 | 1.0 | 635 / 635 | 7,285 | 2 | `complete` | `complete` | yes |
| `catalog_sadness-3` | 1.0 | 1.0 | 12 / 12 | 12,501 | 4 | `approximate` | `approximate` | yes |
| `catalog_sadness-4` | 1.0 | 1.0 | 12 / 12 | 9,613 | 5 | `approximate` | `approximate` | yes |

Both catalog runs got every hit's years right (`waves_exact` 1.0). None of the six runs had a false positive, so the keys are unchanged.

**Before and after** (Task 51 runs, then Task 53 runs):

| Question | Recall before | Recall after | Tokens read before | Tokens read after |
|---|---|---|---|---|
| Religion, full GSS | 0.03, 0.11 | 0.86, 0.18 | 35–40k | 6–10k |
| Ballot A 1988, full GSS | 0.02, 0.07 | 1.0, 1.0 (labels right) | 40k | 5–7k |
| Catalog sadness | 0.83, 1.0 (years 0.5, 0.17) | 1.0, 1.0 (years 1.0, 1.0) | 33–35k | 10–13k |

### Findings

1. **Structural queries are solved at full scale.** Both ballot agents ran the `available` search with `--names` and reported 642 names, labeled `complete`, in 2–3 calls and 5–7k tokens.
   - One added `--release all` and then took the 7224r3a names, which is also right.
   - This is plan §13's criterion met on a 6,943-variable release, not a 50-variable slice.
2. **Topic queries now depend on what the agent does with the subject list.**
   - Run 3 took the GSS publisher's Religion subject (405 names) as it is: recall 0.85, precision 1.0. Its 37 misses are hits outside that subject, mostly belief items such as `biblauth`, `chrstsav` and the `postlf*` series.
   - Run 4 pruned the subject list by judgment to 65 GSS names: recall 0.18.
   - Both read about a quarter of their Task 51 tokens. The spread between them is the agent's choice, not the tools'.
   - The key counts the subject's off-topic members as neutral, so keeping them costs nothing here. A user who wants a precise list still has to judge each one.
3. **The catalog question is answered with years.** Both agents used `--names`, whose lines carry years. They found all 12 hits, `shakeblu` included, and gave exact years. Each also listed `sadblue`, which the key counts as neutral.
4. **The read-only rule is still bent.** Every run but one piped search output through `head`, `tail`, `grep` or a Python script. Tokens read are counted at the source, so they're an upper bound. The answers are scored as written.

### Next

- Topic recall in the GSS is now limited by the publisher's subject list. A topic annotation for religion, or a battery or section group for the belief modules, would let a search reach the other 37 items. That's §7.5's with/without-annotations comparison, which this setup can now run.
- `gss_spending_2024` wasn't rerun. SKILL.md now names `spending_3` and says what it gives, so a rerun would test whether the label problem (finding 3 of Task 51) is gone.

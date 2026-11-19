# Task 23 — Answer keys for the topic and structural queries

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE` (eval thread, 2026-11-19; not pushed)

Spike step 5. Before any search tool exists, build by hand:
- the **religion answer key** across the GSS, ANES and NSFG slices, and the full files where practical: every variable about religious affiliation, attendance, importance or belief;
- one **structural query** with its exact answer, e.g. every GSS item on ballot A in 1988 within the slice.

Then a scoring script for recall, precision and tokens read. Write the protocol before running any agent, as the earlier plan's §7.5 says. CultureWar's `notebooks/inventories/` are a starting point.

**Files:** new `eval/` in this repo.

**Done (eval thread):** [`eval/`](../../eval/), with [`PROTOCOL.md`](../../eval/PROTOCOL.md) committed before any run (8ef0d59) and [`RESULTS.md`](../../eval/RESULTS.md).
- **Keys.** Religion in the three slices: 19 variables (GSS 5, ANES 5, NSFG 9 over three tables). Structural: GSS ballot A in 1988 (39 hits plus 4 administrative variables as neutral) and ANES thermometers asked in 1978 (2), built from `metadata/` by script. Full-release religion keys in [`eval/keys/full/`](../../eval/keys/full/): GSS 241 hits and 327 neutral out of 762 candidates, ANES CDF 13 and 12, NSFG 17 and 3. Each was hand-sorted by a written rule.
- **Harness and scorer.** Agents get a copy of `agent/` and two logged commands, `read` and `search`, with a 40k-token budget that is enforced. `eval/score.py` gives recall, precision (neutral items ignored), tokens read, effort and whether the label is right. Tests are in `eval/test_eval.py`.
- **Results.** Six Sonnet runs on the slices: recall and precision 1.0 everywhere at 4k to 11k tokens; 5 of 6 labels right. After the `available` filter (df13f6f), four structural reruns were all exact with the right label (`complete` / `complete_by_rule`) at 1k to 2k tokens.

**Findings:**
- **The slices can't test topic search.** A release's line form is about 2.5k tokens, so agents read everything. The religion question needs a full release, where the line form would be about 350k tokens; the keys for that are ready.
- **No availability filter** (fixed): structural queries couldn't be `complete`, against STANDARD.md §7's own example. The coordinator decided to add `available`, and the views thread built it with these keys as tests.
- **Labels after pruning a shard by hand go wrong** (1 of 2 thermometer runs said `complete_by_rule`). The filter removes the need to prune.
- **Caveat on the reruns:** SKILL.md's `available` examples are the two test queries word for word. A structural question that isn't an example is the next test.
- **Measurement:** tokens read is what the commands printed. Agents that piped output through `head` or `grep` saw less, so the counts are an upper bound.


**For the full-release rerun (coordinator, 2026-11-19):** `pdt-gss` now builds from gssrdoc 0.9 and has two releases (7224r3, 7224r3a). Before rerunning the topic test on the full GSS release (Task 26), rebuild `eval/keys/full/gss_religion.yaml` from gssrdoc 0.9, and score names within the current release, so the two releases don't double count.

# Task 51 — Eval rerun on the full GSS

**Status:** `DONE (blue)`, 2026-11-20. Results: [`eval/RESULTS.md`](../../eval/RESULTS.md#task-51-the-full-gss-release).

Rebuild the eval keys from pdt-gss's 0.9 records, then rerun the topic and structural questions on the full GSS. Add a catalog question, with a hand-built key by Claude (PublicDataToolkit Task 51). The assignment came from the coordinator.

## Stopped here (2026-11-19)

**Done and committed** (`280dd86`, before any run, as the protocol requires):
- PROTOCOL.md's Task 51 section.
- Four keys, built by `eval/keys/build_task51.py` from `git archive` copies of the repos:

  | Key | Hits | Neutral |
  |---|---|---|
  | `religion_full` | 256 | 327 |
  | `gss_ballot_a_1988_full` | 635 | 7 |
  | `gss_spending_2024` | 27 | 0 |
  | `catalog_sadness` | 11 | 33 |

- `full/gss_religion.yaml`, rebuilt from the 0.9 records, with `reltrad16` added as a hit.
- Harness changes: `setup_run.py --repos`, `search catalog`, and `waves_exact` and `match_on` in `score.py`. pytest eval/ passes.

**Started, not committed:** 8 run directories in `eval/runs/`. Their sandboxes and repo copies are in the session scratchpad, which won't survive. Before Allen asked everyone to stop:
- 3 runs finished;
- 5 were still running, and I stopped them (spending ×2, catalog ×2, religion_full-1).

Outcomes of the finished runs, not yet scored or written into RESULTS.md:

| Run | Outcome |
|---|---|
| `gss_ballot_a_1988_full-1` | 0 items. Searched correctly, but the result was about 32,000 tokens, and a truncating pipe wasted the budget |
| `gss_ballot_a_1988_full-2` | No answer. It saved the search output to a file outside the harness, against the rules, and the classifier blocked its write. Excluded |
| `religion_full-2` | 9 items, NSFG only. It spent the budget reading the full GSS `index.md` unfiltered |

**Findings so far** (for RESULTS.md):
1. `pdt search` on a repo with two releases returns both. The ballot filter gives 1,282 rows (7224r3 plus 7224r3a), twice the 642 in the current release, and about 32,000 tokens: nearly the whole budget. Search should default to the current release, as the catalog does (`--all-releases`).
2. The full GSS `agent/index.md` is too big to read whole on a 40,000-token budget. SKILL.md or the index should warn about this, or the index should be split.
3. Agents work around the budget with shell pipes and files. The harness can't stop that, so the rules need a check, or the agents need a way to page through search results.

**Next step.**
1. Delete the 8 run directories in `eval/runs/` (`*_full-*`, `gss_spending_2024-*`, `catalog_sadness-*`). Their sandboxes are gone.
2. Recreate the repo copies (`git archive` of the commits in `PROTOCOL.md`'s Task 51 section).
3. Ideally after findings 1–2 are fixed in `pdt search` and the views (red), rerun all 8 with the same protocol. Record the fixes as a protocol change.
4. Score with `python eval/score.py eval/runs/<run>` and write RESULTS.md.

## Resumed and finished (2026-11-20)

- **The interrupted runs.** All 8 were mine (pinned to pdt-gss `cf22b43`) and incomplete, so I deleted them unscored.
- **The copies.** I recreated them at the pre-registered commits. pdt-brfss now has a commit, `e81369f`; before, its copy came from the working tree.
- **No drift.** The keys rebuilt identically, and `lib/pdt` hadn't changed since `280dd86`.
- **The reruns.** All 8 reran under the same protocol, one key changed by protocol, and the scores and findings went into `eval/RESULTS.md`.

| Question | Recall |
|---|---|
| Religion, full GSS | 0.03 and 0.11 |
| Ballot A 1988, full | 0.02 and 0.07 |
| Spending 2024 | 1.0 and 1.0 (labels `approximate`, not `complete_by_rule`) |
| Catalog sadness | 0.83 and 1.0 |

- **Key change.** `shakeblu` was a real miss in `catalog_sadness`, and the key now includes it (`58e55f6`). The scores against both keys are in RESULTS.md.

**Main findings, for red and the coordinator:**
1. `pdt search` returns both GSS releases, which doubles the output: 1,282 rows, about 32,000 tokens.
2. The full GSS `index.md` is about 31,000 tokens, and agents read it first.
3. Agents don't find scale signatures unless they're named.
4. Catalog search can't return or filter by year.

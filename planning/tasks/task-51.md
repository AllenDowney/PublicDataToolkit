# Task 51 — Eval rerun on the full GSS

**Status:** `DOING (blue)`. Stopped 2026-11-19 for Allen's shutdown.

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

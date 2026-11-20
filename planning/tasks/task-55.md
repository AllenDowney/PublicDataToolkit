# Task 55 — A Household Pulse Survey slice

**Status:** `DOING (purple)` — assigned by the coordinator on 2026-11-20.

The Census Bureau's Household Pulse Survey (HPS), an online survey of adults run every one or two weeks from April 2020 to 2024. Its questionnaire changed by phase, so it tests availability across many waves, rotating content, and links across phases. From [`planning/twenge_catalog.md`](../twenge_catalog.md).

1. Find the public-use files (PUFs), data dictionaries, questionnaires and technical documentation on census.gov, and record the Census terms. The decision stays open for Allen.
2. `~/pdt-pulse` from the template (`copier copy --vcs-ref v0.1.0`), no remote.
3. About 25 variables: demographics, the anxiety and depression items, food sufficiency, the weights, in every wave they appear. Replicate weights go in `design.replicates`, with `fay_factor` if Census's documentation gives it. Use `data_waves` if only some weeks' data are kept.
4. `make data` round trip; `pdt check` 0 failures.
5. Here: what the HPS tests, with proposals.

**Files:** `~/pdt-pulse/` (new, no remote); this file; the Task 55 block on the board.

## Progress

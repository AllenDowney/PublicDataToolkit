# Task 59 — A Cooperative Election Study slice

**Status:** `DOING (red)`, claimed 2026-11-20.

The Cooperative Election Study (CES, formerly CCES), an online survey of U.S. adults run by YouGov since 2006, released on Harvard Dataverse. It has a cumulative common-content file and a file per year, so it's the second cumulative↔yearly case after the ANES.

1. Find the cumulative common-content file and the yearly common-content files on Dataverse, their guides, and the Dataverse license. Leave the terms decision for Allen.
2. `~/pdt-ces` from the template (`copier copy --vcs-ref v0.1.0`), no remote.
3. A slice: the cumulative file and two or three yearly files, linked by `derived_from` where the cumulative guide documents how a variable was built from the yearly items.
4. `make data` round trip under the memory cap; `pdt check` 0 failures.
5. Here: what the CES tests, with proposals.

**Files:** `~/pdt-ces/` (new, no remote); this file; the Task 59 block on the board.

## Progress

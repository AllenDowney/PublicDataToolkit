# Task 60 — An NSDUH slice

**Status:** `DOING (blue)`, claimed 2026-11-20.

The National Survey on Drug Use and Health (SAMHSA) in `~/pdt-nsduh`, built from the Copier template, as in the other dataset tasks:
- annual public-use files, for recent years;
- substance use and mental-health items, plus the design variables (weights, strata, PSUs).

SAMHSA's terms are recorded in the repo, and the decision is left to Allen. Every data job runs under the memory cap (`systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0`).

Task 57 (blue) is paused waiting for an API key. The coordinator will say when to go back to it, or to the catalog rebuild.

**Files:** `~/pdt-nsduh/`, this file and the Task 60 block on the board.

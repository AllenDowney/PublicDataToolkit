# Task 18 — `download.py` and the data release

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DOING (views + site)`

Part of Task 11. A standard `scripts/download.py` for dataset repos:
- it reads `sources.yaml`;
- fetches automated sources, and explains the manual ones;
- checks the SHA-256 sums;
- has a `--check` mode;
- refuses to run until the user accepts the publisher's terms, as MarriageNSFG's script does.

Also a build step that writes the common-format parquet files for a data release. Start with `pdt-nsfg`, where every source can be downloaded. **Don't create GitHub releases**; Allen does that when the repos are published.

**Files:** new code in `lib/pdt/` (e.g. `download.py`), `scripts/` and `Makefile` in the dataset repos. Later, `templates/` for Copier (Task 8).

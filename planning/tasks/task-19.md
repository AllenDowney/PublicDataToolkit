# Task 19 — `extract.py`, the extract builder

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `TODO` — ready for a second thread

Part of Task 11. `scripts/extract.py` in a dataset repo: the user names the variables, waves and how to treat each missing type, and gets an extract, with no analysis choices built in. It uses `pdt.data.recode`. Test it by rebuilding a CultureWar GSS extract column and comparing.

**Files:** `lib/pdt/data.py` (owned by this task while `DOING`), new `lib/pdt/extract.py`, tests, `scripts/` in the dataset repos.

**Also (from Task 20, STANDARD.md §5.3):** when `recode` classifies a code because of an `inferred` correction (e.g. ANES 2024 `-1` → inap), it must say so: warn, or report the codes and corrections it relied on.

# Task 36 — Non-survey data in the library

**Status:** `DOING (orange)`, from 2026-11-19.

The library side of the standard changes from Task 33's proposals (STANDARD.md and `schema/`, commit `827af76`):

1. **`check.py`:** C5 checks only a file's `data_waves`. C6 reports missing question text only when `kind` is `survey`, or absent. C11 checks that the README contains `terms.notice` when it's set.
2. **`download.py`:** for a `live` source, `--check` reports "changed since snapshot <date>", not a mismatch; a fetch keeps the new file as `.new`, as usual.
3. **The dataset repos:** pdt-chicago-crimes gets `data_waves: ["2024"]`, live sources, `kind: portal` and the City's disclaimer as `terms.notice`. pdt-gss, pdt-anes-cdf and pdt-nsfg get `kind: survey`; pdt-fars gets `kind: administrative`. `pdt check` on all five.
4. Tests.

**Files:** `lib/pdt/check.py`, `lib/pdt/download.py` (from red for this task) and their tests; `dataset.yaml`, `sources.yaml` and the README in the dataset repos; this file and Task 36's block on the board.

# Task 17 — Data checks C3–C5 in `pdt check`

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `TODO` — ready for a second thread

Move the data checks out of each repo's build and into `pdt check`, reading the common-format parquet files:
- **C3 coverage:** every data column has a record, and every record a column.
- **C4 codes:** every code in the data is documented.
- **C5 availability:** waves and forms match the data, using the dimension columns in `dataset.yaml`.

They're skipped, with a notice, when the parquet files are absent.

**Files:** `lib/pdt/check.py` (owned by this task while `DOING`) and its tests. Each dataset repo needs a step that writes its parquet files with `pdt.data`; coordinate with Task 18.

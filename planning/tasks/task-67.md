# Task 67 — Library and pdt-brfss use the Task 30 standard changes

**Status:** `DOING (green)`

Assigned by the coordinator on 2026-11-20, after accepting Task 30's proposals 1–5 into the standard (e882451).

1. **The library:** everything that reads `valid_range` accepts the list form (`check.py`, `diff.py`, `site.py`, `export.py`, `derived.py`), and availability filters and views handle `geography`. Tests.
2. **pdt-brfss uses them:** ALCDAY5's two ranges; state-module availability as `geography` (with `dimensions.geography`); per-code notes (`values[].note`) instead of joined notes; histories with `origin: rule`; a `series` annotation for one or two concepts (depression, 2011–2023), labeled as ours.
3. **Proposal 6:** a label lint in `pdt check`, warn-level.
4. **Proposal 7:** `pdt.readers.read_sas_xport` from `pdt-brfss/build/xport.py` (selected columns, from a zip, SAS missing values as `Code`), with a test. Orange is editing `readers.py` for Task 58: coordinate first.

Data jobs run under the memory cap.

**Files:** `lib/pdt/` (the modules above, and tests in `lib/tests/`); `~/pdt-brfss/`; this file; Task 67's block on the board.

## Progress

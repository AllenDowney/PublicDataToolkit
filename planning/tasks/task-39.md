# Task 39 — Library changes from the YRBSS findings

**Status:** `DOING (purple)` — assigned by the coordinator on 2026-11-19, from the proposals in [task-29.md](task-29.md).

1. `lib/pdt/derived.py`: `valid_labels` handles valid codes without a label (the schema makes `label` optional), with a test.
2. `lib/pdt/readers.py`: add `read_sas_input`, from pdt-yrbss's `build/sadc.py`, with tests, and switch pdt-yrbss to it. Red owns `readers.py`; this adds one function and changes nothing else.
3. `lib/pdt/check.py`: warn when a name appears in two releases with no link between those records, while one of them links to a different name (proposal 1).
4. `lib/pdt/data.py` and extract: an option of `recode` and extract, off by default, that splits a missing code whose types include `not_asked`: `not_asked` outside the variable's availability, the other types inside it (proposal 5).
5. pdt-yrbss: set `design` in `dataset.yaml`, `make views`, `pdt check` 0 failures.

**Files:** `lib/pdt/derived.py`, `lib/pdt/readers.py`, `lib/pdt/check.py`, `lib/pdt/data.py`, `lib/pdt/extract.py`, their tests in `lib/tests/`; `~/pdt-yrbss`; this file; the Task 39 block on the board.

## Progress

# Task 39 — Library changes from the YRBSS findings

**Status:** `DONE (purple)` — assigned by the coordinator on 2026-11-19, from the proposals in [task-29.md](task-29.md); done the same day.

1. `lib/pdt/derived.py`: `valid_labels` handles valid codes without a label (the schema makes `label` optional), with a test.
2. `lib/pdt/readers.py`: add `read_sas_input`, from pdt-yrbss's `build/sadc.py`, with tests, and switch pdt-yrbss to it. Red owns `readers.py`; this adds one function and changes nothing else.
3. `lib/pdt/check.py`: warn when a name appears in two releases with no link between those records, while one of them links to a different name (proposal 1).
4. `lib/pdt/data.py` and extract: an option of `recode` and extract, off by default, that splits a missing code whose types include `not_asked`: `not_asked` outside the variable's availability, the other types inside it (proposal 5).
5. pdt-yrbss: set `design` in `dataset.yaml`, `make views`, `pdt check` 0 failures.

**Files:** `lib/pdt/derived.py`, `lib/pdt/readers.py`, `lib/pdt/check.py`, `lib/pdt/data.py`, `lib/pdt/extract.py`, their tests in `lib/tests/`; `~/pdt-yrbss`; this file; the Task 39 block on the board.

## Progress

**Done (purple, 2026-11-19).** Toolkit commits `3276237`, `9ab5f84`, `52fa250`, `e61f3a3`; pdt-yrbss `701cb58`, `6f5fb98`. pytest: 204 passed, 1 skipped.

| Item | Change | Tests |
|---|---|---|
| `valid_labels` | A valid code without a label gives `None`, so its record has no signature; no KeyError. Rule stays 0.2: no signature it gave before changes. | `test_derived.py::test_valid_codes_without_labels` |
| `read_sas_input` | `pdt.readers.parse_sas_input(path)` gives `{name: (start, end, is_text, label)}` from a SAS input program's `input` and `label` statements. `read_sas_input(dat, input_sas, columns)` keeps `$` columns as text, blanks included, and reads a numeric `.` or blank as `Code(".")`. Nothing else in `readers.py` changed (agreed with red). | `test_readers_sas_input.py` (4 tests, including a common-format round trip) |
| Name reuse (proposal 1) | C2 reports a warning when a name is in two releases, the two records aren't linked, and one of them is linked to a different name in the other release. | `test_check.py`: warns for YRBSS-like renumbering; no warning when the name is linked or when there are no links |
| C12 `target_columns` | From yellow's CPS finding, added by the coordinator. C12 looks for `target_columns` (default `columns`) in the target table, and C2 checks that those columns have records and that there are as many as `columns`. | `test_check_data.py`: a passing and a failing reference with `target_columns`; C2 with an unknown target column |
| `not_asked` from availability (proposal 5) | `recode(..., not_asked_from_availability=True, waves=<column or sequence>)`, off by default. A missing code whose types include `not_asked` counts as `not_asked` only, in a wave outside the record's `availability`, and as its other types inside it. A row with no wave keeps every type. `result.attrs["not_asked_split"]` counts both. `extract(..., not_asked_from_availability=True)` and `--not-asked-from-availability` use the wave column and say in the report how many cells went each way. | `test_not_asked.py` (5 tests) |
| pdt-yrbss | `design: {weights: [weight], strata: stratum, psu: PSU}`. The data is read with `pdt.readers.read_sas_input`; records and data are unchanged. The link rules, now 0.2, compare labels with `pdt.compare.compare_text`, so `sex` (case only) is `same_item`. Views regenerated; `pdt check` 0 failures. | |

**Checks on real repos:**
- **pdt-yrbss:** the name-reuse warning fires on exactly its 7 renumbered names: `q26`, `q27`, `q28`, `q41`, `q42`, `q85`, `qn26`. `extract` with the new option turns all 55,734 of `q26`'s blanks in 1991–1997 into `not_asked`, and leaves its 2,313 blanks from 1999 on as no answer or invalid.
- **pdt-cps-asec:** its working tree has uncommitted changes (yellow's, it seems), and its data files match neither the committed nor the current records, so `pdt check` skips C12 there. I ran C12's function directly on the data files and the references in `dataset.yaml`, read-only. All 5 references run and pass in all 7 years (35). With the previous `check.py`, the `target_columns` references were skipped ("columns not in the data: FH_SEQ").

**Notes:**
- A full pytest run failed once (1 failed, 182 passed) while another thread had uncommitted edits to `lib/pdt/diff.py` and `lib/tests/test_diff.py`. The next run passed, and I didn't touch those files.
- Orange committed its Task 41 hunks of `check.py` while mine were in the working tree. Then I committed my hunks only.

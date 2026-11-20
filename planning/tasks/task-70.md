# Task 70 — `pdt check` says which checks didn't run, and why

**Status:** `DONE (purple)`, 2026-11-20. This is next step 3 of [`planning/daaf.md`](../daaf.md), suggested by the coordinator after Task 68. DAAF's data-ingest agent declares each check that doesn't apply, with a reason. Before this task, `pdt check` skipped some checks silently.

**Files:**
- `lib/pdt/check.py`: `Result.skip` and `Result.not_run`. Orange's uncommitted Task 58 hunk in this file was left out of the commit.
- `lib/pdt/cli.py`: prints a "not run" section.
- [`lib/tests/test_check_not_run.py`](../../lib/tests/test_check_not_run.py): 5 tests.

## What changed

**`Result`:**
- `Result.not_run` lists every check, or part of a check, that didn't run.
- `Result.skip(check, message)` records one, with "not run, because ...".
- A report whose message says "skipped" goes in the list too. So the existing skip messages (C3–C5 and C12 data files, C5 without a wave column, C12 columns absent) keep their wording, and the tests that match them don't change.

**`pdt check`** prints those lines once, as `not run C7: because there are no corrections`, rather than as reports.

**Parts that used to be silent or to look like findings:**

| Check | Not run when |
|---|---|
| C3 | `data_rows` names a column the data file lacks. The wording is unchanged, because a test matches it. |
| C5 | no record has `availability` |
| C7 | there are no corrections |
| C8 | `views=False` (the tests); docs/ isn't built here; export/daaf/ isn't exported here (made on request) |
| C9 | the repo isn't a git repository, so tracked files can't be checked |
| C10 | no record has extensions |
| C12 | no table declares a key or references; a reference points to another dataset or release (this one was silent) |

## Result

- **pytest:** 296 passed, 1 skipped.
- **pdt-nhis:** C7 and C10 don't apply. The data checks don't run on its 15 data files, which were built before the round-trip marker (Task 58), until `make data` rebuilds them.

## Not done

**A documented-frequency check,** the other half of step 3: compare the `n` the codebook gives for each code with the data. It's left for a later task, since it needs `values[].n` from more than the NSFG.

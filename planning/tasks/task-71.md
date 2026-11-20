# Task 71 — `pdt check` compares codebook counts with the data

**Status:** `DONE (blue)`, 2026-11-20. Asked for by the coordinator: four builds checked counts by hand (NSDUH, NHANES, MEPS, NCVS), so the library should do it.

**Files:** `lib/pdt/check.py` (`has_counts`, `code_counts`, `check_counts`, called from `check_data`), `lib/tests/test_check_counts.py`, two assertions in `lib/tests/test_check_data.py`, and C5's row in STANDARD.md §9.

## What it does

Part of C5, at warn level, per data file (release or table), on the common-format files in `data/processed/`:

- **Code counts.** Each `values[].n` (the publisher's count of cases with that code in the release) is compared with the rows that have it. Valid codes are counted in the value column. Missing and unresolved codes are counted in `<name>__code`, where `data.split` puts them. The records are the corrected ones, as the other data checks use. A mismatch warns with the code, its label and both counts: `C5: warning: r1/crash/LIGHT: code counts differ from the data: 1 (Day): codebook 3, data 2`.
- **Availability counts.** Each `availability[].n` (non-missing responses in that wave) is compared with the non-missing values in that wave. It uses the wave column, or the whole file when the file is one wave.

**Not run, each recorded with `Result.skip` (Task 70):**

| Case | Why |
|---|---|
| Data files are loaded but no record has counts | "counts not run, because there are no codebook counts" (once per repo) |
| The file holds only some rows (`data_rows`) | Neither count can be compared |
| The file holds only some waves (`data_waves`) | `values[].n` counts the whole release, so it isn't compared; availability is compared for the kept waves |
| An availability entry with a form, sample, mode, phase or geography | The file doesn't say which rows it covers (BRFSS's state modules) |

Tests: `lib/tests/test_check_counts.py`, 7 cases. The full suite passes: 304 in the working tree, and 294 on the committed tree without orange's uncommitted Task 58 hunks.

## Run across the repos (2026-11-20)

I ran `pdt check` on the 13 repos with `data/processed/`, under the 6 GB cap. In the working tree, every file was skipped before C3–C5:
- Orange's uncommitted Task 58 hunk skips any file without a `round_trip: verified` marker, and no existing file has one yet.
- GSS's and YRBSS's files were also built from older records.

So, to see what the check finds, a scratch script ran `check_data` with the marker treated as present. It changed no repo.

| Repo | values n | availability n | Result |
|---|---|---|---|
| anes-cdf, pisa, pulse | 0 | 0 | not run: no counts |
| atus | 0 | 14,501 | match; one table has no wave column (existing C5 skip) |
| brfss | 0 | 364 | match; 74 counts by geography not run |
| chicago-crimes, cps-asec, fars | 0 | 546 / 287 / 80 | match |
| nhis | 753 | 231 | match |
| nsfg | 699 | 104 | match |
| nlsy97 | 4,213 | 661 | one warning (below) |

**One finding, for the NLSY97 thread:** `person_year/CV_INCOME_FAMILY`, wave 2023, availability 5,955 but 5,957 non-missing values in the data. The build's note says n "counts values that aren't negative codes", so two negative values are probably valid incomes. On a rerun the file was being rebuilt (13:17), so the check skipped it as stale. The repos I built by hand (NSDUH, NHANES, MEPS, NCVS, HINTS) have no `data/processed/`, so their build reports still hold their count checks.

GSS's full `pdt check` took 40 minutes, and the time went outside the data checks: its files were skipped as stale. Its C8 fails because the views generator changed.

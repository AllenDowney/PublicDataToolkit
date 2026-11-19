# Task 17 — Data checks C3–C5 in `pdt check`

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `TODO` — ready for a second thread

Move the data checks out of each repo's build and into `pdt check`, reading the common-format parquet files:
- **C3 coverage:** every data column has a record, and every record a column.
- **C4 codes:** every code in the data is documented.
- **C5 availability:** waves and forms match the data, using the dimension columns in `dataset.yaml`.

They're skipped, with a notice, when the parquet files are absent.

**Files:** `lib/pdt/check.py` (owned by this task while `DOING`) and its tests. Each dataset repo needs a step that writes its parquet files with `pdt.data`; coordinate with Task 18.

## Done (fars thread, 2026-11-19)

`pdt check` runs C3, C4, C5 and C12 on the common-format files in `data/processed/` (commit `ec78d00`, 16 tests in `lib/tests/test_check_data.py`). Each check is skipped with a notice when a release's or table's file is missing, or when it was built from other records: its `metadata_sha256` doesn't match the current `variables.jsonl`. pdt-fars now has `make data` (`scripts/build_data.py`, pdt-fars `1ead90b`), so all four repos have data files.

| Check | What it does | On failure |
|---|---|---|
| C3 | Every record has a column in the repo's data file, and every column has a record | fail |
| C4 | Every code in a code column (`X__code`) is in the record's `values`. A categorical or ordinal variable's valid values that aren't listed and aren't in `valid_range` are reported | fail; report |
| C5 | The waves in `availability` are the waves with non-missing values. The wave comes from `dimensions.wave.column`; a file without that column whose records declare a single wave is that wave (NSFG cycles, FARS's vehicle, person and parkwork tables) | warn |
| C12 | Each table's key is unique and non-blank. Each reference within a release finds its target row, for the rows its `when` selects | fail |

**Results on the four repos:** 0 failures in each. The only data reports are 9 for the ANES CDF, which go to the ANES thread:
- C4: `VCF0878` has the valid value 2 in the data, but it isn't in `values`.
- C5: values in waves that `availability` doesn't list: `VCF0006`, `VCF0104`, `VCF0301` and `VCF0128` in 1954; `VCF0830` in 2012; `VCF0878` and `VCF0704` in 2016; and the weight `VCF0009z` in 17 waves.
- The checks take 2–4 seconds per repo.

**For the standard (coordinator):**
1. **C3 and slices.** §9 says "every variable in the data file has a record". A slice repo's data file holds only the variables it has records for (`pdt.release` writes it that way), so C3 compares records with that file. Checking against the publisher's full file would fail every slice. Suggested wording: "the repo's data file".
2. **C4 and value labels.** §9 asks about codes that "have a value label" in the data file. The common format doesn't keep the source's value labels, so `pdt check` can't see them. That half stays in each build's comparison with the source (FARS's NAME columns, Stata labels). `pdt check` checks the code columns, and reports unlisted valid values.
3. **C5 covers waves only.** Forms (GSS ballots) and `n` aren't compared yet. A table without the wave column in a release with several waves is skipped with a notice. It could take its wave through a reference to a table that has one.
4. **The §9 paragraph is out of date.** It still says "Version 0.1 implements C1, C2, C6, C7, C9, C10 and C11. C3–C5 ... run in each repo's build". Now C8 is the only check not implemented.

**Overlap:** pdt-fars's build still checks keys and references against the CSVs (`build/report.md`), which C12 now does from the parquet files. It can be removed once `make data` is part of the usual build.

## The ANES reports, triaged (fars thread, 2026-11-19)

All 9 are resolved. `pdt check` on pdt-anes-cdf now gives 0 failures and no data reports.

- **`VCF0878` value 2 (C4), and 7 of the 8 C5 warnings, were a bug in `pdt check`.** `pdt.release` splits the data with the *corrected* records, and the data checks were comparing against the uncorrected ones. Correction `vcf0878-2024-code-2` (inferred) makes code 2 valid, so the file has 2 in the value column, which the uncorrected record lists as unresolved. The 1954, 2012 and 2016 waves for `VCF0104`, `VCF0128`, `VCF0301`, `VCF0830`, `VCF0704` and `VCF0878` are Task 20's verified availability corrections. The data checks now apply `corrections.jsonl`, as `pdt.release` does. A data file whose `corrections_sha256` doesn't match is skipped as stale. Commit `7a8278d`, with a test.
- **`VCF0006` in 1954 was a codebook omission** (PDF page 17: the Sources list has no 1954), like Task 20's four 1954 corrections. All 1,139 respondents in 1954 have a case ID. It's now correction `vcf0006-sources-1954`, `verified`, upstream `not_filed`. Task 20 missed it because the ANES build exempts `VCF0004`, `VCF0006` and `VCF0009z` from its own availability check.
- **`VCF0009z`, the weight, in 17 waves, was incomplete availability, not an error in the codebook.** Its Sources list names the 16 years with a study weight. In each of the other 17 years (1948–1956, 1962–1972, 1978–1990), every respondent has exactly 1.0, a uniform weight. That includes 1970, even though the label says "for 1970 type 0". The waves are added by hand (`availability_added` in `build/slice.yaml`, `origin: hand`, with the reason in the field's provenance). They aren't a correction, because the codebook doesn't say anything wrong. pdt-anes-cdf commit `03a091a`; `make data` was rerun, and the build script is unchanged.

# Task 19 — `extract.py`, the extract builder

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE (nsfg)` 2026-11-19. PublicDataToolkit f4d57fe; `scripts/extract.py` in pdt-gss (b64f40c), pdt-anes-cdf (fb843fd), pdt-nsfg (67cbd4a) and pdt-fars (0bd5e10). Not pushed. `lib/pdt/data.py` is free again.

Part of Task 11. `scripts/extract.py` in a dataset repo: the user names the variables, waves and how to treat each missing type, and gets an extract, with no analysis choices built in. It uses `pdt.data.recode`. Test it by rebuilding a CultureWar GSS extract column and comparing.

**Files:** `lib/pdt/data.py` (owned by this task while `DOING`), new `lib/pdt/extract.py`, tests, `scripts/` in the dataset repos.

**Also (from Task 20, STANDARD.md §5.3):** when `recode` classifies a code because of an `inferred` correction (e.g. ANES 2024 `-1` → inap), it must say so: warn, or report the codes and corrections it relied on.

## What was built

- **`lib/pdt/extract.py`.** `extract(root, release, variables, table=None, missing=None, unresolved=None, waves=None, codes=False)` returns `Extract(frame, report)`:
  - It reads `data/processed/<dataset>-<release>[-<table>].parquet`, and warns (`MetadataMismatch`) if the file was built from other records or other corrections.
  - It recodes each variable with `pdt.data.recode`, using the corrected record (variables.jsonl with corrections.jsonl applied, as `pdt.release` split the file). `missing` maps types to replacements (`{"dk": "DK"}`); every other missing value, and every unresolved code unless `unresolved` is given, is null.
  - `waves` keeps rows by the dataset's `dimensions.wave.column` (GSS `year`, ANES `VCF0004`, FARS `YEAR`). The NSFG has no wave column, since its waves are its releases.
  - `codes=True` keeps the code columns. Names match ignoring case when that's unambiguous.
  - A column with only numbers and nulls keeps its value column's dtype; a text replacement makes it objects.
- **`main()`** is the CLI. `scripts/extract.py` in each of the four dataset repos calls it: `--release`, `--table`, `--vars`, `--missing dk=DK refused=DK`, `--unresolved`, `--waves 2000-2024`, `--codes`, `--out x.csv|x.parquet`. The report goes to stderr.
- **Inferred corrections (STANDARD.md §5.3).** `pdt.data.recode` takes `inferred={code text: [correction ids]}` and warns `InferredClassification` when those codes occur, with the count and what was done (replaced with X, or left null as their type). The extract finds those codes from the corrections applied to each record (`/values/N` pointers with `confidence: inferred`). It also reports a code that an inferred correction made valid, which is a value in the file. On the ANES 2020-2024 waves:
  - VCF0806 code -1 (245 values) is missing only because of inferred correction vcf0806-code-minus1, and VCF0218 code -8 (9 values) only because of vcf0218-code-minus8;
  - VCF0878 value 2 (1,130 values) is valid, labeled "No (2024; coded 5 in other years)", only because of inferred correction vcf0878-2024-code-2.

## Checks

| Comparison | Result |
|---|---|
| pdt-gss 7224r3a, every missing value null, against CultureWar's `notebooks/gss_extract_2024_r3a.hdf` | all 50 shared columns identical, 75,699 rows |
| pdt-nsfg 2017-2019 female: RMARITAL, FMARITAL, WGT2017_2019, against MarriageNSFG's `data/interim/FemMarriageData.parquet` (cycle 11), joined on case ID | identical, 6,141 rows |
| pdt-nsfg 2022-2023 female: the same, against cycle 12, by row position | identical, 5,586 rows |

Tests: `lib/tests/test_extract.py` (10), with a small repo that has an inferred correction of each kind.

## Findings

- **MarriageNSFG's cycle 12 `caseid` is all null** in `data/interim/FemMarriageData.parquet`. Its reader probably asks for `caseid`, and the 2022-2023 SAS file spells it `CaseID`. That's for MarriageNSFG, not this repo.
- **pdt-anes-cdf's data file predates its latest corrections.jsonl** (the corrections were marked `filed` after `make data`), so the extract warns that it was built with other corrections. Rebuilding with `make data` clears it.
- No Makefile targets were added; the dataset repos' Makefiles had other threads' uncommitted changes. `make extract` could be added later.

# Task 18 — `download.py` and the data release

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE` (views + site thread, 2026-11-19; nothing pushed, no GitHub releases made)

Part of Task 11. A standard `scripts/download.py` for dataset repos:
- it reads `sources.yaml`;
- fetches automated sources, and explains the manual ones;
- checks the SHA-256 sums;
- has a `--check` mode;
- refuses to run until the user accepts the publisher's terms, as MarriageNSFG's script does.

Also a build step that writes the common-format parquet files for a data release. Start with `pdt-nsfg`, where every source can be downloaded. **Don't create GitHub releases**; Allen does that when the repos are published.

**Files:** new code in `lib/pdt/` (e.g. `download.py`), `scripts/` and `Makefile` in the dataset repos. Later, `templates/` for Copier (Task 8).

## What was built

| Piece | What it does |
|---|---|
| [`lib/pdt/download.py`](../../lib/pdt/download.py), `pdt download` | Reads `sources.yaml`. `--check` reports ok / missing / mismatched / manual without using the network, and exits non-zero if anything is missing. Fetching needs `--accept-terms`; without it, the script prints the terms URL and summary from `dataset.yaml`. It verifies SHA-256 and keeps a mismatched download as `<path>.new`. It never overwrites without `--force`, prints `manual_steps`, prints the values to record when no checksum exists, and converts PDF codebooks with `pdftotext -layout`. |
| [`lib/pdt/readers.py`](../../lib/pdt/readers.py) | Raw-frame readers that read only the recorded columns: Stata (`.dta`, `.dta.gz`; extended missing → `Code`), SAS (missing → `Code(".")`), CSV in a zip, and fixed-width `.dat` with a Stata `.dct` (blank → `Code(".")`; names matched case-insensitively). |
| [`lib/pdt/release.py`](../../lib/pdt/release.py) | `write_release(root, reader)` writes `data/processed/<dataset>-<release>[-<table>].parquet` and proves the round trip. `data_source` finds a release's or table's data file from `dataset.yaml` and `sources.yaml`. `package(root)` (`pdt package`) assembles `data/release/<dataset>-data/`: the publisher's data files unchanged, the common-format files, and `SHA256SUMS`. |
| Export | Each table's `source` names its parquet file, so data-dict can validate the data. |
| Dataset repos | `scripts/download.py` and `scripts/build_data.py` in `pdt-nsfg`, `pdt-gss` and `pdt-anes-cdf`. `pdt-fars`'s `build_data.py` was written by the fars thread with the shared readers. Make targets: `download`, `data` and `package` in `pdt-nsfg` and `pdt-anes-cdf`; `data` in `pdt-fars` (fars thread). |

## Results on the real files

| Repo | Files | Rows | Round trip | `data-dict validate-data` |
|---|---|---|---|---|
| `pdt-nsfg` | 6 (2022-2023 SAS; 2017-2019 fixed-width) | 5,586 to 10,215 per table | exact | ok, both releases |
| `pdt-gss` | 2 (7224r3a, 7224r3) | 75,699 each | exact | ok, both releases |
| `pdt-anes-cdf` | 1 | 73,745 | exact, with 11 corrections applied | ok |
| `pdt-fars` | 8 (2017, 2024 × 4 tables) | 1,383 to 88,326 | exact | ok, both releases |

`pdt package` runs for `pdt-nsfg` (16 files, 175 MB), `pdt-gss` and `pdt-anes-cdf`. `data/` is gitignored, so none of this is committed.

## Decisions

- **Split with the corrected records** (coordinator, option (a); STANDARD.md §8, c24b364). The identity holds `corrections_sha256` and lists the corrections applied (`id`, `confidence`, `variable`). This came up because ANES `vcf0878-2024-code-2` makes code 2 valid. Split with the source records, the data and the export disagreed, and data-dict failed with D04.
- **Terms** (coordinator, after the C9 change): building `data/processed/` is allowed for any terms. A file whose `terms.data` or source isn't `ship` gets `local_only` in its identity, and `package` refuses before writing anything.
- **Code columns in every release:** a variable whose records list missing codes always has `<name>__code`, all null if no code occurs, with the code texts as its categories. Without this, FARS 2017 `PHARM_EV__code` was missing from the data (data-dict M02). An all-null column with no categories reads as a number (M01).
- **Conditional references aren't foreign keys in the export.** FARS person → vehicle applies only when PER_TYP is 1, 2 or 9. Non-motorists have VEH_NO 0, and data-dict checks every foreign key unconditionally (D05). The relationship stays, with its condition in the description.
- **Parquet files hold the variables the repo has records for,** not the whole publisher file. The identity names the `variables.jsonl` and `corrections.jsonl` they were split with. (Not yet confirmed by the main thread.)
- **One `--accept-terms` flag for every dataset,** instead of MarriageNSFG's `--i-accept-nchs-terms`; the terms text comes from `dataset.yaml`. (Not yet confirmed.)

## Findings

- **www.cdc.gov** answers 403 to a custom User-Agent (`PublicDataToolkit-download/0.1`) and to a browser string, but accepts urllib's default and curl's. ftp.cdc.gov accepts all of them. The script sends urllib's default.
- **The PDF → text conversion is reproducible:** fetching the NSFG pregnancy codebook and running pdftotext 24.02 gives exactly the recorded checksum. A different poppler version may not.
- **pandas' sas7bdat reader** prints "column count mismatch (426 + 1395 != 1912)" for the NSFG female file. The round-trip check is against what pandas reads.
- **Reading only the recorded columns** keeps the GSS (thousands of columns, 75,699 rows) to about 20 s per release. Most of that is decompressing the gzip.
- **Shared-checkout hygiene:** two of my commits picked up other threads' work (the board in 2f2f3b6, a staged rename in 9daad38), and a helper script emptied the board's working copy before reading it. The habits now: commit with `git commit -- <paths>`; never write a shared file before reading it in full; restore from git.

## Proposed for Task 25

- **Conversions in `sources.yaml`:** a field such as `convert: pdftotext-layout`, so `download.py` doesn't infer it from a `.pdf` URL and a `.txt` path. The checksum then depends on the converter's version.

## Follow-ups (other threads)

- `pdt-gss`: `make download`, `data` and `package` targets. The gss thread has uncommitted Makefile changes, so I didn't edit it. The scripts are committed.
- `pdt-fars`: a `scripts/download.py` (all FARS sources are manual, so it's `--check`), and committing its `build_data.py`.
- Regenerate `pdt-anes-cdf`'s views once the anes thread commits its pending metadata change.
- `templates/` for Copier (Task 8): the scripts are the same in every repo except the reader.

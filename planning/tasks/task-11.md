# Task 11 — Data releases, download script and extract builder

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `TODO` — decided 2026-11-19

The workflow for someone who clones a dataset repo:
1. `make download` runs `scripts/download.py`. It fetches the data release, checks the SHA-256 sums in `sources.yaml`, and refuses to run until the user accepts the publisher's terms, as MarriageNSFG's script does.
2. `scripts/extract.py` builds the extract the user asks for: variables, years, and how to treat each missing type.

None of this exists yet for `pdt-gss` or `pdt-anes-cdf`.

**Decided (Allen, 2026-11-19):**
- **Extract builders live in dataset repos** (plan §10 item 5), rather than only in analysis projects. To keep STANDARD.md's first principle, the builder's options encode no analysis choices; the user supplies them. The recoding by missing type lives in the shared library, so it behaves the same everywhere.
- **A data release holds the publisher's original files plus a common format (parquet) written by the build.** The library reads every dataset through the common format.

**Design out for review (2026-11-19):** [`planning/missing_codes_design.md`](../../planning/missing_codes_design.md) compares three layouts, and parquet against Arrow and CSV, measured on both slices. It recommends one parquet file with a `<name>__code` column next to each value column. Round trips back to the publisher's values are exact for both slices. Waiting for review before building.

**To design first:** how the common format keeps missing codes distinct. Stata's `.d`/`.i`/`.n` have no parquet equivalent, and the ANES stores missing codes as ordinary numbers. A code column next to each value column is one option. The same files could feed the data checks C3–C5 in `pdt check`, so they no longer have to run in each repo's build.

**Steps:**
1. Design the common format; add it to STANDARD.md and a schema if needed.
2. The library: read the common format; select; recode by missing type.
3. `download.py` and `extract.py` in the Copier template, and copies in `pdt-gss` and `pdt-anes-cdf`.
4. The first data releases, once the repos are pushed.

**Progress (2026-11-19):** Review 2 accepted Option A with five refinements; triage and decisions are in [`planning/review_2.md`](../../planning/review_2.md). All five are in the design doc and STANDARD.md §4.2, §8 and §10, and `dataset.schema.json` gained `column` and `codes` for dimensions.
- `lib/pdt/data.py` implements split, write, rebuild and recode. 10 tests, including metadata evolution; 24 library tests pass in all.
- `pdt check` rejects reserved names (`__code`, `_row`).
- **Cross-language:** both slices read identically in pandas, Polars, DuckDB, R arrow and R DuckDB, in a new conda env, `pdt-xlang`.
- **Full-file round trips:** the NSFG female respondent file (1,912 variables) is exact; the GSS and ANES results are in the design doc §9.
- A second-opinion review of `data.py` by an agent is in progress.

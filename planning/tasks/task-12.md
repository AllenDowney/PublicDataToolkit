# Task 12 — Tables: several files in one release

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE` (2026-11-19). Allen decided to add a table level; it's built, and first used for the NSFG

The standard identifies a variable by (release, name). An NSFG release has three files (female respondents, male respondents, pregnancies) that share names such as `MARSTAT`. A portal dataset's coded columns refer to other tables (Chicago crimes `iucr` → the IUCR code list). Both need a table level, which data-dict has (`tables`, `relationships`).

Likely shape: `metadata/releases/<release>/<table>/variables.jsonl`, a `table` field in records and in variable references, and optional relationships between tables. Background: [`planning/next_datasets.md`](../../planning/next_datasets.md) §1 and §3.

**Progress (2026-11-19):** implemented in the standard, the schemas and `pdt check`.
- **`dataset.yaml`:** a release may list `tables`, each with an id, label, sources, `key` columns, and `references` to other tables (foreign keys, possibly in another release or dataset).
- **Layout:** records go in `metadata/releases/<release>/<table>/variables.jsonl`. A release without tables keeps the old layout, so the three existing repos are unchanged.
- **Records** carry `table`. Variable references (group members, links, corrections, annotations, derived properties) may name one, and must when a name is in several tables of the release.
- **`pdt check`** enforces all of this: a record's table matches its directory, there are no ambiguous references, and keys and reference columns have records. Six new tests cover it, with 36 library tests passing.
- **The common format** has one parquet file per table.
- **First real use, the NSFG** (2026-11-19). `pdt-nsfg` now has three tables in release 2022-2023: female respondents (23 variables), male respondents (17) and pregnancies (12).
  - Keys: `CaseID`, and (`CaseID`, `PREGORDR`). The pregnancy → female reference is checked against the data: every pregnancy's `CaseID` is a female respondent, and male and female IDs never overlap.
  - `MARSTAT` and others appear in two tables without conflict. `pdt check` passes.
  - The male and pregnancy files round-trip exactly through the common format.
  - Findings:
    - The cycle 12 data is in `/NCHS/NSFG/` on the CDC FTP site, not `/Datasets/NSFG/`. The earlier `sources.yaml` URL was wrong.
    - The pregnancy data has a column `AGER` with no entry in the pregnancy codebook.
    - The male codebook carries NCHS's own correction in a margin box ("Corrected universe for MFLASTP"), and the universe field says only "see box to the right". The parser now keeps margin text and records it in the variable's notes, labeled.
    - Some pregnancy names are lowercase in the data (`agepreg`) but uppercase in the codebook.

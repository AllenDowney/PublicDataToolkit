# Task 33 — An open-portal dataset

**Status:** `DONE (orange)`, 2026-11-19.

The plan calls an open-data portal the best test of the standard beyond surveys (plan §6, §9). A portal table has no questions and no waves, and it changes every day.

**Steps** (from the coordinator):
1. The dataset: Chicago's "Crimes - 2001 to Present" (Socrata `ijzp-q8t2`), unless a Chicago or Illinois dataset is a better test. The IUCR codes are a separate code list (`c7ck-438e`).
2. Metadata from Socrata's API (`/api/views/<id>.json`): columns, descriptions, types, update history. Terms from the portal's terms of use; data stays `unknown` until Allen decides, and the build is local only.
3. `~/pdt-chicago-crimes` from the Copier template (`v0.1.0`), with no remote.
4. A record for every column. IUCR and FBI codes from the code list. A release is a dated snapshot of the metadata. Common-format data for 2024 only. `pdt check` with 0 failures.
5. `skills/from-open-data-portal/SKILL.md`, and the list in `skills/README.md`.
6. Here: what the standard handles badly for non-survey data, with proposals. No changes to STANDARD.md or `schema/`.

**Files:** `~/pdt-chicago-crimes/`; `skills/from-open-data-portal/` and `skills/README.md`; this file and Task 33's block on the board.

## Done (orange, 2026-11-19)

- **The dataset:** Chicago's "Crimes - 2001 to Present" (`ijzp-q8t2`), as proposed. It's a good test: the IUCR codes are their own dataset (`c7ck-438e`, 434 codes, 10 of them retired), and the table's columns and content change over time. `ward` and `community_area` are about 1% filled in 2001 (4,422 and 6,401 of 485,981 rows), and the portal's change notes record two data revisions in 2026. I didn't look further for a better Illinois dataset.
- **The repo:** `~/pdt-chicago-crimes`, generated with `copier copy --vcs-ref v0.1.0`, with no remote. First commit `7c18de2`.
- **A release is a dated snapshot.** The portal has no versions, only "rows updated" and "metadata updated" timestamps. On one date the build fetches:
  - the Socrata metadata of both datasets;
  - the code list's rows;
  - one SODA aggregate query, each column's non-null count by year;
  - the 2024 rows, ordered by `id`;
  - the two change notes and the terms page.

  Each has a checksum in `sources.yaml`, under `data/raw/20261119/`. The release id is the date.
- **The records:** 27 in two tables. `crimes` has 22, one per public column; `iucr` has 5, for the code list's columns.
  - **Label and description:** Socrata's display name and description, verbatim.
  - **Storage type:** by rule `socrata_storage_type`.
  - **Availability:** each column's count by year, from the portal itself.
  - **`crimes/iucr` values:** all 434 codes, by rule `iucr_code_list_label`.
  - **Key and reference:** `crimes` has key `id` (`case_number` repeats: homicides have one row per victim), and `crimes.iucr` refers to the `iucr` table.
- **The data:** `make data` writes the 2024 rows (259,696, the portal's own count for 2024) and the code list in the common format. Both round-trip exactly, and `pdt.release` marks them local only.
- **`pdt check`: 0 failures.** C3, C4 and C12 pass: all 341 IUCR codes used in 2024 are on the list. There are 21 C5 warnings, one per `crimes` column (proposal 1), and C9 reports the tracked metadata, because the terms are `unknown` and there's no remote.
- **The skill:** [`skills/from-open-data-portal/SKILL.md`](../../skills/from-open-data-portal/SKILL.md), and [`skills/README.md`](../../skills/README.md)'s table.
- **Terms:** quoted in `dataset.yaml`, all `unknown`, for Allen to decide.
  - The City's Terms of Use allow derivative applications if they carry the City's disclaimer, and include an indemnity.
  - The dataset's description adds that the data "should not be used for comparison purposes over time", and forbids deriving specific addresses.
  - Nothing covers LLM processing.
  - `pdt download` refuses to run without `--accept-terms`. I passed it, on the coordinator's instruction to build locally, before any person had reviewed the terms.

## What the standard handles badly here, with proposals

No changes have been made to STANDARD.md or `schema/`.

1. **A data file that holds some of the rows.** The records describe 2001–2026, and the data file holds 2024, so C5 warns for every other year on every column: 21 warnings that say nothing. *Proposal:* a table (or the data file's identity) can declare the rows it holds, e.g. `rows: {waves: [2024]}`, or the source's query. C5 compares only those waves, and the views say the data file is a subset.
2. **A moving table.** A dated snapshot fits the release-id rule, but the sources are live API queries, so a second download never matches its checksum, and `pdt download --check` will call that a mismatch. *Proposal:* a source can be marked `live: true` (a query on a changing table). Then `--check` reports "changed since the snapshot; a new snapshot is a new release" instead of a mismatch, and `fetched_on` could take a time, since the table changes daily.
3. **Storage types.** There's no `boolean` (Socrata `checkbox`: `arrest`, `domestic`, `active`) and no geometry (`location`, a point). Those records have no `storage_type`. *Proposal:* add `boolean`, and `geometry` with a `units`/CRS note (the x and y columns are in State Plane Illinois East, NAD 1983; latitude and longitude are WGS84).
4. **Code lists published as data.** A table plus a reference works, and C12 tests it. But the codes are also copied into the column's `values`, with a label built from two of the list's fields, and a value has no place to say a code is retired. *Proposal:* a reference can name the target's label column(s) (`labels: [primary_description, secondary_description]`), so a column's values can point to a code-list table instead of copying it. A value could also carry the waves (or dates) when it's in use, as code histories (§5.4) do across releases.
5. **No questions.** C6 reports "27 of 27 records have no questions", which is noise for non-survey data. FARS had the same. *Proposal:* `dataset.yaml` says what kind of data it is (`survey`, `administrative`, `portal`). C6 reports missing question text only for surveys, and missing `description` for the others.
6. **Change notes between snapshots.** The portal's notes record data revisions (2026-09-08: records with no known location added; 2026-10-01: missing locations, mostly fixed). They predate this snapshot, so they aren't `revisions` *of* it (§2.1), and they don't fit links. *Proposal:* dataset-level `changes` (`date`, `description`, `source`) for the history of a table that has no releases of its own. Or let `revisions` say which releases a change falls between.
7. **Terms that attach conditions.** The City requires its disclaimer on any derivative application. `terms` can say `ship`, but not "ship with this notice". *Proposal:* `terms.notice`, text that must go with anything that ships (README, docs, data release).
8. **Columns the publisher adds.** The portal's `:@computed_region_*` columns are in the metadata but not the data. I left them out and noted it in the build. A dataset-level note may be enough; it needs no change to the standard.

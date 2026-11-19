# Task 33 — An open-portal dataset

**Status:** `DOING (orange)`, from 2026-11-19.

The plan calls an open-data portal the best test of the standard beyond surveys (plan §6, §9). A portal table has no questions and no waves, and it changes every day.

**Steps** (from the coordinator):
1. The dataset: Chicago's "Crimes - 2001 to Present" (Socrata `ijzp-q8t2`), unless a Chicago or Illinois dataset is a better test. The IUCR codes are a separate code list (`c7ck-438e`).
2. Metadata from Socrata's API (`/api/views/<id>.json`): columns, descriptions, types, update history. Terms from the portal's terms of use; data stays `unknown` until Allen decides, and the build is local only.
3. `~/pdt-chicago-crimes` from the Copier template (`v0.1.0`), with no remote.
4. A record for every column. IUCR and FBI codes from the code list. A release is a dated snapshot of the metadata. Common-format data for 2024 only. `pdt check` with 0 failures.
5. `skills/from-open-data-portal/SKILL.md`, and the list in `skills/README.md`.
6. Here: what the standard handles badly for non-survey data, with proposals. No changes to STANDARD.md or `schema/`.

**Files:** `~/pdt-chicago-crimes/`; `skills/from-open-data-portal/` and `skills/README.md`; this file and Task 33's block on the board.

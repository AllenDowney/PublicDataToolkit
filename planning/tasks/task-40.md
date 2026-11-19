# Task 40 — `pdt diff` pairs by links first

**Status:** `DONE (red)` (see the update below)

From purple's YRBSS (Task 29): each YRBSS release renumbers its variables, so 2021's q26 "Considered suicide" is 2023's q27, and 2023's q26 is "Sad or hopeless". `pdt diff` pairs by name, so it reports a wording change for q26 and a bogus rename.

Make `pdt diff` pair by the links between the two releases first, and by name only for the variables no link pairs. Flag names that match across the releases when the links say they're different variables. Test on `~/pdt-yrbss`.

**Files:** `lib/pdt/diff.py`, its tests, the `release-diff` skill, this file.

**Status update:** `DONE (red)`, 2026-11-19; committed locally, not pushed.

## What changed in `pdt diff`

- **Links first.** `linked_pairs()` pairs variables by the links between the two releases (either direction, same table). Only one-to-one relations pair: `same_item`, `renamed`, and the `*_changed` and `data_revised` relations; `derived_from`, `split_from` and `merged_into` don't. Names pair only the variables no link pairs. Each pair records `paired_by` (`link` or `name`); a linked pair has `link_relations` and `link_agrees`. For that comparison, `renamed` and `data_revised` are dropped (records can't show them), and so is `same_item` when other relations accompany it.
- **Name conflicts.** A name present in both releases whose links pair it elsewhere is listed, with what each side is linked to.
- **`valid_range`** (from yellow's CPS FPOVCUT, added to this task):
  - a documented range that changed (min or max), or any change in top or bottom coding, is `codes_changed`;
  - a range read from each release's data (origin `data_file`) is reported as `observed` without a relation: FARS MOD_YEAR 1927–2018 vs 1929–2025;
  - identifiers aren't compared;
  - when only one release states a range, it's a change only if the other's valid codes fall outside it.
- **New standard fields** (cdae64a): a change in `questions[].number` is `reference_only`; a change in `implied_decimals` is `codes_changed`; `flag_for` changes and the releases' `reference_period` are reported.

## On real pairs

| Pair | Paired by link | Agree | Notes |
|---|---|---|---|
| YRBSS sadc-2021 → sadc-2023 | 28 | 27 | 7 name conflicts (q26, q27, q28, q41, q42, q85, qn26); only q78 and q80 unpaired. By name alone, q26–q28 read as wording changes ("Considered suicide" → "Sad or hopeless"), with 7 bogus rename candidates and 11 unpaired names on each side. The one disagreement: `sex`'s label differs only in case (`text_only`), but the link says `labels_changed`. |
| CPS ASEC 2021 → 2022 | 41 | 41 | FPOVCUT `codes_changed` (documented range 60000 → 99999) |
| FARS 2017 → 2024 | 40 | 40 | ST_CASE, YEAR, MOD_YEAR ranges move: observed or identifier, not changes |
| NSFG 2017-2019 → 2022-2023 | 18 | 11 | the other 7 are the publisher's and hand links (Task 37) |
| GSS 7224r3 → 7224r3a | 6,941 | 6,924 | the rest are NORC's `data_revised` links that the diff sees as `codes_changed` |

## For other threads

- **purple (YRBSS):** the `sex` link (2021 → 2023) says `labels_changed` for a label that differs only in case. `pdt.compare` calls that `text_only`, not a change. The link rule could use `compare_text`.

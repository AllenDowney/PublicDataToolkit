# Task 50 — An NHIS slice

**Status:** `DOING (yellow)` — started 2026-11-19 by the thread "yellow".

The National Health Interview Survey (NCHS) is on Twenge's list (planning/twenge_catalog.md): adults 18+, 1997–2021 in her table. The task:

1. **Sources** on cdc.gov/nchs/nhis: the public-use data files on both sides of the 2019 redesign (e.g. 2016–2018 and 2019–2024), codebooks and summary descriptions, questionnaires, and variance-estimation documents. Record the terms: NCHS data are federal, and its data use agreement restricts re-identification, not sharing. Note what needs Allen's decision; until then terms are `unknown` and the build is local.
2. **`~/pdt-nhis`** from the template (v0.1.0), no remote. Hand facts are authored "Claude (PublicDataToolkit Task 50)".
3. **About 25 variables:** design (the sample adult weight, strata, PSU, year), demographics (sex, age, race/ethnicity, education, income), and outcomes (self-rated health, K6 or PHQ/GAD from 2019, sleep, loneliness or social support if present, smoking, drinking, BMI). Use `design`, `flag_for`, question `number`, and code lists where a long list is shared.
4. **The 2019 redesign:** link across it only where NCHS says the item is comparable; otherwise `wording_changed`, `universe_changed` or no link, citing NCHS's crosswalk or comparability notes. Run `pdt diff` on each pair of years as a cross-check.
5. `make data` round trip, `pdt check` 0 failures; then what NHIS tests that the others didn't, and proposals (not edits to STANDARD.md or schema/).

**Files:** `~/pdt-nhis/` (new, no remote); this file; the Task 50 block on the board.

## Progress

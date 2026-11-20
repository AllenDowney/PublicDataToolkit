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

### Stopped here (2026-11-19)

**Done.** These are committed in `~/pdt-nhis` (fadb9bb, no remote):
- The data and documents for 2016–2024 are downloaded to `data/raw/` (not committed).
- `build/nhis_docs.py` parses both kinds of documentation: the pre-2019 layout PDFs and the 2019+ codebooks, including the 2023–2024 codebook layout.
- `build/slice.yaml` lists about 25 variables on each side of the redesign. It has an imputation flag (IMPINCFLG_A) and three links across 2019 that NCHS's redesign evaluation states item by item: SMKSTAT2→SMKCIGST_A, DEP_1→DEPFREQ_A and ANX_1→ANXFREQ_A. Everything else is unlinked across 2019.
- `build/build_records.py` gives 231 records and 169 links. The rule finds these changes within eras:
  - HISPALLP_A 2020→2021: labels_changed ("NH" → "Non-Hispanic");
  - POVRATTC_A 2019→2020: codes_changed (top code 10 → 11);
  - SUPPORT_A 2021→2024: labels_changed.
  The comparison ignores the "* " markers in 2024's question text.

**Uncommitted.** The generated `metadata/` and `build/report.md` are not committed, because `pdt check` hasn't run on them.

**Next:**
1. Write `dataset.yaml`:
   - tables samadult, person and family before 2019, and adult from 2019; keys HHX/FMX/FPX and references;
   - design: WTFA_SA or WTFA_A with PSTRAT and PPSU;
   - terms `unknown`, quoting the NCHS Data User Agreement.
2. Write `sources.yaml` with sha256 for each file.
3. Write `scripts/build_data.py`.
4. Run `make data`, `make views` and `make check` to 0 failures.
5. Run `pdt diff` on each pair of years.
6. Update the README, and add the findings and proposals here.

**Allen to decide:** the NHIS terms. The NCHS DUA forbids re-identification and says nothing about redistribution.

# Task 50 — An NHIS slice

**Status:** `DONE (yellow)` on 2026-11-20, except the terms, which are pending Allen's decision. Started 2026-11-19 by the thread "yellow".

The National Health Interview Survey (NCHS) is on Twenge's list (planning/twenge_catalog.md): adults 18+, 1997–2021 in her table. The task:

1. **Sources** on cdc.gov/nchs/nhis: the public-use data files on both sides of the 2019 redesign (e.g. 2016–2018 and 2019–2024), codebooks and summary descriptions, questionnaires, and variance-estimation documents. Record the terms: NCHS data are federal, and its data use agreement restricts re-identification, not sharing. Note what needs Allen's decision; until then terms are `unknown` and the build is local.
2. **`~/pdt-nhis`** from the template (v0.1.0), no remote. Hand facts are authored "Claude (PublicDataToolkit Task 50)".
3. **About 25 variables:** design (the sample adult weight, strata, PSU, year), demographics (sex, age, race/ethnicity, education, income), and outcomes (self-rated health, K6 or PHQ/GAD from 2019, sleep, loneliness or social support if present, smoking, drinking, BMI). Use `design`, `flag_for`, question `number`, and code lists where a long list is shared.
4. **The 2019 redesign:** link across it only where NCHS says the item is comparable; otherwise `wording_changed`, `universe_changed` or no link, citing NCHS's crosswalk or comparability notes. Run `pdt diff` on each pair of years as a cross-check.
5. `make data` round trip, `pdt check` 0 failures; then what NHIS tests that the others didn't, and proposals (not edits to STANDARD.md or schema/).

**Files:** `~/pdt-nhis/` (new, no remote); this file; the Task 50 block on the board.

## Terms: pending Allen's decision

`dataset.yaml` quotes the NCHS Data User Agreement (https://www.cdc.gov/nchs/policy/data-user-agreement.html, dated September 17, 2024), and every terms field is `unknown`. Nothing is shipped or packaged. The data in `data/processed/` is local and untracked.

**Summary for Allen.** The NHIS public-use files are on ftp.cdc.gov with no registration. The only terms are the NCHS Data User Agreement. It says the data "may be used only for statistical reporting and analysis", and users agree to:
- make no attempt to learn anyone's identity;
- not link the data with individually identifiable data;
- not research disclosure methods or re-identification.

"By using these data you signify your agreement." It says nothing about redistribution, so it's the same situation as the NSFG, which uses the same agreement. The decision has four parts:
1. whether the metadata and the NCHS documentation ship;
2. whether the common-format data (parquet of about 25 variables per year) ships, which would need a notice that carries the agreement's restrictions to users;
3. whether LLM processing is allowed;
4. the notice text.

## What was done

`~/pdt-nhis` (commits 36f735e template, fadb9bb build, 5b5813b slice; no remote):

| Item | Detail |
|---|---|
| Releases | 2016–2018 (tables `samadult`, `person`, `family`); 2019–2024 (table `adult`) |
| Records | 231, from about 25 variables a year; content rotates after 2019 |
| Links | 170: 4 stated by NCHS, 166 from the rule `nhis_identical_documentation` within an era |
| Sources | 40 in `sources.yaml`, with sha256: data zips, layout PDFs or codebooks, survey descriptions, the redesign evaluation |
| Design | `samadult`: WTFA_SA, PSTRAT, PPSU; `adult`: WTFA_A, PSTRAT, PPSU; notes from each year's Survey Description |
| Flag | IMPINCFLG_A `flag_for` the income variables built from INCTOTAL_A (rule `nhis_flag_from_sources`) |
| `make data` | 15 parquet files, round trip exact |
| `pdt check` | 0 failures, C3–C5 and C12 included |

**Links stated by NCHS** (`origin: publisher`, with quotes):

| From | To | Relations | NCHS source |
|---|---|---|---|
| SMKSTAT2 2018 | SMKCIGST_A 2019 | renamed | redesign evaluation, p. 24: "The two questions used for this indicator were unchanged from 2018 to 2019." |
| DEP_1 2018 | DEPFREQ_A 2019 | renamed | evaluation, p. 20: question text unchanged, "the context surrounding these questions changed" |
| ANX_1 2018 | ANXFREQ_A 2019 | renamed | evaluation, p. 18: same wording as for depression |
| EDUC_A 2020 | EDUCP_A 2021 | renamed, codes_changed, labels_changed | 2021 Survey Description, p. 103: EDUCP_A is "top-coded to combine professional school degree ... with doctoral degree" |

Every other variable is unlinked across 2019. That includes K6 (ASISAD… in 2016–2018, SAD_A… in 2021 and 2024), self-rated health, sex, age, race, BMI and drinking. The evaluation doesn't assess them item by item, and the files, universes and code lists changed. An analyst who wants to bridge them needs NCHS's statement first, or a hand link from someone who has compared the questionnaires.

**Changes found within an era:**
- POVRATTC_A 2019→2020: codes_changed, because the top code moved from 10 to 11.
- HISPALLP_A 2020→2021: labels_changed ("NH" → "Non-Hispanic").
- SUPPORT_A 2021→2024: labels_changed. The question number also moved from SOS.0010.00.4 to SSL.0010.00.3, a new section.

**`pdt diff` cross-check:**
- I ran it on each consecutive pair and on the gap pairs that rotation creates (2019/2022, 2020/2022, 2021/2024).
- It agrees with the links except for one thing, described below. It suggested EDUC_A → EDUCP_A as a rename (similarity 0.906), which led me to NCHS's statement.
- It doesn't show the three links across 2019, because those join different tables (`samadult` → `adult`), and diff pairs table by table.

**One disagreement with `pdt diff`:** HOPELESS_A, EFFORT_A and WORTHLESS_A 2021→2024. From 2022 the codebook prints "* " before interviewer instructions ("* Read if necessary: ..."), and does so unevenly across years and items. My rule ignores the marker and says same_item. `pdt.compare` calls the text changed, so diff reports wording_changed. I believe the marker isn't wording, but no NCHS document says what it means.

## What NHIS tests that the other datasets didn't

1. **A redesign that changes files, names and tables at once.**
   - 2018→2019 isn't a renamed variable within a table. Three files become one, every name gains `_A`, and the table ids differ.
   - Links across tables work in `links.jsonl`, but `pdt diff` compares table by table and doesn't see them.
2. **Rotating content.**
   - Variables skip years: PHQ/GAD in 2019 and 2022, K6 in 2021 and 2024, sleep and drinking in 2020, 2022 and 2024, loneliness in 2024 only.
   - Consecutive-year diffs miss the changes across those gaps. Links go from each year a variable appears to the next year it appears.
3. **The documentation format changes by era and within one.** Pre-2019 layout PDFs and post-2019 codebooks need two parsers, and the 2023 codebook dropped the indentation the 2019–2022 parser relied on.
4. **Comparability is stated per indicator, not per variable.** The redesign evaluation discusses estimates ("Current Cigarette Smoking"), and a link needs a judgment that the indicator's variable is the one meant.
5. **Missing codes mixed with "Unknown".** NCHS codes 7/8/9 (Refused, Not ascertained, Don't know). Some recodes have one "Unknown" code that combines them, and the rule maps it to `unknown`.
6. **Implied decimals stated only in a label.** For BMI before 2019, the code range 0001-9994 is labeled "00.01-99.94". The rule sets `implied_decimals` from the label.
7. **Text identifiers.** HHX is numeric before 2019 and text ("H048109") after.
8. **Imputation in separate files.** From 2019, family income is multiply imputed in a separate file, `adultincYYcsv.zip`, and the main file carries only the flag. This slice uses POVRATTC_A and RATCAT_A, which are on the main file, and doesn't use the imputed files.

## Proposals (not edits to STANDARD.md or schema/)

1. **`pdt diff` across tables.**
   - Let diff follow links whose ends are in different tables, or take `--table-map samadult=adult`.
   - It would then show the redesign links next to the unlinked variables.
2. **Diff over gaps.**
   - With `--follow-links`, compare each variable with the next release it appears in, not only the next release.
   - Rotating surveys (NHIS, BRFSS modules) would then be covered by one run.
3. **A normalization hook in `pdt.compare`.**
   - Let a dataset repo declare formatting markers to ignore, such as NHIS's leading "* ".
   - Rule links and `pdt diff` would then agree.
   - Until then, the two disagree on three NHIS variables.
4. **A relation for "same questions, different context".**
   - NCHS says DEP_1 and ANX_1 kept their wording but moved in the interview, and suspects an effect on the worry estimate.
   - `renamed` plus a note records it now. A relation like `context_changed` would let a reader filter for it.
5. **Links from indicator-level statements.**
   - STANDARD.md could say how to cite a publisher's statement about an estimate when making a variable-level link.
   - It could also say when that's enough.

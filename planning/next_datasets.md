# Preliminary work on MTF, NSFG and an open-portal dataset

**Status:** 2026-11-19, done while Allen was away. Allen's answers to the questions are in §6.

## 1. NSFG: a slice, built

A new local repo, `pdt-nsfg`, not pushed, with 23 variables from the 2022–2023 (cycle 12) female respondent file:
- design variables;
- marital status;
- religion;
- marijuana use;
- same-sex partners.

`build/build_slice.py` parses the CDC codebook (already converted to text by MarriageNSFG), and checks it against the SAS data file. `pdt check` passes.

**Terms:** everything `ship`, taken from Allen's own review in MarriageNSFG Task 20 (2026-11-10):
- the NCHS Data User Agreement restricts use and re-identification, not sharing;
- NCHS documentation is a US government work, in the public domain.

`dataset.yaml` says the terms were recorded from that review and need Allen's confirmation for this repo.

**What the NSFG tests that the GSS and ANES didn't:**
- **No question text.** Every one of the 23 records lacks `questions`. The codebook gives only a label that starts with the questionnaire item ("AD-7b R's marital or cohabiting status"). The item reference is kept as the extension `nsfg.item`. Question text would have to come from the questionnaire (CAPI instrument) documents.
- **The publisher doesn't mark missing codes.** "Refused 8", "Don't know 9" and "Inapplicable ." are ordinary rows of the distribution table. The build types them with a recorded rule over the labels (`nsfg_missing_from_labels`), which is the standard's third choice (§4.2). This is the first dataset where that path is the main one.
- **Coverage is complete:** all 1,912 columns of the data file have codebook entries.
- **Variable types.** NCHS labels each variable `raw`, `recode`, `computed`, `imputation flag` or `weight-related`. That distinction is likely to matter for other publishers too, so the extension `nsfg.variable_type` is a candidate for the standard.
- **PDF artifacts.** After a page break the text repeats the section and the variable's name as a header. The first parse lost `SSMARCOH`'s label to it until the parser ignored the repeat. The codebook also rounds ranges (the weight is "1170.96–78770.13"), so range checks have to allow for rounding.
- **Name case.** The data file uses `CaseID`; the codebook writes `CASEID`. Names are stored as the data file spells them.

**A gap in the standard, found here and in the portal case (§3):** an NSFG release has several files: female respondents, male respondents and pregnancies. The same name (`MARSTAT`) appears in more than one, but the standard identifies a variable by (release, name) only. It needs a level for the file or table, as data-dict has. The slice avoids the problem by covering only the female respondent file. **Question 1 in §5.**

**The common data format, on a third publisher format:** the whole female respondent file (1,912 variables, 5,586 rows) round-trips exactly through the parquet format. The parquet file is 5.3 MB, against 86.4 MB for the SAS file. In this file 60.5% of cells are codes, almost all "inapplicable", which makes the case for code columns stronger still.

## 2. MTF: research only

A research agent looked up the sources. ICPSR and monitoringthefuture.org both return 403 to automated requests, so most facts below come from search snippets and **need checking by a person**.

- **Studies:** the 2024 12th-grade file is ICPSR study 39444 (released 2025-10-30); 2023 is 39172, 2015 is 36408, 2005 is 4536. A restricted-use version (39446) has geography.
- **Structure:** six questionnaire forms with a shared core. DS1 is the core file across all forms; DS2–DS7 are forms 1–6. V-numbers are MTF's item reference numbers: V1 is year, V3 is form.
- **Crosswalk:** a "cross-time question index" ships with each year's User Guide, sorted by subject, item reference number and form, from 1976 on. That is the publisher-asserted continuity the standard's `links.jsonl` is for.
- **Metadata export:** study pages have had DDI 2.5 export, but ICPSR has retired its OAI-PMH and DDI XML services in favor of a Metadata Export API. Whether either includes variable-level detail is unverified.
- **Terms:**
  - ICPSR forbids redistributing "data or other materials we supply" without written permission, so data and documentation are `build-only`.
  - ICPSR's study-level metadata is CC BY-NC, but variable-level metadata derived from codebooks isn't clearly covered.
  - **ICPSR's LLM policy** forbids LLMs that "retain user-provided data", and asks to be contacted before any other LLM use. It's unclear whether codebook text counts as "data". **Until that's settled, Claude shouldn't read MTF codebooks**, and an agent-built MTF repo may not be possible without ICPSR's permission. **Question 3 in §5.**

So MTF tests the standard where it's weakest: build-only terms, a login, and possibly no LLM processing. The instructions have to work when the agent can't read the documentation itself.

## 3. An open-portal dataset: a first look

The Chicago data portal's "Crimes – 2001 to Present" dataset (Socrata id `ijzp-q8t2`) publishes its metadata through a public API, with no login: https://data.cityofchicago.org/api/views/ijzp-q8t2.json

- 22 data columns, each with a name, a type and a plain-language description. They map directly onto variable records: no questions, no value labels, and nulls as the only missing values.
- Coded columns point to **other tables**: `iucr` refers to the city's IUCR code list, and `beat`, `district`, `ward` and `community_area` refer to boundary datasets. The standard has no way to say "these codes are defined in that table". data-dict's `relationships` does. This is the same gap as NSFG's several files.
- **Releases** are daily: rows are updated every day, and the metadata rarely changes. A release per snapshot doesn't fit a GitHub release per release. Options: metadata releases only when the metadata changes, and data fetched live with a recorded snapshot date.
- **Terms:** the API's license field says only "See Terms of Use", pointing to the city portal's terms. Not yet read.

## 4. The common data format: tests the review asked for

Results are recorded in [`missing_codes_design.md`](missing_codes_design.md) §9:
- **cross-language:** the slices read identically in pandas, Polars, DuckDB, R arrow and R DuckDB;
- **metadata evolution:** a library test;
- **full-file round trips:** the NSFG female respondent file is exact; the GSS and ANES results are added to §9 when the run finishes.

## 5. Questions for Allen

1. **Tables.** Should the standard add a table level, so one release can hold several files (NSFG female/male/pregnancy; a portal dataset and its code lists)? The likely shape: `metadata/releases/<release>/<table>/variables.jsonl`, with `table` in each record and in references. This is the biggest open design question from today.
2. **NSFG terms.** Confirm the terms recorded from your MarriageNSFG Task 20 review (everything `ship`).
3. **MTF and LLMs.** ICPSR's LLM policy may forbid sending MTF codebook text to Claude. Read it, and decide whether to ask ICPSR (contact them, or the MTF team) before going further: https://wpvip.icpsr.umich.edu/icpsr/wp-content/uploads/sites/11/2025/06/ICPSR-Policy-on-the-Use-of-Large-Language-Models.pdf
4. **MTF downloads, if you go ahead** (ICPSR login needed; the site blocks scripts):
   - study 39444 (2024 12th grade): https://www.icpsr.umich.edu/web/NAHDAP/studies/39444. The Stata or SAS files for DS1 (core) and two forms, the PDF codebooks, and the User Guide, which has the cross-time question index;
   - one earlier year for V-number changes, e.g. 2015 (36408);
   - the Terms of Use and redistribution policy pages, saved from the browser as you did for ANES.
5. **Portal terms.** Is a city open-data portal still the non-survey case you want? If so, which city or dataset, and should I read Chicago's terms of use?
6. **The topic query.** The ANES has no marijuana item. The candidates for the cross-survey topic query are religion (all three surveys so far), abortion or gay rights (GSS and ANES), or marijuana (GSS and NSFG).

## 6. Allen's answers (2026-11-19)

1. **Tables:** add a table level to the standard (Task 12).
2. **NSFG terms:** confirmed as recorded (everything `ship`).
3. **MTF:** ask ICPSR first. Claude drafts the email and Allen sends it; MTF waits for the answer. The draft is kept outside this repo.
4. **Non-survey case:** the [Fatality Analysis Reporting System](https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars) (FARS, NHTSA) instead of a city portal.
   - It has several tables per year (crash, vehicle, person and others), so it tests the table level.
   - Its codes change across years, and it is a federal dataset.
   - www.nhtsa.gov returns 403 to automated requests, so **Allen needs to download**: the FARS Analytical User's Manual (PDF); one recent year's national data (CSV); and NHTSA's terms or data-use statement, saved from the browser.
5. **Topic query:** religion, which is in all three surveys. Religion items to be added to the GSS and ANES slices.

## 7. Later the same day

- **NSFG tables:** done; see the board, Task 12.
- **Full-file round trips:** done for the GSS (6,943 variables), the ANES (1,030) and the NSFG (all three files). All exact. Results are in [`missing_codes_design.md`](missing_codes_design.md) §9. The GSS data file has 6,943 variables, but gssrdoc documents 6,904, so 39 are missing from gssrdoc.
- **Religion:** added to the GSS and ANES slices for the topic query. The ANES missing-type rule went to version 0.2, to type "form B", "short form" and similar questionnaire versions as `not_asked`.
- **FARS:** Allen downloaded the 2024 national data (CSV and SAS, with the auxiliary files), the Analytical User's Manual (1975–2024), and NHTSA's Q&A on the auxiliary files (DOT HS 811 364). They're in `../pdt-fars/data/raw/`. nhtsa.gov and icpsr.umich.edu block headless browsers too.
- **ICPSR contact:** icpsr-help@umich.edu, with a copy to mtfinformation@umich.edu, both from search results and added to the email draft.

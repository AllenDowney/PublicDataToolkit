# Task 62 — An NCVS slice, metadata only

**Status:** `DOING (blue)`, claimed 2026-11-20. Metadata from the codebooks (pdt-ncvs 6c94a4a), checked against the Stata files (1ce52e4). Local only, unpublished.

The National Crime Victimization Survey (Bureau of Justice Statistics, distributed by ICPSR's National Archive of Criminal Justice Data) in `~/pdt-ncvs`: household, person and incident tables for a few years.

ICPSR doesn't allow redistribution, so this is the metadata-only path:
- no data ships;
- `scripts/download.py` fetches the files only with `--accept-terms`, or prints the manual steps;
- C3–C5 run only locally.

Stop at any login or bot check, and tell the coordinator what ICPSR requires. The terms are recorded for Allen. Memory cap.

**Files:** `~/pdt-ncvs/`, this file and the Task 62 block on the board.

## Blocked at ICPSR's bot check (2026-11-20)

- **ICPSR/NACJD** (`https://www.icpsr.umich.edu/web/NACJD/series/95`, and the ICPSR series page) returns 403 with a Cloudflare "Performing security verification" page, to curl and to a headless browser (Playwright) alike. Per the rules, I stopped at the bot check and didn't try to get around it. So I couldn't read the study list, the file names, the codebooks or ICPSR's terms of use.
  - From general knowledge, not verified today: ICPSR data downloads need a free MyData login and acceptance of its terms of use at download. NACJD data can't be redistributed. The documentation (codebooks, user guides) is usually downloadable without a login, but here it's behind the same bot check.
- **BJS** (`bjs.ojp.gov/data-collection/ncvs`) answers scripts. It hosts the questionnaires for each year (`/document/ncvs24_bsq.pdf` and `ncvs24_cir.pdf`, for the basic screen questionnaire and the crime incident report, back to 2015 and earlier) and the 2025 redesign questionnaire. It hosts no data files or codebooks: those are at ICPSR.
- **NCVS Select** (BJS's public subset files on `data.ojp.gov`): the host doesn't resolve, so that alternative path isn't available.

**What Allen would need to do:** in a browser, logged in to ICPSR:
1. Pick the studies and years.
2. Download each study's codebook (PDF) and data (Stata or SPSS) for the household, person and incident files.
3. Save the study page and ICPSR's terms-of-use page.
4. Put the files in `~/pdt-ncvs/data/raw/`.

Then `sources.yaml` records them with `acquisition: manual`, and `scripts/download.py --check` verifies the hashes. Nothing ships.

**Not started:** the repo. `~/pdt-ncvs` doesn't exist yet. It can start from the template while the files are fetched, with the BJS questionnaires as automated sources.

## Built from the codebooks (2026-11-20)

Allen downloaded ICPSR 38603 (NCVS 2022, version 1), documentation only, and copied the terms' key passages. Both are in `~/pdt-ncvs/data/raw/` as manual sources with hashes. pdt-ncvs commit 6c94a4a; `pdt check` passes with 0 failures.

**Terms (Allen, 2026-11-20):** data `build-only`, documentation `build-only`, metadata `unknown` (unpublished until ICPSR agrees in writing), llm_processing `allowed`. The ICPSR passages are quoted in `dataset.yaml`. The README and the repo's CLAUDE.md say not to publish or push.

**Tables and keys**, from the user guide ("NCVS ID variables are unique only within each six-month interview period"):

| Table | Records | Key | References |
|---|---|---|---|
| address | 10 | YEARQ, IDHH | |
| household | 448 | YEARQ, IDHH | address on YEARQ, IDHH |
| person | 427 | YEARQ, IDPER | household on YEARQ, IDHH |
| incident | 1261 | YEARQ, IDPER, V4011, V4012 | person on YEARQ, IDPER |

The incident key is read from the codebook: V4011 is the screen question that prompted the report and V4012 "indicates which of these incidents is being discussed" when one screen question has several. It hasn't been checked against the data. The extract file (DS0005) is left out: ICPSR builds it from the four files.

**What the parser takes from each codebook entry** (`build/build_records.py`, codebook text from `pdftotext -layout`): label, question text and number, BJS's "Source code" (extension `ncvs.source_code`, listed in EXTENSIONS.md), notes, labeled codes with frequencies, the valid range, storage type and the count of valid cases (availability). Entry counts match ICPSR's manifest for all four files.

**Missing codes:** the codebook marks them itself (a "Missing Data" section in each value table, and "(Range of) Missing Values"). Rule `ncvs_missing_types` types them by label: Out of universe → inap, Blank → no_answer, Residue → uncodeable, Don't know → dk, Refused → refused; a declared code with no row → unspecified. One code stays unresolved: household V2031 99 "Intv, typeB, typeC".

**Gaps:**
- 8 variables list only their first 50 categories in the PDF (in `build/report.md`).
- 1059 of 2146 records have no question text (IDs, weights, derived and admin variables).
- C3–C5 need the Stata files; when they arrive, add `read_data()` as in pdt-nhanes. 2023 (ICPSR 38962) would be a second release.

## Checked against the data (2026-11-20)

Allen downloaded the Stata version, about 795 MB. It's in `data/raw/ICPSR_38603-V1-stata.zip`, recorded as a manual, build-only source with its sha256. The zip also holds ICPSR's full TermsOfUse.html.

`build/check_data.py` (`make check-data`) reads the files in row chunks of 25,000 and reads only the key columns for the key checks. It ran under the 6 GB cap and writes `build/data_report.md`. pdt-ncvs commit 1ce52e4; `pdt check` passes with 0 failures.

| Table | Rows | Columns |
|---|---|---|
| address | 257,272 | 10 |
| household | 257,272 | 448 |
| person | 277,892 | 427 |
| incident | 9,545 | 1,261 |

- **C3:** the data's columns match the records exactly in all four files.
- **C4:** clean. No value is outside the listed codes and the codebook's range. Two false alarms came from the check, not the data, and are fixed in it: YEARQ is a Stata float, so 2022.1 reads as 2022.0999755859375 and is now rounded to float precision; and identifiers have no codes or range to check.
- **C5:** every codebook count matches the data, for every listed code and every count of valid cases.
- **Keys and references:**
  - All four keys are unique and have no blanks, and every reference finds its row.
  - The incident key `[YEARQ, IDPER, V4011, V4012]` is minimal. Without V4011 there are 834 duplicate rows, and without V4012 there are 1,178.
- **Missing codes:** ICPSR's supplemental .do files recode the same codes the records mark missing, in all 809 variables, with one exception: V4400.

**V4400, corrected (inferred):**
- The codebook doesn't mark code 99 "Out of universe" (6,303 cases) missing, although it marks every other "Out of universe" code missing.
- The .do file recodes 9 instead, which doesn't occur. It is probably left over from the 2017 collapse of categories the codebook notes.
- `metadata/corrections.jsonl` makes 99 missing (inap), with confidence `inferred` and upstream `not_filed`. Reporting it to ICPSR is Allen's call.

**What ICPSR counts as missing:** only "Out of universe" and blank codes. "Residue" (8/98, 692 codes), "Don't know" (95) and "Refused" (19) are listed as valid. The records follow the codebook; a user who wants them treated as missing has to recode them.

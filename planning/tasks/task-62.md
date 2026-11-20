# Task 62 — An NCVS slice, metadata only

**Status:** `DOING (blue)`, claimed 2026-11-20. Metadata from the codebooks done (pdt-ncvs 6c94a4a); waiting for the data files for C3–C5.

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

# Task 62 — An NCVS slice, metadata only

**Status:** `DOING (blue)`, claimed 2026-11-20.

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

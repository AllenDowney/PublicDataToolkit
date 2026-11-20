# Task 65 — An NLSY slice

**Status:** `DONE (yellow)` on 2026-11-20; terms pending Allen. Started 2026-11-20 by the thread "yellow".

The National Longitudinal Surveys of Youth 1979 or 1997 (BLS) in `~/pdt-nlsy`: a small panel extract, the first test of a panel's rounds as waves. Data come through BLS's Investigator tool, so the sources are probably manual. Record the terms for Allen. Memory cap applies. The coordinator: stop at any login and say what it needs.

**Files:** `~/pdt-nlsy97/` (new, no remote; named for its id, nlsy97); this file; the Task 65 block on the board.

## Progress

### 2026-11-20: access, without a login

- **Cohort:** NLSY97 (born 1980–84; rounds 1–21, 1997–2023).
- **The NLS Investigator** (https://www.nlsinfo.org/investigator/) doesn't need a login: "It is not necessary to get an account to browse data, but an account is necessary to save datasets online" (https://www.nlsinfo.org/content/getting-started/accessing-data).
  - But its pages and scripts return 403 to anything that isn't a browser session.
  - Its System Use Notification (https://www.nlsinfo.org/system-use-notification) says "Any attempt to exceed these limitations or gain additional functionality is prohibited" and cites the Computer Fraud and Abuse Act.
  - So I didn't script it. Its "Downloads" page only lists extracts a user has built.
- **Whole-cohort downloads** are published as direct links on https://www.nlsinfo.org/content/access-data-investigator/accessing-data-cohorts, for "users who have the capacity to utilize extremely large data files". Each zip has the data (.dat and .csv), a codebook (.cdb), SAS and R read programs, and a tagset of reference numbers.
  - NLSY97: https://nlsinfo.org/cohort-data/nlsy97_all_1997-2023.zip (475 MB, updated 2026-01-23 per Last-Modified);
  - NLSY79: nlsy79_all_1979-2022.zip (450 MB).
  - curl fetches them with no login. This slice uses the NLSY97 file, read in batches under the memory cap.
- **Terms, for Allen:**
  - NLS public data are free. The citation page (https://www.nlsinfo.org/bibliography/citing-nls-data) gives "Bureau of Labor Statistics, U.S. Department of Labor. National Longitudinal Survey of Youth 1997 cohort, 1997-2023 (rounds 1-21). Produced and distributed by the Center for Human Resource Research (CHRR), The Ohio State University. Columbus, OH: …".
  - No redistribution statement found yet. Terms stay `unknown`.
- `~/pdt-nlsy97` was created from the template (7d8196f; first made as ~/pdt-nlsy, renamed to match the id). Release `1997-2023`; the wave is the round.

### 2026-11-20: the slice is built (option B)

`~/pdt-nlsy97` 292be33 and 5f4178f (no remote). Release `1997-2023`; the wave is the survey year (21 rounds). `pdt check` gives 0 failures.

**The design the coordinator approved (B):** one record per question name, `availability` by survey year, and `source_columns` (STANDARD.md, a6e0a8c) giving each year's reference number. The common format is long:

| Table | Rows | Key | Records |
|---|---|---|---|
| `person` | 8,984 | PUBID | 8: PUBID, KEY!SEX, KEY!BDATE_M, KEY!BDATE_Y, KEY!RACE_ETHNICITY, CV_SAMPLE_TYPE, VSTRAT, VPSU |
| `person_year` | 188,664 (8,984 × 21) | PUBID, SURVEY_YEAR | 17: PUBID, SURVEY_YEAR (rule `nlsy_reshape`), SAMPLING_WEIGHT_CC, CV_HGC_EVER_EDT, CV_INCOME_FAMILY, CV_MARSTAT_COLLAPSED, CV_WKSWK_DLI_ALL, YHEA-100, YSAQ-282C–G, YSAQ-359, YSAQ-360C, YSAQ-361, YSAQ-363 |

- **Reading the 8.1 GB CSV:** `scripts/extract_slice.py` copies the slice's 188 columns as text in 1,000-row chunks, with a 0.34 GB peak in about 4–5 minutes. `make data` peaks at 0.54 GB.
- **The reshape is checked both ways** before pdt's own round trip:
  - every publisher cell (181 columns in `person_year`) lands in exactly one (PUBID, year, variable) cell, NLS's negative codes included;
  - every long cell either equals its one publisher cell or, in a year with no column for that question, is empty.

  A non-interview is the code -5 on the row, not a missing row.
- **From the codebook:** labels, wordings with their years, universes, codes and labels, ranges, implied decimals, and NLS's reserved codes -1 to -5, each with its count.
  - The counts are summed over the years, which gives the long table's count.
  - The reserved codes' types come from their labels (rule `nlsy_reserved_codes`): -1 refused, -2 dk, -3 invalid skip → `no_answer`, -4 valid skip → `inap`, -5 non-interview → `not_asked`.
- **Every code in the data is covered.** C5 warns once: YSAQ-363 ("ever drink alcohol?") was in the 2004 file but asked of no one. Its 2004 universe was people who hadn't answered as of the last interview, and all 7,501 were valid skips.
- **Design:** SAMPLING_WEIGHT_CC, each year's weight, is on `person_year`. VSTRAT and VPSU are on `person`, and `design` can't name strata or a PSU in another table, so the note says so.

### The coordinator's question: changes between rounds inside one record

`pdt diff` compares releases, and here there's one release, so it has nothing to compare. Links join records, so a change between rounds of one record can't be a link either. In this slice the changes are recorded inside the record:

| Change between rounds | How it's recorded | Example |
|---|---|---|
| Wording | `questions[]`, each with its `waves` | YSAQ-360C: "since the last interview" (1998–2011), "within the past twelve months" (2013, 2015) |
| Universe | in `notes` ("Universe by year: …"); `universe` takes one text | YSAQ-363: "All" (1997), then only those who hadn't answered as of the last interview |
| Title | `label` is the latest; `notes` lists titles by year | SAMPLING_WEIGHT_CC: "ROUND n SAMPLING WEIGHT …" |
| Code labels | the latest label; `notes` lists differences beyond case | none in this slice ("YES"/"Yes", "Never married"/"Never-married") |
| Codes | `values[].waves` (when a code is in use) | none: every question's code set is the same in every year |

A history (§5.4) would also work for codes, but it's for a publisher's own multi-year matrix, which NLS doesn't publish.

### Proposals (not edits to STANDARD.md or schema/)

1. **Universe by wave.** Let `universe` be a list of `{text, waves}`, like `questions`, or give each `questions[]` entry its own `universe`. NLSY universes change by round, and they carry the "already answered as of the last interview" logic Task 69 is about.
2. **`design.strata` and `design.psu` in another table,** as `replicates.table` now allows. NLSY's VSTRAT and VPSU are per person; the weights are per person-year.
3. **A missing type for unit non-response in a panel round.** -5 Non-interview is typed `not_asked`, which is close: the person wasn't asked anything that round. A distinct `noninterview` type would let a user drop person-years that never happened without dropping valid skips. This bears on Task 69.
4. **`pdt diff` across waves within a release,** for records that span waves: compare a record's per-wave facts (wordings, universes, code counts by year).
5. **Counts by wave.** `values[].n` is one number for the release; the codebook gives counts per year, so this slice sums them. `n_by_wave` would keep them, and C4 could check them against the data by year.

### For Task 69

The slice holds the cases the coordinator listed:
- CV_MARSTAT_COLLAPSED: status as of each interview, all 21 years;
- CV_WKSWK_DLI_ALL: weeks worked since the last interview, 2019–2023 only, under this name;
- YSAQ-359 "ever smoked?": asked in 6 years; after 1997 only of those who hadn't answered it as of the last interview (1998, 1999), or had answered don't know or refused (2000, 2004, 2005);
- YSAQ-360C "smoked since the last interview?": its reference period changes to twelve months in 2013;
- YSAQ-363 "ever drink?": asked of no one in 2004.

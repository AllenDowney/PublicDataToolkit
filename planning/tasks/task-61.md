# Task 61 — An NHANES slice

**Status:** `DOING (blue)`, claimed 2026-11-20.

The National Health and Nutrition Examination Survey (NCHS) in `~/pdt-nhanes`, from the Copier template:
- two or three cycles;
- in each cycle, several files linked on `SEQN` (demographics, a questionnaire, an exam and a lab file), as tables with references (STANDARD.md §2.1);
- every data job under the memory cap.

The terms are the NCHS data use agreement, as for the NSFG and NHIS. They're recorded for Allen to decide.

**Files:** `~/pdt-nhanes/`, this file and the Task 61 block on the board.

## Done (2026-11-20)

`~/pdt-nhanes`: commits `20596fe` (records) and `7dfe25b` (agent/ and export/; docs/ gitignored). `pdt check`: 0 failures.

**What it holds.** Three releases: `2015-2016`, `2017-2020` (NCHS's "2017-March 2020 pre-pandemic" file) and `2021-2023` ("August 2021-August 2023"). Each has four tables, keyed on `SEQN`, and each file is taken whole:

| Table | File | References |
|---|---|---|
| `demo` | Demographics and sample weights | — |
| `dpq` | The PHQ-9 depression screener | `demo` |
| `bmx` | Body measures (examination) | `demo` |
| `ghb` | Glycohemoglobin (laboratory) | `demo` |

That's 213 records in all, plus 25 sources with hashes: 12 HTML codebooks, 12 XPT files, and the NCHS Data User Agreement. `design` is set per release: the interview and examination weights (`WTINTPRP`/`WTMECPRP` for 2017–2020), with `SDMVSTRA` and `SDMVPSU`.

**Findings**
- **Documentation and data match exactly.** Across all 12 files, every column has a codebook entry and every entry has a column (C3). Every code in the data is listed or inside a listed range (C4). Every count in the codebook equals the data's (C5).
- **Keys and references hold**, checked by hand because `pdt check` C12 needs `make data`. `SEQN` is unique in each file, and every `SEQN` in `dpq`, `bmx` and `ghb` is in the same cycle's `demo`.
- **pandas' XPORT reader turns an exact zero into 5.4e-79.** It looked like an undocumented code in 20 variables. pyreadstat's `read_xport` reads it right. Worth a line in `skills/from-data-labels`.
- **The codebook rounds the ends of a range** ("… to 338363.6" for a weight of 338363.600192). The C4 check allows half a unit of the last printed decimal. `valid_range` keeps the printed ends.
- **The codebook marks no code as missing.** Rule `nhanes_missing_from_labels` 0.1 types "Refused" as `refused` and "Don't know" as `dk`.
  - "." labeled "Missing" (201 codes) is `missing` with type `unspecified`: NCHS uses it for skips and nonresponse alike.
  - Nothing is unresolved.
- **The demographics file changed between cycles:** 47 variables in 2015–2016, 29 and 27 later. Only 15 names are in all three.
- **No links are written.** NHANES has no crosswalk like SAMHSA's or NORC's, and the standard allows no inferred links (§3 rule 2). Same-name variables (all of `dpq`, and most of `bmx`) are candidates for `pdt diff` and the `release-diff` skill, for a person to review.

**For Allen: the terms.** It's the NCHS Data User Agreement, the one decided for pdt-nhis and pdt-nsfg, quoted in `dataset.yaml`. All four fields are `unknown`.

**Not done:**
- `make data`.
- Links (via `pdt diff`).
- A measure per variable.

# Task 45 — A PISA slice

**Status:** `DONE (purple)`: assigned by the coordinator on 2026-11-19; done 2026-11-20.

PISA is the OECD's Programme for International Student Assessment of 15-year-olds, every three years since 2000 (2022 was delayed a year by COVID). Twenge uses its student questionnaire on loneliness and belonging at school.

1. Find the sources on oecd.org: the student questionnaire data files for 2012, 2015, 2018 and 2022, the codebooks, technical reports and questionnaires. Record OECD's terms; until Allen decides they stay `unknown` and the build is local.
2. `~/pdt-pisa` from the template (`copier copy --vcs-ref v0.1.0`), no remote.
3. About 25 variables: design (CNT, school and student ids, W_FSTUWT, the 80 replicate weights as a group), demographics (sex, grade, ESCS), the sense-of-belonging items (ST034 in 2012–2018 and their 2022 equivalent) and the BELONG index, and one plausible-value set (PV1–PV10 READ) as a group. Use `design` for the weights; propose a field for replicate weights and their method if `design` can't say it. Links across cycles.
4. Data for a few countries (USA, GBR, DEU, JPN) if the files allow; `make data` round trip; `pdt check` 0 failures.
5. Here: what PISA tests (plausible values, replicate weights, international item adaptation, scales rescaled across cycles), with proposals. STANDARD.md and schema/ aren't changed.

**Files:** `~/pdt-pisa/` (new, no remote); this file; the Task 45 block on the board.

## Progress

### Stopped here (purple, 2026-11-19)

Stopped at the coordinator's request, at a safe point. Nothing is uncommitted, and no job is running.

**Done.** `~/pdt-pisa`, commits `0bf5490` (template), `b051a0d` (releases and sources), the coordinator's terms commit (Allen's decision: everything ships), and `d77a338` (the slice). `pdt check`: 0 failures. The data checks C3–C5 and C12 run on all four files.
- **Releases:** `2012`, `2015`, `2018`, `2022`, each with one table, `student`.
- **Records:** 414, 102–104 per release: ids, `W_FSTUWT` and its 80 replicate weights, sex, grade, ESCS, the belonging items (ST87Q01–09 in 2012, ST034Q01TA–06TA from 2015), BELONG, and PV1–10READ (PV1–5READ in 2012).
- **Groups:** 12; per release, the replicate weights, the plausible values and the belonging battery.
- **Links:** 204, 2015→2018 and 2018→2022, made by rule `pisa_same_name_same_label` 0.2. 189 are `same_item` only. 15 also have `codes_changed`, and 14 of those `labels_changed` too: CNT, whose list of participating countries changes each cycle, and the ST034 items, whose missing codes go from 5–9 to 95–99 in 2022 and whose codebook stem changes each cycle.
- **Data:** `make data` writes the four countries' rows (USA, GBR, DEU, JPN; 29,000–33,000 per cycle), and every cell round-trips exactly. 2015–2022 are read with pyreadstat; 2012 with `pdt.readers.read_sas_input`, through a copy of the SAS program with `$` added from its LENGTH statement.
- **pdt-yrbss** (Task 29 follow-ups): `73c22bf` uses per-wording origin; `041678b` uses `questions[].numbers` (Q22 in 1999 … Q26 in 2023). `pdt check` 0 failures.

**Sources:** webfs.oecd.org serves urllib. www.oecd.org's database pages for 2012–2018 show a Cloudflare challenge, and I stopped there. Files under www.oecd.org/content/dam/ download in a headless browser after the 2022 database page has loaded: the 2012 data and control files, and the 2022 student questionnaire. Nothing manual is needed from Allen. Missing: the 2012–2018 questionnaires and the technical reports, whose links are on the blocked pages.

**Findings so far (what PISA tests):**
1. **Replicate weights:** variance comes from 80 BRR-Fay replicate weights, not strata and PSUs. `design` can name `weights`, but not the replicates or their method (BRR with Fay's factor, which the technical report gives and the sources here don't). For now `design.note` says so, and each release has a group. Proposal: `design.replicates: {variables: [...] or {prefix, n}, method: brr-fay, fay_factor}`.
2. **Plausible values:** PV1–10READ (5 in 2012) are draws to analyse together. They're a group of kind `other`, with `variable_type: computed`. Proposal: a group kind (or variable_type) `plausible_values`, so tools don't treat one PV as the score.
3. **Codes that disagree between codebook and data file:** the 2022 and 2018 codebooks give BELONG's and ESCS's missing codes as 9999995–9999999 (the SAS files' codes), and 2022's ST004D01T as 95–99, while the SPSS data files use 95–99 and 5–9. The build matches them by label and records it in each code's origin note and in build/report.md. Proposal: say in §4.2 that the codes are the data file's, and that documentation with other codes is matched by label and reported.
4. **Missing codes nobody marks:** grade (`ST001D01T`) labels 97–99 as "Not Applicable", "Invalid" and "Missing", but neither the codebook nor the SPSS file marks them missing. They're classified by rule `pisa_missing_from_label` (§4.2's third choice), the first real use of it.
5. **Missing codes change by cycle:** the ST034 items use 5–9 in 2015/2018 and 95–99 in 2022, and 2015 alone has "Not Reached" (6). The links record `codes_changed` and list them.
6. **Scales re-estimated each cycle:** BELONG and ESCS are WLE indices estimated afresh in each cycle, and the OECD publishes rescaled ESCS for trend analysis separately. They aren't linked. Proposal: a link relation (or a record field) for "same construct, rescaled; not comparable without the trend file".
7. **International adaptation:** the questionnaire asks "What <grade> are you in?". `<grade>` is a placeholder each country fills in, and the national versions are separate files (per-country zips on the 2022 page). Proposal: a note or field for adaptation placeholders.
8. **Renamed items across cycles with no crosswalk in hand:** 2012's ST87Q01–06 look like 2015's ST034Q01TA–06TA, but no source here says so (the technical reports would). They're left unlinked, as rule 2 requires.
9. **Rows kept by country:** the common-format files hold four countries' rows. `data_waves` covers waves, not other row selections; the tables' descriptions say it. Proposal: `data_rows: {column: CNT, in: [...]}`, which C3–C5 would read like `data_waves`.
10. **A second reader to share:** `pdt.readers` has no SPSS reader. `build/pisa.py` has `read_sav` (pyreadstat, user-missing codes kept as numbers, system missing as `Code(".")`), and the shared reader is a proposal for views + site. `read_sas_input` would also need to take text types from a LENGTH statement (the 2012 program).

**Next step:**
- Refine the terms `notice` if the OECD's exact dataset citations turn up.
- Ask Allen for the 2015 and 2022 technical reports, which would give the ST87→ST034 continuity and the Fay factor.
- Then write up these proposals and report to the coordinator.

### Resumed (purple, 2026-11-20): decisions on the proposals

The coordinator's decisions (2026-11-20; standard `d04af94`):

| Proposal | Decision | What pdt-pisa does |
|---|---|---|
| 1 `design.replicates` | accepted: `{variables \| prefix + n, method, fay_factor, note}` | `prefix: W_FSTURWT, n: 80, method: fay`; `fay_factor` only from a source in hand |
| 2 plausible values | accepted: group kind `plausible_values` | the `pv-read` groups use it |
| 3 codes that disagree | accepted: §4.2, the data file's codes, matched by label, noted in the origin | as built |
| 4, 5, 8 | no change | |
| 6 rescaled indices | accepted: link relation `rescaled`, only where a source says so | BELONG and ESCS linked only with a source |
| 7 adaptation placeholders | declined for now; a note is enough | |
| 9 `data_rows` | accepted: `data_rows: {column, in}` on a release or table | C3–C5 to read it (`lib/pdt/check.py`, with a test) |
| 10 shared readers | accepted: `read_sav` in `pdt.readers`; `read_sas_input` takes text types from LENGTH | tests on a tiny generated .sav |

**Source search (2026-11-20).**
- **OECD hosts:**
  - The OECD's 2012–2018 questionnaires and technical reports are on www.oecd.org and t4.oecd.org under the old `/pisa/` paths. urllib gets 403, and a headless browser gets Cloudflare's "Just a moment..." challenge, so I stopped there.
  - OECD iLibrary (oecd-ilibrary.org, read.oecd-ilibrary.org) answers 403.
  - search.oecd.org no longer resolves.
  - webfs.oecd.org has no directory listing.
- **NCES** (https://nces.ed.gov/surveys/pisa/questionnaire.asp) serves the US versions of every cycle's questionnaires to urllib: 2018 and 2015 as HTML, 2012 as three PDFs, one per rotated form (A, B, C). These are national (US) versions, not the international source versions:
  - **2012:** the belonging question is on forms B and C only, printed with its international id (ST87, question Q40 on form B).
  - **2015, 2018:** the question is printed with its id (ST034).

### Done (purple, 2026-11-20)

**Toolkit** (pytest: 217 passed, 1 skipped):
- `3bd276c`: `pdt.readers.read_sav` (pyreadstat; user-missing codes kept as numbers, system missing as `Code(".")`; `rows=` keeps some rows). `parse_sas_input` now takes text columns from a LENGTH statement and matches labels ignoring case when that's unambiguous. Tests: `lib/tests/test_readers_pisa.py`, including a tiny generated .sav. Red agreed.
- `a85d59a`: `data_rows` in `pdt check`, taken from the table, the release or the dataset.
  - **C3:** fails on rows outside `data_rows`, reports kept codes with no rows, and reports when the column isn't in the file.
  - **C5:** notes, without warning, a wave in availability that has no data in the kept rows.
  - Tests are in `test_check_data.py`.

**pdt-pisa** (`5cfe629`; `pdt check` 0 failures; every file round-trips exactly):
- **Question text for 2012–2018** comes from NCES's US versions (5 new sources), each wording noted as the US version:
  - 2015 and 2018: the ST034 battery.
  - 2012: ST87Q01–09 from forms B and C (Q40 on B, Q54 on C, with ST87 printed above), so their availability is `{wave: 2012, form: B}` and `{wave: 2012, form: C}`. The 2012 file's `QuestID` is now a record, with `dimensions.form` mapping 1–3 and 5 to forms A–C and UH. The data agree: answers to ST87Q01 come from QuestID 2 and 3 only (9,305 and 9,077 in the kept rows).
  - The 2015 US version lists the responses from "Strongly Disagree" to "Strongly Agree", the reverse of the data's codes. Its records' notes say so.
- **New fields in `dataset.yaml`:**
  - `design.replicates`: `{prefix: W_FSTURWT, n: 80, method: fay}`, and the 2012 release overrides it with `W_FSTR`. `fay_factor` is left out: no source here gives it.
  - `data_rows`: `{column: CNT, in: [USA, GBR, DEU, JPN]}`. `build/slice.yaml` no longer lists the countries, and `scripts/build_data.py` reads `data_rows`.
- **Groups:** the plausible-value groups are kind `plausible_values`.
- **Links:** ESCS 2015→2018 and 2018→2022 are `rescaled`. The source is the OECD's data-files page (a new source, `pisa-data-files-page`), which lists "Rescaled indices of economic, social and cultural status (ESCS) for use with the PISA 2012, 2015 and 2018 datasets". BELONG stays unlinked, since no source here says it was rescaled.
- **Readers:** the data are read with `pdt.readers.read_sav` and `read_sas_input`, so the local reader and the marked copy of the 2012 SAS program are gone.

**Open:**
- The NCES files' `redistribution` is `unknown`. NCES is a US federal agency, so they are probably public domain, but that's Allen's decision.
- Still missing: the OECD's international 2012–2018 questionnaires and the technical reports, which would give Fay's factor, BELONG's rescaling, and whether ST87 continues as ST034. They are behind a bot check. Per the coordinator, ask Allen for them only if needed.

### Technical reports (coordinator, 2026-11-20)

- **2012:** Allen downloaded the report from UNESCO's NEQMAP mirror (https://neqmap.bangkok.unesco.org/wp-content/uploads/2019/08/PISA-2012-technical-report-final-1.pdf). It's now in `~/pdt-pisa/data/raw/PISA-2012-technical-report-final-1.pdf` (5.2 MB). Record it as a source, with the mirror and the OECD as publisher.
- **2015 and 2018:** the OECD links failed for Allen in a browser too, so don't ask him again. Look for mirrors that serve scripts: NEQMAP, NCES's "Technical Report and User Guide" for PISA 2015 and 2018, and ministry repositories. Stop at any bot check.
- Then settle the three open facts, citing pages: Fay's factor, whether BELONG was rescaled, and ST87→ST034.

### Technical reports, settled (purple, 2026-11-20)

pdt-pisa `afde85d`, `pdt check` 0 failures. New sources: `pisa2012-techrep` (the copy from UNESCO's NEQMAP mirror, `acquisition: manual`), and NCES's `nces-pisa2015-techrep` (NCES 2017-095) and `nces-pisa2018-techrep` (NCES 2021-011), which urllib fetches. All three have `redistribution: unknown`. They're OECD and NCES reports, not questionnaires, so that's Allen's call.

| Question | Answer | Source |
|---|---|---|
| Fay's factor | **0.5**, for 2012, 2015 and 2018, set in those releases' `design.replicates.fay_factor`. Left out for 2022, which has no source. | 2012: PISA 2012 Technical Report, Ch. 8, pp. 139–140 (weights × 1.5 and × 0.5; V = 0.05 Σ). 2015: NCES 2017-095, §10.1, p. 64 ("the Fay coefficient set to 0.5"). 2018: NCES 2021-011, §10, p. 66 (the same words). |
| ST87Q01–06 → ST034Q01TA–06TA | **Not settled; still unlinked.** The 2012 report says only ST87Q01–06 are trend items with 2003 (p. 51: "Trend analyses should only involve the 6 common items (i.e. ST87Q01 to ST87Q06)"; p. 332: same wording as the first 6 items of 2012). It predates 2015, so it can't say what continues. | Needs the OECD's 2015 Technical Report, Ch. 16. |
| BELONG rescaled | **Not settled; still unlinked.** The 2012 report says the 2012 scale was extended from 6 to 9 items (p. 51), which concerns 2003→2012, not the cycles here. | Needs the 2015 and 2018 OECD reports, Ch. 16. |

**Still blocked:** every copy of the OECD's 2015 and 2018 technical reports that searches turn up is on www.oecd.org, t4.oecd.org or search.oecd.org, behind the bot check or no longer resolving. NCES's US reports carry no chapter on scaling the context questionnaire. No other mirror turned up (NEQMAP has only 2012).

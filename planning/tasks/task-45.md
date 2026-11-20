# Task 45 — A PISA slice

**Status:** `DOING (purple)` — assigned by the coordinator on 2026-11-19.

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

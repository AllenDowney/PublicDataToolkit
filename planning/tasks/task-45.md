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

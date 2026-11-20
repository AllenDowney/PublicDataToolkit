# Task 60 — An NSDUH slice

**Status:** `DOING (blue)`, claimed 2026-11-20.

The National Survey on Drug Use and Health (SAMHSA) in `~/pdt-nsduh`, built from the Copier template, as in the other dataset tasks:
- annual public-use files, for recent years;
- substance use and mental-health items, plus the design variables (weights, strata, PSUs).

SAMHSA's terms are recorded in the repo, and the decision is left to Allen. Every data job runs under the memory cap (`systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0`).

Task 57 (blue) is paused waiting for an API key. The coordinator will say when to go back to it, or to the catalog rebuild.

**Files:** `~/pdt-nsduh/`, this file and the Task 60 block on the board.

## Done (2026-11-20)

`~/pdt-nsduh`: commits `74eabec` (records) and `43c8ba6` (agent/ and export/; docs/ gitignored). `pdt check`: 0 failures.

**What it holds**

| Release | File | Records |
|---|---|---|
| `2023` | public use file v2 | 43 |
| `2024` | v1 | 43 |
| `2025` | v1 | 47 |

- **Variables:** design (QUESTID2, ANALWT2_C, VESTR_C, VEREP), demographics, tobacco and vaping, alcohol, marijuana, other drugs (ILLYR, and ILLYR2 from 2025), and mental health. Mental health covers the six K6 items, the K6 score, serious psychological distress, adult and youth depression, suicidal thoughts, treatment, and any mental illness.
- **Sources:** each year's Stata bundle and PDF codebook, and SAMHSA's comparability chart for 2021–2025, all fetched by URL with hashes.
- **Links (86).** 85 are `same_item`: same comparability number in the chart for both years. One is `renamed`: ILLYR → ILLYR2 in 2025, with the chart's note that the two aren't comparable for youths.
- **Groups:** 20 module groups from the chart.
- **Scale signatures:** 29, by the shared rule.

**Findings**
- **The codebooks are complete and exact.** In every release, each data column has a codebook entry and each entry has a column. Every value's frequency in the codebook equals the count in the data. No other dataset here has matched this well.
- **The 2024 data file spells 1,881 of its 2,632 names in lowercase** (`verep`, `filedate`). Its codebook, and the 2023 and 2025 files, use capitals. Records keep each file's spelling, and links match names case-insensitively.
- **The codebook marks no code as missing.** SAMHSA writes its reserved codes' labels in capitals: 85 BAD DATA, 94 DON'T KNOW, 97 REFUSED, 98 BLANK, 99 LEGITIMATE SKIP, 91 NEVER USED, 93 DID NOT USE. Rule `nsduh_missing_from_labels` 0.1 types them.
  - "." (blank) labeled "Aged 12-17" is `inap`.
  - Six "." codes stay `unresolved`: "Aged 12-17/Unknown (Otherwise)" mixes out-of-universe with unknown.
- **The question text comes from the codebook** (the paragraph above each entry), with the questionnaire item as `questions[].number` (e.g. HOPE30).
  - A recode lists its source variables instead, kept as the extension `nsduh.source_variables`, a candidate for the standard.
  - A superscript note marker merges into names in the PDF text (`DSTHOP301`). The parser resolves it against the data's names and attaches the section note.
- **The design** is in `dataset.yaml`, with the 2024 override for `verep`.

**For Allen: the terms.**
- SAMHSA's public use files page offers every file with no login, click-through, data use agreement or license.
- The codebooks give only a recommended citation, and no copyright or reuse statement was found on SAMHSA's site.
- The same series is also at ICPSR (series 64), under ICPSR's terms. This repo uses SAMHSA's own files.
- All four fields are `unknown`, so nothing may ship.
- **Caveat:** `llm_processing` is `unknown`, but I read parts of the codebooks while writing the parser, before a decision. Instructions step 1 says to stop first when LLM processing may not be allowed.

**Not done:**
- `make data` (the common format). It needs the terms.
- Earlier years (2021–2022, also in the chart).

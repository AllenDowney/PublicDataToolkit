# Task 22 — NSFG question text and earlier cycles

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE (nsfg)` 2026-11-19. Committed in `pdt-nsfg` (896791f, 7ab721e, 2038396, 3c13d85, 787fd4a); not pushed. The views need regenerating after 787fd4a. Allen sent the report of the BABYSEX error to NCHS on 2026-11-19; both corrections are `filed` (pdt-nsfg 13305db).

- **Question text:** the codebooks give item references ("AD-7b") but no wording. Find the CAPI questionnaire documents on the CDC site, and add `questions` to records by item reference.
- **Earlier cycles:** add 2017–2019 as a second release (data and download code in MarriageNSFG; codebooks from CDC), and link items across cycles.

**Files:** `../pdt-nsfg/` only.

## What was done

| | 2022-2023 | 2017-2019 (new) |
|---|---|---|
| Records | 52 (unchanged except `questions` and range labels) | 49: the same variables where the name exists, plus WGT2017_2019, SECU and SEST |
| Question text | 15 of 52, every record with an item reference, from the CAPI-lite questionnaires | 12 of 49, from the codebooks, which print the question under each raw item |
| Codebook | NCHS layout, one per table | ICPSR layout, 13 or 14 section PDFs per table; 7 female and 6 male sections hold slice variables |
| Data | SAS files | fixed-width `.dat` plus Stata `.dct` from ftp.cdc.gov (byte-identical to MarriageNSFG's copies); the `.dct` labels are the records' labels |

New in `pdt-nsfg/build/`: `capilite.py` (rule `nsfg_capilite_text` 0.2) and `icpsr_codebook.py`. `build_slice.py` builds both releases and writes `metadata/links.jsonl`. It checks every code's count in the codebook against the data, and flags any entry that yields no codes. Neither check finds anything in either release.

## Findings

- **Getting the documents.** cdc.gov returns 403 to curl and urllib, for the pages and the PDFs. Headless Chromium (Playwright) loads them with no bot check, if it opens the cycle's documentation page first. The documents are in `sources.yaml` as `acquisition: manual`, with those steps. ftp.cdc.gov serves scripts, so the 2017-2019 data and dictionaries are `automated`. For Task 18: `pdt download` could fall back to a browser for cdc.gov.
- **Question text, 2022-2023.** The User's Guide (p. 29) says variable names match the questionnaire's, so questions are matched by name. NCHS publishes two forms of each questionnaire: the CRQ (the reference, with programming logic) and CAPI-lite (readable). The text comes from CAPI-lite. When the wording depends on a condition (MARSTAT has 5 wordings, by spouse or partner and sex), each wording is one question, with its condition as printed ("IF ANY RELAR[X]=1 and SEX[X]=1", "ELSE") in `condition` (STANDARD.md §4.1, added for this). Lines marked as interviewer instructions go in `instructions`.
- **A codebook error.** The 2022-2023 pregnancy codebook labels BABYSEX "BB-6a", but the CRQ and CAPI-lite give BC-6a. (In 2017-2019 it was BD-2, so BB-6a isn't a leftover from that cycle.) Two `verified` corrections in `metadata/corrections.jsonl` fix the label and `nsfg.item`. Allen reported it to nsfg@cdc.gov, the address the User's Guide (p. 19) gives for errors, on 2026-11-19; both corrections are `filed`.
- **2017-2019's female section A codebook is OCR text.** Names, column numbers and table borders are misread ("H1SP{17-17)" for HISP; a border read as "I" hid fmarit's codes until the parser allowed for it). The count check confirms the slice variables from that section: AGE_R, MARSTAT, EVRMARRY and FMARIT.
- **Names change case.** 2017-2019 codebooks write computed variables in lowercase (`age_r`, `pregordr`, `currprts`), and its data file writes everything in lowercase. Records use the codebook's spelling. `pdt` resolves names exactly, so links give each side's spelling.

## Links (decided with the coordinator)

Allen's brief: link only as NCHS's documentation supports. NCHS's only statement linking the two cycles is the "Summary of NSFG Questionnaire Changes for 2022-2023 (relative to 2017-2019 NSFG)". No crosswalk covers 2022-2023, and the FAQ urges caution comparing 2022-2023 with earlier cycles (multimode design). The coordinator decided:

- (a) **From the change summary**, `origin: publisher`: MARSTAT, female and male, `wording_changed` + `codes_changed` (codes 1–6 in 2017-2019, 1–3 in 2022-2023; the note says the codes come from the codebooks). The summary also names LMARSTAT, RELNOW and birth weight, but no 2017-2019 variable in the slice that it says they replace. In 2017-2019, AD-7c is FMARSTAT, not LMARSTAT.
- (b) **Rule `nsfg_identical_documentation`**, `origin: rule`, `same_item`. It went through three versions, each the coordinator's decision. Each link's note lists the allowances it used.
  - **0.1** required the same name (ignoring case), item reference, question text, codes and labels. It gave 4 links.
  - **0.2** allowed three artifacts of the documentation:
    - labels that differ only in case;
    - codes listed by only one codebook, because the codebooks list only codes that occur;
    - different item references, when nothing else differs.
  - **0.3** narrows the second allowance. It applies only when one release's codes are a subset of the other's. When each side has codes the other lacks, the codes changed: HIEDUC_I (1 "multiple regression" vs 2 "logical") and male MFLASTP (7 vs 8, 9).
- **Rule `nsfg_count_labels_reworded` 0.1**, `origin: rule`, `labels_changed`. A pair qualifies when everything else passes `nsfg_identical_documentation` 0.3, and every label that differs is a count label in both cycles: the code alone, or with an ordinal or a unit ("15" vs "15 years", "1" vs "1ST BIRTH").
- Not (c): silence in the summary isn't evidence.

**Result: 21 links.**

| Source | Relation | Links |
|---|---|---|
| The change summary | `wording_changed`, `codes_changed` | 2: MARSTAT (female, male) |
| `nsfg_identical_documentation` 0.3 | `same_item` | 14: CASEID (3 tables), EVRMARRY (female, male), FMARITAL (female, male), RELDLIFE (female, male; item numbers differ), FMARIT, male RELIGION, AGEPREG, OUTCOME_I, PMARPREG |
| `nsfg_count_labels_reworded` 0.1 | `labels_changed` | 5: AGE_R (female, male), RSCRAGE, BIRTHORD, PREGORDR |

OUTCOME_I still links under 0.3. 2017-2019 lists codes 0 and 1, and 2022-2023 lists only 0, so one is a subset of the other: no 2022-2023 pregnancy outcome was imputed by regression. HIEDUC_I's codes go both ways, so it doesn't link.

**19 shared names stay unlinked.** `pdt-nsfg/build/report.md` lists each with what differs.

## Follow-up: a later pass with `codes_changed` and `labels_changed`

These pairs are the same variable with real changes. A pass with an NCHS source, or a rule that records the change, could link them:

| Variable | What changed |
|---|---|
| HIEDUC (female, male) | recoded: 2017-2019 codes 5–15, 2022-2023 codes 1–11, with different categories |
| HIEDUC_I (female) | imputation codes: 1 "multiple regression" in 2017-2019, 2 "logical" in 2022-2023 |
| MFLASTP (male) | codes: 7 "Not ascertained" in 2017-2019; 8 "Refused" and 9 "Don't know" in 2022-2023 |
| RMARITAL (female, male) | labels for codes 2, 5 and 6; code 6 became "Never been married to, nor currently cohabiting with a person of the opposite-sex" |
| OUTCOME (pregnancy) | code 2: "INDUCED ABORTION" → "Abortion" |
| HISPRACE2 (female, male) | code 1: "Hispanic" → "Hispanic (regardless of race reporting)" |
| RELIGION (female, pregnancy) | code 4: "OTHER RELIGIONS" → "Other religion" |
| POT12 (female, male) | wording: "smoked" → "used" marijuana; male item KC-3 → KC-6 |
| ATTND14, ATTNDNOW (female, male) | the show card: "Card 79" → "Card 77", and item numbers |
| SAMLIFENUM (female) | count labels reworded, and the top code: "10 OR MORE PARTNERS" → "10 or more" |
| CURRPRTS (female) | count labels reworded, and code 0: "NONE" → "0" |

## Limitations

- 2017-2019 coverage (C3) isn't checked, because only the codebook sections that hold slice variables are sources.
- Labeled ranges ("0-19 Under 20 years") keep their labels only in `valid_range.note`, as in pdt-fars.

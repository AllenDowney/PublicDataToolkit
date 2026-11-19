# Task 22 — NSFG question text and earlier cycles

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE (nsfg)` 2026-11-19. Committed in `pdt-nsfg` (896791f, 7ab721e, 2038396, 3c13d85); not pushed. The views need regenerating after 2038396. The report of the BABYSEX error to NCHS is drafted for Allen to send.

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
- **A codebook error.** The 2022-2023 pregnancy codebook labels BABYSEX "BB-6a", but the CRQ and CAPI-lite give BC-6a. (In 2017-2019 it was BD-2, so BB-6a isn't a leftover from that cycle.) Two `verified` corrections in `metadata/corrections.jsonl` fix the label and `nsfg.item`. A report for nsfg@cdc.gov, the address the User's Guide (p. 19) gives for errors, was drafted outside the repository. Once it's sent, set `upstream` to `filed`.
- **2017-2019's female section A codebook is OCR text.** Names, column numbers and table borders are misread ("H1SP{17-17)" for HISP; a border read as "I" hid fmarit's codes until the parser allowed for it). The count check confirms the slice variables from that section: AGE_R, MARSTAT, EVRMARRY and FMARIT.
- **Names change case.** 2017-2019 codebooks write computed variables in lowercase (`age_r`, `pregordr`, `currprts`), and its data file writes everything in lowercase. Records use the codebook's spelling. `pdt` resolves names exactly, so links give each side's spelling.

## Links (decided with the coordinator)

Allen's brief: link only as NCHS's documentation supports. NCHS's only statement linking the two cycles is the "Summary of NSFG Questionnaire Changes for 2022-2023 (relative to 2017-2019 NSFG)". No crosswalk covers 2022-2023, and the FAQ urges caution comparing 2022-2023 with earlier cycles (multimode design). The coordinator decided:

- (a) **From the change summary**, `origin: publisher`: MARSTAT, female and male, `wording_changed` + `codes_changed` (codes 1–6 in 2017-2019, 1–3 in 2022-2023; the note says the codes come from the codebooks). The summary also names LMARSTAT, RELNOW and birth weight, but no 2017-2019 variable in the slice that it says they replace. In 2017-2019, AD-7c is FMARSTAT, not LMARSTAT.
- (b) **Rule `nsfg_identical_documentation`**, `origin: rule`, `same_item`. Version 0.1 required the same name (ignoring case), item reference, question text, codes and labels; it gave 4 links. Version 0.2 (the coordinator's decision) allows three documentation artifacts, and each link's note lists the ones it used:
  - labels that differ only in case;
  - codes listed by only one codebook, because the codebooks list only codes that occur; the note records which side lacked them;
  - different item references, when nothing else differs.
- Not (c): silence in the summary isn't evidence.

**Result: 18 links,** 2 from the summary and 16 by the rule: CASEID (3 tables), EVRMARRY (female, male), FMARITAL (female, male), RELDLIFE (female, male; item numbers differ), FMARIT, HIEDUC_I, MFLASTP, male RELIGION, AGEPREG, OUTCOME_I and PMARPREG.

Note that HIEDUC_I and OUTCOME_I link even though their imputation codes don't overlap (2017-2019 lists code 1, "multiple regression", and 2022-2023 lists code 2, "logical"). That's the second allowance at work: each codebook lists only the codes that occurred.

**22 shared names stay unlinked.** `pdt-nsfg/build/report.md` lists each with what differs.

| What differs | Variables |
|---|---|
| Changes that look real | HIEDUC (recoded); RMARITAL (code 6 became "Never been married to, nor currently cohabiting with a person of the opposite-sex"); POT12 ("smoked" → "used" marijuana; code 7 only in 2017-2019); OUTCOME ("INDUCED ABORTION" → "Abortion"); HISPRACE2 code 1; RELIGION code 4 (female and pregnancy) |
| Count labels reworded | AGE_R and RSCRAGE ("15 years" → "15"), SAMLIFENUM and CURRPRTS ("1 PARTNER" → "1"), BIRTHORD and PREGORDR ("1ST BIRTH" → "1") |
| Question text: card number | ATTND14 and ATTNDNOW ("Card 79" → "Card 77"), with item numbers changed too |

The rule doesn't allow reworded count labels or card numbers, so those stay unlinked.

## Limitations

- 2017-2019 coverage (C3) isn't checked, because only the codebook sections that hold slice variables are sources.
- Labeled ranges ("0-19 Under 20 years") keep their labels only in `valid_range.note`, as in pdt-fars.

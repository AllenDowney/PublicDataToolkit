# Task 22 — NSFG question text and earlier cycles

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE (nsfg)` 2026-11-19. Committed in `pdt-nsfg` (896791f, 7ab721e); not pushed. The views need regenerating (asked of the coordinator).

- **Question text:** the codebooks give item references ("AD-7b") but no wording. Find the CAPI questionnaire documents on the CDC site, and add `questions` to records by item reference.
- **Earlier cycles:** add 2017–2019 as a second release (data and download code in MarriageNSFG; codebooks from CDC), and link items across cycles.

**Files:** `../pdt-nsfg/` only.

## What was done

| | 2022-2023 | 2017-2019 (new) |
|---|---|---|
| Records | 52 (unchanged except `questions`) | 49: the same variables where the name exists, plus WGT2017_2019, SECU and SEST |
| Question text | 15 of 52, every record with an item reference, from the CAPI-lite questionnaires | 12 of 49, from the codebooks, which print the question under each raw item |
| Codebook | NCHS layout, one per table | ICPSR layout, 13 or 14 section PDFs per table; 7 female and 6 male sections hold slice variables |
| Data | SAS files | fixed-width `.dat` plus Stata `.dct` from ftp.cdc.gov (byte-identical to MarriageNSFG's copies); the `.dct` labels are the records' labels |

New in `pdt-nsfg/build/`: `capilite.py` (rule `nsfg_capilite_text`) and `icpsr_codebook.py`. `build_slice.py` builds both releases, writes `metadata/links.jsonl`, and now checks every code's count in the codebook against the data. No mismatches in either release.

## Findings

- **Getting the documents.** cdc.gov returns 403 to curl and urllib, for the pages and the PDFs. Headless Chromium (Playwright) loads them with no bot check, if it opens the cycle's documentation page first. The documents are in `sources.yaml` as `acquisition: manual`, with those steps. ftp.cdc.gov serves scripts, so the 2017-2019 data and dictionaries are `automated`. For Task 18: `pdt download` could fall back to a browser for cdc.gov.
- **Question text, 2022-2023.** The User's Guide (p. 29) says variable names match the questionnaire's, so questions are matched by name. NCHS publishes two forms of each questionnaire: the CRQ (the reference, with programming logic) and CAPI-lite (readable). The text comes from CAPI-lite. When the wording depends on a condition (MARSTAT has 5 wordings, by spouse or partner and sex), each wording is one question, with its condition in `note` ("Asked when: IF ANY RELAR[X]=1 and SEX[X]=1"). Lines marked as interviewer instructions go in `instructions`. The schema has no field for a condition like this; `note` holds it for now.
- **A codebook error.** The 2022-2023 pregnancy codebook labels BABYSEX "BB-6a", but the CRQ and CAPI-lite give BC-6a: the pregnancy series was renumbered. Two `verified` corrections in `metadata/corrections.jsonl` fix the label and `nsfg.item`. Not yet reported to NCHS.
- **2017-2019's female section A codebook is OCR text.** Names and column numbers are misread ("H1SP{17-17)" for HISP). The parser accepts misread headers, and the count check confirms AGE_R, MARSTAT, EVRMARRY and FMARIT, the slice variables from that section.
- **Names change case.** 2017-2019 codebooks write computed variables in lowercase (`age_r`, `pregordr`, `currprts`), and its data file writes everything in lowercase. Records use the codebook's spelling. `pdt` resolves names exactly, so links give each side's spelling.

## Links (decided with the coordinator)

Allen's brief: link only as NCHS's documentation supports. NCHS's only statement linking the two cycles is the "Summary of NSFG Questionnaire Changes for 2022-2023 (relative to 2017-2019 NSFG)". No crosswalk covers 2022-2023, and the FAQ urges caution comparing 2022-2023 with earlier cycles (multimode design). The coordinator decided:

- (a) **From the change summary**, `origin: publisher`: MARSTAT, female and male, `wording_changed` + `codes_changed` (codes 1–6 in 2017-2019, 1–3 in 2022-2023; the note says the codes come from the codebooks). The summary also names LMARSTAT, RELNOW and birth weight, but no 2017-2019 variable in the slice that it says they replace. In 2017-2019, AD-7c is FMARSTAT, not LMARSTAT. So no other links.
- (b) **Rule `nsfg_identical_documentation` 0.1**, `origin: rule`, `same_item`: same name (ignoring case), same item reference, same question text and the same codes and labels in both cycles' NCHS codebooks. 4 links: CASEID in all three tables, and male RELIGION.
- Not (c): silence in the summary isn't evidence.

**34 shared names stay unlinked.** `pdt-nsfg/build/report.md` lists each with what differs. Three causes do most of it, and the coordinator may want to revisit the rule:

| Cause | Examples |
|---|---|
| Item renumbering only | male RELDLIFE (JB-9 → JB-7) differs in nothing else; female RELDLIFE differs only in its item number and in "Don't know" vs "Don't Know" |
| Label case only | EVRMARRY, FMARITAL, PMARPREG: 2017-2019 recode labels are in capitals |
| Codes that occur in only one cycle | the codebooks list only codes that occur in the data (AGE_R 49 and 50; male ATTND14's "Refused") |

Real changes are mixed in with these: HIEDUC's codes, MARSTAT's, POT12's "Not ascertained" (code 7), and SAMLIFENUM's code 997. A rule that ignored case and zero-frequency codes would separate them, but deciding that is the coordinator's call.

## Limitations

- **Labeled ranges lose their labels.** When the codebook gives a range with a label ("0-19 Under 20 years" in AGEPREG; "2-95 2 OR MORE PARTNERS" in CURRPRTS), the build records a `valid_range` and drops the label. The same is true of 2022-2023. The range itself is fixed: it now spans the single codes beside the range rows (7ab721e).
- 2017-2019 coverage (C3) isn't checked, because only the codebook sections that hold slice variables are sources.

# Task 75 — pdt-nsfg: every cycle and variable MarriageNSFG uses

**Status:** `DONE (yellow)` on 2026-11-20. Started 2026-11-20. Created by the coordinator, 2026-11-20, at Allen's request.

## Why

MarriageNSFG (`../MarriageNSFG`, read only from here) reads the NSFG with its own per-cycle readers (`nsfg/marriage.py`: `read_fem_resp_1982` … `read_fem_resp_2023`, `read_male_resp_2002` … `read_male_resp_2023`). pdt-nsfg covers only 2017–2019 and 2022–2023, with 18–24 variables per table; for 2022–2023 only 7 of them are among the variables MarriageNSFG reads. Allen would like MarriageNSFG to use pdt-nsfg instead, once pdt-nsfg covers what it needs.

## What to do

1. **Inventory.** From `nsfg/marriage.py` and its `download_nsfg.py`, list per cycle and file (female respondent, male respondent) every variable MarriageNSFG reads, and the raw files and setup programs it uses. Don't modify MarriageNSFG.
2. **Releases.** Add the female respondent file for 1982 (Cycle 3), 1988 (4), 1995 (5), 2002 (6), 2006–2010, 2011–2013, 2013–2015 and 2015–2017, and the male respondent file for 2002 through 2015–2017, to `dataset.yaml` and `sources.yaml`, with NCHS's URLs and checksums. Record which documentation each cycle has (codebook PDF, SAS or Stata setup, data dictionary); older cycles differ.
3. **Records** for every inventoried variable in every cycle that has it, from NCHS's documentation (extend `build/nsfg_docs.py` or add a parser per documentation style); value labels from the setup programs where the codebook lacks them; missing codes typed.
4. **Links** between consecutive cycles, by NCHS's statements where they exist and the same-name rule where the documentation is identical (`pdt diff` for candidates). Recodes MarriageNSFG applies ("make codes consistent with most recent cycles", guessing hidegree) are analysis choices: don't make them links or corrections; note them in task-75.md for the MarriageNSFG switch.
5. **Data:** `make data` for every release under the memory cap, with exact round trips.
6. **Runbook:** `instructions/` (or the release-diff skill): a short "adding a release to an existing dataset repo" procedure, written from doing it here, for Task 76.
7. **The switch, as a plan only:** in task-75.md, what MarriageNSFG would change to read pdt-nsfg's files (which functions go, what stays), for a later session in that repo.

## Progress

### 2026-11-20: inventory and sources

**From `../MarriageNSFG/nsfg/marriage.py`** (read only; extracted from the readers' `names` and `usecols` lists and `raw()` file names). For 1982, 1988 and 1995 MarriageNSFG reads fixed columns under its own names; the NCHS name is the one NCHS's SAS setup program gives those columns (MarriageNSFG name = NCHS name).

| Release | File | Variables | Files MarriageNSFG reads | Variables (NCHS names) |
|---|---|---|---|---|
| 1982 | female | 19 | 1982NSFGData.dat.gz | finalwgt=FINALWT, ageint=AGE, mar2p=MAR2P, cmmarrhx=FMAR1MO, fmarital=FMARITAL, cmintvw=R7_CM, cmbirth=CMBIRTH, marend01=F18_1, cmdivorcx=F21_1CM, cmstphsbx=F22_1CM, fmarno=FMARNO, rmarital=MARITAL, parity=PARITY, intent=INTENT, addexp=ADDEXP, agebaby1=AGEBABY1, strloper=STRLOPER, wantkid2=WANTKID2, educat=EDUCAT |
| 1988 | female | 19 | 1988FemRespDataLines.dat.gz | finalwgt=W5, ageint=A_5, currentcm=F15MO, firstcm=F19M1MO, cmintvw=QDICMO, cmbirth=A_3, marend01=F23M1, cmdivorcx=F26M1MO, cmstphsbx=F27M1MO, fmarno=FMARNO, rmarital=RMARITAL, parity=PARITY, intent=INTENT, addexp=ADDEXP, agebaby1=AGEBABY1, strloper=STRLOPER, wantkid2=WANTKID2, educat=EDUCAT, fmarital=FMARITAL |
| 1995 | female | 19 | 1995FemRespData.dat.gz | cmintvw=A_DOI, timesmar=TIMESMAR, cmmarrhx=MARDAT01, cmbirth=BDAYCENM, finalwgt=POST_WT, marend01=MAREND01, cmdivorcx=DIVDATH1, cmstphsbx=WNSTPH1, marstat=MARSTAT, fmarno=FMARNO, rmarital=RMARITAL, parity=PARITY, intent=INTENT, addexp=ADDEXP, agebaby1=AGEBABY1, strlopev=STEROPEV, hieduc=HIEDUC, fmarital=FMARITAL, hidegree=HIDEGREE |
| 2002 | female | 25 | 2002FemResp.dct, 2002FemResp.dat.gz | CASEID, CMMARRHX, CMDIVORCX, CMBIRTH, CMINTVW, EVRMARRY, PARITY, FINALWGT, MARDAT01, MAREND01, MARDIS01, RMARITAL, FMARITAL, FMARNO, MAR1DISS, INTENT, ADDEXP, AGEBABY1, STRLOPER, TUBS, HYST, RWANT, HIEDUC, HAVEDEG, DEGREES |
| 2006-2010 | female | 25 | 2006_2010_FemRespSetup.dct, 2006_2010_FemResp.dat.gz | CASEID, CMMARRHX, CMDIVORCX, CMBIRTH, CMINTVW, EVRMARRY, PARITY, WGTQ1Q16, MARDAT01, MAREND01, MARDIS01, RMARITAL, FMARITAL, FMARNO, MAR1DISS, NCHILDHH, INTENT, ADDEXP, AGEBABY1, STRLOPER, TUBS, HYST, RWANT, HIEDUC, DEGREES |
| 2011-2013 | female | 24 | 2011_2013_FemRespSetup.dct, 2011_2013_FemRespData.dat.gz | CASEID, CMMARRHX, CMDIVORCX, CMBIRTH, CMINTVW, EVRMARRY, PARITY, WGT2011_2013, MARDAT01, MAREND01, MARDIS01, RMARITAL, FMARITAL, FMARNO, MAR1DISS, NCHILDHH, INTENT, ADDEXP, AGEBABY1, STRLOPER, TUBS, HYST, RWANT, HIEDUC |
| 2013-2015 | female | 24 | 2013_2015_FemRespSetup.dct, 2013_2015_FemRespData.dat.gz | CASEID, CMMARRHX, CMDIVORCX, CMBIRTH, CMINTVW, EVRMARRY, PARITY, WGT2013_2015, MARDAT01, MAREND01, MARDIS01, RMARITAL, FMARITAL, FMARNO, MAR1DISS, NCHILDHH, INTENT, ADDEXP, AGEBABY1, STRLOPER, TUBS, HYST, RWANT, HIEDUC |
| 2015-2017 | female | 21 | 2015_2017_FemRespSetup.dct, 2015_2017_FemRespData.dat.gz | CASEID, CMINTVW, AGER, EVRMARRY, PARITY, WGT2015_2017, MARDAT01, MAREND01, MARDIS01, RMARITAL, FMARITAL, FMARNO, NCHILDHH, INTENT, ADDEXP, AGEBABY1, STRLOPER, TUBS, HYST, RWANT, HIEDUC |
| 2017-2019 | female | 21 | 2017_2019_FemRespSetup.dct, 2017_2019_FemRespData.dat.gz | CASEID, CMINTVW, AGER, EVRMARRY, PARITY, WGT2017_2019, MARDAT01, MAREND01, MARDIS01, RMARITAL, FMARITAL, FMARNO, NCHILDHH, INTENT, ADDEXP, AGEBABY1, STRLOPER, TUBS, HYST, RWANT, HIEDUC |
| 2022-2023 | female | 21 | NSFG-2022-2023-FemRespPUFData.sas7bdat | CASEID, CMINTVW, AGER, EVRMARRY, PARITY, WGT2022_2023, MARDAT01, MAREND01, MARDIS01, RMARITAL, FMARITAL, FMARNO, NCHILDHH, INTENT, ADDEXP, STRLOPER, TUBS, HYST, RWANT, HIEDUC, FTFMODE |
| 2002 | male | 18 | 2002Male.dct, 2002Male.dat.gz | CASEID, MARDAT01, CMDIVW, CMBIRTH, CMINTVW, EVRMARRY, FINALWGT, FMARITAL, TIMESMAR, MARREND4, RMARITAL, ADDEXP, INTENT, EVRCHIL, EVRCHILN, EVEROPER, RWANT, HIEDUC |
| 2006-2010 | male | 19 | 2006_2010_MaleSetup.dct, 2006_2010_Male.dat.gz | CASEID, MARDAT01, CMDIVW, CMBIRTH, CMINTVW, EVRMARRY, WGTQ1Q16, MAREND01, RMARITAL, FMARITAL, FMARNO, MAR1DISS, ADDEXP, INTENT, EVRCHIL, EVRCHILN, EVEROPER, RWANT, HIEDUC |
| 2011-2013 | male | 18 | 2011_2013_MaleSetup.dct, 2011_2013_MaleData.dat.gz | CASEID, MARDAT01, CMDIVW, CMBIRTH, CMINTVW, EVRMARRY, WGT2011_2013, MAREND01, RMARITAL, FMARITAL, FMARNO, MAR1DISS, ADDEXP, INTENT, BIOKIDS, EVEROPER, RWANT, HIEDUC |
| 2013-2015 | male | 18 | 2013_2015_MaleSetup.dct, 2013_2015_MaleData.dat.gz | CASEID, MARDAT01, CMDIVW, CMBIRTH, CMINTVW, EVRMARRY, WGT2013_2015, MAREND01, RMARITAL, FMARITAL, FMARNO, MAR1DISS, ADDEXP, INTENT, BIOKIDS, EVEROPER, RWANT, HIEDUC |
| 2015-2017 | male | 17 | 2015_2017_MaleSetup.dct, 2015_2017_MaleData.dat.gz | CASEID, MARDAT01, CMINTVW, AGER, EVRMARRY, WGT2015_2017, MAREND01, RMARITAL, FMARITAL, FMARNO, MAR1DISS, ADDEXP, INTENT, BIOKIDS, EVEROPER, RWANT, HIEDUC |
| 2017-2019 | male | 17 | 2017_2019_MaleSetup.dct, 2017_2019_MaleData.dat.gz | CASEID, MARDAT01, CMINTVW, AGER, EVRMARRY, WGT2017_2019, MAREND01, RMARITAL, FMARITAL, FMARNO, MAR1DISS, ADDEXP, INTENT, BIOKIDS, EVEROPER, RWANT, HIEDUC |
| 2022-2023 | male | 19 | NSFG-2022-2023-MaleRespPUFData.sas7bdat | CASEID, MARDAT01, CMINTVW, AGER, EVRMARRY, WGT2022_2023, MAREND01, RMARITAL, FMARITAL, FMARNO, MAR1DISS, ADDEXP, INTENT, EVBIOKID, NUMBIOKID, EVEROPER, RWANT, HIEDUC, FTFMODE |

MarriageNSFG renames each cycle's weight to `finalwgt`, and the male `biokids` to `numbiokid`.

**NCHS's documentation for every cycle: SAS setup programs.** `ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NSFG/sas/` has one per file for every cycle from 1982 to 2017–2019. For 2002 it's three files: Input, ValueLabel, VarLabel. Each gives:
- the layout (INPUT);
- the variable labels (LABEL);
- the value labels (PROC FORMAT);
- which labels go with which variable (FORMAT).

`ftp.../Datasets/NSFG/stata/` has Stata .dct and .do files from 2002. There are two styles:
- ICPSR's for 1982–1995: value labels prefixed "(code)"; 1982 reads a record type and keeps type 0;
- NCHS's own from 2002.

2015–2017 ships PROC FORMAT and FORMAT commented out, but they're complete. `~/pdt-nsfg/build/sas_setup.py` parses both styles: 741 (1982) to 5,754 (1995) variables per female file, almost all with labels and value labels.

**Findings so far:**
- **1982 F22_1CM (date of separation from the first husband).**
  - NCHS's setup program gives columns 622–628, which overlaps F21_1CM (619–622).
  - In the data the four-digit century months sit in 625–628 ("      9999"), and MarriageNSFG reads 625–628.
  - It looks like an error in the setup program; to verify and record as a correction (with evidence) before building that column.
- **1995 BDAYCENM** is columns 13–16, and MarriageNSFG reads 14–16. Column 13 is "0" in every record, so the values are the same.
- **1988's data file has no line breaks.** MarriageNSFG derives `1988FemRespDataLines.dat.gz` by cutting fixed-length records. pdt-nsfg will read NCHS's file as published, by record length.

**What MarriageNSFG does on top (for the switch, not records):**
- "make codes consistent with most recent cycles" (FMARITAL 3–6 → 2–5 in 1982–1995);
- marend01 recodes (1988: 1, 2, 3 → 3, 1, 2);
- -9000 / -90000 for "month unknown" century months;
- dividing ADDEXP by 10 and AGEBABY1 by 100;
- replacing 9797/9898/9999 with NaN;
- anycoll and bdegree from EDUCAT or HIEDUC ("Since we don't have hidegree in this cycle, we have to guess");
- rwant from WANTKID2;
- dropping divorce dates before the marriage date;
- 1988 cmmarrhx from firstcm or currentcm.

These stay in MarriageNSFG.

### 2026-11-20: built

`~/pdt-nsfg` 6715049. The repo is public on GitHub, so the coordinator reviews and pushes. `pdt check` gives 0 failures.

| Release | Tables | Documentation | Rows (female / male) |
|---|---|---|---|
| 1982 | female | SAS setup (ICPSR style; record type 0 only) | 7,969 |
| 1988 | female | SAS setup (fixed 3,553-byte records, no line breaks) | 8,450 |
| 1995 | female | SAS setup | 10,847 |
| 2002 | female, male | SAS setup (Input, ValueLabel, VarLabel) | 7,643 / 4,928 |
| 2006-2010 | female, male | SAS setup | 12,279 / 10,403 |
| 2011-2013 | female, male | SAS setup | 5,601 / 4,815 |
| 2013-2015 | female, male | SAS setup | 5,699 / 4,506 |
| 2015-2017 | female, male | SAS setup (PROC FORMAT and FORMAT commented out) | 5,554 / 4,540 |
| 2017-2019 | + MarriageNSFG's variables | ICPSR section codebooks (+ D, G; male B, F, H) | 6,141 / 5,206 |
| 2022-2023 | + MarriageNSFG's variables | NCHS codebooks | 5,586 / 4,371 |

**Totals:**
- 427 records;
- 174 links between consecutive releases;
- 51 inferred corrections;
- 72 unresolved codes in the source records: 51 blanks, all classified by those corrections, and 21 undocumented 2002 codes;
- 19 tables of common-format data, every round trip exact, 0.74 GB peak.

Row counts are NCHS's sample sizes.

**How the new releases are built** (build/sas_setup.py, build/build_slice.py, codebook_format `sas_setup`):
- the setup program gives each record's label and value labels; no question text and no counts;
- availability and counts come from the data (origin data_file);
- missing codes are typed from the labels by a new rule, `nsfg_missing_from_setup_labels` ("Date refused", "DK, don't remember", NCHS's typo "Data refused"), so the earlier releases' rule and records don't change;
- a quantity whose value labels cover only its special codes (1982 CMBIRTH: 9797, 9898, 9999) takes its valid range from the data; it isn't left with hundreds of unresolved codes;
- a `$` column (2002 CASEID) is stored as text.

**Findings:**
- **1982 F22_1CM's columns.** The setup gives 622-628; the data puts it in 625-628. Fixed in slice.yaml `layout_fixes`, with the evidence there and in the record's notes. A candidate for an NCHS report (Allen decides).
- **Blanks the setup programs don't label.** They're unresolved in the source records. 51 corrections (`confidence: inferred`, evidence: 2002's value labels and the 2017-2019 codebooks, which both label "." INAPPLICABLE) classify them `inap`.
- **2002's undocumented codes.** The data has codes neither 2002 setup program nor the Stata .do defines: RWANT 8/9, TIMESMAR 98/99, the century months' 9997-9999. They stay unresolved; NCHS's 2002 codebook (not fetched) may define them.
- **Links where documentation differs in kind.**
  - 2015-2017 (setup: labels only) to 2017-2019 (codebook: question text, universe): 0 rule links. The rule compares what each side documents, and they document different things.
  - The cycles from 2002 to 2015-2017 link well (28 to 40 per pair).
  - 1982 to 1995 links only a few (labels reworded between ICPSR cycles). No links are relaxed to compensate.
- **Spelling by release.** 2022-2023 spells MAR1DISS as `mar1diss`; names follow each release.

### The switch, as a plan (for a later session in MarriageNSFG)

Replace the per-cycle readers with one loader over pdt-nsfg's common-format files:

1. **A loader.** `load(release, table)` reads `nsfg-<release>-<table>.parquet` (pdt.data.read), rebuilds the publisher's values (pdt.data.rebuild), and sets missing codes to NaN with pdt.data.recode by type (refused, dk, no_answer, inap). That is what the readers' `replace([9797, 9898, 9999], np.nan)` and `replace([7, 8, 9], ...)` do now.
   - Unresolved codes (2002's 8/9, 98/99, 9997-9999) need an explicit decision in MarriageNSFG, as now. pdt warns when it meets them.
   - For 1982-1995, rename NCHS's names to MarriageNSFG's (the inventory table above: FINALWT→finalwgt, R7_CM→cmintvw, …). For 2006 on, the weight renames stay.
2. **What goes from MarriageNSFG:** the colspecs and fixed-width reading for 1982-1995; `read_stata_dct`, `read_resp` and the .dct files; `scripts/download_nsfg.py`'s NCHS fetches and the derived `1988FemRespDataLines.dat.gz`; the SAS7BDAT reads for 2022-2023.
3. **What stays:** every harmonizing recode listed above (FMARITAL 3-6 → 2-5, marend01 orderings, +9000/+90000 month-unknown adjustments, ADDEXP/10, AGEBABY1/100, anycoll and bdegree, rwant from WANTKID2, invalid divorce dates, 1988 cmmarrhx), `clean_resp`, `digitize_resp`, and the validate_* functions. These are MarriageNSFG's analysis choices.
4. **Prove it before switching:** for each cycle, compare the new loader's frame (after the same recodes) with the old reader's, column by column. Expected differences:
   - none for values (pdt-nsfg's round trip is exact; 1982 F22_1CM uses the same 625-628 MarriageNSFG reads; 1995 BDAYCENM's leading 0 doesn't change the value);
   - possibly NaN vs code where pdt types a code MarriageNSFG left as a number.
5. **Then** the extracts MarriageNSFG publishes (FemMarriageData.parquet) can be rebuilt from pdt-nsfg's, with their checksums compared.

**Runbook:** [`instructions/09-add-a-release.md`](../../instructions/09-add-a-release.md), for Task 76.

### 2026-11-20: follow-up, 2002's codes

At the coordinator's request, the 21 unresolved 2002 codes are resolved from NCHS's 2002 codebooks (`Cycle6Codebook-Female.pdf` and `-Male.pdf` on ftp.cdc.gov), added as sources, in `~/pdt-nsfg` e78ee1a.
- The build reads them as a supplement: only for codes the setup program doesn't label, with origin the codebook and missing types by the same label rule.
- All 21 are labeled there (2002's scheme: 9997 Not ascertained, 9998 Refused, 9999 Don't know; 8 Refused, 9 Don't know), and every count matches the data.
- Four 2002 blanks are labeled there too, so 47 inferred corrections remain (was 51).
- With the codes documented, 9 more 2002 → 2006-2010 links pass the rule: 183 links in all.
- `pdt check` gives 0 failures.

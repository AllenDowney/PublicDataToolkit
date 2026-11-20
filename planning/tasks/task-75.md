# Task 75 — pdt-nsfg: every cycle and variable MarriageNSFG uses

**Status:** `DOING (yellow)`: started 2026-11-20. Created by the coordinator, 2026-11-20, at Allen's request.

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

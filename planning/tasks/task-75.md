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

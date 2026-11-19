# Task 32 — A CPS-ASEC slice

**Status:** `DOING (yellow)` — started 2026-11-19 by the thread "yellow".

The CPS Annual Social and Economic Supplement (the March CPS) is run by the Census Bureau for BLS. It's on Allen's list from Twenge's *Generations*. The task: a slice of about 20–30 variables over recent years (at least 2019–2024, further back if the format holds), in a new local repo, `~/pdt-cps-asec`, made with the Copier template (`v0.1.0`), with the common-format data and `pdt check` at 0 failures, C3–C5 and C12 included. Use Census's own public-use files and documentation, not IPUMS (IPUMS extracts can't be redistributed).

**Variables:**
- design and weights: the person weight (MARSUPWT/ASECWT), household and family ids;
- demographics: age, sex, race, Hispanic origin, education, marital status;
- outcomes: personal and household income, poverty status, employment status, hours worked, living arrangements (living with parents).

Household, family and person are tables, with keys and references (STANDARD.md §2.1). Link variables across years, and record code histories (income topcodes, education recodes). Note the 2014 redesign of the income questions and the 2019 processing change.

**Files:** `~/pdt-cps-asec/` (new, no remote); this file; the Task 32 block on the board. A new reader module in `lib/pdt/` if one is needed.

## Progress

# Task 30 — A BRFSS slice

**Status:** `DOING (brfss)` (2026-11-19)

Assigned by the coordinator. A slice of the CDC's Behavioral Risk Factor Surveillance System (BRFSS), an annual adult telephone survey run by the states since 1984, in a new repo `~/pdt-brfss` made from the Copier template (`v0.1.0`). It's on Allen's high-priority list from Twenge's *Generations*.

1. Find the sources on cdc.gov: annual data files (SAS XPT), codebooks, calculated-variables documents, questionnaires, and module lists by state. Record what CDC says about terms.
2. Make `~/pdt-brfss` from the template. No remote; don't push.
3. Build a slice of about 20–30 variables over 2011–2023 (2011 added cell phones and new weighting; note how earlier years differ):
   - design: `_LLCPWT`, `_STSTR`, `_PSU`, `_STATE`, `IYEAR`;
   - demographics: sex, age group, race/ethnicity, education, income;
   - outcomes: general health, poor mental and physical health days, depression diagnosis, life satisfaction (where asked), binge drinking, smoking, BMI category;
   - one or two calculated variables, to test `derived_from` links.

   Link names and codes across years (by rule where the documentation is identical), and record code histories. Availability varies by state for optional modules.
4. `make data`, and `pdt check` with 0 failures, including C3–C5 and C12.
5. Write what BRFSS tests that earlier datasets didn't, and propose standard changes (don't make them).

**Files:** `~/pdt-brfss/`; this file; Task 30's block on the board.

## Progress

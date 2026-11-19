# Task 43 — The older repos and the new fields

**Status:** `DOING (yellow)` — started 2026-11-19 by the thread "yellow".

Bring the older dataset repos up to the fields added in cdae64a (from Task 32) and Task 39:
- **pdt-nsfg:** replace the `nsfg.item` extension with `questions[].number` (and drop it from EXTENSIONS.md); `flag_for` on the `*_I` imputation flags, with `variable_type: imputation_flag`; `design` in dataset.yaml (weights, strata SEST/VEST, PSU SECU, per release as needed). `values[].n` is already there (Task 35).
- **pdt-cps-asec:** `design` (weights; the replicate weights if the slice has them; a note on how CPS variance is estimated).
- **pdt-anes-cdf:** `design` (the VCF0009x/y/z weights, and the strata and PSU if the CDF has them). `kind` is already set.
- **pdt-fars:** `kind: administrative`, no design; check whether any flag variables need `flag_for`.

pdt-gss (blue) and pdt-yrbss (purple) get a one-line note about `design` and `number` instead.

In each repo: `make views`, `pdt check` 0 failures, commit.

**Files:** `~/pdt-nsfg`, `~/pdt-cps-asec`, `~/pdt-anes-cdf`, `~/pdt-fars`; this file; the Task 43 block on the board.

## Progress

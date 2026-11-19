# Task 43 — The older repos and the new fields

**Status:** `DONE (yellow)` 2026-11-19. The CPS-ASEC terms are the coordinator's to record (see the end).

Bring the older dataset repos up to the fields added in cdae64a (from Task 32) and Task 39:
- **pdt-nsfg:** replace the `nsfg.item` extension with `questions[].number` (and drop it from EXTENSIONS.md); `flag_for` on the `*_I` imputation flags, with `variable_type: imputation_flag`; `design` in dataset.yaml (weights, strata SEST/VEST, PSU SECU, per release as needed). `values[].n` is already there (Task 35).
- **pdt-cps-asec:** `design` (weights; the replicate weights if the slice has them; a note on how CPS variance is estimated).
- **pdt-anes-cdf:** `design` (the VCF0009x/y/z weights, and the strata and PSU if the CDF has them). `kind` is already set.
- **pdt-fars:** `kind: administrative`, no design; check whether any flag variables need `flag_for`.

pdt-gss (blue) and pdt-yrbss (purple) get a one-line note about `design` and `number` instead.

In each repo: `make views`, `pdt check` 0 failures, commit.

**Files:** `~/pdt-nsfg`, `~/pdt-cps-asec`, `~/pdt-anes-cdf`, `~/pdt-fars`; this file; the Task 43 block on the board.

## Progress

| Repo | Commit | What changed |
|---|---|---|
| pdt-nsfg | 5d024a8 | `nsfg.item` → `questions[].number` (the 2017-2019 codebook's item, or the 2022-2023 questionnaire's: BABYSEX is BC-6a); the link rule reads it there; the `babysex-item-extension` correction retired (the label correction stays); EXTENSIONS.md now empty. `flag_for` on HIEDUC_I and OUTCOME_I (rule `nsfg_flag_from_label`). `design` per release: WGT2022_2023/VEST/VECL (VECL added to the slice) and WGT2017_2019/SEST/SECU. Links unchanged (18). |
| pdt-cps-asec | 5b7b884 | `design` per table (HSUP_WGT, FSUP_WGT, MARSUPWT). The note: no strata or PSU in the public file; Census's 160 replicate weights (`asec_csv_repwgt_YYYY.csv` in the same zip, matched by h_seq and PPPOS, not in the slice), var = 4/160 Σ(θᵢ−θ₀)²; generalized variance parameters in the technical documentation. |
| pdt-anes-cdf | 03c9201 | VCF0009x (FTF) and VCF0009y (web) added beside VCF0009z (39 variables). `design`: the three weights; the CDF has no strata or PSU. The x/y system-missing values (all of 2020; one sample each in 2024) are `unresolved`, since the codebook lists no missing codes; `availability_added` entries can now name their own author. |
| pdt-fars | none | `kind: administrative` was already set. None of the 40 variables is a flag; FARS's imputed values (BAC) are in auxiliary files outside the slice. `pdt check` 0 failures. |
| pdt-gss, pdt-yrbss | none | One-line notes sent to blue and purple about `design` and `questions[].number`. |

In each changed repo: `make data` exact, `make views`, `pdt check` 0 failures.

**Not done here:** the CPS-ASEC terms. Allen decided everything ships, but the decision came relayed through the coordinator, and recording it writes "reviewed by Allen Downey" into dataset.yaml. The coordinator, who had it from Allen directly, applies it in pdt-cps-asec.

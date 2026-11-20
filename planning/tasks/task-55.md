# Task 55 — A Household Pulse Survey slice

**Status:** `DOING (purple)` — assigned by the coordinator on 2026-11-20.

The Census Bureau's Household Pulse Survey (HPS), an online survey of adults run every one or two weeks from April 2020 to 2024. Its questionnaire changed by phase, so it tests availability across many waves, rotating content, and links across phases. From [`planning/twenge_catalog.md`](../twenge_catalog.md).

1. Find the public-use files (PUFs), data dictionaries, questionnaires and technical documentation on census.gov, and record the Census terms. The decision stays open for Allen.
2. `~/pdt-pulse` from the template (`copier copy --vcs-ref v0.1.0`), no remote.
3. About 25 variables: demographics, the anxiety and depression items, food sufficiency, the weights, in every wave they appear. Replicate weights go in `design.replicates`, with `fay_factor` if Census's documentation gives it. Use `data_waves` if only some weeks' data are kept.
4. `make data` round trip; `pdt check` 0 failures.
5. Here: what the HPS tests, with proposals.

**Files:** `~/pdt-pulse/` (new, no remote); this file; the Task 55 block on the board.

## Progress

**Notes so far (purple, 2026-11-20), kept here in case of another crash:**
- `~/pdt-pulse` was made from the template (`2b00815`), with no remote.
- **Data:** www2.census.gov serves directory listings and files to urllib. The PUFs are under `/programs-surveys/demo/datasets/hhp/<year>/wkNN/` (2020 weeks 1–21, 2021 weeks 22–40, 2022 weeks 41–51, 2023 weeks 52–63) and `/2024/cycleNN/` (Phase 4.0–4.2, cycles 01–09).
  - Each cycle has `HPS_WeekNN_PUF_CSV.zip` (2024: `HPS_Phase4CycleNN_PUF_CSV.zip`, `HPS_Phase4-2Cycle09_...`) and a SAS zip.
  - A CSV zip holds a data dictionary (xlsx), the PUF and the person replicate-weight file. Week 1's household weights (`pulse2020_puf_hhwgt_01.csv`) are a separate file.
  - Out of scope: the 2024 "topical" files (October, December) and 2025's HTOPS files, which are a different design.
- **Documentation:** `/programs-surveys/demo/technical-documentation/hhp/`. It has a questionnaire per phase, a Source and Accuracy statement per cycle (some weeks missing), and user notes.
- **Variance method:** the Source and Accuracy statements say "Eighty replicate weights" and Var = 4/80 Σ(θᵢ − θ̂)². Phase 4.2 cycle 09 calls the method "successive difference replication", so `method: sdr`. Week 1 says only "replication methods". Phase 4.2 cites Judkins (1990), "Fay's Method for Variance Estimation", but states no Fay factor, so `fay_factor` is left out.
- **Dictionary format:** four rows per variable (Q#, name, Description, Question wording, Range), then Values, Universe and Internal Notes. Values are text lines "1) Not at all", and include -99 "Question seen but category not selected" and -88 "Missing / Did not report", outside the Range ("1:4"). The text has Excel's escaped carriage returns (`_x000D_`), a layout artifact.
- **Interruptions:** the download of all 72 CSV zips (about 5 GB) was interrupted twice by session crashes; it skips files already present. A headless fetch of census.gov's terms pages was killed (exit 137); run it under the memory cap.

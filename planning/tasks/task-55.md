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

### Result (purple, 2026-11-20)

`~/pdt-pulse` `7437145`. No remote; `pdt check` 0 failures; terms `unknown`, for Allen.

- **Releases:** 72, one per cycle: `week01`–`week63` (2020–2023) and `cycle01`–`cycle09` (2024, Phase 4.0–4.2). Each has two tables:
  - `puf`, the respondents, keyed by `SCRAM`;
  - `repwgt`, `SCRAM` plus PWEIGHT1–80, keyed by `SCRAM` and referring to `puf`.
- **Records:** 1,451 in `puf` and 5,904 in `repwgt` (7,355 in all). Each slice variable has a record in every cycle whose dictionary (or data) has it. EGENDER covers weeks 1–33 and EGENID_BIRTH week 34 to cycle 09. GENID_DESCRIBE and SEXUAL_ORIENTATION cover week 34 to cycle 07. PRIFOODSUF covers weeks 1–21 and HWEIGHT week 13 onward. The rest are in all 72.
- **Links:** 1,427, between consecutive cycles: 1,359 `same_item` only, and 68 with a change. Most links are made by rule `hps_same_name_same_dictionary`. Where Census's user notes state a change, the link cites them, quoting the note:
  - the mental-health battery's reference period, 7 days → two weeks (week 34);
  - INCOME, data year 2020 → 2021 (week 46);
  - Hispanic origin and race, combined (week 58) and split again (week 61);
  - the gender question replaced (week 61).
- **Design:** `design.replicates: {prefix: PWEIGHT, n: 80, method: sdr}`, with no `fay_factor`. The Source and Accuracy Statements say "successive difference replication" and Var = 4/80 Σ (θᵢ − θ̂)², and give no factor.
- **Data:** all 144 files (72 cycles × 2 tables) were written and round-trip exactly, one cycle per process under the memory cap, about 35 s each.
  - **Rebuild needed:** after orange's Task 58 lib changes are committed. The working tree's `pdt check` already asks each file for a "record of a verified round trip", so it skips the 142 files written before that change. Week 55, rebuilt since, passes C3–C5 and C12.
  - **Workaround to remove:** a `read_sas` workaround in `scripts/build_data.py`, once orange's fix is committed.

### What the HPS tests that earlier datasets didn't

1. **Many short releases.** Each of 72 cycles is its own file and dictionary, with no cumulative file. That makes 72 releases and 1,427 links between neighbours, most of them `same_item`. The views run to 6,297 files in `docs/` and 216 agent shards, and each cycle's 80 replicate-weight records are identical.
2. **Valid codes from a Range column.** Each dictionary gives a variable's Range ("1:4"), and lists -99 "Question seen but category not selected" and -88 "Missing / Did not report" among its Values, outside that range. The Range is how the publisher marks valid codes, so a code outside it is missing with the dictionary as its origin. Its types come by rule from the label (-99 → `skipped`, -88 → `no_answer`).
3. **Valid ranges that move:** TBIRTH_YEAR's top code moves each year (1932–2002 to 1935–2005), and THHLD_NUMPER's range goes from 1–10 (week 1) to 1–40 (week 13). The links call these `codes_changed`, but no code changed meaning.
4. **Dictionaries with gaps:**
   - Cycles 1–4's dictionaries omit CYCLE, which their data have; the records' origin is `data_file`.
   - The SAS dictionary of week 55 omits -88, because the SAS files store "did not report" as SAS's missing value `.`.
   - The gender question's replacement at week 61, which Census documents, doesn't show in the dictionaries, whose wording for GENID_DESCRIBE is unchanged.
5. **One file blocked.** www2.census.gov answers week 55's CSV zip with a "Request Rejected" page, to urllib and to a browser alike, so that week comes from its SAS zip. One dataset thus has two source formats, with different missing-value conventions.
6. **Changes stated in prose.** The user notes list changes in sentences. A link cites them with `origin: publisher`, the location, and the quote in `note`.
7. **Weights published later:** Phase 1's household weights (`hhwgt`) were made later and published as separate files beside the PUFs (Phase 3 user notes). That's a revision within a release, outside this slice.

### Proposals (not made; for the coordinator)

1. **Replicate weights without a record each.** `design.replicates` already names them (prefix and n). Let C3 accept a column covered by `design.replicates` without a record, or let one series record stand for all 80. Pulse has 5,760 identical replicate-weight records; PISA has 320.
2. **`range_changed`** as a link relation, for a valid range or top code that moves while every code keeps its meaning (TBIRTH_YEAR, THHLD_NUMPER). `codes_changed` overstates it.
3. **`evidence` on links,** like corrections have: a quote and a location as structure, not in `note`. Pulse's publisher-stated links carry the quote in `note` for now.
4. **Many-release datasets in the views:** for 72 releases, one page per variable per release is a lot. The views could collapse a variable's consecutive `same_item` releases into a run, as red's `pdt.chains` does for the catalog.
5. **A dataset whose releases differ in format.** Nothing needed. `data_source` with `format` already copes, and `sources.yaml` says why week 55 is SAS.

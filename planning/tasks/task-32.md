# Task 32 — A CPS-ASEC slice

**Status:** `DONE (yellow)` 2026-11-19. `~/pdt-cps-asec` (8f70e5b template, 343b0c8 slice); no remote, not pushed. Terms wait for Allen.

The CPS Annual Social and Economic Supplement (the March CPS) is run by the Census Bureau for BLS. It's on Allen's list from Twenge's *Generations*. The task: a slice of about 20–30 variables over recent years (at least 2019–2024, further back if the format holds), in a new local repo, `~/pdt-cps-asec`, made with the Copier template (`v0.1.0`), with the common-format data and `pdt check` at 0 failures, C3–C5 and C12 included. Use Census's own public-use files and documentation, not IPUMS (IPUMS extracts can't be redistributed).

**Variables:**
- design and weights: the person weight (MARSUPWT/ASECWT), household and family ids;
- demographics: age, sex, race, Hispanic origin, education, marital status;
- outcomes: personal and household income, poverty status, employment status, hours worked, living arrangements (living with parents).

Household, family and person are tables, with keys and references (STANDARD.md §2.1). Link variables across years, and record code histories (income topcodes, education recodes). Note the 2014 redesign of the income questions and the 2019 processing change.

**Files:** `~/pdt-cps-asec/` (new, no remote); this file; the Task 32 block on the board. A new reader module in `lib/pdt/` if one is needed.

## Sources

Everything is on www2.census.gov, which serves scripts (curl and urllib), so nothing needs a manual download. Per ASEC year, under `https://www2.census.gov/programs-surveys/cps/datasets/<year>/march/`:

| File | What it is | In sources.yaml |
|---|---|---|
| `asecpubYYcsv.zip` | `hhpubYY.csv`, `ffpubYY.csv`, `pppubYY.csv`, and the replicate weights (147–184 MB) | yes, kind data |
| `asecYYYY_ddl_pub_full.pdf` (2019: `06_ASEC_2019-Data_Dictionary_Full.pdf`; 2020: `ASEC2020ddl_pub_full.pdf`) | the data dictionary: name, length, position, range, label, values, universe | yes, kind codebook |
| `../../techdocs/cpsmarYY.pdf` | technical documentation, with the questionnaire facsimile | yes, kind other |
| `hhldfmt.txt`, `famlfmt.txt`, `persfmt.txt` | name, width, position and range per variable; no labels | downloaded, not used |
| `asecYYYY_pubuse.zip`, `asecpubYYsas.zip`, `CPS_ASEC_ASCII_REPWGT_YYYY.*` | the fixed-width file, SAS files, replicate weights | not used |

The split CSVs start in 2019. Before that, each year is one hierarchical fixed-width file (see below). 2025 is out, so the slice covers 2019–2025: 7 releases.

**Terms.** Not decided; all four fields are `unknown` in `dataset.yaml`, which blocks shipping but not local builds. What I found, for Allen to decide:
- The ASEC pages state no restriction on use or redistribution. The files are federal works (17 U.S.C. §105).
- Census's data API terms (https://www.census.gov/data/developers/about/terms-of-service.html) carry the Title 13 obligations: don't use the data to identify anyone, don't link it to identify anyone, and report an inadvertent identification. They're the closest statement to a use agreement.
- Citation guidance: https://www.census.gov/about/policies/citation.html.

## What was built

`~/pdt-cps-asec`, from the template v0.1.0 (Copier 9.19.1):

- **32 variables in 3 tables, for 7 releases: 224 records.**
  - household (6): H_SEQ, H_YEAR, GESTFIPS, HSUP_WGT, H_NUMPER, HTOTVAL;
  - family (7): FH_SEQ, FFPOS, FKIND, FPERSONS, FTOTVAL, FPOVCUT, FSUP_WGT;
  - person (19): PH_SEQ, P_SEQ, PF_SEQ, A_LINENO, MARSUPWT, A_AGE, A_SEX, PRDTRACE, PEHSPNON, A_HGA, A_MARITL, A_EXPRRP, PEPAR1, PEPAR2, PEMLR, HRSWK, PTOTVAL, PEARNVAL, PERLIS.
  - The person weight is MARSUPWT in these files; ASECWT is the IPUMS name.
- **Keys and references**, all of which hold in the 2025 data:
  - household `[H_SEQ]`; family `[FH_SEQ, FFPOS]` → household; person `[PH_SEQ, P_SEQ]` → household and → family `(FH_SEQ, FFPOS)`;
  - two references within the person table: `(PH_SEQ, PEPAR1)` → `(PH_SEQ, A_LINENO)` when PEPAR1 is 1–16, and the same for PEPAR2. This is what "living with parents" rests on: 38% of 18–34-year-olds in 2025 have a parent in the household (unweighted).
- **`build/census_dictionary.py`** parses the two-column dictionary PDF by converting each half page separately. **`build/build_records.py`** has three rules:
  - `cps_dictionary_values`: codes become `values`; ranges, "Min Value"/"Max Value" pairs, "1 hour ... 99 = 99 hours plus" and values described in words ("negative amt = income (loss)") become `valid_range`, with the labels in its note;
  - `cps_missing_from_labels`: "NIU"/"Not in universe" become `inap`, "Noninterview household" becomes `not_asked`, and nothing else is missing;
  - `cps_identical_dictionary` for links.
- **Every code in every year's data is in its dictionary** (C4 in the build report: none to look at).
- **`scripts/build_data.py`** writes 21 common-format files with the shared `read_csv_zip` and `zip_member` (2019's zip keeps its CSVs in a folder). No new reader was needed. `scripts/extract.py` is as in the other repos.

## Links and code histories

As the coordinator decided: no `histories.jsonl`, because Census prints no multi-year matrix. Links between consecutive years come from rule `cps_identical_dictionary` 0.1, which compares the two dictionaries' entries (range, label, universe, codes and their labels, ignoring case and spacing). `labels_changed` means the variable's label or a shared code's label changed, not just that a code was added. There are 192 links: 189 `same_item` and 3 with changes.

| Variable | Years | Relations | What changed |
|---|---|---|---|
| FPOVCUT | 2019 → 2020 | codes_changed, labels_changed, universe_changed | NIU 0 became -1; the label went from "Poverty cutoff dollar amount" to "ANNUAL FAMILY POVERTY THRESHOLD"; the universe from "All Families" to all families and unrelated individuals |
| PERLIS | 2019 → 2020 | codes_changed, universe_changed | -1 "NOT IN POVERTY UNIVERSE" added, and the universe changed |
| FPOVCUT | 2021 → 2022 | codes_changed | the range widened from (−1:60000) to (−1:99999) |

No income top codes or education recodes change in 2019–2025. A_HGA's codes 31–46 are stable, and A_AGE top-codes at 80 ("80-84") and 85 ("85+") every year. The income totals (PTOTVAL, HTOTVAL, FTOTVAL) aren't top-coded. Census top-codes and swaps the income *components*, with a flag for each (e.g. "Topcode flag for HCHCARE_VAL", "Data swapping flag for HPROP_VAL").

## The 2014 redesign and the 2019 processing change

From the 2025 technical documentation (`cpsmar25.pdf`, pp. 9–10), also in the repo's README:
- **2014:** "the ASEC questionnaire was redesigned to incorporate new income and health insurance questions." Health insurance estimates for 2014–2017 aren't comparable with earlier years. For income and poverty, Census adjusts historical estimates where the change was significant.
- **2019:** "An updated data processing system was implemented beginning with data year 2018 estimates" (the 2019 ASEC). It brought edits for same-sex couples, new editing of income and health insurance, and new imputation. The 2017 and 2018 legacy files aren't directly comparable with 2019 on; the 2018 Bridge File and the 2017 Research File connect them.

The slice starts at 2019, after both breaks, so neither falls inside it.

## Extending before 2019

Not built. It would take:
1. **A reader for the hierarchical fixed-width file** (`asecYYYY_pubuse.dat.gz`). One file holds every record. The first character is the record type (1 household, 2 family, 3 person), and each type has its own positions. The reader would split rows by type and give each table its columns: a new module, `lib/pdt/readers_hierarchical.py` or similar.
2. **A parser for the text dictionary** used through 2018 (`08ASEC2018_Data_Dict_Full.txt`, `asec2016_pubuse.dd.txt`): lines `D NAME length position (range)`, `U universe` and `V code .label`. It's easier to parse than the PDF.
3. **Releases for years with several files:** 2014 has two (`asec2014_pubuse_3x8_rerun_v2` and `asec2014_pubuse_tax_fix_5x8_2017`), and 2016 has `_v3`. Each would be a release, or the latest a release and the others noted.
4. **Links across the 2018/2019 break**, where the processing system changed. The 2018 Bridge File is a separate file, and a candidate release of its own.
5. **Ranges and names change further back** (H_NUMPER is (00:39) in 2018 and (0:16) from 2019), so expect more `codes_changed` links.

## What the CPS-ASEC tests that the earlier datasets didn't

1. **Two time dimensions.** A release is a collection year (ASEC 2024), but income, poverty and work experience describe the year before. The standard has one wave dimension; the README and `dimensions.wave.note` say this in prose.
2. **Scaled values.** Weights are stored as integers with two implied decimals. Nothing in a record says so except a note.
3. **References within a table, with conditions.** A person's PEPAR1 points to another person in the same household. The schema handled it (`table: person`, `target_columns`, `when`) with no change, and C12 checks it.
4. **Hierarchical files** before 2019 (not built).
5. **Valid values described in words**, "Min Value"/"Max Value" pairs and "1 ... 99 = 99 hours plus", in a two-column PDF. Each needed a rule, and the result lives only in `valid_range.note`.
6. **Noninterviewed units as rows.** The household file has noninterviewed households, with no persons (H_NUMPER 0, typed `not_asked`), so a household count from the file isn't a count of interviewed households.
7. **No don't-knows or refusals.** Census imputes them, with allocation flags (`I_*` variables), and top-codes and swaps income components, with flags. The standard has no way to say "this variable is the imputation flag for that one", except `variable_type: imputation_flag`.
8. **No question text in the dictionary.** The questionnaire facsimile is in the technical documentation's Appendix E; 224 of 224 records have no `questions`.
9. **A documented release a year, with no crosswalk.** The links are all by rule, like the NSFG's.

## Proposals for the standard (not made)

- **A reference-period field** on a release (or a second time dimension), e.g. `reference_period: {from: 2023-01-01, to: 2023-12-31}` for ASEC 2024, so a tool can tell collection year from income year.
- **`scale` (or `implied_decimals`) on a record**, so `pdt.extract` can divide weights and amounts by 100, and the views can show 2552.12 rather than 255212.
- **`flag_for`** (or a link relation) **from an allocation, top-code or swapping flag to its variable**, generalizing `variable_type: imputation_flag`. The NSFG's `*_I` variables would use it too.
- **Labeled points inside a valid range**, such as A_AGE's 80 "80-84 years of age" and 85 "85+ years of age", HRSWK 99 "99 hours plus" and AGEPREG's ranges. These are top codes, and `valid_range` only has a note for them.
- **`item` as a standard field** rather than an extension: `cps.item` and `nsfg.item` are the same thing (EXTENSIONS.md).
- **Row universes on tables**: a table could say some rows aren't interviews (the ASEC household file's noninterviews), the way a reference can say `when`.

## Checks

| Check | Result |
|---|---|
| `make data` | 21 files (7 releases × 3 tables), every round trip exact; local only while `terms.data` is `unknown` |
| `pdt check` | 0 failures; C3–C5 run on all 21 files; C8 current after `make views` |
| C12 keys | unique and non-blank in all 21 files |
| C12 references | **skipped by `pdt check`** (see below); checked by hand instead: all 5 references hold in all 7 years (e.g. 2025: 64,529 families, 142,125 persons, and 44,713 and 35,839 parent pointers, all matched) |
| `pdt diff` on the 6 consecutive pairs | agrees with the links, except as below |

**Found while checking:**
- **C12 ignores `target_columns`.** `check_keys_in_data` looks for a reference's `columns` in the target table (`[c for c in cols if c not in target]`, `target[cols]`), so a reference whose target columns have other names (every CPS reference: `FH_SEQ` → `H_SEQ`, `(PH_SEQ, PEPAR1)` → `(PH_SEQ, A_LINENO)`) is reported as skipped. The fix: `tcols = ref.get("target_columns", cols)`, then check `tcols` in the target and build `have` from `target[tcols]`. `check.py` isn't this task's file; sent to the coordinator.
- **`pdt diff` doesn't compare `valid_range`.** It calls FPOVCUT 2021 → 2022 `same_item`, but the range widened from (−1:60000) to (−1:99999). Sent to the coordinator for red.
- **`pdt diff` found that my rule missed universe changes**, and counted an added code as `labels_changed`. Fixed before commit: FPOVCUT and PERLIS 2019 → 2020 now have `universe_changed`, and PERLIS has no `labels_changed`.

## Follow-up: the new fields (cdae64a, c9450dc)

The coordinator adopted four proposals. Applied in pdt-cps-asec (cbe4110):
- **`flag_for`**: 9 allocation flags joined the slice, one for each person variable that has one: AXAGE, AXSEX, AXHGA, PXRACE1, PXHSPNON, PXMARITL, PXPAR1, PXPAR2 and I_HRSWK. `flag_for` and `variable_type: imputation_flag` come from the label "Allocation flag for X" (rule `cps_flag_from_label`). PXPAR2's entry says only "Same as PXPAR1", so its codes are copied from PXPAR1's, and the provenance says so. The flags' codes keep what the main variables lose: "Blank – no change", "Don't know – no change", "Refused – no change". The income totals have no flags; their components do.
- **`implied_decimals: 2`** on HSUP_WGT, FSUP_WGT and MARSUPWT, from the dictionary's "2 implied decimals (example: 255212=2552.12)".
- **`reference_period`** on each release: the calendar year before the ASEC year, with a note that demographics are as of the February–April interview.
- **`questions[].number`**: A_HGA has the question quoted in each year's technical documentation (glossary, "Level of School Completed/Degree Received"), with number "18h" from the dictionary. The `cps.item` extension is gone. **pdt-nsfg should switch `nsfg.item` to `questions[].number` too**; red owns pdt-nsfg now.
- **Labeled points in a range**: HRSWK's 1 ("1 hour") and 99 ("99 hours plus") are now values as well as the ends of the range, as A_AGE's 80 and 85 already were.

Now 41 variables, 287 records, 246 links (243 `same_item`). `make data`: 21 files, every round trip exact. `pdt check`: 0 failures, after c9450dc added the two fields to `provenance.fields`.

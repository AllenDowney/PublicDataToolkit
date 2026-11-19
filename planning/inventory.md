# Inventory of the GSS, ANES and NSFG work

Task 3 on the [project board](../PROJECT_BOARD.md). This file records what already exists in the CultureWar, GssExtract, ExtractANES and MarriageNSFG repos, so the plan (Task 1) can decide what to generalize. Everything was read on 2026-11-19 and nothing in those repos was changed.

Each piece gets: path, what it does, inputs and outputs, whether it is generic or specific to CultureWar's analysis, what an agent would need to repeat it for a new dataset, and the problems noticed. "Generic" means the step belongs in the toolkit's instructions or skills. "Ours" means it is an analysis decision that stays in CultureWar.

What was not read: the Pew pieces (`CultureWar/notebooks/external/pew_ingest.py`, `notebooks/pew_extract.py`), `scripts/where_used.py`, `notebooks/utils.py`, `notebooks/survey_weights.py`, `notebooks/religion_coding.py`, the ExtractANES notebooks other than their names, the GssExtract notebooks other than `make_generic_extract.md`, and `MarriageNSFG/nsfg/marriage.py`. The JSON files were sampled, not read in full.

## 1. GSS codebook layer (`CultureWar/codebook/`)

### 1.1 Files at a glance

| Path | What it does | Generic or ours |
|---|---|---|
| `codebook/convert_gssrdoc_to_json.R` | Loads `gss_doc` from Kieran Healy's gssrdoc package and writes five JSON views of it | Generic step, GSS-specific source |
| `codebook/extract_codebook.py` | Parses the NORC 2024 codebook PDF with pdfplumber and regex | Generic step, superseded for the GSS |
| `codebook/explore_codebook.py` | Prints page text and tables from the first pages of the PDF, to learn its layout | Generic (a "look before you parse" probe) |
| `codebook/examine_variable.py` | Finds the PDF page for one variable (`RACOPEN`) and prints its text | Generic probe |
| `codebook/codebook_plan.md` | Inventory of the four NORC PDFs and a phased extraction plan (structured data, then index, then Python helpers) | Generic as a template |
| `codebook/gssrdoc_evaluation.md` | Compares gssrdoc JSON with the PDF extraction and recommends which file to use for what | Generic as a template |
| `codebook/gssrdoc_issue_draft*.md` | Errata drafts; the first was filed upstream as kjhealy/gssrdoc#1 (`racschol`, `racopen`, `racfew`, `rachaf`) | Generic (errata record) |
| `codebook/ReadMe.txt` | NORC's own readme, pointing at the "Suspected Issues in the GSS" PDF | Publisher file |
| `codebook/*.pdf` | NORC 2024 Codebook R2, Release Variables, What's New, Release Notes 7224 | Publisher files, gitignored by `*.pdf` |

### 1.2 `convert_gssrdoc_to_json.R`

- Input: `gss_doc.rda` from a local clone of gssrdoc, at a hard-coded path. gssrdoc scrapes the GSS Data Explorer. The tibble has list columns `var_yrtab`, `yrballot_df`, `module_df`, `subject_df`.
- Outputs, written to `extracted/` relative to the working directory, 6,904 variables each:

| File | Shape | Fields |
|---|---|---|
| `gssrdoc_full.json` | list | `variable`, `description`, `question`, `value_labels`, `var_yrtab_json`, `yrballot_df_json`, `module_df_json`, `subject_df_json`, `norc_id`, `norc_url` (nested data as JSON strings) |
| `gssrdoc_simple.json` | list | `variable`, `description`, `question`, `value_labels`, `years_available`, `ballot_info`, `modules`, `subjects`, `norc_id`, `norc_url` |
| `gssrdoc_dict.json` | dict of one-element lists | same as simple |
| `gssrdoc_dict_flat.json` | dict keyed by lowercase name | same as simple; the file the extract builder uses |
| `gssrdoc_minimal.json` | dict | `variable`, `question`, `value_labels`, `years_available` |

- Sample (`abany` in `gssrdoc_dict_flat.json`): `value_labels` is one string, `"[1] yes / [2] no / [NA(d)] don't know / [NA(i)] iap / ..."`; `years_available` is `"1972, 1973, ..."`; `ballot_info` is `"year=1977; ballots=-/-; availability=full | ..."`; `norc_url` is `https://gssdataexplorer.norc.org/variables/607/vshow`.
- Gotchas:
  - The script depends on that local clone, which wasn't available, so it cannot be rerun as is. The five outputs are gitignored (`codebook/extracted/gssrdoc_*.json`), so a fresh clone of CultureWar has no GSS catalog and `make run_gss_extract` would fail at `load_gss_catalog()`.
  - The output directory is relative to the CWD, so it must be run from `codebook/`.
  - Everything structured is flattened to strings: value labels, years, ballots. Consumers re-parse them with regex.
  - The `NA(...)` tokens are not per-variable. In `gssrdoc_dict_flat.json`, 6,898 of 6,904 variables carry the same list of ten tokens (`NA(i) iap`, `NA(m) dk, na, iap`, `NA(n) no answer`, `NA(p)`, `NA(r)`, `NA(s) skipped on web`, `NA(u)`, `NA(x)`, `NA(y)`, `NA(z)`), so they say which Stata extended-missing codes exist in the file, not which ones apply to this item. Only `NA(d)` varies ("don't know" in 6,033, "can't choose" in 865).
  - 185 variables have no `years_available`; one has no question.
  - Five derived files are four views too many; the evaluation already marks two as "optional" and one as "not recommended".
- Agent needs: a skill for "an upstream metadata package already exists: convert it to the standard record", including how to pin the upstream version (commit or release) and record it as provenance.

### 1.3 `extract_codebook.py` (PDF parser) and its probes

- Input: `codebook/GSS 2024 Codebook R2.pdf` (hard-coded, same directory). Requires `pdfplumber`.
- Method: walks pages; a page with `Variable: NAME Type: ...` starts a new variable and text accumulates until the next one. Regexes pull `Label:`, `Notes:`, the value table (`LABEL VALUE COUNT PCT`), and the `RESERVED CODES:` block.
- Outputs (477 variables, uppercase names):

| File | Fields |
|---|---|
| `extracted/variables.json` (dict) | `name`, `type`, `label`, `notes`, `values` [`value`, `label`, `count`, `pct`], `reserve_codes` [`code`, `label`, `count`, `pct`] |
| `extracted/variables_list.json` (list) | `variable` plus the same fields |
| `extracted/variables_summary.csv` | `Variable`, `Type`, `Label`, `Num Values`, `Num Reserve Codes`, `Has Notes` |

- Strength: the only GSS source that keeps reserve codes separate (`D` don't know, `N` no answer, `I` IAP, `S` skipped) with 2024 frequencies.
- Gotchas: only the first `Variable:` match on a page starts a record, so a page with two variables merges them; `Label:` stops at the first newline, so long question text is cut; counts and percents are strings; only one release (2024) is covered. `explore_codebook.py` and `examine_variable.py` are throwaway probes with a hard-coded target variable.
- Agent needs: a PDF-codebook skill with a probe step (print sample pages, find the record delimiter), a parser template, and a coverage check against the data file's variable list. Natural PDF (Jonathan Soma) or `pdftotext -layout` (as in NSFG) are alternatives to regex over pdfplumber text.

### 1.4 Planning and errata documents

- `codebook_plan.md` lists each publisher document with type, likely contents and priority. Phase 2 (topic index) and Phase 3 (`get_variable_info`, `search_variables`) were planned and not built as such; `notebooks/utils.py` took over some of it. The "What's New" and Release Notes PDFs were never extracted, so release-to-release changes are not captured anywhere in structured form.
- `gssrdoc_evaluation.md` is a good model for a "which source and which file for which question" page.
- The two issue drafts are the only errata records. Each names the variable, quotes the bad text, gives the corrected text, cites a source (GSS Data Explorer URL or a paper), and says when the fix is an inference rather than verified (`racfew`). That is close to a correction-record schema already: variable, field, wrong value, corrected value, source, confidence, upstream issue link, status (filed or not).
- Gotcha: corrections live only in markdown and in hand-edited `question` text in `variables.yaml`. No machine-readable corrections file overrides the catalog.

## 2. ANES codebook layer

### 2.1 `ExtractANES/codebook/extract_cdf_codebook.py`

- Inputs: `ExtractANES/codebook/ANES TIME SERIES CUMULATIVE DATA FILE 1948-2024 VARIABLE CODEBOOK.html` (a pandoc-generated HTML codebook dated 2026-02-05, committed to ExtractANES) and `data/raw/anes_timeseries_cdf_stata_20260205.dta.gz` (Stata header only: variable labels and value-label sets). Run with `make extract_codebook`.
- Method: regex over the HTML for each `VCFnnnn` header table, then for sections `Question`, `Valid`, `Missing`, `Notes`, `Weight`, `Sources`. Missing codes are the numbers that start lines in the `Missing` section. `years_available` comes from `YYYY:` patterns in `Sources`. The Stata file supplies the authoritative variable list, short labels and value labels.
- Outputs in `codebook/extracted/`, 1,030 entries:

| File | Fields |
|---|---|
| `anes_cdf_minimal.json` (dict) | `variable`, `label`, `question`, `value_labels`, `missing_codes` (list of int), `valid_range` (e.g. `"1-9"`), `years_available`, `notes` |
| `anes_cdf_dict.json` (dict) | the minimal fields plus `label_html`, `valid_text`, `missing_text`, `weight`, `sources`, `value_labels_dict` |
| `anes_cdf_summary.csv` | `variable`, `label`, `question` (truncated 120), `valid_range`, `missing_codes`, `years_available`, `has_notes`, `n_value_labels` |

- `validate()` prints counts (Stata vs HTML variables, how many have question, missing codes, years) and spot-checks four variables. It reports and never fails.
- The minimal schema was designed to be "GSS-compatible" (same `value_labels` string format), which is why one regex family handles both.
- Gotchas:
  - The script and `anes_cdf_dict.json` stayed in ExtractANES; only `anes_cdf_minimal.json` and the CSV were copied to `CultureWar/codebook/extracted/` (by `make sync_culturewar_codebook`). The two copies are byte-identical today. CultureWar cannot rebuild its own ANES catalog.
  - Uses the private `StataReader._varlist` and `_lbllist`, which can break with a pandas upgrade.
  - Where the HTML came from is not recorded (no URL or download step). `data_watch_plan.md` notes that electionstudies.org returns 403 to `curl`.
  - `valid_range` takes min and max over listed codes, so it includes DK codes inside the range: `VCF0803` gets `"1-9"` where 9 is "DK; haven't thought much about it", and `missing_codes` is `[0]` only.
  - 264 entries have no missing codes and 69 have no `years_available`.
- Agent needs: an HTML-codebook skill (find the per-variable block, map section names to fields), plus a rule to join codebook text with the data file's own labels and to report codebook-only and data-only variables.

### 2.2 ANES documentation in `CultureWar/codebook/`

| Path | What it is | Generic or ours |
|---|---|---|
| `anes_pilot_panel_extracts_inventory.md` | How the Pilot and Panel extracts relate to the CDF; rebuild commands, HDF key, conventions (thermometers 0–100, codes `< 0` to NaN, per-wave weights) | Mixed: the study-family map is generic, the "book VCF" naming is ours |
| `anes_pilot_panel_harmonization.md` | Living checklist of polarity flips and caveats (H and W items) across Pilot and Panel waves | Generic pattern (harmonization log) |
| `anes_midterm_coverage.md` + `anes_midterm_year_matrix.csv` | Which book variables exist in midterm years; matrix fields `variable`, `label`, `n_nonmiss`, `n_waves`, `first_year`, `last_year`, `years_data`, `midterms_in_extract`, `midterms_in_catalog`, `midterms_catalog_not_in_extract_data`, `catalog_years_available` | Generic idea (catalog availability checked against data availability), ours in scope |
| `extracted/anes_extract_notes.md` | Per-column decisions for the CDF extract (`cohort = year - age`, top-coded ages, VCF0103 vs cohort) | Ours, but the format (column, source, type, derivation, caveats) is a good template |

- Gotchas: `anes_midterm_coverage.md` cites `codebook/extracted/anes_variables.csv`, which does not exist, and a questionnaire PDF outside the repo.
- The midterm matrix is the only place where catalog `years_available` was checked against the data. That check is worth making a standard validation step.

## 3. Extract builders

### 3.1 `CultureWar/notebooks/gss_extract/` (missing-code detection)

- `paths.py` points at `codebook/extracted/gssrdoc_dict_flat.json`. `catalog.py` provides `load_gss_catalog`, `parse_value_label_parts`, `numeric_codes_from_entry`, `missing_codes_for_var`, `substantive_codes_for_var`, `recode_values_to_nan`, `recode_gss_columns`. Tested by `notebooks/test_gss_extract_catalog.py` (not read).
- Method: split `value_labels` into `(code, label)` pairs, skip `NA(...)` tokens, skip labels starting with yes/no, and flag a numeric code as missing when its label matches `dk|don't know|refused|no answer|iap|inap|skipped|not imputable|uncodeable|not available|see codebook|can't choose|cannot choose|not asked|no post iw|don't have a job`.
- Generic: yes, as a fallback when the publisher does not mark missing codes.
- Gotchas:
  - All matched codes become one NaN, so DK, refused, IAP and "can't choose" are no longer distinguishable. The PDF parser kept them apart (`reserve_codes`); this path throws that away.
  - The yes/no guard skips real missing codes whose label starts with "no": 7 cases in gssrdoc, e.g. `adhdknow` code 3 "no answer", `freeexp1` code 98 "no answer dont know", `exptext` code 9.
  - It depends on Stata extended missing values (`.d`, `.i`, ...) already being NaN when read with `convert_categoricals=False`; the regex only catches leftover numeric codes. That assumption is GSS-specific and undocumented.
  - Out-of-universe codes that the regex cannot see are patched by hand in `make_gss_extract.py` (`EXTRA_MISSING_CODES`: `racchurh` 3, `racwork` 6, `racchng` 3).

### 3.2 `CultureWar/notebooks/make_gss_extract.py` (937 lines)

- Input: `../data/raw/gss7224_r3a.dta.gz` (NORC cumulative Stata file; path relative to `notebooks/`). Release and year parsed from the file name pattern `gss72{YY}_r{release}`.
- Outputs: `gss_extract_2024_r3a.hdf` (key `gss`) and `gss_extract_2024_r3a_interviewer.hdf`; log `logs/extract_{year}_r{release}.txt`; diagnostics such as `tables/extract/marsame_inventory.csv`.
- Steps: select `BASE_COLUMNS` + `OPTIONAL_COLUMNS` (a hand list), warn on missing columns, `year` to float, merge `marsame1` into `marsame`, catalog missing recode, extra missing codes, derive `race_eth4`/`race_eth5`, religion, segregation and stereotype columns, weights (`wtsmerge`, within-year normalization), then the interviewer extract (drop 2021 and web respondents in 2022/2024, rake to margins).
- Generic: reading, column selection with a missing-column report, release parsing from the file name, catalog recode, the log file. Ours: the column list, `marsame` merge, race/ethnicity and religion derivations, weighting and mode decisions (plan §3 says the same).
- Gotchas: CWD-relative paths (`logs/`, `../data/raw`); imports from sibling modules (`religion_coding`, `survey_weights`, `utils`) so it only runs from `notebooks/`; `git_commit=True` runs `git add -f`, `git commit` and `git push` through `os.system`; the output is gitignored and not published anywhere.

### 3.3 `CultureWar/notebooks/anes_extract/`

| Module | Input | Output | Notes |
|---|---|---|---|
| `paths.py` | — | — | Hard-codes release stems: `anes_timeseries_cdf_stata_20260205`, `anes_mergedfile_2016-2020-2024panel_20260519.sav` |
| `catalog.py` | `anes_cdf_minimal.json` | — | Missing codes = catalog `missing_codes` plus codes whose label matches `\b(DK\|RF\|INAP)\b` or a bare `NA`; thermometer rule (outside 0–100 or listed codes); `harmonize_vcf0878_adopt` (5 to 2) |
| `cleaning.py` | — | — | `clean_thermometer` (outside 0–100 to NaN), `clean_scale` (`< 0` to NaN) |
| `cdf.py` | CDF `.dta.gz` | `notebooks/anes_extract_<stem>.hdf` (key `anes`) + `_labels.csv` (`variable`, `label`) + log | Column lists are chapter allowlists (`THERMOMETER_ALLOWLIST`, `ATTITUDE_COLUMNS`), renames to `year`, `age`, `sex`, ...; turnout derivations |
| `timeseries.py` | single-year Time Series `.dta` 2012–2024 | fills columns in the CDF frame | Joins on `VCF0006` = study case ID; raises if the CDF already has the value, so the supplement is dropped when the CDF catches up |
| `pilot.py` | Pilot `.dta`/`.sav` 2016–2022 | `anes_pilot_extract.hdf` + labels | Per-year `PILOT_SPECS` maps source columns to CDF names; coalesces split-form columns |
| `panel.py` | merged panel `.sav` | `anes_panel_extract.hdf` + labels | Wide to long, per-wave `WAVE_SPECS`; polarity fix for bathroom item |

- Generic: the pattern of a per-study crosswalk (source column per year or wave mapped to one harmonized name with a recode dict), the "supplement until the cumulative file catches up" check in `timeseries.py`, labels CSV next to the data, and per-run logs. Ours: every column list.
- Gotchas:
  - Same DK/RF/INAP collapse into one NaN as the GSS path.
  - `recode_values_to_nan(..., drop_negatives=True)` and `clean_scale` assume negative codes are always missing, which holds for recent ANES but is a convention, not something read from the codebook.
  - `catalog.log_and_print` finds its log file by inspecting the caller's globals (`debug_log`), which is fragile.
  - `cdf.py` imports `survey_weights` as a top-level module, so it only runs with `notebooks/` on `sys.path`.
  - Which copy is the source of truth for the CDF builder is ambiguous: the CultureWar README says it was "ported" from ExtractANES on 2026-09-15, and ExtractANES still has its own copy.

### 3.4 `GssExtract` (older GSS extract repo)

- Cookiecutter Data Science layout. The package directory is `gss-extract/` (hyphen), while the Makefile's `data`, `lint` and `format` targets point at `gss_extract/`, so those targets cannot work; `gss-extract/data/make_dataset.py` is a 30-line template stub. `notes.txt` records this very lesson ("don't put a hyphen in project_name").
- The real work is six jupytext notebooks (`notebooks/make_*_extract.md`), each reading a `gss72YY_rN.dta(.gz)` with `pd.read_stata(convert_categoricals=False)` and writing `data/interim/gss_<name>_<year>_r<release>.hdf`. No codebook-based missing recode; `utils.fill_missing` replaces `[98, 99]` with random draws, and `utils.read_gss` downloads an old `GSS.dct`/`GSS.dat.gz` from GitHub.
- Downstream repos fetch the extracts by URL. `GSSEXTRACT_DOWNLOAD_CATALOG.md` lists the consumer repos and the file names they depend on.
- `CONSOLIDATION_PLAN.md` and `notebooks/NOTEBOOK_INVENTORY.md` inventory notebooks by input file, output file and columns. Last commit 2026-02-06.
- Lessons: the download catalog shows the cost of unversioned file names (`gss_pacs.hdf`) and the value of `{name}_{year}_r{release}`. A GitHub release with checksums is the better way to publish extracts.

### 3.5 `ExtractANES` (older ANES extract repo)

- Same template, with Makefile targets that work: `extract_codebook`, `run_extract`, `run_pilot_extract`, `run_panel_extract`, EDA runs, and `sync_culturewar` / `sync_culturewar_codebook`, which copy outputs into `CultureWar` by path.
- `data/raw/INVENTORY.md` is a good raw-file inventory: file, size, description, verified rows and columns (73,745 × 1,030), survey years. `data/` is gitignored, and the CDF download zip and the codebook PDFs (`anes_timeseries_cdf_codebook_var_20260205.pdf`, `..._app_...pdf`) are kept there.
- Holds the only copies of `extract_cdf_codebook.py`, the HTML codebook and `anes_cdf_dict.json`. Last commit 2026-08-15.

## 4. The analysis layer and its tools (`CultureWar`)

| Path | What it does | Generic or ours |
|---|---|---|
| `notebooks/variable_metadata/variables.yaml` (5,562 lines, 354 variables) | Hand-edited per-variable metadata for figures and models | Ours |
| `notebooks/variable_catalog.py` | Strict loader for the YAML: rejects duplicate keys and unknown fields, validates `codings`, exposes accessors | Ours in content; the strict-loader pattern is generic |
| `scripts/fill_question_verbatim.py` | Copies `question` from `gssrdoc_minimal.json` or `anes_cdf_minimal.json` into `question_verbatim` | Lookup generic, target ours |
| `scripts/check_question_wording.py` | Checks that quoted wording in metadata and chapter prose matches `question_verbatim` | Ours, but the idea generalizes (see below) |
| `notebooks/inventories/*.md` (13 topic files + README, about 3,400 lines) | Hand sweeps of GSS, ANES and other sources per chapter topic | Ours, valuable as recall answer keys |
| `.cursor/skills/gss_data.md` | Agent skill: which GSS/ANES file to use for which question | Generic as a pattern |
| `data_watch_plan.md` | Table of every external source: what we have, expected next release, when to check, where | Generic as a pattern |

- `variables.yaml` fields (counts of entries using each): `source` 354, `question` 354, `subtitle` 353, `selected_values` 345, `legend_label` 341, `title` 339, `ymax` 306, `question_verbatim` 297, `notes` 73, `codings` 66, `outcome` 27, `mean_range` 18, `display_range` 18, `display_labels` 18, `codebook_var` 5, `legend_loc` 3. Allowed `source` values: `gss`, `anes_cdf`, `anes_panel`, `pew`, `ipums`, `gallup`, `synthetic`, `derived`. Only `question_verbatim` and `codebook_var` belong to the codebook layer; the rest (valence, titles, codings) is analysis.
- `fill_question_verbatim.py` inserts text by line editing to keep comments, then round-trips the YAML and asserts each filled value equals the source and nothing else changed. That round-trip assertion is a pattern worth copying for any tool that writes to hand-edited files.
- `check_question_wording.py` normalizes case, punctuation and quotes, expands wording alternatives such as `(Negroes/Blacks/African-Americans)`, splits at ellipses and looks for each piece. It imports `where_used` and reads chapter files, so it is tied to the book. A generic version would be "check that text quoted from the codebook really is in the codebook".
- Inventories: each variable gets a `### variable` block with Question, Waves · span, Valence, Notes. The README says question text comes from `VARIABLE_QUESTIONS` in `utils.py`, else from the minimal JSON files. These give a list of known relevant items per topic, which is what recall measurement needs; valence and "featured" marks are ours.
- `gss_data.md` is a Cursor skill, not a Claude skill. It explains the extract HDFs, the five gssrdoc files, the PDF files, and a "which format for which question" table, plus an ANES section. Its claims depend on files that a fresh clone does not have (gssrdoc JSON, HDF extracts).
- `data_watch_plan.md` records access traps per publisher: Pew's terms forbid automated bulk access and pewresearch.org returns 403 to `curl`; electionstudies.org returns 403 to `curl` (use a browser or Playwright); ANES CDF errata in `VCF0205` and `VCF9096` are pending a new release.

## 5. NSFG as a third worked example (`MarriageNSFG`)

| Path | What it does | Inputs | Outputs |
|---|---|---|---|
| `scripts/download_nsfg.py` | Fetches the public-use files for ten cycles; `--check` reports what is present offline; `--extracts` fetches the published release | `https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NSFG/...` (`.dat`, `.dct`, Stata, SAS) | `data/raw/*.dat.gz` etc.; `data/interim/*.parquet`, `*.csv.gz` |
| `scripts/fetch_codebooks.py` | Downloads codebook and recode-spec PDFs to a temp dir, runs `pdftotext -layout`, keeps only text | `https://www.cdc.gov/nchs/data/nsfg/codebooks/...PUFCodebook.pdf`, `.../recodespecs/...pdf` | `codebooks/*.txt` |
| `codebooks/` | Five text files for 2022–2023 (FemResp, Male, FemPreg codebooks; FemResp and Male recode specs), 3.5 MB, with a README on grepping (`grep -A16 '^HIEDUC$'`) | — | — |
| `nsfg/validate.py` | `check_counts` (expected rows and ever-married counts per cycle), `check_reconstructed_age` (feasibility of a derived variable), `check_cross_cycle` (flag derived variables that jump at a cycle boundary) | harmonized frames | `ValidationError` |
| `tests/test_validate.py` | Runs the count checks without the raw data | — | — |
| GitHub release `data-2026-11-10` | Harmonized extracts, about 6 MB | — | `FemMarriageData.parquet`, `MaleMarriageData.parquet`, `marriage_nsfg_female.csv.gz`, `marriage_nsfg_male.csv.gz` |

- Data release: `download_nsfg.py` pins the tag in `EXTRACTS_TAG` and a SHA-256 per file in `EXTRACTS`; it reports "present, differs" rather than overwriting a local rebuild unless `--force`. A new release means a new tag and new checksums in the script. This is the most complete data-release pattern of the three datasets.
- Terms: the script refuses to run without `--i-accept-nchs-terms`, and the docstring explains that the FTP paths serve without the click-through but the obligation applies anyway. CLAUDE.md records the reasoning for each source: NCHS public-use files may be shared (the agreement restricts use and re-identification), IPUMS extracts may not, NCHS documentation is public domain and so is committed.
- Publisher quirks handled in the download step: NCHS serves uncompressed `.dat` and the readers want `.dat.gz`; the 1988 file has no line breaks (8,450 records of 3,553 bytes) and is split into lines locally.
- Codebook layer: text only, no structured records. There is no per-variable JSON, no missing-code list and no availability by cycle. Only cycle 12 is cached; extending to 2002–2019 is Task 10 there.
- Gotchas: README's pipeline diagram says `clean_nsfg` writes `FemMarriageData.hdf`, but `notebooks/clean_nsfg.md` writes `.parquet` (lines 1103, 1334) and the release ships parquet. Cycle numbers vs years are a trap (cycle 12 = 2022–2023, labelled 2023 in `validate.py`). The validation baseline (shape, columns, per-cycle counts, frame hash) in CLAUDE.md is a good, generic regression check for extract builders.

## 6. Cross-cutting quality issues

| Issue | Where | Consequence for the toolkit |
|---|---|---|
| Build inputs missing or outside the repo | the gssrdoc clone unavailable; gssrdoc JSON gitignored; ANES codebook script and HTML only in ExtractANES | Every target repo must hold its own build scripts and pin its sources, and must rebuild from a clean clone |
| Hard-coded release stems and paths | `anes_extract/paths.py`, `make_gss_extract.py` default input, `extract_codebook.py` PDF name | Release identity should be data (a manifest), not code |
| CWD-dependent scripts | R converter, `make_gss_extract.py`, `cdf.py` imports | Paths resolved from the file (as in `nsfg.paths`) |
| Missing codes collapsed | Both regex detectors | The record must keep each missing code with its type (DK, RF, IAP/skip, not asked, not available) |
| Missing codes guessed from labels | Both regex detectors, `drop_negatives` | Record the source of each missing-code fact: publisher-marked, rule-derived, or hand-added |
| Structured data flattened to strings | `value_labels`, `years_available`, `ballot_info` | Store lists and objects; render strings only in views |
| No release-change capture | GSS "What's New" and Release Notes not parsed; ANES errata only in `data_watch_plan.md` | A changes/errata record type |
| Corrections not machine-readable | Issue drafts in markdown | A corrections file that overrides catalog fields, with source and status |
| Validators report but never fail | `extract_cdf_codebook.py validate()` | Coverage checks with thresholds |

## Patterns that generalize

The same eight steps recur across the three datasets, done by hand each time.

1. Acquire the documentation and data. GSS: NORC PDFs by hand, Stata cumulative file by hand, gssrdoc as a third-party mirror. ANES: HTML and PDF codebooks and Stata files by hand, because the site blocks `curl`. NSFG: a script with a URL table per cycle, a terms flag, and a `--check` mode. Generalize the NSFG approach: a sources manifest (URL, file name, release, date fetched, checksum, terms) plus a download script, with manual steps written down when automation is blocked.
2. Probe and parse the codebook. PDF (GSS 2024, NSFG), HTML (ANES CDF), an existing structured package (gssrdoc), and the data file's own labels (Stata headers). Each parser started with a probe script. Generalize as one skill per source format, all writing the same record, with a coverage check against the data file's variable list.
3. Detect missing codes. Publisher-marked (ANES `Missing` section, GSS PDF `RESERVED CODES`, Stata extended missing values) and label regexes as a fallback, plus hand additions (`EXTRA_MISSING_CODES`). Generalize as typed missing codes with provenance, never a bare list that collapses to NaN.
4. Availability by year or wave. gssrdoc `years_available` and ballots, ANES `Sources` years, the midterm matrix that checked catalog years against the data, NSFG cycles. Generalize as a per-variable list of waves, checked against non-missing counts in the data.
5. Corrections and errata. gssrdoc issues, the ANES CDF errata page, NORC's "Suspected Issues" PDF, the ANES harmonization log, VCF0878 recoding. Generalize as a corrections record (field, old, new, source, verified or inferred, upstream link, status).
6. Build extracts. Column selection with a missing-column report, rename to stable names, missing recode from the catalog, per-wave crosswalks to harmonized names, logs, a labels file next to the data. Generalize the mechanics; leave column choice, recodes to y=1 and weighting decisions to the user's project.
7. Publish data. GssExtract: HDF committed to `main`. CultureWar: gitignored HDF plus copies by Makefile. NSFG: a tagged GitHub release with SHA-256 sums and a fetch script. Generalize the NSFG release, gated on the publisher's terms.
8. Validate. NSFG's expected counts per cycle, feasibility checks and cross-cycle jump detection; ANES's Stata-vs-HTML counts; `timeseries.py` raising when the CDF already has the value; `fill_question_verbatim.py`'s round-trip assertion. Generalize as tests that ship with each dataset repo and run without the microdata where possible.

## Mapping to the three forms

| Form | What exists | Gaps |
|---|---|---|
| Human-readable | NORC and ANES PDFs and HTML (publisher); GSS Data Explorer pages linked by `norc_url`; NSFG `codebooks/*.txt`; `gssrdoc_evaluation.md`, `codebook_plan.md`, `anes_extract_notes.md`, the harmonization log, `data/raw/INVENTORY.md`; topic inventories (ours) | No generated per-variable pages (gssrdoc has them for the GSS; nothing for ANES or NSFG); no page listing changes across releases; corrections not shown next to the variable they correct |
| Programmable | `gss_extract/catalog.py` and `anes_extract/catalog.py` (load, missing codes, recode); `variable_catalog.py` for our YAML; `nsfg/validate.py`; download scripts | No common record schema (GSS lowercase names with `description`/`modules`, ANES uppercase with `missing_codes`/`valid_range`); structured fields stored as strings; no installable package or stable API per dataset; no lookup by release; missing codes untyped |
| LLM access | `gssrdoc_minimal.json` and `anes_cdf_minimal.json` (designed "for topic scanning"); `gss_data.md` Cursor skill; NSFG greppable text with an anchored-grep recipe | Files are 1–21 MB single JSONs, too big to read whole; no shards, no index, no search tool, no statement of completeness in results; no measured recall (inventories exist as answer keys but were never used as one) |

## Open questions for the plan

- Is gssrdoc the upstream for the GSS dataset repo (we wrap and correct it), or do we rebuild from NORC sources so the GSS follows the same path as every other dataset?
- What is the one record schema, and does it extend data-dict's YAML or replace it? The two existing schemas already disagree on field names and case.
- How are missing codes typed (DK, RF, IAP/skip, not asked, not in release), and how is each fact's origin (publisher, rule, hand, LLM) recorded?
- Where do corrections live and how are they applied: an overrides file in the dataset repo, upstream issues, or both?
- What can be released under each publisher's terms? NSFG releases rely on a reading of the NCHS agreement; Pew forbids automated access. Who signs off on each?
- What happens when automated download is blocked (ANES 403, Pew terms)? Is a documented manual step enough for the standard?
- Does a dataset repo hold extract builders, or only the catalog and raw-data release, leaving extracts to analysis projects like CultureWar?
- Which dataset is the first build: GSS (most existing material), ANES (codebook script needs rescuing from ExtractANES), or NSFG (best data-release practice, weakest metadata)?

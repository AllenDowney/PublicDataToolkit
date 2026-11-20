# Task 30 — A BRFSS slice

**Status:** `DOING (green)`, stopped 2026-11-19 for Allen's travel (see "Stopped here" at the end)

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

## What was built

`~/pdt-brfss`, from the template at `v0.1.0`:

| Part | What |
|---|---|
| Releases | 13, one per survey year, 2011–2023 |
| Records | 295: 23 concepts × 13 years, less the years a concept doesn't exist. `build/slice.yaml` maps each concept to its name in each year |
| Sources | 121 in `sources.yaml`, all hashed and fetched with urllib (1.2 GB): data (SAS transport, zipped), codebook, calculated-variables document, variable layout, SAS input program, formats, modules by state, overview and comparability notes for each year; CDC's agency-materials terms and the 2013 Data User Guide |
| Terms | Decided by Allen (2026-11-19): CDC's "Use of Agency Materials" (public domain, with attribution, a no-endorsement disclaimer, unchanged content, and "available at no charge"). Everything `ship`, `llm_processing: allowed`; the credit and disclaimer are in `terms.notice` and the README |
| Links | 298: 4 renames CDC states, by rule the same name with identical documentation, and 65 `derived_from` from the calculated variables' codebook notes. `build/links_report.md` lists the rest |
| Histories | 24, 10 with more than one period, assembled by rule from the yearly codebooks |
| Data | `make data`: `data/processed/brfss-<year>.parquet`, 13 files, every round trip exact |
| Check | `pdt check`: 0 failures, including C3–C5 and C12; 0 unresolved codes |

The build is three scripts: `build/codebook.py` parses the codebooks, `build/build_records.py` writes records and groups, and `build/build_links.py` and `build/build_histories.py` follow. `build/xport.py` reads the data.

## What BRFSS tests that the earlier datasets didn't

1. **Each year is a release with its own names.** CDC renames a variable when its question changes (`SEX` → `SEX1` in 2018 → `SEXVAR` in 2019; `INCOME2` → `INCOME3`; `ADDEPEV2` → `ADDEPEV3`), and calculated variables follow their inputs (`_RFBING5` → `_RFBING6`, `_INCOMG` → `_INCOMG1`). A name can even come back: `_RACEGR3` (2013–2021) → `_RACEGR4` (2022) → `_RACEGR3` (2023). The slice needed a hand map from concepts to names by year (`build/slice.yaml`), which is ours, not the publisher's.
2. **Renames the publisher states are only some of them.** Each year's "Calculated Variables in Data Files" says "X changed to Y due to A changing to B", which names the calculated renames and the raw ones behind them. The build parses those sentences into links. But CDC states none of these, so they stay unlinked under rule 2:
   - `SEX` → `SEX1` → `SEXVAR`;
   - `ADDEPEV2` → `ADDEPEV3`;
   - `_RACEGR2` → `_RACEGR3`;
   - `_RACEGR4` back to `_RACEGR3`.

   A cross-year catalog (red's) shows them as separate lines.
3. **Same name, changed documentation.** About 50 same-name pairs differ between consecutive codebooks: a question reworded (ADDEPEV2 2016→2017), a range narrowed (ALCDAY5: 101–199 and 201–299 in 2011, 101–107 and 201–230 from 2016), codes added (refused for SEX from 2016). The rule links only identical documentation, and reports the rest.
4. **Three codebook layouts in 13 years.** PDF 2011–2015, PDF 2016–2021 except 2019, and SAS-generated HTML in 2019, 2022 and 2023 (zipped in 2022–23). Traps, each now handled and named in `build/codebook.py`:
   - running headers that match words in titles: `_LLCPWT`'s title "Final weight: Land-line and cell-phone data" was dropped as a header, and the label became the previous row (found by red's catalog);
   - a header split over two lines in 2021 ("Overall version data" / "weighted with _LLCPWT"), which leaked into labels and turned "Not asked or Missing" into a valid code (also found by red);
   - a table continued on the next page repeats the entry's whole header, `SAS Variable Name` included;
   - long values leave one space before the label ("101 - 107 Days per week"), or wrap ("101 -" then "107");
   - rows with no label (IYEAR), in PDF and HTML;
   - labels wrapped with their counts on the last line, and the em dash before a skip instruction rendered as a soft hyphen and dashes (2013, 2015; rule `brfss_pdf_text`);
   - skip instructions inside value labels ("Refused—Go to Section 07.05 USENOW3"), which the missing-code rule must ignore;
   - "HIDDEN: Data not displayed" for strata and weights.

   **A label check found most of these.** The build reports any label that looks like a table row, a count, a fragment or header text. It's worth having in every build, or in `pdt check` (proposal 6).
5. **Availability by state.** The core is asked in every state, but an optional module only where a state chose it: LSATISFY in 2017, 2022 and 2023 lists each state that asked it, as `sample` (a FIPS code). In 2011 the variable and its codebook entry exist, but no state asked it, so it has no availability.
6. **Questionnaire versions.** CDC puts a module in the combined file only when a state asked it of every eligible respondent all year. Modules asked of part of a state's sample are in separate version files with their own weights (2011 Comparability of Data, "Other Issues"). These are forms in the standard's sense, with a different file and weight per form. The slice doesn't cover them.
7. **Calculated variables document their derivation code by code** ("Notes: SMOKE100 = 1 and SMOKEDAY = 1"). The build turns the names in those notes into `derived_from` links, with the codebook as the source. The notes misname one input in every year, 2011–2023: "SMOKEDAY" is `SMOKDAY2` in the data. A hand name-fix with its evidence maps it.
8. **The file year isn't the interview year.** A year's file includes interviews from early in the next year (2023: 25,311 in 2024). So IYEAR isn't the wave column, and the wave is the release.
9. **The data format.** SAS transport files in zips. pandas reads them, but turns SAS's special missing values into NaN. The ZIP member's name has a trailing space (`LLCP2014.XPT `), and it unzips with mode 000. `build/xport.py` reads only the wanted columns straight from the zip and keeps `.`, `.A`–`.Z` and `._`; on 2014 it matches pandas cell for cell. No special missing values occur in the slice, but the reader is ready for them.
10. **The codebook isn't complete for design variables.** `_LLCPWT` has no codebook entry in 2016–2018 and 2020–2021. Its label comes from the data file there, with `origin: data_file`.
11. **No code matrix.** The FARS manual prints codes by year range; the BRFSS documents one year at a time. The histories are assembled by rule (`brfss_histories_from_codebooks`) from the yearly records, along the chains the links connect. A name change CDC doesn't state starts a new history.

## Earlier years (before 2011)

The 2010 page has `CDBRFS10XPT.zip` (landline only), `codebook_10.pdf`, `SASOUT10.SAS`, and the weight `_FINALWT`, post-stratified rather than raked. A slice reaching back would need:
- a second weight name and a `design` per release (STANDARD.md allows that);
- a link, or a stated break, between `_FINALWT` and `_LLCPWT`, which CDC describes as a change of method, not a rename;
- the codebook parser checked on pre-2011 layouts.

CDC's 2011 Comparability of Data describes the 2011 changes (cell phones, raking). It doesn't say whether to compare across them, so the repo starts in 2011 and says why.

## Proposals

For the standard (the coordinator's):
1. **Several valid ranges.** ALCDAY5's valid values are 101–107 (days per week) and 201–230 (days in the past 30), two ranges with different meanings. `valid_range` holds one. The build records the span and quotes both ranges in its note, which isn't exact. Proposal: allow a list, each range with its label, e.g. `valid_ranges: [{min, max, label}]`.
2. **Geography in availability.** A state isn't a "subsample", but `sample` is the only dimension that fits. Proposal: a `geography` dimension, or the standard says `sample` may hold a geographic unit and `dimensions.sample.label` names it. Either way, a filter like `{"available": {"wave": 2022, "sample": "25"}}` answers "asked in Massachusetts in 2022".
3. **Histories by rule.** §5.4 says the build writes the publisher's matrix with the publisher as origin. A history assembled by rule from one-year documents, as here, should be allowed and labeled as such: `origin: rule`, its periods only as fine as the releases built.
4. **Per-code notes.** The codebook's notes per code ("1: SMOKE100 = 1 and SMOKEDAY = 1") are the publisher's derivation of a calculated variable. Today they're joined into `notes`. Proposal: `values[].note`, verbatim, so tools and links can read them per code.
5. **Concept series across releases.** Readers want "depression, 2011–2023", across an unstated rename. A link can't say it (rule 2). Proposal: an annotation kind `series`, origin `hand` or `rule`, grouping one variable per release. It's `approximate` by construction, and it keeps the publisher's continuity (links) separate from ours.

For the library (views + site, or red):

6. **A label lint in `pdt check`:** report labels that look like table rows, counts or running headers. Here it found five parser bugs.
7. **`read_sas_xport` for `pdt.readers`,** from `pdt-brfss/build/xport.py`: selected columns, straight from a zip, keeping SAS's missing values as `Code`. The coordinator asked red to review it.

## Messages

- Terms: sent to the coordinator; decided by Allen.
- Downloads: www.cdc.gov returns 403 to curl's and Chromium's User-Agents but not to urllib's (as red found in Task 18), so `pdt download` works and nothing needs a manual download. Documentation was first fetched through a headless browser; the browser fetch isn't needed now.
- red: the `_LLCPWT` and 2021 header labels (fixed); the ADDEPEV and SEX chains (unlinked on purpose, explained).

## Stopped here (2026-11-19, green)

`~/pdt-brfss` is committed (e81369f; no remote), after a final run that includes the 2021 header fix (MENTHLTH's and the other "." codes):
- `make data`: all 13 years round-trip exactly;
- views regenerated;
- `pdt check`: 0 failures, 0 unresolved codes, 0 labels flagged.

**Open bug:** `_RACEGR2`'s "." code in 2011 and 2012 is labeled with a count ("126", "105") and typed valid. It's probably a BLANK row with a count and no label in that layout. Every other "." code in all 13 years is missing, with the right types.

**Next steps:**
1. Fix `_RACEGR2` in `build/codebook.py`, then `make build && make data && make views && make check`.
2. Check two claims in this file: "about 50" same-name pairs with changed documentation, and "refused for SEX from 2016" (finding 3).
3. Set the status to DONE, then ask red to review `build/xport.py` for `pdt.readers` and to regenerate views.

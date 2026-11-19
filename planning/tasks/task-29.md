# Task 29 — A YRBSS slice

**Status:** `DONE (purple)` — 2026-11-19. Worked by the thread first named "yrbss", renamed "purple".

The Youth Risk Behavior Survey (YRBS) is CDC's survey of US high-school students, run every odd year since 1991. It's on Allen's high-priority list from Twenge's *Generations*. The task: a slice of about 20–30 variables in a new local repo, `~/pdt-yrbss`, made with the Copier template (`v0.1.0`), with the common-format data and `pdt check` at 0 failures.

**Variables:** survey design (weight, stratum, PSU, year), demographics (sex, grade, age, race/ethnicity), and items on sadness or hopelessness, suicidal ideation, physical fights, alcohol, marijuana, sexual activity, screen time or TV, and sleep, for every year each was asked.

**Files:** `~/pdt-yrbss/` (new, no remote); this file; the Task 29 block on the board.

## Result

`~/pdt-yrbss`, commits `a59c7f0` (the template) and `9c55077` (the slice). No remote. `pdt check`: 0 failures, with the data checks C3–C5 and C12 run on both releases.

| | sadc-2023 | sadc-2021 |
|---|---|---|
| Publisher's file | `sadc_2023_national.dat` | `SADC_2021_National.dat` |
| Years, rows | 1991–2023, 254,675 | 1991–2021, 234,572 |
| Records | 29 of 269 columns | 29 of 241 columns |
| Common format | round trip exact, 24 code columns | round trip exact, 24 code columns |

- **Variables.** Design: `year`, `weight`, `stratum`, `PSU`, `record`. Demographics: `age`, `sex`, `grade`, `race4`, `race7`. Items: fighting, sad or hopeless, considered suicide, suicide plan, suicide attempts, age at first drink, current drinking, binge drinking, ever and current marijuana, ever had sex, current sexual activity, mental health, sleep. Screen time is 2021's `q78`; social media is 2023's `q80`. Four of CDC's dichotomized `qn` variables are included in each release.
- **Groups:** 18. These are the guide's categories (sample, demographic, questionnaire) and the content document's topics, per release.
- **Links:** 36. Of these, 28 go from 2021 to 2023: 17 are `renamed`, and 5 are `labels_changed`, where only the variable label changed. The other 8 are `derived_from`, `qnN` to `qN`, from Appendix C.
- **Code histories:** 3: `age` (1991's option G is "18 years old"), `grade` (option E's wording), and `q41`, age at first drink (1991–1993 used "Less than 9 years old" ... "17 or more years old").
- **Terms:** Allen decided them on 2026-11-19: everything `ship`, and `llm_processing: allowed`. CDC's credit and disclaimer are in `terms.notice` and, verbatim, in the README. The YRBSS FAQ adds nothing stricter: "There is no charge for the data nor is permission needed to download or use the data," and the questionnaires "are in the public domain".
- **Sources:** 11, all fetched by `pdt download`; www.cdc.gov accepts urllib's User-Agent. A headless browser also works if it navigates to each file. Playwright's request API gets 403 from Akamai.

### Sources

- The **combined datasets** ("SADC"), national file: fixed-width ASCII, with a SAS input program for the layout and labels, and a SAS formats program for the value labels. Two releases: 2023 is current, and 2021 is the one before it.
  - A **2025** combined release is posted, with data and SAS programs but no user's guide yet. It would be the next release to add.
- The **Combined Datasets User's Guide** for each release. Appendix C gives each question with its `qn` numerator and denominator.
- **YRBS Questionnaire Content 1991–2023**: one row per wording of each question, with the question number it had in each year's national dataset. This is the cross-year source: the question text by year, the availability, the links and the histories all come from it.
- The single-year national **Data User's Guides** for 2021 and 2023, used only for what a missing answer means (Data Edits).

## What YRBSS tests that the earlier datasets didn't

1. **A cumulative file that renumbers every variable in each release.** The combined file maps every year to the release year's question numbers, so a name means different items in different releases. `q26` is "Considered suicide" in sadc-2021 and "Sad or hopeless" in sadc-2023. Even the publisher's labels for one name differ only in wording. The links come from the content document, not from names. `pdt diff sadc-2021 sadc-2023` shows the danger: it pairs by name and reports 2021 `q26` → 2023 `q26` as `labels_changed, wording_changed`. It also proposes the rename `qn25 → qn27`, which is wrong. GSS, ANES CDF, NSFG and FARS all keep a name for an unchanged item.
2. **Which wordings a cumulative variable folds in is visible only in the data.** For 2023's `q43` (binge drinking), the content document has three rows. These are the 2019–2023 wording, a 2017 wording, and the 1991–2015 item "5 or more drinks of alcohol in a row". The data have `q43` for 2017–2023 only, so the 2017 row is folded in and the older item isn't. The guide doesn't say this. The row whose release-year column names the variable is the publisher's. The earlier rows (age 1991, grade 1991–1997, `q41` 1991–1993, `q43` 2017) are assigned by hand in `build/slice.yaml`. The build checks that the rows' years are exactly the years with data. So one record's `questions` mixes a publisher wording with hand-assigned ones, under one `provenance.fields.questions` (now `hand`, with a note).
3. **Response letters aren't codes.** The data code the options 1, 2, 3, ... by position. In the content document, 2021's screen-time item (Q78) is lettered A, C, D, E, F, G, skipping B, in both the high-school and middle-school rows. The 2021 formats code those six options 1–6. So the histories' codes come from a rule, with `origin: rule`, not straight from the publisher. This also looks like an error in CDC's document.
4. **History `names` from another product.** The content document gives each item's name in each year's single-year national file (Q32 in 1991, Q38 in 1993, ...). In the combined file, the name is fixed by the release, not by the wave. §5.4's `names` assumes names change by wave within the dataset, so here they hold the single-year files' names, and each history's note says so.
5. **One missing code with three meanings.** A blank (or SAS `.`) is "Missing" in the formats. The Data User's Guide sets invalid and inconsistent answers to missing, and the combined guide says earlier years have more missing data because the questions weren't asked. So each missing code has `["no_answer", "uncodeable", "not_asked"]`, like GSS `.m`. Availability already says which years weren't asked, so the library could tell `not_asked` cells from the others.
6. **A blank is a code.** The q items are one-character text (`$` in SAS, `(A)` in SPSS), and CDC's formats label `" "` as "Missing". So `" "` is a string code, and the code column holds `" "`. This works, but a whitespace code is fragile in YAML, CSV and anywhere text gets trimmed.
7. **Row-partition files.** A release is nine files with the same columns: national, district, and states in seven groups by name. This slice declares the national file as a table, `national`, keyed by `record`, so C12 has something to check. The standard's tables are different kinds of records, not partitions of one kind.
8. **A new data format:** fixed-width text laid out by a SAS input program, with `.` in numeric fields. `pdt.readers.read_stata_dictionary` would fail on the `.`. The repo has its own reader, `build/sadc.py`, as §8 allows.
9. **Publisher-defined recodes.** Each `qn` variable is "set to 1" for the "response(s) of interest" and 2 otherwise, with a numerator and denominator in Appendix C. These are stored as a `derived_from` link within the release, with the definition in `description` and `notes`. The definition is structured, so a field could hold it.
10. **An item that survives only in a superseded release.** Screen time (2017–2021) is in sadc-2021 and not in sadc-2023, which has social media instead. Keeping the older release is the only way the repo offers it. TV watching, which Twenge uses, is in neither release: it needs the single-year files or an older combined release.
11. **Survey design variables.** `weight`, `stratum` and `PSU` are present for every year. Nothing in `dataset.yaml` says that these three columns are the design.

## Proposals for the standard (not made; for the coordinator)

The coordinator's decisions (2026-11-19): 2, 3 and 6 are in STANDARD.md and the schemas (`8ae8813`). 1, 5 and 7, and the `valid_labels` bug, went to the library as [Task 39](task-39.md). 4 is deferred.

1. **Warn on name reuse across releases.** `pdt check` (or `pdt diff`) should report a name that appears in two releases without a `same_item` link between those two records, when the name has a link to a different name. `pdt diff` should pair by existing links before pairing by name.
2. **Per-wording provenance.** Let each `questions` entry carry its own `origin`. A record whose wordings come from different origins needs this; §10 lists it as provisional ("Provenance per field rather than per value").
3. **§5.4 `names`:** say whose names they are. Allow names in another product, such as the single-year files, with a `source`, or rename the field to "the publisher's identifiers by wave".
4. **Tables as partitions.** *Deferred by the coordinator (2026-11-19) until someone builds the state or district files.* Say that a release's tables may be partitions of one kind of record (by site or region), with the same columns. Or add `parts` to a table, so the national, state and district files form one table.
5. **`not_asked` from availability.** A missing code whose types include `not_asked` could be split by the library: in a wave outside `availability` it is `not_asked`, and inside it, the other types. This would apply to any cumulative file.
6. **Design variables in `dataset.yaml`,** e.g. `design: {weight: weight, strata: stratum, psu: PSU}`. The YRBSS, BRFSS and CPS all need one.
7. **A shared reader for SAS input programs** (`pdt.readers.read_sas_input`), from `build/sadc.py`. It reads `$` columns as text, and numeric `.` or blank as `Code(".")`. CDC publishes BRFSS and other datasets the same way. This is for the views + site thread, which owns `readers.py`.

## Problems found in shared code (reported, not changed)

- **`pdt.derived.valid_labels` raises KeyError for a valid code without a label.** The schema makes `label` optional, and the `qn` codes 1 and 2 have none. The YRBSS build works around it by passing only fully labeled records to `scale_signatures`.

## Problems found in CDC's documentation

- **For Allen:** the Questionnaire Content document letters 2021 Q78 (screen time) A, C, D, E, F, G, with no B, in both the high-school and middle-school rows. The 2021 formats and the data have six codes, 1–6. The coordinator judged it not worth an email by itself; it's listed here in case it goes with another report to CDC.
- **The formats' labels are CDC's "short response" labels,** not the questionnaire's text: `q59` "Never had sex", against the questionnaire's "I have never had sexual intercourse". That isn't an error; the build report lists the differences.
- **The 2021 combined guide prints no page numbers.** Page references in both releases are PDF pages.

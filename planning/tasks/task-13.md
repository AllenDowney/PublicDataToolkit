# Task 13 — FARS slice

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE (fars)` (2026-11-19): PARKWORK, code histories, the 2017 release and links. Worked by the thread "fars". The main thread built the preliminary slice and handed the rest off

The non-survey case Allen chose. Allen downloaded the 2024 national CSV and SAS files, the auxiliary files, the Analytical User's Manual 1975–2024 (823 pages), and NHTSA's Q&A on the auxiliary files. They're in `../pdt-fars/data/raw/`; the manual's text is `data/interim/manual.txt`.

**What FARS tests:**
- **Tables:** 33 data files, keyed by `ST_CASE`, `VEH_NO` and `PER_NO`.
- **History across years:** the manual gives each element's codes as a matrix of year ranges. For example, `LGT_COND` code 9 is "Unknown" until 2017 and "Reported as Unknown" from 2018.
- **No questions:** it's a census, coded from police reports.
- **A second source for labels:** the CSV pairs most coded columns with a label column, e.g. `LGT_CONDNAME`.

**Progress (2026-11-19):** `build/build_slice.py` parses 432 elements and builds 32 variables in three tables (`accident`, `vehicle`, `person`). **The parser isn't right yet**:
- labels run on into the next element's title;
- code tables that continue onto the next page lose their codes, so the report's 220 "unresolved" codes, such as `STATE` 1–22, are artifacts;
- `WEATHER` finds no 2024 column.

The comparison of the manual's labels with the data's labels already works, and shows only small differences: dashes, case, "(Since 2011)". **Update (2026-11-19, later):** the parser is fixed, and the slice is committed locally in `pdt-fars`. `pdt check` passes.
- **Parser fixes:**
  - a table continued on the next page repeats its year header, and now continues the same block;
  - wrapped labels are recognized by indentation;
  - a discontinued element that shares a SAS name with the current one (`WEATHER`) no longer replaces it.
- **Codes:** 0 unresolved, down from 220. All of those were parser artifacts.
- **Labels:** compared with the CSV's label columns. After ignoring case, punctuation, year notes and added examples, 8 codes differ in wording. For example, `DR_DRINK` is "Drinking" in the manual and "Yes" in the data. For code 99, the manual's "Unknown/Reported as Unknown (Since 2018)" puts the year's change inside one label.
- **Tables and keys:** `accident`, `vehicle` and `person`, with keys and references checked against the data. Person → vehicle can't be declared: 9,020 non-motorists have `VEH_NO` 0, and 426 occupants of parked or working vehicles refer to the PARKWORK file. That's a conditional reference, which the standard can't express (Task 25).
- **Common format:** all three full tables round-trip exactly; CSV is the third source format, after Stata and SAS.
- **Still open:** terms (Allen); only the 2024 column of each element's year-range matrix is used. A second year (2017, before the 2018 code changes) would test release comparison.

**Terms:** NHTSA's manual has a disclaimer, no license, and "available to the public"; it's a US government work. Allen decided on 2026-11-19: everything `ship`.

**Next steps, for the worker thread:**
1. **The PARKWORK table:** add it as a fourth table, with a reference from person (`ST_CASE`, `VEH_NO`) `when` `PER_TYP` is 3 (an occupant of a motor vehicle not in transport). Check the reference against the data, as was done for vehicle.
2. **History across years:** the manual's code matrix gives each element's codes by year range. Propose a structured form for it (STANDARD.md §5.2 links, a release-comparison report, or something new), and send the proposal to the coordinator before building it, since it may change the standard. `LGT_COND` code 9 ("Unknown" to 2017, "Reported as Unknown" from 2018) is the test case.
3. **A second release:** to test release comparison, Allen downloads the 2017 national CSV (nhtsa.gov blocks scripts and headless browsers). Ask him when you're ready.
4. More variables only as these steps need them.

**Files:** `../pdt-fars/` only (not its `agent/` or `docs/`, which the views thread generates).

**Step 1, done (fars thread, 2026-11-19):** the PARKWORK table. pdt-fars commit `f2761b7`.
- `parkwork`: 8 variables; key (`ST_CASE`, `VEH_NO`); refers to `accident`.
- person (`ST_CASE`, `VEH_NO`) → `parkwork` `when` `PER_TYP` is 3. The manual says so on page 295 ("When PER_TYPE = 3, the occupied vehicle will be found in the PARKWORK data file"). It holds for all 426 rows, and the parkwork and vehicle keys don't overlap.
- The build now checks every key and reference in `dataset.yaml` against the data and lists the results in `build/report.md`. `pdt check` only checks that the tables and columns exist.
- **Parser:** the SAS Name field can span several lines, each with its years (`HARM_EV 2005-2009`, `PHARM_EV 2010-Later`). The parser read only the first line, so in PARKWORK it found the 2005–2009 names. 88 elements were renamed this way. All the lines are read now. The other tables' records didn't change, and every ACCIDENT column is now found in the manual.
- **Parser:** pdftotext printed two rows of `PHARM_EV` on one line (code 98, two labels). The parser now splits rows like that. 0 unresolved codes.

**Step 2, proposal: code histories (fars thread, 2026-11-19; sent to the coordinator, not built)**

*What the manual has.* Each element's codes are a matrix: one row per attribute, as the publisher prints it, and one column per year range. Across the manual there are 462 matrices with 5,162 rows. Both kinds of change occur:
- the same code changes meaning: `LGT_COND` 9 is the row "Unknown" for 1975–2017 and the row "Reported as Unknown" from 2018;
- the same attribute changes code: `WEATHER` "Unknown" is 9 until 2017 and 99 after, and `CL_TWAY` "County Road" is 6, then 4. 54 rows change code this way, not counting widened ranges such as 1-99 → 1-999.

There are also renames (88 elements, above) and 338 labels with year notes inside them ("(Since 2018)").

*Why the existing forms don't fit.*

| Form | Problem |
|---|---|
| Links (§5.2) | Variable-level, between two release records. A link can say `codes_changed`, but not which code changed or how. It also needs a record in every release (50 FARS years). |
| A release-comparison report | Generated from two releases' records. It finds differences, but doesn't record what the publisher asserts, and covers only releases we've built. |
| `since`/`until` on each value in the 2024 record | Goes against the Task 25 decision that a record says only what its own release means. |

*Proposal.* A new source file, `metadata/histories.jsonl`, written by `build/`, with one line per element the publisher documents across years. It is the manual's matrix stored as structure (rule 5):

```json
{"id": "accident/LGT_COND", "table": "accident", "name": "LGT_COND",
 "names": [{"name": "LGT_COND", "waves": {"from": 1975}}],
 "periods": [{"from": 1975, "to": 1979}, {"from": 1980, "to": 2008}, {"from": 2009, "to": 2009},
             {"from": 2010, "to": 2017}, {"from": 2018}],
 "attributes": [
   {"label": "Daylight", "codes": [1, 1, 1, 1, 1]},
   {"label": "Unknown", "codes": [9, 9, 9, 9, null]},
   {"label": "Reported as Unknown", "codes": [null, null, null, null, 9]}],
 "origin": {"origin": "publisher", "source": "fars-manual-1975-2024", "location": {"page": 78}}}
```

- **Periods** are in the units of `dimensions.wave` (the data year for FARS). A period with no `to` runs through the latest release.
- **Attributes** are the publisher's rows, in its order. `codes` lines up with `periods`, and `null` is the manual's `--`. A range stays a string (`"1-99"`). Labels are verbatim, year notes included.
- **Names** give the element's name in each period (`HARM_EV` 2005–2009, `PHARM_EV` from 2010).
- Identity is (`table`, the current name). A discontinued element is keyed by its last name and has no 2024 record.

*What it's for.*
1. **Records for other years.** A 2017 record can be built from the 2017 column plus the 2017 data's labels, with no separate parser.
2. **Release comparison.** For each code, compare which attribute (row) it belongs to in each release: the same row, a different row with the same code (`LGT_COND` 9), a new code, or a dropped one. The comparison is a rule over the publisher's history, not a guess.
3. **Links.** A `codes_changed` or `renamed` link between two releases' records can be generated from the history by a named rule (`origin: rule`), like the GSS naming-convention links. Rule 2 still holds, because the publisher asserts the rows.
4. **Views.** A per-variable "code history" table. That is where a history string like "(Since 2018)" belongs.

*Questions for the coordinator.*
1. Put this in the standard now, as an optional file (a new §5.4, `schema/history.schema.json`, C2 checks that the target exists), or keep it FARS-only until a second dataset needs it? GSS and ANES CDF codebooks also document year-specific codes, so it may generalize. Extensions (§4.4) are per record and don't fit a separate file.
2. Scope: only the slice's elements (as §5.1 does for groups), or all 433 in the manual? I'd do the slice, plus the discontinued elements that share a name with one in the slice (`WEATHER`).
3. Is (`table`, current name) the right identity, given that one element can hold several SAS names (`WEATHER1`, `WEATHER2`)? I'd make one history per name, and duplicate the history where names share it.

*Test.* Once Allen downloads the 2017 national CSV (step 3), check the matrix's 2017 column against the 2017 data's codes and labels. The data should say "Unknown" for `LGT_COND` 9 in 2017 and "Reported as Unknown" in 2024.

**Step 2, built (fars thread, 2026-11-19).** The coordinator approved the proposal and added it to the standard (§5.4, `schema/history.schema.json`, commit `832696f`). pdt-fars commit `01f920a` adds `metadata/histories.jsonl`, with 42 histories: the 40 variables in the slice, plus `WEATHER1` and `WEATHER2` from the discontinued Atmospheric Conditions element. `pdt check` passes.
- `LGT_COND` matches the manual's matrix (p. 78): "Unknown" is `[9, 9, 9, 9, null]` and "Reported as Unknown" is `[null, null, null, null, 9]`.
- **The records agree with their histories:** the build compares each record's codes with the last period of its history, and all 27 records with values agree.
- **Several matrices for one element:** 9 of the slice's elements have more than one (`HARM_EV` prints 1975–1981 separately from 1982–Later). Their periods are joined in order, and the rows aren't matched across matrices, because the manual doesn't match them; each such history's `note` says so.
- **Names:** successive names are kept with their years (`OCUPANTS` 2005–2008, `NUMOCCS` 2009, `PNUMOCCS` from 2010). Names printed on one line are parallel variables (`WEATHER1`, `WEATHER2`). Each gets its own history, and both list the element's earlier name `WEATHER` (1975–2006).
- **Ambiguous in the source:** the current `WEATHER` (C26, a derived element) also claims the name `WEATHER` for 1975–2006, so that name appears in two histories for the same years. That's what the manual says.
- **Limit:** a label can change inside a period. `WEATHER` "Unknown/Reported as Unknown (Since 2018)" is code 99 for the whole 2013–Later period. A change like that stays only in the label's year note; 338 labels have one. Parsing those notes would be a further step.

**Step 3, done (fars thread, 2026-11-19):** the 2017 release. pdt-fars commit `acf7f12`.
- **Sources.** Allen downloaded the 2017 national CSV, SAS and auxiliary files, and the release note. They're in `data/raw/fars2017/`, recorded in `sources.yaml` with sha256. The release note shows the 2017 files were reissued until 2022-03-02. The CSV's NAME label columns arrived only in the 12/18/2020 update, so the "2017" labels were written in 2020 or later. Even so, they use 2017's wording ("Unknown", not "Reported as Unknown").
- **Release 2017** has the same four tables and the same 40 variables, all under the same names. Codes come from each history's column for 2017, and labels from the 2017 CSV. All keys and references hold, including person → parkwork for 358 rows.
- **The histories against the data:** every code that occurs in the 2017 and 2024 data is in the history's column for its year. Most labels match exactly or differ only in detail (case, punctuation, year notes). The rest are listed in `build/report.md`: 18 codes in 2017 and 15 in 2024. They're the wording differences seen before (`DR_DRINK` "Drinking" vs "Yes"), plus labels whose year notes describe a change inside a period.
- **The test case:** `LGT_COND` 9 is "Unknown" in the 2017 data (133 crashes) and "Reported as Unknown" in 2024, as the history says.
- **The limit in §5.4, confirmed by data:** `WEATHER`, `SEAT_POS` and `REST_USE` code 99 have one row, "Unknown/Reported as Unknown (Since 2018)", across 2017 and 2024. The data say "Unknown" in 2017 and "Reported as Unknown" in 2024. `BODY_TYP` 81 "Moped (Since 2022)" and 96 "(Since 2024)" are the same kind.
- **Links:** `metadata/links.jsonl` has 40 links from 2017 to 2024, made by rule `fars_links_from_history` 0.1 from the histories, with the manual as their source. 24 are `same_item`, 15 `labels_changed` and 8 `codes_changed`; each link's `note` lists the changed codes.
  - `labels_changed`: a code moves to a row with another label (`LGT_COND` 9), or its row's label says "(Since Y)" with Y after 2017 and no later than 2024. Without the second case, the rule would miss `WEATHER`, `SEAT_POS` and `REST_USE`.
  - `codes_changed`: the set of codes changes, or a row's code does. For example, `ROLLOVER` replaced 1, 2 and 9 with 3 ("Rollover") and 8 in 2022, and the data agree.
  - No `renamed`: none of the 40 variables changed name between 2017 and 2024. The PARKWORK renames were in 2010.
- **Build:** `build/slice.yaml` now lists releases and their data files. The 2024 records changed only in the values' provenance note, which now names the period used ("column for 2018-Later"). Scale signatures name their release.
- **Not done:** the release note's data revisions (12/18/2020: body type, rollover, restraint use and more in many States) happened inside the 2017 release, so they aren't links. A record of revisions within a release would need another form.

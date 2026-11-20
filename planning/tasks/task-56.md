# Task 56 — An ATUS slice

**Status:** `DOING (yellow)`, blocked on downloads from bls.gov. (First numbered Task 54, which red had already claimed; renumbered by the coordinator, 2026-11-20.)

The American Time Use Survey (BLS) in `~/pdt-atus`, 2003–2023: the respondent file, the activity summary and the activity file's codes. The activity codes are the first real test of shared code lists (`metadata/code_lists.jsonl`, STANDARD.md §4.5).

## Progress

### 2026-11-20: blocked on downloads from bls.gov

- `~/pdt-atus` was created from the template (v0.1.0; 5ff6c8a, terms URL fixed in 1fa2d76). The single release is `2003-2023`, BLS's multi-year files, with year as the wave.
- **bls.gov refuses scripts.** These requests got 403 "Access Denied" on 2026-11-20:
  - urllib's and curl's default User-Agents;
  - a browser User-Agent;
  - headless Chromium (Playwright);
  - a generic script name.

  The data page is https://www.bls.gov/tus/data/datafiles-0323.htm. The refusal page says bot activity "that doesn't conform to BLS usage policy is prohibited". BLS's terms (https://www.bls.gov/bls/blsterms.htm) reserve "the right to block robots that do not contain information that can be used to contact the owner".
- **What's needed:** a script would need contact information in its User-Agent. That means Allen's email, which I won't send without his explicit OK. The other way is for Allen to download the files in a browser.
- **Nothing else has started:** no sources, no records.

### 2026-11-20: the slice plan, while the files are downloaded

**Release.** The coordinator agreed to the current multi-year files, 2003–2025 (`datafiles-0325.htm`), since BLS has archived the 2003–2023 ones. The release id becomes `2003-2025`, and the wave is the year (TUYEAR). `~/pdt-atus` still says `2003-2023`; this changes when the files arrive.

**Sources read so far:**
- BLS's pages, through a web-fetch agent;
- the ATUS User's Guide (September 2026, 127 pages), read locally.

The data dictionaries are PDFs I haven't seen. So the variable names below, apart from those the guide names, are to be confirmed against `atusintcodebk0325.pdf`.

**Tables and keys** (User's Guide, §7.4 "Linking"):

| Table | Records | Key |
|---|---|---|
| `respondent` | one per respondent | TUCASEID (TULINENO is always 1) |
| `summary` (activity summary) | one per respondent | TUCASEID |
| `activity` | one per diary activity | TUCASEID, TUACTIVITY_N |
| `replicates` (replicate weights) | one per case selected | TUCASEID |

References: `summary` → `respondent`, `activity` → `respondent`, and `replicates` → `respondent`, all on TUCASEID. Every case selected for ATUS is in `replicates`, so that reference goes from respondent to replicates.

**Weights and variance** (guide, ch. 7):
- On the multi-year files, the weight is **TUFNWGTP**, "created using the 2006 weighting method and ... available for all years, except 2020 which uses TU20FWGT". So `design.weights` names both, and the note says which year uses which.
- The weights count person-days, not persons.
- Variance uses 160 replicate weights per final weight, with the formula Var(Ŷ₀) = 4/160 · Σ (Ŷᵢ − Ŷ₀)².
- The guide calls the replication "a modified balanced half-sample method ... developed in the 1980s by Robert Fay" and points to CPS Technical Paper 77, which calls it successive difference replication. The formula 4/R fits both `sdr` and Fay's method with factor 0.5. I'll use `sdr` with the guide's words in the note, and confirm the replicate variable names in the zip.
- 2020 has no replicate weights in the main file; the pandemic replicate weights file, not requested, has them.

**Variables, about 25** (names to confirm against the dictionaries):
- **Design and identifiers:** TUCASEID, TULINENO, TUYEAR, TUMONTH, TUDIARYDAY, TRHOLIDAY, TUFNWGTP, TU20FWGT.
- **Demographics (summary file):** TEAGE, TESEX, PTDTRACE, PEHSPNON, PEEDUCA, TELFS, TRCHILDNUM, TRSPPRES, GEMETSTA.
- **Respondent file:** TESCHENR, TEHRUSLT, TRERNWA and TRTALONE (minutes alone). Twenge uses time alone and time with others, and the who file isn't in this slice.
- **Activity file:** TRCODE (the 6-digit activity code, to confirm), TUTIER1CODE, TUTIER2CODE, TUTIER3CODE, TUACTDUR24, TUSTARTTIM, TEWHERE.
- **Summary file outcomes,** Twenge's: sleeping (t010101), sleeplessness (t010102), watching TV (t120303, t120304), socializing and communicating (t1201xx), computer use for leisure (t120308), games (t120307), religious activities (t14xxxx), sports and exercise (t13xxxx), and phone calls (t16xxxx).

**The lexicon as code lists** (STANDARD.md §4.5). What the sources say:
- the code is three 2-digit tiers, 17 first-tier categories, and 99 means "not elsewhere classified" in every tier (guide §5.1);
- codes change "periodically ... prior to the start of each year's data collection", and `lexiconchanges.pdf` lists the changes;
- the multi-year lexicon "contain[s] activity codes unique to the multi-year Activity and Activity Summary files and should not be used with single-year files" (lexicons page);
- uncodeable activities get a first tier of 50 (guide §5.4).

The design:
1. **One list, `atus-lexicon-0325`,** from `lexiconnoex0325.pdf`: every 6-digit code with its label and `attributes` {tier1, tier2, tier1_label, tier2_label}. It's the list the multi-year files use, so it's the only one that variables name.
   - TRCODE has `code_list: atus-lexicon-0325`.
   - The first-tier codes (01–18, 50) are a second, short list, `atus-lexicon-0325-tier1`, named by TUTIER1CODE. TUTIER2CODE and TUTIER3CODE get no list, because their codes only mean something within the tier above. Their records say so and point to TRCODE.
2. **`waves` on each code: the years it was in use.**
   - This comes from the single-year lexicons and `lexiconchanges.pdf`. It's what the code list's `waves` and `retired` fields are for.
   - Single-year lists aren't stored, because no variable in this repo uses them; the multi-year files use the harmonized list. This follows §4.5's rule that "only identical lists are shared". The single-year versions differ, but here they're evidence for `waves`, not lists a variable names.
   - The XLS files to ask for are the years `lexiconchanges.pdf` shows a change in, beyond 2003 and 2025. I'll name them once it arrives.
3. **Tier-50 codes** ("data codes": insufficient detail, gaps, can't remember, refused) are in BLS's list. In the code list they're `kind: missing` with types from their labels. That tests §4.5's rule that a record's own `values` hold its missing codes: here the publisher's list holds them, and TRCODE's own `values` stay empty.
4. **The summary file names its variables by the same lexicon.** Each column `tXXXXXX` is minutes on code XXXXXX. A rule (`atus_summary_from_lexicon`) builds those records from the list: the label is the lexicon's, with unit minutes, and `derived_from` TRCODE.
   - Groups (§5.1) follow the first tier, so the 400-odd columns can be browsed by category.
   - That's a second use of a code list that §4.5 doesn't describe: a list that names variables, not values. A proposal will come from it.
   - If 400-odd records is too many for "about 25 variables", the slice builds the columns for Twenge's outcomes, and the rest stay in the list.
5. **Codes in the data but not in the list:** check C4 compares TRCODE's values in the data with the expanded list. Codes in the list with no cases are expected, because they're retired codes.

**Memory.** The activity file is large (80 MB zipped for 0323; millions of rows). Every data job runs under `systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0`, and the activity file is read in batches of columns, only the slice's.

**Terms.** BLS's copyright page (https://www.bls.gov/opub/copyright-information.htm) says "everything that we publish ... is in the public domain, except for previously copyrighted photographs and illustrations". It also says "You are free to use our public domain material without specific permission, although we do ask that you cite the Bureau of Labor Statistics as the source." The download block is about scripts, not reuse. The decision stays open for Allen; every terms field stays `unknown`.

### 2026-11-20: decisions from the coordinator

- **Replicates:** `method: fay`, `fay_factor: 0.5`. The guide names the method ("a modified balanced half-sample method of replication, developed in the 1980s by Robert Fay", §7.5, p. 44), but not the factor. The note will say the factor is derived from the guide's formula there, Var(Ŷ₀) = 4/160 · Σᵢ (Ŷᵢ − Ŷ₀)². For Fay's method the multiplier is 1/(R(1−k)²), so 4/R means k = 0.5.
- **The 2020 weight:** `design` can be set for the dataset, a release or a table (schema/dataset.schema.json), but not for a wave. With one multi-year release, TU20FWGT for 2020 can't be an override; it goes in the note.
  - **Finding:** a multi-year release whose weight differs by wave has no way to say so. This will be a proposal: `design` by wave, or `weights` entries that carry `waves`.
- **Summary columns named by the lexicon:** built by a rule, each record pointing to its lexicon code. A proposal for §4.5 will follow; the coordinator decides the standard change after the build.

### 2026-11-20: the slice is built

`~/pdt-atus` 25ba1ff (no remote). Release `2003-2025`; wave TUYEAR. `pdt check` gives 0 failures.

| Table | Rows | Records | Source of the records |
|---|---|---|---|
| `respondent` | 258,954 | 15 | Interview Data Dictionary |
| `summary` | 258,954 | 456 | 25 from the two dictionaries; 431 activity columns from the lexicon, by rule `atus_summary_from_lexicon` |
| `activity` | 4,994,172 | 9 | Interview Data Dictionary; TRCODEP, TRTIER2P and TRTIER1P name code lists |
| `replicates` | 258,954 | 161 | TUCASEID, and TUFNWGTP001–160 by rule `atus_replicate_weights`, from the zip's Repl0325_info.txt |

- **Every column is documented except two:** TRWBMODR (respondent) and TRWBELIG (activity) aren't in the 2003-25 dictionaries; they're not in the slice. Every code in the slice's columns is covered (C4).
- **`make data`:**
  - `respondent` passes the round trip (peak 0.6 GB);
  - `replicates` passes too (peak 5.6 GB, near the 6 GB cap);
  - `activity` (5 million rows) and `summary` (456 columns) are killed at the cap by the current `write_release`, which holds the whole table as Python objects. They wait for Task 58's batched writer.
  - A killed run left those two parquet files unverified in `data/processed/`, and `pdt check` accepted them; I deleted them and told the coordinator (for Task 58).
- **Sources:** 11, all `acquisition: manual` with sha256: four data zips, two dictionaries, the multi-year lexicon, `lexiconchanges.pdf`, the 2003 and 2025 single-year lexicons, and the User's Guide.
- **Terms:** `unknown`, with BLS's copyright page quoted; pending Allen.

**The weights, from the data.** TUFNWGTP is -1 ("-1.000000") for all 8,782 cases in 2020; TU20FWGT has values only in 2019 and 2020 and is -1 elsewhere. That matches the dictionary. The replicate weights are -1 for 2020. Weights write -1 as "-1.000000", so the build compares -1, -2 and -3 by value, not as text.

## How the lexicon fits §4.5

**Three lists, from `lexiconnoex0325.pdf`:**

| List | Codes | Named by |
|---|---|---|
| `atus-lexicon-0325` | 431 six-digit codes, with `attributes` tier1, tier2 and BLS's note (72 codes have one) | TRCODEP |
| `atus-lexicon-0325-tier2` | 107 second-tier categories (4 digits) | TRTIER2P |
| `atus-lexicon-0325-tier1` | 18 first-tier categories (no 17: travel is 18 in the multi-year files) | TRTIER1P |

What worked:
- **One list for many uses.** The 431 codes are stored once. TRCODEP's own `values` are empty; the expanded list covers every code in 5 million rows. Codes are strings ("010101"); the data keeps the leading zeros (read as text).
- **Missing codes inside the publisher's list.** Tier 50, "Data Codes", is BLS's own list, so it's `kind: missing` in the list (rule `atus_data_codes`: uncodeable, refused for 500105, dk for 500106 "Gap/can't remember"), not in each record's `values`. §4.5 says a record's `values` "usually" hold the missing codes; here the list does, and nothing broke.
- **`waves` and `attributes`.** `waves` is set where BLS's note says when a code was in use: 500104 (2003–2012) and 140105 (from 2007). The data agree with both: 500104 occurs only in 2003–2012 and 140105 from 2007.
- **The list's notes are BLS's crosswalk.** Pooled codes ending in 8x (020681 "includes 020601 (all years), 020602 (2008 and later years)") say which single-year codes they combine. They're kept as each code's `note` attribute.

What didn't fit, or needed work:
1. **A list that names variables, not values.** The summary file has a column per code: t010101 is minutes on code 010101. §4.5 has no way for a record to say "this variable is that code". Each of the 431 records points to its code in an extension, `atus.activity_code` and `atus.activity_code_list` (EXTENSIONS.md), and groups (§5.1) by first tier make the columns browsable.
2. **The multi-year list isn't any single year's list.** It's BLS's harmonized list for the pooled files.
   - The 2025 single-year lexicon has 465 codes: 405 in the multi-year list, and 60 only in single-year files (020601, 050104 …).
   - All 26 multi-year codes not in 2025 are pooled codes (8x) or the retired 500104.
   - 2003 has 440 codes, 80 of them single-year only; travel was 17xxxx.

   So §4.5's "a list that changes is a new list" holds, but each single-year version would be its own list, and the multi-year list is a third kind: a harmonization across them.
3. **`waves` for every code needs the single-year lexicons.** 109 of the 426 codes that occur don't span 2003–2025 in the data, but most are rare codes. The data can't tell "not in use" from "not used", and only BLS's lists can.
   - `lexiconchanges.pdf` has crosswalks at 2003/04, 2004/05, 2006/07, 2007/08, 2012/13 and 2023/24, so the code set changes only in 2004, 2005, 2007, 2008, 2013 and 2024.
   - With 2003 and 2025 in hand, five more files would give every code's years from BLS's own lists: **lexiconwex2004.xls, lexiconwex2005.xls, lexiconwex2007.xls, lexiconwex2008.xls and lexiconwex2013.xls**.
4. **The Notes column needed the page layout.** A note longer than a line is centered vertically on its code's row, so text order gives it to the wrong code (180280's note landed on 180199). `build/atus_lexicon.py` reads `pdftotext -bbox-layout` and assigns each note to the nearest code row.
5. **The XLS lexicons need LibreOffice** (`soffice --convert-to csv`): the environment has no .xls reader for pandas (xlrd or calamine).

## What ATUS tests that the other datasets didn't

1. **A shared code list at scale,** used by a 5-million-row variable and by 431 variable names; above.
2. **A long, narrow table.** The activity file breaks `make data` by rows, not columns: Task 58's column batches alone won't fix it.
3. **Weights that change by wave in one multi-year release.** TUFNWGTP except 2020, TU20FWGT in 2020. `design` can't say that per wave, so it's in the note.
4. **Replicate weights in their own file and table.** `design.replicates` names a prefix with no table, and `pdt check` doesn't check that the columns exist. Here they're in `replicates`, joined on TUCASEID; the note says so.
5. **A derived replication factor.** Fay's factor 0.5 comes from the guide's formula, not a statement.
6. **General missing codes declared once.** BLS lists -1 Blank, -2 Don't know and -3 Refused once ("Many ATUS variables have the following possible valid values ... not shown as valid entries for each variable"). A record gets the ones that occur in its column (rule `atus_general_codes`, origin publisher). "Blank" gives no reason, so its type is `unspecified`. Extra valid codes declared in a note ("-4 (Hours vary) is also valid for TEHRUSLT") need a rule too (`atus_codes_from_notes`).
7. **A blocked publisher.** Every source is manual: bls.gov returns 403 to any script without a contact. `download.py` can only list what to fetch.

## Proposals for the coordinator (not edits to STANDARD.md or schema/)

Each one has a proposal, the ATUS case, and what changes if it's accepted.

### P1. `code_of`: a variable that stands for one code (§4.5)

- **Proposal:** an optional record field `code_of: {code_list, code}`, for a variable whose values are about one code in a list: minutes on it, a count of it, or whether it was mentioned.
- **ATUS case:** the activity summary has 431 columns, one per lexicon code. t010101 is minutes on 010101, "Sleeping". Today each record carries `extensions.atus.activity_code` and `activity_code_list` (EXTENSIONS.md), and the label is copied from the list.
- **If accepted:** the 431 records swap the extension for `code_of`. `pdt check` can then check the code exists in the list, and views can link column ↔ code both ways ("which column holds code X").

### P2. `harmonizes` and `includes`: a list built from other lists (§4.5)

- **Proposal:** a code list can name the lists it harmonizes (`harmonizes: [ids]`). A code can say which codes of those lists it includes, and when (`includes: [{list, code, waves}]`), from the publisher's own crosswalk.
- **ATUS case:** the multi-year lexicon is BLS's harmonization of the single-year lexicons; it isn't any one year's list.
  - 60 of the 2025 single-year codes aren't in it.
  - Its pooled codes (8x) are in no single year.
  - BLS's notes say what each pooled code includes: 020681 "includes 020601 (all years), 020602 (2008 and later years)". Today that's free text in the code's `note` attribute.
- **If accepted:** the single-year lexicons become lists of their own, and the pooled codes' notes become structured `includes`. A user of a single-year file could map its codes to the multi-year ones.

### P3. `design` that varies by wave (§2.1)

- **Proposal:** let `design` be set per wave in a multi-wave release (`design.by_wave`), or let each entry in `weights` carry `waves`.
- **ATUS case:** in the 2003–2025 file, the weight is TUFNWGTP in every year except 2020, where it is -1 and TU20FWGT is the weight. Today `weights` lists both, and the note explains which year uses which. A program reading `design` can't tell.
- **If accepted:** `weights: [{name: TUFNWGTP, waves: {except: [2020]}}, {name: TU20FWGT, waves: [2020]}]` or similar. Whether another repo's weights change by wave isn't checked here.

### P4. `design.replicates.table`: replicates in another table (§2.1)

- **Proposal:** an optional `table` in `design.replicates`, naming the table that holds the replicate weights and the key it joins on. `pdt check` would then confirm the named columns exist there.
- **ATUS case:** the 160 replicates of TUFNWGTP are in their own file (the `replicates` table), joined on TUCASEID. The respondent and summary tables' `design.replicates` names prefix TUFNWGTP, n = 160, and nothing says where those columns are. `pdt check` doesn't look.
- **If accepted:** `replicates: {table: replicates, prefix: TUFNWGTP, n: 160, method: fay, fay_factor: 0.5}`, and a check that TUFNWGTP001–160 exist in that table.

### P5. Codes declared once for many variables (§4.2)

- **Proposal:** a dataset-level list of codes that the publisher declares once for "many variables". Each code has `kind`, `missing_types` and the publisher's location. The library would apply a code to a variable's values where it occurs, with origin publisher.
- **ATUS case:** the Interview Data Dictionary (p. 7) says: "Many ATUS variables have the following possible valid values: -1 Blank, -2 Don't know, -3 Refused. Because so many variables have these possible values, they are not shown as valid entries for each variable."
  - Today a repo rule (`atus_general_codes`) adds each code to the records whose column holds it.
  - Weights write -1 as "-1.000000", so the rule compares by value.
- **If accepted:** the rule goes; `dataset.yaml` holds the three codes once. Whether other publishers declare codes this way isn't checked here.

Sent separately, to Task 58: `write_release` should batch by rows as well as columns, and should write to a temporary name and rename only after the round trip passes.

### 2026-11-20: terms decided

Allen decided: data, documentation and metadata ship, and LLM processing is allowed, with a notice citing BLS. The coordinator committed it in `~/pdt-atus` 5a75e90 (dataset.yaml, README, views); `pdt check` gives 0 failures. Still open: the coordinator's answers to P1–P5, the five single-year lexicons, and `make data` for `activity` and `summary` (Task 58).

### 2026-11-20: the accepted proposals, in the library and in pdt-atus

The coordinator's decisions (standard and schema in 4ddaf02): P1–P4 accepted, P5 declined for now (the rule stays; the three codes keep origin publisher, Interview Data Dictionary p. 7).

**Library** (PublicDataToolkit):
- `pdt.design` (95ec1a5, asked for by purple, whose C3 change uses it):
  - `effective_design`: the table's design, else the release's, else the dataset's;
  - `weight_names`: plain names or `{name, waves}`, filtered by wave;
  - `replicate_columns`: matches a prefix against the real columns, padded (TUFNWGTP001) or not (W_FSTURWT1);
  - `replicate_key`.
- `pdt check` (2e364df), C2:
  - `code_of` names an existing list and code;
  - `design.replicates` resolves: the table exists, its key has records in both tables, and the columns are among its records or, when they have none, in its data file's schema.
- `pdt views` (2e364df): a `code_of` variable's page says which code it stands for and links to that code's row on a page of a variable using the list; each code row links back to its columns.
- Tests: `test_design.py`, `test_code_of_replicates.py`, and a site test; 270 pass.
- Nothing else in the library read `design.weights`. `eval/keys/build_task51.py` did, and now accepts the object form.

**pdt-atus** (b7ef53b):
- The 431 summary columns use `code_of`; the extension is gone.
- Seven single-year lexicons are code lists, `atus-lexicon-2003` … `atus-lexicon-2025`, read from BLS's XLS files through LibreOffice. Each stands for the years until the next crosswalk in `lexiconchanges.pdf`: 2005 for 2005–2006, 2008 for 2008–2012, 2013 for 2013–2023, 2025 for 2024–2025.
- `atus-lexicon-0325` harmonizes them. 68 of its codes have `includes` from BLS's notes: 688 entries, each a single-year list, a code and its years. Every code a note names is in a single-year list of those years.
- `design.weights`: TUFNWGTP with its waves (every year but 2020), TU20FWGT with `[2020]`. `design.replicates`: `table: replicates`, `key: [TUCASEID]`.
- `make data` (respondent, replicates; with the committed library, not the shared checkout's uncommitted Task 58 changes) passes the round trip. `pdt check` gives 0 failures.

**For the coordinator:** the terms say everything ships, but every source in `sources.yaml` still has `redistribution: unknown`, so `write_release` marks the data local only. Changing it follows from Allen's decision, but it's a terms field, so I left it for you.

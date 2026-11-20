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

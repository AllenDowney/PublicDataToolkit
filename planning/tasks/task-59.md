# Task 59 — A Cooperative Election Study slice

**Status:** `DOING (red)`, claimed 2026-11-20.

The Cooperative Election Study (CES, formerly CCES), an online survey of U.S. adults run by YouGov since 2006, released on Harvard Dataverse. It has a cumulative common-content file and a file per year, so it's the second cumulative↔yearly case after the ANES.

1. Find the cumulative common-content file and the yearly common-content files on Dataverse, their guides, and the Dataverse license. Leave the terms decision for Allen.
2. `~/pdt-ces` from the template (`copier copy --vcs-ref v0.1.0`), no remote.
3. A slice: the cumulative file and two or three yearly files, linked by `derived_from` where the cumulative guide documents how a variable was built from the yearly items.
4. `make data` round trip under the memory cap; `pdt check` 0 failures.
5. Here: what the CES tests, with proposals.

**Files:** `~/pdt-ces/` (new, no remote); this file; the Task 59 block on the board.

## Progress

**Notes so far (red, 2026-11-20):**
- **Sources:** four Dataverse datasets, each showing the license "CC0 1.0" with no custom terms: Cumulative CES Common Content (doi:10.7910/DVN/II2DB6, version 12, 2006–2025, 718,955 rows × 109 columns) and the 2020, 2022 and 2024 Common Content (E9N6PH v4, PR4L8P v4, X11EP6 v9). Each has a guide PDF; the yearly Stata files are 850 MB–1 GB.
- **The mapping is in code, not the guide.** The cumulative guide (Kuriwaki) gives each variable's wording, years and limitations, but not which yearly variable it comes from. Its "source code repository", github.com/kuriwaki/cces_cumulative (no license file), does: `std_name()` in `05_functions-stack.R` renames each year's items (`approval_pres = CC20_320a`), and `05_stack-cumulative.R` stacks the rest by the same name (`find_stack(ccs, pid7)`). Pinned at `0fd71db`; three files are sources (kind `crosswalk`), and the `derived_from` links cite them with the line quoted.
- `~/pdt-ces` from the template (`eafe04a`), no remote. Releases: `cumulative` (table `cumulative`, key year + case_id) and `2020`, `2022`, `2024` (table `common`, key caseid). Slice: 22 cumulative variables and their yearly sources (build/slice.yaml).
- **Missing codes:** the cumulative file has only Stata system missing, printed "(Missing)" in the guide with no reason (`unspecified`, rule `ces_system_missing`). The CES never marks codes missing: "Not Sure", "Don't Know", "Skipped", "Prefer not to say" are ordinary numbered answers in the files and the guides. They're typed by a whole-label rule (`ces_missing_from_label`).
- The cumulative turnout item is `intent_turnout_self`, a factor rebuilt from `intent_trn`'s labels (three "I Plan to Vote Before November Nth" merged), so its link carries `codes_changed` and `labels_changed`.

### Result so far (red, 2026-11-20)

`~/pdt-ces` `f14d80c`. No remote. `pdt check`: 0 failures. Terms are `unknown`, for Allen. **Pending: `make data`**, which waits until orange's Task 58 changes to `pdt.readers` and `pdt.release` are committed (they're in the shared working tree now).

| Release | Table, key | Records | Missing codes (by the label rule) |
|---|---|---|---|
| `cumulative` (2006–2025, v12) | `cumulative`, year + case_id | 22 | 25 (9) |
| `2020` | `common`, caseid | 18 | 49 (39) |
| `2022` | `common`, caseid | 18 | 48 (38) |
| `2024` | `common`, caseid | 18 | 47 (38) |

- **Links: 86.**
  - 60 `derived_from`, from each cumulative variable to its source in each year, `origin: publisher`. Each cites one of the three build-code files, quotes the line and says which year's rows it covers.
  - The extra relations come from what the code does: `renamed` (`approval_pres` ← `CC20_320a`), `codes_changed` (`faminc` coarsens `faminc_new`'s brackets; `weight_cumulative` rescales), and `labels_changed` (`race`'s code 6 relabeled "Mixed"). `gender` ← `gender4` from 2021 drops codes 3 and 4. `intent_turnout_self` and `voted_pres_20` are rebuilt from labels.
  - 26 `same_item` between consecutive yearly releases, by rule `ces_same_name_same_documentation`: same name, label, question and codes. Two pairs are reported instead: `caseid` 2020→2022 ("Panman Sample ID" became "Case ID"), and `birthyr` 2022→2024 (only 2024's guide tabulates it).
- **A check, not a source:** the build compares the cumulative file's codes for each year with the yearly file's. Every difference is a recode the build code states. One, `voted_pres_20`'s, I had missed: the check found it, and the code (`clps_pres20()`) confirmed it.
- **Views:** `agent/` 4 shards, `docs/` 61 files, `export/data-dict/` 4 files.

### What the CES tests that earlier datasets didn't

1. **A cumulative file whose crosswalk is code.** The guide documents each harmonized variable, but not where it comes from. That's in the author's R build code. The code works as a crosswalk: it's precise (`approval_pres = CC24_312a`), versioned by commit and readable, but it isn't documentation and has no license. Links cite it as `origin: publisher` with `kind: crosswalk` sources pinned to a commit. A change in the code changes the links, so the pin matters.
2. **`derived_from` that holds for one year's rows.** Each link from a cumulative variable to a yearly item applies only to that year's rows. The link schema has nowhere to say so except `note`. ANES's cumulative links would need the same thing.
3. **Recodes visible only by comparing data.** Several cumulative variables are rebuilt from labels (`clps_pres20()`, `intent_turnout_self`). Where the code says so, the link records it. Comparing the two files' codes year by year is a cheap check that found one recode missing from the slice.
4. **A publisher that never marks codes missing.** "Not sure", "Don't know", "Prefer not to say", "skipped" and "not asked" are ordinary numbered answers in both the data and the guides. All typed missing codes come from a whole-label rule. Two exceptions come from the publisher: the yearly guides say system missing means skipped or not asked, and the cumulative guide prints system missing as "(Missing)" without a reason (`unspecified`).
5. **Labelled codes that never occur.** The 2020 file labels 8/98 "skipped" and 9/99 "not asked" on every variable, but skips are stored as system missing, so those codes have no cases.
6. **Yearly items are linked only through the cumulative file.** `CC20_302` and `CC22_302` both feed `economy_retro`, but no source says the two yearly items are the same. `pdt diff` lists them as rename candidates, and they stay unlinked.

### Proposals (not made; for the coordinator)

1. **A `waves` field on a link** (or on `derived_from`), saying which waves of the `from` variable the link covers. It would replace the note "For the cumulative file's 2020 rows" here, and fits ANES CDF ↔ yearly too.
2. **A source kind for build code** (`build_code`), or guidance that `crosswalk` covers it. Here the publisher's own harmonizing code is the only statement of the mapping.
3. **Codebook counts vs. data counts.** `values[].n` is the codebook's count. The CES guides print tabulations, but parsing them is a second parser for numbers the data already gives. A separate field for data counts (or a provenance note allowing them) would let builds record them; C4 already reads the data.
4. **Optional, for discussion:** whether two yearly items that the cumulative file stacks with no recode (`derived_from` with only `renamed`) may be linked to each other by a rule that cites the build code. That's an inference from two publisher statements, so it may not count as a publisher assertion.

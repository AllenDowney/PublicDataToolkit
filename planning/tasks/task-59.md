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

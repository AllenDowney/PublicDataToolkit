# Task 37 — Count test in the NSFG rule; occurring-codes field; Cases column

**Status:** `DONE (red)` (see the update below)

The coordinator's answers to Task 35's questions:

1. The count test goes in the NSFG rule, as `nsfg_identical_documentation` 0.5. OUTCOME_I then gets a `codes_changed` link by rule, not no link: method 1 was used in 7 cases, then not at all.
2. `sources.yaml` has `lists_only_occurring_codes: true` (a3f6e1f, STANDARD.md §2.2). Set it on the NSFG codebooks, and have `pdt diff` and the rule read it instead of the flag; keep the flag only as an override.
3. Attribution: add nothing new under Allen's name. Task 35's three hand links get author "Claude (PublicDataToolkit Task 35)", keeping the note. The other hand facts in the repos wait for Allen's decision.
4. A "Cases" column in the site's code tables when `n` is present.

Then regenerate and report.

**Files:** `lib/pdt/compare.py`, `lib/pdt/diff.py`, `lib/pdt/site.py` and their tests; in `pdt-nsfg`, `sources.yaml`, `build/` and the generated records and views; this file.

**Status update:** `DONE (red)`, 2026-11-19; committed locally, not pushed.

## What changed

- **`pdt.compare.absent_by_chance(n, total_here, total_there)`**: a code missing from one release, in documentation that lists only occurring codes, plausibly had no cases there when its count, scaled to that release's total for the variable, is under 5. `total_cases(record)` sums `values[].n`.
- **`pdt diff`** reads `lists_only_occurring_codes` from `sources.yaml` for the source documenting each record (its `source_location`, or the values' or record's provenance source), separately for each side. `--omitted-codes-have-no-cases` remains as an override that treats every source this way.
- **NSFG `sources.yaml`:** all 17 codebook sources have `lists_only_occurring_codes: true`. Checked against the text: the NCHS 2022-2023 codebooks print no zero rows (0 of 26,953 count rows). The ICPSR-format 2017-2019 codebooks print 3 of about 45,000: female Section B's 98 and 99 (Refused, Don't know) and one Section C date range. What a comparison relies on still holds: a code that's absent had no cases.
- **NSFG rule `nsfg_identical_documentation` 0.5:** a code on one side only is allowed when it's in the other release's `valid_range` (AGE_R 49–50), or when the other side's codebook lists only occurring codes and `absent_by_chance` holds (PREGORDR 15–16, AGEPREG 97, HIEDUC_I 1). Any other one-sided code makes the link `codes_changed` instead of leaving the pair unlinked:
  - **OUTCOME_I:** "multiple regression imputation", 7 cases in 2017-2019, none in 2022-2023;
  - **HIEDUC_I:** code 2, "logical imputation", 11 cases in 2022-2023, none in 2017-2019.
- **Links: 18** (2 publisher, 5 hand, 7 by 0.5, 4 by `nsfg_count_labels_reworded`). **Every rule link agrees with `pdt diff`**. The 7 that differ are NCHS's MARSTAT links (the diff also sees `labels_changed`) and the 5 hand links (`universe_changed` is a judgment).
- **Attribution:** the 5 hand links from Task 35 now have author "Claude (PublicDataToolkit Task 35)". Their notes say it was decided at the coordinator's request. No other hand facts were changed.
- **Site:** a variable page's code table has a "Cases" column when its values have `n`, with a line saying where the counts come from. Only NSFG has `n` so far.

## Regenerated

- `pdt-nsfg` (88c0521), and `pdt-anes-cdf` and `pdt-fars` for orange's `kind` (Task 36). `pdt check`: 0 failures in each.
- **`pdt-gss` not regenerated.** The gss thread has uncommitted records (5 files under `metadata/`), so its views should be built after it commits. A first attempt was stopped partway; its partial output in `agent/` and `docs/` was restored to HEAD and removed, so `pdt-gss` holds only the gss thread's own changes.

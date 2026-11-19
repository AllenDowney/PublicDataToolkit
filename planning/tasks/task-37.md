# Task 37 — Count test in the NSFG rule; occurring-codes field; Cases column

**Status:** `DOING (red)`

The coordinator's answers to Task 35's questions:

1. The count test goes in the NSFG rule, as `nsfg_identical_documentation` 0.5. OUTCOME_I then gets a `codes_changed` link by rule, not no link: method 1 was used in 7 cases, then not at all.
2. `sources.yaml` has `lists_only_occurring_codes: true` (a3f6e1f, STANDARD.md §2.2). Set it on the NSFG codebooks, and have `pdt diff` and the rule read it instead of the flag; keep the flag only as an override.
3. Attribution: add nothing new under Allen's name. Task 35's three hand links get author "Claude (PublicDataToolkit Task 35)", keeping the note. The other hand facts in the repos wait for Allen's decision.
4. A "Cases" column in the site's code tables when `n` is present.

Then regenerate and report.

**Files:** `lib/pdt/compare.py`, `lib/pdt/diff.py`, `lib/pdt/site.py` and their tests; in `pdt-nsfg`, `sources.yaml`, `build/` and the generated records and views; this file.

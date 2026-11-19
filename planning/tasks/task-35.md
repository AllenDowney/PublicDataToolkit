# Task 35 — Shared text comparison; NSFG links and code counts

**Status:** `DONE (red)` (see the update below)

From Task 34's proposals, accepted by the coordinator:

a. Move `compare_text` (`text_only`, `reference_only`) into a new module, `lib/pdt/compare.py`, with tests, and have `diff.py` use it.
b. Red owns `pdt-nsfg` for this task. Rebuild the NSFG link rule as `nsfg_identical_documentation` 0.4 on `compare.py`. EVRMARRY's and FMARITAL's change to "opposite-sex spouse" is a change of meaning, not `same_item`: link them `labels_changed` plus `universe_changed`, with a note quoting both labels. Check the other same_item links against `pdt diff` the same way.
c. NSFG's codebooks print frequencies: fill `values[].n` (new in variable.schema.json). Rerun `pdt diff` and see whether AGE_R 49–50 and PREGORDR 15–16 read as codes with no cases instead of new codes; teach `pdt diff` to use `n`.
d. Regenerate `pdt-nsfg`'s views; `pdt check` with 0 failures; report.

**Files:** new `lib/pdt/compare.py` and its tests; `lib/pdt/diff.py`; in `pdt-nsfg`, `build/` and the generated records and views; this file.

**Status update:** `DONE (red)`, 2026-11-19; committed locally, not pushed.

## a. `lib/pdt/compare.py`

[`compare_text(a, b)`](../../lib/pdt/compare.py) returns `same`, `text_only` (case, whitespace, dashes), `reference_only` or `changed`. `reference_only` covers questionnaire item references (`IC-9`, `JB-4`, `FC A-2b`), "(Computed in FC A-2b)", and a type marker like 2017-2019's "(RECODE)". `is_change()` is true only for `changed`. `pdt diff` and the NSFG build use it. Tests: [`lib/tests/test_compare.py`](../../lib/tests/test_compare.py). The case-insensitive parts are scoped, so lowercase text like "covid-19" isn't treated as a reference.

## b. NSFG links: `nsfg_identical_documentation` 0.4

**What 0.3 missed:** it compared item references, question texts and value labels, but not the variable label or the universe. That's how EVRMARRY ("Whether R was ever married" → "Ever married to an opposite-sex spouse") linked as `same_item`.

**0.4** ([`pdt-nsfg/build/build_slice.py`](../../../pdt-nsfg/build/build_slice.py)) compares label, universe, question texts and value labels with `pdt.compare`:
- `text_only` and `reference_only` differences are allowed, and each link's note lists them;
- a changed variable label gives `labels_changed`, with both labels in the note;
- a changed universe leaves the pair unlinked, with the reason in `build/report.md`.

**Hand links** (`slice.yaml` `hand_links`; `origin: hand`, author Allen Downey, through the coordinator) for the variables whose 2022-2023 label counts only opposite-sex spouses. Each is `labels_changed` + `universe_changed`, and its note quotes both labels:
- EVRMARRY (female, male);
- FMARITAL (female, male);
- FMARIT (female), which has the same change as FMARITAL.

**Links: 17, down from 21.**

| Source | Links |
|---|---|
| NCHS's change summary (MARSTAT) | 2 |
| Hand | 5 |
| Rule 0.4 | 6: CASEID female and male (same_item), male RELIGION (same_item; "(RECODE)" is a type marker), OUTCOME_I (same_item), AGEPREG and PMARPREG (labels_changed: labels reworded) |
| `nsfg_count_labels_reworded` | 4: AGE_R female and male, RSCRAGE, PREGORDR |

**The other same_item links from 0.3, checked against the diff:**
- **No longer linked:** RELDLIFE (female, male) and BIRTHORD, whose universe text changed. RELDLIFE's universe refers to a renumbered item ("IC-5 RELNOW = 2-11" vs "IC-4 RELNOW = 1-8"). Whether the population changed is a judgment. Pregnancy CASEID is unlinked too: its universe added "(respondent-level variable)". It's obviously the same ID, but the rule can't tell that from the text.
- **Now `labels_changed`:** AGEPREG ("Age at pregnancy outcome" → "R's age in years when pregnancy ended") and PMARPREG ("1st marriage (premaritally)" → "first marriage (premarital)").

## c. `values[].n`, and what it tells `pdt diff`

Every NSFG value now has `n`, the count the codebook prints: 98 of 101 records (the other 3 have no codes). The records are unchanged otherwise.

`pdt diff` now:
- shows `n` on added and dropped codes;
- calls a one-sided code inside the other release's `valid_range` **`in_other_range`**, not a change. **AGE_R 49–50 is resolved:** 2017-2019 prints them as a range row ("49-50"), so they weren't new codes. CURRPRTS 2–3 is the same case.
- With `--omitted-codes-have-no-cases`, for documentation that lists only codes that occur, calls a one-sided code **`no_cases_in_other`** when its count, scaled to the other release's total for the variable, is under 5. A zero is then chance (Poisson P(0 | 5) < 1%). **PREGORDR 15–16 (1 case each) and AGEPREG 97 (3) are resolved.**

**`n` alone isn't enough.** The NSFG codebooks print no zero rows, so a code missing from one release could be a code with no cases or a code that no longer exists. The count tells them apart: MARSTAT 6, "Never been married", had 2,820 cases in 2017-2019, and its absence from 2022-2023 can't be chance. It's a recoding, and it stays `codes_changed`. The plain subset test (rule 0.3's allowance) would have called it "no cases".

**Agreement now:** `pdt diff --omitted-codes-have-no-cases` matches 9 of the 17 links. The differences:
- MARSTAT: the diff also sees `labels_changed`; the link uses NCHS's words.
- The 5 hand links: `universe_changed` is a judgment the records can't show.
- OUTCOME_I: the rule allows code 1 (7 cases in 2017-2019) by the subset test; the count test says 7 cases can't vanish by chance, so the diff reads `codes_changed`.

## d. `pdt-nsfg`

- Data rebuilt: 6 files, every round trip exact.
- Views regenerated; `pdt check`: 0 failures.
- Commit 3548e0b.

## For the main thread

1. **OUTCOME_I:** should the NSFG rule use the count test (`pdt.diff`'s `no_cases_in_other`) instead of the subset test? OUTCOME_I would then be unlinked (`codes_changed`: 2017-2019's "MULTIPLE REGRESSION IMPUTATION" code isn't in 2022-2023). It would also make the rule and the diff agree.
2. **"The documentation lists only codes that occur"** is a property of a source, not of `pdt diff`. A field in `sources.yaml` (say `lists_only_occurring_codes: true`) would let the diff and the rules read it, instead of a command-line flag.
3. **The hand links' attribution:** author Allen Downey, decided through the coordinator in this task. Allen should confirm.
4. **The site doesn't show `values[].n` yet.** That would be a "Cases" column in each variable page's code table; it's a small change in `site.py` if wanted.

# Task 35 — Shared text comparison; NSFG links and code counts

**Status:** `DOING (red)`

From Task 34's proposals, accepted by the coordinator:

a. Move `compare_text` (`text_only`, `reference_only`) into a new module, `lib/pdt/compare.py`, with tests, and have `diff.py` use it.
b. Red owns `pdt-nsfg` for this task. Rebuild the NSFG link rule as `nsfg_identical_documentation` 0.4 on `compare.py`. EVRMARRY's and FMARITAL's change to "opposite-sex spouse" is a change of meaning, not `same_item`: link them `labels_changed` plus `universe_changed`, with a note quoting both labels. Check the other same_item links against `pdt diff` the same way.
c. NSFG's codebooks print frequencies: fill `values[].n` (new in variable.schema.json). Rerun `pdt diff` and see whether AGE_R 49–50 and PREGORDR 15–16 read as codes with no cases instead of new codes; teach `pdt diff` to use `n`.
d. Regenerate `pdt-nsfg`'s views; `pdt check` with 0 failures; report.

**Files:** new `lib/pdt/compare.py` and its tests; `lib/pdt/diff.py`; in `pdt-nsfg`, `build/` and the generated records and views; this file.

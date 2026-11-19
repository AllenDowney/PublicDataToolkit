# Task 40 — `pdt diff` pairs by links first

**Status:** `DOING (red)`

From purple's YRBSS (Task 29): each YRBSS release renumbers its variables, so 2021's q26 "Considered suicide" is 2023's q27, and 2023's q26 is "Sad or hopeless". `pdt diff` pairs by name, so it reports a wording change for q26 and a bogus rename.

Make `pdt diff` pair by the links between the two releases first, and by name only for the variables no link pairs. Flag names that match across the releases when the links say they're different variables. Test on `~/pdt-yrbss`.

**Files:** `lib/pdt/diff.py`, its tests, the `release-diff` skill, this file.

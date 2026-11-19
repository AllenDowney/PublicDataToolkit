# Task 27 — Shared derived rules in the library

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DOING (fars)` — assigned 2026-11-19. fars does `lib/` and switches over pdt-anes-cdf and pdt-fars; the gss and nsfg threads switch their own builds over, since they're working in those repos

`scale_signature_from_valid_labels` is copied into all four dataset builds, but STANDARD.md §6 puts derived rules in the shared library, and copies drift (as `check_metadata.py` did). Move it into `lib/pdt/` (e.g. `derived.py`, with tests), versioned, with one table of signatures that every dataset uses. Change the four builds to call it. Found by the instructions thread (Task 24).

**Files:** new `lib/pdt/derived.py` and its tests; the `build/` scripts of the four dataset repos (coordinate with any thread working in a repo).

**Done (fars thread, 2026-11-19), sent while the board was being restored:** `lib/pdt/derived.py` has rule `scale_signature_from_valid_labels` 0.2, with `lib/tests/test_derived.py` (5 tests).
- **One table, the union of the four copies:** yes_no (yes/no in either order), favor_oppose, spending_3. Labels match ignoring case and surrounding spaces. A valid range in degrees is `thermometer`, taken from the ANES build.
- `scale_signatures(records, per_release=True)` writes the derived lines with the target `{release, table, variable}`. With `per_release=False` there's one line per variable, as the GSS and ANES builds already do.
- **What was in one table but not the others:**
  - favor_oppose and thermometer were only in ANES's;
  - spending_3 was only in GSS's;
  - yes_no was in GSS's (lowercase), NSFG's ("Yes", "No") and FARS's ("No", "Yes"), and each matched only its own case and order.
- **Switched:** pdt-fars (`fdbcd30`) and pdt-anes-cdf (`4326270`). Their signatures are unchanged; only `rule_version` went from 0.1 to 0.2. nsfg has switched pdt-nsfg's build (to be committed with Task 22): `pmarpreg` in both releases.
- **Waiting:** gss switches pdt-gss's build. Computed read-only from its committed records, the GSS gains `gunlaw` and `cappun` as favor_oppose (27 → 29 lines).

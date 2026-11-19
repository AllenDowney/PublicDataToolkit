# Task 44 — One line per variable across releases

**Status:** `DONE (red)`, 2026-11-19; committed locally, not pushed.

Task 42's proposal 2, accepted by the coordinator.

- **In the catalog,** collapse a variable's lines across releases by its links (`same_item`, `renamed`, and relabels), and show its release span and names: "BRFSS ADDEPEV2 2011–2018 → ADDEPEV3 2019–2023".
- **A change of meaning** (`universe_changed`, `codes_changed`) keeps lines separate, but shows them together with the relation.
- **In each repo's agent index,** use the same collapse if it fits, keeping the per-release detail.

Rerun Task 42's three test questions, and report the line counts before and after.

**Files:** a new `lib/pdt/chains.py` and its tests; `lib/pdt/catalog.py`; `lib/pdt/views.py` if the agent index uses it; this file.

## What was built

- **[`lib/pdt/chains.py`](../../lib/pdt/chains.py)** joins a variable's records across releases (union-find) along links whose relations keep the meaning: `same_item`, `renamed`, `labels_changed` or `data_revised`.
  - A link that changes the meaning (`codes_changed`, `wording_changed`, `universe_changed`) relates two chains instead of joining them.
  - Links that aren't one to one, and links within one release, are left out.
  - `names_text()` writes a chain as "ADDEPEV2 2011–2016" or "q25 sadc-2021 → q26 sadc-2023".
  - `ordered_with_related()` puts a related chain right under the one it continues.
- **The catalog** writes one line per chain. A related chain goes under the one it continues, marked "↳ codes_changed:". `catalog.jsonl` has one object per variable with its `members` (each release's name) and `related`. `pdt search --catalog` adds `variables` (hits grouped by chain, each with its related chains) and `variable_count`.
- **Each repo's agent index:** a repo with several releases gets `agent/variables.txt` (split at about 20k tokens), one line per variable across all its releases, with the same marks. `index.md` lists it under "Across releases", and C8 checks it. The per-release shards are unchanged, so the per-release detail stays.
- **`views.runs`** writes runs of waves that are ranges themselves with "to": NSFG "2017-2019 to 2022-2023", not "2017-2019-2022-2023".

## Examples, from the regenerated `agent/variables.txt`

- **YRBSS:** `national.q25 sadc-2021 → q26 sadc-2023 | 1999-2023 | Sad or hopeless`, then `national.q26 sadc-2021 → q27 sadc-2023 | Considered suicide`. The renumbering is visible.
- **NSFG:** `female.CASEID 2017-2019 → CaseID 2022-2023` is one line. `female.FMARITAL 2017-2019`, then `↳ labels_changed, universe_changed: female.FMARITAL 2022-2023` (the opposite-sex relabel).
- **FARS:** `accident.LGT_COND 2017–2024` is one line. `accident.HARM_EV 2017`, then `↳ codes_changed, labels_changed: accident.HARM_EV 2024`.

## Findings

- **BRFSS shows ADDEPEV as three lines,** and that's by design. Green's rule (STANDARD.md rule 2: a link records only continuity the publisher asserts) doesn't link 2016 → 2017, because the 2017 wording differs. It doesn't link ADDEPEV2 2018 → ADDEPEV3 2019 either: CDC states renames only in its "Calculated Variables" documents, and 2019's doesn't mention ADDEPEV. The same holds for SEX → SEX1 → SEXVAR and _RACEGR2 → _RACEGR3. The catalog shows only what the publishers assert. A reader-facing grouping would come from green's own `concept` grouping in `build/slice.yaml`, which is the repo's, not the publisher's (approximate, like Task 42's proposed concept vocabulary).
- **The GSS (blue) and BRFSS (green)** have uncommitted records, so their `agent/variables.txt` waits for those threads' next `make views`.

## Line counts, before and after

The catalog (`~/pdt-catalog`, regenerated after Allen's decision that CPS ASEC and Chicago crimes ship) now holds 8 datasets. "Before" is one line per record in the releases in scope (Task 42), and "after" is one line per variable.

| Dataset | Before | After |
|---|---|---|
| anes-cdf | 39 | 39 |
| brfss | 295 | 76 |
| chicago-crimes | 27 | 27 |
| cps-asec | 287 | 44 |
| fars | 80 | 48 |
| gss | 6,943 | 6,943 |
| nsfg | 104 | 95 |
| yrbss | 29 | 29 |
| **all** | **7,804** | **7,301** |

The GSS, ANES, YRBSS and Chicago have one release in scope each, so nothing collapses there.

**The test questions** (names and labels):

| Question | Before | After | Notes |
|---|---|---|---|
| Sadness or depression | 32 | 22 | BRFSS 26 lines → 3 (ADDEPEV2 2011–2016, ADDEPEV2 2017–2018, ADDEPEV3 2019–2023) |
| Marital status | 45 | 39 | CPS A_MARITL 2019–2025 is one line (7 before). NSFG's marital variables stay apart, each 2022-2023 line under its 2017-2019 one, because their links say the meaning changed |
| Age at first marriage | 4 | 4 | GSS agewed, agewedcr, marcohrt; NSFG PMARPREG 2017-2019 → pmarpreg 2022-2023 |

CPS ASEC's `agent/variables.txt` waits for yellow's next `make views`, because its records had uncommitted changes when the catalog was built. The catalog read the working copy.

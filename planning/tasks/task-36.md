# Task 36 — Non-survey data in the library

**Status:** `DONE (orange)`, 2026-11-19.

The library side of the standard changes from Task 33's proposals (STANDARD.md and `schema/`, commit `827af76`):

1. **`check.py`:** C5 checks only a file's `data_waves`. C6 reports missing question text only when `kind` is `survey`, or absent. C11 checks that the README contains `terms.notice` when it's set.
2. **`download.py`:** for a `live` source, `--check` reports "changed since snapshot <date>", not a mismatch; a fetch keeps the new file as `.new`, as usual.
3. **The dataset repos:** pdt-chicago-crimes gets `data_waves: ["2024"]`, live sources, `kind: portal` and the City's disclaimer as `terms.notice`. pdt-gss, pdt-anes-cdf and pdt-nsfg get `kind: survey`; pdt-fars gets `kind: administrative`. `pdt check` on all five.
4. Tests.

**Files:** `lib/pdt/check.py`, `lib/pdt/download.py` (from red for this task) and their tests; `dataset.yaml`, `sources.yaml` and the README in the dataset repos; this file and Task 36's block on the board.

## Done (orange, 2026-11-19)

Library commit `40ef5f8`, with 6 tests. pytest: 174 passed, 1 skipped.

- **C5:** `data_waves` on a table overrides the release's. Availability is checked only for those waves.
- **C6:** with `kind` `administrative` or `portal`, it reports missing `description` instead of missing question text. No `kind` counts as `survey`.
- **C11:** when `terms.notice` is set, the README's terms section must contain it verbatim. Line breaks, extra spaces and blockquote markers are ignored.
- **`pdt download`:** a `live` source whose file differs from the recorded snapshot is `changed since snapshot <fetched_on>`, not a mismatch. `--check` counts these separately and doesn't fail on them. A fetch that differs keeps the new copy as `<path>.new` and isn't counted as a failure: a new snapshot is a new release.

**The dataset repos:**

| Repo | Change | Commit |
|---|---|---|
| pdt-chicago-crimes | `kind: portal`; `data_waves: ["2024"]` on `crimes`; all 8 sources `live`; the City's disclaimer as `terms.notice`, verbatim from the snapshot's terms page, and quoted in the README; views regenerated | `daffcc0` |
| pdt-gss, pdt-anes-cdf, pdt-nsfg | `kind: survey` | `824638b`, `5a8d5d6`, `dedc4ed` |
| pdt-fars | `kind: administrative` | `3bd8f7e` |

**`pdt check`:**
- pdt-chicago-crimes has 0 failures. C5 no longer warns: there were 21 warnings before `data_waves`.
- The other four fail only C8, because `kind` changed `dataset.yaml` after their views were generated. Red regenerates their views.
- With the views current, they'd pass as before. FARS's C6 now reports missing descriptions rather than questions.

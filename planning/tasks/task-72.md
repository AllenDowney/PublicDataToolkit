# Task 72 — Make `pdt check` fast on the full GSS

**Status:** `DONE (blue)`, 2026-11-20. The coordinator asked for it after the Task 71 run: the full-GSS `pdt check` took 40 minutes outside the data checks. The target was under 2 minutes.

**Files:** `lib/pdt/schemas.py` (`inline_refs`, used by `validators`), `lib/pdt/check.py` (`Repo.name_index`, `Repo.resolve`, duplicate counts in `check_references`), `lib/tests/test_check_speed.py`.

## Where the time went

I timed each check on a `git archive` copy of pdt-gss, and on the real repo with a read-only script, under the 6 GB cap. GSS has 13,885 variable records, 6,974 links and 654 groups.

| Check | Before | What |
|---|---|---|
| C1 `check_schemas` | 30–50 s | jsonschema resolved every `$ref` through the registry each time it was used: 47,000 lookups per 300 records, most of them inside `values` |
| C2 `check_references` | 22–26 s | `Repo.resolve` scanned all 13,885 records for each of 26,481 references (group members, link ends, corrections): quadratic. Duplicate names used `list.count` in a loop (1.4 s) |
| C8 `check_views` | 0.2–0.4 s | hashing the inputs and checking that 9,500 view files exist: not slow |
| `check_data` | 0.5 s | GSS's data files are stale, so they're skipped |
| everything else | about 1 s | |

So the whole check took about 60–75 s, not 40 minutes. The 40-minute run (Task 71, in the 13-repo loop) doesn't reproduce: the same code and repo took 60 s afterwards. It was probably contention, or the shared working tree being mid-change at the time. I couldn't find a cause in the code.

## Fixes

- **Inlined schemas.** `validators()` now replaces each schema's `$ref`s with their targets once, when it builds the validators. A `$ref` beside other keywords becomes `allOf [target, rest]`, which validates the same in draft 2020-12. A schema with recursive refs keeps them, resolved through the registry. The toolkit's schemas have none. C1 is about 2.2 times faster.
- **Name index.** `Repo.resolve` looks names up in an index of `{name: [(release, table, record)]}`, in the same order as before. The index is rebuilt if the tables change shape.
- Duplicate names and ids are found with `collections.Counter`.

## Same results

- **Tests** (`test_check_speed.py`):
  - The inlined validators give the same errors, path and message, as registry-resolved ones on every schema example, and on more than 1,000 broken copies of them (wrong types, bad enum values, missing and unexpected keys, at each level).
  - No inlined schema has a `$ref` left, and property names are kept.
  - Recursive refs raise.
  - `resolve` matches the old scan for every name, release and table combination, and sees changes to the tables.
- **Full suite:** 319 pass in the working tree, and 309 on the committed tree alone.
- **`pdt check` output before and after:** byte-identical apart from timing, on pdt-gss, pdt-nsfg, pdt-meps and pdt-hints. "Before" is a scratch copy of the library with only these changes reverted.

| Repo | Before | After |
|---|---|---|
| pdt-gss | 76 s | 27 s (18 s on a quieter run) |
| pdt-hints | 3.7 s | 2.6 s |
| pdt-nsfg | 1.5 s | 1.3 s |
| pdt-meps | 1.5 s | 1.3 s |

The rest of GSS's time is mostly C1, about 20 s of jsonschema. A compiled validator would cut it further: fastjsonschema is installed but doesn't support draft 2020-12, and jsonschema-rs would be a new dependency. Not needed for the target.

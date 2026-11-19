# Task 41 — Shared code lists

**Status:** `DONE (orange)`, 2026-11-19; the GSS lists are a follow-up, when blue frees pdt-gss.

Implements [Task 38's design](../code_lists_design.md), accepted as written (option C). Lists shared across datasets are out of scope, and §10 says so.

1. **STANDARD.md and `schema/`:** apply the design's diffs. The coordinator handed over these sections for this task: §2 layout, §4.1, §4.2, the new §4.5, §5.3, §9 C2, §10, and the schemas. They go in their own commit, "STANDARD: code lists (Task 41)".
2. **The library:**
   - `Repo.load` expands lists;
   - C1, C2 and C7;
   - `code_lists_sha256` in the data identity (red's `release.py`);
   - views and export;
   - `pdt diff`;
   - corrections that target a list;
   - tests.
3. **The repos:** pdt-chicago-crimes (IUCR as a list, `retired` from `active`; keep the `iucr` table). Then the GSS occupation and industry lists, if blue isn't holding pdt-gss.
4. `pdt check` on all repos.

**Files:** the sections of STANDARD.md and `schema/` above; `lib/pdt/check.py`, `views.py`, `site.py`, `export.py`, `search.py`, `release.py` (with red) and `diff.py` (with red, who holds it for Task 40), with their tests; pdt-chicago-crimes; pdt-gss's build (with blue); this file and Task 41's block on the board.

## Done (orange, 2026-11-19); GSS is a follow-up

**The standard:** `1d4b9be`, the coordinator's review commit "STANDARD: code lists (Task 41)":
- §2 layout, §4.1 `code_list`, §4.2 retired codes, the new §4.5, §5.3 corrections to a list, §9 C2, and §10 (lists shared across datasets are out of scope);
- `schema/code_list.schema.json`;
- `code_list`, `retired`, `waves` and `attributes` in `variable.schema.json`;
- `correction.schema.json`: a target names a variable *or* a list.

`500aabc` adds `code_list` to `provenance.fields`' allowed names, which C1 needed and I had missed. The coordinator caught it too.

**The library:** `f6b1b40`, with 6 tests in `lib/tests/test_code_lists.py`.
- **`Repo.load`:** expands a record's list into `values` (the list's codes, then the record's own) and keeps the records as stored in `repo.stored`, for C1.
- **C1:** validates `code_lists.jsonl` and the stored records.
- **C2:** list ids are unique; codes are unique within a list; every record's list exists; no code is in both a list and a record's own `values`.
- **C7:** checks corrections that target a list.
- **`apply_corrections`:** applies a list correction to every record that uses the list. List codes come first, so `/codes/N` becomes `/values/N`.
- **Data identity:** `code_lists_sha256`, so a data file built from another list is stale.
- **`pdt diff`:** a `code_lists` section compares each pair of lists once: added, dropped, relabeled and newly retired codes. The same content under a new id isn't a change.
- **Site and data-dict export:** the site names a record's shared list, and both mark retired codes.
- **Not done:**
  - The agent shards still carry each record's expanded codes. A shard of lists of their own is left to red.
  - The commit was staged from the index, because `check.py`'s working copy also held purple's uncommitted Task 39 hunks. Purple has since committed them.

**pdt-chicago-crimes:** `9770d0a`. `metadata/code_lists.jsonl` holds `iucr-20261119`:
- 434 codes, 10 retired (`active` false): 0499, 0830, 0840–0843, 3970, 5005, 5008, 9901;
- the primary description, secondary description and index code as `attributes`.

`crimes/iucr` names the list instead of copying it. The `iucr` table stays, for joins and C12. The data and views are rebuilt, and `pdt check` gives 0 failures.

**`pdt check` on all repos:** 0 failures for pdt-anes-cdf, pdt-chicago-crimes, pdt-cps-asec, pdt-fars, pdt-nsfg and pdt-yrbss. pdt-gss fails only C8, while blue's Task 26 build is uncommitted. pdt-brfss, Task 30's repo with no commits yet, fails on its links' missing `source` and its views, which isn't related to code lists.

**Follow-up: the GSS lists.** Blue is holding pdt-gss for Task 26 and will say when it's free. Then: 13 lists of 100 or more valid codes (Census 2010 and 1980 occupations and industries, ISCO-08 and others), each shared by 3–6 variables. Each record names its list and keeps its own missing codes. Labels differ in whitespace between near-duplicates (`kdocc10`), so only identical lists are shared.

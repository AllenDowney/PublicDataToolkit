# Task 41 — Shared code lists

**Status:** `DOING (orange)`, from 2026-11-19.

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

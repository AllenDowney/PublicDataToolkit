# Task 38 — Code lists as tables, and retired codes

**Status:** `DOING (orange)`, from 2026-11-19.

A design, not code: Task 33's deferred proposal 4. [`planning/code_lists_design.md`](../code_lists_design.md) covers:
- the cases: Chicago's IUCR list (its own dataset), FARS's code lists that change by year, NSFG and CPS (inline), GSS occupation and industry codes, and others found;
- the options: values copied inline (now), a reference to a code-list table naming its code and label columns, or a shared codes file per release. For each, what `pdt check`, the views, the data-dict export, `pdt diff` and extract need, and what breaks;
- retired codes: a field on values, availability per code, or histories only;
- a recommendation, with the changes to the standard and schema as a diff for the coordinator to apply.

No changes to STANDARD.md, `schema/` or the library.

**Files:** `planning/code_lists_design.md`, this file, and Task 38's block on the board.

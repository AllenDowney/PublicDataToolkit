# Task 16 — Export data-dict YAML

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE` (views + site thread, 2026-11-19; not pushed)

Export one `data-dict.yaml` per release (per table, for releases with tables), following the mapping in [`planning/data_dict.md`](../../planning/data_dict.md) §2, and validate it with data-dict's own CLI (`uvx data-dict validate-spec`). Record what the export loses, as evidence for the conversation with Hadley (Task 6).

**Files:** new `lib/pdt/export.py` and its tests; `export/data-dict/` in the dataset repos (generated); notes in this task's section.

**Result (views + site thread):**
- [`lib/pdt/export.py`](../../lib/pdt/export.py) writes `export/data-dict/<release>.yaml`, one dictionary per release with the release's tables inside, as STANDARD.md §2 lays out (not one file per table: data-dict holds several tables and their relationships). It also writes `LOSSES.md` and `manifest.json`. `make views` builds it with `agent/` and `docs/`; `pdt views --only export` builds it alone.
- **Validated:** every file passes `data-dict validate-spec` (data-dict-yaml 0.0.3, spec 0.1.0). A test builds a small common-format parquet with `pdt.data.split` and runs `validate-data` against the export; it passes. The test runs when `data-dict` is on PATH or `PDT_DATA_DICT` names it, and is skipped otherwise.
- **Install note:** the PyPI package is `data-dict-yaml`. `uv` isn't installed here. `pip install data-dict-yaml` into a venv works, but the wheel installs the `data-dict` binary without its execute bit; `chmod +x` fixes it.
- **The export describes the common format:** a value column per variable, and an enum `<name>__code` column for its missing codes, with the types in brackets (`.d: don't know [dk]`). Tables have no `source` yet, because the parquet file names wait on Task 18.

**What data-dict can't hold (evidence for Task 6, Hadley):** counts per release are in each repo's `export/data-dict/LOSSES.md`. The main findings:
1. **Numeric codes can't be labeled.** data-dict's `enum` is a string column, and our value columns hold numbers. An enum with `{"1": yes}` passes `validate-spec` but fails `validate-meta` (M01: "the data is `number`"). Labels go in `details` as text: 47 of 50 GSS variables, 34 of 37 ANES, 42 of 52 NSFG, 24 of 40 FARS. This is probably the most important question for Hadley, since most survey data is labeled integers.
2. **No ordered enum.** An ordinal scale is `number(ordinal)` with the range of codes, and its labels are in text.
3. **Missing codes and their types:** only as text in the `__code` enum's labels (182 GSS codes, 89 ANES).
4. **Availability by wave and form:** one line of text (2,871 entries for the GSS release).
5. **Wording by wave:** flattened into `details` (7 ANES variables).
6. **Corrections:** only the corrected text survives (4 GSS, 11 ANES).
7. **Provenance per field:** dropped (about 300 field origins per repo).
8. **Groups, links between releases, derived properties, code histories:** dropped (25 GSS groups, 50 GSS links, 42 FARS histories).
9. **Conditional joins:** FARS person → vehicle "when PER_TYP is 1, 2 or 9" can only be a description.
10. **Release versions:** ids like `7224r3a` or `2022-2023` are neither semver nor a date, so `version` is left out.
11. **Keys:** a join's "one" side must be `primary_key` or `unique`, so key columns are marked; composite keys work by marking each column.

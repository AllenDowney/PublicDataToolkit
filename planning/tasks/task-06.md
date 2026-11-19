# Task 6 — Talk to Hadley Wickham about data-dict

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `TODO`

Ask him about:
- the gaps we found: missing-value sentinels, history across releases, provenance, non-parquet sources, numeric enum codes;
- whether exporting data-dict YAML from our records is a reasonable use of the format;
- whether any of those gaps belong upstream in data-dict.

Background: plan §4.3.

**Progress (2026-11-19):** Wrote [`planning/data_dict.md`](../../planning/data_dict.md) to share with Hadley. It explains the export (one `data-dict.yaml` per release, generated from our records), maps our fields onto data-dict, shows the `abany` dilemma (numeric codes or labels, not both), and asks nine questions. Checked against the data-dict spec (`$version: 0.1.0`, tool v0.0.3). Two corrections to what we had noted:
- Value labels exist only on `enum` columns, and enum codes must be strings. `number` columns get `range` and `examples`.
- The spec has `number(ordinal)`, `number(quantity)` and `number(id)` measures, `units`, a `glossary`, and `relationships`. It doesn't say whether the validator rejects unknown keys, so we ask (question 3).

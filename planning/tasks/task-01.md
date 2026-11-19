# Task 1 — Write the plan

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DOING` — first draft 2026-11-19

Write `planning/plan.md`, based on [`planning/context.md`](../../planning/context.md) and the earlier design [`planning/survey_metadata_packages_plan.md`](../../planning/survey_metadata_packages_plan.md).

The plan should settle:

1. **What this repo contains.** Instructions, agent skills, templates and checklists, and how an agent uses them to create a dataset repository or improve an existing one.
2. **The target repository.** What a finished dataset repository looks like, modeled on gssrdoc: layout, data as a release or a download script, metadata files, tests, and a "definition of done" an agent can check.
3. **The three forms of access**, with use cases for each:
   - human-readable (a browsable site, per-variable pages);
   - programmable (a Python API, and maybe R: lookup, missing values, availability, release comparison);
   - LLM access (shards, an index, search results that say whether they are complete; MCP later, if it earns its keep).
4. **The metadata model.** What carries over from §5 of the earlier plan, and what changes now that each dataset has its own repo instead of an adapter in one package.
5. **Relationship to data-dict.** Whether to use data-dict YAML as the per-release layer and add what it lacks (missing-value codes, history across releases, provenance), or keep a format of our own. Talk to Hadley.
6. **Which datasets come first.** GSS (reference), ANES, Monitoring the Future (the adversarial case), and a non-survey case, perhaps a Socrata portal.
7. **Terms of use** for each dataset: ship or build-only.
8. **The two-day snake_case spike:** a small, achievable scope, adapted from §13 of the earlier plan.
9. **Open decisions for Allen.** Carry over §14 of the earlier plan and update it.

**Progress (2026-11-19):** First draft written: [`planning/plan.md`](../../planning/plan.md). It covers all nine points above. Main proposals:
- one repo per dataset, with a shared library and a `pdt check` definition of done;
- our own JSONL records as the canonical form, with data-dict YAML exported;
- dataset order: GSS, then ANES, then MTF, plus an open-portal dataset;
- a reduced snake_case spike (§9).

**Decided (2026-11-19):**
- one repo per dataset, with a shared library;
- our JSONL records as the source of truth, with data-dict YAML exported;
- the spike covers GSS, ANES and MTF.

**Still open:** plan §10, items 3–5, 7 and 8.

# PublicDataToolkit Project Board

Numbered tasks for tracking work. Each task has a permanent number; add new tasks at the end. Update status as work progresses.

**Status labels:** `TODO` | `DOING` | `DONE`

### Current focus (2026-11-19)

Started at the snake_case hackathon, November 19–20, 2026. Background is in [`planning/context.md`](planning/context.md).

- **Task 1:** Write the plan — `DOING`. Draft in [`planning/plan.md`](planning/plan.md). Decided: one repo per dataset, JSONL as the source of truth with data-dict exported, and a GSS + ANES + MTF spike. Remaining decisions are in plan §10.
- **Task 2:** Recover the earlier planning session — `DONE`. Found as CultureWar Task 186 and copied to [`planning/`](planning/).
- **Task 3:** Inventory the GSS and ANES work in CultureWar — `DONE`. [`planning/inventory.md`](planning/inventory.md).
- **Task 4:** Publish the repo on GitHub — `TODO`, waiting for Allen's OK.
- **Task 5:** snake_case spike: STANDARD.md, schema, and GSS, ANES and MTF slices — `DOING`. Step 1 drafted: [`STANDARD.md`](STANDARD.md) and [`schema/`](schema/). Next: the GSS slice.
- **Task 6:** Talk to Hadley Wickham about data-dict — `DOING`. Note to share: [`planning/data_dict.md`](planning/data_dict.md).
- **Task 7:** Withdrawn.
- **Task 9:** Remove private information so the repo can be public — `DONE`.
- **Task 10:** Respond to review 1 of the proposal — `DONE`. [`planning/review_1.md`](planning/review_1.md).
- **Task 8:** Versions, layout and names for dataset repos — `DONE`. Decided; see [`planning/versions_layout_names.md`](planning/versions_layout_names.md). Applied to STANDARD.md.

---

## Task 1 — Write the plan

**Status:** `DOING` — first draft 2026-11-19

Write `planning/plan.md`, based on [`planning/context.md`](planning/context.md) and the earlier design [`planning/survey_metadata_packages_plan.md`](planning/survey_metadata_packages_plan.md).

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

**Progress (2026-11-19):** First draft written: [`planning/plan.md`](planning/plan.md). It covers all nine points above. Main proposals:
- one repo per dataset, with a shared library and a `pdt check` definition of done;
- our own JSONL records as the canonical form, with data-dict YAML exported;
- dataset order: GSS, then ANES, then MTF, plus an open-portal dataset;
- a reduced snake_case spike (§9).

**Decided (2026-11-19):**
- one repo per dataset, with a shared library;
- our JSONL records as the source of truth, with data-dict YAML exported;
- the spike covers GSS, ANES and MTF.

**Still open:** plan §10, items 3–5, 7 and 8.

## Task 2 — Recover the earlier planning session

**Status:** `DONE` (2026-11-19)

The earlier planning session's output was a design written for the CultureWar project (its Task 186), revised 2026-11-17. It is copied, with small edits, to [`planning/survey_metadata_packages_plan.md`](planning/survey_metadata_packages_plan.md).

It designs one Python package (`surveydoc`) with a core and one adapter per dataset. It covers design principles, a data model, operations, agent views and recall measurement, non-goals, a gssrdoc strategy, ANES, a ranking of other sources, a roadmap, a hackathon spike and decisions for Allen. How it differs from today's idea is in [`planning/context.md`](planning/context.md).


## Task 3 — Inventory the GSS and ANES work in CultureWar

**Status:** `DONE` (2026-11-19)

Read, and don't modify, the GSS and ANES codebook and extract code in the CultureWar, GssExtract and ExtractANES repos. Starting points are listed in §3 of the earlier plan and in [`planning/context.md`](planning/context.md). For each piece, record:

- what it does and which inputs it reads;
- whether it is generic (it belongs in the instructions or skills) or specific to CultureWar's analysis;
- what an agent would need in order to do the same thing for a new dataset.

Write the result to `planning/inventory.md`. Also check MarriageNSFG as a third worked example (NSFG: a download script, a data release, codebooks as text).

**Result:** [`planning/inventory.md`](planning/inventory.md). Main findings:
- **The GSS catalog can't be rebuilt.** `convert_gssrdoc_to_json.R` reads a local clone of gssrdoc at a hard-coded path, and its outputs are gitignored.
- **Missing codes collapse.** The GSS and ANES detectors turn DK, refused and IAP into one NaN. The GSS regex misses 7 real missing codes whose labels start with "no". gssrdoc's `NA(x)` tokens are almost the same for every variable.
- **The ANES codebook build is stranded.** The script and its HTML input are only in ExtractANES, with no record of where the HTML came from.
- **The GSS and ANES record schemas disagree** on name case and field names, and both store structured data as strings.
- **NSFG has the best data-release practice** (release with SHA-256 sums, terms flag) **and the weakest metadata.**
- **Not yet captured:** GSS release notes have never been parsed, and the errata exist only as markdown.

## Task 4 — Publish the repo on GitHub

**Status:** `TODO` — needs Allen's OK

Create the public repository `AllenDowney/PublicDataToolkit` (the name is free as of 2026-11-19) and push. The repo was cleaned for publication in Task 9.

## Task 5 — snake_case spike

**Status:** `DOING` — step 1 drafted 2026-11-19. Scope in [`planning/plan.md`](planning/plan.md) §9, decided 2026-11-19: GSS, ANES and MTF.

1. Write `STANDARD.md` and `schema/`.
2. GSS slice (30–50 variables) from CultureWar's extracted JSON.
3. ANES CDF slice (30–50 variables).
4. MTF slice: one 12th-grade year, two or three forms, and items whose V-number changes. Needs an ICPSR login and a terms check first.
5. Generate the three forms for all three slices. Run one structural and one topic query against hand-built answer keys.
6. Prepare the 2-minute demo.
7. Optional, if a teammate joins: an open-portal dataset in parallel.

Record what ended up in dataset-specific extensions and where the agent got stuck. Those notes are the main result.

**Progress (2026-11-19), step 1:** [`STANDARD.md`](STANDARD.md) v0.1 and nine JSON Schemas in [`schema/`](schema/), with real GSS and ANES example records in [`schema/examples/`](schema/examples/). [`schema/check_examples.py`](schema/check_examples.py) validates them and confirms five bad records are rejected; all pass.

Changes from plan §3–4, made while writing the standard:
- **New `dataset.yaml`** next to `sources.yaml`, for the dataset's terms, releases and what "wave" and "form" mean in it.
- **Terms and acquisition are separate fields.** The plan listed `ship`, `build-only` and `manual` as one set of values. Now each source has `redistribution` (`ship`, `build-only` or `unknown`) and `acquisition` (`automated` or `manual`). `unknown` blocks shipping.
- **Corrections aren't applied to source records.** `variables.jsonl` keeps the publisher's text, and the library applies `corrections.jsonl` when it builds the views.
- **`questions` is a list.** ANES VCF0803 has three wordings, by year and mode.
- **Codes can be strings,** for Stata extended missing values such as `.d`.
- **Each missing code needs its own origin**: publisher, data file, rule or hand.
- **Nine missing types:** `dk`, `refused`, `no_answer`, `inap`, `skipped`, `not_asked`, `not_available`, `uncodeable`, `other`. One code can have several (GSS `.m` "dk, na, iap").
- **Link relations are a list,** so one pair can be both renamed and reworded. Links can't come from a model.

Findings:
- **The ANES codebook lists VCF0803 code 9, "DK; haven't thought much," as valid.** The standard keeps the publisher's classification, so it's stored as valid. A label regex would have called it missing.
- **gssrdoc's MIT license covers its code, not NORC's documentation,** so the gssrdoc source takes the GSS terms. The GSS terms are still unreviewed.
- **No Python environment for the toolkit yet.** The base Python lacks `jsonschema`; the check ran with a temporary install. The shared library (`lib/`) will need a `pyproject.toml`.
- **Still open:** how to choose release ids (`7224r3a` from the GSS file name, `20260205` from the ANES release date). Listed in STANDARD.md §10 with the other provisional parts.

## Task 6 — Talk to Hadley Wickham about data-dict

**Status:** `TODO`

Ask him about:
- the gaps we found: missing-value sentinels, history across releases, provenance, non-parquet sources, numeric enum codes;
- whether exporting data-dict YAML from our records is a reasonable use of the format;
- whether any of those gaps belong upstream in data-dict.

Background: plan §4.3.

**Progress (2026-11-19):** Wrote [`planning/data_dict.md`](planning/data_dict.md) to share with Hadley. It explains the export (one `data-dict.yaml` per release, generated from our records), maps our fields onto data-dict, shows the `abany` dilemma (numeric codes or labels, not both), and asks nine questions. Checked against the data-dict spec (`$version: 0.1.0`, tool v0.0.3). Two corrections to what we had noted:
- Value labels exist only on `enum` columns, and enum codes must be strings. `number` columns get `range` and `examples`.
- The spec has `number(ordinal)`, `number(quantity)` and `number(id)` measures, `units`, a `glossary`, and `relationships`. It doesn't say whether the validator rejects unknown keys, so we ask (question 3).

## Task 7 — Withdrawn

**Status:** withdrawn (2026-11-19). Out of scope for this repo.

## Task 8 — Versions, layout and names for dataset repos

**Status:** `DONE` — decided 2026-11-19

Allen's questions: a version system so a repo built with version 1 can be updated to version 2; whether dataset repos should follow Cookiecutter Data Science (CCDS) or adopt ideas from it; and a name scheme for dataset repos.

**Proposal:** [`planning/versions_layout_names.md`](planning/versions_layout_names.md).
- **Versions:** one semantic version for the standard, the template and the shared library. Copier instead of cookiecutter, because CCDS has no way to update a generated project and Copier does (`copier update`, migrations). Major versions come with an upgrade guide for the dataset-specific code, and old schemas are kept so older repos still validate.
- **CCDS:** don't follow its layout; it's built for analysis projects (models, reports). Use its names where the meaning is the same: `data/raw`, `data/interim`, `references/`, `docs/` for the site, Makefile targets, `.env`.
- **Names:** `pdt-<dataset-id>`, e.g. `pdt-gss`, `pdt-anes-cdf`, `pdt-mtf-12`. No language in the name: the repos are language-neutral and the shared library provides language access. A registry of dataset ids in this repo, and a `publicdatatoolkit` GitHub topic.

**Decided (Allen, 2026-11-19):** all four proposals as written: one version plus Copier; CCDS names only; `pdt-<dataset-id>`; a registry plus the GitHub topic. Applied to [`STANDARD.md`](STANDARD.md) §1–2 (name, layout, §2.4 versions and updates, `docs/` instead of `site/`).

**Not done yet:** the Copier template (`templates/`), the registry file (create it when the first dataset repo is claimed), and versioned schema paths (at 1.0).

## Task 9 — Remove private information so the repo can be public

**Status:** `DONE` (2026-11-19)

Before the first public commit, removed from all files: the names of collaborators and event participants (authors of public tools are still named), paths on the author's machine, notes about other repositories' contents, and remarks about an upstream maintainer. The earlier local history was replaced by a single fresh commit.

## Task 10 — Respond to review 1 of the proposal

**Status:** `DONE` (2026-11-19)

The first review of [`PROPOSAL.md`](PROPOSAL.md) recommends going ahead with a focused prototype. Its suggestions are triaged against STANDARD.md in [`planning/review_1.md`](planning/review_1.md).

**Done:**
- `unresolved` codes in the schema and the standard;
- an operational definition of `complete`, `complete_by_rule` and `approximate` (STANDARD.md §7);
- the proposal revised, including a new §8, "How we will know this works."

**Decided:** a small R reader once the spike settles the format; spike queries only for now, with a full benchmark decided after snake_case.

**Deferred until after the spike:**
- a review status on every record;
- a human spot check with an error rate;
- a defined release-change report;
- a build record;
- a `collection` field;
- schema design rules;
- release monitoring.

DDI comparison isn't scheduled.

# Task 68 — `pdt export daaf`: a dataset repo as a DAAF data-source skill

**Status:** `DOING (purple)`. The design was approved on 2026-11-20 with answers to its open questions (below). The prototype is built: `pdt export daaf`, tested on pdt-nhis and pdt-gss, and DAAF's lint passes. A load test inside DAAF waits for Allen.

**Goal:** `pdt export daaf` turns a dataset repo's records and agent views into a skill in [DAAF](https://github.com/DAAF-Contribution-Community/daaf)'s data-source template (`agent_reference/DATA_SOURCE_SKILL_TEMPLATE.md`), carrying our terms. It's an exporter like the data-dict one: generated, never edited, checked by C8.

**What I read** (2026-11-20, read-only through `gh`): DAAF's data-source template (930 lines), its extension guide (`user_reference/04_extending_daaf.md`), the file tree of its countypres skill, and the list of its skills and lint scripts. The review in `planning/daaf.md` covers the rest.

## What DAAF expects

- **One directory per source:** `.claude/skills/<domain>-data-source-<acronym>/`, holding `SKILL.md`, `references/*.md` and optional `scripts/`.
- **SKILL.md** has 12 mandatory sections in a fixed order:
  1. frontmatter;
  2. title;
  3. summary;
  4. a "Value Encodings" warning blockquote;
  5. "What is …";
  6. Reference File Structure;
  7. Decision Trees;
  8. Quick Reference;
  9. Data Access;
  10. Common Pitfalls;
  11. Related Data Sources;
  12. Topic Index.
- **Optional sections** go between 10 and 11: a source-specific critical section, `## Survey Design` (weights, strata, PSU, replicate weights with the Fay coefficient, the variance method), and `## Multi-File Structure`. SKILL.md should run 250–400 lines (500 at most).
- **Frontmatter:** `name` must match the directory. `description` is at most 1,024 characters, with no angle brackets, and says what the source is, its years, when to use it and what not to use it for. `metadata`: `audience: any-agent`, `domain: data-source`, `skill-authored`, `skill-last-updated`, and an optional `data-provenance` (`real`, or `synthetic-*`).
- **Reference files:** `columns.md`, `coded-values.md`, `data-quality.md`, `variable-definitions.md`, `analytical-context.md`, plus topic files. Together they should be 4–6 times SKILL.md's length.
- **Linter:** `tests/lint/check-daaf-conventions.sh` checks the conventions.

## The mapping

| DAAF section or file | From our records | Notes |
|---|---|---|
| Frontmatter `name` | `<domain>-data-source-<dataset id>` | `domain` is an export option: `health` (NHIS, BRFSS, NSDUH, NHANES, MEPS), `social` (GSS, ANES), `education` (PISA). The default comes from `dataset.yaml` `kind`, else `survey`. |
| `description` | `title`, `description`, the release and wave span, the 3–5 largest groups or subjects as triggers, and "metadata from the publisher's documentation; not analysis advice" | Built to ≤ 1,024 characters by dropping triggers first. Angle brackets removed. |
| `metadata` | DAAF's keys, plus ours under a `pdt-` prefix: `pdt-version`, `pdt-inputs-sha256`, `pdt-generator-sha256`, `pdt-standard-version`, and `pdt-terms` (the four decisions, the URL, `reviewed_on`) | `skill-authored` and `skill-last-updated` are the export date, passed in (`--date`, default today), so the output is reproducible. `data-provenance: real`. |
| **Terms of Use** (an optional critical section, placed first) | `terms.notice` verbatim, the summary, the decisions, `llm_processing`, the URL | DAAF's template has no terms field, so this section carries them. The notice also heads every reference file. |
| Summary and "What is …" | `description`, publisher, `kind`, releases (`label`, status), `dimensions` | |
| Value Encodings warning | 3 example variables with typed missing codes, picked by a rule: different missing types, and the most-used codes | Says the codes are the publisher's, as stored, and that the common-format files split them into `<name>__code`. |
| Reference File Structure | the files below | |
| Decision Trees | three fixed trees, filled from the records: "Which release or wave?" (`dimensions`, availability); "Is this code missing, and why?" (missing types); "Is a search result complete?" (`complete`, `complete_by_rule`, `approximate`) | No tree recommends an analysis. |
| Quick Reference | keys and references (tables), `design`, the missing types used, the largest groups | |
| Survey Design (optional) | `design`: weights (by wave), strata, PSU, replicates (`method`, `fay_factor`, table and key) | Points to DAAF's `svy` skill for syntax. |
| Multi-File Structure (optional) | `tables`: key, references with `when` | |
| Data Access | how to get the data: our data release if `terms.data` is `ship`, else `pdt download`; the common-format files; a `pdt.extract` example (Python) and an `arrow::read_parquet` one (R) | DAAF fetches from a mirror (`mirrors.yaml`). Our GitHub data release could be one; that's a later step. |
| Common Pitfalls | generated from facts, never advice. Each pitfall names the facts behind it | A name reused for different items across releases (C2's warning); links that change meaning (`codes_changed`, `range_changed`, `rescaled`); plausible-value groups; replicate weights; unresolved codes; corrections and their confidence; codes the publisher's documents disagree on (noted in origins); `data_rows` slices. |
| Related Data Sources | the catalog's other datasets that share a group kind or subject words | Optional; omitted without a catalog. |
| Topic Index | groups and subjects, each pointing to a reference file or agent shard | |
| `references/columns.md` | our agent table shards (`.txt`), one line per variable or lineage | Split into parts as the shards are. |
| `references/coded-values.md` | every code with a missing type or `unresolved`, grouped by its set of codes | |
| `references/data-quality.md` | corrections (with evidence), unresolved codes, the build report's documentation differences, `revisions` | |
| `references/variable-definitions.md` | groups (batteries with stems, sections, subjects), lineages across releases with the changes between runs and their evidence | |
| `references/analytical-context.md` | design, universe statements, releases, `reference_period`, terms | Descriptive only. DAAF asks for "valid/invalid analyses", and the file says this repository doesn't make analysis decisions, and why. |
| `references/agent/` | a copy of `agent/` (index, SKILL, shards) | So a DAAF agent can use our completeness labels and, with the library installed, `pdt search`. |

## Rules for the exporter

1. **Terms first.** It refuses unless `terms.metadata` and `terms.documentation` are `ship` (the skill copies question text) and `terms.llm_processing` is `allowed` (DAAF is an LLM framework). It says which term blocked it. When `terms.data` isn't `ship`, Data Access gives only the publisher's route.
2. **No analysis decisions.** No "exclude", "use", "recode" or "should" about the data: generated text states what the records say. A test greps the output for an agreed list of such words.
3. **Provenance.** The generated files start with the header the other views carry (pdt version, inputs hash, generator hash), as an HTML comment after the frontmatter. `export/daaf/manifest.json` lists the files, and C8 checks it like `export/data-dict/`.
4. **Size.** SKILL.md stays under 500 lines: Quick Reference and Topic Index are cut to the largest groups, with the rest in reference files. The description stays under 1,024 characters.
5. **Where it goes.** `export/daaf/<skill name>/` in the dataset repo, generated on request (`pdt export daaf`, `make export-daaf`), not by `make views`; the design first said `make views`, and the coordinator's answer 4 changed it. Copying it into a DAAF checkout's `.claude/skills/` is the user's step.

## Prototype and test plan (as designed)

1. Write `lib/pdt/daaf.py` with tests: frontmatter limits, the 12 sections in order, the terms refusal, the no-advice word list, and C8.
2. Export two repos:
   - **pdt-nhis:** many releases, design, links across the 2019 redesign;
   - **the GSS slice:** subjects, batteries, corrections.
3. Run DAAF's `tests/lint/check-daaf-conventions.sh` on the output in a scratch clone of DAAF, read-only toward upstream.
4. Load the skill in DAAF (its Docker setup), and ask DAAF's agent one eval-style question per dataset. That needs Allen or the coordinator to say whether to run DAAF's container here.

## Open questions, answered by the coordinator (2026-11-20)

1. **Names:** follow DAAF's convention exactly. Its data-source skills are `education-data-source-ccd`, ..., `election-data-source-countypres`: a subject prefix, then `-data-source-`, then the source's acronym. So `--domain` is required (`health`, `social`, ...). A default could come from a new optional `dataset.yaml` field; that's a schema change, proposed to the coordinator, not made.
2. **Copy agent/:** yes, since DAAF skills stand alone, with the repository URL and release as the canonical source. When agent/ is large (pdt-gss: 60 MB), copy the index and the shards that fit, and point to the rest.
3. **License:** in both places. DAAF's frontmatter allows only `name`, `description`, `when_to_use` and `metadata` (string values), so it's a `pdt-license` metadata key, plus a line in the Terms of Use section.
4. **On request only:** `pdt export daaf` or `make export-daaf`, not part of `make views`. C8 checks export/daaf/ only where it exists.
5. **No Docker for now:** run DAAF's lint in a scratch clone. The coordinator will ask Allen about a load test once the lint passes.

## The prototype

**Files:**
- [`lib/pdt/daaf.py`](../../lib/pdt/daaf.py): the exporter.
- [`lib/tests/test_daaf.py`](../../lib/tests/test_daaf.py): 15 tests.
- `lib/pdt/cli.py`: `pdt export daaf`.
- `lib/pdt/check.py`: C8 for export/daaf/.
- `templates/template/Makefile`: `make export-daaf DAAF_DOMAIN=...`.

**What it writes:** `export/daaf/manifest.json` and `export/daaf/<domain>-data-source-<id>/`:

| File | Content |
|---|---|
| `SKILL.md` | DAAF's 12 sections in order. Terms of Use sits after the Value Encoding blockquote, where countypres puts its Prerequisites. Survey Design and Multi-File Structure come between Common Pitfalls and Related Data Sources, where the template puts optional sections. |
| `references/columns.md` | One line per variable across releases, from `pdt.chains`. |
| `references/coded-values.md` | Each distinct set of non-valid codes, with the records that use it. |
| `references/data-quality.md` | Corrections, unresolved codes and `data_revised` links. |
| `references/variable-definitions.md` | Links that change meaning, with their evidence, and the groups. |
| `references/analytical-context.md` | Releases, waves, `data_rows`, design, tables and terms. |
| `references/agent/` | agent/ regenerated from the records and copied: all of it under 2 MB, else the index, the guide and the .txt shards that fit. |

A file over 20,000 tokens splits into parts (`columns-01.md`, ...), with each part's table header repeated.

**Rules as built:**
- **Terms:** the export raises `TermsError` and writes nothing unless metadata and documentation are `ship` and llm_processing is `allowed`. The terms notice heads every generated file.
- **Advice words:** `advice_lines` scans generated text for them (should, recommend, exclude, drop, recode, avoid, prefer, ...). It skips quoted record text: blockquotes, code, quoted strings, bold names, and table rows outside Common Pitfalls. DAAF's template wants a "Solution" column in Common Pitfalls; ours says where the facts are.
- **`skill-authored`:** kept from the previous manifest, so it stays fixed across re-exports, as DAAF asks.
- **C8:** the manifest records its own generator hash (the views' hash plus `daaf.py`), so this module doesn't change the hash for every repo's views.
- **`agent-guide.md`:** the copy of agent/SKILL.md is renamed, so a skill directory holds one SKILL.md.

**Results (2026-11-20):**

| | pdt-nhis | pdt-gss (to the scratchpad) |
|---|---|---|
| Skill | `health-data-source-nhis` | `social-data-source-gss` |
| Files | 39; agent/ copied whole | 289; agent/ in part: 273 of 1,908 files (the across-release lines and the group shards, 2.6 MB) |
| SKILL.md | 264 lines | 257 lines |
| Description | 654 characters | 552 characters |
| Peak memory, time | 71 MB, 2 s | 0.5 GB, 79 s |
| Advice lines | 0 | 0 |

- **DAAF's lint:** `tests/lint/check-daaf-conventions.sh` (DAAF commit 99ac264) passes with both skills in a scratch clone's `.claude/skills/`: 0 failures. The 18 warnings are all about DAAF's own host scripts. For skills, the lint checks only the provenance keys and stale key spellings, so the tests also check DAAF's frontmatter rules: the name regex, the description length and no angle brackets, the allowed fields, and string metadata values.
- **pdt-nhis:** has `export/daaf/` and `make export-daaf` (`DAAF_DOMAIN ?= health`), and `pdt check` gives 0 failures.
- **pdt-gss:** exported only to the scratchpad, because orange has uncommitted work there.
- **pytest:** 290 passed, 1 skipped.

**Findings:**
- **No LICENSE file:** pdt-nhis and pdt-gss have none. The template's `LICENSE.jinja` (CC BY 4.0 for metadata/ and export/) came after them. The export's license line follows the template.
- **Unjoined names:** in NHIS, names like `HHX` appear before and after 2019 with no link joining them. The pitfall says the records don't say whether they're the same item, rather than calling them different items.
- **`--repo-url`:** without a git remote (none of the repos has one yet), the canonical source reads "the repository pdt-<id>". After publishing, `--repo-url` or the remote fills it in.

**Next:**
- A load test inside DAAF (Allen).
- A `dataset.yaml` field for the domain, if the coordinator wants one.
- Related Data Sources from the catalog: it now says the records relate no other dataset.

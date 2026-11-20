# Task 68 — Design: `pdt export daaf`, a dataset repo as a DAAF data-source skill

**Status:** `DOING (purple)` — design only, assigned by the coordinator on 2026-11-20 ([`planning/daaf.md`](../daaf.md), next step 1). No code until the coordinator has read it.

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
5. **Where it goes.** `export/daaf/<skill name>/` in the dataset repo, generated by `make views` (a new `pdt views --only daaf`, also run by default). Copying it into a DAAF checkout's `.claude/skills/` is the user's step.

## Prototype and test (next step, after this design is read)

1. Write `lib/pdt/daaf.py` with tests: frontmatter limits, the 12 sections in order, the terms refusal, the no-advice word list, and C8.
2. Export two repos:
   - **pdt-nhis:** many releases, design, links across the 2019 redesign;
   - **the GSS slice:** subjects, batteries, corrections.
3. Run DAAF's `tests/lint/check-daaf-conventions.sh` on the output in a scratch clone of DAAF, read-only toward upstream.
4. Load the skill in DAAF (its Docker setup), and ask DAAF's agent one eval-style question per dataset. That needs Allen or the coordinator to say whether to run DAAF's container here.

## Open questions for the coordinator

1. **Domain names:** `health-data-source-nhis`, `social-data-source-gss`, `education-data-source-pisa`? DAAF groups by subject area.
2. **Is copying `agent/` into the skill acceptable?** It duplicates generated files, so a DAAF agent sees them without our repo. The alternative is a pointer to the repo, which a DAAF agent in Docker may not have.
3. **License of the exported skill:** our metadata and views are CC BY 4.0 (the repos' LICENSE). DAAF is LGPL-3.0-or-later but says skills may carry their own license. A `license` line in the frontmatter, or in the Terms section?
4. **Run `make views` by default,** or only `pdt export daaf` on request? On request keeps the repos smaller until there's a user.

**Files (for the prototype, later):** new `lib/pdt/daaf.py` and its tests; `lib/pdt/cli.py` (the `export` subcommand or `views --only daaf`); `lib/pdt/check.py` (C8 for `export/daaf/`, staged on its own).

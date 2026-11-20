# DAAF and PublicDataToolkit

A review of [DAAF](https://github.com/DAAF-Contribution-Community/daaf) (Data Analyst Augmentation Framework), for connections with this project. Read on 2026-11-20 through `gh` (README, file tree, skills, agents, templates, releases, issues) by a Claude subagent for the coordinator. Nothing was forked, starred or commented on. Points marked *inferred* are judgment, not something read.

## What DAAF is

- **A Claude Code framework for researchers' data analysis:** plan, fetch, clean, analyze, report, reproduce. Every step is a script run through `scripts/run_with_capture.sh`, with logs and a `STATE.md`.
- **Parts:** one orchestrator skill with 10 modes (`.claude/skills/daaf-orchestrator/`), 20 agents, 20 safety and audit hooks, about 60 skills, protocol docs (`agent_reference/`), a Docker install, and a benchmark (`benchmarks/`, "DAAFBench").
- **Data:** about 14 education sources from the Urban Institute Education Data Portal (CCD, CRDC, IPEDS, Scorecard, ...), through a Parquet mirror on Hugging Face pinned by commit (`education-data-query/references/mirrors.yaml`), plus MIT county presidential returns (CC0). Its "MEPS" is Model Estimates of Poverty in Schools, not AHRQ's survey. No survey microdata: GSS, ANES, NSFG, BRFSS and NHIS appear only as examples in its method skills (`svy`, `survey-r`).
- **Maturity:** created 2026-02; v3.1.0 on 2026-11-03 (8 releases); about 870 commits, 240 stars, 35 forks; essentially one maintainer (Brian Heseung Kim). License LGPL-3.0-or-later; skills may carry their own license.

## Where it overlaps

DAAF's **Data Onboarding** mode (`daaf-orchestrator/references/data-onboarding-mode.md`) addresses our problem: turning a dataset and its codebook into documentation an agent can use. The approaches differ:

| | DAAF | PublicDataToolkit |
|---|---|---|
| Output | One SKILL.md per data source, from a 12-section template (`agent_reference/DATA_SOURCE_SKILL_TEMPLATE.md`) | Records under a JSON Schema, with three generated views |
| Evidence | Profiles the data, then reconciles it with the documentation | Codebook facts copied verbatim, each with its origin |
| Missing codes | Tables in prose | Typed codes, each with an origin |
| Provenance | Per skill: dates, a real/synthetic flag, bundled profiling scripts | Per fact; corrections are separate records |
| Completeness | Not addressed | Every result is `complete`, `complete_by_rule` or `approximate` |
| Scope | Description and analysis | Description only |

## Connections

**From us to DAAF (the most promising, *inferred*).** A dataset repo's agent views could be packaged as a DAAF data-source skill: a generated SKILL.md in DAAF's template (including its "Survey Design" section, from our `design`), pointing to our index and shards. DAAF's extension guide (`user_reference/04_extending_daaf.md`) says a new data source needs only a new skill. That would give DAAF its first survey microdata, with typed missing codes and completeness labels. On our side it's a small exporter, like the data-dict one. It should carry each dataset's terms, including `llm_processing`, which DAAF's template has no field for.

**From DAAF to us, ideas worth borrowing:**
- **Reconciling documentation with the data.** DAAF's countypres skill (`coded-values.md`) lists codebook claims the data contradicts and undocumented empty values. That's our corrections and `unresolved`, and suggests a check: every documented frequency against the data (blue did this by hand for NSDUH, NHANES and MEPS).
- **Profiling scripts kept as provenance** (the template's "Provenance Scripts" section).
- **Synthetic data for restricted datasets,** so an agent can test code without the real file (relevant to NCVS and MTF).
- **Declaring checks that don't apply,** with a reason, rather than skipping them silently (`.claude/agents/data-ingest.md`). Our `pdt check` could report "not run, because ..." for each check.
- **DAAFBench** as a model for our recall evals.

## Differences and risks

- **Terms.** DAAF's template has no per-dataset terms field, and it redistributes the Portal data as a mirror (Urban's terms weren't checked). Anything we export to it must carry our terms decisions.
- **Provenance.** DAAF's skills are model-written prose with human checkpoints, without field-level source/derived separation. They can't be a source for our records.
- **Analysis advice.** Its skills say things like "exclude from analysis" for missing codes. We don't make analysis decisions, so an exporter shouldn't add them.
- **Coupling and bus factor.** DAAF depends on Claude Code and Docker, and has one maintainer.

## Possible next steps

1. A prototype exporter, `pdt export daaf`, for one dataset (the GSS slice or NHIS), and a test of it inside DAAF.
2. If it works, a note to DAAF's maintainer offering survey data sources (Allen's decision; no correspondence drafted here).
3. Adopt the "not run, because" reporting in `pdt check`, and a documented-frequency check.

# Context from snake_case, 2026-11-19

This file collects what was discussed on day 1 of the snake_case hackathon (November 19–20, 2026), before the repo was created.

## The project as proposed at snake_case

"Stable APIs for messy public datasets" (Allen Downey):

> Define an adapter API that sits between published datasets and analysis code, providing stable variable access, cleaned metadata, provenance, coding/value labels, availability information, and warnings about changes across releases. Use GSS as one reference implementation and build a second adapter for a substantially different public dataset (Monitoring the Future) to test whether the abstraction holds up. Experiment with using LLMs to turn codebooks and release notes into candidate adapter metadata that is reviewed and then used deterministically.

## The structure proposed on 2026-11-19

- This repo is **instructions and skills, not a package.** Someone clones it and tells an agent to use the instructions to create a new repository for a dataset, or to improve an existing one, until it is in the condition we're aiming for.
- **gssrdoc is the model** for the target repository.
- **Data:** included as a release on the target repo when the terms allow it; otherwise, scripts or instructions for downloading it.
- **Metadata documents** are created from the publisher's documentation.
- The core is to **generalize what was done with the GSS and ANES in CultureWar** into skills and instructions for other datasets.
- The metadata is available in **three forms**, each with its own use cases:
  1. human-readable;
  2. programmable access;
  3. LLM access.
- **Name:** not all the data will be surveys, so "SurveyDoctor" was too narrow, and a commercial product already uses that name. "PublicDataToolkit" is free on PyPI and as a GitHub org name, and only one empty GitHub repo uses it.

**How this differs from the earlier plan.** [`survey_metadata_packages_plan.md`](survey_metadata_packages_plan.md) (2026-11-17) designs one Python package, `surveydoc`, with a core module and one adapter per dataset. Today's idea is a toolkit of instructions that produces a **separate repository per dataset**, each built to a common standard. Most of the earlier plan still carries over: the principles, the data model, the agent views, recall measurement, the non-goals and the spike. Reconciling the two is part of Task 1.

## Related work

| Tool | Relevance |
|---|---|
| **data-dict** (Hadley Wickham, https://data-dict.tidyverse.org/, v0.0.3) | A YAML data-dictionary spec plus a validator CLI that drafts from parquet, validates data and renders a website. It includes an agent skill for drafting from PDF, HTML or DOC codebooks. **Gaps for us:** no missing-value sentinels (only `required`), no record of changes across releases (just one `version` field), provenance limited to `origin`, parquet-only sources, string-only enum codes. Possible split: data-dict describes a release; we add missing-value codes, history across releases and the stable interface. See [`data_dict.md`](data_dict.md) |
| **gssrdoc** (Kieran Healy) | GSS documentation as an R package; the model for a dataset repository |
| **Natural PDF** (Jonathan Soma) | For parsing PDF codebooks |
| **Narwhals**, **Polars**, DuckDB and Arrow | For dataframe-agnostic access, and for carrying metadata in a file's schema |
| Open-data portals (Socrata, CKAN) | A non-survey use case: city and state open data |

## Source material

These repositories hold the existing work the toolkit generalizes. They are read, not modified, from here.

- **CultureWar** `codebook/`: the gssrdoc conversion, a GSS PDF parser, ANES CDF JSON, a gssrdoc evaluation and errata drafts.
- **CultureWar** `notebooks/gss_extract/` and `notebooks/anes_extract/`: extract builders and missing-code detection.
- **CultureWar** `notebooks/inventories/`: hand-built topic inventories that can serve as answer keys for recall.
- **CultureWar** `notebooks/variable_metadata/variables.yaml`: the analysis layer, which stays in CultureWar.
- **GssExtract** and **ExtractANES**: older extract repos. The ANES codebook build script lives in ExtractANES.
- **MarriageNSFG**: the NSFG across ten cycles, with a download script, a data release and codebooks as text. A third candidate in the GSS/ANES style.

# PublicDataToolkit

Instructions and agent skills for turning a messy public dataset into a well-documented, stable resource.

**Status:** draft, open for review. Started November 2026. The proposal is [`PROPOSAL.md`](PROPOSAL.md), and the draft standard for dataset repositories is [`STANDARD.md`](STANDARD.md). Work in progress is tracked in [`PROJECT_BOARD.md`](PROJECT_BOARD.md).

## The idea

Many important public datasets are hard to use. Examples are the General Social Survey, the American National Election Studies, Monitoring the Future, and city open-data portals. Variable names and codings change across releases. The metadata lives in PDF codebooks. Missing-value conventions vary. And analysis code ends up tied to the details of one release.

This repository doesn't hold any dataset. It holds the **instructions and skills** for building a repository that does. Here is how you would use it:

1. Clone PublicDataToolkit.
2. Point an AI agent at a dataset and tell it to follow the instructions. It either creates a new repository for that dataset or brings an existing one up to standard.
3. The result is a repository that contains:
   - the data, published as a GitHub release when the terms allow it, or scripts and instructions for downloading it when they don't;
   - the dataset's metadata, collected from the codebooks and documentation, with corrections and a record of where each fact came from.

## Three forms of access

The metadata is published in three forms, generated from the same records so they can't drift apart:

| Form | For | Typical use |
|---|---|---|
| **Human-readable** | researchers, students, journalists | browse variables, read question wording, check when and how an item was asked |
| **Programmable** | analysis code and pipelines | look up variables, apply missing-value codes, check availability, compare releases |
| **LLM access** | agents searching for questions | find every item on a topic or in a battery, with search results that say whether they are complete |

## Background

The approach generalizes work on the GSS and ANES in [CultureWar](https://github.com/AllenDowney/CultureWar). It takes inspiration from [gssrdoc](https://github.com/kjhealy/gssrdoc) and relates to [data-dict](https://data-dict.tidyverse.org/). The earlier design is in [`planning/survey_metadata_packages_plan.md`](planning/survey_metadata_packages_plan.md).

## License

Code (lib/, schema/, scripts) is under the MIT License ([`LICENSE`](LICENSE)). The standard, the instructions, the skills and the planning documents are under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Each dataset repository has the same split, and keeps its publisher's terms for the publisher's files.

# PublicDataToolkit: a proposal for review

**Status:** draft for comment, November 2026; revised after the first review. Nothing here is final, and the open questions in §9 are where feedback would help most.

## 1. The problem

Many important public datasets are hard to use well. The General Social Survey, the American National Election Studies, Monitoring the Future and city open-data portals all share some of these problems:

- **The documentation is built for reading, not for code.** Question wording, codes and notes live in PDF or HTML codebooks. Anyone who wants them in a program writes a parser, and most people write their own.
- **Missing-value conventions vary,** and they carry information. "Don't know," "refused" and "not asked this year" mean different things, but most analysis code turns them all into one NaN, often with a regular expression over labels that misses some codes.
- **Things change between releases.** Variables are renamed, reworded or recoded, and the changes are described in release notes that nobody parses.
- **The documentation has errors,** and the corrections live in issue threads and people's notebooks.
- **LLM agents are bad at this documentation.** A codebook with thousands of variables is too big to read in one go. A search returns some matches with no way to know whether it found them all.

## 2. The idea

PublicDataToolkit is a set of instructions, agent skills, templates and a small shared library for turning one public dataset into a **well-documented repository**. Someone clones the toolkit, points an AI agent at a dataset, and the agent builds (or improves) a repository for it, stopping to ask a person whenever terms of use, logins or judgment calls come up.

The durable contribution is the metadata: a reliable, versioned, machine-readable account of what each dataset's documentation says, with errors corrected openly and every fact traceable to its source. Agents help build and use it, but the project should be judged on whether the metadata can be trusted, not on how sophisticated the agents are.

If people adopt it, the result is a family of repositories, one per dataset, with the same structure and the same tools: `pdt-gss`, `pdt-anes-cdf`, `pdt-mtf-12`, `pdt-chicago-crimes`. Code and agents that work with one work with all of them.

The toolkit grew out of work on the GSS and ANES, and takes inspiration from [gssrdoc](https://github.com/kjhealy/gssrdoc), which does much of this for the GSS in R.

## 3. What a dataset repository contains

- **The data, or a reproducible way to get it.** When the publisher's terms allow redistribution, the data is a GitHub release with checksums. When they don't, a download script fetches it from the publisher, or documents the manual steps when a login or click-through is required. The data is never in git.
- **A sources manifest** listing every file the repo depends on: URL, release, date fetched, checksum and terms.
- **Metadata records** for every variable in every release: label, question text, the full value set with missing codes typed, availability by wave and form, notes, and where each fact came from. Every record names its dataset and release. Provenance is recorded per field, and per code for missing values, so question wording from the codebook, availability from the data file, and a classification made by a person are each labeled as such.
- **Corrections** to the publisher's documentation, as records with their own ids: the original text, the corrected text, evidence, author, date, the releases they apply to, and a link to the upstream report. A test fails when a correction's original text no longer appears, which usually means the publisher fixed it.
- **The build code** that turns the publisher's documentation into records, so anyone can rebuild everything from a clean clone.
- **Three generated forms** of the metadata (§4).

What it does **not** contain: analysis decisions. Which answers count as "agree," how to weight, which variables to harmonize: those belong to the projects that use the data.

The full specification is [`STANDARD.md`](STANDARD.md), and the record formats are JSON Schemas in [`schema/`](schema/).

## 4. Three forms of access, from one set of records

| Form | For | What the repo provides |
|---|---|---|
| **For people** | A researcher checking wording before citing it; a student browsing; a journalist checking when a question changed | A static site with a page per variable: wording, codes, missing types, when and to whom it was asked, corrections, and links to the publisher; pages for each release and for what changed between releases |
| **For code** | Analysis code that loads data, recodes missing values and checks availability, getting the same answer every run | The records as JSONL, readable from any language, and a Python library: look up a variable, recode missing values by type (DK one way, "not asked" another), check availability, compare releases. A small R reader once the format settles after the first three datasets |
| **For LLM agents** | An agent asked to find every question on a topic, or every item in a battery | An index plus "shards" small enough to read in full, a compact one-line-per-variable form, and search results that say whether they are complete |

All three are generated from the same records, so they can't drift apart.

**Completeness for agents.** Some questions have exact answers: "every item in this battery," "every agree/disagree item on ballot A in 1985." The records support these by construction, and results say `complete`. Topic questions ("every question about gay rights") don't have exact answers, because wording changes over decades and no tag set is complete. For those, the goal is high recall that can be measured against hand-built lists, and results say `approximate`. An agent should always know which kind of answer it is giving.

The labels are defined by how a result was produced, not by anyone's confidence. `complete` means the result is every record in scope matching a filter on facts taken from the publisher or the data file. The result carries the filter and the scope, so anyone can rerun it and get the same set, and the tests do. A third label, `complete_by_rule`, covers filters that also use properties computed by a published, versioned rule, such as "agree/disagree scale".

## 5. Principles

1. **Describe the data; don't analyze it.**
2. **Keep the publisher's identity.** Variables keep their published names. Links between variables record continuity the publisher asserts, such as a crosswalk, and never equivalence we infer.
3. **Copy text verbatim, and fix errors with corrections,** not edits, so the original stays visible.
4. **Leave a field empty rather than guess.**
5. **Every fact has an origin:** the publisher, the data file, a named rule, a person, or a model. Anything generated by a rule or an LLM is labeled as such and never overwrites what the publisher said.
6. **An open question beats a confident mistake.** When the documentation doesn't say what a code means, the record says `unresolved` instead of guessing, and the checks report it rather than fail.
7. **Respect each publisher's terms.** Each dataset records, after review by a person and as separate permissions, whether its data, its documentation and the metadata we derive may be redistributed, and whether its documentation may be sent to a hosted LLM. Anything not yet reviewed doesn't ship.

## 6. How repositories stay consistent

The risk with many repositories built by different people and agents is that they quietly drift apart. Three things guard against it:

- **A shared library** for everything that must behave the same everywhere: loading, validation, missing-value recoding, release comparison, generating the three forms. Only the step that parses one publisher's documentation is dataset-specific.
- **A definition of done.** `pdt check` validates every record against the schemas and checks:
  - coverage against the data file;
  - that every missing code is typed and sourced;
  - that every source file is checksummed;
  - that corrections still apply;
  - that the generated forms are current;
  - that nothing restricted by the terms is published.

  A repository meets the standard when the check passes. **Passing establishes structure, not truth.** The check can confirm that every variable in the data file has a record and that every code is accounted for. It can't confirm that question wording was copied correctly or that a code's meaning was read correctly. That's why provenance and source locations are kept, so any fact can be checked by hand, and why the acceptance criteria in §8 include checks against known answers.
- **Versions.** The standard, the template and the library share one version number. Dataset repositories are generated with [Copier](https://copier.readthedocs.io/), which can bring an existing repository forward to a newer template. A breaking change comes with an upgrade guide an agent can follow, and older repositories keep validating against the version they declare.

**Names.** `pdt-<dataset-id>`, where the id starts with the name people already use (`gss`, `anes-cdf`, `nsfg`). There's no language in the name, because the repositories are language-neutral. A registry in this repository records which ids are taken, and the GitHub topic `publicdatatoolkit` marks the rest.

**Relation to other tools.** Directory names follow [Cookiecutter Data Science](https://cookiecutter-data-science.drivendata.org/) where the meaning is the same (`data/raw`, `references/`, `docs/`), but a dataset repository isn't an analysis project, so it doesn't use the rest of that layout. An analysis project built with Cookiecutter Data Science would use a dataset repository as a source. For each release, the records are also exported to [data-dict](https://data-dict.tidyverse.org/) YAML, so data-dict's validator and renderer work on them. Our own format stays the source of truth because it holds things data-dict doesn't yet: typed missing values, history across releases, corrections and provenance.

## 7. Where things stand

- **Written:** the standard ([`STANDARD.md`](STANDARD.md), version 0.1) and the schemas, tested on real GSS and ANES records.
- **Next:** small slices of three surveys chosen to be different from each other. The GSS is the reference case. The ANES cumulative file has wording that varies by year. Monitoring the Future renames every variable every year and splits its questionnaire into forms. The test: the same code and the same agent files work on all three without knowing how their documentation is organized.
- **After that:** the agent instructions, the Copier template, the shared library, and a dataset that isn't a survey, such as a city open-data portal.

## 8. How we will know this works

For each of the first three datasets:

- **Coverage:** every variable in a release has a metadata record, and every record matches a variable in the data.
- **Missing values:** every missing-value code has a documented classification or an explicit `unresolved` status.
- **Provenance:** every fact in every record traces to a source file, a named rule, a person or a model.
- **Reproducibility:** rebuilding from a clean clone and the documented sources produces the same records. LLM drafts are kept, not regenerated.
- **Release comparison:** comparing two releases finds the changes the publisher documents in its release notes.
- **Corrections:** known errata, such as the GSS question-text errors already reported upstream, are recorded and still apply.
- **Across datasets:** the same code and the same agent files answer the same kinds of question for the GSS, the ANES and Monitoring the Future, with no dataset-specific branches in the shared library.
- **Agents:** a structural query (every item on one ballot or form) returns exactly the hand-checked answer and is labeled `complete`. A topic query that appears in all three surveys reaches high recall against a hand-built answer key while reading far less than the full documentation.

## 9. Questions for reviewers

1. **Scope.** Is one repository per dataset the right unit, or would one package covering many datasets serve people better?
2. **Format.** Is it right to keep our own record format and export data-dict, rather than extend data-dict directly?
3. **Missing values.** The standard types missing codes as `dk`, `refused`, `no_answer`, `inap`, `skipped`, `not_asked`, `not_available`, `uncodeable` and `other`, one code can have several, and a code nobody can classify yet is `unresolved`. Does this fit the datasets you know?
4. **Structure.** One "group" type covers batteries, codebook sections, modules and questionnaire forms. One "link" type, with a list of relations, covers renamed, reworded and derived variables. Will these hold up?
5. **Terms of use.** Is "ship, build-only or unknown" for data, documentation and metadata, plus a separate answer for LLM processing, enough to handle the datasets you work with?
6. **Languages.** The repositories are language-neutral, the first library is Python, and a small R reader will follow once the format settles. What would R users need from it?
7. **Agents.** Are the `complete` and `approximate` labels on search results useful? What else would an agent need to answer questions about a dataset reliably?
8. **Datasets.** Which datasets would benefit most? Would you build or maintain one?

Comments are welcome as GitHub issues on this repository.

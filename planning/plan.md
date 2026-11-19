# PublicDataToolkit plan (Task 1)

**Status:** first draft, 2026-11-19 (day 1 of snake_case). The public summary is [`../PROPOSAL.md`](../PROPOSAL.md). §3 is superseded by [`../STANDARD.md`](../STANDARD.md), and naming and versioning by [`versions_layout_names.md`](versions_layout_names.md). Decided: one repo per dataset; our JSONL records as the source of truth, with data-dict YAML exported; the spike covers GSS, ANES and MTF (§10). Other decisions are still open.

Sources:
- [`context.md`](context.md): today's discussion;
- [`inventory.md`](inventory.md): what exists for the GSS, ANES and NSFG (Task 3);
- [`survey_metadata_packages_plan.md`](survey_metadata_packages_plan.md): the Nov 17 design. It's called "the earlier plan" below, with section numbers like §5.

## 1. Goal

> Give anyone with an AI agent a reliable way to turn a messy public dataset into a well-documented repository: the data (or a reproducible way to get it), and its metadata published in three forms (for people, for code and for LLMs) that all come from the same records.

GSS and ANES are where we start, and gssrdoc is the model. But the output is a **standard and the instructions for meeting it**, not one package that covers a fixed list of datasets.

### What changed from the earlier plan

The earlier plan designs one package (`surveydoc`) with a shared core and one adapter per dataset. This plan keeps its substance but changes the delivery:

| | Earlier plan | This plan |
|---|---|---|
| Unit of output | an adapter module inside one package | **one repository per dataset**, built to a common standard |
| Who builds a new dataset | the package maintainers | **anyone, with an agent**, following this repo's instructions |
| Shared code | the `core` module | a small shared library that dataset repos depend on (§4.4), plus templates |
| Scope | surveys | surveys first, but also administrative and open-portal data |

What carries over unchanged:
- the design principles (earlier §2);
- most of the data model (earlier §5);
- the agent views and the two kinds of completeness (earlier §7);
- recall measurement against the CultureWar inventories (earlier §7.5);
- the non-goals (earlier §8);
- the gssrdoc strategy (earlier §9).

The main new risk is **drift between dataset repos**. If each repo is built by a different agent run, they can quietly diverge. The defense is a machine-checkable definition of done (§3.3) and a shared library for the parts that must behave identically.

## 2. What this repository contains

```text
PublicDataToolkit/
  README.md            what this is, how to use it
  STANDARD.md          what a finished dataset repo must contain (§3); the definition of done
  instructions/        the procedure an agent follows, step by step (§5)
  skills/              agent skills for the steps that vary by source (§6)
  templates/           files copied into a new dataset repo: README, CLAUDE.md,
                       sources.yaml, download script, tests, CI workflow
  schema/              JSON Schema for the metadata records (§4)
  lib/                 the shared library (§4.4): load, validate, render, shard
  examples/            small worked slices (GSS, ANES, one non-survey dataset)
  planning/            designs like this one
```

**How it's used.** Clone this repo, then tell the agent something like: "Use PublicDataToolkit to build a dataset repo for Monitoring the Future in `~/mtf-data`," or "Bring `MarriageNSFG` up to the PublicDataToolkit standard." The agent reads `STANDARD.md` and `instructions/`, works through the steps, and finishes with the check in §3.3. Steps that need a human, such as accepting terms of use, logging in, or a manual download, stop and ask.

## 3. The target: a finished dataset repository

> **Superseded (2026-11-19).** [`STANDARD.md`](../STANDARD.md) now defines the layout, the manifests, the definition of done and the generated views. Differences from this section: repos are named `pdt-<dataset-id>`; there is a `dataset.yaml`; terms (`ship`, `build-only`, `unknown`) are separate from acquisition (`automated`, `manual`); the site goes in `docs/`; and there are 11 checks rather than 7. This section is kept as the record of the first draft.

### 3.1 Layout

```text
gss-data/                     (one repo per dataset; name to be decided, §10)
  README.md                   what the dataset is, terms, how to get the data, how to cite
  CLAUDE.md                   instructions for agents working in this repo
  sources.yaml                the sources manifest (§3.2)
  scripts/download.py         fetches the data and documentation; --check mode; terms gate
  metadata/
    releases/<release>/variables.jsonl    canonical records, one variable per line
    groups.jsonl, links.jsonl             batteries/sections/modules; continuity across releases
    corrections.jsonl                     errata: original, corrected, evidence, upstream link
    annotations/                          topic tags, aliases, summaries (labeled, optional)
    changes/<old>__<new>.md               what changed between releases
  build/                      parsers that turn the publisher's documentation into the records
  site/                       generated human-readable pages (§3.4)
  agent/                      generated LLM views: index.md, shards (§3.4)
  tests/                      schema, coverage, missing-code and round-trip checks
```

The data itself is never in git. It is a **GitHub release** (with SHA-256 sums) when the terms allow it, as MarriageNSFG does, or it is fetched by `scripts/download.py` when they don't.

### 3.2 The sources manifest

Every file the repo depends on is recorded in `sources.yaml` with:
- URL;
- file name;
- release;
- date fetched;
- checksum;
- terms (`ship`, `build-only` or `manual`);
- a note on how to get the file when a download can't be automated.

The ANES site blocks `curl` and Pew forbids automated downloads, so "manual, documented" is a legitimate state. An undocumented file is not.

This generalizes NSFG's `download_nsfg.py` (inventory §5), which is the best existing practice.

### 3.3 Definition of done

A command in the shared library, roughly `pdt check`, verifies:

1. **Schema:** every record validates against `schema/`.
2. **Coverage:** every variable in the data file has a metadata record, and every record matches a variable in the data file (when the data is available).
3. **Missing codes:** every code is typed (`valid` or `missing`, with a missing type), and every missing code has a source: the publisher, a rule or a hand edit.
4. **Provenance:** every source field traces to a file in `sources.yaml`.
5. **Corrections:** each one still applies; a test fails if the original text has disappeared upstream.
6. **Generated views are current:** `site/` and `agent/` were regenerated from the current records.
7. **Terms:** nothing marked `build-only` is in git or in a release.

The check is what keeps dataset repos built by different agents from drifting apart (§1).

### 3.4 The three forms of access

| Form | Users and use cases | What the repo provides |
|---|---|---|
| **Human-readable** | A researcher checking question wording before citing it. A student browsing what's available. A journalist checking when a question changed. | A static site: one page per variable (wording, codes with labels and missing types, years and forms asked, corrections, links to the publisher), pages per group and per release, and "what changed" pages. Possibly built with data-dict's `render-spec` (§4.3) |
| **Programmable** | Analysis code that loads, recodes and checks availability, with the same answer every run. Pipelines that detect a new release and report what changed. | A Python API from the shared library: `meta["homosex"].values`, `meta.availability(...)`, `meta.apply_missing_values(df, dk=..., inap=...)`, `compare(release_a, release_b)` (earlier §6). JSONL that R or anything else can read directly |
| **LLM access** | An agent finding every question on a topic, or every item in a battery, and saying whether its answer is complete. An agent writing analysis code that uses the right codes. | Shards small enough to read in full, an index, a one-line-per-variable text form, lexical search whose results describe the search and say whether they are `complete`, `complete_by_rule` or `approximate` (earlier §7.4). A skill file telling agents how to use these. MCP later if it earns its keep |

The inventory found that what exists today serves the first two forms partly and the third barely. The LLM-oriented files are single JSON files of 1–21 MB, too large to read whole (inventory, "Mapping to the three forms").

## 4. Metadata model

### 4.1 Start from the earlier plan's model

The entities from earlier §5 carry over:
- Dataset, Release, Variable;
- Question text (stem separate from item);
- Value set with **typed missing codes**;
- Availability as (wave, form, sample) records;
- Group, Link, Correction;
- Derived property, Annotation, Provenance.

The two likely stress points it names (one `Group` type for sections, batteries and modules; `Link` mixing identity and transformation) are still open.

### 4.2 Fixes the inventory makes necessary

- **One schema for every dataset.** The existing GSS and ANES JSON already disagree:
  - name case: lowercase for the GSS, uppercase for the ANES;
  - field names: `description`/`modules` versus `missing_codes`/`valid_range`.

  Both store structured data as strings.
- **Missing types, not a regex.** Both existing detectors collapse DK, refused and IAP into one NaN. The GSS regex also misses real missing codes whose label starts with "no", such as `adhdknow` code 3 "no answer".
- **Missing codes per variable.** gssrdoc attaches the same ten `NA(x)` tokens to almost every variable, so per-variable missing codes have to come from the data file's labels or the codebook.
- **Changes between releases as data.** The GSS "What's New" and release notes PDFs have never been parsed. Changes between releases are the core of "stable APIs," so they need a structured form: `links.jsonl` plus generated `changes/` pages.
- **Machine-readable corrections.** Today the errata exist only as markdown.

### 4.3 Relationship to data-dict

data-dict (Hadley Wickham) covers a lot of what we need for a single release: tables, columns, types, enum labels, constraints, a validator and a rendered site. It lacks several things we need:
- missing-value sentinels;
- history across releases;
- provenance beyond one `origin` link;
- sources other than parquet;
- numeric codes (enum values must be strings).

**Proposal:** keep our JSONL records as the canonical form, and **export** a data-dict YAML for each release. Then each dataset repo gets data-dict's validator and rendered site for free. Missing codes, links, corrections and annotations live in our files. Some of them may move upstream into data-dict if Hadley wants them. Raise this with him at snake_case (Task 6).

The alternative is to make data-dict YAML the canonical form, with our additions in its free-text fields or an extension block. That ties us to a v0.0.3 spec, and missing types and history would be second-class.

### 4.4 The shared library

The generic operations have to behave identically everywhere, and an agent shouldn't write them anew for each dataset:
- loading and validation;
- missing-value recoding by type;
- availability and release comparison;
- shard generation and search;
- rendering the site;
- the `pdt check` definition of done.

They live in one small installable library, in `lib/` here, possibly published later as `publicdatatoolkit` on PyPI, where the name is free. Dataset repos depend on it.

Only the **build** step is dataset-specific: parsing this publisher's documentation into records. That's where agents and skills do the work.

## 5. The procedure an agent follows

These are the eight steps the inventory found recurring across the GSS, ANES and NSFG, all done by hand each time. Each becomes a file in `instructions/`:

1. **Survey the dataset.** Publisher, releases, file formats, documentation formats, terms of use, existing tools (IPUMS, gssrdoc, ICPSR search). Stop if a good tool already exists; earlier §11 lists those cases.
2. **Write `sources.yaml` and the download script.** Record terms, and document any manual steps.
3. **Parse the documentation into records.** Use the skill for the format: PDF, HTML, DDI XML, Stata/SPSS labels, a Socrata or CKAN API, or an existing structured package. Check coverage against the data file's variable list.
4. **Type the missing codes.** Use publisher markings first, then labels from the data file, with rules and hand edits recorded as such. Never a bare list.
5. **Record availability** by wave, form and sample, checked against the counts of non-missing values in the data.
6. **Link releases and record corrections.** Use the publisher's crosswalks and release notes; collect errata from the publisher and from issues.
7. **Generate the three forms** with the shared library.
8. **Publish and check.** Make the data release, if the terms allow it, then run `pdt check`, then write the README and CLAUDE.md from the templates.

Agents may draft records with an LLM, for example from a PDF codebook. But drafts are validated against the schema and checked deterministically, and they are marked as model-derived until a human reviews them. The runtime behavior stays deterministic (earlier §13, "LLM-built metadata").

## 6. Skills

One skill per source format, all producing the same records:

| Skill | Source | First real case |
|---|---|---|
| `from-structured-package` | an existing package (gssrdoc `.rda`, R/Stata label sets) | GSS via gssrdoc |
| `from-html-codebook` | HTML codebooks | ANES CDF (rescue `extract_cdf_codebook.py` from ExtractANES) |
| `from-pdf-codebook` | PDF codebooks, with LLM-assisted drafting | GSS 2024 PDF, NSFG, MTF |
| `from-data-labels` | Stata/SPSS/SAS value labels in the data file | all three; the cross-check for missing codes |
| `from-ddi-xml` | DDI XML (ICPSR) | MTF, if ICPSR provides it |
| `from-open-data-portal` | Socrata, CKAN, ArcGIS Hub metadata APIs | a Chicago or Illinois dataset |
| `release-diff` | two releases' records, plus release notes | GSS 2024 R1 → R3a |
| `use-dataset-repo` | for agents *consuming* a finished repo: how to search, read shards, report completeness | everything |

## 7. Datasets

| Order | Dataset | Why | Notes from the inventory |
|---|---|---|---|
| 1 | **GSS** | Reference implementation; the most existing material; gssrdoc as the upstream | The catalog can't be rebuilt today: `convert_gssrdoc_to_json.R` reads a local gssrdoc clone that isn't available |
| 2 | **ANES CDF** | Much of the machinery exists | The build script and its HTML input are stranded in ExtractANES with no record of where the HTML came from; `valid_range` errors such as VCF0803 |
| 3 | **Monitoring the Future** | The adversarial case: forms, V-numbers that change every year, PDF codebooks | ICPSR terms: probably build-only |
| — | **Open-portal dataset** | Tests whether the standard works beyond surveys. Socrata has a metadata API, and portals change often, which exercises `release-diff` | Pick at snake_case |
| later | **NSFG** | Already has the best data-release practice; needs metadata | Codebooks are plain text and cover cycle 12 only |

## 8. Terms of use

Every dataset gets a terms entry before anything is shipped: whether the data can be redistributed, whether the documentation can, and whether its text may be sent through an LLM.

**Who decides.** For now, Allen signs off on each dataset; the instructions make the agent stop and ask.

## 9. snake_case: what to do in the remaining time

**Decided 2026-11-19:** the three-survey test from the earlier plan (earlier §13): GSS, ANES and MTF. That's ambitious for a day and a half, so the plan is ordered so that stopping at any point still leaves something to show.

1. **Today: write `STANDARD.md` and `schema/`,** adapted from §3–4 and earlier §5, concrete enough for an agent to follow.
2. **GSS slice (30–50 variables)** from CultureWar's existing extracted JSON. It should include a battery, a ballot-split item, typed missing codes and the `racopen`/`racfew` corrections. This is the reference and should be done first.
3. **ANES CDF slice (30–50 variables)** from `anes_cdf_minimal.json` and the data's Stata labels. It should include thermometers, a pre/post item, and DK/RF/INAP codes. The build script in ExtractANES is the starting point.
4. **MTF slice:** one 12th-grade year with two or three forms, plus a few items whose V-number changes across years. This is the adversarial case. It needs the ICPSR codebooks downloaded (ICPSR login) and a check of the terms before any of it goes through an LLM. If that can't happen today, MTF moves to tomorrow morning, built by an agent from the PDF codebook using the instructions. That also tests the instructions themselves.
5. **Tomorrow afternoon:** generate the three forms for all three slices and run:
   - one **structural** query, such as every agree/disagree item on one ballot or form, checked against a hand list;
   - one **topic** query that appears in all three surveys (marijuana is a good candidate), scored against a hand-built answer key.
6. **Demo:** the same code and the same agent views work on GSS, ANES and MTF without knowing how their documentation is organized.

**What we learn either way** (the main result; write it down as we go):
- what had to go into dataset-specific extensions, and why;
- where the instructions or the agent got stuck;
- what data-dict could or couldn't express.

**A fourth dataset.** If a teammate joins, an open-portal dataset is still the best test of the standard beyond surveys, and it could run in parallel. Otherwise it's next after snake_case.

**Before starting MTF:** an ICPSR login, the terms check, and choosing the year and forms.

## 10. Decisions for Allen

1. **Delivery — decided 2026-11-19:** one repo per dataset, built from this toolkit, with a shared library.
2. **Canonical format — decided 2026-11-19:** our JSONL records are the source of truth, and data-dict YAML is exported for each release. Still talk to Hadley (Task 6) about which gaps might go upstream.
3. **GSS upstream — decided 2026-11-19:** option C, a hybrid that starts as A. Stay downstream of gssrdoc, pinned per release: 0.9 documents Release 3 exactly, so add a 7224r3 release; 7224r3a uses 0.9's text with the mismatch recorded. The Stata file stays the authority for labels and codes. Names gssrdoc lacks (`vote_ts`, `pres_ts`) come from the R3a codebook. The options are in the board's Task 21 section.
4. **Dataset repo names — decided 2026-11-19:** `pdt-<dataset-id>`, with one version number and Copier for updates, and CCDS names for shared directories. See [`versions_layout_names.md`](versions_layout_names.md) (Task 8).
5. **Extract builders — decided 2026-11-19:** dataset repos ship an extract builder, `scripts/extract.py`, like GssExtract did. The user names the variables, years and missing-value handling; the builder uses the shared library's recoding. Data releases hold the publisher's original files plus a common format (parquet) that keeps missing codes distinct. See STANDARD.md §1, §8 and §10.
6. **The snake_case spike — decided 2026-11-19:** GSS, ANES and MTF (§9). An open-portal dataset is optional.
7. **Public repo:** when to publish (Task 4), and whether the earlier plan goes public as is.
8. **Carried over from earlier §14:** Python only? Annotations shipped as an optional, labeled layer? Archive GssExtract and ExtractANES once they're superseded?

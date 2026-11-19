# Survey metadata packages (Task 186)

**Status:** proposal, revised 2026-11-17. Nothing built yet. Decisions for Allen are in §14. A two-day hackathon spike to test the design is in §13.

## 1. Mission

> Provide a stable, machine-readable metadata interface for public survey datasets whose published documentation and coding conventions are hard to use programmatically: for scripts and analysis pipelines, and for LLMs and agents searching for questions.

The package describes what each variable in a published survey is: its question text, coded values, missing codes, when and to whom it was asked, where each fact came from, and known errors in the official documentation. It came out of the GSS and ANES work for CultureWar, but it isn't about the book or limited to the surveys we use.

It serves two audiences:

- **Code:** scripts and pipelines look up variables, apply missing-value rules and check availability, and get the same answers every run.
- **Agents:** an LLM or agent searching for questions. Structural queries ("every item in this battery," "every agree/disagree item asked in 1985") can be complete by construction. For topic queries ("every question about gay rights"), the package makes high recall measurable and gives the agent a bounded set of candidates it can read in full, without reading the whole codebook.

In one line: not a chatbot over codebooks, but a reliable metadata layer whose structure lets both programs and agents reason about survey documentation, and lets agents tell exhaustive structural retrieval from approximate topic retrieval.

## 2. Design principles

1. **The package describes published data; it does not decide how variables should be analyzed.** Question wording and missing codes belong in it. "Count strongly agree and agree as 1" does not, and neither do weighting and mode decisions. This is the test for feature requests.
2. **Preserve source identity; don't harmonize it away.** Each variable keeps the publisher's name in its own release. Links between variables come in two kinds:
   - **Continuity the publisher asserts** belongs in the package: the same GSS name across years, a publisher or ICPSR crosswalk, an ANES CDF variable built from single-year items.
   - **Equivalence we infer** (that two differently worded items measure the same thing) is a non-goal.

   This matters most for MTF. The same question gets a different V-number each year, so a package that can't record published linkage gives MTF users little.
3. **Every field traces to its source, an explicit correction, or a labeled derivation.** Errata are one case of this: the original text, the corrected text, the evidence and the upstream issue. Anything we generate is the other case, whether by rule (scale signatures, inferred batteries) or by a model (topic tags, plain-language summaries). It's marked as derived and records how it was made, and it never overwrites source fields.
4. **Two audiences, one model.** Agent-facing views are generated from the same canonical records the code uses, never maintained by hand, so they can't drift apart.
5. **Partial information is fine.** An adapter leaves a field empty when the source doesn't provide it; it never makes one up. Not every dataset supports every field.

## 3. What we have now

| Piece | Where | Reusable or ours |
|---|---|---|
| GSS codebook converted from gssrdoc (6,904 variables, 1972–2024) | [`codebook/convert_gssrdoc_to_json.R`](codebook/convert_gssrdoc_to_json.R) → `codebook/extracted/gssrdoc_*.json`; evaluated in [`codebook/gssrdoc_evaluation.md`](codebook/gssrdoc_evaluation.md) | Reusable |
| GSS 2024 codebook parsed from the NORC PDF (477 variables, with 2024 frequencies) | [`codebook/extract_codebook.py`](codebook/extract_codebook.py) → `codebook/extracted/variables*.json` | Reusable, mostly superseded by gssrdoc |
| GSS missing-code detection from value labels | [`notebooks/gss_extract/catalog.py`](notebooks/gss_extract/catalog.py) | Reusable |
| GSS extract builder | [`notebooks/make_gss_extract.py`](notebooks/make_gss_extract.py) | Mixed: reading, recoding and `cohort` are generic; the `marsame` merge and the interviewer-mode raking (Task 175) are our decisions |
| ANES CDF codebook as JSON (1,030 entries) | `codebook/extracted/anes_cdf_minimal.json`, `anes_cdf_summary.csv` | Reusable. **The build script did not come over:** it's still in `ExtractANES/codebook/extract_cdf_codebook.py`, with the codebook HTML it reads and the fuller `anes_cdf_dict.json`. So this repo can't rebuild the ANES codebook for a new CDF release |
| ANES missing codes (DK/RF/INAP), CDF, pilot, panel and single-year builders | [`notebooks/anes_extract/`](notebooks/anes_extract/) | Mixed, as with the GSS |
| ANES pilot/panel inventory and harmonization | [`codebook/anes_pilot_panel_extracts_inventory.md`](codebook/anes_pilot_panel_extracts_inventory.md), [`codebook/anes_pilot_panel_harmonization.md`](codebook/anes_pilot_panel_harmonization.md) | Reusable as documentation |
| Pew ATP catalog and wave index; ingest and extract | `codebook/extracted/pew_catalog.csv`, `pew_atp_waves.csv`; [`notebooks/external/pew_ingest.py`](notebooks/external/pew_ingest.py), [`notebooks/pew_extract.py`](notebooks/pew_extract.py) | Partly reusable; Pew's terms limit what can be shared (§11) |
| Copying codebook text into our metadata | [`scripts/fill_question_verbatim.py`](scripts/fill_question_verbatim.py) | The lookup is reusable; the YAML it writes is ours |
| Corrections to the GSS documentation (`racschol`, `racopen`, `racfew`, `rachaf`) | [gssrdoc issue #1](https://github.com/kjhealy/gssrdoc/issues/1) | Reusable: errata |
| Topic inventories from hand sweeps of the GSS, ANES and other sources | [`notebooks/inventories/`](notebooks/inventories/) (orientation, race, ethnicity, gender, religion, …) | Ours, but valuable as **answer keys** for measuring agent search recall (§7.5) |
| Per-variable figure and analysis metadata (`selected_values`, titles, subtitles, legend labels, codings) | [`notebooks/variable_metadata/variables.yaml`](notebooks/variable_metadata/variables.yaml) | Ours |
| `where_used.py`, `check_question_wording.py` | `scripts/` | Ours |

**The dividing line** (principle 1). The package takes the *codebook layer*: what each variable is, and corrections to the official text. The *analysis layer* stays in CultureWar: which answers count as y=1, valence, titles, merge rules, weighting and mode decisions.

## 4. Architecture

Three layers:

1. **Source adapters** (dataset-specific, messy by nature): read the publisher's materials (gssrdoc, ANES codebook HTML, MTF PDFs or DDI XML, BRFSS codebooks) and produce canonical records.
2. **Canonical metadata model** (§5): the stable representation the package exposes. This is the product.
3. **Operations and views** (§6, §7): generic code built only on the model, covering lookup, search, availability, missing-value recoding, release comparison and the agent-facing views.

```text
surveydoc.core      model, validation, operations, views
     ↑
     ├── surveydoc.gss
     ├── surveydoc.anes
     └── surveydoc.mtf
```

Adapters depend on `core`. `core` knows nothing about any dataset, and adapters never import each other. That rule is what makes it cheap to move an adapter into its own package later.

**Repo structure.** One repo, one package, one module per dataset, rather than one repo per dataset. The core is most of the code, and the shared model is what's worth publishing. Separate repos would either copy the core and let the copies drift, or need a core package anyway, and one maintainer would carry three to five sets of CI, releases and docs. A dataset can move to its own package if it gets an outside maintainer or a large separate audience. Optional dependencies (an HTML parser, a PDF parser) go in pip extras. PyPI names checked 2026-11-17: `surveydoc`, `gssdoc`, `gsspydoc`, `anesdoc`, `mtfdoc`, `survey-codebooks` are free; `codebooks` and `pycodebook` are taken.

## 5. Data model

A first version, meant to be broken by the spike (§13).

| Entity | Fields | Notes |
|---|---|---|
| **Dataset** | id, publisher, URL, terms (`ship` or `build-only`) | Terms decide whether built metadata can be distributed (§14 Q4) |
| **Release** | dataset, release ID, date, source files with hashes, adapter version | Lets us compare releases and detect upstream changes |
| **Variable** | dataset, release, name (source identity), label, question text, value set, availability, universe, source location (page, URL, NORC ID), corrections, extensions | `extensions` is a dict namespaced by adapter for things the core doesn't model yet |
| **Question text** | stem, item text, interviewer instructions, show-card text, kept separate when the source separates them; otherwise verbatim | Battery items share a stem. Keeping the stem separate is what makes battery search work (§7.3) |
| **Value set** | codes: code, label, kind (`valid` or `missing`), missing type (`dk`, `refused`, `inap`, `no_answer`, `skipped`, `other`) | Missing types matter: a pipeline may treat INAP differently from DK. The two regex versions in CultureWar collapse them |
| **Availability** | records: wave or year, form or ballot, sample or mode, optional N | Not just a list of years. MTF forms, GSS ballots and ANES pre/post waves all need it. This is where GSS/ANES assumptions are most likely to leak in |
| **Group** | id, kind (`battery`, `section`, `module`), stem, members in order, origin (`source` or `derived`) | Source groups: gssrdoc modules, codebook sections, MTF question sets. Derived groups (§7.3) are labeled as derived. **Likely stress point:** these are different relationships. A codebook section organizes the document, a battery is questionnaire structure, a module is about administration, and a derived battery is an inference. One `Group(kind=...)` may not hold all four; the spike should try to break it |
| **Link** | from, to, kind (`same_item`, `renamed`, `wording_changed`, `derived_from`), source | Only continuity the publisher asserts (principle 2). **Likely stress point:** the kinds mix identity, transformation and provenance, and one pair can be both renamed and reworded. May need several links per pair or a richer relation object; flag it in the spike, don't solve it yet |
| **Correction** | variable, field, original, corrected, evidence, upstream issue, status | A test flags any correction whose original text no longer appears upstream, which means upstream fixed it |
| **Derived property** | variable or group, kind (`scale_signature`, derived group membership), value, rule and version | Deterministic and reproducible from source fields. Exact, like a source field, but labeled as derived |
| **Annotation** | variable or group, kind (`topic`, `alias`, `summary`), value, origin (`human`, `rule` or `model`), method (model + prompt version + date, or rule, or reviewer), reviewed | Retrieval aids, not facts about the survey. Kept in separate files from source records; never overwrites them (principle 3). `alias` holds retrieval aliases in general ("homosexual" → gay, lesbian, LGBT, sexual orientation), not only modern terms |
| **Provenance** | per field: source file and location, correction ID, or annotation method | Designed in from the start; the first implementation may record it per variable rather than per field |

**Storage.** The canonical form is a JSON Schema and one JSONL file per release, one variable per line, plus files for groups, links, corrections and annotations. Python loads these into typed objects. JSONL is grep-able, diff-able in git, and loads fast; Parquet can be added if size requires it.

## 6. Operations for code

Built only on the model, so they work the same for every dataset:

```python
meta = surveydoc.gss.metadata("2024r3a")
meta["homosex"].question.text
meta["homosex"].values
meta.availability("homosex")               # waves, ballots
meta.apply_missing_values(df)              # by missing type; options per type
meta.search("death penalty")              # hits plus a description of the search (§7.4)
surveydoc.compare(gss_2024r1, gss_2024r3a) # added, removed, changed variables
```

The extract helper (read a release file, keep columns, recode, write) is secondary and lives in adapters where convenient. The core works without ever reading survey data.

## 7. Semantic access for agents

### 7.1 Why agents change the metadata requirements

Analysis code mostly needs exact lookup and recoding: give me `homosex`, set its missing codes to NaN. Agents searching for questions need more from the same records:

- explicit groups (batteries, sections, modules), so they can take a whole battery at once;
- retrieval aliases, because question wording from 1972 doesn't use today's words;
- normalized scale types, so a query about response format is a filter, not a search;
- compact one-line summaries, so a candidate set is cheap to read;
- provenance they can inspect, so they can tell what the publisher said from what was inferred;
- bounded collections they can read to the end.

These are additions to the model, and most of them help human users too, so the agent work comes out of the data model rather than sitting beside it.

### 7.2 Two kinds of completeness

1. **Structural completeness:** "every item in this battery," "every agree/disagree item asked in 1985," "every item on ballot A." These queries filter on exact fields, so the answer can be **complete by construction**.
2. **Topic completeness:** "every question about gay rights." Topics have no exact boundary, so completeness can't be guaranteed. The package's job here is to make recall **measurable** (§7.5) and to let the agent narrow to a bounded set of candidates and read all of it.

An agent should always know which kind of query it is answering, and say so when it reports results.

**Why plain search isn't enough for topic queries.**

- **Wording changes over the decades.** Lexical search misses "homosexuals," "Negro," "colored" and "the Communist Party" when the query uses modern terms.
- **Embedding search** handles synonyms, but there's no point at which you know you've found everything.
- **Source subject tags are incomplete.** In gssrdoc, 1,287 of 6,904 GSS variables have no subject (there are 634 distinct subjects). The ANES CDF JSON has no topic field at all.

### 7.3 Three tiers of retrieval metadata

Kept separate in the API, the files and the docs, because they support different claims:

| Tier | Examples | Exact? | Supports |
|---|---|---|---|
| **Source and structural facets** | dataset, release, years asked, form or ballot, source groups (module, section, battery) | Yes; from the publisher | Complete structural queries |
| **Derived deterministic properties** | scale signature (agree/disagree with 4 or 5 points, favor/oppose, thermometer, spending, yes/no, …); derived batteries from a shared stem, adjacent order and a shared value set | Yes, given the rule; reproducible | Complete queries *relative to the rule*, which is published and versioned |
| **Annotations** | topic tags, retrieval aliases, plain-language summaries, from humans, rules or models | No; aids to retrieval | Higher recall on topic queries; never a basis for a completeness claim |

Examples of annotations: `racopen` gets the topic "housing discrimination" and the alias "fair housing law"; the 1970s `homosex` wording gets the aliases "gay, lesbian, LGBT, sexual orientation."

### 7.4 Agent views

Generated from the canonical model (principle 4), as plain files that any agent can read and any human can inspect, so nothing depends on MCP:

```text
gss/
  index.json        shards with variable counts and token sizes
  index.md          the same, for reading
  by_group/         one shard per source or derived group
  by_scale/         one shard per scale signature
  by_topic/         one shard per topic annotation (labeled as annotation-based)
  variables.jsonl   the canonical records
```

**Shard format:** each shard exists as JSONL, for programs, and as one-line-per-variable text, for agents: name, years, scale type, short question text. The text form exists because tokens read is the cost we're measuring. JSON repeats every key on every line, roughly doubling the size. Both are generated from the same records.

**Size:** a shard is kept small enough to read in full (on the order of 10–20k tokens). For scale: all 6,904 GSS variables at about 40 tokens a line is close to 280k tokens, too much for one read, so the shards are what make "read everything left" practical.

**Search** is a fallback for topics that cut across the shards: lexical search (BM25) over question text and annotations. Embeddings are an optional extra, built locally. Results carry their facet values, so the agent can widen to whole groups.

**Results describe the search, not just the matches.** Every query, whether through the Python API, the CLI or a future MCP tool, returns, along with the hits:

- the number of candidates;
- the total number of variables in scope;
- the filters applied;
- the groups or shards searched;
- the kind of result: `complete` (structural filters only), `complete_by_rule` (filters on derived properties), or `approximate` (any annotation or text search involved).

This is how the API carries the distinction in §7.2. The agent shouldn't have to work out from the hits which kind of answer it got.

**Access paths:** the files first, then a CLI with `--json` output, then an MCP server if it earns its keep.

### 7.5 Measuring recall

The CultureWar inventories are hand-built answer keys for topic searches across the GSS and ANES: orientation, race, ethnicity, gender, religion and others. Run an agent on each topic using only the agent views, and report two numbers:

- **Recall:** the share of inventory items found.
- **Effort:** tokens read, compared with reading the whole corpus.

Do this with and without annotations, and with and without embeddings, which shows which parts are worth shipping. Items the agent finds that aren't in an inventory get checked by hand. Some will be real misses from our original sweeps.

**Optional extension: does explicit structure beat discovered structure?** This corpus has both structure supplied by publishers and topics that have to be inferred, which makes it a good test bed for a question that goes beyond this package. Compare three approaches on the same topics:

1. flat search over all variables (lexical or embeddings);
2. hierarchical search over structure discovered from the text: clusters of embedded question text, named by a model;
3. our approach: exact facets and groups first, then annotations, then reading the whole remaining candidate set.

Measure recall, tokens read, tool calls and false positives. **Write the protocol before running any of them:** the same answer keys, the same token budget and tool access for each approach, and the same scoring. Otherwise "structure helps" becomes a result we tuned our way into.

## 8. Non-goals

- No cross-survey ontology or concept-equivalence claims.
- No substantive harmonization (principle 2).
- No weighting, valence or modeling decisions (principle 1).
- No promise to redistribute documentation or data whose terms forbid it.
- No requirement that every dataset fill every field (principle 5).
- Not a universal data-access package: downloading, credentials and file formats stay in adapters, where convenient, and are optional.

## 9. GSS: build on gssrdoc, contribute back, or build in parallel?

**What gssrdoc is.** An R data package by Kieran Healy, MIT-licensed. The documentation is scraped from GSS Data Explorer (`data-raw/make_gss_doc.R`), and a cleanup step (`data-raw/fix_chrs.R`) is where text corrections would naturally go upstream. We filed [issue #1](https://github.com/kjhealy/gssrdoc/issues/1) on 2026-09-26.

| Option | For | Against |
|---|---|---|
| **Contribute only** (issues and PRs to gssrdoc) | One source of truth for R users; the least work | Doesn't help Python users or agents. Structured value sets and missing types would change the package's data format |
| **Parallel from scratch** (`gsspydoc` scraping GSS Data Explorer itself) | Fully independent | Repeats the scraping gssrdoc already does, and we'd have to maintain a scraper; corrections end up split between two projects |
| **Downstream** (recommended) | Structured, corrected metadata for Python users and agents; no duplicate scraping; corrections still reach R users | Depends on gssrdoc for new GSS releases |

**Recommendation: downstream, and send corrections upstream too.** The GSS adapter reads gssrdoc's `gss_doc`, with credit. Every correction is also filed upstream. The risk is the 2026 GSS release: if gssrdoc doesn't cover NORC's 2026 cumulative file when we need it, we add a fallback source, either the NORC codebook PDF (we already have a parser) or Data Explorer.

## 10. ANES

We haven't found a Python or R package that does this for the ANES; a quick search of PyPI, CRAN and GitHub comes first. What we'd contribute: the CDF codebook parsed into structured records (question text, value sets with DK/RF/INAP typed, years asked), the pilot and panel harmonization, and errata as we find them. The next CDF release, which is expected to fix the known 2024 errors, is a natural test of the build step. The build script and its HTML input move from `ExtractANES` into the ANES adapter, which also closes the rebuild gap in §3.

## 11. Other data sources

Ranked by how much it would help to have structured metadata, after accounting for tools that already exist.

| Source | Why it's painful | Existing tools | Fit |
|---|---|---|---|
| **Monitoring the Future** (ICPSR) | Separate files each year and for each 12th-grade questionnaire form; V-number variable names change across years; codebooks are PDFs | ICPSR's search; ICPSR offers DDI XML for many studies (check whether MTF has it, and whether MTF publishes a crosswalk across years) | **High.** The test of whether the model generalizes. ICPSR terms limit redistribution, so probably build-only |
| **Cooperative Election Study** (CES) | Each year's file has its own variable names | A harmonized cumulative file exists for the core items | Medium. We already use it ([`notebooks/external/ces.py`](notebooks/external/ces.py)) |
| **Pew ATP** | One file per wave; battery letters change between waves; matching depends on labels | None that we know of | Medium. We already have a catalog. Pew forbids automated downloads, so we'd ship a parser only |
| **BRFSS** | A codebook per year; variable names and state modules change | CDC's codebooks | Medium (Task 153) |
| **American Housing Survey** | Variable names change across PUF eras, 1973–2023 | None that cover all the eras | Medium. We built `ahs_recode` (Task 154) |
| **World Values Survey / EVS, ISSP** | Many countries and waves | Integrated files and codebooks already exist | Low; maybe for agent views only |
| **CPS, ACS, NHIS** | | IPUMS already does this well | Don't build |
| **HRS, PSID, NLSY** | | Each has its own variable search | Skip unless we need them |
| **Gallup, Roper iPoll, CIRP Freshman Survey** | | Access and terms are restrictive | Skip |

## 12. Roadmap

Organized to prove the abstraction before existing code can lock it in:

1. **Define the model and adapter interface** (§5): the spike (§13).
2. **GSS adapter:** the source we know best, so mistakes are easy to spot.
3. **ANES adapter:** much of the machinery exists.
4. **MTF adapter:** the adversarial case, to find where GSS/ANES assumptions leak into the model.
5. **Migrate CultureWar** once the model is provisional, not after it's declared stable. CultureWar is the only real user, and "the GSS and ANES extracts come out frame-equal" is a cheap, objective test that a demo won't replace. `variables.yaml` keeps its own copy of `question_verbatim`, so a package update can't change chapter wording without our noticing.
6. **Agent views and the recall evaluation** against the inventories (§7.4, §7.5).
7. **Stabilize the model and API.**
8. **Publish 0.x** once Allen approves.
9. **Add datasets opportunistically** rather than aiming for full coverage.

## 13. Hackathon spike: test the abstraction

The long-term project is a maintained package. The spike isn't meant to build it. It tests the core abstraction before we commit to it, and can be thrown away afterward. Hard-coded mappings, three different parsers, or switching from dataclasses to Pydantic halfway through are all fine.

**Question.** Can one canonical model and adapter interface represent three substantially different documentation systems without dataset-specific branches in the core? And can the same records support both code and agent search?

**Test cases.** Small, deliberately chosen slices:

- **GSS:** 30–50 variables, including at least one battery, a ballot-split item, and the `racopen` and `racfew` corrections.
- **ANES CDF:** 30–50 variables, including thermometers, a pre/post item, and items with DK, RF and INAP codes.
- **MTF:** one 12th-grade year with two or three forms, plus a few items whose V-number changes across years.

**What to build.**

1. A provisional schema (§5) and a minimal adapter protocol.
2. Three small adapters.
3. Generic operations that run unchanged on all three: lookup, text search, availability, missing-value recoding (on small synthetic frames, so nobody needs microdata).
4. Generated agent views for the slices: an index, shards and scale signatures. Lexical search only; **no embeddings** unless everything else is done, since the structure-first approach is what needs testing.
5. If time allows, two AI experiments:
   - **LLM-built metadata:** the LLM produces candidate MTF records from the codebook. These go through schema validation and deterministic checks, and are scored field by field against about 20 records built by hand **before** the event.
   - **Agent search:** an agent searches the slices for a topic that appears in all three surveys, and its results are scored against a hand list.

**Questions to answer.**

- Which fields belong in the core, and which stay adapter extensions?
- Does availability as (wave, form, sample) records cover all three?
- Can missing-value handling be expressed generically, by missing type?
- How much provenance is practical to keep?
- Do scale signatures and battery detection work across sources?
- Does one `Group` model hold sections, batteries, modules and derived batteries? Does `Link` need several dimensions (identity, transformation, provenance)? These are the two places in §5 most likely to break.
- Does the same API feel natural on all three datasets?
- Can AI cut the cost of building an adapter while runtime behavior stays deterministic and auditable?

**Success criterion.** The same user-facing code inspects GSS, ANES and MTF metadata without knowing how their documentation is organized, and the core contains no dataset-specific branches. Two retrieval tests:

- one **structural** query (for example, every agree/disagree item on one ballot or form) returns a complete answer by construction, checked against a hand list;
- one **topic** query that appears in all three surveys reaches high recall against a hand-built answer key while reading far less than the full metadata for the slices.

The main output is a written list of everything that ended up in adapter extensions, with a reason for each.

```python
for ds in [gss, anes, mtf]:
    print(ds.search("marijuana"))
    v = ds.variable(...)
    print(v.question.text, v.values, v.availability)
    df = ds.apply_missing_values(df)
```

**Before the event.**

- Download the MTF codebooks and any DDI files (ICPSR login).
- Check whether ICPSR's terms allow sharing those files with teammates and sending their text through an LLM.
- Pick the slices.
- Build the hand-checked answer keys: the ~20 MTF records and the cross-survey topic list.

## 14. Decisions for Allen

1. **Structure:** one package with a module per dataset (recommended), or one repo per dataset?
2. **Name:** `surveydoc` or something else.
3. **GSS:** downstream of gssrdoc, with corrections sent upstream (recommended)?
4. **Shipping metadata vs building it:** gssrdoc already redistributes the GSS documentation, so we'd ship the GSS metadata. For the ANES and MTF, read the terms of use first. Until then, the package builds from codebooks the user downloads.
5. **Annotations:** ship topic tags and retrieval aliases, labeled with origin and version, as a separate optional layer (recommended), or keep them local? Recommended: ship facets, derived properties, shards, annotations and lexical search; build embeddings locally as an optional extra, so the package doesn't depend on an embedding model.
6. **Old repos:** archive `GssExtract` and `ExtractANES` on GitHub once the package can rebuild everything they did (recommended), or reuse one as the new repo?
7. **Language:** Python only? R users already have gssrdoc for the GSS.

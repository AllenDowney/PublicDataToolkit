# PublicDataToolkit Project Board

Numbered tasks for tracking work. Each task has a permanent number; add new tasks at the end. Update status as work progresses.

**Status labels:** `TODO` | `DOING` | `DONE`

### Current focus (2026-11-19, evening)

Started at the snake_case hackathon, November 19–20, 2026. Background is in [`planning/context.md`](planning/context.md). Four dataset repos exist locally, next to this one; none has a remote yet: `pdt-gss`, `pdt-anes-cdf`, `pdt-nsfg` and `pdt-fars`.

**Done**
- **Task 2:** Recover the earlier planning session. [`planning/`](planning/)
- **Task 3:** Inventory the GSS and ANES work in CultureWar. [`planning/inventory.md`](planning/inventory.md)
- **Task 4:** Publish this repo on GitHub. https://github.com/AllenDowney/PublicDataToolkit (local `main` is ahead; push after Allen checks)
- **Task 8:** Versions, layout and names for dataset repos. [`planning/versions_layout_names.md`](planning/versions_layout_names.md)
- **Task 9:** Remove private information before publishing.
- **Task 10:** Respond to review 1 of the proposal. [`planning/review_1.md`](planning/review_1.md)
- **Task 12:** Tables in a release: in the standard, the schemas and `pdt check`, and used for the NSFG (female, male, pregnancy).
- **Task 14:** Agent views: `agent/` in all four dataset repos, `pdt views` and `pdt search` with completeness labels.

**Doing**
- **Task 1:** The plan. [`planning/plan.md`](planning/plan.md); remaining decisions in plan §10.
- **Task 5:** The snake_case spike.
  - GSS: 50 variables (`pdt-gss`).
  - ANES CDF: 37 variables (`pdt-anes-cdf`).
  - NSFG: 52 variables in three tables (`pdt-nsfg`).
  - FARS: started (`pdt-fars`); see Task 13.
  - MTF: waiting for ICPSR ([`planning/icpsr_email.md`](planning/icpsr_email.md)).
  - Religion is the cross-survey topic.
- **Task 6:** Talk to Hadley Wickham about data-dict. [`planning/data_dict.md`](planning/data_dict.md)
- **Task 11:** Data releases, download scripts and extract builders. The common data format is accepted and implemented (`lib/pdt/data.py`); the rest is in Tasks 18 and 19.
- **Task 13:** FARS slice. The parser for the manual needs work.

**To do, ready for a second thread** (see [Working in parallel](#working-in-parallel))
- **Task 15:** Human-readable site: `docs/`.
- **Task 16:** Export data-dict YAML and validate it with data-dict.
- **Task 17:** Data checks C3–C5 in `pdt check`, using the common format.
- **Task 18:** `download.py` and the data-release workflow.
- **Task 19:** `extract.py`, the extract builder.
- **Task 20:** ANES codebook errors: verify and record as corrections.
- **Task 21:** GSS follow-ups: the 39 variables missing from gssrdoc, release notes, pinning gssrdoc.
- **Task 22:** NSFG question text and earlier cycles.
- **Task 23:** Answer keys and scoring for the topic and structural queries.
- **Task 24:** Agent instructions and skills.
- **Task 25:** Standard changes from the findings so far. Main thread only.

**Withdrawn:** Task 7.

### Working in parallel

Two or more Claude threads can work at once if they don't edit the same files. Rules:

- **One thread per task, and one task per thread at a time.** Claim a task by setting its status to `DOING (thread name)` in its section and in the list above. Don't start a task another thread has claimed.
- **File ownership.** Each task lists the files it may change. Stay inside them. Read anything.
- **The main thread owns** `STANDARD.md`, `schema/`, `PROPOSAL.md` and `planning/plan.md`. Another thread that needs a change there writes the proposal in its own task section, and the main thread makes it.
- **The board.** Each thread edits only its own task sections and their lines in the list above. Record findings there.
- **`lib/`:** a thread may add new modules and tests. Only one thread at a time changes an existing module: `check.py` is Task 17's while it's `DOING`, and `data.py` is Task 19's.
- **Shared checkout:** threads share this repo's working tree. Stage only the files you changed (`git add <path>`, never `git add -A` or `git commit -a`), and check `git diff --cached` before committing, so you never commit another thread's unfinished edits.
- **Commits:** commit locally, in small commits, with the task number in the message. Run `pytest` in this repo before committing here. **Don't push** anything; Allen checks before anything goes public.
- **Environment:** the `CultureWar` conda env has everything except R, DuckDB and Polars, which are in `pdt-xlang`. Use the scratchpad for temporary files, never `/tmp` directly.
- **Web:** if a site returns 403, try a headless browser (Playwright, in the CultureWar env). Stop at a bot check and ask Allen.

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

**Status:** `DONE` (2026-11-19)

Published as the public repository https://github.com/AllenDowney/PublicDataToolkit, after the cleanup in Task 9. Comments on [`PROPOSAL.md`](PROPOSAL.md) go to its GitHub issues.

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

**Progress (2026-11-19), step 2, the GSS slice:** a new local repo, `pdt-gss`, next to this one; not pushed. It has 45 variables from release 7224r3a:
- design variables;
- the abortion battery (7) and the core spending battery (18), both complete;
- two ballot-split items (`natracey`, `natfarey`);
- the race items with corrections (`racopen`, `racfew`, `rachaf`, `racmost`, `racschol`);
- `grass` (marijuana, for the cross-survey topic query) and five others.

`build/build_slice.py` builds the records from gssrdoc (question text, value labels, years and ballots) and the Stata file (variable labels, and which missing codes occur), using only pandas' public API. Four corrections from gssrdoc issue #1 are in `corrections.jsonl`. `tests/check_metadata.py` runs C1, C2, C6, C7, C9 and C10, and all pass; C7 was confirmed to fail on a stale correction. The build runs C3–C5 against the data.

GSS terms, decided by Allen on 2026-11-19: everything `ship`. The 2024 R3a codebook grants MIT-style rights, provided NORC's notice is included (`pdt-gss/NOTICE.md`). The data goes in a GitHub release when `pdt-gss` is published.

Findings from the GSS slice:
- **gssrdoc doesn't match release 7224r3a.** Its 2024 counts differ from the data: `racopen` 462 vs 981, `grass` 867 vs 862. So gssrdoc was scraped from an earlier 2024 release. Ballots and years match exactly for every other variable.
- **Missing codes per variable come from the data.** gssrdoc lists the same twelve `NA(x)` codes for every variable. The data shows which occur: `.d`, `.i` and `.n` in 41 of 45 variables, `.s` in 32, `.y` in 8, and none of the others.
- **gssrdoc doubles every apostrophe** ("DON''T") in 239 variables. It's handled by a recorded parser rule rather than 239 corrections. STANDARD.md rule 3 should say that systemic source artifacts may be fixed by a named rule.
- **`.z` "see codebook" has no missing type,** but the data file says it's missing. The schema can't say "missing, reason unknown"; `other` is the closest. `unresolved` doesn't fit, because the kind is known.
- **The shared-stem rule for batteries is fragile.** `natrace` was left out until the rule accepted an item letter right after "?". The rule also merges the Y and Z wording versions, which NORC fields on different ballots, into one 26-item group, and it can't see the `racfew`/`rachaf`/`racmost` chain, which has no shared stem. The build writes a group only when all its members are in the slice, and reports partial ones.
- **gssrdoc has no yearly counts for weights,** so the build counted `wtssps`'s availability in the data and labeled that field `origin: data_file`.
- **Per-code provenance is bulky.** Every missing code repeats the same long origin. A default origin for missing codes per variable would shrink the records a lot, which matters for files LLMs read.
- **A possible documentation error, not verified:** the spending stem repeats a clause ("name some of these problems, and for each one I'd like you to name some of these problems…").
- **Only one extension so far:** `gss.modules`. Every slice variable is `Core`, so a module group would say nothing.

**Progress (2026-11-19), step 3, the ANES CDF slice:** a new local repo, `pdt-anes-cdf`, not pushed. It has 32 variables from the February 5, 2026 release:
- design variables;
- ten thermometers;
- ideology scales;
- abortion, gay-rights and death-penalty items;
- pre- and post-election vote items.

`build/build_slice.py` parses the HTML codebook's Valid, Missing, Sources and Notes sections, with block regexes taken from ExtractANES. Unlike the old script, it keeps the codebook's own valid/missing split, types each missing code, and doesn't compute a valid range from listed codes. The Stata file is read only through pandas' public API. The same `check_metadata.py` passes, with no extensions needed.

ANES terms, decided by Allen on 2026-11-19: everything `ship`. electionstudies.org is behind a Cloudflare bot check, so neither the agent nor a headless browser could read the terms (an archive.org request was blocked as a way around the check). Allen saved the three pages from a browser; they're kept in `pdt-anes-cdf/data/raw/terms/` and recorded as source `anes-terms-pages`. They say:
- use the data only for research or statistical purposes, make no use of respondents' identities, and cite ANES;
- public release datasets are "public goods," and derived datasets may be shared with a link back to the original;
- no login is needed any more.

They don't address mirroring the original files or LLM processing; Allen decided both may ship. The README links back to the original dataset, as the FAQ asks.

**For the instructions:** when a publisher's site blocks scripts, the agent asks the person to save the terms pages from a browser, stores them in `data/raw/terms/`, records them as a source, and quotes them in `dataset.yaml`. That worked here, and it keeps the evidence for each terms decision.

Findings from the ANES slice:
- **The checks against the data find codebook errors:**
  - VCF0878 (gays adopting) has 1,130 cases of code 2, which the codebook doesn't list, and 2016 has data but is missing from its Sources. It looks like 2016 was coded 1/2 instead of 1/5; CultureWar's `harmonize_vcf0878_adopt` recodes 5 to 2 for the same reason.
  - VCF0704 (presidential vote) has 2016 data, but 2016 is missing from its Sources.
  - VCF0104 and VCF0301 have 1954 data that isn't in their Sources; VCF0830 has 2012 data that isn't.
  - There are undocumented codes: `-1` in VCF0806 and VCF9236 (245 cases each), `-8` in VCF0218 and VCF0224, `-4` in VCF0206. They're marked `unresolved`.

  These are candidates for `corrections.jsonl` once checked against the PDF codebook and the ANES errata.
- **The standard fits without extensions.** Three wordings by year and mode (VCF0803), INAP as Stata's system missing (`.`), codes listed under Valid that look like DK (VCF0803 code 9, VCF0876 code 8), and ranges with labeled codes beyond them (thermometers 0–96 plus 97) all fit the schema.
- **Missing labels mix several reasons in one code** ("NA; no Post IW; form III,IV (1972)"). Splitting at ";" and typing each part works. Parts the rule can't type ("don't recognize", "breakoff", "'other' vote") are listed in the build report.
- **Pre/post phase is mostly not recorded.** Only one variable's notes say "This is a pre var." The rest is implied by labels ("no Post IW"), so `phase` is nearly empty.
- **No marijuana item in the CDF,** so the cross-survey topic query (spike step 5) needs another subject. Abortion, gay rights and the death penalty are in both the GSS and ANES slices.
- **No groups.** The CDF has 92 thermometers whose shared question text sits in a preamble before VCF0201, which the variable parser doesn't see. A `thermometer` scale signature, from the "Degrees" range, supports the structural query instead (`complete_by_rule`).
- **The shared library is overdue.** `check_metadata.py` was copied from `pdt-gss` into `pdt-anes-cdf`, which is exactly the drift between repos the plan warned about. It should move into `lib/` here before MTF.

**Progress (2026-11-19), the shared check:** `check_metadata.py` moved into the shared library, as `lib/pdt/check.py` with `pdt check` as the command. `pyproject.toml` packages it as `publicdatatoolkit` with `schema/` bundled, so there's one copy of the schemas.
- It implements C1, C2, C6, C7, C9, C10 and C11 (README sections and CLAUDE.md). C3–C5 still run in each repo's build, because they need the data and the code to read it; C8 waits for the views.
- Two hacks in the copied script were replaced: the regex scan for source ids and the count of unreviewed model output now walk the records.
- `lib/tests/test_check.py` has 14 tests: a small valid repo passes, and each check catches its own kind of breakage. All pass.
- Both dataset repos dropped their copy. Their `make check` runs `python -m pdt check .` against the toolkit checkout next to them, so nothing is installed into the conda env. Both pass, with the same reports as before.
- `schema/check_examples.py` uses the shared validators too.

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

## Task 11 — Data releases, download script and extract builder

**Status:** `TODO` — decided 2026-11-19

The workflow for someone who clones a dataset repo:
1. `make download` runs `scripts/download.py`. It fetches the data release, checks the SHA-256 sums in `sources.yaml`, and refuses to run until the user accepts the publisher's terms, as MarriageNSFG's script does.
2. `scripts/extract.py` builds the extract the user asks for: variables, years, and how to treat each missing type.

None of this exists yet for `pdt-gss` or `pdt-anes-cdf`.

**Decided (Allen, 2026-11-19):**
- **Extract builders live in dataset repos** (plan §10 item 5), rather than only in analysis projects. To keep STANDARD.md's first principle, the builder's options encode no analysis choices; the user supplies them. The recoding by missing type lives in the shared library, so it behaves the same everywhere.
- **A data release holds the publisher's original files plus a common format (parquet) written by the build.** The library reads every dataset through the common format.

**Design out for review (2026-11-19):** [`planning/missing_codes_design.md`](planning/missing_codes_design.md) compares three layouts, and parquet against Arrow and CSV, measured on both slices. It recommends one parquet file with a `<name>__code` column next to each value column. Round trips back to the publisher's values are exact for both slices. Waiting for review before building.

**To design first:** how the common format keeps missing codes distinct. Stata's `.d`/`.i`/`.n` have no parquet equivalent, and the ANES stores missing codes as ordinary numbers. A code column next to each value column is one option. The same files could feed the data checks C3–C5 in `pdt check`, so they no longer have to run in each repo's build.

**Steps:**
1. Design the common format; add it to STANDARD.md and a schema if needed.
2. The library: read the common format; select; recode by missing type.
3. `download.py` and `extract.py` in the Copier template, and copies in `pdt-gss` and `pdt-anes-cdf`.
4. The first data releases, once the repos are pushed.

**Progress (2026-11-19):** Review 2 accepted Option A with five refinements; triage and decisions are in [`planning/review_2.md`](planning/review_2.md). All five are in the design doc and STANDARD.md §4.2, §8 and §10, and `dataset.schema.json` gained `column` and `codes` for dimensions.
- `lib/pdt/data.py` implements split, write, rebuild and recode. 10 tests, including metadata evolution; 24 library tests pass in all.
- `pdt check` rejects reserved names (`__code`, `_row`).
- **Cross-language:** both slices read identically in pandas, Polars, DuckDB, R arrow and R DuckDB, in a new conda env, `pdt-xlang`.
- **Full-file round trips:** the NSFG female respondent file (1,912 variables) is exact; the GSS and ANES results are in the design doc §9.
- A second-opinion review of `data.py` by an agent is in progress.

## Task 12 — Tables: several files in one release

**Status:** `DONE` (2026-11-19). Allen decided to add a table level; it's built, and first used for the NSFG

The standard identifies a variable by (release, name). An NSFG release has three files (female respondents, male respondents, pregnancies) that share names such as `MARSTAT`. A portal dataset's coded columns refer to other tables (Chicago crimes `iucr` → the IUCR code list). Both need a table level, which data-dict has (`tables`, `relationships`).

Likely shape: `metadata/releases/<release>/<table>/variables.jsonl`, a `table` field in records and in variable references, and optional relationships between tables. Background: [`planning/next_datasets.md`](planning/next_datasets.md) §1 and §3.

**Progress (2026-11-19):** implemented in the standard, the schemas and `pdt check`.
- **`dataset.yaml`:** a release may list `tables`, each with an id, label, sources, `key` columns, and `references` to other tables (foreign keys, possibly in another release or dataset).
- **Layout:** records go in `metadata/releases/<release>/<table>/variables.jsonl`. A release without tables keeps the old layout, so the three existing repos are unchanged.
- **Records** carry `table`. Variable references (group members, links, corrections, annotations, derived properties) may name one, and must when a name is in several tables of the release.
- **`pdt check`** enforces all of this: a record's table matches its directory, there are no ambiguous references, and keys and reference columns have records. Six new tests cover it, with 36 library tests passing.
- **The common format** has one parquet file per table.
- **First real use, the NSFG** (2026-11-19). `pdt-nsfg` now has three tables in release 2022-2023: female respondents (23 variables), male respondents (17) and pregnancies (12).
  - Keys: `CaseID`, and (`CaseID`, `PREGORDR`). The pregnancy → female reference is checked against the data: every pregnancy's `CaseID` is a female respondent, and male and female IDs never overlap.
  - `MARSTAT` and others appear in two tables without conflict. `pdt check` passes.
  - The male and pregnancy files round-trip exactly through the common format.
  - Findings:
    - The cycle 12 data is in `/NCHS/NSFG/` on the CDC FTP site, not `/Datasets/NSFG/`. The earlier `sources.yaml` URL was wrong.
    - The pregnancy data has a column `AGER` with no entry in the pregnancy codebook.
    - The male codebook carries NCHS's own correction in a margin box ("Corrected universe for MFLASTP"), and the universe field says only "see box to the right". The parser now keeps margin text and records it in the variable's notes, labeled.
    - Some pregnancy names are lowercase in the data (`agepreg`) but uppercase in the codebook.

## Task 13 — FARS slice

**Status:** `DOING` (main thread)

The non-survey case Allen chose. Allen downloaded the 2024 national CSV and SAS files, the auxiliary files, the Analytical User's Manual 1975–2024 (823 pages), and NHTSA's Q&A on the auxiliary files. They're in `../pdt-fars/data/raw/`; the manual's text is `data/interim/manual.txt`.

**What FARS tests:**
- **Tables:** 33 data files, keyed by `ST_CASE`, `VEH_NO` and `PER_NO`.
- **History across years:** the manual gives each element's codes as a matrix of year ranges. For example, `LGT_COND` code 9 is "Unknown" until 2017 and "Reported as Unknown" from 2018.
- **No questions:** it's a census, coded from police reports.
- **A second source for labels:** the CSV pairs most coded columns with a label column, e.g. `LGT_CONDNAME`.

**Progress (2026-11-19):** `build/build_slice.py` parses 432 elements and builds 32 variables in three tables (`accident`, `vehicle`, `person`). **The parser isn't right yet**:
- labels run on into the next element's title;
- code tables that continue onto the next page lose their codes, so the report's 220 "unresolved" codes, such as `STATE` 1–22, are artifacts;
- `WEATHER` finds no 2024 column.

The comparison of the manual's labels with the data's labels already works, and shows only small differences: dashes, case, "(Since 2011)". **Update (2026-11-19, later):** the parser is fixed, and the slice is committed locally in `pdt-fars`. `pdt check` passes.
- **Parser fixes:**
  - a table continued on the next page repeats its year header, and now continues the same block;
  - wrapped labels are recognized by indentation;
  - a discontinued element that shares a SAS name with the current one (`WEATHER`) no longer replaces it.
- **Codes:** 0 unresolved, down from 220. All of those were parser artifacts.
- **Labels:** compared with the CSV's label columns. After ignoring case, punctuation, year notes and added examples, 8 codes differ in wording. For example, `DR_DRINK` is "Drinking" in the manual and "Yes" in the data. For code 99, the manual's "Unknown/Reported as Unknown (Since 2018)" puts the year's change inside one label.
- **Tables and keys:** `accident`, `vehicle` and `person`, with keys and references checked against the data. Person → vehicle can't be declared: 9,020 non-motorists have `VEH_NO` 0, and 426 occupants of parked or working vehicles refer to the PARKWORK file. That's a conditional reference, which the standard can't express (Task 25).
- **Common format:** all three full tables round-trip exactly; CSV is the third source format, after Stata and SAS.
- **Still open:** terms (Allen); only the 2024 column of each element's year-range matrix is used. A second year (2017, before the 2018 code changes) would test release comparison.

**Terms:** NHTSA's manual has a disclaimer, no license, and "available to the public"; it's a US government work. Allen decided on 2026-11-19: everything `ship`.

**Files:** `../pdt-fars/` only.

## Task 14 — Agent views: `agent/` index and shards

**Status:** `DONE` (views thread, 2026-11-19; not pushed)

Build the LLM-facing view from STANDARD.md §7 in a new library module. It generates, for a dataset repo:
- `agent/index.md`;
- shards by group, by table and by scale signature, each under about 20k tokens, in two forms: JSONL, and one line per variable for reading;
- corrections applied and marked.

Search results label themselves `complete`, `complete_by_rule` or `approximate`, by the rules in §7. Spike step 5 needs this.

**Files:** new `lib/pdt/views.py` (or `lib/pdt/agent.py`), `lib/tests/test_views.py`, and `agent/` in the dataset repos (generated). A `make views` target in each dataset repo's Makefile.

**Done when:** the four dataset repos have `agent/`, the tests pass, and an agent given only `agent/` can find every GSS abortion item and say the answer is `complete`.

**Progress (2026-11-19, views thread):**
- **Built.** [`lib/pdt/views.py`](lib/pdt/views.py) writes `agent/`: `index.md`, `SKILL.md`, `manifest.json`, and shards by release/table, group, publisher subject, scale signature and topic annotation. Each shard comes as `.txt` (one line per variable) and `.jsonl` (corrected records with a `view` block), and is split into parts above about 20k tokens. [`lib/pdt/search.py`](lib/pdt/search.py) holds the filter language and assigns the completeness label. Every shard is a filter result, and a test reruns each shard's filter. CLI: `pdt views [PATH]` and `pdt search PATH --filter JSON`. Tests: [`lib/tests/test_views.py`](lib/tests/test_views.py).
- **All four dataset repos** have `make views` and a generated `agent/`, and `pdt check` passes in each.
- **Blind test passed.** A fresh agent given only a copy of `pdt-gss/agent/` found the 7 abortion items, labeled the list `complete` with respect to NORC's subject list and the 50 variables in scope, and read about 3,000 tokens. It went SKILL.md → index.md → `shards/subject/abortion.txt`.
- **Fixed from the blind test.** The agent read the gap in `1972-1985,1987-2024` as "no survey in 1986". The index now lists each release's waves and says that a gap means the variable wasn't available in those waves.

**Decisions and findings:**
- **Publisher subjects are groups** (Task 25 decision, f3d70d9). The `subject` filter and subject shards use groups of kind `subject`, and topic annotations are always `approximate`.
- **JSONL header:** the first line is `{"shard": {...}}`, and `agent/manifest.json` holds the input hash (now in §7). `views.is_current(root)` is ready for C8 when Task 17 wants it.
- **Size:** JSONL costs about 1,200 tokens per GSS variable (availability 36%, provenance and origins 36%). The line form costs about 60. Recorded as open in Task 25.
- **Non-surveys:** FARS has no question text, so the line form falls back to `notes`, marked `[notes]`. If Task 25 adds a definition field, the line form should use it.
- **Redundant shards:** in the GSS slice, `subject-abortion` and `battery-abdefect` have the same members, labeled `complete` and `complete_by_rule`. SKILL.md says to cite the one with the better label.
- **`cli.py` is shared:** Tasks 15 and 16 will add subcommands too, so whoever goes next should check for conflicts there.

**After the Task 25 answers (a995a31):**
- **Compact JSONL** (§7). `availability` maps each form, or `all`, to runs of waves, and `n` is dropped. `origins` gives each field's origin as a short string, and `origins.codes` holds the origin the codes share; a code without its own origin falls back to `provenance.codes`. Each shard header's `full_records` names the canonical files in `metadata/`. The GSS cost fell from about 1,200 to about 480 tokens per variable (all 50: 61k to 24k; Abortion: 8.4k to 3.3k).
- **Line form** uses question text, else `[description]`, else `[notes]`.
- **SKILL.md** now uses §7's wording: when two filters return the same set, report the stronger label.

## Task 15 — Human-readable site: `docs/`

**Status:** `TODO` — ready for a second thread

A static site per dataset repo, from STANDARD.md §7: a page per variable, per group and per release, with codes, missing types, availability, corrections and provenance. MkDocs is the suggested generator. The site goes in `docs/`, so GitHub Pages can serve it.

**Files:** new `lib/pdt/site.py` and its tests; `docs/` in the dataset repos (generated).

**Done when:** `make views` writes a browsable site for `pdt-gss` that a person can use to look up `abany` and see its wording, codes, years and ballots.

## Task 16 — Export data-dict YAML

**Status:** `TODO` — ready for a second thread

Export one `data-dict.yaml` per release (per table, for releases with tables), following the mapping in [`planning/data_dict.md`](planning/data_dict.md) §2, and validate it with data-dict's own CLI (`uvx data-dict validate-spec`). Record what the export loses, as evidence for the conversation with Hadley (Task 6).

**Files:** new `lib/pdt/export.py` and its tests; `export/data-dict/` in the dataset repos (generated); notes in this task's section.

## Task 17 — Data checks C3–C5 in `pdt check`

**Status:** `TODO` — ready for a second thread

Move the data checks out of each repo's build and into `pdt check`, reading the common-format parquet files:
- **C3 coverage:** every data column has a record, and every record a column.
- **C4 codes:** every code in the data is documented.
- **C5 availability:** waves and forms match the data, using the dimension columns in `dataset.yaml`.

They're skipped, with a notice, when the parquet files are absent.

**Files:** `lib/pdt/check.py` (owned by this task while `DOING`) and its tests. Each dataset repo needs a step that writes its parquet files with `pdt.data`; coordinate with Task 18.

## Task 18 — `download.py` and the data release

**Status:** `TODO` — ready for a second thread

Part of Task 11. A standard `scripts/download.py` for dataset repos:
- it reads `sources.yaml`;
- fetches automated sources, and explains the manual ones;
- checks the SHA-256 sums;
- has a `--check` mode;
- refuses to run until the user accepts the publisher's terms, as MarriageNSFG's script does.

Also a build step that writes the common-format parquet files for a data release. Start with `pdt-nsfg`, where every source can be downloaded. **Don't create GitHub releases**; Allen does that when the repos are published.

**Files:** new code in `lib/pdt/` (e.g. `download.py`), `scripts/` and `Makefile` in the dataset repos. Later, `templates/` for Copier (Task 8).

## Task 19 — `extract.py`, the extract builder

**Status:** `TODO` — ready for a second thread

Part of Task 11. `scripts/extract.py` in a dataset repo: the user names the variables, waves and how to treat each missing type, and gets an extract, with no analysis choices built in. It uses `pdt.data.recode`. Test it by rebuilding a CultureWar GSS extract column and comparing.

**Files:** `lib/pdt/data.py` (owned by this task while `DOING`), new `lib/pdt/extract.py`, tests, `scripts/` in the dataset repos.

## Task 20 — ANES codebook errors

**Status:** `TODO` — ready for a second thread

The ANES build found likely errors (Task 5, step 3):
- VCF0878 is coded 1/2 in 2016 rather than 1/5, and 2016 is missing from its Sources;
- VCF0704's Sources omit 2016;
- some Sources omit 1954 or 2012;
- there are undocumented codes: `-1` (VCF0806, VCF9236), `-8` and `-4`.

Check each one against the PDF codebook (`../pdt-anes-cdf/data/raw/`) and ANES's "Data Alerts" (a person may need to open the page). Record the confirmed ones in `metadata/corrections.jsonl` with evidence, and draft a report to anes-project@umich.edu for Allen to send.

**Files:** `../pdt-anes-cdf/` only; the draft goes in this task's section or a new `planning/` file.

## Task 21 — GSS follow-ups

**Status:** `TODO` — ready for a second thread

- **The 39 missing variables:** release 7224r3a has 6,943 variables, and gssrdoc 6,904. Find the 39 and decide how to document them, perhaps from the NORC PDF codebook.
- **Pin gssrdoc,** or decide to build from NORC sources (plan §10 item 3; ask Allen).
- **Links between releases:** parse the "What's New" and Release Variables PDFs (in CultureWar's `data/raw/`) to build `links.jsonl` between 7224r3 and 7224r3a.

**Files:** `../pdt-gss/` only.

## Task 22 — NSFG question text and earlier cycles

**Status:** `TODO` — ready for a second thread

- **Question text:** the codebooks give item references ("AD-7b") but no wording. Find the CAPI questionnaire documents on the CDC site, and add `questions` to records by item reference.
- **Earlier cycles:** add 2017–2019 as a second release (data and download code in MarriageNSFG; codebooks from CDC), and link items across cycles.

**Files:** `../pdt-nsfg/` only.

## Task 23 — Answer keys for the topic and structural queries

**Status:** `TODO` — ready for a second thread

Spike step 5. Before any search tool exists, build by hand:
- the **religion answer key** across the GSS, ANES and NSFG slices, and the full files where practical: every variable about religious affiliation, attendance, importance or belief;
- one **structural query** with its exact answer, e.g. every GSS item on ballot A in 1988 within the slice.

Then a scoring script for recall, precision and tokens read. Write the protocol before running any agent, as the earlier plan's §7.5 says. CultureWar's `notebooks/inventories/` are a starting point.

**Files:** new `eval/` in this repo.

## Task 24 — Agent instructions and skills

**Status:** `TODO` — ready for a second thread

Write `instructions/` (the eight-step procedure in plan §5) and the first skills in plan §6, using what the four slices taught. Examples:
- probe a PDF before parsing it;
- watch for page-break headers and margin boxes;
- check every source against the data;
- save the terms pages when a site blocks scripts.

Each step should say what to check before moving on.

**Files:** new `instructions/` and `skills/` in this repo.

## Task 25 — Standard changes from the findings

**Status:** `DONE` (2026-11-19) — main thread

Findings that need a decision or a change to STANDARD.md and the schemas:
- **A definition field:** FARS and data-dict both have one; FARS definitions are in `notes` for now.
- **Variable type** (raw, recode, computed, imputation flag), now the NSFG extension `nsfg.variable_type`.
- **Publisher corrections printed in the documentation,** such as NSFG's margin box.
- **Missing types for non-surveys:** "Unknown" in a police report isn't "don't know".
- **"Missing, reason unknown":** GSS `.z`.
- **Rules for release ids.**
- **The size of per-code provenance.**
- **Systemic source artifacts fixed by a named rule:** gssrdoc's doubled apostrophes.
- **Conditional references between tables:** a FARS person's `VEH_NO` refers to a vehicle in transport, a parked vehicle, or nothing (non-motorists).
- **Histories inside one label:** FARS writes "Unknown/Reported as Unknown (Since 2018)" for a code whose meaning changed. The record for a single year should probably say only what that year means.

**Files:** `STANDARD.md`, `schema/`, and the `lib/` code that enforces them.

**Decided (2026-11-19):**
- **Publisher subject lists are groups,** of kind `subject` (STANDARD.md §5.1). Proposed by the views thread (Task 14), with Allen's approval of the direction. The main thread chose groups over "complete-capable annotations", so the rule stays simple: annotations never support completeness, and publisher groups can. `pdt-gss` now emits gssrdoc's subjects as `subject` groups instead of annotations.
- **Headers for generated JSONL** (§7): the first line is a `{"shard": {...}}` object, and `agent/manifest.json` holds the input hashes. This was the views thread's convention.
- **The rest, decided 2026-11-19.** Allen chose the first three; the main thread decided the others. All are in STANDARD.md, the schemas, `pdt check` (68 library tests) and the dataset repos.
  - **Missing types:** new `unknown`, for administrative and coded data such as FARS's "Reported as Unknown", and `unspecified`, for codes marked missing without a reason, such as GSS `.z`. The FARS and GSS rules went to version 0.2.
  - **Corrections the publisher prints** go in the field, with the superseded text in `notes`: NSFG `MFLASTP`'s universe.
  - **Conditional references:** a reference may have `when: {column, in}`. FARS declares person → vehicle when `PER_TYP` is 1, 2 or 9; that holds for all 78,880 such rows.
  - **`description`** holds the publisher's definition (FARS).
  - **`variable_type`:** response, recode, computed, imputation_flag, weight, design, administrative or other. The NSFG maps its types by the rule `nsfg_variable_type`, and the extension is gone.
  - **Release ids** use the publisher's own name for the release, lowercased; otherwise the date (`YYYYMMDD`).
  - **Systemic source artifacts** may be fixed by a named, versioned rule (rule 3).
  - **`provenance.codes`** is a default origin for a record's missing codes; `pdt check` requires that each code has one or the other. The GSS uses it, and its records are 13% smaller.
  - **One release's labels:** a record uses the release-specific label when a source gives one. FARS now takes labels from the 2024 CSV.
  - **Views thread's questions:**
    - shards may use a compact JSONL form, while `metadata/` stays canonical;
    - `description` exists now, so the line form can use it;
    - when two filters return the same set, report the stronger label (§7).


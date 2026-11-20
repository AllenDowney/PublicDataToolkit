# PublicDataToolkit Project Board

One short block per task, numbered for good. The board is short on purpose: each task's description, progress, findings and decisions are in its own file, `planning/tasks/task-NN.md`, linked from its block. Add new tasks at the end.

**Status:** `TODO` | `DOING (thread)` | `DONE (thread)` | `WITHDRAWN`

## Tasks

### Task 1 — Write the plan

`DOING`. The plan, in [`planning/plan.md`](planning/plan.md). Remaining decisions are in §10. Details: [`planning/tasks/task-01.md`](planning/tasks/task-01.md).

### Task 2 — Recover the earlier planning session

`DONE`. Found the earlier design (CultureWar Task 186) and copied it to `planning/`. Details: [`planning/tasks/task-02.md`](planning/tasks/task-02.md).

### Task 3 — Inventory the GSS and ANES work in CultureWar

`DONE`. Inventory of the GSS, ANES and NSFG work: [`planning/inventory.md`](planning/inventory.md). Details: [`planning/tasks/task-03.md`](planning/tasks/task-03.md).

### Task 4 — Publish the repo on GitHub

`DONE`. Published https://github.com/AllenDowney/PublicDataToolkit. Details: [`planning/tasks/task-04.md`](planning/tasks/task-04.md).

### Task 5 — snake_case spike

`DOING`. The snake_case spike: GSS, ANES, NSFG and FARS slices built. MTF waits for ICPSR's answer about LLM use. Details: [`planning/tasks/task-05.md`](planning/tasks/task-05.md).

### Task 6 — Talk to Hadley Wickham about data-dict

`DOING`. Talk to Hadley Wickham about data-dict. The note, with the export's evidence: [`planning/data_dict.md`](planning/data_dict.md). Details: [`planning/tasks/task-06.md`](planning/tasks/task-06.md).

### Task 7 — Withdrawn

`WITHDRAWN`. Out of scope for this repo. Details: [`planning/tasks/task-07.md`](planning/tasks/task-07.md).

### Task 8 — Versions, layout and names for dataset repos

`DONE`. Versions, layout and names: [`planning/versions_layout_names.md`](planning/versions_layout_names.md). Details: [`planning/tasks/task-08.md`](planning/tasks/task-08.md).

### Task 9 — Remove private information so the repo can be public

`DONE`. Removed private information before publishing. Details: [`planning/tasks/task-09.md`](planning/tasks/task-09.md).

### Task 10 — Respond to review 1 of the proposal

`DONE`. First review of the proposal: [`planning/review_1.md`](planning/review_1.md). Details: [`planning/tasks/task-10.md`](planning/tasks/task-10.md).

### Task 11 — Data releases, download script and extract builder

`DONE`. Data releases and extracts: the common data format ([`planning/missing_codes_design.md`](planning/missing_codes_design.md)), `pdt download` and `pdt package` (Task 18), and `pdt.extract` (Task 19). Details: [`planning/tasks/task-11.md`](planning/tasks/task-11.md).

### Task 12 — Tables: several files in one release

`DONE`. Tables: several files in one release. Used by the NSFG and FARS. Details: [`planning/tasks/task-12.md`](planning/tasks/task-12.md).

### Task 13 — FARS slice

`DONE (fars)`. FARS: four tables, code histories, releases 2017 and 2024 compared on real data. Details: [`planning/tasks/task-13.md`](planning/tasks/task-13.md).

### Task 14 — Agent views: `agent/` index and shards

`DONE (views + site)`. Agent views (`agent/`), with `pdt search` and the `available` filter. Details: [`planning/tasks/task-14.md`](planning/tasks/task-14.md).

### Task 15 — Human-readable site: `docs/`

`DONE (views + site)`. Human-readable site (`docs/`), built by `make views`. Details: [`planning/tasks/task-15.md`](planning/tasks/task-15.md).

### Task 16 — Export data-dict YAML

`DONE (views + site)`. data-dict export (`export/data-dict/`), validated; what it loses is in the task file. Details: [`planning/tasks/task-16.md`](planning/tasks/task-16.md).

### Task 17 — Data checks C3–C5 in `pdt check`

`DONE (fars)`. Data checks in `pdt check`: C3–C5 and C12 (keys and references) against the data. Details: [`planning/tasks/task-17.md`](planning/tasks/task-17.md).

### Task 18 — `download.py` and the data release

`DONE (views + site)`. `pdt download`, the shared readers and `pdt package`; all four repos' data round-trip exactly and pass data-dict `validate-data`. Details: [`planning/tasks/task-18.md`](planning/tasks/task-18.md).

### Task 19 — `extract.py`, the extract builder

`DONE (nsfg)`. `pdt.extract` and `scripts/extract.py` in all four repos; reports inferred classifications; GSS columns identical to CultureWar's extract. Details: [`planning/tasks/task-19.md`](planning/tasks/task-19.md).

### Task 20 — ANES codebook errors

`DONE (anes-errata)`. ANES codebook errors: 11 corrections, report sent, all `filed`. Details: [`planning/tasks/task-20.md`](planning/tasks/task-20.md).

### Task 21 — GSS follow-ups

`DONE (gss)`. GSS: gssrdoc 0.9 pinned, release 7224r3 added, links from NORC's release notes. Details: [`planning/tasks/task-21.md`](planning/tasks/task-21.md).

### Task 22 — NSFG question text and earlier cycles

`DONE (nsfg)`. NSFG: question text for 2022-2023, release 2017-2019 added, 21 links (19 shared names unlinked, listed for a later pass). BABYSEX error reported to NCHS; corrections `filed`. Details: [`planning/tasks/task-22.md`](planning/tasks/task-22.md).

### Task 23 — Answer keys for the topic and structural queries

`DONE (eval)`. Answer keys and scoring. The topic-test rerun waits for the full GSS release (Task 26). Details: [`planning/tasks/task-23.md`](planning/tasks/task-23.md).

### Task 24 — Agent instructions and skills

`DONE (instructions)`. Agent instructions (`instructions/`) and build skills (`skills/`). Details: [`planning/tasks/task-24.md`](planning/tasks/task-24.md).

### Task 25 — Standard changes from the findings

`DONE`. Standard changes from the findings (main thread). Details: [`planning/tasks/task-25.md`](planning/tasks/task-25.md).

### Task 26 — The full GSS release

`DONE (blue)`. All of 7224r3 and 7224r3a in pdt-gss (6,942 + 6,943 records, 6,974 links), plus agent/ and export/. Details: [`planning/tasks/task-26.md`](planning/tasks/task-26.md).

### Task 27 — Shared derived rules in the library

`DONE (orange)`. Shared derived rules in `lib/pdt/derived.py`; fars, ANES and NSFG use it, and blue switches the GSS build when Task 26 ends. Details: [`planning/tasks/task-27.md`](planning/tasks/task-27.md).

### Task 28 — The Copier template for dataset repos

`DONE (instructions)`. The Copier template: `copier.yml` at the toolkit's root, `templates/template/`, tagged `v0.1.0` locally (not pushed); `copier copy` and `copier update` tested. Details: [`planning/tasks/task-28.md`](planning/tasks/task-28.md).

### Task 29 — A YRBSS slice

`DONE (purple)`. YRBSS combined datasets in `~/pdt-yrbss`: 29 variables in releases sadc-2021 and sadc-2023, which renumber every question; 28 links from CDC's Questionnaire Content document, 3 code histories, data round-trip exact, `pdt check` 0 failures; 7 proposals for the standard. Details: [`planning/tasks/task-29.md`](planning/tasks/task-29.md).

### Task 30 — A BRFSS slice

`DONE (green)`. CDC's BRFSS, 2011–2023, in `~/pdt-brfss`: 23 concepts, 295 records, 300 links (4 renames CDC states), 24 code histories by rule, data round-trip exact, `pdt check` 0 failures (2 unresolved codes, `_RACEGR2` "." in 2011–12); 7 proposals. Details: [`planning/tasks/task-30.md`](planning/tasks/task-30.md).

### Task 31 — Check C8

`DONE (red)`. `pdt check` C8 compares each generated view's manifest with the current records; every check in §9 is now implemented. Details: [`planning/tasks/task-31.md`](planning/tasks/task-31.md).

### Task 32 — A CPS-ASEC slice

`DONE (yellow)`. CPS ASEC 2019–2025 in `~/pdt-cps-asec`: 32 variables in household, family and person tables, 192 links by rule, data round-trip exact, `pdt check` 0 failures; terms decided by Allen (everything ships); 6 proposals, 4 adopted. Details: [`planning/tasks/task-32.md`](planning/tasks/task-32.md).

### Task 34 — release-diff

`DONE (red)`. `pdt diff` compares two releases' records and proposes links and histories for review; tested on FARS, NSFG and GSS pairs, with the `release-diff` skill. Details: [`planning/tasks/task-34.md`](planning/tasks/task-34.md).


### Task 33 — An open-portal dataset

`DONE (orange)`. Chicago's "Crimes - 2001 to Present" (Socrata) in `~/pdt-chicago-crimes`, a dated portal snapshot, 27 records, `pdt check` 0 failures; the `from-open-data-portal` skill; 8 proposals for the standard. Details: [`planning/tasks/task-33.md`](planning/tasks/task-33.md).
### Task 35 — Shared text comparison; NSFG links and code counts

`DONE (red)`. `pdt.compare` shared by `pdt diff` and NSFG's link rule 0.4 (17 links; the opposite-sex marital labels relinked by hand); NSFG `values[].n`, which `pdt diff` uses to tell codes with no cases from recodings. Details: [`planning/tasks/task-35.md`](planning/tasks/task-35.md).

### Task 36 — Non-survey data in the library

`DONE (orange)`. `data_waves`, dataset `kind`, `terms.notice` and live sources in `pdt check` and `pdt download`, applied to the five dataset repos; four need their views regenerated. Details: [`planning/tasks/task-36.md`](planning/tasks/task-36.md).
### Task 37 — Count test in the NSFG rule; occurring-codes field; Cases column

`DONE (red)`. NSFG rule 0.5 with the count test (18 links, every rule link agreeing with `pdt diff`); `lists_only_occurring_codes` on NSFG's codebooks, read by `pdt diff` and the rule; a Cases column on the site. Details: [`planning/tasks/task-37.md`](planning/tasks/task-37.md).

### Task 38 — Code lists as tables, and retired codes

`DONE (orange)`. A design, accepted: [`planning/code_lists_design.md`](planning/code_lists_design.md); implemented in Task 41. Details: [`planning/tasks/task-38.md`](planning/tasks/task-38.md).

### Task 39 — Library changes from the YRBSS findings

`DONE (purple)`. `valid_labels` without labels, `pdt.readers.read_sas_input`, a C2 warning on names reused across releases, C12 with `target_columns` (CPS: 35 references pass), `not_asked_from_availability` in recode and extract, and `design` in pdt-yrbss. Details: [`planning/tasks/task-39.md`](planning/tasks/task-39.md).
### Task 40 — `pdt diff` pairs by links first

`DONE (red)`. `pdt diff` pairs by links first (YRBSS's renumbering: 28 of 28 by link, 7 name conflicts flagged), compares valid ranges (CPS FPOVCUT) and question numbers. Details: [`planning/tasks/task-40.md`](planning/tasks/task-40.md).

### Task 41 — Shared code lists

`DONE (orange)`. Shared code lists (`metadata/code_lists.jsonl`, §4.5) and retired codes in the standard, the library and pdt-chicago-crimes (IUCR, 434 codes, 10 retired); the GSS lists follow when blue frees pdt-gss. Details: [`planning/tasks/task-41.md`](planning/tasks/task-41.md).
### Task 42 — A cross-dataset catalog

`DONE (red)`. `pdt catalog` (in `~/pdt-catalog`: 6 datasets, 7,485 variables; CPS and Chicago left out for `terms.metadata: unknown`) and `pdt search --catalog`; tested on sadness, marital status and age at first marriage. Details: [`planning/tasks/task-42.md`](planning/tasks/task-42.md).

### Task 43 — The older repos and the new fields

`DONE (yellow)`. `questions[].number`, `flag_for` and `design` in pdt-nsfg, pdt-cps-asec and pdt-anes-cdf; pdt-fars needed nothing; notes to blue and purple. Details: [`planning/tasks/task-43.md`](planning/tasks/task-43.md).
### Task 44 — One line per variable across releases

`DONE (red)`. `pdt.chains`: one line per variable across releases in the catalog (8 datasets, 7,804 lines → 7,301; BRFSS 295 → 76, CPS 287 → 44) and in each repo's `agent/variables.txt`; a change of meaning keeps lines apart, marked ↳. Details: [`planning/tasks/task-44.md`](planning/tasks/task-44.md).

### Task 45 — A PISA slice

`DONE (purple)`. PISA 2012–2022 student files in `~/pdt-pisa`: 415 records, replicate weights in `design`, `plausible_values` groups, four countries kept by `data_rows`, 2012–2018 question text from NCES's US versions, ESCS linked as `rescaled`; `pdt check` 0 failures. Library: `read_sav`, LENGTH in `read_sas_input`, `data_rows` in C3/C5. Details: [`planning/tasks/task-45.md`](planning/tasks/task-45.md).

### Task 46 — Who made the hand facts

`DONE (orange)`. 599 hand facts named Allen but were agents'; every repo now names the real author (Allen keeps only GSS `partyid` and the 4 carried-over GSS corrections), and the template starts with `author:` empty. [`planning/attribution_audit.md`](planning/attribution_audit.md). Details: [`planning/tasks/task-46.md`](planning/tasks/task-46.md).
### Task 47 — Large sites: docs/ built for Pages

`DONE (red)`. C8 checks `docs/` only where it exists (and says when it's gitignored); a Pages workflow in the template builds `docs/` at the repo's toolkit tag without data (checked locally); a proposal to cut the GSS site from 14,546 files to about 7,000 with one page per variable across releases. Details: [`planning/tasks/task-47.md`](planning/tasks/task-47.md).

### Task 48 — What the codebooks trip over

`DONE (yellow)`. The failure modes met parsing publishers' documentation in eight datasets, by format, with examples, detection and fixes, for data-dict item 8: [`planning/codebook_failure_modes.md`](planning/codebook_failure_modes.md). Details: [`planning/tasks/task-48.md`](planning/tasks/task-48.md).
### Task 49 — One site page per variable; a `data` extra

`DONE (red)`. One site page per variable across releases (GSS 14,546 files → 7,605, 87 → 51 MB; BRFSS 295 variable pages → 65); `publicdatatoolkit[data]` for pandas, numpy and pyarrow, so `pdt views` and `pdt check` run on the base install. Details: [`planning/tasks/task-49.md`](planning/tasks/task-49.md).

### Task 50 — An NHIS slice

`DONE (yellow)`. The National Health Interview Survey (NCHS, adults) in `~/pdt-nhis`, 2016–2024: 231 records and 170 links, four of them stated by NCHS (three across the 2019 redesign); `pdt check` 0 failures. Terms: everything ships, as for the NSFG (Allen, 2026-11-20). Findings and proposals: [`planning/tasks/task-50.md`](planning/tasks/task-50.md).

### Task 52 — Pre-publish review

`DONE (red)`. Read only. Toolkit: clean except §5's history (a verified rewrite plan); 7 dataset repos ready, nsfg after a terms confirmation, brfss and nhis not yet; commands in order. [`planning/publish_checklist.md`](planning/publish_checklist.md). Details: [`planning/tasks/task-52.md`](planning/tasks/task-52.md).

### Task 53 — Search fixes from the full-GSS eval

`DONE (blue)`. `pdt search` defaults to the current release, with `--names` and paging; catalog search returns and filters waves; SKILL.md points agents to exact searches first. Reruns: ballot A 1988 and catalog sadness recall 1.0; religion 0.86 and 0.18. Details: [`planning/tasks/task-53.md`](planning/tasks/task-53.md).
### Task 54 — Comparing releases: ignored markers, across tables, over gaps

`DONE (red)`. `pdt diff --ignore` (NHIS's "* ": the three variables now agree with their links), across tables (samadult → adult, merges by `--table-map`) and `--gaps` (14 NHIS gap pairs, all agreeing with the links). Details: [`planning/tasks/task-54.md`](planning/tasks/task-54.md).

### Task 55 — A Household Pulse Survey slice

`DOING (purple)`. Census's Household Pulse Survey (weekly and biweekly, 2020–2024, questionnaire changing by phase) in `~/pdt-pulse`: demographics, anxiety and depression, food sufficiency, weights and replicate weights, in every wave they appear. Details: [`planning/tasks/task-55.md`](planning/tasks/task-55.md).











## Working in parallel

Several Claude threads work at once. The coordinator is the thread named **"main: standard + FARS"**. It assigns tasks, decides questions about the standard (or takes them to Allen), and owns `STANDARD.md`, `schema/`, `PROPOSAL.md`, `planning/plan.md` and this board's structure.

- **Claim a task** by changing its status to `DOING (thread name)`. Work on one task at a time.
- **Write details in the task's file,** `planning/tasks/task-NN.md`: progress, findings, proposals. On the board, change only your task's block, and keep it to a sentence or two.
- **Stay in your task's files.** Each task file lists the files it may change. Read anything.
- **The shared checkout:** threads share this repo's working tree. Stage only the files you changed (`git add <path>`, never `git add -A` or `git commit -a`), commit with `git commit -- <paths>` so entries other threads staged stay out of your commit, and check `git diff --cached` first. **But** `git commit -- <path>` commits the whole working copy of that path: for a file others edit too (this board), stage only your own change through the index (`git add -p`, or apply it to the HEAD version) and run a plain `git commit`. and never write a shared file you haven't read in full. If a shared file looks wrong, restore it from git; don't rewrite it.
- **`lib/`:** add new modules freely. Only one thread at a time changes an existing module.
- **Commit locally** with the task number in the message, run `pytest` here first, and **don't push**. Allen checks before anything goes public.
- **Report** to the coordinator with SendMessage (find it with ListAgents): questions, proposals for the standard, record changes that need the views regenerated, and a short report when a task is done.
- **Drafts of emails** go outside every repo (`~/pdt-private/`). **The web:** on a 403, try a headless browser, and stop at a bot check.
- **Environment:** the `CultureWar` conda env; R, DuckDB and Polars are in `pdt-xlang`.
- **Memory cap:** the machine has 31 GB, shared by every thread, and two uncapped jobs crashed all sessions on 2026-11-20 (the full-GSS `make data`, 13–15 GB each). Run anything that reads data or runs for long (`make data`, `make build`, `make check` on data, `pdt package`, readers, eval runs) under a cap: `systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 --quiet <command>`. A job over the cap is killed by itself, exit 137; then make it use less memory (read columns or rows in batches), don't raise the cap. Don't run `make data` on the full pdt-gss until the reader works in batches (Task 58).

### Task 56 — An ATUS slice

`DOING (yellow)`. The American Time Use Survey (BLS) in `~/pdt-atus`, 2003–2025: 641 records in four tables, the activity lexicon as three code lists, `pdt check` 0 failures; terms: everything ships (Allen, 2026-11-20). Proposals P1–P4 accepted and built (library: `pdt.design`, C2 checks for `code_of` and replicate tables, view links; pdt-atus uses them, with seven single-year lexicons harmonized); P5 declined. Waiting on batched `make data` for the activity and summary tables (Task 58). Details: [`planning/tasks/task-56.md`](planning/tasks/task-56.md).

### Task 57 — Design: topic annotation vs. belief-module groups

`DOING (blue)`. A design for the §7.5 comparison: a religion topic annotation versus belief-module groups, and how to measure each with the eval. Design only, until the coordinator has read it. Details: [`planning/tasks/task-57.md`](planning/tasks/task-57.md).

### Task 58 — Data builds that fit in memory

`DOING (orange)`. The full-GSS `make data` loads 6,943 columns × 75,000 rows as one pandas object frame (`pdt.readers.read_stata`, then `pdt.data.split` and `write_release`), and needs 13–15 GB; it crashed every session twice on 2026-11-20. Read, split, write and round-trip check in column batches (a few hundred columns), building the parquet file with pyarrow, so peak memory stays under about 3 GB for the full GSS; the same for the other readers where it's easy. Measure the peak (`/usr/bin/time -v`) under the memory cap, and add a test that the build is batched. Then rerun the GSS rebuild. Details: [`planning/tasks/task-58.md`](planning/tasks/task-58.md).

### Task 59 — A Cooperative Election Study slice

`DOING (red)`. The CES (Harvard Dataverse) in `~/pdt-ces`: the cumulative common-content file and two or three yearly files, linked by `derived_from` where the guide documents it, a second cumulative↔yearly case after the ANES. Record the Dataverse license and leave the terms for Allen. Memory cap applies. Take the next task file, `planning/tasks/task-59.md`, when you claim it.

### Task 60 — An NSDUH slice

`DONE (blue)`; terms pending Allen. NSDUH 2023–2025 public use files in `~/pdt-nsduh`: 43–47 variables per year (design, substance use, mental health), 86 links from SAMHSA's comparability chart; codebook counts match the data exactly; `pdt check` 0 failures. Details: [`planning/tasks/task-60.md`](planning/tasks/task-60.md).

### Task 61 — An NHANES slice

`DONE (blue)`; terms pending Allen. NHANES 2015-2016, 2017-March 2020 and 2021-2023 in `~/pdt-nhanes`: demographics, PHQ-9, body measures and glycohemoglobin as tables on SEQN (213 records); codebooks match the data exactly; keys and references hold; `pdt check` 0 failures. Details: [`planning/tasks/task-61.md`](planning/tasks/task-61.md).

### Task 62 — An NCVS slice, metadata only

`DOING (blue)`. The National Crime Victimization Survey (BJS, through ICPSR/NACJD) in `~/pdt-ncvs`, metadata only and unpublished. 2022 built from ICPSR's codebooks: four linked tables, 2146 records; checked against the Stata files (C3–C5 clean, keys unique, one inferred correction); `pdt check` passes. Details: [`planning/tasks/task-62.md`](planning/tasks/task-62.md).

### Task 63 — A HINTS slice

`DOING (blue)`. The Health Information National Trends Survey (NCI) in `~/pdt-hints`: HINTS 5 Cycle 4, 6 and 7, every variable (1,380 records), checked against the Stata files, with the JK1 replicate design; `pdt check` passes. No login is needed to download. Terms are quoted for Allen and all `unknown`. Details: [`planning/tasks/task-63.md`](planning/tasks/task-63.md).

### Task 64 — A MEPS slice

`DONE (blue)`; terms pending Allen. MEPS-HC 2022–2024 in `~/pdt-meps`: consolidated (37 variables) and office-based visit files as tables on DUPERSID (247 records), reserved codes from AHRQ's tables, 164 links by AHRQ's naming convention; codebooks match the data; `pdt check` 0 failures. Details: [`planning/tasks/task-64.md`](planning/tasks/task-64.md).

### Task 65 — An NLSY slice

`DONE (yellow)`; terms pending Allen. NLSY97 1997–2023 (21 rounds) in `~/pdt-nlsy97`: 25 questions, one record per question across rounds (`source_columns`), long `person_year` table (188,664 rows) checked both ways against the wide file; `pdt check` 0 failures. Findings and proposals: [`planning/tasks/task-65.md`](planning/tasks/task-65.md).

### Task 66 — Two data-dict PRs: integer enums and typed missing codes

`DOING (red)`. Hadley offered to review a PR for data-dict#9. Clone tidyverse/data-dict locally, read its spec, validator and tests, and plan the PR(s) for integer enums with labels and typed missing codes, plus how our exporter would use them. Plan only; nothing forked, pushed or opened. Details: [`planning/tasks/task-66.md`](planning/tasks/task-66.md).


### Task 67 — Library and pdt-brfss use the Task 30 standard changes

`DONE (green)`. `pdt.ranges` (one valid range or a list) in check, diff, site, export and derived; `geography` in the `available` filter and the views; `values[].note` on site pages; a label lint under C6 (2 real hits, ATUS, fixed); `pdt.xport.read_sas_xport`; a `pdt search` bug fixed (`name` with `available` matched nothing). pdt-brfss uses all of them (ee3c818). Every repo's views need regenerating. Details: [`planning/tasks/task-67.md`](planning/tasks/task-67.md).

### Task 68 — `pdt export daaf`

`DOING (purple)`. A dataset repo as a DAAF data-source skill (`export/daaf/<domain>-data-source-<id>/`), refused unless the metadata and documentation ship and LLM processing is allowed. Design approved; prototype built and tested on pdt-nhis and pdt-gss; DAAF's lint passes. A load test inside DAAF waits for Allen. Details: [`planning/tasks/task-68.md`](planning/tasks/task-68.md).

### Task 69 — Panel responses spread across rounds (NLSY)

`DONE (yellow)`; the layer is designed, not built, waiting for the coordinator and Allen. In a panel like the NLSY, a given respondent isn't interviewed in every round, and many questions ask about the time "since the date of last interview", so the answer for a person at a given age, or about a given year, may be in any of several rounds. Investigate how NLS documents this and what practice it recommends, describe it in the metadata, and design (not yet build) a layer on top that answers "this question, for this person, at age A or in year Y". Details: [`planning/tasks/task-69.md`](planning/tasks/task-69.md).

### Task 70 — `pdt check` says which checks didn't run, and why

`DONE (purple)`. Each check, or part of one, that doesn't run is listed as "not run, because ..." (`Result.not_run`, printed by `pdt check`), not left silently absent: C5, C7, C8, C9, C10 and C12 when they don't apply, plus the data checks' existing skips. From DAAF's data-ingest agent ([`planning/daaf.md`](planning/daaf.md), step 3); the documented-frequency check is left for later. Details: [`planning/tasks/task-70.md`](planning/tasks/task-70.md).

### Task 71 — `pdt check` compares codebook counts with the data

`DONE (blue)`. C5 now also compares each code's `n` in `values`, and each wave's `n` in `availability`, with the data, at warn level. It honors `data_rows` and `data_waves`; counts it can't compare are listed as not run (Task 70). Run across 11 repos with data, with Task 58's round-trip gate bypassed in scratch: all match except one NLSY97 count off by 2. Details: [`planning/tasks/task-71.md`](planning/tasks/task-71.md).

### Task 72 — Make `pdt check` fast on the full GSS

`DONE (blue)`. Profiled on the full GSS: C1 resolved every schema `$ref` at each use, and C2's `Repo.resolve` scanned every record for each of 26,000 references. Schemas are now inlined once, and names indexed. Output is identical on four repos, and GSS takes 18–27 s, down from 76 s. The reported 40 minutes didn't reproduce. Details: [`planning/tasks/task-72.md`](planning/tasks/task-72.md).

### Task 74 — "About" and "Using this site" pages on every dataset site

`DOING (purple)`. site.py generates two pages for every dataset site, from the standard's vocabularies. About covers what the repository is and isn't, its three forms, the terms notice and citation, a link to the toolkit, and how to report errors. Using this site covers how to read a variable page, the missing types, completeness labels, lineages and availability, how to get and use the data and records, and agent/ with an LLM. The terms notice goes in every page's footer. Details: [`planning/tasks/task-74.md`](planning/tasks/task-74.md).

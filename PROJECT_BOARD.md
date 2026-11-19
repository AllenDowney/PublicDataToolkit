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

`DOING (gss)`. The full GSS release: all 6,943 variables. Details: [`planning/tasks/task-26.md`](planning/tasks/task-26.md).

### Task 27 — Shared derived rules in the library

`DONE (orange)`. Shared derived rules in `lib/pdt/derived.py`; fars, ANES and NSFG use it, and blue switches the GSS build when Task 26 ends. Details: [`planning/tasks/task-27.md`](planning/tasks/task-27.md).

### Task 28 — The Copier template for dataset repos

`DONE (instructions)`. The Copier template: `copier.yml` at the toolkit's root, `templates/template/`, tagged `v0.1.0` locally (not pushed); `copier copy` and `copier update` tested. Details: [`planning/tasks/task-28.md`](planning/tasks/task-28.md).

### Task 29 — A YRBSS slice

`DONE (purple)`. YRBSS combined datasets in `~/pdt-yrbss`: 29 variables in releases sadc-2021 and sadc-2023, which renumber every question; 28 links from CDC's Questionnaire Content document, 3 code histories, data round-trip exact, `pdt check` 0 failures; 7 proposals for the standard. Details: [`planning/tasks/task-29.md`](planning/tasks/task-29.md).

### Task 30 — A BRFSS slice

`DOING (brfss)`. A slice of CDC's Behavioral Risk Factor Surveillance System (adults, by state, 2011–2023) in `~/pdt-brfss`, built from the Copier template: about 25 variables from Twenge's *Generations*. Details: [`planning/tasks/task-30.md`](planning/tasks/task-30.md).
### Task 31 — Check C8

`DONE (red)`. `pdt check` C8 compares each generated view's manifest with the current records; every check in §9 is now implemented. Details: [`planning/tasks/task-31.md`](planning/tasks/task-31.md).

### Task 32 — A CPS-ASEC slice

`DONE (yellow)`. CPS ASEC 2019–2025 in `~/pdt-cps-asec`: 32 variables in household, family and person tables, 192 links by rule, data round-trip exact, `pdt check` 0 failures; terms wait for Allen; 6 proposals, 4 adopted. Details: [`planning/tasks/task-32.md`](planning/tasks/task-32.md).

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

`DOING (purple)`. Library changes from Task 29: `valid_labels` without labels, `read_sas_input`, a warning on name reuse across releases, `not_asked` from availability, and `design` in pdt-yrbss. Details: [`planning/tasks/task-39.md`](planning/tasks/task-39.md).
### Task 40 — `pdt diff` pairs by links first

`DONE (red)`. `pdt diff` pairs by links first (YRBSS's renumbering: 28 of 28 by link, 7 name conflicts flagged), compares valid ranges (CPS FPOVCUT) and question numbers. Details: [`planning/tasks/task-40.md`](planning/tasks/task-40.md).

### Task 41 — Shared code lists

`DOING (orange)`. Task 38's design: `metadata/code_lists.jsonl`, `retired` and `waves` on codes, in the standard, the library, pdt-chicago-crimes and (if blue is free) the GSS. Details: [`planning/tasks/task-41.md`](planning/tasks/task-41.md).
### Task 42 — A cross-dataset catalog

`DONE (red)`. `pdt catalog` (in `~/pdt-catalog`: 6 datasets, 7,485 variables; CPS and Chicago left out for `terms.metadata: unknown`) and `pdt search --catalog`; tested on sadness, marital status and age at first marriage. Details: [`planning/tasks/task-42.md`](planning/tasks/task-42.md).

### Task 43 — The older repos and the new fields

`DOING (yellow)`. `questions[].number`, `flag_for` and `design` in pdt-nsfg, pdt-cps-asec, pdt-anes-cdf and pdt-fars. Details: [`planning/tasks/task-43.md`](planning/tasks/task-43.md).
### Task 44 — One line per variable across releases

`DOING (red)`. The catalog, and the agent index where it fits, collapse a variable's lines across releases by its links (same item, renamed, relabeled), showing its names and release span; a change of meaning keeps lines apart but shows them together. Details: [`planning/tasks/task-44.md`](planning/tasks/task-44.md).






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

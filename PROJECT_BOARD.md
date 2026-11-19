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

`DOING`. Data releases and extracts. The common data format is done ([`planning/missing_codes_design.md`](planning/missing_codes_design.md)); the rest is Tasks 18 and 19. Details: [`planning/tasks/task-11.md`](planning/tasks/task-11.md).

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

`DONE (nsfg)`. NSFG: question text for 2022-2023, release 2017-2019 added, 21 links (19 shared names unlinked, listed for a later pass). The BABYSEX report to NCHS waits for Allen. Details: [`planning/tasks/task-22.md`](planning/tasks/task-22.md).

### Task 23 — Answer keys for the topic and structural queries

`DONE (eval)`. Answer keys and scoring. The topic-test rerun waits for the full GSS release (Task 26). Details: [`planning/tasks/task-23.md`](planning/tasks/task-23.md).

### Task 24 — Agent instructions and skills

`DONE (instructions)`. Agent instructions (`instructions/`) and build skills (`skills/`). Details: [`planning/tasks/task-24.md`](planning/tasks/task-24.md).

### Task 25 — Standard changes from the findings

`DONE`. Standard changes from the findings (main thread). Details: [`planning/tasks/task-25.md`](planning/tasks/task-25.md).

### Task 26 — The full GSS release

`DOING (gss)`. The full GSS release: all 6,943 variables. Details: [`planning/tasks/task-26.md`](planning/tasks/task-26.md).

### Task 27 — Shared derived rules in the library

`DOING (fars)`. Shared derived rules in `lib/pdt/derived.py`. Done except gss switching its build over. Details: [`planning/tasks/task-27.md`](planning/tasks/task-27.md).

### Task 28 — The Copier template for dataset repos

`DONE (instructions)`. The Copier template: `copier.yml` at the toolkit's root, `templates/template/`, tagged `v0.1.0` locally (not pushed); `copier copy` and `copier update` tested. Details: [`planning/tasks/task-28.md`](planning/tasks/task-28.md).

### Task 29 — A YRBSS slice

`DOING (yrbss)`. A slice of CDC's Youth Risk Behavior Survey (high school, 1991–2023) in `~/pdt-yrbss`, built from the Copier template: about 25 variables from Twenge's *Generations*. Details: [`planning/tasks/task-29.md`](planning/tasks/task-29.md).

### Task 30 — A BRFSS slice

`DOING (brfss)`. A slice of CDC's Behavioral Risk Factor Surveillance System (adults, by state, 2011–2023) in `~/pdt-brfss`, built from the Copier template: about 25 variables from Twenge's *Generations*. Details: [`planning/tasks/task-30.md`](planning/tasks/task-30.md).

## Working in parallel

Several Claude threads work at once. The coordinator is the thread named **"main: standard + FARS"**. It assigns tasks, decides questions about the standard (or takes them to Allen), and owns `STANDARD.md`, `schema/`, `PROPOSAL.md`, `planning/plan.md` and this board's structure.

- **Claim a task** by changing its status to `DOING (thread name)`. Work on one task at a time.
- **Write details in the task's file,** `planning/tasks/task-NN.md`: progress, findings, proposals. On the board, change only your task's block, and keep it to a sentence or two.
- **Stay in your task's files.** Each task file lists the files it may change. Read anything.
- **The shared checkout:** threads share this repo's working tree. Stage only the files you changed (`git add <path>`, never `git add -A` or `git commit -a`), commit with `git commit -- <paths>` so entries other threads staged stay out of your commit, check `git diff --cached` first, and never write a shared file you haven't read in full. If a shared file looks wrong, restore it from git; don't rewrite it.
- **`lib/`:** add new modules freely. Only one thread at a time changes an existing module.
- **Commit locally** with the task number in the message, run `pytest` here first, and **don't push**. Allen checks before anything goes public.
- **Report** to the coordinator with SendMessage (find it with ListAgents): questions, proposals for the standard, record changes that need the views regenerated, and a short report when a task is done.
- **Drafts of emails** go outside every repo (`~/pdt-private/`). **The web:** on a 403, try a headless browser, and stop at a bot check.
- **Environment:** the `CultureWar` conda env; R, DuckDB and Polars are in `pdt-xlang`.

# Task 73 — A Pages site for the toolkit, and a contribution guide

**Status:** `DOING (red)`, assigned by the coordinator on 2026-11-20 (approved by Allen).

1. A GitHub Pages site for this repo, generated from README.md, PROPOSAL.md and STANDARD.md where possible, not copied by hand: the goals, how a dataset repo works (the three forms of access), the standard, the catalog of dataset repos with links to each one's site, and how to take part. A Pages workflow in `.github/workflows/`.
2. `CONTRIBUTING.md`: the kinds of contribution (a new dataset, an error in a publisher's documentation, a correction, a proposal for the standard, library code); the rules that matter (terms reviewed by a person, no microdata, source and derived facts labeled, hand facts name their author); how to run `pdt check` and the tests.
3. Issue templates in `.github/ISSUE_TEMPLATE/`: new dataset, documentation error (with evidence), standard proposal, bug.
4. Public-facing: nothing from `planning/`, no internal names, no private correspondence. data-dict#9 and PR #268 only as public context. Nothing is published until Allen pushes.

## Progress
- 2026-11-20 (red): done, not pushed.
  - **Site:** `pages/build.py` writes six pages to `_site/`: Home (README), Proposal, Standard (with a contents sidebar), Guides (the step table from `instructions/README.md` and the skill table from `skills/README.md`), Datasets (`pages/datasets.yaml`), and Contribute (`CONTRIBUTING.md`). Links to other repo files go to GitHub. Links to `planning/` and the project board are dropped with their sentence, and the build lists what it dropped (2 in README, 5 in STANDARD). `pages/style.css` has light and dark themes and a phone layout. `.github/workflows/pages.yml` builds with `markdown` and `pyyaml` and deploys with actions/deploy-pages; the repo's Pages source must be set to GitHub Actions.
  - **Datasets:** `pages/datasets.yaml` lists 19 repos, refreshed from their `dataset.yaml` by `--refresh-datasets` (keeping hand-entered `repo` and `site`). None is published yet, so none has a link.
  - **Guide:** `CONTRIBUTING.md`, plus a "Taking part" section in README.
  - **Issue forms:** `.github/ISSUE_TEMPLATE/`: new-dataset, documentation-error, standard-proposal and bug, plus config.yml.
  - **Left for the owners of those files:** STANDARD.md's first lines and §10 mention "Task 5", the snake_case spike, the project board and `planning/`; the site drops those sentences, which loses "Version 0.1, draft". §3's `author` example names "PublicDataToolkit Task 35". `instructions/README.md` mentions the coordinating thread and task numbers, and other instruction and skill files cite task numbers and sibling paths. The site shows only the two tables, but the files are public on GitHub. The template's Makefile has no `data` target (pdt-pulse and pdt-ces add their own).

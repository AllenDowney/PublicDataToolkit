# Task 8 — Versions, layout and names for dataset repos

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE` — decided 2026-11-19

Allen's questions: a version system so a repo built with version 1 can be updated to version 2; whether dataset repos should follow Cookiecutter Data Science (CCDS) or adopt ideas from it; and a name scheme for dataset repos.

**Proposal:** [`planning/versions_layout_names.md`](../../planning/versions_layout_names.md).
- **Versions:** one semantic version for the standard, the template and the shared library. Copier instead of cookiecutter, because CCDS has no way to update a generated project and Copier does (`copier update`, migrations). Major versions come with an upgrade guide for the dataset-specific code, and old schemas are kept so older repos still validate.
- **CCDS:** don't follow its layout; it's built for analysis projects (models, reports). Use its names where the meaning is the same: `data/raw`, `data/interim`, `references/`, `docs/` for the site, Makefile targets, `.env`.
- **Names:** `pdt-<dataset-id>`, e.g. `pdt-gss`, `pdt-anes-cdf`, `pdt-mtf-12`. No language in the name: the repos are language-neutral and the shared library provides language access. A registry of dataset ids in this repo, and a `publicdatatoolkit` GitHub topic.

**Decided (Allen, 2026-11-19):** all four proposals as written: one version plus Copier; CCDS names only; `pdt-<dataset-id>`; a registry plus the GitHub topic. Applied to [`STANDARD.md`](../../STANDARD.md) §1–2 (name, layout, §2.4 versions and updates, `docs/` instead of `site/`).

**Not done yet:** the Copier template (`templates/`), the registry file (create it when the first dataset repo is claimed), and versioned schema paths (at 1.0).

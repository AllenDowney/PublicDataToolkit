# Task 28 — The Copier template for dataset repos

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE` (instructions thread, 2026-11-19; not pushed)

Task 8 decided that dataset repos are generated from `templates/` with Copier, but there's no template yet, and the instructions (Task 24) refer to it. Build one from what the four repos share: `dataset.yaml` and `sources.yaml` skeletons, the Makefile targets (`build`, `check`, `views`), README and CLAUDE.md skeletons with the sections in STANDARD.md §2.3, `EXTENSIONS.md`, `.gitignore`, and a `build/` stub. Test it by generating a repo and running `pdt check` on it.

**Files:** new `templates/` in this repo; a note in `instructions/` where it explains starting a repo (coordinate with whoever owns `instructions/`).

**Done (instructions thread):** [`templates/`](../../templates/README.md): `copier.yml` (17 questions) and `template/`. It generates:
- `dataset.yaml` and `sources.yaml` skeletons that pass the schemas, with every term `unknown` (only a person decides terms) and free-text answers quoted, so a title with a colon stays valid YAML;
- the Makefile (`build`, `views`, `check`);
- README and CLAUDE.md skeletons, with the README passing C11;
- `EXTENSIONS.md`, `.gitignore` and `.copier-answers.yml`;
- a `build/` stub: `build_records.py`, with C3–C5 helpers and `build/report.md`, and `slice.yaml`.

[`templates/test_template.py`](../../templates/test_template.py) has 3 tests, which pass with Copier 9.19.1 and are skipped without it. `instructions/02-sources-and-download.md` now starts a repo with `copier copy`.

**Tested** in the scratchpad:
- A fresh repo builds (the stub writes empty records and a report), and `pdt check` fails only C6, because the first source isn't fetched yet.
- Once the source is hashed, `pdt views` runs (agent/, docs/, export/).
- `pdt check` then failed C9: the records were tracked in git while `terms.metadata` was `unknown`. That's the standard working as written, and the instructions now say not to commit `metadata/` until a person has decided the terms.
- With the terms decided, `pdt check` passes.

**Findings:**
- **`copier update` can't work while `copier.yml` is in `templates/`.** Copier records the template's version (`_commit`, from a git tag) only when the template is at the root of a git repo. From a subdirectory, it records nothing, so a generated repo can't be updated. Tested in scratch repos: with `copier.yml` at the root and `_subdirectory: templates/template`, a repo copied at tag v0.1.0 recorded it, and `copier update` to v0.1.1 brought a Makefile change forward while keeping a local edit. **Proposal to the coordinator:** move `copier.yml` to the toolkit's root (outside this task's files), set `_subdirectory: templates/template`, and tag releases as STANDARD.md §2.4 says.
- **Copier records the template path as given.** Use an absolute path or a URL; with a relative path, `copier update` fails from inside the generated repo.
- **Build script name:** the template uses `build/build_records.py`, matching pdt-gss's rename; the other three repos still use `build_slice.py`.
- **A new repo's records can't be committed before terms are decided (C9).** That's intended, but it means step 1's terms question blocks the first commit of records, not just shipping. If local commits before a decision should be allowed, C9 would need to distinguish "tracked" from "published"; that's for the coordinator.

**Added after the board text above was written (instructions thread):** the template also includes `scripts/download.py`, a wrapper for `pdt.download`, and `make download` (b676e48).

**Decisions for Allen** (decided 2026-11-19, see below):
1. `copier update` can't work while `copier.yml` is in `templates/`: Copier records the template's version only when the template is at a git repo's root. The proposal is to move `copier.yml` to the toolkit's root, with `_subdirectory: templates/template`, and to tag releases as STANDARD.md §2.4 says. It was tested in scratch repos: a repo copied at tag v0.1.0 recorded it, and `copier update` to v0.1.1 merged a template change while keeping a local edit. Copier also records the template path as given, so use an absolute path or a URL.
2. C9 blocks even the first *local* commit of records until the terms are decided, not just publishing. If that's not intended, C9 needs to separate "tracked" from "published".
3. Minor, for Task 18's owner: `download --check` on a missing manual source prints "0 missing or mismatched".

**Decided (Allen, 2026-11-19):**
1. Move `copier.yml` to the toolkit's root, with `_subdirectory: templates/template`, and tag toolkit releases (v0.1.0, ...) as STANDARD.md §2.4 says. Assigned to the instructions thread. Tags stay local until Allen pushes.
2. C9 blocks only publishing: a git remote or a data release. Local commits of records are fine while the terms are `unknown`. STANDARD.md §9 updated; the `pdt check` change is assigned to the fars thread.
3. The `download --check` message is passed to views + site (Task 18).


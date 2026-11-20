# Task 47 — Large sites: docs/ built for Pages

**Status:** `DONE (red)` (see the update below)

The full GSS's `docs/` is 123 MB (14,546 files), so STANDARD.md §2 now lets a repo leave `docs/` out of git and build it for GitHub Pages (a8237e4). C8 changed with it.

a. C8 checks `docs/` only where it exists, and `agent/` and `export/` always. If `docs/` is in `.gitignore`, the report says so.
b. A GitHub Actions workflow in `templates/template` that runs `make views` (docs only) and deploys `docs/` to Pages on a push to main. It must not need the data, and it installs the toolkit at the pinned tag. Nothing is enabled or pushed; it's a file in the template. Orange is editing the template's `build/slice.yaml` (Task 46); this task doesn't touch it.
c. Could the site generator write fewer files for a large release (one page per variable is 14k files)? A proposal here, without changing the generator yet.

**Files:** `lib/pdt/check.py` and its tests; `templates/template/.github/workflows/`, `templates/template/Makefile`; this file.

**Status update:** `DONE (red)`, 2026-11-19; committed locally, not pushed. The site generator is unchanged (c is a proposal).

## a. C8 (67e0f2f)

`check_views` checks `agent/` and `export/data-dict/` always, and `docs/` only where it exists. When `docs/` is in `.gitignore` (asked of git with `git check-ignore`, or read from `.gitignore` outside a git checkout), the report says so: "docs/ is in .gitignore: built for GitHub Pages, not committed", and adds "not built here, so not checked" when it's absent. A `docs/` that's present is checked as before, gitignored or not. Tests: `test_c8_docs_only_where_it_exists`. `templates/test_template.py` no longer expects a C8 failure for a fresh repo's missing `docs/`.

## b. The Pages workflow in the template

[`templates/template/.github/workflows/pages.yml`](../../templates/template/.github/workflows/pages.yml), on a push to main (and by hand):

1. Checks out the dataset repo.
2. Reads `_commit` from `.copier-answers.yml`: the template tag the repo was made from, or updated to.
3. Checks out `AllenDowney/PublicDataToolkit` at that tag into `_toolkit/`.
4. Installs only `pyyaml`, `jsonschema` and `referencing`.
5. Runs `make views PDT=_toolkit VIEWS_ARGS="--only site"`.
6. Uploads `docs/` and deploys it with `actions/deploy-pages`.

No data is needed: the site comes from `dataset.yaml` and `metadata/`. The template's `views` target takes `$(VIEWS_ARGS)` (empty by default, so `make views` is unchanged).

**Checked locally:** in a fresh clone of `pdt-yrbss`, with the toolkit cloned at `v0.1.0` and a virtualenv holding only those three packages, the same `make` command writes `docs/` (83 files) with exit 0. Without `--only site`, `pdt views` fails at the data-dict export, which imports pandas through `pdt.data`. So "docs only" is necessary, not just faster.

**Before it can run:**
- The toolkit's tags must be on GitHub (`v0.1.0` is local, not pushed).
- In each dataset repo, Settings > Pages > Source must be "GitHub Actions". Until then the deploy step fails and nothing is published.
- Nothing has been enabled or pushed.

**Note:** `pyproject.toml` lists only `jsonschema`, `referencing` and `pyyaml`, while `pdt.data` (and through it `export`, `release`, `extract`) needs pandas, numpy and pyarrow. A pip install of the toolkit can't run `pdt views` in full. Either add them to the dependencies (or an extra), or keep the workflow on `--only site` as it is.

## c. Fewer files for a large release: a proposal

Measured on the full GSS (both releases, 6,943 and 6,942 variables), built into a scratch directory:

| | Files | Content | On disk |
|---|---|---|---|
| Whole site | 14,546 | 87 MB | 123 MB |
| Variable pages | 13,885 | about 74 MB (median 4.7 KB, largest 89 KB) | 109 MB |
| … of which the superseded release 7224r3 | 6,942 | 36 MB | |
| Group and subject pages | 654 | | 5.7 MB |
| `search-index.js` | 1 | 4.1 MB | |
| gzipped | | 7.1 MB | |

Building it takes about 95 s. Most of the size is repetition: the two releases' pages are nearly identical, and the site gzips to 7 MB.

**Proposal, in order of payoff:**

1. **One page per variable across releases**, using `pdt.chains` (Task 44). A variable page shows the current release's record, and a "Releases" section lists each earlier release with only what differs (from `pdt diff`'s comparison). Unlinked variables and changes of meaning keep their own pages, cross-linked. For the GSS: 13,885 pages become about 6,945, and about 36 MB is no longer written. It also helps every multi-release repo (BRFSS's 13 years become one page per variable, not 13).
2. **Pages for a superseded release only where they differ.** If (1) is too much, write a superseded release's page only for variables whose records differ from the current release, which is 17 for GSS r3 → r3a (the changes page lists them), and point the rest at the current page. That alone halves the GSS.
3. **Buckets for very large releases**, as an option above a threshold (say 2,000 variables): one page per two-letter name prefix (`ab.html#abany`), about 300 pages of about 25 variables (~120 KB each) for the GSS. Variable URLs become anchors, which keeps deep links but breaks the one-URL-per-variable shape that the search index and the catalog link to. Use it only if (1) and (2) aren't enough.
4. **The search index** (4.1 MB) is fine for Pages, but it could be split by first letter and loaded on demand if it grows.

I'd do (1), which subsumes (2), and stop there. 7,000 files of about 5 KB is fine for Pages (1 GB limit), and with `docs/` built by Actions, its size no longer weighs on git.

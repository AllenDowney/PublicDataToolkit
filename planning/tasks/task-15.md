# Task 15 — Human-readable site: `docs/`

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE` (views + site thread, 2026-11-19; not pushed)

A static site per dataset repo, from STANDARD.md §7: a page per variable, per group and per release, with codes, missing types, availability, corrections and provenance. MkDocs is the suggested generator. The site goes in `docs/`, so GitHub Pages can serve it.

**Files:** new `lib/pdt/site.py` and its tests; `docs/` in the dataset repos (generated).

**Done when:** `make views` writes a browsable site for `pdt-gss` that a person can use to look up `abany` and see its wording, codes, years and ballots.

**Result (views + site thread):**
- [`lib/pdt/site.py`](../../lib/pdt/site.py) writes `docs/` as plain static HTML, with no MkDocs and no new dependency. MkDocs isn't installed in either environment and would add a build step. The HTML opens from disk, and GitHub Pages serves `docs/` as it is (`.nojekyll` included). Light and dark themes; checked at phone width.
- **Pages:**
  - home: the dataset, its terms, citation, dimensions, releases, groups and corrections, plus a search box over name, label and question text;
  - one page per release or table;
  - one page per variable: label, each wording and where it applies, codes with kind, missing types and who classified them, availability as a table of waves by forms with `n`, notes, description, universe, corrections with original, evidence and upstream status, groups, links to other releases, topics (marked as annotations), provenance, and the publisher's page;
  - one page per group;
  - a "what changed" page per pair of adjacent releases (no repo has two releases yet; tested on a fixture).
- **Reused from `agent/`:** the input hash, the HTML header comment, `docs/manifest.json` and `site.is_current(root)` for C8; corrections applied through the same `Index`; and the same wave summary, so pages also say `ballot A, C 1988-2024 (not 1986)`. The availability table gives a skipped wave its own row, "not in this year".
- **`make views`** now builds `agent/` and `docs/`. `pdt views --only agent|site` builds one.
- Sizes: GSS 80 files, ANES 42, NSFG 59, FARS 39. Tests: [`lib/tests/test_site.py`](../../lib/tests/test_site.py).

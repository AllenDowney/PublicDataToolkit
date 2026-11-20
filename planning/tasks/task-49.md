# Task 49 — One site page per variable; a `data` extra

**Status:** `DONE (red)` (see the update below)

a. Task 47's proposal 1: one site page per variable across releases, using `pdt.chains`. A "Releases" section shows what differs, with the per-release detail inside it. A change of meaning gets a separate page, cross-linked as in the catalog. The per-release-pair "what changed" pages stay (STANDARD.md §7). Fallback 2 (pages for a superseded release only where it differs) only if a case needs it. Report page counts and disk size for the GSS (after blue commits Task 26), BRFSS (after green commits) and NSFG.

b. `pyproject.toml`: pandas, numpy and pyarrow go in an optional extra, `publicdatatoolkit[data]`, so the Pages workflow stays light and a full install says what `pdt.data` needs. Update the template README, the instructions and the workflow to match. Importing `pdt.data` without the extra fails with a clear message.

Regenerate any repo whose site changes, once its thread has committed.

**Files:** `pyproject.toml`; `lib/pdt/data.py` (the import guard), `lib/pdt/site.py`, a light module for code text if `export` needs it without pandas; tests; `templates/template/` (README, workflow); `instructions/` where it says how to install; this file.

**Status update:** `DONE (red)`, 2026-11-19; committed locally, not pushed.

## b. The `data` extra

- `pyproject.toml`: `[project.optional-dependencies] data = ["pandas>=2", "numpy", "pyarrow"]`. The base install is `pyyaml`, `jsonschema` and `referencing`.
- **[`lib/pdt/common_format.py`](../../lib/pdt/common_format.py)** holds the common format's names and code text, without pandas: `CODE_SUFFIX`, `ROW`, `PROCESSED`, `file_name`, `is_number`, `as_float`, `code_text`. `pdt.data` and `pdt.release` re-export them, so their callers are unchanged. `pdt.export` and `pdt.check`'s metadata checks import from it. As a result, **`pdt views` runs in full on the base install**, including the data-dict export, as do `check`, `search`, `diff` and `catalog`.
- **Without the extra,** `import pdt.data` raises `ImportError: pdt.data reads and writes the common-format parquet files, and needs pandas, numpy and pyarrow (numpy is missing). Install them with: pip install "publicdatatoolkit[data]"`. `pdt check` reports C3–C5 and C12 as skipped, with that message.
- **Checked:** in a bare virtualenv (only the three base packages), `pdt views` and `pdt check` on a clone of `pdt-yrbss` give 0 failures. `pip install` of the toolkit into a clean virtualenv installs no pandas, numpy or pyarrow, and builds the site. A test imports every metadata module with pandas, numpy and pyarrow blocked.
- **Updated:** the template's README ("How to rebuild": which install does what); `instructions/README.md`; the Pages workflow, which now runs `pip install ./_toolkit` (base, no extra) instead of naming packages.

## a. One page per variable across releases

- `site.py` builds the chains (`pdt.chains`, all releases). A page is `variables/[table/]<name>.html`, named after the latest name. When two chains end in the same name, the older gets `@<release>` (NSFG `FMARITAL@2017-2019.html`, before the opposite-sex change). Every reference (release, group and changes pages, the search index, links) goes through `var_path`, which maps a record to its chain's page.
- **A page** shows the latest record in full, as before. Then:
  - **Releases** (when the variable is in two or more): each release's name, waves, and what differs from the latest ("same as 2023", "codes", "label"), via `pdt.diff.compare_pair`, ignoring `text_only`, `reference_only` and observed ranges. A folded `<details>` per differing release gives the old text and a code-by-code diff.
  - **Related variables:** the chains a change of meaning separates, each cross-linked both ways ("FMARITAL 2017-2019 (earlier): labels_changed, universe_changed").
  - **Other links** keeps links that leave the variable (derived_from, merges); it skips the variable itself and the related ones.
- The per-release-pair "what changed" pages stay (STANDARD.md §7). Fallback 2 wasn't needed.

**Page counts and sizes** (built into a scratch directory from each repo's records; GSS after blue's Task 26, BRFSS from green's working copy):

| Repo | Variable pages before → after | Site files after | Content | On disk |
|---|---|---|---|---|
| GSS (7224r3, 7224r3a) | 13,885 → 6,944 | 7,605 (was 14,546) | 51.3 MB (was 87) | 69 MB (was 123) |
| BRFSS (13 years) | 295 → 65 | 242 | 0.9 MB | 1.4 MB |
| NSFG | 104 → 95 | 106 | 0.5 MB | 0.7 MB |
| CPS ASEC | 287 → 44 | 75 | 0.3 MB | 0.4 MB |
| FARS | 80 → 48 | 61 | 0.6 MB | 0.7 MB |
| YRBSS | 58 → 30 | 55 | 0.2 MB | 0.4 MB |

The GSS site is still above the 25 MB guideline, so it stays gitignored and built for Pages (blue's cf22b43).

**Regenerated and committed** (`pdt check`: 0 failures each): pdt-anes-cdf, pdt-nsfg, pdt-fars, pdt-yrbss, pdt-chicago-crimes, pdt-cps-asec. In pdt-gss, `agent/` and `export/` matched blue's commit, and `docs/` is built locally. pdt-brfss waits for green, whose records are uncommitted.

**Found on the way (told green):** BRFSS 2021 MENTHLTH's "." code is labeled "Not asked or Missing Overall version data" and classified valid. The page's Releases section shows it as the one release where "." isn't missing.

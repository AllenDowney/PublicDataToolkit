# Task 49 — One site page per variable; a `data` extra

**Status:** `DOING (red)`

a. Task 47's proposal 1: one site page per variable across releases, using `pdt.chains`. A "Releases" section shows what differs, with the per-release detail inside it. A change of meaning gets a separate page, cross-linked as in the catalog. The per-release-pair "what changed" pages stay (STANDARD.md §7). Fallback 2 (pages for a superseded release only where it differs) only if a case needs it. Report page counts and disk size for the GSS (after blue commits Task 26), BRFSS (after green commits) and NSFG.

b. `pyproject.toml`: pandas, numpy and pyarrow go in an optional extra, `publicdatatoolkit[data]`, so the Pages workflow stays light and a full install says what `pdt.data` needs. Update the template README, the instructions and the workflow to match. Importing `pdt.data` without the extra fails with a clear message.

Regenerate any repo whose site changes, once its thread has committed.

**Files:** `pyproject.toml`; `lib/pdt/data.py` (the import guard), `lib/pdt/site.py`, a light module for code text if `export` needs it without pandas; tests; `templates/template/` (README, workflow); `instructions/` where it says how to install; this file.

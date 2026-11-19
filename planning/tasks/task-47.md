# Task 47 — Large sites: docs/ built for Pages

**Status:** `DOING (red)`

The full GSS's `docs/` is 123 MB (14,546 files), so STANDARD.md §2 now lets a repo leave `docs/` out of git and build it for GitHub Pages (a8237e4). C8 changed with it.

a. C8 checks `docs/` only where it exists, and `agent/` and `export/` always. If `docs/` is in `.gitignore`, the report says so.
b. A GitHub Actions workflow in `templates/template` that runs `make views` (docs only) and deploys `docs/` to Pages on a push to main. It must not need the data, and it installs the toolkit at the pinned tag. Nothing is enabled or pushed; it's a file in the template. Orange is editing the template's `build/slice.yaml` (Task 46); this task doesn't touch it.
c. Could the site generator write fewer files for a large release (one page per variable is 14k files)? A proposal here, without changing the generator yet.

**Files:** `lib/pdt/check.py` and its tests; `templates/template/.github/workflows/`, `templates/template/Makefile`; this file.

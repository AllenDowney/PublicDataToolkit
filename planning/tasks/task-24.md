# Task 24 — Agent instructions and skills

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE` (instructions thread, 2026-11-19; not pushed)

Write `instructions/` (the eight-step procedure in plan §5) and the first skills in plan §6, using what the four slices taught. Examples:
- probe a PDF before parsing it;
- watch for page-break headers and margin boxes;
- check every source against the data;
- save the terms pages when a site blocks scripts.

Each step should say what to check before moving on.

**Files:** new `instructions/` and `skills/` in this repo.

**Done (instructions thread):**
- **[`instructions/`](../../instructions/)** has a README and one file for each of plan §5's eight steps. Each step says what to do, which STANDARD.md sections apply, what to check before moving on (`pdt check`; coverage, codes, availability, keys and references against the data), and when to stop and ask a person. The examples are the four builds' real traps. The README also says what exists today and what doesn't: C3–C5 run in each build, and `download.py`, `extract.py` and the template aren't written yet.
- **[`skills/`](../../skills/)** has five Claude Code skills, each with `name` and `description` frontmatter: `from-upstream-package` (gssrdoc), `from-html-codebook` (ANES), `from-pdf-codebook` (NSFG; FARS's code matrices), `from-data-labels` (Stata, SAS, CSV label columns) and `from-release-notes` (GSS notes into links).
- **Using a finished repo** links to the generated `agent/SKILL.md` rather than adding a second version.

**Findings:**
- **Skill names differ from plan §6.** `from-upstream-package` matches the standard's origin `upstream_package` (the plan says `from-structured-package`). `from-release-notes` is new: the plan's `release-diff` compares two releases' records, which is a different job and is still unwritten, along with `from-ddi-xml` and `from-open-data-portal`, for want of a real case.
- **No build used an LLM to draft records.** All four sources parsed deterministically once their traps were handled, so the model-drafting path (rule 8) is untested.
- **What every build had to do that the standard doesn't name:** write `build/report.md`; check keys and references against the data (scripted in FARS, done by hand for the NSFG); check that an upstream package documents the release it's used for (gssrdoc). Proposals below.
- **Derived rules are copied into each build.** `scale_signature_from_valid_labels` is in all four repos' build scripts, although STANDARD.md §6 puts derived properties in the shared library. This is the same drift `check_metadata.py` had before it moved into `lib/`.

**Proposals sent to the coordinator** (STANDARD.md is the main thread's):
1. §0 still says `instructions/` is "not written yet"; link it.
2. A numbered data check for keys and references (unique keys; each reference holds in the data, under its `when`).
3. Record which release an upstream source documents (e.g. `documents: [7224r3]` in `sources.yaml`), so a mismatch like gssrdoc's is data, not a note.
4. Name `build/report.md` in §2's layout, as the place for the data checks until `pdt check` runs C3–C5.
5. (`lib/`, not the standard) Move the scale-signature rule into the shared library.

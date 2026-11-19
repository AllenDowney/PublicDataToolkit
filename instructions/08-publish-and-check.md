# Step 8. Publish and check

**Goal:** the repo meets the standard (`pdt check` passes), its README and CLAUDE.md are written, and the data is available as the terms allow.

**Standard:** §2.3 (README and CLAUDE.md), §8 (terms and data, the common format), §9 (definition of done).

## Do

1. **Run the whole build from a clean state:** `make build`, `make views`, `make check`. Every generated file must come from the build, and a fresh clone with `data/raw/` filled should reproduce them.
2. **Write the README** with the sections of §2.3, in order: what the dataset is; terms of use; how to get the data; how to use the metadata (all three forms); how to cite the dataset and this repo; how to rebuild. Include whatever the terms require. The ANES asks for a citation and a link back to the original dataset.
3. **Write CLAUDE.md** for agents working *in* the repo: which files are generated and by what, which are hand-written, how to build and check, and where terms questions go. Copy the shape of [`pdt-gss/CLAUDE.md`](../../pdt-gss/CLAUDE.md), and add the dataset's own traps (pdt-nsfg's: "Watch for page-break headers and margin boxes").
4. **The data release,** only when `terms.data` is `ship`:
   - the publisher's files, unchanged, with SHA-256 sums;
   - the same data in the common format (§8), written with `pdt.data`. The build proves the conversion is lossless by rebuilding every cell. Every file tried so far round-trips exactly: the full GSS (6,943 variables), the full ANES CDF, all three NSFG files, and the FARS tables in the slice ([`missing_codes_design.md`](../planning/missing_codes_design.md) §9; [Task 12](../planning/tasks/task-12.md), [Task 13](../planning/tasks/task-13.md)).

   `pdt.release` (Task 18) writes the common-format files to `data/processed/` and checks the round trip; pdt-nsfg's `make data` shows how. Publishing the GitHub release waits for a person (below).
5. **Record findings in the task's file,** `planning/tasks/task-NN.md`, and keep its entry on the board current: what the build found, what ended up in extensions and why, and what's still open.

## Check before moving on

- [ ] `pdt check` reports no failures. Read its reports too: records without label, question text or values, unresolved codes, unreviewed model output.
- [ ] The build report's data checks (C3–C5, keys and references) are clean or explained.
- [ ] **C9: nothing whose terms are `build-only` or `unknown` is tracked in git.** `git ls-files data/` is empty.
- [ ] **C11:** the README has the six sections in order, and CLAUDE.md exists.
- [ ] The repo's commits are small and say what changed.

## Stop and ask a person

- **Before pushing, publishing a GitHub release, or making anything public.** A person checks first.
- Before claiming the dataset id in the registry, once it exists.
- If any term is still `unknown`.

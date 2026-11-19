# Task 26 — The full GSS release

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DOING (gss)`

Build all of release 7224r3a in `pdt-gss`, not just the 50-variable slice. Eval's topic test needs a full release: on the slices, agents just read everything (Task 23).

- **All 6,943 variables,** from gssrdoc 0.9 (pinned, Task 21). For the 40 names it lacks, use the fallback deferred from Task 21: labels and codes from the R3a Stata file, and text from the R3a codebook where it has an entry.
- **Groups:** batteries by rule and subject groups over the whole file. Battery groups no longer need the slice's "all members present" rule.
- **Links:** the 477 pending note-derived links can now be written, where both releases have records. 7224r3 should also be full.
- **The slice:** keep its 50 variables identifiable, because eval's slice keys refer to them. Ideally `build/slice.yaml` stays as a named subset, and the full build is the default.
- **Checks:** `pdt check` passes, `pdt views` runs (watch shard sizes and counts), and `build/report.md` covers C3–C5 for the whole file.
- **Then** tell the coordinator, so views + site regenerates the views and eval reruns the topic test with its full keys (`eval/keys/full/`, to be rebuilt from 0.9).

**Files:** `../pdt-gss/` only (not its `agent/` or `docs/`).

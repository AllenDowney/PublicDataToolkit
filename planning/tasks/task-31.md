# Task 31 — Check C8

**Status:** `DOING (red)`

Implement C8 in `pdt check`: `docs/`, `agent/` and `export/` are current with the records (STANDARD.md §9). It's the last check not implemented. Red owns the generators (Tasks 14–16) and, for this task, `lib/pdt/check.py` (last changed by orange for Task 17).

The coordinator's suggestion: when the views are generated, record the SHA-256 of the inputs in a small manifest, and have C8 compare the manifest with the current inputs, rather than hashing the outputs.

**Files:** `lib/pdt/check.py`, its tests, and the generators' manifests if they need to change.

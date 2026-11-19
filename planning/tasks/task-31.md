# Task 31 — Check C8

**Status:** `DONE (red)`, 2026-11-19; committed locally, not pushed.

Implement C8 in `pdt check`: `docs/`, `agent/` and `export/` are current with the records (STANDARD.md §9). It was the last check not implemented. Red owns the generators (Tasks 14–16) and, for this task, `lib/pdt/check.py` (last changed by orange for Task 17).

The coordinator's suggestion: when the views are generated, record the SHA-256 of the inputs in a small manifest, and have C8 compare the manifest with the current inputs, rather than hashing the outputs.

**Files:** `lib/pdt/check.py`, its tests, and the generators' manifests if they need to change.

## What C8 does

The generators already wrote such manifests: `agent/manifest.json`, `docs/manifest.json` and `export/data-dict/manifest.json`. Each holds the library version, `inputs_sha256` (one SHA-256 over `dataset.yaml` and every file under `metadata/`, from `pdt.views.inputs_hash`) and the files written. So no generator changed. `check_views` in [`lib/pdt/check.py`](../../lib/pdt/check.py) fails when:

- a view's manifest is missing (not generated);
- its `inputs_sha256` differs from the current records ("out of date");
- a file it lists is gone.

It **reports** without failing when the view was made by another library version, so a toolkit release doesn't fail every repo before step 2 of the upgrade (STANDARD.md §2.4).

The hash covers all of `metadata/`, not only `variables.jsonl`, `corrections.jsonl`, groups and links. The views also use derived properties, annotations and code histories, and a change in any of them makes the views stale.

Hand edits to generated files aren't detected; that would need hashing the outputs, which the coordinator ruled out as fragile. Every generated file says "Do not edit" in its header.

## Tests

- `test_c8_views_current` in [`lib/tests/test_views.py`](../../lib/tests/test_views.py): fails before generation, passes after, fails when a derived file changes, and fails when a generated page is deleted.
- The other checks' tests call `run(root, views=False)`, because their fixture repos have no views.
- `test_cli_exit_codes` now generates views before expecting exit 0.

## Run on the four repos (2026-11-19)

| Repo | C8 | Why |
|---|---|---|
| `pdt-anes-cdf` | pass | |
| `pdt-fars` | pass | |
| `pdt-nsfg` | failed, then pass | Its corrections changed (b572d57) after the last regeneration. Regenerated (d2a3fd7). |
| `pdt-gss` | fails | The gss thread has an uncommitted record file. The views should be regenerated after it commits. |

## For the main thread

STANDARD.md §9 still says "Version 0.1 implements every check except C8, which waits for the generated views." That sentence can now say every check is implemented.

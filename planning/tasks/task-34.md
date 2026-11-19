# Task 34 — release-diff

**Status:** `DOING (red)`

`pdt diff <repo> <release-a> <release-b>`: compare two releases' records, optionally per table, and report:
- variables added, dropped, or renamed (candidates);
- label, question-text and universe changes;
- code changes: codes added or dropped, relabeled, or moved between kinds (valid, missing, unresolved).

It's the input for writing links (STANDARD.md §5.2) and code histories (§5.4). Optionally, it writes proposed links and histories as JSONL with `origin: rule`, for review. It never writes into `metadata/`.

Test on real pairs: FARS 2017 vs 2024 against orange's `histories.jsonl`; NSFG 2017-2019 vs 2022-2023 against yellow's 21 links and the unlinked list in [`task-22.md`](task-22.md); GSS when blue's Task 26 lands.

Also `skills/release-diff/SKILL.md`, and its line in [`skills/README.md`](../../skills/README.md). Plan §6 lists `release-diff` (two releases' records, plus release notes).

**Files:** new `lib/pdt/diff.py` and its tests; the `diff` subcommand in `lib/pdt/cli.py`; `skills/release-diff/`; this file. STANDARD.md and `schema/` stay the main thread's.

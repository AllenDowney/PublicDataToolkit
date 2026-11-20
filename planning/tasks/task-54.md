# Task 54 — Comparing releases: ignored markers, across tables, over gaps

**Status:** `DOING (red)`

Yellow's library proposals from the NHIS slice ([`task-50.md`](task-50.md), "Proposals" 1–3).

## Design

**1. Patterns to ignore, in `pdt.compare`.** From 2022, NHIS's codebook prints "* " before interviewer instructions ("* Read if necessary: ..."), unevenly across years and items. So HOPELESS_A, EFFORT_A and WORTHLESS_A 2021→2024 read as wording changes, while yellow's rule says same_item.
- `compare_text(a, b, ignore=())`. `ignore` is a list of regular expressions. Each match is removed from both texts before they're compared again. A difference that disappears only then is `text_only`: formatting, not wording.
- `pdt diff --ignore REGEX`, repeatable, passes them in. A dataset's link rule passes the same list, so the two agree.
- **Proposed to the main thread, not done:** a `dataset.yaml` field (say `comparison.ignore`) so that a repo declares its markers once. `dataset.yaml` is closed under the schema, which is the main thread's.

**2. `pdt diff` across tables.** Diff pairs variables table by table, so links that cross tables (NHIS 2018→2019: `samadult` → `adult`, every name gaining `_A`) aren't seen.
- Before pairing, diff decides which table in A corresponds to which in B:
  1. `--table-map samadult=adult` (repeatable), when given;
  2. otherwise, the same table id;
  3. otherwise, the table in B that most of the table's links go to.
- Each table pair is then diffed as one table is now: links pair first, names pair the rest. The result's entry for the pair says `from_table` and `table`, and the report heads it "[samadult → adult]".
- A table with no counterpart is listed as "only in A" or "only in B".

**3. Over gaps: `pdt diff REPO --gaps`.** NHIS rotates content: PHQ and GAD in 2019 and 2022, K6 in 2021 and 2024. Diffs of consecutive releases miss the changes across those gaps.
- `--gaps` follows each variable through the releases (oldest first), from each appearance to its next one: by a link when there is one (any one-to-one relation), else by the same name and table.
- Pairs that skip at least one release are compared (`compare_pair`) and reported, with the releases skipped and, when linked, whether the link's relations match the records.
- Pairs in consecutive releases are left to the ordinary diff.
- `--releases` limits it to some releases.

All three are additive. The existing `pdt diff A B` output keeps its fields, and a table pair with the same id reads as before.

**Files:** `lib/pdt/compare.py`, `lib/pdt/diff.py` and their tests; the `release-diff` skill; this file. Not `lib/pdt/search.py`, `lib/pdt/catalog.py` or `lib/pdt/cli.py` (blue, Task 53).

# Task 54 — Comparing releases: ignored markers, across tables, over gaps

**Status:** `DONE (red)` (see "Done" below)

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

### 2026-11-20: blocked on downloads from bls.gov

- `~/pdt-atus` was created from the template (v0.1.0; 5ff6c8a, terms URL fixed in 1fa2d76). The single release is `2003-2023`, BLS's multi-year files, with year as the wave.
- **bls.gov refuses scripts.** These requests got 403 "Access Denied" on 2026-11-20:
  - urllib's and curl's default User-Agents;
  - a browser User-Agent;
  - headless Chromium (Playwright);
  - a generic script name.

  The data page is https://www.bls.gov/tus/data/datafiles-0323.htm. The refusal page says bot activity "that doesn't conform to BLS usage policy is prohibited". BLS's terms (https://www.bls.gov/bls/blsterms.htm) reserve "the right to block robots that do not contain information that can be used to contact the owner".
- **What's needed:** a script would need contact information in its User-Agent. That means Allen's email, which I won't send without his explicit OK. The other way is for Allen to download the files in a browser.
- **Nothing else has started:** no sources, no records.

## Done (2026-11-20)

**Status:** `DONE (red)`; committed locally, not pushed.

**1. Ignore patterns** (`lib/pdt/compare.py`). `compare_text(a, b, ignore=())` replaces each match with a space in both texts. A difference that disappears only then is `text_only`. `compare_pair` and `code_changes` (value labels) pass `ignore` through. `pdt diff --ignore REGEX` (repeatable) passes it in, and the result records it.
- On pdt-nhis 2021 → 2024: HOPELESS_A, EFFORT_A and WORTHLESS_A read `wording_changed` without `--ignore '(?:^|(?<=\s))\*\s'` and `same_item` with it, which matches yellow's links.

**2. Across tables** (`lib/pdt/diff.py`). `table_pairs()` maps tables in this order: `--table-map A=B` (repeatable), the same id, then the table in B that most of the table's one-to-one links reach. Several tables can map to one (a merge). `diff()` pairs variables in two passes: links and names per table pair, then B's unpaired variables, listed once per B table. Result entries gain `from_table` and `only_table`; the report heads pairs "[samadult → adult]" and "[person: only in 2018]". Proposed links use each side's table.
- On pdt-nhis 2018 → 2019: `samadult` → `adult` is found from yellow's three links, which now appear next to the 4 name-paired variables and the unlinked ones.
- `person` and `family` have no links, so they need `--table-map person=adult --table-map family=adult`. With it, their rename candidates show: PHSTAT → PHSTAT_A (0.88), RAT_CAT5 → RATCAT_A.
- The three linked pairs differ from their links. Yellow's links say only `renamed`; the records also show changed labels, wording and universes (SMKSTAT2 → SMKCIGST_A; DEP_1 → DEPFREQ_A; ANX_1 → ANXFREQ_A). That's for yellow to look at.

**3. Over gaps.** `gaps()` and `pdt diff REPO --gaps [--releases ...]` follow each variable to its next appearance: by a one-to-one link to the nearest later release, else by the same name in the counterpart table. Only pairs that skip releases are compared and reported, with the releases skipped and, for links, whether the relations match.
- On pdt-nhis (with `--ignore` for "* "), there are 14 gap pairs, among them PHQCAT_A and GADCAT_A 2019 → 2022, K6SPD_A 2021 → 2024, and DRKSTAT_A and SLPHOURS_A 2020 → 2022 → 2024. All 14 agree with yellow's links.

**Tests:** `test_ignore_markers` (compare); `test_across_tables_by_links_and_by_map`, `test_gaps_follow_links_and_names`, `test_cli_gaps_and_ignore` (diff). pytest: 229 passing, 1 skipped. The `release-diff` skill documents the three options.

**Proposed to the main thread:** a `dataset.yaml` field (for example `comparison.ignore: ["(?:^|(?<=\\s))\\*\\s"]`), so that a repo declares its markers once. Then `pdt diff` and a repo's link rule would read the same list, instead of the rule hard-coding it and diff taking it on the command line.

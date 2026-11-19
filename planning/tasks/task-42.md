# Task 42 — A cross-dataset catalog

**Status:** `DOING (red)`

There are nine repos (gss, anes-cdf, nsfg, fars, chicago-crimes, yrbss, cps-asec, brfss in progress, and the toolkit's eval). A researcher or an agent asking "which datasets ask about sadness or depression, and in which years?" has to search each one.

`pdt catalog <dir-or-repos...> --out <dir>`:
- reads each repo's records (through `Repo.load`);
- writes a combined agent index (one line per variable: dataset, release/table, name, label, waves);
- writes a small static site page listing the datasets, their terms, kinds, releases, waves and record counts.

`pdt search --catalog` searches across repos, with the same completeness labels.

Constraints:
- The output goes outside the toolkit repo (`~/pdt-catalog`; local, no remote).
- No microdata: only metadata.
- A dataset is included only when its `terms.metadata` is `ship`. The catalog says which repos were left out, and why.

Test questions: sadness or depression across YRBSS, BRFSS, NSFG and GSS; marital status across GSS, NSFG and CPS; age at first marriage. Record what the catalog gets right and what it misses (concepts with different names) here.

**Files:** new `lib/pdt/catalog.py` and its tests; the `catalog` subcommand and `search --catalog` in `lib/pdt/cli.py`; this file. Output in `~/pdt-catalog`.

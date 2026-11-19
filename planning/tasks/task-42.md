# Task 42 — A cross-dataset catalog

**Status:** `DONE (red)` (see the update below)

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

**Status update:** `DONE (red)`, 2026-11-19; committed locally, not pushed. The catalog is in `~/pdt-catalog`, a local git repo with no remote.

## What was built

- **[`lib/pdt/catalog.py`](../../lib/pdt/catalog.py)**, as `pdt catalog <dirs-or-repos...> --out DIR [--all-releases]`.
  - **Repos:** a directory with `dataset.yaml` is a dataset repo. A repo is included only when `terms.metadata` is `ship` and its records load. Every other repo is listed, with its reason, in the index, the site page and the manifest. A `pdt-*` directory without `dataset.yaml` is listed and nothing in it is read. The output directory itself is skipped.
  - **Scope:** each dataset's current releases (`--all-releases` for all).
  - **It writes:**
    - `agent/index.md`;
    - `agent/<dataset>.txt`, one line per variable (`release[/table].name | waves | label | question`), split at about 20k tokens (GSS: 16 parts);
    - `catalog.jsonl`;
    - `index.html`: datasets, publishers, kinds, releases with waves and counts, terms, links to each repo's site;
    - `manifest.json`, with each repo's input hash.
  - Metadata only; no data file is read.
- **`pdt search --catalog <dirs-or-repos...> --filter JSON`** runs the filter in each included repo:
  - the completeness label is the weakest of the datasets' labels;
  - a filter key a dataset doesn't have (a subject or group) is no match there, with a note;
  - `text` may be a list (any term), matched at the start of a word, so "sad" doesn't match "disadvantaged";
  - `text_in` limits the match to `name`, `label` and/or `question`.
- Tests: [`lib/tests/test_catalog.py`](../../lib/tests/test_catalog.py).

## In the catalog (2026-11-19)

| Dataset | Releases in scope | Variables |
|---|---|---|
| ANES CDF | 20260205 | 37 |
| BRFSS (in progress) | 2011–2023, 13 one-year releases | 295 |
| FARS | 2024, 2017 | 80 |
| GSS | 7224r3a | 6,943 |
| NSFG | 2022-2023, 2017-2019 | 101 |
| YRBSS | sadc-2023 | 29 |

**Left out:** `pdt-chicago-crimes` and `pdt-cps-asec`, because their `terms.metadata` is `unknown`. `pdt-private`, because it has no `dataset.yaml` and wasn't read. The toolkit's `eval/` isn't a dataset repo.

## The test questions

**Sadness or depression.** `{"text": ["sad", "depress", "hopeless"], "text_in": ["name", "label"]}` gives 32 variables:
- BRFSS ADDEPEV2 (2011–2018) and ADDEPEV3 (2019–2023), "(Ever told) you had a depressive disorder";
- GSS 17, among them `sad`, `cesd1`, `cesd5`, `depress`, `hopeless`, `unhappy`, `hlthdep`, `sadblue`;
- YRBSS q26 and qn26, "Sad or hopeless".

The NSFG slice has no such variable, so none is found. Searching question text as well (79 results) adds BRFSS MENTHLTH, GSS `downblue`, `feeldown` and `mntlhlth`, and YRBSS q84 "Current mental health". It also adds noise: "blue" finds blues and bluegrass music and ANES's "Blue Cross".

**Marital status.** `{"text": "marital", "text_in": ["name", "label"]}` gives 38: GSS `marital`, `martype`, `marunion` and the household roster `mar1`–`mar14`; NSFG MARSTAT, LMARSTAT, FMARITAL, RMARITAL, FMARIT and RMARIT. **CPS isn't there:** its `terms.metadata` is `unknown`. Searching question text too gives 209, because 185 GSS questions mention marriage.

**Age at first marriage.** Found: GSS `agewed` ("Age when first married"), plus `agewedcr` and `marcohrt` (year of first marriage). The NSFG slice has no age at first marriage, so the catalog can't find one there, though the NSFG has it.

## What it gets right and what it misses

**Right:**
- It finds the obvious items in every dataset that has them, quickly (under 3 s for 7,500 variables).
- It shows the waves for each.
- It never claims more than `approximate` for text.
- It says what it left out and why.

**Misses:**
1. **Concepts with different names.** "Depressive disorder" (BRFSS), "sad or hopeless" (YRBSS), "unhappy or depressed", "downhearted and blue" and "mental health not good" (GSS) need several search terms, and some terms ("blue") add noise. Nothing in the records says these are one concept.
2. **No complete answer across datasets.** Subjects are each publisher's own. The GSS's subject list says nothing about the NSFG, so a cross-dataset answer is always `approximate`.
3. **The same variable appears once per release.** BRFSS has 13 lines for MENTHLTH, and its rename ADDEPEV2 → ADDEPEV3 shows as two variables. Names that differ only in case appear twice (NSFG `fmarit` and `FMARIT`).
4. **Slices are slices.** Searching across slices tells you only what the slices include; an empty answer for NSFG depression doesn't mean the NSFG has none.
5. **Terms gate the catalog.** CPS is out until its `terms.metadata` is decided.

## Proposals

1. **A concept vocabulary for the catalog:** annotations (origin hand or model, so always `approximate`) that map variables in several datasets to shared concepts such as depression or marital status, kept in `~/pdt-catalog` or a repo of its own. That addresses misses 1 and 2 without claiming completeness.
2. **One line per linked chain:** use the links (as `pdt diff` does) to show a variable once, with the releases and names it had (BRFSS ADDEPEV2 → ADDEPEV3; 13 BRFSS years as one line).
3. **Decide `terms.metadata`** for `pdt-cps-asec` and `pdt-chicago-crimes` (Allen).
4. **For green (BRFSS):** `_LLCPWT`'s label reads "BLANK Missing 203,895", which looks like a codebook row read as the label.

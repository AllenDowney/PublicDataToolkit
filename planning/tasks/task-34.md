# Task 34 — release-diff

**Status:** `DONE (red)`, 2026-11-19; committed locally, not pushed.

`pdt diff <repo> <release-a> <release-b>`: compare two releases' records, optionally per table, and report:
- variables added, dropped, or renamed (candidates);
- label, question-text and universe changes;
- code changes: codes added or dropped, relabeled, or moved between kinds (valid, missing, unresolved).

It's the input for writing links (STANDARD.md §5.2) and code histories (§5.4). Optionally, it writes proposed links and histories as JSONL with `origin: rule`, for review. It never writes into `metadata/`.

Test on real pairs: FARS 2017 vs 2024 against orange's `histories.jsonl`; NSFG 2017-2019 vs 2022-2023 against yellow's 21 links and the unlinked list in [`task-22.md`](task-22.md); GSS when blue's Task 26 lands.

Also `skills/release-diff/SKILL.md`, and its line in [`skills/README.md`](../../skills/README.md). Plan §6 lists `release-diff` (two releases' records, plus release notes).

**Files:** new `lib/pdt/diff.py` and its tests; the `diff` subcommand in `lib/pdt/cli.py`; `skills/release-diff/`; this file. STANDARD.md and `schema/` stay the main thread's.

## What was built

- [`lib/pdt/diff.py`](../../lib/pdt/diff.py), as `pdt diff <repo> <a> <b> [--table T] [--json] [--proposals DIR]`. Per table it reports:
  - names in both (case ignored), each with the relations the records support;
  - codes added, dropped, relabeled, and moved between kinds or missing types;
  - two classes of difference that aren't changes: `text_only` (case, spacing, dashes) and `reference_only` (questionnaire item references such as `IC-9` or `(FC A-2b)`);
  - rename candidates (between unpaired names) and merge or split candidates (an unpaired name that resembles a paired one), scored on label, question text and codes.
- `--proposals` writes `links.jsonl` (one per name in both) and `histories.jsonl` (two-period, for variables whose codes changed; rows paired by label, then by code), with `origin: rule`, `release_diff` 0.1. Each note says the proposal needs a publisher source. It refuses a directory inside `metadata/`.
- [`lib/tests/test_diff.py`](../../lib/tests/test_diff.py): every category, proposals, the metadata guard, the CLI, and a merge.
- [`skills/release-diff/SKILL.md`](../../skills/release-diff/SKILL.md), and its line in `skills/README.md`.

## Tested on real pairs

**FARS 2017 → 2024**, against orange's 40 links and 42 histories (from the manual):
- Relations agree on **40 of 40** links.
- Codes added and dropped agree for **every** variable whose history covers both years.
- Every change of meaning in the histories (a code whose row changes between the 2017 and 2024 columns: LGT_COND 9, HARM_EV 72 and 99, MAN_COLL 0 and 99, BODY_TYP 42, 65 and 73, ...) shows up as a relabel. **Nothing missed.**
- The diff reports **more relabels** than the histories (BODY_TYP 18 against 3; WEATHER 99). The 2024 records take labels from the CSV's text, which rewords answers the manual keeps as one row. WEATHER 99 is "Unknown/Reported as Unknown (Since 2018)", one row inside one period. The matrix decides what's a change of meaning.

**NSFG 2017-2019 → 2022-2023**, against yellow's 21 links and 19 unlinked names (task-22):
- Relations agree on **3 of 21**. The differences:
  1. **Real label changes the NSFG rule set aside.** EVRMARRY's label went from "Whether R was ever married" to "Ever married to an opposite-sex spouse (computed in FC A-17)", and FMARITAL changed similarly; both are linked `same_item`. Also pregnancy CaseID ("Case identification number" → "Respondent ID Number"), male RELIGION ("(RECODE)" dropped), and PMARPREG.
  2. **Codes the codebook lists only when they have cases.** AGE_R 49–50, PREGORDR 15–16, AGEPREG 97 and OUTCOME_I 1 appear in one release. The records don't keep per-code counts, so the diff reports `codes_changed`; yellow's rule knew there were no cases.
  3. **`labels_changed` together with `codes_changed`** (MARSTAT), which conflicts with the standard's definition; see below.
  4. **Universe text** that changed because other items were renumbered (RELDLIFE: "IC-5 RELNOW = 2-11" vs "IC-4 RELNOW = 1-8"). Reported as `universe_changed`. Whether the population changed is a judgment.
- For all **19 unlinked** names, the diff shows the differences `pdt-nsfg/build/report.md` lists (HIEDUC's recoding, MFLASTP's 7 → 8 and 9, RMARITAL's labels, ...).
- **Rename candidates:** WGT2017_2019 → WGT2022_2023 (0.89) and SEST → VEST (0.76) in each table. SECU, and the 2022-2023 marital and pregnancy additions, stay unpaired.

**GSS 7224r3 → 7224r3a** (blue's Task 26: 6,942 and 6,943 variables), against 6,942 links:
- Relations agree on **6,921**.
- Of the 20 `data_revised` links from NORC's notes, the diff saw **17** as `codes_changed`, because GSS records list the missing codes that occur in the data. It **missed 3** (racopen, racopenv, strvbias), whose revision didn't change which codes occur. Records alone can't show revised data.
- `strvbiasy` → `strvbias` (`merged_into`) is found as a **merge candidate** (0.78).
- `vote_ts` and `pres_ts` are new and `derived_from` variables in the same release, which a two-release diff doesn't cover.

## Findings and proposals (for the main thread)

1. **`labels_changed` with `codes_changed`.** STANDARD.md §5.2 defines `labels_changed` as "the variable label or value labels changed, with the codes unchanged". Orange's FARS links use the two together (7 links), and so does the diff, because labels can change alongside added or dropped codes. Either drop "with the codes unchanged" from the definition, or say that `codes_changed` covers relabels too.
2. **Per-code counts would separate "no cases" from "not a code".** NSFG codebooks print frequencies. A `n` on each value (like availability's `n`) would let the diff, and `pdt check`, tell a code with no cases from a code that was added.
3. **`text_only` and `reference_only` as a library rule.** Item references (`IC-9`, `JB-4`, `(FC A-2b)`) change with questionnaire layout in every NSFG cycle, and probably in other surveys. If the comparison is right, the NSFG rule and future link rules could share it (`pdt.diff.compare_text`).
4. **Variable-label changes the NSFG `same_item` links set aside** (EVRMARRY, FMARITAL: "opposite-sex spouse") may be worth a second look by the nsfg thread.

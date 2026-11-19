---
name: release-diff
description: Compare two releases of a PublicDataToolkit dataset repo with `pdt diff`, and turn what changed into links (links.jsonl) and code histories (histories.jsonl) backed by the publisher. Covers reading the report, telling real changes from text noise, rename and merge candidates, what records can't show (revised data, codes with no cases), and why proposals need a publisher source before they go in metadata/.
---

# Comparing two releases

When a dataset repo has records for two releases, `pdt diff` lists what changed between them. It's the input for links (STANDARD.md §5.2) and code histories (§5.4). It isn't their source: a link records continuity the publisher asserts, never an equivalence we infer.

```
pdt diff . 2017 2024                          # a report, per table
pdt diff . 2017 2024 --table person --json    # everything, as JSON
pdt diff . 2017 2024 --proposals build/diff   # also proposed links and histories, for review
```

It reads the source records (corrections are listed, not applied) and never writes into `metadata/`.

## Read the report

For each table:

| Section | What it means |
|---|---|
| in both, by relations | names in both releases (case ignored), with the relations the records support: `same_item`, `labels_changed`, `codes_changed`, `wording_changed`, `universe_changed` |
| codes added / dropped | a code in one release's values only |
| codes relabeled | the same code, a different label: the meaning may have changed (FARS LGT_COND 9, "Unknown" to "Reported as Unknown") |
| codes kind_changed | valid, missing or unresolved changed, or the missing types did |
| `text_only` | differs only in case, spacing or dashes ("Dark - Not Lighted" vs "Dark – Not Lighted"); not a change |
| `reference_only` | differs only in questionnaire item references ("IC-9" vs "IC-7", "(FC A-2b)"); not a change |
| rename candidates | an unpaired name in each release with similar label, question and codes (NSFG `WGT2017_2019` → `WGT2022_2023`) |
| merge / split candidates | an unpaired name that resembles one present in both (GSS `strvbiasy` merged into `strvbias`) |

## Do

1. **Run it before writing links or histories,** and keep the report in `build/` with the pair it describes.
2. **Find the publisher's word for each change:** release notes, a crosswalk, a code matrix like the FARS manual's, or a documented naming convention. Use [`from-release-notes`](../from-release-notes/SKILL.md) for notes.
3. **Write links from that source.** The source names the link's `origin`. The diff's relations are a check on what you wrote: if the diff shows `codes_changed` and the notes say nothing, look again.
4. **Write histories from the publisher's matrix** when there is one. `--proposals` writes two-period histories that pair rows by label and then by code. That's a starting point when the publisher prints no matrix, and a cross-check when it does.
5. **Treat candidates as questions.** A rename, merge or split candidate is a similarity score. Link it only when the publisher says so.

## What records can't show

- **Revised data without a change in codes.** GSS 7224r3 → r3a has 20 `data_revised` links from NORC's notes. The diff saw 17, as `codes_changed`, because GSS records list the missing codes that occur in the data. It missed racopen, racopenv and strvbias, whose codes didn't change.
- **Codes listed only when they have cases.** NSFG codebooks omit codes with no cases, so AGE_R 49–50 appear in one release only. The diff reports `codes_changed`; the NSFG rule `nsfg_count_labels_reworded` knows better.
- **Variables built from others in the same release** (GSS `vote_ts`, `pres_ts`, `derived_from` vote68…vote20). Those are within one release, not between two.
- **Label rewording the publisher treats as the same answer.** FARS 2024 labels come from the CSV's text, so the diff reports 18 relabels for BODY_TYP where the manual's matrix has 3 changes of meaning. The matrix decides.

## Verify

- [ ] Every link you wrote has a publisher `source`, and no link comes from a model (rule 8) or from the diff alone.
- [ ] For each pair, the diff's relations and your link's agree, or the link's note says why not.
- [ ] Proposed files stay outside `metadata/` until reviewed. `pdt check` C1 and C2 pass once they're in.
- [ ] `make views` after the links change; the site's changes page between the releases reads correctly.

## Tested on

| Pair | Against | Result |
|---|---|---|
| FARS 2017 → 2024 | 40 links and 42 histories from the manual | relations agree on 40/40; codes added and dropped agree on every variable; every change of meaning in the histories found; extra relabels from CSV label text |
| NSFG 2017-2019 → 2022-2023 | 21 links, 19 names left unlinked | agree on 3/21; the rest are real label changes the NSFG rule set aside (EVRMARRY: "ever married to an opposite-sex spouse"), codes with no cases, and `labels_changed` together with `codes_changed`; all 19 unlinked show the differences `build/report.md` lists; weights renamed and `SEST` → `VEST` found |
| GSS 7224r3 → 7224r3a | 6,942 links from NORC's notes and the naming rule | agree on 6,921; 17 of 20 `data_revised` seen as `codes_changed`; `strvbiasy` merge found |

# Who made the hand facts

Task 46, 2026-11-19. A read-only audit of every `origin: hand` fact in the dataset repos: who made it, and when. It was written for Allen's decision on how agent-made judgments are labeled.

Allen has since decided (STANDARD.md §3, commit `e230eaa`): agent-made judgments stay `origin: hand`, with the agent and its task as `author`, never Allen unless he made or checked them. The fixes below follow that decision.

## How this was checked

- **Inventory:** every `origin: hand` object in each `pdt-*/metadata/` (records, links, groups, corrections' corrected values), with its field and author string. Corrections carry their author in their own `author` field, so they are counted separately.
- **Where the facts come from:** each build writes hand facts from a hand-written input, usually `build/slice.yaml`, and stamps every one with that file's single `author:` value. The author string therefore says who is named in the file, not who made each entry.
- **Who made each entry:**
  - The git history of each build input, and the commit that added each entry.
  - Every commit in these repos is made under Allen's git identity. Every one checked is co-authored by Claude (`Co-Authored-By: Claude Opus 5.5`). Those are commits by agent threads in this project, all made on 2026-11-19.
  - Allen's own decisions are recorded in the task files: the scope (which datasets) and each dataset's terms. None of them is a `measure` or another hand fact.
- **What carried over:** a search of Allen's earlier repos (`../CultureWar`, `../GssExtract`, `../ExtractANES`, `../MarriageNSFG`; read only) for any earlier classification of the same variables, and for earlier records of the same corrections.

## The counts

1,071 hand facts. Some are copies: a `measure` is written into each release's record, so one decision for a variable in two releases counts twice. There are 393 distinct decisions.

| Repo | Field | Facts | Distinct | Author string now | Made by | Held by now |
|---|---|---|---|---|---|---|
| pdt-gss | `measure` | 100 | 50 | Allen Downey | Task 5 (the spike, main thread), `2dfbb6b`, `abdd205` | blue |
| pdt-gss | group `slice-snake-case` | 1 | 1 | Allen Downey | Task 5 (which variables are in the slice) | blue |
| pdt-fars | `measure` | 80 | 40 | Allen Downey | Task 5/13 (32 variables, `7a23f52`), Task 13 (orange: 8 PARKWORK variables, `f2761b7`) | yellow (Task 43) |
| pdt-anes-cdf | `measure` | 37 | 37 | Allen Downey | Task 5, `ef7e87b`, `443cb1a` | yellow (Task 43) |
| pdt-anes-cdf | availability of `VCF0009z` | 1 | 1 | Allen Downey | Task 17 (orange), `03a091a` | yellow (Task 43) |
| pdt-anes-cdf | corrected codes (inside corrections) | 5 | 5 | Claude (Task 20) for Allen Downey | Task 20 | yellow (Task 43) |
| pdt-nsfg | `measure`, release 2022-2023 | 55 | 55 | Allen Downey | Task 5, `89390c4`, `1191c93` | yellow (Task 43) |
| pdt-nsfg | `measure`, release 2017-2019 | 49 | 49 | Claude (Task 22) for Allen Downey | Task 22, `896791f` | yellow (Task 43) |
| pdt-nsfg | links | 5 | 5 | Claude (Task 35) | Task 35 (red) | yellow (Task 43) |
| pdt-chicago-crimes | `measure`, `variable_type` | 30 | 30 | Allen Downey | Task 33 (orange), `7c18de2` | orange |
| pdt-brfss | `measure` | 295 | 31 | Allen Downey | Task 30 (green); the repo has no commits yet | green |
| pdt-cps-asec | `measure` | 287 | 41 | Claude (Task 32) for Allen Downey | Task 32 (yellow) | yellow |
| pdt-yrbss | `measure`, `variable_type`, `questions`, availability | 126 | 88 | Claude (Task 29) for Allen Downey | Task 29 (purple) | purple (now on Task 45) |

**Named "Allen Downey" alone:** 599 facts, 245 distinct decisions, in six repos. Every one was made by an agent in this project.

**Corrections** (`author` field):
- **GSS:** 4, "Allen Downey" (`racopen`, `racschol`, `racfew`, `rachaf`). **Carried over:** CultureWar's `codebook/gssrdoc_issue_draft.md` (2026-09-26) records the same four errors, and the first was filed upstream as kjhealy/gssrdoc#1 (`planning/inventory.md`). Allen's name stays, with a note saying where they came from.
- **ANES:** 12. Eleven are "Claude (PublicDataToolkit Task 20) for Allen Downey"; the twelfth, `vcf0006-sources-1954`, is "Claude (PublicDataToolkit Task 17) for Allen Downey" (orange).
- **NSFG:** 1, "Claude (PublicDataToolkit Task 22) for Allen Downey".

## Was any `measure` carried over?

No. None of the earlier repos has a per-variable measure or level of measurement. What they have:
- **Role lists:** ID and weight columns.
- **An ordinal registry:** CultureWar's `notebooks/ordinal/ordinal.py`, covering `polviews`, `partyid`, `VCF0803` and `VCF0301`.
- **`outcome: mean`:** in CultureWar's `variables.yaml`, on 36 thermometers and difference scores.
- **Some implied treatments:** NSFG `hieduc` cut at thresholds.

About 17 of the 123 GSS, ANES and NSFG assignments agree with that earlier evidence, and about 85 have none. So the project's assignments are new judgments, and some happen to agree with Allen's earlier code.

**One disagreement, for Allen:** GSS `partyid` is `categorical` in pdt-gss, but CultureWar models it as a 0–6 ordinal (`ordinal.py`, lines 72–75). That's a substantive question, apart from attribution.

## What each option would have changed

| | `origin: model`, `reviewed: false` | `origin: hand`, the agent as author (**Allen's decision**) |
|---|---|---|
| Facts relabeled | the 599 named "Allen Downey", plus the 472 already naming Claude: all 1,071 | the 599 named "Allen Downey" (245 distinct). The 472 naming Claude already comply; "for Allen Downey" can be dropped for consistency |
| `model` | can be filled honestly: every commit names Claude Opus 5.5 | — |
| `date` | can be filled honestly: the commit date | as now |
| `reviewed` | `false` is honest: no record shows Allen reviewing any of them | — |
| `pdt check` | C9 fails model facts when `llm_processing` isn't `allowed`: pdt-cps-asec, and pdt-chicago-crimes until its terms are recorded. C6 would report 1,071 unreviewed facts | no change |
| Links | rule 8 forbids model-made links: NSFG's 5 hand links would need a person's review, or removal | no change |
| Carried over | the 4 GSS corrections stay Allen's | the same |

## The fixes

The author goes in each repo's **build input**, not in the generated records. A build input may hold judgments made by several tasks, but the builds stamp one author per file. So where entries come from more than one task, the author names all of them, and the file's comments say which entries came from which task. Where a build supports an author per entry, it gets one.

| Repo | Build input | Change | Who applies it |
|---|---|---|---|
| pdt-chicago-crimes | `build/slice.yaml` | `author: Claude (PublicDataToolkit Task 33)` | orange, after the coordinator's terms edit |
| pdt-gss | `build/slice.yaml` | `author: Claude (PublicDataToolkit Task 5)`. The 4 corrections keep "Allen Downey", with a `note`: carried over from CultureWar's gssrdoc issue draft (2026-09-26), filed as kjhealy/gssrdoc#1 | blue, when Task 26 is committed |
| pdt-fars | `build/slice.yaml` | `author: Claude (PublicDataToolkit Tasks 5 and 13)`; a comment that the PARKWORK measures are Task 13's | yellow (Task 43) |
| pdt-anes-cdf | `build/slice.yaml` and `build/build_slice.py` | `author: Claude (PublicDataToolkit Task 5)`; `availability_added.VCF0009z.author: Claude (PublicDataToolkit Task 17)`, used by the build for that field | yellow (Task 43) |
| pdt-nsfg | `build/slice.yaml` | release 2022-2023's `author: Claude (PublicDataToolkit Task 5)` | yellow (Task 43) |
| pdt-brfss | `build/slice.yaml` | `author: Claude (PublicDataToolkit Task 30)` | green |
| pdt-cps-asec, pdt-yrbss; ANES and NSFG corrections | | already name Claude. Optionally drop " for Allen Downey" | their threads |

After each change: rebuild, `make views`, `pdt check`.

**Going forward:** the template's `build/slice.yaml` could start with `author:` empty and a comment: "who makes these judgments: a person, or Claude (PublicDataToolkit Task N)". Then a new repo doesn't start with Allen's name.

## Where the fixes stand (2026-11-19)

| Repo | Status |
|---|---|
| pdt-chicago-crimes | **done**, `f60f6fe`: `Claude (PublicDataToolkit Task 33)`; rebuilt; 0 failures |
| pdt-fars | **done** by yellow, `d03412e`: `Claude (PublicDataToolkit Tasks 5 and 13)` |
| pdt-anes-cdf | **done** by yellow, `65f3463`: `Claude (PublicDataToolkit Task 5)`; VCF0009z's availability `Claude (PublicDataToolkit Task 17)`; " for Allen Downey" dropped from the corrections |
| pdt-nsfg | **done** by yellow, `cff7abd`: 2022-2023 `Claude (PublicDataToolkit Task 5)`; 2017-2019 `Claude (PublicDataToolkit Task 22)` |
| the template | **done**, `8ec956a`: `build/slice.yaml` starts with `author:` empty, the stub's build stops until it's filled, and instructions 03 and 04 say so |
| pdt-gss | sent to blue, for after Task 26 |
| pdt-brfss | sent to green, before its first commit |
| pdt-cps-asec, pdt-yrbss | already name Claude; yellow drops " for Allen Downey" in CPS after the coordinator's terms edit; optional for YRBSS (purple) |

Re-run of the inventory after these fixes: hand facts naming "Allen Downey" alone remain only in pdt-gss (101, with blue) and pdt-brfss (157, with green).

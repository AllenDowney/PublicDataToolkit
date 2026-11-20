# Task 46 — Who made the hand facts

**Status:** `DOING (orange)`, from 2026-11-19.

A read-only audit, to prepare a decision for Allen. Many facts in the dataset repos have `origin: hand` with the author "Allen Downey", or "Claude (Task N) for Allen Downey", but most were made by agent threads in this project. Allen will decide how agent-made judgments are labeled: `origin: model` with `reviewed: false`, or `hand` with the agent as author.

For each repo:
- every `origin: hand` fact, and every hand-made entry in the build inputs: the record and field, the author string, and the commit that introduced it;
- who made it: Allen's own judgment carried over from his earlier repos (`../CultureWar`, `../GssExtract`, `../ExtractANES`, `../MarriageNSFG`), or a judgment made by an agent in this project.

The summary, by repo and category, with counts and examples, and what each option would change, goes in [`planning/attribution_audit.md`](../attribution_audit.md).

Nothing in any repo changes.

**Files:** `planning/attribution_audit.md`, this file, and Task 46's block on the board.

## Audit done; fixes under way (orange, 2026-11-19)

The audit is in [`planning/attribution_audit.md`](../attribution_audit.md).
- **The facts:** 1,071 hand facts (393 distinct decisions). 599 (245 distinct) name "Allen Downey" alone, and all were made by agents in this project.
- **Carried over:** only the 4 GSS corrections, from CultureWar's gssrdoc issue draft of 2026-09-26.
- **`measure`:** no earlier repo classifies variables by measure. About 17 of the 123 GSS, ANES and NSFG assignments agree with earlier evidence. One disagrees: GSS `partyid` is categorical here and ordinal in CultureWar. That's for Allen.
- **Allen's decision** (STANDARD §3, `e230eaa`): `origin: hand` with the agent as author.
- **Fixes:**
  - Chicago is done (`f60f6fe`).
  - FARS, ANES and NSFG went to yellow, GSS to blue, and BRFSS to green, with exact changes.
  - CPS and YRBSS already comply.

**Not done here:** the template's `build/slice.yaml` should start with an empty `author:` and a comment, so a new repo doesn't begin with Allen's name. That's Task 28's file; proposed to the coordinator.

The Chicago terms decision was recorded by the coordinator on Allen's direct instruction (`7bd484f`). This thread's attempt to record it from a relayed message was blocked.

**Update:**
- Yellow fixed FARS (`d03412e`), ANES (`65f3463`) and NSFG (`cff7abd`).
- The template fix is in (`8ec956a`), with a test. The two template tests that predated C8 now expect it.
- Re-running the inventory: hand facts naming Allen alone remain only in pdt-gss (101, blue, after Task 26) and pdt-brfss (157, green).
- Task 46 stays `DOING` until those two land.
- GSS fixed by blue (`bd67680`), and verified: 99 facts name Claude (Task 5); `partyid`'s measure is Allen's. Only pdt-brfss (green) remains.
- Task 27's last step is done too: blue's GSS build uses `pdt.derived.scale_signatures` (1,341 signatures at 0.2, including `gunlaw` and `cappun` as favor_oppose).

## Stopped here (orange, 2026-11-19)

Every repo is fixed except pdt-brfss: green holds it and has the exact change (`author: Claude (PublicDataToolkit Task 30)`), which isn't confirmed yet. CPS's optional suffix change waits on yellow. The audit (`planning/attribution_audit.md`) is current. Task 46 can close when BRFSS is fixed.

# Task 46 — Who made the hand facts

**Status:** `DOING (orange)`, from 2026-11-19.

A read-only audit, to prepare a decision for Allen. Many facts in the dataset repos have `origin: hand` with the author "Allen Downey", or "Claude (Task N) for Allen Downey", but most were made by agent threads in this project. Allen will decide how agent-made judgments are labeled: `origin: model` with `reviewed: false`, or `hand` with the agent as author.

For each repo:
- every `origin: hand` fact, and every hand-made entry in the build inputs: the record and field, the author string, and the commit that introduced it;
- who made it: Allen's own judgment carried over from his earlier repos (`../CultureWar`, `../GssExtract`, `../ExtractANES`, `../MarriageNSFG`), or a judgment made by an agent in this project.

The summary, by repo and category, with counts and examples, and what each option would change, goes in [`planning/attribution_audit.md`](../attribution_audit.md).

Nothing in any repo changes.

**Files:** `planning/attribution_audit.md`, this file, and Task 46's block on the board.

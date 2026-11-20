# Task 69 — Panel responses spread across rounds (NLSY)

**Status:** `DOING (yellow)`: started 2026-11-20. Created by the coordinator, 2026-11-20, at Allen's request.

## The problem

Allen's experience with the NLSY: to find a respondent's answer to a question at a certain age, you may have to look across several rounds. Each round sees only some of the cohort (people miss rounds and come back), and he hasn't pinned down how it works or how best to handle this "smearing" of responses over time.

Likely mechanisms, to confirm from NLS's documentation rather than assume:
- **Non-interviews:** a respondent missed in one round is often interviewed in a later one, and some questions then cover the whole gap.
- **"Since date of last interview" (DLI) questions:** the reference period depends on each person's previous interview, so it varies by person, not by round.
- **Rounds change frequency:** NLSY97 was annual, then biennial; NLSY79 likewise. Ages at interview drift.
- **Event histories and created variables:** NLS builds arrays by week, month or year (employment, marital status, enrollment) and "created variables" that already resolve some of this. They may be the recommended route for many questions.
- **Questions asked once, or only of some people** (by age, or new entrants), and **retrospective questions** that look back over years.

## What to do

1. Read NLS's own guidance: the NLSY97 and NLSY79 topical guides and user guides on nlsinfo.org, on interviews and non-interviews, DLI, event histories and created variables; plus any FAQ on "age at" questions. Cite pages.
2. Measure it in the data: for a few variables in the slice, how often is a person's answer for a given age or year in a different round than the obvious one, and how often missing in all of them?
3. Describe it in the metadata, using the standard where it can (universe, condition, notes, groups for the event arrays). Propose what's missing: for example, a record field for the reference period ("since DLI", "past 12 months", "ever"), or a link between a round's question and the event array it feeds.
4. Advice for users, in the dataset's README and SKILL.md: how to find a person's answer at an age or in a year, and when to use NLS's created variables or event histories instead. This is describing how the publisher's data work, not making analysis choices: say what the options are and what NLS recommends.
5. Design a layer on top: a function (or a derived table, labeled as derived) that, for a question, a person and an age or year, returns the answer with the round it came from and the reference period, or says why there's none. Write the design here; don't build it until the coordinator and Allen have read it.

## Progress

# Task 69 — Panel responses spread across rounds (NLSY)

**Status:** `DONE (yellow)` on 2026-11-20, the layer included (built after Allen approved it). Started 2026-11-20. Created by the coordinator, 2026-11-20, at Allen's request.

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

### 2026-11-20: findings, metadata, advice, and a design

Work is in `~/pdt-nlsy97` 9c54cb0, with library changes in PublicDataToolkit 0de1e5c and afaaa4a.

#### 1. What NLS says (cited)

- **Rounds.** "Surveys were conducted annually through round 15, with biennial interviews beginning in round 16." Fielding begins "in the fall of the survey year and continued through the spring of the following year." "Researchers analyzing topics where time periods are critical should carefully examine the reference period of the questions and the actual interview date for individual respondents." For the previous interview, "first identify the round when the respondent was last interview[ed] … then pick up the corresponding date of interview for that round." ([Interview Methods](https://nlsinfo.org/content/cohorts/nlsy97/intro-to-the-sample/interview-methods))
- **Missed rounds.** "The NLSY97 collects detailed retrospective information about work history, education, training, marital status, and fertility since the date of the respondent's last interview. These questions help capture information lost due to missed interviews. As a result, a perfect response record is not needed …, unless the respondent permanently leaves the survey." Each non-interviewed respondent has a "Reason for Noninterview" code in the round's RNI variable. ([Retention & Reasons for Non-Interview](https://nlsinfo.org/content/cohorts/nlsy97/intro-to-the-sample/retention-reasons-non-interview))
- **Codes.** "Data that are missing because of a non-interview situation are coded with a -5." ([Item Nonresponse & Interview Timings](https://nlsinfo.org/node/485))
- **Created variables.**
  - Interview date and age (CV_INTERVIEW_DATE~M/~Y, CV_AGE_INT_DATE, CV_INTERVIEW_CMONTH);
  - CVC_RND, "the round in which the respondent was last interviewed";
  - cumulative CVC_ versions "across all interview rounds regardless of interview status" (the CV_HGC_EVER_EDT codebook note).

  ([Created Variable Appendices](https://nlsinfo.org/node/411))
- **Event history arrays.** Employment by week; marital and cohabitation status by month; program participation, schooling, arrests and incarceration. "Using these arrays, researchers can extract the status of a respondent at a point in time or over time."
  - They run from age 14 (12 for arrests) to the last interview.
  - Jobs reported late don't change earlier arrays; "backreporter" variables (EMP_BK_WKS, EMP_BK_STATUS, EMP_BK_HOURS) say what would have changed.
  - Denials are flagged (EMP_DENY, MAR_DENY).

  ([Codebook Supplement, Appendix 6](https://nlsinfo.org/content/cohorts/nlsy97/other-documentation/codebook-supplement/appendix-6-event-history-creation-and))

So the mechanisms the coordinator listed are confirmed: non-interviews with later DLI questions covering the gap, annual to biennial rounds, event histories and created variables as NLS's own resolution, and questions asked only of some people. The slice adds two more:
- an "ever" question is asked later only of those who haven't answered it;
- a question's reference period can change from "since the last interview" to "past twelve months".

#### 2. How often it happens in the slice

From `scripts/measure_spread.py` in `~/pdt-nlsy97`:

#### 1. Months between a person's consecutive interviews

| Pairs of interviews | Count | Months between them |
|---|---|---|
| annual (to 2011) | 107,974 | p50 12, p90 19, p99 41, max 178 |
| biennial (2013 on) | 41,206 | p50 24, p90 29, p99 115, max 329 |
| after a missed round | 7,110 | p50 41, p90 96, p99 223, max 329 |

149,180 pairs of consecutive interviews; 7,110 (4.8%) skip at least one round. 3,978 of 8,984 people (44.3%) missed a round and came back. Interviews per person: p10 9, p50 20, max 21.

#### 2. A person's interviews at age A, and NLS's monthly marital array at that age

| Age | 0 interviews at that age | 1 | 2 or more | Of the 0: nearest interview ≤ 12 months from the birthday | > 12 months | MAR_STATUS has a status the month of the birthday |
|---|---|---|---|---|---|---|
| 16 | 2,416 (27%) | 6,355 (71%) | 213 (2%) | 1,661 | 755 | 8,841 (98%) |
| 18 | 1,302 (14%) | 7,220 (80%) | 462 (5%) | 876 | 426 | 8,851 (99%) |
| 21 | 1,733 (19%) | 6,785 (76%) | 466 (5%) | 901 | 832 | 8,695 (97%) |
| 25 | 1,927 (21%) | 6,604 (74%) | 453 (5%) | 791 | 1,136 | 8,449 (94%) |
| 30 | 4,800 (53%) | 4,007 (45%) | 177 (2%) | 3,074 | 1,726 | 8,117 (90%) |
| 35 | 5,090 (57%) | 3,894 (43%) | 0 (0%) | 2,870 | 2,220 | 7,649 (85%) |

#### 3. YSAQ-360C (smoked since the last interview): how many rounds' periods overlap year Y

| Year | People with ≥1 answer whose period overlaps Y | 1 round | 2 rounds | 3 or more | none |
|---|---|---|---|---|---|
| 2000 | 8,759 | 5,324 | 3,235 | 200 | 225 |
| 2005 | 8,377 | 3,302 | 4,310 | 765 | 607 |
| 2010 | 7,784 | 3,131 | 4,464 | 189 | 1,200 |
| 2012 | 1,752 | 1,719 | 33 | 0 | 7,232 |
| 2014 | 4,183 | 3,311 | 872 | 0 | 4,801 |

Periods behind the 107,266 answers: p50 12, p90 19, p99 41, max 178 months; 10,806 (10.1%) are longer than 18 months. (Since-the-last-interview answers only; in [2013, 2015] the question asks about the past twelve months.)

#### 4. YSAQ-359 (ever smoked): the year of a person's first substantive answer

| First answered | People |
|---|---|
| 1997 | 8,953 |
| 1998 | 26 |
| 1999 | 3 |
| 2000 | 1 |
| never answered | 1 |

#### 5. CV_MARSTAT_COLLAPSED at each interview vs MAR_STATUS in the interview month

Married or not agrees in 140,266 of 140,327 person-interviews (100.0%).


Reading these:
- **Missed rounds.** Almost half the cohort (44%) missed a round and came back. After a missed round, the median gap is 41 months.
- **"At age A".** It has one obvious round for 71–80% of people at ages 16–25. It has none for about half at 30 and 35, because by then rounds are two years apart. About 5% have two interviews at the same age.
- **"In year Y" for a since-the-last-interview question.** Half or more of people have two or more answers whose periods overlap a year in 2005–2010. With the twelve-month wording in a two-year cycle, 80% have no answer whose period overlaps 2012.
- **The event array.** MAR_STATUS has a status for the birthday month for 85–99% of people, more than have an interview at that age. It agrees with the interview's marital status (married or not) in 99.96% of person-interviews.

#### 3. In the metadata

- **Wording by round:** `questions[].waves`. For example, YSAQ-360C's two wordings.
- **Universe by round:** `universe` as a list of `{text, waves}` (standard b820cc6). The "ever" questions' universes say who was asked again.
- **Codes by round:** `values[].counts`, the codebook's count each year.
- **Non-interviews:** -5 is `not_asked` (coordinator's decision), and RNI gives the reason.
- **Interview month and age:** person_year has CV_INTERVIEW_CMONTH and CV_AGE_INT_DATE.
- **The event array:** MAR_STATUS is 369 person-level records, in group `array-mar-status` (origin publisher, Appendix 6).
- **Changes between rounds:** `pdt diff . 1997-2023 --waves` lists them.

What the standard lacks (proposals; not edits to STANDARD.md or schema/):

1. **A reference period on each wording:** `questions[].reference_period`, one of
   - `as_of_interview` (CV_MARSTAT_COLLAPSED);
   - `since_last_interview` (YSAQ-360C to 2011, CV_WKSWK_DLI_ALL);
   - `{past_months: 12}` (YSAQ-360C 2013–2015);
   - `past_30_days` (YSAQ-361);
   - `ever` (YSAQ-359, YSAQ-363);
   - `calendar_year` (CV_INCOME_FAMILY, "in the previous year").

   It's from the wording, so origin publisher. In this slice it would be set by hand or by a rule over the text, labeled. A layer needs it to know which period an answer covers.
2. **The panel's timing variables, in `dataset.yaml`:** e.g. `dimensions.wave.timing: {unit: PUBID, interview_month: CV_INTERVIEW_CMONTH, month_zero: 1979-12, age: CV_AGE_INT_DATE}`. Then a layer or check finds them without knowing NLS's names.
3. **A link from a round's question to the event array built from it:** a relation such as `feeds` (CV_MARSTAT_COLLAPSED → MAR_STATUS) or a group `kind: event_history` with the variables it's built from. It's from Appendix 6, so origin publisher.
4. **`AGENT_NOTES.md` in the layout (STANDARD.md §2):** a repo's own advice, copied into agent/SKILL.md. It's implemented in pdt views (0de1e5c) and used by pdt-nlsy97; the standard doesn't list the file yet.

#### 4. Advice for users

`~/pdt-nlsy97/AGENT_NOTES.md` is copied into `agent/SKILL.md` under "About this dataset", and the README has a section that points to it. They give:
- why answers spread;
- NLS's recommendations, quoted with links;
- the options in this repo: the round at age A, the rounds whose periods cover year Y, or the event array, with how often each finds an answer here.

They don't choose among them.

#### 5. Design for a layer (not built)

A library function, `pdt.panel.answers(repo, data, name, person, *, year=None, age=None)`. It returns **every** candidate answer, each with its provenance, and never picks one silently:

```
Answer(value, code_label, kind,              # kind: valid | missing type (not_asked = non-interview, inap, ...)
       wave, interview_month, age,           # the round it came from
       period=(from_month, to_month), period_kind,   # what the answer is about
       overlap_months,                       # for year=: months of Y the period covers
       distance_months,                      # for age=: from the A-th birthday to the interview
       how)                                  # "interview at age A" | "period covers Y" | "event array" | ...
NoAnswer(reason)                             # not interviewed (RNI code), not in universe (-4),
                                             # not in that round's file, outside the array's months
```

How it works:
1. **Timing** comes from proposal 2: the interview month and age for each (person, wave). The previous interview is the person's last interviewed round, not the round before, so a missed round is covered as NLS intends.
2. **The period of each answer** comes from proposal 1, per wording:
   - `as_of_interview`: the interview month;
   - `since_last_interview`: (previous interview, this interview];
   - `{past_months: N}`: (interview − N, interview];
   - `calendar_year`: the year before the survey year;
   - `ever`: (birth, interview].
3. **Candidates.**
   - For `age=A`: rounds whose interview is at age A, then the others by distance from the A-th birthday, each with `distance_months`.
   - For `year=Y`: rounds whose period overlaps Y, each with `overlap_months`.
   - An "ever" answer not asked again (-4, universe "already answered") points back to the round where it was answered, using the universe by wave.
4. **The event array.** When a question feeds one (proposal 3), the array's value for the month is offered too, with `how = "event array"`.
5. **Choosing is a separate, named policy.** `pick(answers, policy)` takes `"exact"` (only at age A, or only periods within Y), `"nearest"`, `"most_overlap"` or `"array_first"`, and the result keeps the candidates and the policy. Defaults are the user's choice; the library doesn't set one.
6. **A derived table** (optional, later): `person_year_resolved` or `person_age`, labeled derived (rule, policy and version), for users who want columns. It would be built from `answers` and `pick`, never shipped as publisher data.

Tests would use small synthetic panels:
- a person who misses a round;
- the annual to biennial switch;
- a wording change from since-the-last-interview to past twelve months;
- an "ever" item asked once;
- two interviews at one age.

They'd check that each candidate's period, overlap and reason are right, and that no policy runs unless asked.

### 2026-11-20: the accepted proposals, and the layer, built

The coordinator accepted all four proposals (standard e0c4e64), and Allen approved the layer.

- **Library:**
  - `pdt check` C2 (3abcff2): `panel` names variables with records, and `past_months` gives `months`.
  - `pdt.panel` (0e5a3e5), as designed. `answers(name, person, year=|age=)` returns every candidate with its round, interview month, age, period and `period_kind`, its overlap with the year or distance from the age, `how`, and that round's universe; or `NoAnswer` reasons.
  - `pick(candidates, policy)` applies `exact`, `nearest`, `most_overlap` or `latest`. It reports disagreeing ties instead of breaking them and keeps the candidates.
  - Calendar years need `month_zero`, the scale's month 0, which the `panel` block doesn't give yet. NLS's is December 1979; a `panel.month_zero` field would make it automatic (a small proposal).
  - Tests: `lib/tests/test_panel.py`, a synthetic panel covering a missed round, the switch from since-the-last-interview to twelve months, ages and ties.
- **pdt-nlsy97** (c74b289):
  - `questions[].reference_period` on 21 wordings, by rule `nlsy_reference_period` from explicit phrases only. YHEA-100 states no period and gets none.
  - `panel: {id: PUBID, interview_date: [CV_INTERVIEW_CMONTH], age_at_interview: CV_AGE_INT_DATE, noninterview: RNI}`.
  - AGENT_NOTES.md has an author line and a `pdt.panel` section, and the README mentions it.
  - `scripts/panel_check.py` reproduces `measure_spread.py`'s counts with `pdt.panel` exactly (2005, 2010, 2012).
  - No `derived_from` links: NLS builds MAR_STATUS from the marriage section's dates (Appendix 6), and those questions aren't in the slice.
- **Not built:** a derived table. When it comes, it's labeled derived, with the rule, policy and version.

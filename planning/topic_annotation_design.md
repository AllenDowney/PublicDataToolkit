# Topic annotation or more groups? A design for the §7.5 comparison

Task 57. A design for review; nothing is built yet. Written by Claude (PublicDataToolkit Task 57), 2026-11-20.

## The question

The Task 53 reruns ([eval/RESULTS.md](../eval/RESULTS.md#task-53-after-the-search-fixes)) left topic search limited by the publisher's subject list:
- the best religion run took the GSS subject "Religion" (405 variables) whole, for recall 0.85;
- its 37 misses are hits the subject doesn't contain.

What gets an agent to those 37: more groups, which keep a `complete` or `complete_by_rule` label, or a topic annotation, which is always `approximate` (STANDARD.md §6)? Plan §7.5 asks for this comparison: search with and without annotations.

## What the misses are

The 37 GSS hits outside the subject "Religion" (key `religion_full`, pdt-gss `cf22b43`, release 7224r3a):

| Kind | Examples | Count |
|---|---|---|
| No subject, module or battery at all, mostly variables newer than Data Explorer's subject tags | `relidimp`, `relidwe`, `religimp`, `norelgsp`, `chrstsav`, `sinsacri`, `evangclx`, `mditate1`, `relscrpt` | about 18 |
| Experiment versions of a subject member, `-v` and `-nv` | `relitenv`, `relitennv`, `postlifev`, `postlifenv`, `biblev`, `biblenv` | 6 |
| GSS Next follow-on versions, `_next` | `relig_next`, `denom_next`, `fund_next`, `jew_next`, `other_next` | 5 |
| In another subject's battery | `grace` (parapsychology), `impchurh` (life aspects), `lfegod` (success), `grprelig`, `grpchurh` (associations), `relig30`, `wwwrelig` (internet), `chnang7` (emotions) | 8 |
| Publisher subject "Jews" | `jewaj`, `jew16aj` | 2 |

## What each mechanism would cover, before any agent runs

Coverage of the key's 242 GSS hits by the bare filter: no agent, no judgment.

| Mechanism | Variables | Hits | Recall | Neutral | Outside the key |
|---|---|---|---|---|---|
| Subject "Religion" (today) | 405 | 205 | 0.85 | 200 | 0 |
| Religion modules (from gssrdoc's module lists) | 341 | 143 | 0.59 | 134 | 64 |
| Subject ∪ modules | 478 | 205 | 0.85 | 209 | 64 |
| Subjects Religion, Jews, Prayer In School | 429 | 207 | 0.86 | 222 | 0 |
| …plus `-v`/`-nv` variants of members | 508 | 212 | 0.88 | 232 | 64 |
| …plus `_next` follow-on versions | 513 | 217 | 0.90 | 232 | 64 |
| Keyword rule over label and question | 618 | 235 | 0.97 | 268 | 115 |

Three things follow:

1. **Module groups don't help religion.** Every religion-module hit is already in the subject. Modules may still be worth adding as publisher facts (EXTENSIONS.md deferred them until the slice had topical modules), but not for this.
2. **Variant groups by rule help a little:** about +5 percentage points. They also help every topic, since any subject member can have experiment or follow-on versions.
3. **The keyword row is circular.** The key's candidates came from the same keywords, subjects and modules ([keys/full/README.md](../eval/keys/full/README.md)), so a keyword annotation scores well by construction. It can't be the annotation we test.

## Proposal: three conditions, measured two ways

**Conditions:**

| Condition | What's added to pdt-gss | Origin, and the label a search gets |
|---|---|---|
| Base | Nothing (Task 53's views) | as today |
| Groups | Variant groups by rule: `-v`/`-nv` experiment versions and `_next` follow-on versions, each grouped with its base variable | `rule`, `complete_by_rule` |
| Annotation | A `religion` topic tag on each variable, drafted by a model that reads each record's label, question and values, and never sees the key | `model`, `reviewed: false`, `approximate` |

Groups and annotation together is a fourth condition, if the first three justify it.

**Measure 1, filter level (no agent).** For each condition, score the bare search, e.g. subject + variants, or topic `religion`, against the key: recall, precision, size. That separates what the mechanism can reach from what an agent does with it.

**Measure 2, agent level.** Rerun `religion_full` under each condition, with the Task 53 protocol (Sonnet, 40,000 tokens). Use three runs per condition rather than two: Task 53's two runs spread from 0.18 to 0.86. Report recall, precision, tokens and label, plus whether the agent used the new mechanism.

**Keeping it honest:**
- **Adjudicate new items.** Every annotation hit outside the key is judged by hand, and the result is reported both against the original key and against the key with real misses added. That's the existing rule: a key change is a separate commit, with both scores.
- **Measure what the key itself misses.** Draw a random sample of 300 of the 6,943 GSS variables that no candidate rule caught, and judge each by hand. This estimates how many on-topic variables the key misses.
- **A second topic, chosen before any annotation is made,** with its own key, so the result isn't tuned to religion. For example, mental health, where the subjects are thin.

## Decisions needed

1. **Variant groups in the standard.** Is a within-release "version of" relation a group kind (`kind: variants`) or a link relation? Links are across releases today, so this is the coordinator's call.
2. **The model annotation's cost.**
   - 6,943 records at about 150 tokens each is about 1M input tokens. In batches of about 200 records per call, that's roughly 35 calls with a small model.
   - It needs an API key and a budget: Allen's decision.
   - The cheaper fallback, annotating only the candidate superset, brings back the circularity.
3. **The second topic,** and who builds its key: a second reader, as the Task 23 README asks.
4. **Scope.** GSS only, or also ANES and NSFG? Those are slices of 39 and 55 variables, where the subject lists already cover religion, so the comparison says little there.

## What isn't proposed

- No change to search, labels or the existing keys.
- No embeddings. The plan keeps them optional, and the annotation is the cheaper test of the same idea.

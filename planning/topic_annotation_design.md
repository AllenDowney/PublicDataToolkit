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

## Decisions (coordinator and Allen, 2026-11-20)

1. **Variant groups** are a group kind, `variants`, with `origin: rule`. They're versions of one item within a release, not continuity across releases. The coordinator adds the kind to STANDARD.md and the schema. They're built by rule in pdt-gss after orange's rebuild is committed.
2. **The annotation** uses a Haiku-class model through the API key, capped at 2M input tokens.
   - Each tag gets `origin: model`, with the model id and prompt version, `reviewed: false`, and the label `approximate`.
   - The prompt and batch plan (below) are fixed before the first call.
   - The job runs under the memory cap and stops if the token cap is reached.
3. **The second topic** is mental health.
   - Its key is built by an agent under a blind protocol, before any annotation exists, and is labeled agent-made with no human check (Allen's choice).
   - It's a fresh subagent that sees only the records.
4. **Scope:** GSS only.

**Order:**
1. The mental-health key.
2. The annotation.
3. Adjudication and the 300-item sample.
4. Reruns, three per condition.

## The mental-health key: blind protocol

**The question,** fixed now, word for word for the eval (`gss_mental_health_full`): "In the GSS, find every variable about the respondent's own mental health: how often they felt sad, depressed, anxious, stressed or lonely, their mental-health diagnoses, days of poor mental health, and treatment or help they sought for emotional problems."

**The builder** is a fresh subagent. Its working directory holds only:
- `records.jsonl`: one line per variable of pdt-gss 7224r3a at `cf22b43`, with name, label, question text, valid value labels, subjects and modules;
- its instructions.

It's told not to read anything else: not the religion keys or results, not `eval/`, not any annotation (none exists yet).

**Its method,** as in the religion key:
1. Find candidates by any rule it chooses (keywords, subjects, modules). It writes the rule down.
2. Read each candidate.
3. Sort each one under this rule:

| Status | What |
|---|---|
| `hit` | The respondent's own mental-health state: feelings and symptoms (sad, depressed, anxious, stressed, lonely, hopeless), diagnoses, days of poor mental health, and treatment or help sought for their own emotional problems |
| `neutral` | On the topic, but not the respondent's own state: attitudes toward mental illness, stigma vignettes, other people's mental health, hypothetical help-seeking, and general happiness or life satisfaction |
| out | Matched a candidate rule but isn't about mental health |

**Output:** `decisions.yaml`, with its candidate rule, its counts, and each hit and neutral with a reason. `eval/keys/full/build_gss_mental_health.py` turns it into the key, records the builder as "agent (fresh subagent, Task 57), no human check", and checks every name against the records.

## The annotation: prompt and batch plan

**Input:** the same `records.jsonl` as the key's builder. Each variable is shown with its name, its label, its question text cut to 400 characters, and up to 12 valid value labels.

**Topics:** both topics are tagged in one pass, so the annotation treats them the same way. The definitions are the two eval questions' wording; the model never sees a key.

**Prompt** (version `topics-0.1`). The system prompt:

> You tag survey variables with topics. For each variable, list every topic below that the variable is about. A variable is about a topic if it asks the respondent about it, or records something about it. Use only these topics; give an empty list if none applies.
> - religion: religious affiliation or preference, attendance at services, the importance of religion to the respondent, prayer, religious belief (for example, views about the Bible), religious experience, and attitudes about religion, religious groups or clergy.
> - mental_health: feelings such as sadness, depression, anxiety, stress or loneliness, mental-health diagnoses, days of poor mental health, treatment or help for emotional problems, and attitudes about mental illness.
> Answer with one JSON object mapping each variable name to its list of topics, and nothing else.

The user message is the batch, one variable per block.

The topic definitions are deliberately wider than the keys' hit rules: they include attitudes. A tag says only that a variable is on the topic. The key's neutral band absorbs the difference, as it does for subjects.

**Batches:**
- 100 variables per call, so 70 calls, run one at a time and resumable.
- Each call's input tokens are logged, and the job stops before a call that would pass 2M.
- The expected total is about 1M: about 110 tokens per variable plus the prompt.

**Output:** `metadata/annotations/topics.jsonl` in pdt-gss, one line per (variable, topic), with:
- `origin: model`, the model id and `prompt_version: topics-0.1`;
- the date and `reviewed: false`.

The raw responses are kept, outside any repo, for checking.

**Amendment (before the first call).** These details were settled while writing the script, [`eval/harness/annotate_topics.py`](../eval/harness/annotate_topics.py):
- **Model:** `claude-haiku-5-5`, at effort `low`.
- **Output:** structured output (`output_config.format`, a JSON schema: a list of `{name, topics}` where each topic is one of `religion` or `mental_health`), instead of free JSON. The answer always parses, and an off-list topic can't occur.
- **The prompt's last sentence** is now "Give the tags for every variable in the batch, by its name." The rest of `topics-0.1` is as above.
- **Records:** each batch file keeps the raw answer and its usage. A refused or cut-off batch is kept on record as untagged, not retried silently. Names missing from an answer are counted.
- **Cap:** the run stops before a call that could pass 2M input tokens, assuming each call is no smaller than the largest so far.

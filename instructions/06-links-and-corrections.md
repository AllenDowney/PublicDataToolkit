# Step 6. Link releases and record corrections

**Goal:** what the publisher says about how variables continue across releases is in `links.jsonl`. Errors in the documentation are in `corrections.jsonl` with evidence. A publisher's code history, if there is one, is in `histories.jsonl`.

**Standard:** §5.2 (links), §5.3 (corrections), §5.4 (code histories), rule 2 (only continuity the publisher asserts), rule 8 (links never from a model).

## Links

1. **Find what the publisher asserts:** release notes, crosswalks (MTF's cross-time question index), naming conventions. The [`from-release-notes`](../skills/from-release-notes/SKILL.md) skill covers release notes.
2. **Write a link only when both ends have records.** `pdt check` fails a link to a missing record. pdt-gss transcribed 50 release-note entries into 464 links but could write only 50 until a second release had records. The rest are listed as pending in `build/links_report.md`.
3. **Every link names its source**: the release notes with a page, or a rule for a documented convention. The GSS rule `gss_same_name_same_item` says a name the notes don't mention is unchanged, because NORC keeps names while items are unchanged.
4. **List every relation that holds** (`same_item`, `data_revised`, `labels_changed`, ...). The relations are your reading of the publisher's text, so the link's note says so and quotes the text.

## Corrections

1. **Candidates come from the data checks** in steps 3–5, and from the publisher's errata pages and issue trackers. gssrdoc issue #1 gave the four GSS race-item corrections.
2. **Verify each one against a second source** before recording it. For the ANES candidates, that was the PDF codebook and the data. Some candidates turn out different on checking: the VCF0878 code problem was in 2024, not 2016.
3. **Record it with evidence** (§5.3): the target and JSON Pointer, `original` and `corrected`, the problem in one sentence, a citation with a quote (counts are good evidence), `confidence`, `upstream`, author and date.
   - `verified` means a source confirms the corrected value. The data file confirming a year counts.
   - `inferred` means it's our best reading, such as the ANES 2024 `-8` as `dk` from the 2024 study's own coding.
4. **Publisher-printed corrections aren't ours.** The NSFG margin box "Corrected universe for MFLASTP" goes into `universe`, with the publisher as origin and the superseded text in `notes`.
5. **Report confirmed errors upstream** and record the report in `upstream`. Drafts of emails to publishers are written outside every repo (in `~/pdt-private/`), and a person sends them.

## Code histories

When the documentation gives codes for many years in one place (FARS's matrices of year ranges), write `metadata/histories.jsonl` from the build: the publisher's periods and rows, verbatim, one line per variable (§5.4). Each release's record still says only what that release means.

## Check before moving on

- [ ] `pdt check` passes C2 (every link end and correction target resolves) and C7 (each correction's `original` still appears in its target).
- [ ] **Every name in a link exists in that release's data file.** pdt-gss's build checks link names against the R2, R3 and R3a Stata files, and found one misprint in NORC's notes: DSDNTPAY for `dsndntpay`. It's recorded as a `name_fixes` entry with its evidence.
- [ ] **Records agree with their histories.** pdt-fars checks each record's codes against the last period of its history: all 27 agree.
- [ ] No link has `origin: model`.
- [ ] A C7 failure means upstream fixed the error. Retire the correction; don't edit the record.

## Stop and ask a person

- Before sending anything to a publisher. You draft the report; a person sends it.
- When a candidate correction would reclassify a code on thin evidence. A single unexplained case (ANES `-4`, one case) stays `unresolved` and is only reported.

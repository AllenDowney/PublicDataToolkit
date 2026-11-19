# Review 1 of PROPOSAL.md: triage

**Received:** 2026-11-19. **Verdict:** "a strong, worthwhile project with a sound architectural idea." It recommends going ahead with a focused prototype (GSS, ANES, MTF), on three conditions: stabilize the schema and provenance model, show that the same architecture works on all three, and build an independent benchmark. Its main strategic point: the project should be judged on how trustworthy its metadata is, not on how sophisticated its agents are.

**Decisions (Allen, 2026-11-19)** are in §4.

The reviewer had only the proposal, which summarizes STANDARD.md. So several suggestions are things the standard already does. The table below says, for each suggestion, what the standard does now and what to change.

## 1. Agreements (no change)

- One repo per dataset; shared library for common machinery.
- Our own format, exported to data-dict.
- Typed missing values; the missing-type list "a good starting point."
- "Describe the data; don't analyze it."
- `complete` vs `approximate`; keep both.
- GSS, ANES, MTF, then a non-survey dataset.

## 2. Suggestions

| # | Suggestion | Already in STANDARD.md? | Proposed response |
|---|---|---|---|
| 1 | **Allow an explicit "unresolved" classification** for codes whose meaning the documentation doesn't give; don't force agents to classify | No. A missing code must have `missing_types`, so an agent would have to guess or use `other` | **Add** `kind: "unresolved"` for codes whose status is unknown, with origin and a note. `pdt check` reports them instead of failing |
| 2 | **Review status,** separate from provenance: extracted, auto-validated, human-reviewed, corrected, unresolved | Partly: model output has `reviewed: true/false`; nothing for parser output | **Add** an optional `review` object on variable records (`status`: `unreviewed`, `checked`, `reviewed`; `by`; `date`). `pdt check` reports counts. "Corrected" already comes from corrections, and "unresolved" from #1 |
| 3 | **Valid ≠ correct:** schema checks establish structure, not facts. Say so throughout | No | **Add** a statement to STANDARD.md and PROPOSAL.md. Add a factual check: a recorded **audit sample** of N random records compared by a person against the source, with the error rate reported |
| 4 | **Define `complete` operationally:** a testable enumeration procedure, not the agent's belief | Labels only (§7) | **Add** a definition: `complete` means the result is every record in scope matching a filter over fields whose origin is publisher, upstream package or data file, and the result includes the filter so anyone can rerun it. `complete_by_rule` is the same, with rule-derived fields allowed. Anything else is `approximate` |
| 5 | **Release-difference report:** added, removed, renamed, wording, categories, missing definitions, availability; never treat a rename as equivalence | Mentioned only ("what changed" pages) | **Add** a defined report with those categories. Renames come only from publisher-asserted links (already rule 2) |
| 6 | **Field-level provenance** | **Yes:** `provenance.fields` and a per-code `origin` | Say so in the proposal |
| 7 | **Explicit version identity** (release, form, wave) on every record | **Yes:** `dataset` and `release` are required; availability has wave, form, sample, mode and phase | Say so in the proposal |
| 8 | **Corrections as first-class records** with ids, dates, authors, evidence, applicability, tested against later releases | **Yes:** `corrections.jsonl` and check C7 | Say so in the proposal |
| 9 | **Separate permissions** for data, documentation and derived metadata | **Yes:** `terms.data`, `.documentation`, `.metadata`, `.llm_processing` | Say so in the proposal |
| 10 | **Value, interpretation and provenance of interpretation are separate;** never infer a meaning from the code alone | **Yes:** `code`, `label`, then `kind`/`missing_types`, then `origin`; publisher marking first | No change |
| 11 | **Reproducibility:** record tool versions, extraction versions and build inputs; keep LLM outputs rather than expect to regenerate them | Partly: source hashes; model, prompt version and date on model output; input hash in generated files | **Add** a build manifest (`metadata/build.json`: library and parser versions, input hashes, date). State that model drafts are stored, never regenerated |
| 12 | **Dataset vs release vs collection** (e.g. the GSS cumulative file and its releases; ANES CDF, single-year studies and panels) | Dataset and release only | **Add** an optional `collection` to `dataset.yaml` (`anes` for `anes-cdf` and `anes-panel`) |
| 13 | **Keep the schema minimal.** Requirements: every field has a defined meaning; every record is interpretable on its own; schema changes stay backward-compatible where practical | Required fields are few; versioning in §2.4 | **Add** the three requirements to STANDARD.md. Partial gap: a record's source ids point into `sources.yaml`, so a record isn't fully interpretable without it. Acceptable; note it |
| 14 | **Define link relation semantics precisely** | One-line meanings; listed as provisional | Tighten during the spike, when MTF tests it |
| 15 | **Compare with DDI Codebook and Lifecycle** | No | **New task:** a short comparison. ICPSR distributes DDI, so MTF is the natural case |
| 16 | **R support early** | "Python first, R later" | **Decide.** A small R reader for the JSONL files (load, look up, recode missing values by type) is cheap if the format is stable |
| 17 | **Automate release monitoring** | No | **Add** to the template: a scheduled CI job running `download.py --check` that opens an issue when a source changes |
| 18 | **Evaluation benchmark:** questions with independent answers, scored on recall, precision, wording fidelity, missing-value accuracy, release differences, abstention and provenance | Partly: recall against hand inventories (earlier plan §7.5) and two queries in the spike | **Expand** into a deliverable: `benchmark/` with questions, answer keys and a scorer. The spike's two queries become its first entries |
| 19 | **Add "How we will know this works"** to the proposal, after §7 | No | **Add,** with the reviewer's acceptance criteria |
| 20 | **Defer** elaborate agent orchestration, broad coverage and sophisticated interfaces | Consistent with the plan | No change |

## 3. Risks the reviewer listed

| Risk | Where it's handled |
|---|---|
| Extraction errors | Source evidence (`source_location`, origins); checks against the data (C3–C5); the audit sample (#3) |
| LLM hallucination | `origin: model` required, review status (#2), links can't come from a model |
| Schema complexity | #13 |
| Licensing | §8 of the standard (#9) |
| Staleness | Release monitoring (#17) |
| Search completeness | Operational definition (#4) and benchmark (#18) |

## 4. Decisions (Allen, 2026-11-19)

| # | Decision |
|---|---|
| 1 | **Done.** `kind: "unresolved"` in the schema (origin required, no missing types) and STANDARD.md §4.2; `pdt check` reports them (C6). Two must-fail cases added to `check_examples.py` |
| 4 | **Done.** STANDARD.md §7 defines `complete`, `complete_by_rule` and `approximate` by how the result was produced, and requires every result to carry its filter and scope so it can be rerun |
| 6–9, 3 (statement), 19 | **Done in PROPOSAL.md:** framing around trustworthy metadata; what the standard already covers (per-field provenance, release identity, corrections, separate permissions); "passing establishes structure, not truth"; the `unresolved` principle; new §8, "How we will know this works" |
| 16 | **R reader early:** a small R reader once the spike settles the format. Python stays the main library |
| 18 | **Spike queries only for now.** Decide on a full benchmark after snake_case |
| 2, 3 (audit sample), 5, 11, 12, 13, 17 | **Not now.** Review status, human spot check, release-change report, build record, collection field, schema design rules, release monitoring. Revisit after the spike |
| 14, 15 | **Open.** Link semantics get tested on MTF in the spike; the DDI comparison isn't scheduled |

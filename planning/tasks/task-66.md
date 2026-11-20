# Task 66 — Two data-dict PRs: integer enums and typed missing codes

**Status:** `DOING (red)`. The plan is written; nothing is forked, pushed or opened.

On [tidyverse/data-dict#9](https://github.com/tidyverse/data-dict/issues/9), Hadley replied to our second comment: "Make sense! I'd be happy to review a PR with the details." That comment asked for two separate capabilities:

1. integer enums with labels, and whether the codes are nominal, ordinal or quantities;
2. typed missing codes: a variable's missing codes, each with a label and one or more types from a shared vocabulary.

This task:
1. Clone tidyverse/data-dict into `~/data-dict` (no fork). Read AGENTS.md, README.md, `schema.yaml`, `schema-field.yaml`, the Rust code that validates enums, the site docs, issue #9 (including nathanj3's proposal) and any contributing notes. Find how it's built and tested.
2. Write the plan here: one PR or two, the exact spec changes (YAML, with abany, polviews and age as examples), the validator changes, tests, docs, and how `lib/pdt/export.py` would use them. Keep it consistent with what we posted, and don't insist on our parquet layout.
3. Stop and report. Nothing is forked, pushed or opened; that's outward-facing, and Allen approves it.

## What I read

Clone: `~/data-dict` at `0161d46` (2026-09-11, "Continue to polish report UI (#256)"). Spec version 0.1.0; crates at 0.0.3.

| Source | What matters here |
|---|---|
| `AGENTS.md` | **New features start in the spec and need a human's explicit yes on the spec wording** before any change to `schema.yaml`, the crates or tests. "Presenting a plan is not sign-off." Spec (`site/spec.md`, `site/dev-validation.md`) and implementation must agree in the same change. Every test that asserts a diagnostic also asserts an `insta` snapshot. If a schema change breaks `site/examples/`, report it rather than fix it. Diagnostics split into `expected` (sentence, full stop) and `message` (lowercase fragment). |
| `site/spec.md` § Types, Measures | `enum` is "a string column … values are always strings". `number` has measures `id` (no compare), `ordinal` (compare), `quantity` (compare, average, sum). `units` is allowed only on `number(quantity)` (S08). |
| `site/spec.md` § Representative values | `values` (enum: list, or map value → label), `range` (required on ordinal, quantity, date, datetime; descriptive, not a constraint), `examples` (required on string, number, number(id)). |
| `site/dev-validation.md` | Checks S01–S36, S60–S69, M01–M05, D01–D09. Next free semantic codes: **S37, S38**. S24 rejects non-string enum values (and map keys). S07 decides which representation key a type takes. M01: `enum` must be backed by string data, never a number. D04: a value outside the enum. |
| `schema.yaml`, `schema-field.yaml` | Closed objects: any new key needs adding to both (columns and struct fields). `values` already admits numbers in list items and map keys structurally, so S24 can report them. |
| `crates/data-dict/src/lower.rs` | `lower_enum_values` already lowers a map's keys as scalars, so `{1: yes, 2: no}` reaches the model as `Scalar::Int` keys with labels. Parsing integer keys needs no change. |
| `crates/data-dict/src/model.rs` | `Column.values: Option<Representation>`; `Representation { items, labels }`. `Scalar::as_enum_value` returns only strings. |
| `crates/data-dict/src/validate_meta.rs` | `types_compatible("enum", "number")` is false: the M01 we hit today. |
| `crates/data-dict-parquet/src/{scan,dictionary}.rs` | The D04 scan and its dictionary-page fast path assume `BYTE_ARRAY` (string) columns. |
| `crates/data-dict/src/export.rs`, `site/export.md` | Export has `values` and `value_labels` for enums. The HTML report (`crates/data-dict-cli/render/dict/app.js`) renders `value_labels` with a `ValueDefs` component. |
| `site/expressions.md` | Assertions support `x IN (a, b, …)`, `IS NULL`, `OR`: enough to state a closed set of codes and "never both" between two columns without new checks. |
| Issue #9 | Hadley's opening post: "we need some way to label numbers, and some way to mark multiple values as missing", with haven's `labelled` as the reference. nathanj3 proposed a `missing` property (list, prefix, range forms), an `enum` whose map keys are numbers, and a `labels` map on `number(quantity)` for partly labelled scales (NPS 0 and 10). Hadley asked why keep codes at all; we answered with polviews, age, partyid, FARS relabels and literature use, and said any representation that keeps values, labels and missing meanings distinct would work for us. |
| CONTRIBUTING | None in the repo. PRs are squash-merged, titled in sentence case, by Hadley and Paul Di Cristina; two other open PRs come from outside contributors. |

**Build and test:** `cargo test --workspace`, `cargo fmt --all`, `cargo clippy --workspace --all-targets`, snapshots with `cargo insta test -p data-dict --test validate_spec` then `cargo insta accept --workspace`. The R package is tested with `R CMD check`; it shells out to the binary and needs no change.

**Not available here:** `cargo` and `rustc` aren't installed. Installing Rust (rustup in `~/.cargo` and `~/.rustup`, about 1 GB) needs Allen's yes. The spec-only first phase of each PR doesn't need it.

## Two PRs, labels first

Two PRs, as the coordinator leaned. Our comment already presented them as "separate, and either one helps alone". The second builds on the first: a missing code on a numeric column needs a label to attach to. Each PR follows data-dict's own two phases: open it with the spec text only, wait for Hadley's yes on that wording, then implement.

### Which form for "integer enums"

The choice that matters most. There are two ways to label numbers, and both came up in the thread:

| | A. `enum` with numeric values | B. `labels` on number types (recommended) |
|---|---|---|
| YAML | `type: enum`, `values: {1: yes, 2: no}` | `type: number(id)`, `labels: {1: yes, 2: no}` |
| Nominal, ordinal, quantity | nominal only; would need a new `ordered` key or similar | already there: `number(id)`, `number(ordinal)`, `number(quantity)` |
| Partly labelled (age 89, childs 8, NPS 0 and 10) | can't: an enum's values are the full set | yes: a label is a note on a value, not a membership list |
| Closed set check | D04 | an assertion, `abany IN (1, 2)`, which exists already |
| Code touched | S24, M01 compatibility, D04 scan and its dictionary fast path for integer columns, export | schema (one key), lowering, one new S check, export, renderer |
| Who proposed it | nathanj3's first form | nathanj3's second form (`labels` on `number(quantity)`); Hadley's "some way to label numbers" |

**Recommend B.** It reuses the measures, so it answers "nominal, ordinal or quantities" with no new concept; it covers partial labels, which A can't; and it touches no metadata- or data-level code. The PR description should say plainly that this is how we propose to meet the "integer enums" request, and why, so Hadley can choose A instead. If he prefers A, the plan for PR 2 doesn't change.

**The name.** `labels`, not `values`. On an enum, `values` is the allowed set, and D04 enforces it. Reusing the name for labels that constrain nothing would give one key two meanings.

### PR 1: value labels on numeric columns

**Spec (`site/spec.md`).** Under Representative values, or a new "Value labels" subsection after Measures:

> `labels`: a map from a value of a numeric column to what it means, such as `{1: yes, 2: no}`. It applies to `number`, `number(id)`, `number(ordinal)` and `number(quantity)`, and to a list whose innermost element type is one of these. Keys are numbers, written unquoted, and labels are strings. A label documents a value; it doesn't restrict the column. A column may label all of its values or only some, as when a scale labels only its ends. To restrict a column to its labelled values, write an assertion such as `abany IN (1, 2)`. `labels` is in addition to the type's representation key, not instead of it: a `number(id)` column still gives `examples`, and an ordinal or quantity still gives `range`.

The measure says what the codes are:

```yaml
# Nominal: the numbers are names for categories.
- name: abany
  label: Abortion if woman wants for any reason
  type: number(id)
  examples: [1, 2]
  labels:
    1: "yes"
    2: "no"
  constraints:
    - assert: abany IN (1, 2)

# Ordinal: ordered, not averaged by the type (an analyst may still treat it as a scale).
- name: polviews
  label: Think of self as liberal or conservative
  type: number(ordinal)
  range: [1, 7]
  labels:
    1: extremely liberal
    2: liberal
    3: slightly liberal
    4: moderate, middle of the road
    5: slightly conservative
    6: conservative
    7: extremely conservative

# Quantity with one labelled value: top-coded age.
- name: age
  label: Age of respondent
  type: number(quantity)
  units: years
  range: [18, 89]
  labels:
    89: 89 or older
```

(YAML 1.1 readers turn unquoted `yes`/`no` into booleans, so the example quotes them. Worth one sentence in the spec, as it already says about quoting numeric strings.)

**Validation (`site/dev-validation.md`), one new check:**

| Code | Name | Sev | Description |
|---|---|---|---|
| S37 | Invalid value labels | E | A column has `labels` but its type isn't a number type (or a list whose innermost element type is); `labels` is empty; or a key isn't a number. `.nan` is never a key. The labels themselves being strings is structural. |

S07 doesn't change: `labels` is not a representation key, so the existing rules for `examples` and `range` still hold. A label outside the column's `range` is not checked, since `range` is descriptive.

**Implementation, after sign-off:**

| File | Change |
|---|---|
| `schema.yaml`, `schema-field.yaml` | `labels: object: additionalProperties: string` on columns and on struct fields |
| `lower.rs`, `model.rs` | `Column.labels: Option<Representation>`, lowered by the same code as an enum's map form (`lower_enum_values` already returns keys and labels) |
| `validate_spec.rs` | S37, in the style of S08 (placement) and S24 (key types, quoting hint for `'1'`) |
| `export.rs`, `site/export.md` | number columns export `value_labels`, as enums already do; numeric keys rendered as their JSON number's text |
| `render/dict/app.js` | show `value_labels` for number columns with the existing `ValueDefs` |
| `draft.rs` | none; it can't infer labels from parquet |

**Tests:** fixtures in `crates/data-dict/tests/fixtures/spec/`: `s37-labels-ok.yaml` (the three examples above), `s37-labels-on-string.yaml`, `s37-labels-string-key.yaml` (quoted `'1'`, with the hint), `s37-labels-empty.yaml`, `s37-labels-list-ok.yaml` (`list(number(id))`). Each gets a test in `tests/validate_spec.rs` with `assert_contains` and a snapshot. An export test that `value_labels` appears on a number column. `validate-meta` and `validate-data` on a parquet with an integer `abany` pass (no M01).

### PR 2: typed missing codes

**The idea.** A column declares which of its values stand for a missing answer, and why. Where the codes live is the author's choice: in the value column itself (SPSS style, `98` in a numeric column), or in a separate column (our layout, or any other). The property sits on the column that holds the codes. That fits Hadley's "the paired 'missing meaning' column makes sense" without making our layout part of the spec.

**Spec.** A new subsection, "Missing codes", after Value labels:

> `missing`: the values of this column that stand for a missing answer rather than a measurement. Like `values`, it takes two forms. A list (`[98, 99]`) says only which values are missing. A map gives each one's missing type, or a list of types when a code combines several reasons (`{98: dont_know, 99: no_answer, 0: [dont_know, refused, no_answer]}`). Keys match the column's type: numbers on a number column, strings on an `enum`. Each key must be a labelled value: in `labels` for a number column, in `values` for an `enum`. The label says what the publisher called the code; the type is a classification from the shared vocabulary below, so two sources can be compared and missing answers recoded by reason.

The vocabulary, from our STANDARD.md §8, spelled out to suit a general spec:

| Type | Meaning |
|---|---|
| `dont_know` | the respondent didn't know or couldn't choose |
| `refused` | the respondent refused |
| `no_answer` | no answer recorded, reason unknown |
| `inapplicable` | not applicable: outside the universe or skipped by design |
| `skipped` | the respondent skipped it (self-administered modes) |
| `not_asked` | not asked of this respondent's wave, form or interview |
| `not_available` | asked, but not released in this file |
| `uncodeable` | answered, but couldn't be coded or imputed |
| `unknown` | the source records the value as unknown (administrative data) |
| `unspecified` | the source marks the code missing but gives no reason |
| `other` | anything else; the label says what |

Examples, in both layouts. Codes inline (as the ANES files and SPSS store them):

```yaml
- name: vcf0101
  type: number(quantity)
  units: years
  range: [17, 99]
  labels:
    0: NA; DK; RF; no Pre IW
    97: 97 years old (1952, 1974, 1996 and later: or older)
    98: 98 years old (1958-1962, 1966, 1968: or older)
    99: 99 years old (1976-1990, 1994, 2002: or older)
  missing:
    0: [no_answer, dont_know, refused, not_asked]
```

Codes in their own column (as Stata's extended missing values and our parquet store them). The value column holds only valid answers:

```yaml
- name: abany
  type: number(id)
  examples: [1, 2]
  labels: {1: "yes", 2: "no"}
  constraints:
    - assert: abany IN (1, 2)
- name: abany__code
  label: "Abortion if woman wants for any reason: missing code"
  type: enum
  values:
    .d: don't know
    .i: iap
    .n: no answer
    .s: skipped on web
  missing:
    .d: dont_know
    .i: inapplicable
    .n: no_answer
    .s: skipped
  constraints:
    - assert: abany IS NULL OR abany__code IS NULL
```

The two-column checks we asked for in the issue are already expressible: "every code is declared" is D04 on the enum, and "never both" is the assertion. No new data check is needed. The spec text should show this pattern as one way, not the way.

A value listed in `values` but not in `missing` is an ordinary category. That covers a code with no known meaning (ANES `VCF9236` `-1`), which our records call `unresolved`.

**Validation, one new check:**

| Code | Name | Sev | Description |
|---|---|---|---|
| S38 | Invalid missing codes | E | A column has `missing` but no `labels` or `values` to hold its keys; `missing` is empty; a key isn't one of the column's labelled values; or a key's type doesn't match the column (a string on a number column). |

The type names are a fixed set in `schema.yaml` (`enum: [dont_know, …]`), so an unknown one is reported structurally as S62 ("value not allowed").

**Implementation, after sign-off:** `schema.yaml` and `schema-field.yaml` (a `missing` key: list of scalars, or a map to a type or list of types); `Column.missing` in the model and lowering; S38 in `validate_spec.rs`; `export.rs` and `site/export.md` (`"missing?": {"value": ["type", …]}`, plus a flag in `value_labels` rendering); `app.js` marks missing codes beside their labels. **Tests:** fixtures for both layouts passing, a missing key that isn't labelled, a string key on a number column, an unknown type (S62), an empty `missing`; snapshot each.

### Open questions for Hadley (in each PR's description)

1. **A or B** for labelling numbers (above).
2. **Closed or open vocabulary.** We recommend closed, with `other`, since a shared vocabulary is the point. The alternative is any string with a recommended set and a warning for others.
3. **`range` and `examples` with inline codes.** Should a number column's `range` cover only its non-missing values (age `[17, 99]` without `0`)? `range` is "observed", so today it would include the codes. We'd suggest it describe the non-missing values once `missing` exists, but this is his call.
4. **nathanj3's prefix and range forms** (`missing(prefix): .`, `missing(range): [95, .inf]`). Left out to keep PR 2 small; they could follow if SPSS users want them.
5. **Spec version.** Both add keys to a closed schema. Leave `$version` at 0.1.0, or bump?

## How our exporter would use them

`lib/pdt/export.py`, once each PR is merged and released (not before; until then the exporter keeps today's output):

| Today | With PR 1 | With PR 2 |
|---|---|---|
| numeric valid codes → `number(id)` or `number(ordinal)`, labels in `details` as "Codes: 1 = yes; 2 = no" | same types, plus `labels` from the valid codes' labels; drop the "Codes:" line. Quantities (`age`) get `labels` for their labelled values only | — |
| LOSSES: `numeric_code_labels` (47 of 50 GSS, 34 of 37 ANES, 42 of 52 NSFG, 24 of 40 FARS) | goes to zero | — |
| `<name>__code` column: `enum`, labels "don't know [dk]" with the types in brackets | — | labels as published ("don't know"); `missing` maps each code to its types (`dk` → `dont_know`, `inap` → `inapplicable`, others unchanged); `unresolved` codes stay in `values` and out of `missing` |
| no assertion between the pair | `abany IN (1, 2)` on closed nominal sets (optional; only where the records say the set is complete) | `abany IS NULL OR abany__code IS NULL` on each code column |
| LOSSES: `missing_codes` | — | goes to zero; who classified each code (`origin`) stays in `details` |

The record fields don't change. The mapping from our type names to data-dict's is a small table in `export.py`. If Hadley picks a different name for a type, only that table changes.

## Next steps (for Allen)

1. Approve the plan, or choose between A and B for PR 1 first.
2. If approved: fork tidyverse/data-dict, open PR 1 as a draft with the spec text only, and ask Hadley for a yes on the wording. Outward-facing, so Allen's call.
3. Installing Rust here to implement and test after sign-off (about 1 GB), under the memory cap.

## Progress

- 2026-11-20: Allen approved the plan with form B. PR 1's spec text is drafted locally in `~/data-dict` on branch `value-labels` (commit `113b002`: `site/spec.md` gains a "Value labels" subsection and the `labels` entries; `site/dev-validation.md` gains S37). The PR description is outside the repo for Allen to read. Nothing forked, pushed or opened; Rust not installed.
- 2026-11-20: Allen changed PR 1: nominal codes get a new measure, `number(nominal)` (same operations as `id`, but a category, not a key), instead of `number(id)`. The branch is amended (commit `1b3e9b6`): Measures table, the id/nominal paragraph, abany as `number(nominal)`, every list of measures, and S28. The exporter's categorical codes would become `number(nominal)` with `labels`. The description adds two open questions: the name (`nominal` or `category`), and whether existing `id` columns holding codes should move.
- 2026-11-20: PR 1 is open as a draft, on Allen's go-ahead: [tidyverse/data-dict#268](https://github.com/tidyverse/data-dict/pull/268), from `AllenDowney:value-labels` (the fork is remote `fork` in `~/data-dict`). It holds the spec text only and waits for Hadley's yes on the wording. Replies on GitHub are Allen's.

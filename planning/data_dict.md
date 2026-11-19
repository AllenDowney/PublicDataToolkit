# PublicDataToolkit and data-dict

**For:** Hadley Wickham. **From:** Allen Downey. **Date:** November 2026, after snake_case.

This note explains how PublicDataToolkit plans to use [data-dict](https://data-dict.tidyverse.org/), where our needs go beyond the current spec (`$version: 0.1.0`), and what we'd like to ask you. The project as a whole is described in [`PROPOSAL.md`](../PROPOSAL.md), and the draft standard is [`STANDARD.md`](../STANDARD.md).

## 1. The project in brief

PublicDataToolkit is a set of instructions, agent skills and a small shared library. With them, an agent can turn one public dataset (the GSS, the ANES, Monitoring the Future, a city open-data portal) into a well-documented repository. Each dataset gets its own repository, named like `pdt-gss`, holding:

- the data, or a script to fetch it when the terms don't allow redistribution;
- metadata records for every variable in every release, built from the publisher's codebooks;
- three generated forms of those records: a website, a Python library, and files an LLM agent can read in full.

The datasets we started with are long-running surveys. Their documentation has features that most data dictionaries don't model:

- **Numeric codes with labels:** `1 = yes`, `2 = no`, `98 = DK`.
- **Several kinds of missing value:** don't know, refused, not asked this year, not asked on this ballot. Analysts treat these differently.
- **Many releases,** in which variables are renamed, reworded or recoded.
- **Question wording that varies by year or interview mode** within a single variable.
- **Known errors in the official documentation,** with corrections that need to stay distinguishable from the original.

## 2. How we plan to use data-dict

Our own JSONL records are the source of truth. From them, **each dataset repository exports one `data-dict.yaml` per release.** That gives every repository data-dict's spec validation, data validation and rendered site, and it lets anyone who knows data-dict read our metadata without learning our format.

How our records map onto data-dict:

| Our record | data-dict |
|---|---|
| dataset title, description, publisher | `name`, `label`, `description` |
| one release | one dictionary; `version: {number: ...}` or `{date: ...}` |
| the URL of the repository that builds the records | `origin` |
| a data file in the release | a table, with `source: {parquet: ...}` (after we convert from Stata or SPSS) |
| a variable's name and label | column `name` and `label` |
| question text, publisher's notes | column `description` and `details` |
| measure (ordinal, continuous, identifier) | `number(ordinal)`, `number(quantity)`, `number(id)` |
| valid range, units | `range`, `units` |
| valid codes with labels | `enum` with a `values` map, codes written as strings |
| **missing codes and their types** | no equivalent |
| **question wording by year or mode** | flattened into `details` |
| **availability by year and ballot** | no equivalent |
| **links between releases** (renamed, reworded) | no equivalent |
| **corrections to the publisher's text** | no equivalent; we export the corrected text |
| **provenance per field** (publisher, data file, rule, person, model) | no equivalent beyond `origin` |
| batteries and sections | no equivalent |
| search aliases ("fair housing law" for a 1970s item) | possibly `glossary`, though it's for defining terms rather than synonyms |

The rows in bold are where the export loses information. For our users that's acceptable, because our own files keep everything. But some of these gaps seem likely to matter to other data-dict users too, which is why we're asking.

## 3. A concrete case

The GSS variable `abany` ("abortion if woman wants for any reason") is stored in the Stata file as a number. Its codes are `1` yes and `2` no, plus Stata extended missing values: `.d` don't know, `.i` inapplicable, `.n` no answer, and several more.

Exported to data-dict today, there are two choices, and both lose something:

```yaml
# Option A: keep the codes numeric; lose the labels.
- name: abany
  label: abortion if woman wants for any reason
  type: number
  range: [1, 2]

# Option B: keep the labels; codes become strings, and the parquet
# column has to be converted to string for validate-data to pass.
- name: abany
  label: abortion if woman wants for any reason
  type: enum
  values: {"1": "yes", "2": "no"}
```

In both, the missing codes either disappear or become nulls. Nulls lose the distinction between "don't know" and "not asked this year." haven's `tagged_na()` and `labelled_spss()` with `na_values` exist to keep exactly that distinction.

## 3a. Evidence from a working export

We've since built the export (PublicDataToolkit Task 16): one `data-dict.yaml` per release for four datasets, GSS, ANES, NSFG and FARS, written from our records. Every file passes `data-dict validate-spec` (data-dict-yaml 0.0.3, spec 0.1.0), and a test passes `validate-data` against a parquet file in our common format.

What the export had to drop or flatten into text:

| | GSS (50 vars) | ANES (37) | NSFG (52) | FARS (40) |
|---|---|---|---|---|
| Numeric codes whose labels went to `details` | 47 | 34 | 42 | 24 |
| Missing codes, typed only in a label's text | 182 | 89 | | |

Also lost or flattened, in all four:
- availability by wave and form, which becomes one line of text (2,871 entries for the GSS);
- wording that varies by wave;
- corrections, of which only the corrected text survives;
- provenance per field (about 300 per repo);
- groups, links between releases, derived properties and code histories;
- conditional joins (FARS person → vehicle "when PER_TYP is 1, 2 or 9");
- release ids that are neither semver nor a date.

The first row is the main one. An `enum` with `{"1": "yes"}` passes `validate-spec` but fails `validate-meta` (M01: "the data is `number`"), because our value columns hold numbers.

## 4. Questions

1. **Labels on numeric codes.** Would data-dict consider value labels on `number` columns, or `enum` values that may be integers? Survey data almost always stores coded answers as numbers.
2. **Missing-value codes.** Is declaring missing codes in scope? For example, a column-level list of codes that are present in the data but mean "missing," each with an optional type (don't know, refused, not applicable). haven already models this for R. A data-dict equivalent would let `validate-data` check those codes too.
3. **Extensions.** Does the validator reject keys it doesn't recognize? If so, would you accept a namespaced extension block (such as `x-pdt:` or an `extensions:` map) that validators ignore? We'd use it to carry missing types, availability and provenance in the export, instead of dropping them.
4. **Releases.** Is "one dictionary per release" the intended way to describe a dataset that's republished with changes, or do you see history across releases as something data-dict might model? For example, a `previous` link, or `renamed_from` on a column.
5. **Sources.** Most of these datasets are published as Stata, SPSS, SAS or CSV. The spec mentions more access methods later. Is reading Stata or SPSS files, or CSV, on the roadmap? Or should we convert to parquet and point `source` at that?
6. **Exporting from another format.** Is generating `data-dict.yaml` from our records, and never editing it by hand, a use you're comfortable with? Would you prefer we mark generated dictionaries in some way, for example in `origin` or `details`?
7. **Stability.** Since we'd export to a 0.x spec, is pinning to a `$version` and updating the exporter when it changes the right approach? Is there a sense of which parts are likely to change?
8. **Agent skills.** data-dict's creation skill drafts dictionaries from PDF, HTML and DOC codebooks, and our build step does something similar. Is there room to share that work? For instance, could our skills produce data-dict drafts, or reuse your prompts?
9. **Rendering.** We'd like each dataset repository's website to come from `render-spec`, plus a few pages of our own (changes between releases, corrections). Is `render-spec` meant to be extended or themed that way?

Whichever of the gaps in §2 belong upstream in data-dict, we'd rather contribute there than keep a parallel format. We'll keep whatever doesn't belong there in our own records.

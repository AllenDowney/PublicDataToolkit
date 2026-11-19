# Code lists as tables, and retired codes

Task 38, for the coordinator's review. This is a design only: STANDARD.md, `schema/` and the library are unchanged. It follows up proposal 4 of [Task 33](tasks/task-33.md).

## The question

Today every variable record copies its codes into `values` (STANDARD.md §4.2). That works for most variables, but three cases strain it:
- **A publisher's list belongs to several variables:** GSS occupation codes are used for the respondent, spouse, father, mother and others.
- **A publisher publishes a list on its own:** Chicago's IUCR codes are a separate dataset, with columns of their own.
- **A code is retired:** it's still in the data for earlier years but no longer used.

Should a list be stored once and referenced? And where does "retired" go?

## The cases

| Dataset | List | Size | How it's published | Shared by | Changes over time |
|---|---|---|---|---|---|
| GSS | Census 2010 occupations | 540 valid codes | inline in gssrdoc, for every variable that uses it | `occ10`, `paocc10`, `maocc10`, `spocc10`, `coocc10`, `occ10_next`; and, with labels differing only in whitespace, `kdocc10`, `sphedocc10`, `sbocc10` | a new classification is a new variable (`occ80`, `occ10`) |
| GSS | ISCO-08 | 587 | inline | `isco08`, `paisco08`, `maisco08`, `spisco08`, `coisco08` | — |
| GSS | Census 2010 industries, 1980 occupations, 1980 industries | 271, 505, 232 | inline | 6, 4 and 6 variables | — |
| Chicago | IUCR | 434, 10 of them retired | its own dataset (`c7ck-438e`), with primary and secondary descriptions, an index flag, and `active` | `crimes.iucr` | codes retired, never removed |
| Chicago | FBI codes | 26 in 2024 | a CPD web page that now needs a sign-in | `fbi_code` | — |
| FARS | `BODY_TYP`, `HARM_EV`, `STATE`, ... | up to 71 per year; histories of up to 194 rows | the manual's matrices by year range | `BODY_TYP` and `PBODYTYP` (similar, not identical) | yes, recorded in histories (§5.4) |
| FARS, BRFSS | states (FIPS) | 52 | inline, from an outside standard | each dataset's state variable | each dataset uses a different subset (49 codes in common) |
| NSFG, CPS, ANES, YRBSS | small scales | at most 36 | inline in the codebook, or SAS formats | a few (NSFG `RELIGION` in 3 tables) | — |

What the numbers say:
- **GSS release 7224r3a:**
  - 54 records list 100 or more valid codes, 18,654 entries in all, but there are only 15 distinct lists.
  - Variables that share a list differ in their missing codes: `occ10` has `.i .n .s .u` and `paocc10` has `.d .i .n .u`. A shared list holds valid codes; missing codes stay per variable.
  - Storing each repeated list once would save 1.0 MB of the 21.4 MB records (5%) for lists of 100 or more codes, or 2.1 MB (10%) for every repeated list. **Size isn't the reason to change.**
- **The reasons:**
  - Information about a list has one place to go: its source (the Census classification), retired codes, a correction, a change between releases.
  - A list the publisher puts out separately keeps its own columns.
- **Near-duplicates stay separate.** `kdocc10`'s labels differ from `occ10`'s only by double spaces in gssrdoc, so verbatim text makes them two lists. A layout rule (§3, rule 3) could merge them; the build decides, and records the rule.

## Options

### A. Copied inline (now)

Each record lists every code. Every tool works. A list's source, a retired flag, or a correction has to be repeated in each record that copies it, and a separately published list's extra columns are lost or squeezed into labels. Chicago's `crimes/iucr` labels already join two columns by a named rule.

### B. A reference from a variable to a code-list *table*

The list is a table in the release (as Chicago's `iucr` is now). A variable names it, with its code and label columns: `"codes_from": {"table": "iucr", "code": "iucr", "label": ["primary_description", "secondary_description"]}`. The codes themselves are the table's **rows**, in the common-format data file.

What breaks: **the codes live in `data/`**, which is gitignored and may be `build-only` under the terms, while metadata often ships. So:
- metadata would no longer be self-contained;
- C1 can't validate a list it can't see;
- views, export, diff and search would all need the data files;
- a list's documentation (source, retired, corrections) would have nowhere to go.

Joins in the data are what tables and `references` are for, and they already work: C12 checks every 2024 IUCR code against the list. B is the wrong place for metadata.

### C. A code-list file in `metadata/`, referenced from records (recommended)

`metadata/code_lists.jsonl`, one line per list. Each line has the list's `id`, `label`, `origin` and the publisher's codes: each a value as in §4.2 (`code`, `kind`, usually `label`), optionally `retired` and `waves`, and optionally `attributes`, the list's other columns. A record names its list in `code_list`, and keeps its own codes, usually the missing ones, in `values`.

The library expands the list when it loads a repo. Every module reads records through `Repo.load` (`check`, `views`, `site`, `export`, `diff`, `extract`, `release` and `search`), so one expansion there gives every tool the full `values`. Records on disk stay small, and nothing downstream sees a difference unless it asks.

### D. A shared codes file per release

Like C, but `metadata/releases/<release>/code_lists.jsonl`. A list that doesn't change between releases (the Census 2010 occupations in both GSS releases) would then be copied once per release. That's better than once per variable, but C with an id per version of a list does the same thing, and keeps one place for a list that spans releases. If the coordinator prefers per-release files, C's format carries over unchanged.

## What each option needs from the library

| | A (now) | B (table reference) | C (code-list file) |
|---|---|---|---|
| `pdt check` | as now | C4 and C12 need the data; C1 can't see the list | C1 validates `code_lists.jsonl`. C2: ids unique, a record's `code_list` exists, codes unique within a list, and no code in both a list and the record's `values`. C4, C6 and C7 run on expanded records |
| Data identity (`pdt.release`) | as now | the list is data | the data file's identity adds `code_lists_sha256`, as it has `corrections_sha256`, so C3–C5's stale-file test sees a changed list |
| Views and site | as now | need the data files | a record shows "codes: *Census 2010 occupations* (540)" with a link; one page per list; one agent shard for lists. Search still finds a variable by a code's label, through the expanded record |
| Export (data-dict) | as now | data-dict relationships only | expands as now (the export doesn't share enums); LOSSES counts `shared_code_lists` |
| `pdt diff` | per variable | needs both releases' data | per variable on expanded values as now, plus each pair of lists compared once. The same content under a new id isn't a change |
| extract | as now | needs the data | none: it uses expanded records |
| Corrections (§5.3) | by `/values/N` in each record | nowhere to target | a target can be a list: `{"code_list": "iucr", "field": "/codes/12/label"}`, applied once for every variable that uses it |
| Builds | as now | as now | a build writes the list once, and gives each record `code_list` plus its own missing codes |

## Retired codes

| Option | What it says | Where it fits | Problem |
|---|---|---|---|
| `retired: true` on a code | the publisher marks it retired (Chicago's `ACTIVE` false) | a cumulative release whose data still has the code | when it was retired isn't recorded |
| `waves: {from, to}` on a code | when the publisher says it's in use | when the publisher gives dates or years | few publishers do |
| availability per code (counts by wave) | when it occurs in the data | — | that's a fact about the data, not what the publisher says. Counts belong in `n` (one release) or a derived property |
| histories only (§5.4) | the publisher's matrix by period | FARS, whose manual prints it | no help for a single cumulative release (Chicago, ANES CDF), which has no periods |

**Recommendation: both optional fields, on list entries and on inline values alike.**
- `retired: true` records the publisher's flag as published.
- `waves`, the same span as in histories, is added when the publisher gives one.
- A retired code stays `kind: valid`, because data from earlier years still uses it.
- Histories stay as they are for publishers that document periods. A history can generate `waves` for a code, but needn't.

## Recommendation

1. **Keep inline `values` as the default.** A list goes in `code_lists.jsonl` when the publisher publishes it separately (Chicago IUCR), or when it's shared by several variables (GSS occupations and industries, ISCO). The build decides, and only identical lists are shared.
2. **The list file holds valid codes,** plus the publisher's own extra columns as `attributes`. Missing codes stay in each record's `values`, since they differ per variable. A list may include missing codes when the publisher's list does.
3. **A list's id names its version** (`census-occ-2010`, `iucr-20261119`). A changed list is a new id, and records in each release name the one they use.
4. **Retired codes:** `retired` and `waves`, as above.
5. **Code-list tables stay for the data:** Chicago keeps its `iucr` table and the reference, for joins and C12. The table and the list are built from the same source.
6. **Library work** (a follow-up task): the expansion in `Repo.load`; the C1, C2 and C7 changes; `code_lists_sha256` in the data identity; the views, site, diff and export changes in the table above. Tests: one list shared by two records with different missing codes; a correction to a list; a code in both a list and `values` (C2 fails); a stale data file after a list changes.
7. **First uses:** Chicago IUCR (a list of 434 with `retired` and `attributes`), and the GSS occupation and industry lists (13 lists of 100 or more codes) once blue's Task 26 is done.

## The changes, for the coordinator to apply

### STANDARD.md

In §2's layout, after `histories.jsonl`:

```diff
     histories.jsonl                      code histories (optional)    schema/history.schema.json
+    code_lists.jsonl                     shared code lists (optional) schema/code_list.schema.json
```

In §4.1's table, after `values`:

```diff
 | `values` | Every documented code, valid and missing, in the publisher's order (§4.2) |
+| `code_list` | The id of a shared code list (§4.5) whose codes come before `values`' own |
```

In §4.2, after "Codes are stored as they appear in the data file...":

```diff
+**Retired codes.** A code the publisher has retired but that still occurs in earlier data stays `valid`, with `retired: true` as the publisher marks it, and `waves` (`{from, to}`) when the publisher says when it was in use.
```

A new §4.5, after §4.4:

```diff
+### 4.5 Shared code lists
+
+When the publisher publishes a list of codes separately (Chicago's IUCR codes), or one list serves several variables (GSS occupation codes for the respondent, spouse, father and mother), the list is stored once in `metadata/code_lists.jsonl` and each record names it in `code_list`. A list has an `id`, which names its version (`census-occ-2010`), a `label`, an `origin`, and its `codes`, each a value as in §4.2 (`code`, `kind`, usually `label`). A code can also have `retired`, `waves`, and `attributes` for the list's other columns. The record's own `values` hold its other codes, usually the missing ones, which differ from variable to variable. A code can't be in both.
+
+The library expands a record's list when it loads a repo, so every check and view sees the full set of codes. Only identical lists are shared; a list that changes is a new list with a new id. A list published as a table of data can also be a table in the release (§2.1) for joins in the data; the code list is its metadata.
```

In §5.3, the target:

```diff
-- the target: variable name, a JSON Pointer to the field (`/questions/0/text`), and optionally the releases;
+- the target: variable name, or a shared code list's id (§4.5), a JSON Pointer to the field (`/questions/0/text`, `/codes/12/label`), and optionally the releases;
```

In §9, C2:

```diff
-| C2 | Ids are unique: (release, name) for variables, `id` for groups and corrections. Every reference resolves: group members, link ends, correction and annotation targets, source ids, release ids | | fail |
+| C2 | Ids are unique: (release, name) for variables, `id` for groups, corrections and code lists. Every reference resolves: group members, link ends, correction and annotation targets, source ids, release ids, a record's `code_list`. A code is in a record's list or its `values`, not both | | fail |
```

In §10, replace the last sentence of the Tables item:

```diff
-Whether `references` are enough to describe code-list tables, such as FARS's or a city portal's, is untested.
+Code-list tables (Chicago's IUCR) work for joins in the data; their codes as metadata are shared code lists (§4.5), which are new and so far designed, not built.
```

### schema/code_list.schema.json (new)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/AllenDowney/PublicDataToolkit/schema/code_list.schema.json",
  "title": "Code list",
  "description": "A list of codes shared by several variables, or published separately by the publisher. One per line in metadata/code_lists.jsonl. Optional (STANDARD.md §4.5).",
  "type": "object",
  "properties": {
    "id": { "description": "Unique; names the list's version, e.g. census-occ-2010, iucr-20261119.", "$ref": "common.schema.json#/$defs/id" },
    "label": { "type": "string" },
    "description": { "type": "string" },
    "codes": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "variable.schema.json#/$defs/value" }
    },
    "columns": {
      "description": "The publisher's other columns, carried in each code's attributes: name -> description.",
      "type": "object",
      "additionalProperties": { "type": "string" }
    },
    "origin": { "$ref": "common.schema.json#/$defs/origin" },
    "source_location": { "$ref": "variable.schema.json#/properties/source_location" },
    "note": { "type": "string" }
  },
  "required": ["id", "label", "codes", "origin"],
  "additionalProperties": false
}
```

### schema/variable.schema.json

```diff
     "values": { ... },
+    "code_list": {
+      "description": "Id of a shared code list in metadata/code_lists.jsonl (STANDARD.md §4.5). Its codes come before this record's own values.",
+      "$ref": "common.schema.json#/$defs/id"
+    },
```

In `$defs.value.properties`, after `n`:

```diff
+        "retired": {
+          "description": "The publisher marks the code retired; it may still occur in earlier data, so it stays valid.",
+          "type": "boolean"
+        },
+        "waves": {
+          "description": "When the publisher says the code is in use: {from, to}, in the dataset's wave units.",
+          "type": "object",
+          "properties": { "from": { "$ref": "common.schema.json#/$defs/wave" }, "to": { "$ref": "common.schema.json#/$defs/wave" } },
+          "required": ["from"],
+          "additionalProperties": false
+        },
+        "attributes": {
+          "description": "The publisher's other columns for this code, in a shared code list (e.g. IUCR's index_code).",
+          "type": "object"
+        },
```

### schema/correction.schema.json

```diff
     "target": {
       "properties": {
         "name": { ... },
+        "code_list": { "description": "A shared code list's id (STANDARD.md §4.5), instead of a variable name.", "$ref": "common.schema.json#/$defs/id" },
         ...
       },
-      "required": ["name", "field"],
+      "required": ["field"],
+      "oneOf": [{ "required": ["name"] }, { "required": ["code_list"] }],
```

## Not decided here

- **Lists from outside standards** (FIPS states, Census occupations) used by several datasets could live in a shared repo and be referenced across datasets. That's not needed yet. FARS and BRFSS use different subsets of the state codes, so each dataset keeps its own list.
- **FARS's histories** could generate per-release code lists. Their lists are per variable and not shared, so there's no gain yet.

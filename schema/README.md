# Schemas

JSON Schemas (draft 2020-12) for the files in a dataset repository. What the fields mean, and the rules the schemas can't express, are in [`../STANDARD.md`](../STANDARD.md).

| Schema | Validates | STANDARD.md |
|---|---|---|
| [`common.schema.json`](common.schema.json) | shared types: ids, codes, waves, missing types, origins, extensions | §3, §4.2 |
| [`dataset.schema.json`](dataset.schema.json) | `dataset.yaml` | §2.1, §8 |
| [`sources.schema.json`](sources.schema.json) | `sources.yaml` | §2.2 |
| [`variable.schema.json`](variable.schema.json) | each line of `metadata/releases/<release>/variables.jsonl` | §4 |
| [`group.schema.json`](group.schema.json) | each line of `metadata/groups.jsonl` | §5.1 |
| [`link.schema.json`](link.schema.json) | each line of `metadata/links.jsonl` | §5.2 |
| [`correction.schema.json`](correction.schema.json) | each line of `metadata/corrections.jsonl` | §5.3 |
| [`derived.schema.json`](derived.schema.json) | each line of `metadata/derived/*.jsonl` | §6 |
| [`annotation.schema.json`](annotation.schema.json) | each line of `metadata/annotations/*.jsonl` | §6 |

## Examples

[`examples/`](examples/) has a few real records, abbreviated, for checking the schemas against real cases:

- `gss/`: `abany` and `racopen`, the abortion battery, a link across releases, the `racopen` and `racfew` corrections, two annotations and a scale signature. Metadata from gssrdoc via CultureWar's extracted JSON.
- `anes-cdf/`: `VCF0803` (wording that varies by year, a DK code the codebook lists as valid) and `VCF0218` (a top-coded thermometer). From the ANES CDF HTML codebook.

Availability lists are shortened to a few entries. The GSS terms in `gss/dataset.yaml` are `unknown` because they haven't been reviewed.

To validate them (needs `jsonschema` 4.18+ and PyYAML):

```bash
python schema/check_examples.py
```

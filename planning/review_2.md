# Review 2: the missing-codes design

**Received:** 2026-11-19, on [`missing_codes_design.md`](missing_codes_design.md). **Verdict:** accept Option A (one parquet file with `__code` columns), make a few refinements, and move on to implementation rather than exploring more layouts. "The common data format is arguably more important to the long-term success of PublicDataToolkit than the agent interface."

## 1. Agreements (no change)

- Option A; parquet; codes as strings; exact round trip as a test.
- Publisher-valid DK codes stay in the value column. The reviewer wants this as a firm principle of the standard. It already is for the metadata (STANDARD.md §4.2: a code's kind follows the publisher), and the data format inherits it.
- CSV only as an optional export, generated from the parquet file.
- Keep the publisher's original files in the release.

## 2. Refinements

| # | Suggestion | Current state | Proposed response |
|---|---|---|---|
| 1 | **Codes are representations, not original types.** Say so, and say how unusual codes are written (string-valued missing codes) | The design says codes are strings "exactly as in the metadata"; nothing on types or escaping | **Specify:** the code column holds the metadata's `code`, written as text (integers without a decimal point, strings as they are). Null means "no code"; an empty string is a code. Parquet tells the two apart, so nothing needs escaping. Reconstructing the original type uses the variable's `storage_type` and the publisher's format, and the round-trip test covers it |
| 2 | **Unresolved isn't a kind of missing.** Don't let recoding treat it like DK; warn | STANDARD §4.2: the library leaves unresolved codes alone unless told otherwise. No warning yet | **Add:** recoding by missing type never touches unresolved codes, and the library warns when a selected variable has any. Handling them needs an explicit option |
| 3 | **A publisher can change its classification between releases** | Records are per release, so each release has its own classification | **State it in the standard:** a release's data is always read with that release's metadata; classification follows the publisher of that release |
| 4 | **Semantic round trip: tie the data file to the exact metadata used to build it** | File-level metadata has dataset, release, standard version, and the publisher file's SHA-256 | **Add:** the SHA-256 of the `variables.jsonl` used, and the dataset repo's commit. The library warns when the metadata it's given doesn't match |
| 5 | **Missing codes in dimension columns** (year, ballot) | Not addressed. They occur: GSS `ballot` is `.i` in 21,875 rows, every year before 1988 | **Specify:** dimension columns are ordinary variables with value and code columns. Availability uses the value column; a row with a code there has no form |
| 6 | **Three tests before freezing the format:** full datasets; cross-language (pandas, R, DuckDB); metadata evolution | Round trip on two slices only | Full-file round trip for the GSS and ANES (MTF later); a metadata-evolution test in the library tests. The cross-language test needs R with `arrow`, and DuckDB, neither installed here |

## 3. Decisions

Allen, 2026-11-19:
- **All five refinements adopted.** They're in [`missing_codes_design.md`](missing_codes_design.md) §4, STANDARD.md §4.2 and §8, the library (`lib/pdt/data.py`) and `pdt check` (reserved names). For refinement 4, the file records the metadata's SHA-256 but not the repo commit: the checksum identifies the metadata exactly, and a commit can change without the metadata changing.
- **All three tests run.** Results are in the design doc §9.
  - Cross-language: pandas, Polars, DuckDB, R arrow and R DuckDB read the GSS and ANES slices identically.
  - Metadata evolution: a library test.
  - Full files: GSS, ANES and the NSFG female respondent file.

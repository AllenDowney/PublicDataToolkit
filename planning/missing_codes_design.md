# Keeping missing-value codes in a common data format

**Status:** accepted, November 2026: Option A in parquet, with five refinements from the first review (§4, marked *Added after review*). Results of the tests run before adopting it are in §9. The questions in §8 remain open for further comment, as GitHub issues on this repository.

## 1. Context

[PublicDataToolkit](../PROPOSAL.md) builds one repository per public dataset (the General Social Survey, the American National Election Studies, and so on), to a common [standard](../STANDARD.md). When the publisher's terms allow it, a dataset repository publishes the data as a GitHub release containing two things:

- the publisher's original files, unchanged, so anyone can verify them;
- the same data in **one common format**, so the shared library, and anyone else, can read every dataset the same way, whatever format the publisher used (Stata, SPSS, SAS, CSV).

This document is about the common format. The hard part is missing values.

## 2. The problem

Survey files record *why* an answer is missing, and the reasons matter to analysts. "Don't know" is a substantive response for some purposes, while "not asked this year" never is. Publishers encode the reasons in different ways:

| Publisher | How "missing" is stored | Example |
|---|---|---|
| GSS (NORC), Stata file | Stata extended missing values | `abany`: `.d` don't know, `.i` inapplicable, `.n` no answer, `.s` skipped on web, `.y` not asked this year |
| ANES, Stata file | Ordinary numbers, plus Stata's system missing | VCF0218 (a 0–100 thermometer): `98` DK, `99` NA; INAP ("question not used") is `.` |
| ANES | Some DK-like codes are **valid** by the publisher's own classification | VCF0803 (liberal–conservative scale): `9` "DK; haven't thought much about it" is listed under Valid, because a follow-up item depends on it |
| ANES | Codes the codebook doesn't document at all | VCF9236 (death penalty): `-1` occurs 245 times and isn't listed |

The metadata records for each variable already say which codes are valid, which are missing (and why, using types such as `dk`, `refused`, `inap`, `not_asked`), and which are `unresolved` because the documentation doesn't say ([STANDARD.md](../STANDARD.md) §4.2). The question is how the *data* should carry those codes.

The common approach, reading the file and turning every missing code into one null (`NaN`), is what we're trying to fix. It's what the existing code this project grew out of did, and it makes "don't know" indistinguishable from "not asked."

In cumulative survey files, missing isn't the exception. In 45 GSS variables and 32 ANES variables, **about 40% of all cells are missing codes**, mostly because most questions aren't asked every year.

## 3. Requirements

1. **No information lost.** Every code comes back exactly: `.d` vs `.i`, `98` vs `99` vs `.`. A test proves it by rebuilding the publisher's values from the common format and comparing them cell by cell.
2. **Ready to analyze without our library.** Opened in pandas, R, Polars or DuckDB, a variable's values are its valid answers, with nulls everywhere else.
3. **Recoding by type is easy.** For example: "treat DK as its own category, and everything else as null."
4. **Generic.** The shared library can check the data against the metadata for any dataset: every code that occurs is documented, and every documented year has answers.
5. **Simple to explain.**

## 4. What all the options share

- **Value columns.** Each variable has a column holding its valid answers, typed as in the metadata (integer, float, string, date). It is null wherever the answer is missing or unresolved. Codes the publisher lists as valid stay, even when they look like DK (ANES VCF0803 code 9). Changing that would be an analysis decision, and the standard leaves those to users.
- **Codes are written as strings, exactly as in the metadata:** `".d"`, `"98"`, `"."`, `"-1"`. One spelling for every publisher means a code can be looked up in the metadata, which gives its label and its missing types.
- *Added after review:* **a code is a representation, not the original value.** The code column holds the metadata's `code` as text: integers without a decimal point, other numbers in their shortest form, strings as they are. `"98"` in a code column isn't the integer 98. Rebuilding the publisher's original cell uses the variable's metadata: a code the metadata lists as a number becomes that number, and in a numeric variable, any other code is the publisher's own token (such as Stata's `.d`). Null means "no code"; an empty string is a code, and parquet tells the two apart, so nothing needs escaping.
- **Unresolved codes**, such as ANES `-1`, are kept as codes, not values, so nobody mistakes `-1` for an answer.
- *Added after review:* **unresolved isn't a kind of missing.** Recoding by missing type never touches an unresolved code, because nobody knows what it means. The library warns when a variable has any, and handling them takes an explicit option.
- *Added after review:* **each release is read with its own metadata.** A publisher can classify a code as valid in one release and missing in the next. Records are per release, so the data file for a release is always split, and read, with that release's metadata.
- **A `_row` column** numbers the rows, in the publisher's file order.
- **File-level metadata** records the dataset, the release, the version of the standard, and the SHA-256 of the publisher's file it came from. *Added after review:* it also records the SHA-256 of the metadata file (`variables.jsonl`) the split was made with, and the library warns when it's given different metadata. It also lists, per variable, which code texts were the publisher's own tokens (Stata's `.d`) rather than ordinary values the metadata calls missing (the ANES's 98); rebuilding uses that list instead of guessing. Without this, an old data file read with newer metadata could quietly be interpreted differently.
- **Converting is generic.** Each dataset repository supplies only a reader, which turns the publisher's file into a table where every cell is either a value or a code string. A library function splits that table into values and codes using the metadata. The logic that decides what counts as missing lives in one place.
- **Dimension columns.** `dataset.yaml` names the columns that identify the wave and the form (`wave: {column: year}`, `form: {column: ballot, codes: {1: A, 2: B, 3: C, 4: D}}`), so availability can be checked against the data the same way for every dataset. *Added after review:* dimension columns are ordinary variables, with code columns when they have codes. They do: the GSS `ballot` is `.i` (not applicable) in 21,875 rows, every year before 1988. Availability uses the value column, so a row with a code there has no form.

## 5. The options

### Option A: code columns in the same file

Each variable with any missing codes gets a second column, `<name>__code`, next to its value column. It is null where the answer is valid.

```text
gss_7224r3a.parquet

_row  year  ballot  abany  abany__code
0     1972  null    1      null
1     1972  null    null   .d
2     1988  1       2      null
3     1988  2       null   .i
```

- **For:** one self-contained file; select `abany` alone for clean data, or both columns for the reasons.
- **Against:** about twice as many columns: 87 instead of 45 for the GSS slice. The full GSS cumulative file has about 6,900 variables. Real variable names must not end in `__code`, which `pdt check` would enforce.

### Option B: a separate file of codes

`values.parquet` holds the value columns. `codes.parquet` has the same rows and the same column names, holding only codes. The two join on `_row`.

```text
gss_7224r3a.values.parquet      gss_7224r3a.codes.parquet

_row  year  abany               _row  year  abany
0     1972  1                   0     null  null
1     1972  null                1     null  .d
2     1988  2                   2     null  null
3     1988  null                3     null  .i
```

- **For:** the values file is a clean analysis table, and nobody sees codes unless they ask for them.
- **Against:** two files that must stay aligned. Anyone who filters or sorts one has to join on `_row` to use the other.

### Option C: a long table of missing cells

`values.parquet` as in B, plus `missing.parquet` with one row per missing cell: `_row`, `variable`, `code`.

```text
gss_7224r3a.missing.parquet

_row  variable  code
1     abany     .d
3     abany     .i
```

- **For:** stores only the missing cells, and it's easy to count codes by variable.
- **Against:** using the codes needs a join and a pivot. In cumulative files 40% of cells are missing, so the long table has millions of rows (3.2 million for the 45-variable GSS slice) and ends up the largest option.

### Options not pursued

- **A struct column per variable** (`{value, code}`): neat in Arrow, but awkward in pandas, R and spreadsheets.
- **Keeping the publisher's encodings** (Stata `.d` in some datasets, numbers like 98 in others): that is exactly the inconsistency the common format exists to remove.
- **Recoding missing values to reserved numbers** (for example, −1 for DK): they collide with real codes, as ANES `-1` shows, and they turn missing data into fake numbers.

### Measurements

The GSS slice is 45 variables from the 1972–2024 cumulative file (75,699 rows). The ANES slice is 32 variables from the Time Series Cumulative Data File (73,745 rows). Sizes are parquet with default (snappy) compression.

| | GSS slice | ANES slice |
|---|---|---|
| Variables with a code column | 42 of 45 | 29 of 32 |
| Cells that are missing codes | 40.3% | 40.8% |
| **A:** one file | **2.2 MB** | **1.7 MB** |
| **B:** values + codes | 2.7 MB (values alone 1.8 MB) | 2.2 MB (values alone 1.6 MB) |
| **C:** values + long table | 2.9 MB (3.2 million missing-cell rows) | 2.5 MB (2.1 million rows) |
| Round trip back to the publisher's values | exact | exact |

The round-trip test reads the publisher's Stata file, splits it into values and codes, rebuilds the original cells from them, and compares every cell.

## 6. Container format

Parquet is the obvious candidate, but it isn't the only one. The same Option A table, stored three ways:

| | Parquet | Arrow IPC (Feather), zstd | CSV, gzipped |
|---|---|---|---|
| GSS slice | 2.2 MB | 2.3 MB | 2.2 MB |
| ANES slice | 1.7 MB | 1.3 MB | 1.5 MB |
| Read one column (GSS slice) | 3 ms | (not measured) | 53 ms, whole file parsed |
| Keeps types (integer with nulls, categorical codes) | yes | yes | no; every reader re-guesses |
| Reads only the columns asked for | yes | yes | no |
| Readable in R, Python, Julia, DuckDB, Spark | yes | yes | yes, plus spreadsheets |
| Readable in a spreadsheet | no | no | yes |
| Read by data-dict's `validate-data` | yes (its only source today) | no | no |
| Long-term archival use | widely used | mainly in-memory and interchange | universal |

Size doesn't decide it. On these slices the three formats are within about a third of each other, and none is smallest on both. What favors parquet:
- **Column selection.** A full cumulative file has thousands of variables and most analyses use a few dozen.
- **Types survive.** No reader has to guess whether a column of codes is a number.
- **data-dict compatibility.** Each repository also exports a [data-dict](https://data-dict.tidyverse.org/) description, and data-dict validates parquet.

CSV's advantage is that anyone can open it. Other candidates, such as a DuckDB or SQLite database file, are convenient but tie users to one tool.

## 7. Recommendation

**Option A in parquet:** one file per release, with `<name>__code` columns next to the value columns. A gzipped CSV of the same table could be added to a release later if spreadsheet users ask for it.

Option A is the smallest and is self-contained. Its clean view is one column selection away, and it needs no joins. Its cost, the doubled column count, matters little in a columnar format, where unused columns aren't read.

With Option A, recoding by type is short. With the library as built ([`lib/pdt/data.py`](../lib/pdt/data.py)):

```python
from pdt.data import read, recode

table = read("gss_7224r3a.parquet", columns=["year", "abany", "abany__code"])

# Without the library: the reasons are right there.
table["abany__code"].value_counts()       # .i 32,507  .d 1,434  .n 311  .s 49

# With it: recode by missing type, using the variable's record.
abany = recode(table, records["abany"], dk="DK")   # DK becomes its own category; other missing stay null
```

## 8. Questions for reviewers

1. **Layout.** Is Option A the right default, or would B's clean values file serve users better?
2. **Container.** Is parquet the right choice? Should a release also include CSV?
3. **Code spelling.** Is one string spelling for every publisher's codes (`".d"`, `"98"`, `"."`) right, or should the code column keep the publisher's type, with numbers as numbers?
4. **Publisher-valid DK codes.** We keep codes the publisher lists as valid (ANES VCF0803 code 9) in the value column. Should the common format move them to the code column instead, or is that an analysis decision, as we think?
5. **Prior art.** haven's `tagged_na()` and `labelled_spss(na_values=)` in R, SAS special missing values `.A`–`.Z`, SPSS user-missing values, and Frictionless Table Schema's `missingValues` all handle parts of this. Is there an established convention for typed missing values in columnar formats that we should follow instead?
6. **What's missing.** Is anything an analyst would need that this design drops?

## 9. Tests run before adopting the format

The first review asked for three tests before the format is treated as stable. The library code is [`lib/pdt/data.py`](../lib/pdt/data.py), and its tests are in [`lib/tests/test_data.py`](../lib/tests/test_data.py).

1. **Cross-language.** Both slices, written by the library, were read five ways: pandas; Polars; DuckDB from Python; R with `arrow`; and R with `duckdb`. Each reader computed, for every column, the number of non-null values and the sum, and for every code column, the count of each code. All five agree on every column: 88 columns for the GSS slice and 62 for the ANES slice.
2. **Metadata evolution.** A library test builds a file with one release's metadata, in which code 9 is valid. It then reclassifies 9 as DK in newer metadata. The old file still holds 9 as a value and still round-trips exactly with its own metadata. The library warns when the file is read with the newer metadata, and splitting the data again with the newer metadata moves 9 to the code column.
3. **Full files.** Every variable of three whole files was split, written to parquet, read back, rebuilt, and compared with the publisher's file cell by cell. Every cell came back exactly:

   | File | Variables | Rows | Mismatched cells | Parquet | Publisher's file | Cells that are codes |
   |---|---|---|---|---|---|---|
   | GSS 1972–2024, release 3a | 6,943 | 75,699 | 0 | 47.8 MB | 45.3 MB, Stata, gzipped | 93.2% |
   | ANES Time Series CDF, 2026-02-05 | 1,030 | 73,745 | 0 | 15.5 MB | 30.9 MB, Stata, gzipped | 68.3% |
   | NSFG 2022–2023, female respondents | 1,912 | 5,586 | 0 | 5.4 MB | 86.4 MB, SAS | 60.5% |

   Notes on the table:
   - Only the slice variables have metadata records yet (50 GSS, 37 ANES, 23 NSFG). For the other variables, only the publisher's own tokens (Stata's `.d`, SAS and Stata system missing) became codes, and the ANES's numeric missing codes such as 98 stayed values. So the ANES and NSFG "codes" columns undercount, and the GSS figure, where nearly every missing code is a token, is close to final.
   - The GSS parquet was written in 12 chunks of columns, so its size is the sum of the chunk files.
   - In a cumulative file like the GSS, nearly every cell is a code: most questions were asked in a few years, or on some ballots only.
   - The GSS data file has 6,943 variables; gssrdoc documents 6,904.
4. **An independent code review** of the library, by a reviewer given the code and this spec but not our reasoning, found five bugs, all now fixed with regression tests:
   - a string variable lost its publisher tokens in the round trip, or gained tokens it never had;
   - codes were matched by their text alone, so the string `"98"` collided with the code 98, and `True` with code 1;
   - float32 columns missed non-integer codes such as 0.1;
   - whole numbers beyond the 64-bit integer range, and columns of mixed types, crashed the conversion.

   The fixes match codes by type and value, record the publisher's tokens in the file, and refuse the one case the format can't represent: a publisher token and an ordinary value with the same text in one variable. The review also led to a stricter rule for codes with several types: GSS `.m` ("dk, na, iap") is recoded only when all three types are given the same replacement, because the code alone doesn't say which one applies.

---
name: from-data-labels
description: Read variable labels, value labels and missing-value markers from a data file itself (Stata .dta, SAS .sas7bdat, CSV with label columns) for PublicDataToolkit records, and use them to check every other source. Covers reading without losing extended missing values, encodings, and label columns.
---

# From the data file's own labels

Every build reads the data file. It is the authority for what exists: names, codes that occur, years with data. It is often the best source for one release's labels too. Its labels go in with `origin: data_file` (STANDARD.md §3). Read with pandas' public API, or with pyreadstat where pandas gets the format wrong (SAS transport, below).

## Reading each format

**Stata** (GSS, ANES):

```python
with pd.io.stata.StataReader(path) as reader:
    var_labels = reader.variable_labels()
    value_labels = reader.value_labels()
frame = pd.read_stata(path, columns=names, convert_missing=True, convert_categoricals=False)
```

- `convert_missing=True` keeps extended missing values (`.d`, `.i`, ...) as `StataMissingValue` objects. Without it they all become NaN, and you can't tell DK from INAP. Get the code with `value.string`.
- `convert_categoricals=False` keeps the codes, not the labels.
- `pd.read_stata` reads `.dta.gz` directly.

**SAS** (NSFG):

```python
frame = pd.read_sas(path, format="sas7bdat", encoding="latin-1")
```

- `.sas7bdat` has no value labels; those are in a separate formats catalog, or only in the codebook.
- SAS system missing reads as NaN.
- Column names may differ in case from the codebook (`CaseID` vs `CASEID`; `agepreg` vs `AGEPREG`).

**SAS transport, `.xpt`** (NHANES):

```python
import pyreadstat
frame, meta = pyreadstat.read_xport(path, encoding="latin1")
```

- Use pyreadstat, not `pd.read_sas(path, format="xport")`. pandas turns an exact zero into `5.397605346934028e-79` (an underflow in its conversion of IBM floating point). In NHANES that looked like an undocumented code in 20 variables, and it broke every count of the code 0.
- An `.xpt` file has variable labels but no value labels; the codebook has those.
- SAS missing reads as NaN.

**CSV with label columns** (FARS):

- Read with `encoding="latin-1"`.
- Most coded columns `X` come with a label column `XNAME` holding each row's label. Count (code, label) pairs to get the data's value labels for this release.
- Label columns aren't variables. Leave them out of coverage counts: FARS's 2024 accident file has 80 columns, 46 without the NAME columns.

## What to take from the data

| Fact | Use |
|---|---|
| Column names | Coverage (C3) against the documentation, both ways |
| Variable labels | `label`, when the documentation's is missing or older |
| Codes that occur, with counts | C4 against `values`; unresolved codes; evidence for corrections |
| Extended missing values that occur, per variable | Which missing codes a variable actually uses |
| Non-missing counts per wave and form | Availability (C5); `n` |
| Value labels for this release | The release's own labels (FARS 2024 "Reported as Unknown", not the manual's 1975–2024 label) |
| Storage type | `storage_type` (integer if every value is whole) |

## Traps we hit

- **Labels that disagree with the documentation**: FARS `DR_DRINK` 1 is "Drinking" in the manual and "Yes" in the data. Compare after removing case, punctuation and year notes, and report what remains (8 codes in FARS).
- **Codes that only the data knows**: the ANES's `-1`, `-8` and `-4` in 2024. They're unresolved until a correction says otherwise.
- **A reader can invent codes.** pandas reads an exact zero in an `.xpt` file as 5.4e-79 (above). When C4 reports a tiny float as an undocumented code, suspect the reader before the codebook.
- **A missing value's meaning isn't in the file.** Stata says `.z` is missing; its label "see codebook" says nothing more. That's `unspecified`.

## Verify

The data file is the check for every other source. If a build reads labels from somewhere else, it still compares them with these.

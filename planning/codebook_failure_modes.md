# What the codebooks trip over

Failure modes we met turning publishers' documentation into variable records, for eight datasets:

- the GSS (through gssrdoc, NORC's PDFs and Stata files);
- the ANES Cumulative Data File (HTML and PDF codebooks, Stata);
- the NSFG 2017–2019 and 2022–2023 (PDF codebooks in two layouts, CAPI questionnaires, SAS and fixed-width data);
- FARS (an 823-page manual, CSV);
- YRBSS (SAS input and format programs, a content document);
- BRFSS (PDF and HTML codebooks, SAS transport files);
- CPS ASEC (PDF data dictionaries, CSV);
- the Chicago crimes table on a Socrata portal.

For each one: what goes wrong, an example, how we detect it, and how we fix it.

Most of these were caught by comparing the documentation with the data file. That's the check we'd recommend first (last section).

## PDF text

All parsed from `pdftotext -layout` output.

| What goes wrong | Example | How we detect it | How we fix it |
|---|---|---|---|
| **Running headers inside an entry.** A page break repeats the section title or the variable's name, and the parser starts a new entry or takes the header as a label | NSFG repeats the variable name after a break; the first parse lost SSMARCOH's label. In BRFSS 2011–2015, a header matched as part of a line made `_LLCPWT`'s label a table row | Labels that look like a count, a table row or a fragment (lower-case start); an entry with no label | Skip a name line equal to the current entry; match running headers as whole lines only |
| **Tables continued on the next page.** The continuation repeats the table's header, and the parser starts a new table and loses codes | FARS: 220 "undocumented" codes (`STATE` 1–22, ...), all parser artifacts | A burst of data codes missing from the documentation | Continue the block when the header repeats |
| **Two-column pages.** `-layout` interleaves the columns line by line | CPS ASEC data dictionaries | Labels mixing two variables' text | Convert each half page separately (`pdftotext -x -W`), and read left column, then right |
| **Margin boxes on the same line as the entry** | NSFG: "Corrected universe for MFLASTP" after 20+ spaces, at column 110 or later | Text after a long run of spaces | Split it off, and keep it as the publisher's own correction |
| **Wrapped labels and values** | NSFG: a label's second line has no value or count. BRFSS 2013 and 2015: the counts are on the wrapped label's last line. BRFSS 2020–2021: a range wraps as "101 -" / "107". FARS: continuation by indentation | Rows with a label but no code, or a code with no count; per-code counts that don't match the data | Join by layout cue (indent, missing count, trailing "-") |
| **Two rows printed on one line** | FARS `PHARM_EV`: code 98 for two periods, labels run together | Two labels joined where a word runs into a capital | Split the cells |
| **An OCR text layer.** Misread names, column numbers, borders and punctuation | NSFG 2017–2019 female Section A: `H1SP{17-17)` for `HISP(17-17)`, "lS" for 15. A table border read as "I" hid `fmarit`'s codes. Fields with the colon dropped | `pdffonts` shows different fonts from the other sections; an entry that yields no codes while the data has values; codebook counts that don't match the data | Accept any characters in the column field and either bracket; tolerate borders; check every code's count against the data |
| **Meaning carried by styling,** which `pdftotext` drops | GSS Release Variables guides: a variable's status is bold, red or struck through | Not visible in the text at all; found by looking at the PDF | Read the PDF's content stream, or transcribe by hand |
| **Values described in words, not codes** | CPS ASEC: "negative amt = income (loss)"; a pair of codes labeled "Min Value"/"Max Value"; "1 = 1 hour ... 99 = 99 hours plus"; a range on the same line as a code ("-1 = Not in poverty universe 1-99,999 = dollar amount"); "Same as PXPAR1" | Data values that aren't listed codes but fall inside the variable's printed range | Turn them into a valid range with the labels kept in a note, and list labeled ends (99 "99 hours plus") as codes too |
| **Rounded or truncated numbers** | NSFG prints ranges rounded ("1170.96-78770.13"). One NSFG weight's range prints "83332.1" in the value column and "83332.13" in the label | A data value just past the printed end | Allow half a unit of the last digit shown, per end |
| **Implied decimals** | CPS ASEC weights: "2 implied decimals (example: 255212=2552.12)"; the files keep the integers | Only from the documentation's note | Record the number of implied places; don't rescale the data |

## HTML codebooks

| What goes wrong | Example | How we detect it | How we fix it |
|---|---|---|---|
| **HTML generated from a PDF keeps the PDF's line breaks** | ANES CDF: question text and notes wrap mid-sentence | Text with hard breaks at page width | Join wrapped lines; keep real structure (a line that's only a year or mode heading starts a new wording) |
| **Several reasons in one missing-code label** | ANES: "NA; no Post IW; form III,IV (1972)" | Labels with ";" | Split at ";" and type each part; report the parts no rule types |
| **Text shared across variables sits outside their blocks** | ANES: the 92 thermometers share a question in a preamble before VCF0201 | Variables with no question text | Read the preamble separately, or say the text is missing |
| **Entities and smart quotes** | "don’t" vs "don't" | Labels that differ only in punctuation | Normalize quotes before comparing |
| **The format changes from year to year** | BRFSS codebooks: one PDF layout for 2011–2015, another for 2016–2021, HTML for 2019, 2022 and 2023 (zipped) | Parsing failures in some years only | One parser per layout, with the same output |

## Spreadsheets

None parsed yet. The only spreadsheet source so far is the PISA codebook (xlsx), not yet built.

## SAS, SPSS and Stata files

| What goes wrong | Example | How we detect it | How we fix it |
|---|---|---|---|
| **Readers collapse distinct missing codes to NaN** | pandas `read_stata` without `convert_missing=True` loses `.d` vs `.i`. pandas' SAS transport reader turns `.A`–`.Z` and `._` into NaN (BRFSS) | Every missing value reads the same | Read with missing codes kept (`convert_missing=True`; a custom XPORT reader) |
| **No value labels in the data file** | `.sas7bdat` has none; they're in a formats catalog or only in the codebook | n/a | Take labels from the formats program or the codebook |
| **A blank is a code** | YRBSS formats label `" "` as "Missing" in one-character text columns | Values that vanish when text is trimmed | Keep `" "` as a string code; don't trim |
| **Fixed-width data with `.` in numeric fields** | YRBSS, laid out by a SAS input program | A Stata-dictionary reader fails on `.` | Read `.` and blank numeric fields as system missing |
| **Name case differs between documentation and data** | NSFG 2022–2023: codebook `CASEID`, data `CaseID`. NSFG 2017–2019: the data file is all lower case, and the codebook writes computed variables in lower case | Names that match only ignoring case | Match ignoring case; store one spelling per release and say which |
| **Format labels are short response labels, not question text** | YRBSS `q59`: "Never had sex", where the questionnaire says "I have never had sexual intercourse" | Labels that read as answers | Treat them as value labels; get question text from the questionnaire |

## What the documentation says about codes

| What goes wrong | Example | How we detect it | How we fix it |
|---|---|---|---|
| **Missing codes aren't marked** | NSFG, FARS, BRFSS and CPS list "Refused", "Don't know", "Not in universe" as ordinary rows | n/a | Type them with a named rule over labels, and record that the type came from the rule |
| **Labels that look missing but are valid** | ANES VCF0803 code 9, "DK; haven't thought much," is listed under Valid; a follow-up item depends on it. CPS A_HGA 0 is "Children" | A label rule would call them missing | Keep the publisher's valid/missing split; type only what the rule is sure of |
| **Codes listed only when they have cases** | NSFG codebooks print no zero rows: none in 26,953 count rows for 2022–2023 | A code present in one release's codebook and absent from the next | Record that the source lists only occurring codes. Before calling a code dropped, check whether its count makes zero plausible (MARSTAT 6 had 2,820 cases: a recode; PREGORDR 15 had 1: chance) |
| **The same missing codes listed for every variable** | gssrdoc lists all twelve `NA(x)` codes for every variable | Codes no data value uses | Take which missing codes a variable uses from the data |
| **Codes only the data knows** | ANES 2024: −1 in 26 variables, for the same 245 respondents; −8 in thermometers, where DK is 98 elsewhere. BRFSS `IYEAR`: interviews dated the next year (18,650 dated 2020 in the 2019 file), which the codebook doesn't list | Data codes missing from the documentation | Mark them unresolved; correct them only with evidence, and report them upstream |
| **A missing code with no reason** | GSS `.z`, "see codebook" | n/a | A missing type for "unspecified" |
| **The upstream package documents another release** | gssrdoc 0.8.2's names and 2024 counts were Release 2's, not 3a's (racopen 462 vs 981) | Per-year counts that differ from the data in one year only | Pin the package; record which release it documents |
| **Systemic text artifacts** | gssrdoc doubles every apostrophe ("DON''T") in 239 variables | One pattern in many fields | One named rule, not hundreds of corrections |

## Across releases

| What goes wrong | Example | How we detect it | How we fix it |
|---|---|---|---|
| **Items renumbered, text unchanged** | NSFG male RELDLIFE: JB-9 → JB-7. YRBSS renumbers every question in each combined release | Item references differ while the text is identical | Compare text with references removed; keep the number per wording |
| **Same name, different item** | YRBSS `q26`: "Considered suicide" in the 2021 file, "Sad or hopeless" in 2023 | Pairing by name reports a reworded question | Pair releases by the publisher's crosswalk first, by name last |
| **Same name, narrower meaning** | NSFG EVRMARRY: "Whether R was ever married" → "Ever married to an opposite-sex spouse" | The variable label changes, the codes don't | Compare variable labels and universes, not only codes and question text |
| **Code changes for the same answer, or meaning changes for the same code** | FARS `WEATHER` "Unknown" is 9, then 99; `LGT_COND` 9 is "Unknown", then "Reported as Unknown". CPS FPOVCUT "not in universe" is 0, then −1. NSFG MARSTAT 1–6 becomes 1–3 | Per-code comparison of two releases | A code history from the publisher's multi-year table, or a codes_changed link |
| **A change inside a period, only in a label's note** | FARS "Unknown/Reported as Unknown (Since 2018)" | Labels with "(Since Y)" | Read the note as a change in year Y |
| **Cosmetic differences** | Case (NSFG 2017–2019 prints recode labels in capitals); reworded count labels ("15 years" → "15", "1ST BIRTH" → "1"); show-card numbers ("Card 79" → "Card 77") | Differences that disappear after normalizing | Normalize case, spacing and references before comparing, and say what was normalized |
| **Names change within one element** | FARS `HARM_EV` 2005–2009 → `PHARM_EV` 2010 on | A SAS Name field spanning several lines with years | Read every line; keep each name with its years |
| **Collection year vs reference year** | CPS ASEC 2024 reports 2023 income. BRFSS files include early-next-year interviews | Year variables with values outside the file's year | Record the reference period separately from the release |
| **A cumulative file folds earlier wordings in** | YRBSS 2023 `q43` includes the 2017 wording but not the 1991–2015 item | Visible only in which years have data | Assign earlier wordings by checking the data, and say so |
| **The file format changes** | CPS ASEC: separate household, family and person CSVs from 2019; before that, one hierarchical fixed-width file | n/a | Start where the format holds, or add a reader per format |

## Errors in the publisher's documentation

Found by the checks above, and confirmed against a second source before being recorded as corrections:

- **ANES CDF:** Sources lists omit years that have data (VCF0104, VCF0128 and VCF0301 for 1954; VCF0830 for 2012; VCF0704 and VCF0878 for 2016). VCF0878 is coded 1/2 in 2024 instead of 1/5. There are undocumented 2024 codes (above). Reported to ANES.
- **NSFG 2022–2023:** the codebook labels BABYSEX "BB-6a"; both questionnaires give BC-6a. Reported to NCHS.
- **GSS:** the release notes misprint DSDNTPAY for `dsndntpay`. gssrdoc's issue tracker lists question texts that belong to other items.
- **YRBSS:** the 2021 content document letters screen time's options A, C, D, E, F, G, with no B. The data has six codes, 1–6.
- **FARS:** manual and data labels differ in wording for 8 codes (`DR_DRINK` 1 is "Drinking" in the manual, "Yes" in the data).

## Checks that catch most of these

1. **Coverage:** every data column has an entry, and every entry a column.
2. **Codes:** every code in the data is documented. A burst of undocumented codes is usually the parser, not the codebook.
3. **Counts:** when the codebook prints frequencies, each code's count matches the data. This caught OCR errors and misread rows.
4. **No empty entries:** an entry that yields no codes, while the data has values, is a parse failure.
5. **Years:** the years the documentation lists match the years with data.
6. **Labels:** compared with the data file's own labels where it has them, after normalizing.
7. **Two releases side by side:** pair by the publisher's crosswalk, then compare label, universe, question text and each code, ignoring cosmetic differences.

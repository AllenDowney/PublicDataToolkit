---
name: from-pdf-codebook
description: Parse a PDF codebook or manual (or its pdftotext output) into PublicDataToolkit variable records. Covers probing the PDF, pdftotext -layout, page-break headers, margin boxes, distribution tables (NSFG), and multi-year code matrices with renamed elements (the FARS Analytical User's Manual). Use for any codebook that only exists as PDF.
---

# From a PDF or text codebook

Convert once with `pdftotext -layout` into `data/interim/`, then parse the text with regexes and a line-by-line state machine. `-layout` keeps columns aligned, which the parsers rely on. Examples:
- [`pdt-nsfg/build/build_slice.py`](../../../pdt-nsfg/build/build_slice.py): CDC codebooks, one entry per variable, with a distribution table;
- [`pdt-fars/build/build_slice.py`](../../../pdt-fars/build/build_slice.py): an 823-page manual that covers 1975–2024 in one document.

## Probe first

1. **Is there text at all?** `pdffonts` and `pdftotext -f 1 -l 3` on a few pages. A scanned PDF needs OCR, which is a different job; ask before starting it.
2. **Find the entry structure** by eye.
   - NSFG: a name line, then fields `LABEL`, `VARIABLE TYPE`, `UNIVERSE`, `NOTES`, then `NAME: Distribution  Value  n` and rows of label, value and count.
   - FARS: `C26. Weather`, then "SAS Name", "Definition", "Attribute Codes", and a matrix with one column per year range.
3. **Look at three page breaks, the widest page, and any boxed or shaded text.** Those are where parsers break.
4. **Check what `pdftotext` loses.** Bold, color and strike-through vanish. The GSS Release Variables guides mark each variable's status that way, so that information needs the PDF's content stream, not text.

## Traps we hit

- **Page-break headers repeat inside an entry.**
  - NSFG repeats the section title and the variable's name after a break. The first parse lost `SSMARCOH`'s label to it. Skip a name line equal to the current entry.
  - FARS has a running header naming the data file ("... The PERSON Data File"). Use it; it tells you each element's table.
- **Tables continued on the next page** repeat their year header. Continue the same block rather than starting a new one. FARS's first parse reported 220 "unresolved" codes, such as `STATE` 1–22. All of them were artifacts of this and the next two traps, and fixing those brought it to 0.
- **Margin boxes** share lines with the entry in `-layout` output. NSFG's "Corrected universe for MFLASTP" sits after 20+ spaces at column 110 or later. Split it off, attach it to its entry, and treat it as the publisher's correction (STANDARD.md §5.3).
- **Wrapped labels:** recognize a continuation by indentation (FARS), or by the absence of a value and count (NSFG rows).
- **Two rows on one line,** a pdftotext artifact: FARS `PHARM_EV` printed codes 98 for two periods with two labels run together. Split the cells, and the label where a word runs into a capital.
- **Multi-year code matrices** (FARS): one column per year range, `--` for "not used", ranges like `1-99`. Take the release's own column (2024 is the one ending "Later"), and keep the whole matrix as a code history (§5.4).
- **Names change over time inside one element.** The SAS Name field can span lines with years (`HARM_EV 2005-2009`, `PHARM_EV 2010-Later`). Read every line. Names on one line are parallel variables (`WEATHER1, WEATHER2`). A discontinued element can share a name with a current one, so keep the one coded for the release.
- **Labels with history inside them:** "Unknown/Reported as Unknown (Since 2018)". Keep the text verbatim in the history. For the release's record, prefer the data file's label for that year (§4.2).
- **Rounded numbers:** the NSFG prints ranges rounded ("1170.96-78770.13"). Compare with half a unit of the last digit.
- **No question text:** NSFG labels start with an item reference ("AD-7b"). The wording is in separate questionnaire documents (Task 22).
- **No missing-code markings:** NSFG and FARS list "Refused", "Don't know" and "Unknown" as ordinary rows. Type them with a rule over labels ([step 4](../../instructions/04-missing-codes.md)).
- **Name case:** the codebook writes `CASEID` and `AGEPREG`, the data `CaseID` and `agepreg`. Match case-insensitively, and store the data's spelling.

## Verify against the data

- [ ] Coverage (C3): every data column has an entry, and the other way. NSFG pregnancy's `AGER` has no entry.
- [ ] Codes (C4): every code in the data is in the parsed values. A burst of unresolved codes usually means a parser bug, not a codebook gap.
- [ ] Labels: compare with the data file's own labels where they exist (FARS's `<NAME>NAME` columns; SAS formats), after normalizing case and punctuation. Report the rest.
- [ ] Spot-check five entries against the PDF itself, with page numbers in `source_location`.

## LLM drafting

When `llm_processing` is `allowed`, an LLM may draft records from PDF pages that defeat a parser. Drafts are `origin: model`, `reviewed: false`, and are checked against the data like everything else. Prefer the parser: both PDFs here parsed deterministically once the traps above were handled.

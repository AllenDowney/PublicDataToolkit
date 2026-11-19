---
name: from-html-codebook
description: Parse an HTML codebook (one block per variable, as in the ANES Time Series Cumulative Data File codebook) into PublicDataToolkit variable records. Covers finding the block structure, layout clean-up, keeping the publisher's valid/missing split, and checking codes and years against the data.
---

# From an HTML codebook

The ANES CDF codebook is one HTML page with a table per variable, and inside it labeled sections: Question, Valid, Missing, Sources, Notes. HTML looks structured, but this page is generated from a PDF and keeps its layout, so treat it as text with markers.

Example: [`pdt-anes-cdf/build/build_slice.py`](../../../pdt-anes-cdf/build/build_slice.py). Its block regexes come from ExtractANES's `extract_cdf_codebook.py`.

## Probe first

1. **Find the block boundaries.** Look at the raw HTML around two variables. In the ANES file each variable starts with `<td class="first">VCF0128</td>` in a header row, and each section is a bold label `<div>` followed by an indented `<div>`.
2. **Count the blocks** and compare with the data file's columns: 1,029 codebook entries vs 1,030 data columns for the ANES.
3. **Read one entry of each kind:** a thermometer (a range plus labeled codes), an item with several wordings, and a summary index (no Valid section).
4. **Look for text outside the blocks.** The CDF's 92 thermometers share question text in a preamble before VCF0201 that the per-variable parser doesn't see.

## Traps we hit

- **PDF line breaks inside the HTML.** Join wrapped lines with single spaces, and turn non-breaking spaces into spaces (rule `anes_text`). Keep real structure: a line that is only a year or mode heading ("2000 TELEPHONE:") starts a new wording, and "... NOTE:" headings in Notes start a new line.
- **Several wordings in one Question section,** marked by year headings. Each becomes its own `questions` entry with `waves` (VCF0803 has three).
- **Code lines:** "1. Favor", "-8. DK; depends (VOL)", "00-96. Degrees as coded", "INAP. question not used". A line that doesn't start a code continues the previous one. "INAP." followed by "Inap. question not used" is one code.
- **Keep the publisher's Valid/Missing split** even when a label looks like a missing code. VCF0803 code 9, "DK; haven't thought much," is under Valid. A label regex would have called it missing, and a follow-up item depends on it. Don't compute a valid range from listed codes either.
- **A Missing label holds several reasons:** "NA; no Post IW; form III,IV (1972)". Split at ";" and type each part. Report the parts no rule types.
- **INAP is the data file's system missing** (`.`) in Stata, not a number.
- **HTML entities and smart quotes** ("don’t") survive unescaping. Match labels after normalizing quotes.

## Verify against the data

- [ ] **Codes (C4):** every code in the data is in Valid or Missing. The ANES build found `-1`, `-8`, `-4` and an undocumented code 2, all real codebook gaps ([Task 20](../../planning/tasks/task-20.md)).
- [ ] **Years (C5):** Sources vs the years with data. Six variables' Sources omit a year that has data.
- [ ] **Coverage (C3)** over the whole codebook. A scan of every entry ([`pdt-anes-cdf/build/scan_codebook_vs_data.py`](../../../pdt-anes-cdf/build/scan_codebook_vs_data.py)) is a useful screen, but summary indexes without a Valid section show up as false positives.

## Stop and ask

The ANES site (electionstudies.org) blocks scripts and headless browsers. Terms pages, errata pages and other studies' codebooks have to be saved by a person.

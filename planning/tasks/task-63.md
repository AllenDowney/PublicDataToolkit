# Task 63 — A HINTS slice

**Status:** `DOING (blue)`, claimed 2026-11-20. Built (pdt-hints 37176bd); terms wait for Allen.

The Health Information National Trends Survey (National Cancer Institute) in `~/pdt-hints`: a few cycles, with replicate weights (`design.replicates`). Record the terms for Allen. Memory cap.

**Files:** `~/pdt-hints/`, this file and the Task 63 block on the board.

## What the download requires

No login and no registration. The [download page](https://hints.cancer.gov/data/download-data.aspx) shows NCI's "suggestions on how to use HINTS data" and a "Continue" button. An email address is optional ("not a requirement for data access"). The zips are plain links that curl fetches. The controlled-access files (HINTS-SEER, the data linkage projects) need approval, and this repo doesn't use them.

## Terms, recorded for Allen (all `unknown`)

Quoted in `dataset.yaml`, from two saved pages:
- **The download page** says NCI "recommends users consider the following provisions": don't publish anything that could identify a respondent, including small cells; don't link the data to identified records; don't try to learn anyone's identity; report an identity discovered by accident to ncihints@mail.nih.gov. It says nothing about redistributing the files.
- **NCI's reuse policy** says "all text within National Cancer Institute (NCI) products is free of copyright and may be reused without our permission. Credit the National Cancer Institute as the source."

The files were prepared for NCI by Westat. Nothing here is a license for the data files themselves. Allen needs to decide data, documentation, metadata and llm_processing.

## What was built

Three cycles, each one public-use file taken whole:

| Release | Year | Rows | Variables |
|---|---|---|---|
| hints5-cycle4 | 2020 | 3,865 | 433 |
| hints6 | 2022 | 6,252 | 477 |
| hints7 | 2024 | 7,278 | 470 |

Each zip holds the Stata file, the codebook PDF, the annotated instruments (English and Spanish), the methodology report, the survey overview and a history document. The build (`build/build_records.py`) parses the codebook text (`pdftotext -layout`) and reads the Stata file with pyreadstat.
- **C3:** codebook entries and data columns match exactly in all three cycles.
- **C4:** clean.
- **C5:** every codebook count matches the data.
- `pdt check`: 0 failures.

**Fields:**
- From the codebook: label, universe ("Criteria description" with the filter expression), codes with unweighted counts, and the codebook page (`source_location.page`).
- Rule `hints_label_split`: the question number and text, split from the label ("A1. Have you ever ...").
- Rule `hints_value_listing`: a numeric item whose codebook lists every value under one repeated label ("Current age, in years") gets a valid range instead of a list of values.

**Missing codes** are HINTS's negative codes. Rule `hints_missing_types` types them by label; HINTS is self-administered (mail and web):

| Code | Label | Types |
|---|---|---|
| -1 | Inapplicable | inap |
| -2 | Question answered in error (Commission Error) | inap |
| -4 | Unreadable or nonconforming response | uncodeable |
| -5 | Multiple responses selected | uncodeable |
| -6 | Missing data (Filter Missing) | inap, skipped |
| -7 | Missing data (Web partial - Question Never Seen) | not_asked |
| -9 | Missing data (Not Ascertained) | skipped |

One code is unresolved: hints7 `SexualOrientation2_OS` -4 "Verbatim response", in an open-ended text item.

**Design:**
- Weight `PERSON_FINWT0`, with 50 replicate weights `PERSON_FINWT1`–`PERSON_FINWT50` (method `jk1`, "jackknife minus one", from the survey overview).
- `VAR_STRATUM` and `VAR_CLUSTER` for Taylor series.

## Findings and traps

- **The HINTS 6 Stata file is Windows-1252, not UTF-8.** pyreadstat fails on byte 0x92. The build retries with cp1252 and the report says which encoding it used.
- **Some codebook entries print character codes that the Stata file stores as numbers.** The design variables Stratum/STRATUM and VAR_STRATUM, and APP_REGION, print SAS-format codes ("HM", "LM", "6_HR", "A"). For those, the build takes the codes and labels from the Stata value labels, with origin `data_file`, and lists them in the report.
- **In HINTS 6, APP_REGION stores Non-Appalachia as -9.** A negative code that isn't missing. The Stata labels show it, and the rule leaves it valid because its label isn't a missing label.
- **Open-ended items (`_OS`) list respondents' verbatim answers in the codebook.** The build keeps only their numeric codes.
- **Long value labels wrap onto the next, indented line.** The parser joins them. One label is cut off in the PDF itself ("Health organizations or groups (for example, the American Cancer Society,"), so the record keeps it as published.

## Not done

- Links between cycles: most names repeat across cycles, but same-item links need a check that the wording matches. That's a follow-up.
- `measure` isn't set, since the files are taken whole.

## Links between cycles (2026-11-20)

The coordinator asked for links where the wording and codes are identical. pdt-hints 7346e46: `build/build_links.py` writes `metadata/links.jsonl` and `build/links_report.md`, and `make build` runs it.

**Rule `hints_same_name_identical`** links a variable to the next cycle's variable of the same name (case-insensitive) only when all of these hold:
- the question text, the label without its item number, and the universe are the same, after normalizing case, whitespace, dashes and quotes;
- the valid codes and their labels are the same (for a numeric item, the same listing label);
- the storage type is the same;
- missing codes differ at most in wording or in which ones occur, and no code is valid in one cycle and missing in the other.

The source is NCI's merge code, which "will match up variables that have the same name and format" (each cycle's Survey Overview, "Merging HINTS Survey Iterations"). It's quoted as evidence on each link.

| Pair | Names in both | Linked | Candidates |
|---|---|---|---|
| hints5-cycle4 → hints6 | 235 | 76 | 159 |
| hints6 → hints7 | 288 | 150 | 138 |

**Relations:**
- 88 links are `same_item` alone.
- 128 add `labels_changed`: only the item number moved ("A1." → "A2.").
- 10 add `renamed`: the name changed case (MailHHAdults vs MAILHHADULTS).

**Candidates aren't linked.** HINTS's methodology reports and history documents don't list item changes between cycles, so there's no publisher statement to cite. Most candidates are real but small rewordings: "3G/4G" became "3G/4G/5G", and "trust information about cancer family or friends" was corrected to "from family or friends". Others are relabeled design variables, and universes with new filter expressions. `build/links_report.md` lists them by reason, and `pdt diff` shows each change.

**Not done:** links between nonconsecutive cycles (2020 → 2024), and renamed items. A renamed item needs the publisher's statement.

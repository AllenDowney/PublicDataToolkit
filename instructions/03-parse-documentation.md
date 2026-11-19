# Step 3. Parse the documentation into records

**Goal:** `build/` turns the files in `data/raw/` into `metadata/releases/<release>/[<table>/]variables.jsonl`, and the result agrees with the data file.

**Standard:** §3 (rules for every record, origins), §4.1 (fields), §4.4 (extensions), §2 (generated vs hand-written files).

## Do

1. **Probe each source before writing a parser.** Use the skill for its format ([step 1](01-survey.md)). Look at a dozen entries by eye, including the first and last ones, a long one, and one that crosses a page.
2. **Start with a slice** (30–50 variables in `build/slice.yaml`) that includes the hard cases: a battery, an item asked on only some forms, a variable with several wordings, missing codes of several kinds, and anything the publisher has corrected. Grow it once the slice is right.
3. **Write one build script** (`build/build_slice.py` in most of the existing repos). Its docstring says where each field comes from; copy that pattern. pdt-gss's says "variable label, which extended missing codes occur: the Stata file; question text, value labels, availability: gssrdoc; measure: build/slice.yaml (hand)".
4. **Fill fields from the best source for each,** and record the origin of every field that differs from the record's (§3). The data file's labels are usually the best for the release itself (FARS's 2024 CSV labels, not the 1975–2024 manual's, per §4.2). The documentation is best for question text, universe and notes.
5. **Copy text verbatim** (rule 3). Remove only layout: line breaks from page width, hyphenation, running headers. A fix that applies across the whole source is a named, versioned rule recorded in provenance. gssrdoc doubles every apostrophe ("DON''T"), so the rule `gssrdoc_text` undoes it. A fix that affects one variable is a correction (step 6), not an edit.
6. **Put hand-made facts in a hand-written input**, such as `measure` in `build/slice.yaml`, with `origin: hand`. Never edit generated records. The input's `author` names whoever made those judgments: a person, or the agent and its task ("Claude (PublicDataToolkit Task 35)"). Never put a person there who didn't make or check them (STANDARD.md §3). The template starts with `author:` empty, and the build stops until it's filled. Task 46 found 599 facts named after Allen that agents had made, because one `author:` was copied from repo to repo.
7. **Use extensions sparingly** (§4.4), and list each one in `EXTENSIONS.md` with a reason. An extension that two datasets need is a proposal for the standard. NSFG's `nsfg.variable_type` became the standard's `variable_type` this way.
8. **Write `build/report.md`** on every build: counts, coverage, codes and labels to look at, and the data checks below.

## Check against the data before moving on

These are C3 and C4 in STANDARD.md §9. Until `pdt check` runs them, the build does, and writes the results in its report.

- [ ] **Coverage (C3), for the whole file, not just the slice.** Every column in the data has a documentation entry, and every entry is a column. The results so far:
  - NSFG female: 1,912 of 1,912;
  - NSFG pregnancy: one data column, `AGER`, has no codebook entry;
  - GSS: 6,943 columns but 6,904 gssrdoc entries;
  - FARS: the CSV has a `<NAME>NAME` label column for most coded columns, which isn't a variable.

  Report every mismatch by name.
- [ ] **Names match the data's spelling.** Store names as the data file spells them (`CaseID`, `agepreg`), and report where the documentation differs (the NSFG codebook writes `CASEID` and `AGEPREG`).
- [ ] **Codes (C4).** Every code that occurs in the data is in `values`, or is reported. See [step 4](04-missing-codes.md).
- [ ] **The source documents this release.** Compare per-wave counts or code frequencies with the data. gssrdoc's 2024 count for `racopen` was 462, while the data has 981. That's how the build found that gssrdoc documented Release 2.
- [ ] **Labels agree,** between the documentation and the data's own labels. FARS: after ignoring case, punctuation and year notes, 8 codes still differed ("Drinking" vs "Yes"). Report them; don't silently pick one.
- [ ] `pdt check` passes (C1, C2, C6, C10).
- [ ] The report's "to look at" list has been read, and each item is fixed, recorded as a finding, or explained.

## Model drafts

You may draft records with an LLM, for example from a PDF codebook, only when `llm_processing` is `allowed`. Drafts carry `origin: model` with the model, the date and `reviewed: false` until a person reviews them. They're validated like any other record. Links never come from a model (rule 8). Prefer a deterministic parser whenever the source has a regular layout: the four existing builds needed none.

## Stop and ask a person

- When coverage shows a source doesn't match the release (gssrdoc vs Release 3a), the choice of what to do is theirs. Present the options.
- When the documentation is missing for many variables and the fix needs a new source (the GSS's 39 variables gssrdoc lacks).

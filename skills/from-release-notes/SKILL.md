---
name: from-release-notes
description: Turn a publisher's release notes (or a crosswalk) into PublicDataToolkit links between releases (links.jsonl), as done for the GSS 1972-2024 releases 1 to 3a. Covers transcription with page numbers, misprinted names, checking every name against each release's data file, and links whose other end has no records yet.
---

# From release notes to links

Release notes say what changed between releases: renamed variables, revised data, corrected labels. Links (STANDARD.md §5.2) record that continuity as the publisher asserts it. Example: [`pdt-gss/build/release_notes_7224.yaml`](../../../pdt-gss/build/release_notes_7224.yaml) and [`build_links.py`](../../../pdt-gss/build/build_links.py).

## Probe first

1. **Find every set of notes.** NORC's notes for Release 3a repeat those for 3, 2 and 1, so one PDF covered four releases. "What's New" documents and variable guides may add nothing at the variable level; check before parsing them.
2. **Count the entries** and read a few. Each GSS entry gives years, variables (upper case, sometimes ranges like `INTRACE1-INTRACE3`), the issue, and the fix.
3. **Check what styling carries.** The GSS Release Variables guides mark status with bold, red and strike-through, which `pdftotext` drops.

## Do

1. **Transcribe into YAML by hand** when there are tens of entries, not thousands. That's quicker and safer than parsing. Keep each entry's years, variables as printed, issue and fix verbatim, and page. The 50 GSS entries took one pass.
2. **Separate what's transcribed from what's yours.** The text is the publisher's. The reading of each entry as relations (`same_item`, `data_revised`, `renamed`, `labels_changed`, ...) is yours, so the link's note says so and quotes the fix.
3. **Generate links by script** from the YAML. Expand ranges and lower-case names to match the data.
4. **Add a naming-convention rule** for names the notes don't mention, if the publisher documents one. `gss_same_name_same_item`: NORC keeps names while items are unchanged, and the notes list the exceptions. Its links have `origin: rule`.

## Traps we hit

- **Misprinted names:** the notes print DSDNTPAY. The data files have `dsndntpay` and no `dsdntpay`. Keep the misprint in the transcription, and map it in a `name_fixes` entry with the evidence.
- **Links need records at both ends.** Of 464 GSS links, only 50 could be written while one release had records. Write the rest to a pending list in `build/links_report.md`, and they appear when the other release is built.
- **New variables have nothing to link from.** An entry that introduces a variable produces no link. Report it separately from a name that's missing by mistake.
- **No relation for a corrected label** at first. A fixed variable label (RADIOACT) or value labels (IMPTHNGS) led to `labels_changed`. If a change doesn't fit any relation, propose one rather than forcing it.
- **Links never come from a model** (rule 8), even when an LLM helped read the PDF.

## Verify against the data

- [ ] Every linked name exists in its release's data file. pdt-gss checks against the R2, R3 and R3a Stata files (variable names only).
- [ ] `pdt check` C2: every link end resolves to a record.
- [ ] Each link's source and page point to the entry it came from.

---
name: from-upstream-package
description: Build PublicDataToolkit variable records from a third-party package that already holds a dataset's documentation as structured data (gssrdoc for the GSS, R or Stata label sets). Use when a package redistributes the publisher's metadata; covers pinning, checking which release the package documents, and its systemic artifacts.
---

# From an upstream package

An upstream package (gssrdoc, which scrapes GSS Data Explorer) gives question text, value labels and availability already structured. That saves a parser, but the package is a third party: you must pin it, find out which release it documents, and treat its quirks as its own.

Records from it have `origin: upstream_package` with the source id (STANDARD.md §3). Its license covers its code, not the publisher's documentation, which keeps the publisher's terms. gssrdoc is MIT, but the GSS text is NORC's.

## Probe first

1. **Pin it.** Record the tag or commit in `sources.yaml` `version`, and fetch the data file at that commit with a SHA-256 check. pdt-gss's `make gssrdoc` fetches `gss_doc.rda` from a pinned commit and runs `sha256sum -c`.
2. **Convert it to something you can read** without the package's language at build time. pdt-gss converts the `.rda` to JSON with `build/convert_gssrdoc.R`, written to `data/interim/`.
3. **Find which release it documents.** Read the package's commit messages. Then compare with the data: are its names exactly the data file's names, and do its per-wave counts match? gssrdoc 0.8.2's 6,904 names were exactly Release 2's, and its 2024 count for `racopen` (462) was R2's, not R3a's (981). gssrdoc 0.9 documents R3; no version documents R3a.
4. **Look at a few fields as raw strings.** gssrdoc writes every value set as one string, `"[1] yes / [2] no / [NA(d)] don't know / ..."`, and availability as a JSON table of years by ballot (`"A/B/C/-"`).

## Traps we hit

- **The same missing codes for every variable.** gssrdoc lists all twelve `NA(x)` codes for every variable. Which ones a variable uses comes from the data file (`.d`, `.i` and `.n` in most; `.y` in a few).
- **Systemic artifacts:** gssrdoc doubles every apostrophe ("DON''T") in 239 variables. Fix it with one named, versioned rule recorded in each field's provenance (`gssrdoc_text`), not 239 corrections.
- **Missing per-wave counts** for some variables, such as weights. Count them in the data and label that field `origin: data_file`.
- **Known errors upstream:** gssrdoc issue #1 lists GSS question texts that belong to other items (`racschol`, `racopen`). Read the package's issue tracker; each confirmed one is a correction with the issue as evidence.
- **Variables the package doesn't have:** gssrdoc lacks 39 of R3a's 6,943 variables. Find them by comparing names with the data (C3), and fill them from the publisher's own documentation, with that origin.
- **Stem and item:** gssrdoc joins a battery's shared stem and the lettered item into one text. Splitting them is a rule. The item letter usually follows a newline, but sometimes "?" or ":".

## Verify against the data

- [ ] Names: package vs data file, both directions; report every difference.
- [ ] Per-wave counts: package vs data. A mismatch in one wave means a different release.
- [ ] Availability (C5): each year the package lists has data, and vice versa.
- [ ] Value labels: package vs the data file's own labels ([`from-data-labels`](../from-data-labels/SKILL.md)).

## When it documents a different release

Record it, don't hide it. pdt-gss builds every release from gssrdoc 0.9 (R3), and the 7224r3a records say in `provenance.record.note` that their text is R3's. Choosing what to do (pin per release, build from the publisher's PDFs, or a hybrid) is a person's decision.

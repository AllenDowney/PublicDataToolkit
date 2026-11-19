# Task 21 — GSS follow-ups

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE` — 2026-11-19 (gss thread)

- **The 39 missing variables:** release 7224r3a has 6,943 variables, and gssrdoc 6,904. Find the 39 and decide how to document them, perhaps from the NORC PDF codebook.
- **Pin gssrdoc,** or decide to build from NORC sources (plan §10 item 3; ask Allen).
- **Links between releases:** parse the "What's New" and Release Variables PDFs (in CultureWar's `data/raw/`) to build `links.jsonl` between 7224r3 and 7224r3a.

**Files:** `../pdt-gss/` only.

**Findings (2026-11-19, gss thread).** pdt-gss commit `8cc7137`.

**gssrdoc_full.json documents Release 2, not 3a.** It was converted from gssrdoc 0.8.2 (commit `26faf3f`, 2025-10-28, "Update for 1972-2024 R2 documentation"). That was the only commit to `data/gss_doc.rda` between then and the file's date, 2026-02-07. The evidence:
- its 6,904 names are exactly the names in the R2 Stata file, with no differences either way;
- its 2024 counts match R2's data: racopen 462 (R3a: 981) and grass 867 (R3a: 862).

So the 50 `7224r3a` records take their question text, value labels and availability from R2 documentation; labels and missing codes come from the R3a Stata file. `sources.yaml` now records the version. Upstream, gssrdoc 0.9 (commit `112286d`, 2026-03-12) documents Release 3, and no gssrdoc version documents 3a.

**The 39 missing variables.** The gap is net: 40 names in R3a aren't in gssrdoc 0.8.2, and 1 name in gssrdoc isn't in R3a.

| Release | Names | What they are |
|---|---|---|
| R3 (38) | `dwelling_8222`, `intage_0418`, `intyrs_0418` | historical-preservation copies of coarsened variables |
| | `migage`, `mighist` | migration summaries that replace `yearsusa`/`mnthsusa` for 2024 |
| | `aneseligible`, `anespre_status`, `anespost_status`, `dateintv_next` | follow-on eligibility and status |
| | `cred*` (6), `topprob1_next`, `topprob2_*` (9), `happy_next`, `chldidel_next`, `chldpref_next`, `hhtype1_next`, `famgen_next`, `petsseq` | GSS Next follow-on items |
| | `perla`, `perla_self`, `knwsexor`, `reltrad16`, `wordsum7`, `wordsumold`, `wordsumnew` | skin tone, other new items, WORDSUM variants |
| R3a (2) | `vote_ts`, `pres_ts` | new "time series" summaries of VOTE68–VOTE20 and PRES68–PRES20 |
| dropped in R3a | `strvbiasy` | merged into `strvbias` |

Coverage in the sources:
- gssrdoc 0.9 documents all 38 R3 names. Only `vote_ts` and `pres_ts` are in no gssrdoc version.
- NORC's 2024 codebook (R3a) has an entry for 37 of the 40, with label, notes and 2024 frequencies. `vote_ts` and `pres_ts` are on p. 457.
- The three `_XXYY` copies are only listed, in Appendix E, because they have no 2024 data.
- The R3a Stata file has variable and value labels for all 40.

**Proposal for documenting them:** document each from the newest source that covers it, and label the origin.
1. Use gssrdoc 0.9 for the 38 R3 names, if Allen chooses to pin it (below).
2. Use the R3a Stata labels (`origin: data_file`) for `vote_ts` and `pres_ts`. Add the codebook's notes ("GSS variables VOTE68 through VOTE20 were combined…", p. 457) with `origin: publisher` and the page as `location`.
3. For the `_XXYY` copies, cite Appendix E of the 2024 codebook as the `source_location`.

None of this matters for the slice until one of these names joins it. All 50 slice names are in both gssrdoc versions.

**Links between releases.**
- NORC's "Release Notes for GSS 1972-2024 Release 3a" repeats the notes for R3, R2 and R1. I transcribed all 50 entries by hand into `build/release_notes_7224.yaml`, with page numbers.
- `build/build_links.py` turns them into 464 links (STANDARD.md §5.2, with the new `data_revised`); all 464 validate against `link.schema.json`. It checks every name against the R2, R3 and R3a Stata files. One misprint turned up: the notes print DSDNTPAY for `dsndntpay`, and a `name_fixes` entry records that.
- **None are written yet.** Each link needs a record at both ends, and pdt-gss has records only for 7224r3a. The pending links are listed in `build/links_report.md`. Those that touch the slice:
  - `racopen` r3→r3a and r2→r3;
  - `grass`, `reliten` and `mode` r2→r3;
  - `reliten` and `relig` r1→r2.
- The "What's New" PDFs add nothing at the variable level beyond the release notes. The R3 and R3a Release Variables guides differ only by ISCO08 (5 names), VOTE_TS and PRES_TS, all of which the notes list.
- The guides mark each variable's status with styling that `pdftotext` drops: bold via text render mode 2, red fill, and drawn strike lines. Parsing that per variable is possible from the content stream but not done.

**Release 7224r3: not added.** We have its Stata file but no records. The natural way to add it is gssrdoc 0.9, which documents exactly R3, plus the R3 Stata file. That depends on the pinning decision. Once both releases have records for the slice, `make build` writes the r3→r3a links with no other change.

**For Allen: GSS upstream (plan §10 item 3).** The current records describe R2 under the R3a label, so some choice is needed.

| Option | What it means for 7224r3a records | Cost |
|---|---|---|
| **A. Stay on gssrdoc, pinned per release** (recommended for now) | Pin 0.9 for a new 7224r3 release, which matches exactly. Keep 7224r3a on the newest gssrdoc and record the mismatch: 0.9 now, 3a's own version when Kieran Healy publishes one. Each record says which release its text came from, and C5 reports count differences | Small. 0.9 needs an R conversion step in `build/` (R is in pdt-xlang). We stay one release behind NORC, as now |
| **B. Build from NORC's own sources** | Labels, codes and missing codes from the R3a Stata file (all 6,943 names). Question text, notes and 2024 frequencies from the 2024 codebook PDF (973 entries; 2024 only). Earlier years' text needs GSS Data Explorer, which is what gssrdoc scrapes, or NORC's cumulative codebook, which isn't in `data/raw` | Large. A PDF parser, and Data Explorer scraping or another source for pre-2024 items. Same path as ANES, NSFG and FARS, and current on release day |
| **C. Hybrid** | A, plus the Stata file as the authority for labels and codes (already true), plus the 2024 codebook for names gssrdoc lacks (`vote_ts`, `pres_ts`) | Medium. Grows from A as gaps appear |

**Recommendation:** C, starting as A:
1. Pin gssrdoc 0.9 now, and add 7224r3 so the release-note links have both ends.
2. Fill gaps from the R3a codebook and Stata file with labeled origins.
3. Keep B as the long-term path if gssrdoc stops tracking releases.

Either way, `sources.yaml` should stop calling 0.8.2 a 7224r3a source once 0.9 is in.

**Standard gaps raised.**
- `data_revised`: decided and added (commit `dfac1da`).
- `labels_changed`: decided and added (commit `d50a601`). It's used for RADIOACT, IMPTHNGS and PAIDLV.

**Decision implemented (2026-11-19).** Allen chose option C, starting as A (plan §10 item 3, commit `f60fc37`). pdt-gss commit `35d1f59`; `pdt check` gives 0 failures.
- **gssrdoc 0.9 is pinned.**
  - `make gssrdoc` downloads `gss_doc.rda` at commit `112286d`, checks its SHA-256, and converts it with `build/convert_gssrdoc.R` (base R and jsonlite; the pdt-xlang env).
  - Its output has the same shape as the old `gssrdoc_full.json`.
  - Its 6,942 names are exactly R3's.
  - Source id `gssrdoc` replaces `gssrdoc-json`.
- **Release 7224r3 is added.** Its 50 slice records come from gssrdoc 0.9 and the R3 Stata file. C5 finds no differences between gssrdoc and the R3 data.
- **7224r3a records:**
  - Their text now comes from 0.9.
  - `provenance.record.note` says the text documents Release 3, and that labels and missing codes come from the R3a Stata file.
  - The only content change from 0.8.2 is grass's 2024 n, which goes from 867 to 862 and now matches the data.
  - C5's one remaining difference is racopen 2024 (gssrdoc 462, data 981). That is the R3a fix NORC describes.
  - Oddity: NORC says R3 "inadvertently removed" racopen's 2024 data, yet R3 still has the R2 count (462). Only racopenv is empty in R3.
- **Links (50 written).**
  - racopen r3→r3a (`same_item`, `data_revised`), from the R3a notes, p. 1.
  - `same_item` for the other 49, by rule `gss_same_name_same_item`. A name in two consecutive releases that the notes don't mention is unchanged; NORC lists the exceptions in its notes.
  - Still pending (477, listed in `build/links_report.md`): 445 cross-release links from the notes, which need r1 or r2 records or name variables outside the slice, and 32 within-release `derived_from` links (`migage`/`mighist`, `vote_ts`/`pres_ts`) whose ends are outside the slice.
- **The slice is unchanged:** 50 variables per release.
- **Deferred:** `vote_ts` and `pres_ts` (and every name gssrdoc lacks) need a fallback to the R3a codebook and Stata file. That fallback goes with the full-release build, where it can be tested on all 40 names (coordinator, 2026-11-19).
- **For the eval thread:**
  - `data/raw/gssrdoc_full.json` (0.8.2) is still linked locally for its key builder, but pdt-gss no longer uses it.
  - With two releases, a name-only search returns two records per variable.

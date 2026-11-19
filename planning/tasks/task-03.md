# Task 3 — Inventory the GSS and ANES work in CultureWar

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE` (2026-11-19)

Read, and don't modify, the GSS and ANES codebook and extract code in the CultureWar, GssExtract and ExtractANES repos. Starting points are listed in §3 of the earlier plan and in [`planning/context.md`](../../planning/context.md). For each piece, record:

- what it does and which inputs it reads;
- whether it is generic (it belongs in the instructions or skills) or specific to CultureWar's analysis;
- what an agent would need in order to do the same thing for a new dataset.

Write the result to `planning/inventory.md`. Also check MarriageNSFG as a third worked example (NSFG: a download script, a data release, codebooks as text).

**Result:** [`planning/inventory.md`](../../planning/inventory.md). Main findings:
- **The GSS catalog can't be rebuilt.** `convert_gssrdoc_to_json.R` reads a local clone of gssrdoc at a hard-coded path, and its outputs are gitignored.
- **Missing codes collapse.** The GSS and ANES detectors turn DK, refused and IAP into one NaN. The GSS regex misses 7 real missing codes whose labels start with "no". gssrdoc's `NA(x)` tokens are almost the same for every variable.
- **The ANES codebook build is stranded.** The script and its HTML input are only in ExtractANES, with no record of where the HTML came from.
- **The GSS and ANES record schemas disagree** on name case and field names, and both store structured data as strings.
- **NSFG has the best data-release practice** (release with SHA-256 sums, terms flag) **and the weakest metadata.**
- **Not yet captured:** GSS release notes have never been parsed, and the errata exist only as markdown.

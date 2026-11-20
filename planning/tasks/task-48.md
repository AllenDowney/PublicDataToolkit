# Task 48 — What the codebooks trip over

**Status:** `DONE (yellow)` 2026-11-19.

To compare notes with data-dict on what the codebooks trip over when drafting dictionaries. Compile `planning/codebook_failure_modes.md` from the task files, the skills in `skills/`, and the build reports in the dataset repos (read only). For each failure mode: what goes wrong, which datasets show it, a short concrete example, how we detect it, and how we fix it. Group them by source format (PDF text, HTML, spreadsheets, SAS/SPSS/Stata setup files, portals), across releases, and publisher errors. Keep it factual and short; Allen may share it with Hadley, so no internal thread names.

**Files:** `planning/codebook_failure_modes.md` (new); this file; the Task 48 block on the board.

## Progress

**Done 2026-11-19.** [`planning/codebook_failure_modes.md`](../codebook_failure_modes.md), about 40 failure modes in seven groups:
- PDF text (11);
- HTML codebooks (5);
- spreadsheets (none parsed yet; the PISA xlsx is pending);
- SAS, SPSS and Stata files (6);
- what the documentation says about codes (8);
- across releases (10);
- errors in the publishers' documentation, by dataset.

It closes with the seven checks that caught most of them. Sources: the task files for the GSS, ANES, NSFG, FARS, YRBSS, CPS ASEC and Chicago slices, the skills in `skills/`, and the BRFSS build (its code and `build/report.md`; its task file has no findings yet). It uses dataset names only, so it can be shared.

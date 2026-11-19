# Task 20 — ANES codebook errors

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE (anes-errata)` 2026-11-19. Report sent to ANES; corrections marked `filed`.

The ANES build found likely errors (Task 5, step 3):
- VCF0878 is coded 1/2 in 2016 rather than 1/5, and 2016 is missing from its Sources;
- VCF0704's Sources omit 2016;
- some Sources omit 1954 or 2012;
- there are undocumented codes: `-1` (VCF0806, VCF9236), `-8` and `-4`.

Check each one against the PDF codebook (`../pdt-anes-cdf/data/raw/`) and ANES's "Data Alerts" (a person may need to open the page). Record the confirmed ones in `metadata/corrections.jsonl` with evidence, and draft a report to anes-project@umich.edu for Allen to send.

**Files:** `../pdt-anes-cdf/` only. The draft report goes outside every repo, in `~/pdt-private/`.

**Findings.** I checked each item against the PDF codebook and the Stata file (both 2026-02-05). Commits are in `pdt-anes-cdf` (2185e80, 0cbfcea, 6959b68).

| Candidate | Result | Correction |
|---|---|---|
| VCF0878 coded 1/2 | Confirmed, but in **2024**, not 2016: 4,041 code 1, 1,130 code 2, no 5s. 2016 uses 1/5 as documented | `vcf0878-2024-code-2`: code 2 is valid "No" (inferred) |
| VCF0878 Sources omit 2016 | Confirmed: 4,215 valid answers in 2016 | `vcf0878-sources-2016` (verified) |
| VCF0704 Sources omit 2016 | Confirmed: 2,609 valid answers | `vcf0704-sources-2016` (verified) |
| Sources omit 1954 or 2012 | Confirmed for VCF0104, VCF0128, VCF0301 (1954) and VCF0830 (2012) | 4 records, `*-sources-<year>` (verified) |
| `-1` in VCF0806, VCF9236 | Confirmed. 2024 only, the same 245 respondents in 26 variables. Those rows are INAP in VCF0128 and VCF0878, and all have VCF0017 = 0 | 2 records: -1 is missing `inap` (inferred) |
| `-8` | Confirmed in VCF0218 and VCF0224 (2024 only, 9 and 11 cases). 98 (DK) is empty in 2024. Also in VCF0424–VCF0429, VCF9016 and VCF9039, outside the slice | 2 records: -8 is missing `dk` (inferred) |
| `-4` in VCF0206 | Confirmed, one case in 2024 | None: left unresolved and reported only (coordinator's decision) |

- **Verified vs inferred.** The Sources corrections are verified, because the data file confirms the year. The code corrections are inferred: they're our reading of the 2024 study's own codes. The ANES 2024 codebook would make them verified, but it's on electionstudies.org, which blocks scripts. The coordinator approved inferred corrections that change an unresolved code's kind (STANDARD §5.3, commit 38cbbb4).
- **Beyond the slice.** `build/scan_codebook_vs_data.py` (in pdt-anes-cdf) compares every codebook entry with the data. It found -1 in VCF0907 and VCF0908 (2012, 75 cases), and -9, -4 and -2 in VCF0107 and VCF0871 (2024). It also found Sources gaps in about 120 variables, most of them a missing 2008 line. It's a screen: the summary indexes with no Valid section (VCF0316–VCF0411, VCF0982–VCF1003) are false positives. Only the 37 slice variables have records, so only they get corrections.
- **For the views thread (Task 15):** a correction's evidence `quote`, which holds the counts, doesn't appear on the docs page; only the `citation` does.
- **Upstream:** Allen sent the report to anes-project@umich.edu on 2026-11-19, and all 11 corrections are `filed`. ANES has no "Data Alerts" page; the closest are [CDF Updates & Errata](https://electionstudies.org/time-series-cumulative-data-file-updates-errata/) and [Updates & Announcements](https://electionstudies.org/updates-announcements/), saved in `pdt-anes-cdf/data/raw/errata/` and listed in its `sources.yaml`. Neither page mentions any of our findings. The VCF0212 erratum is already fixed in 20260205. One open erratum applies to our release: VCF9096's 2024 data used the wrong input variable (2026-03-13). That's a data error outside the slice. If VCF9096 joins the slice, add a note to its record.

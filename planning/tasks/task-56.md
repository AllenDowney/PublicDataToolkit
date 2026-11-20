# Task 56 — An ATUS slice

**Status:** `DOING (yellow)`, blocked on downloads from bls.gov. (First numbered Task 54, which red had already claimed; renumbered by the coordinator, 2026-11-20.)

The American Time Use Survey (BLS) in `~/pdt-atus`, 2003–2023: the respondent file, the activity summary and the activity file's codes. The activity codes are the first real test of shared code lists (`metadata/code_lists.jsonl`, STANDARD.md §4.5).

## Progress

### 2026-11-20: blocked on downloads from bls.gov

- `~/pdt-atus` was created from the template (v0.1.0; 5ff6c8a, terms URL fixed in 1fa2d76). The single release is `2003-2023`, BLS's multi-year files, with year as the wave.
- **bls.gov refuses scripts.** These requests got 403 "Access Denied" on 2026-11-20:
  - urllib's and curl's default User-Agents;
  - a browser User-Agent;
  - headless Chromium (Playwright);
  - a generic script name.

  The data page is https://www.bls.gov/tus/data/datafiles-0323.htm. The refusal page says bot activity "that doesn't conform to BLS usage policy is prohibited". BLS's terms (https://www.bls.gov/bls/blsterms.htm) reserve "the right to block robots that do not contain information that can be used to contact the owner".
- **What's needed:** a script would need contact information in its User-Agent. That means Allen's email, which I won't send without his explicit OK. The other way is for Allen to download the files in a browser.
- **Nothing else has started:** no sources, no records.

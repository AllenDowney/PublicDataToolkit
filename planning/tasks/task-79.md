# Task 79 — Prepare the data releases (nothing uploaded)

**Status:** `DOING (blue)`, 2026-11-20. Stopped at the wrap-up: 14 of 16 repos are packaged, and ATUS and NLSY97 are left (see "Stopped here"). Asked for by the coordinator. Allen decides when to publish data. No tag or release was created, nothing was uploaded, and nothing was pushed.

**What was run**, per repo, under the 6 GB cap (a scratch driver):
1. `pdt check`.
2. `make data` if any data file was missing or stale.
3. `pdt check` again.
4. `pdt package`, which writes `data/release/<id>-data/`: the common-format files, the publisher's data files and `SHA256SUMS`. It's in gitignored `data/`, so nothing is committed.

The 16 repos are the published ones whose `terms.data` is `ship`. GSS and Pulse have no remote yet, and NCVS's data is build-only.

## Results

| Repo | Files | Total | Largest file | SHA-256 of SHA256SUMS (first 16) | Data checks (C3–C5, C12) | Other failures |
|---|---|---|---|---|---|---|
| pdt-anes-cdf | 3 | 33 MB | anes_timeseries_cdf_stata_20260205.dta.gz 31 MB | `c54d28be4206ac3c` | pass | none |
| pdt-brfss | 27 | 1,364 MB | LLCP2011XPT.ZIP 132 MB | `c80499ac7af44890` | pass | C8 |
| pdt-ces | 9 | 3,475 MB | CCES24_Common_OUTPUT_vv_topost_final.dta 993 MB | `0b21301ad219843e` | pass | C8 |
| pdt-chicago-crimes | 6 | 94 MB | crimes-2024.csv 75 MB | `fc71d1fa53feb616` | pass | C8 |
| pdt-cps-asec | 29 | 1,169 MB | asecpub19csv.zip 184 MB | `7aa92687c4382e4c` | pass | C8 |
| pdt-fars | 11 | 65 MB | FARS2024NationalCSV.zip 33 MB | `517a5855bc3d4fbe` | pass | C8 |
| pdt-hints | 7 | 65 MB | HINTS7_STATA_20250731.zip 21 MB | `aaa1ac1e61dfe983` | pass | C8 |
| pdt-meps | 13 | 42 MB | h256dta.zip 6 MB | `d92b7dd0f97ad1b3` | pass | C8 |
| pdt-nhanes | 25 | 22 MB | DEMO_I.xpt 4 MB | `4b6759ce1312d0dc` | pass | C8 |
| pdt-nhis | 25 | 48 MB | adult24csv.zip 6 MB | `e09925905c88c673` | pass | C8 |
| pdt-nsduh | 7 | 62 MB | nsduh-2023-ds0001-bndl-data-stata_v2.zip 20 MB | `1233eb3973dace19` | pass | C8 |
| pdt-nsfg | 42 | 712 MB | 1995FemRespData.dat 142 MB | `6cb69b3ef6d0acdb` | pass | C8 |
| pdt-pisa | 9 | 1,883 MB | STU_QQQ_SPSS.zip 682 MB | `3bb4b1fbb771526b` | pass | C8 |
| pdt-yrbss | 3 | 203 MB | sadc_2023_national.dat 198 MB | `6eb43b24fc789320` | pass | C8 |

- **Data checks:** all pass. `make data` ran where the files were stale or missing: anes-cdf, brfss (12 min, 1.5 GB), chicago-crimes, cps-asec, fars, nhis and yrbss.
- **Other failures:** the only ones are C8, in every repo but anes-cdf. Each repo's views were made by an older views generator (`pdt.views.GENERATOR_MODULES` changed with v0.2.1). The fix is `make views` in each repo, which doesn't affect the data release.
- **Size:** no file is over GitHub's 2 GiB per-asset limit; the largest is CES's 993 MB Stata file. CES (3.5 GB) and PISA (1.9 GB) are big releases.
- The full checksums are in each `data/release/<id>-data/SHA256SUMS`; the table shows the start of a hash of that file, to tell one packaging from another.

## Tag scheme and commands (proposed)

One GitHub release per repo per packaging, tagged with the packaging date: `data-YYYY-MM-DD`. A repo's release holds every dataset release it covers; `SHA256SUMS` and the file names say which. The data's own versions are in the file names and in `sources.yaml`, so the tag only needs to say when it was packaged. The tag isn't `v...`, which stays for the repo's code and metadata. Run from each repo's directory, once Allen decides:

```bash
gh release create data-2026-11-20 --repo AllenDowney/pdt-<id> \
  --title "pdt-<id> data, packaged 2026-11-20" \
  --notes "The publisher's data files and the common-format files (data/processed), with SHA256SUMS. Built from the records at the tagged commit; see README for terms." \
  data/release/<id>-data/*
```

For example, for HINTS:

```bash
cd ~/pdt-hints && gh release create data-2026-11-20 --repo AllenDowney/pdt-hints \
  --title "pdt-hints data, packaged 2026-11-20" \
  --notes "The publisher's data files and the common-format files (data/processed), with SHA256SUMS. Built from the records at the tagged commit; see README for terms." \
  data/release/hints-data/*
```

`gh release create` tags the default branch's HEAD. Each repo's committed records should be the ones the files were built from, so first check that `git status` shows no changes under `metadata/` and that the coordinator has pushed. After any new commit to `metadata/`, run `make data` and `pdt package` again.

## Stopped here

- **pdt-atus and pdt-nlsy97 aren't packaged.** Yellow says their uncommitted changes are only regenerated `docs/` pages (a version stamp), so they're safe to package. ATUS's `make data` takes about 20 minutes and peaks at 3.4 GB. Next: run the same steps on both, add their rows, then `make views` in the repos with C8 failures.
- The scratch driver and its logs are in the session's scratchpad and won't last. The steps above are enough to redo them.

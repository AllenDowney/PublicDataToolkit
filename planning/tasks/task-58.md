# Task 58 — Data builds that fit in memory

**Status:** `DOING (orange)`, from 2026-11-20. Created by the coordinator.

## Why

At 10:53 and 11:04 on 2026-11-20 the kernel's out-of-memory killer stopped a `python` process using 12.8 GB and then 15.3 GB, and every Claude session on the machine crashed with it. Both were orange's `make data` in `~/pdt-gss`, run after the full-GSS rebuild (Task 41's code lists), over all 6,943 variables of the 7224r3a file.

`scripts/build_data.py` calls `pdt.readers.read_stata(path, names)`, which reads every column into one pandas frame. Missing values become `Code` objects, so the frame holds Python objects: about 520 million cells. `pdt.data.split` and `write_release` then copy it again.

## What to do

1. Read, split, write and check in column batches (a few hundred columns at a time). Build the parquet file with pyarrow (one table built from per-batch arrays, or a writer), and round-trip each batch against the Stata file before it's dropped.
2. Keep the output identical: same columns, order, types and file metadata. Compare the new file with one written by the old code on a slice.
3. Measure peak memory with `/usr/bin/time -v` under the board's memory cap, for the full GSS and one other dataset. Target: under about 3 GB.
4. Add a test that the build runs in batches (e.g., a batch size of 2 on a small file gives the same output).
5. Then finish the GSS rebuild: make data, make views, make check, and commit.

Until this is done, don't run `make data` on the full pdt-gss.

## Progress
- 2026-11-20, orange: **committed `acc84a6`.**
  - **Reader:** `read_stata` reads only the columns asked for, with pyreadstat; a `.gz` file is decompressed once per process. A 300-column GSS batch reads in 0.5 GB, against 2.9 GB with `pandas.read_stata`, which parses the whole file. Its cells are identical, type and value, to the old reader on every column of GSS 7224r3a (6,943), 7224r3 (6,942) and the ANES CDF (1,030): 0 differences.
  - **Writer:** `write_release` writes in column batches of 300 and row chunks.
    - Pass 1 splits each chunk, checks its round trip, and writes a part file.
    - Pass 2 gives each column the dtype and code categories `split()` gives the whole column, and assembles the file with pyarrow, a row group per about 25 million cells (`chunk_rows()`): 1,800 rows for the full GSS.
    - A reader may return an iterator of row chunks.
  - **Safety:** the file gets its name only after the round trip, with identity `round_trip: verified`; C3–C5 and C12 skip files without it.
  - **Same output:** files written by the old and new code are identical (columns, types, pandas metadata, identity, data; only the number of row groups differs) on ANES (1 file), FARS (8) and NSFG (6).
  - **Peaks under the 6 GB cap:** ANES `make data` 1.38 GB → 0.76 GB (15 s → 19 s). Full GSS: 0.75–0.9 GB through pass 1 (24 batches, about 55 s each), about 1.3 GB in pass 2.
  - **What went wrong first:** the first full-GSS attempt used 65,536-row chunks and needed several GB per row group across all columns, so the cap stopped it in pass 2. The second split each batch into 42 small chunks, was slow, and grew. Probes showed the reader, split and part writes each flat (250–750 MB). The fix was whole-batch splits, with part files in row groups aligned to the assembly.
  - **Also:** `read_sas` keeps system missing as `Code(".")` (purple); `read_sas_xport` is re-exported; `pyreadstat` is in the data extras. Tests are in `lib/tests/test_release_batched.py`.
  - **Still to come:** the full-GSS wall time and final peak; ATUS activity and summary; then the GSS rebuild.
- 2026-11-20, orange: **pass 2 in Arrow, `029f131`.** The pandas pass 2 converted each row group of each batch to pandas, cast column by column through Python objects and converted back, then did it again to verify; the full GSS would have taken hours. Now a value column is cast only when its chunk's type differs, and a code column's indices are mapped to the whole column's categories with pyarrow. Files written by the old and new code are still identical on ANES, FARS and NSFG. The only differences are the `round_trip` marker, and NSFG 2022–2023's `"."` now recorded as a publisher token (the `read_sas` fix).
- **ATUS, measured on a scratch copy** with yellow's streaming reader, under the 6 GB cap. Both had been killed at the cap before.

  | Table | Size | Peak | Time |
  |---|---|---|---|
  | activity | 4,994,172 rows × 9 variables | 1.85 GB | 4 min 24 s |
  | summary | 258,954 rows × 456 variables (2 column batches) | 1.06 GB | 11 min |
- **Fixes from others:**
  - A table with no records was skipped with an error; it's fixed in purple's `5017b96`, with a test.
  - The replicate columns are also in `5017b96`.

## Stopped here (orange, 2026-11-20)

**Committed in the toolkit:**
- `acc84a6`: the batched reader and writer, the verified-marker gate, the `read_sas` fix and the tests.
- `029f131`: pass 2 in Arrow.
- `eb773e8`: `pdt package` ships current releases by default, with `--release` and `--all`; a release without data files is noted as "not run".
- Purple's `5017b96` fixed the empty-table bug red found.

**Full GSS 7224r3a, measured:** `make data` took about 53 minutes for 7224r3a. The whole run, stopped during 7224r3, took 1 h 08 min and peaked at 4.7 GB: under the 6 GB cap, above the 3 GB target, with the peak in pass 2. Where the time goes: `pdt.data.split` and the round-trip rebuild handle each of 7224r3a's 525 million cells in Python, twice. Vectorizing them is the follow-up that would bring this down to minutes. ATUS activity: 1.85 GB, 4 min 24 s; summary: 1.06 GB, 11 min.

**pdt-gss is uncommitted and not yet checked:**
- the records with the 12 shared code lists (Task 41);
- `data/processed/gss-7224r3a.parquet` (verified; 7224r3's build was stopped and its leftovers removed, per Allen);
- the Makefile's `RELEASES ?= 7224r3a`, `build_data.py` taking releases, and a README note;
- the views, regenerated (2 min 42 s, 380 MB).

**The blocker:** `pdt check` was stopped by the 6 GB cap. Its data checks (C3–C5, C12) read the whole parquet file as one pandas frame (75,699 rows × about 14,000 columns).

**Next:**
1. Make `check.py`'s `load_data` return a lazy frame: columns and row count from the parquet metadata, and a column read only when a check asks for it. Every check reads columns one at a time, or a key's few columns. `check_keys_in_data` needs row filtering on a mask, so the lazy frame should apply a mask to the columns it reads.
2. Test it, then run `pdt check` on pdt-gss under the cap.
3. Commit pdt-gss: metadata/, build/, Makefile, README, scripts/build_data.py, agent/, export/.
4. Tell the coordinator "gss done, <sha>, check 0", and tell green, who swaps in `scripts/extract.py`, and blue.

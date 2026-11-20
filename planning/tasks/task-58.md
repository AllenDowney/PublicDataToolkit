# Task 58 — Data builds that fit in memory

**Status:** `TODO (orange)`. Created by the coordinator, 2026-11-20.

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

# Task 78 — A fast common-format build: vectorized split and round trip

**Status:** `DOING (red)`, assigned by the coordinator on 2026-11-20.

Orange measured the full GSS `make data` at about 50 minutes per release. `pdt.data.split` and the round-trip check (`rebuild`, `same_cells`) handle each of about 525 million cells in Python, once to split and once to verify: about 55 s per 300-column batch.

1. Vectorize with numpy and pyarrow: classify a column's cells against its valid, missing and unresolved codes in bulk, build the value and `__code` columns as arrays, and verify by comparing arrays, not cell by cell.
2. Byte-identical output files (data and file metadata, including `round_trip: verified`) on ANES, FARS, NSFG, BRFSS and a GSS column batch, compared with the current code.
3. The same errors on bad input (an undocumented code, a type mismatch), with tests.
4. Memory no worse, under the cap; benchmark before and after.
5. Changes in `lib/pdt/data.py`. `release.py` is orange's: coordinate before changing it. Don't touch pdt-gss or its running job (read its raw file only for the benchmark batch).

## Progress

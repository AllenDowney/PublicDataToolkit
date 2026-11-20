# Task 78 — A fast common-format build: vectorized split and round trip

**Status:** `DOING (red)`, assigned by the coordinator on 2026-11-20.

Orange measured the full GSS `make data` at about 50 minutes per release. `pdt.data.split` and the round-trip check (`rebuild`, `same_cells`) handle each of about 525 million cells in Python, once to split and once to verify: about 55 s per 300-column batch.

1. Vectorize with numpy and pyarrow: classify a column's cells against its valid, missing and unresolved codes in bulk, build the value and `__code` columns as arrays, and verify by comparing arrays, not cell by cell.
2. Byte-identical output files (data and file metadata, including `round_trip: verified`) on ANES, FARS, NSFG, BRFSS and a GSS column batch, compared with the current code.
3. The same errors on bad input (an undocumented code, a type mismatch), with tests.
4. Memory no worse, under the cap; benchmark before and after.
5. Changes in `lib/pdt/data.py`. `release.py` is orange's: coordinate before changing it. Don't touch pdt-gss or its running job (read its raw file only for the benchmark batch).

## Progress

### Baseline (red, 2026-11-20)

One GSS batch: 300 columns × 75,699 rows of the R3a Stata file, decompressed to a scratch copy, with the 7224r3a records. Code at HEAD 2c3675c, under the 6 GB cap, in the same 41,400-row chunks `write_batched` uses:

| Step | Time | Peak RSS |
|---|---|---|
| `readers.read_stata` (pyreadstat, then a Python loop per cell) | 26.1 s | 2.48 GB after reading |
| `data.split` | 19.1 s | 3.41 GB |
| `data.rebuild` | 15.7 s | |
| `data.same_cells` | 19.5 s | 4.20 GB at the end |

So the split and the round trip take about 54 s per batch, matching orange's 55 s. The reader is another 26 s, which the brief didn't count: its loop per cell (Stata's missing values to `Code`, floats to ints) is worth vectorizing too. A first attempt that also pickled the raw frame was killed at the 6 GB cap: pickling an object frame of 22.7 million cells costs several GB, so don't cache that way.

### Stopped here (2026-11-20, end of session)

No code changed yet; `data.py` is as at HEAD. Next steps:

1. **Keep the per-cell code as the reference.** Rename it `_split_cells`, `_rebuild_cells` and `_same_cells_cells` and keep it for tests. Add property tests comparing the fast and reference paths on random raw columns: ints, floats including NaN and values beyond 2^53, numpy float32, Code tokens, strings, bools, None and pd.NA, numeric and string codes, and token and value texts that collide (the error).
2. **split, vectorized per column:**
   - Classify cells by type once: `types = np.fromiter(map(type, cells), object, n)`. Each distinct type (a handful) is classified as Code, str, bool, number or null, and masks are built with `types == T`.
   - Numeric cells: one float array (`as_float` semantics; float32 through its repr). `np.isin` against the numeric code values, then map code values to texts through a dict lookup on the unique values. String cells: `pd.Series(...).isin(strings)`.
   - The value column is the object array with code and null cells set to None, then `astype(dtype)` as now, so the dtypes are byte-identical.
   - `_value_dtype` gets the same answers from the masks (all whole, abs ≤ INT64_MAX).
   - A column already numeric (float64 or int64 dtype) skips the type pass.
   - Fall back to the reference code for a column with any type the classifier doesn't know.
3. **rebuild:** map the code column's categories through `from_code` once, then `np.where(codes.isna(), values, categories_mapped[codes.cat.codes])`.
4. **same_cells:** compare per column with the same kind classes (code, null, bool, num, val): kind arrays from the type pass, then values within each kind as float arrays (num), `str` arrays (code, val) or bool. Reuse the masks `split` computed if `release.py` passes them; otherwise recompute.
5. **The reader:** `read_stata`'s loop per cell can be vectorized the same way (pyreadstat gives a float column plus strings for missing values). That file is shared; check with orange.
6. **Byte-identical check:** for ANES, FARS, NSFG and BRFSS, run `make data` with the old library (a `git archive` copy of HEAD) and the new into two scratch copies of each repo's `data/processed/`. Compare the files byte for byte, the parquet metadata (`identity_of`, including `round_trip: verified`), and `pq.read_metadata().schema`. For the GSS, one batch: the old and new `split` output frames, `pd.testing.assert_frame_equal(check_exact=True)`, plus the arrow schema of each part file. Benchmark with this file's script (one batch, under the cap).
7. **Errors:** existing tests in `lib/tests/test_data*.py` and `test_release*.py` must pass unchanged; add tests for an undocumented code (stays a value, and C4 reports it), a non-whole value under `storage_type: integer`, mixed types without `storage_type`, and a token/value text collision, with the same messages.

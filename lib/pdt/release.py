"""Write a release's data in the common format (STANDARD.md §8) and prove it lossless.

A dataset repo supplies only a reader for the publisher's format. Its
`scripts/build_data.py` calls `write_release(root, reader)`, where

    reader(release_id, table_id, names) -> (raw DataFrame, source id)

returns the publisher's file (or None to skip a release it can't read) as a raw frame, with at least the columns in `names`
(the variables the repo has records for; `pdt.readers` reads only those): every cell is a value or, for the
publisher's own missing tokens (Stata's ".d", SAS's "."), a `pdt.data.Code`. The
source id names the file in `sources.yaml`, whose SHA-256 goes in the file's identity.

The split uses the corrected records: variables.jsonl with corrections.jsonl applied,
as the views and the export apply them (STANDARD.md §8). The file's identity holds
both files' SHA-256 and lists the corrections applied, with their confidence, so an
inferred correction is visible in the data itself.

Building data/processed/ is allowed for any terms: it's for this machine (extract.py
reads it). Only publishing is blocked (STANDARD.md §9). A file whose terms.data or
source isn't `ship` says why in its identity (`local_only`), and `package` refuses to
put it in a release asset, before writing anything.

    package(root) -> data/release/<dataset>-data/   the publisher's data files, unchanged,
                                                    the common-format files, and SHA256SUMS

For each release, or each table of a release with tables, this writes
`data/processed/<dataset>-<release>[-<table>].parquet` holding the variables the
repo has records for, then reads the file back, rebuilds the raw cells, and
compares them with the reader's frame. A mismatch is an error and the file is removed.
"""

from pathlib import Path

import pandas as pd
import yaml

from . import data
from .check import Repo
from .search import apply_corrections

from .common_format import PROCESSED, file_name  # noqa: E402,F401  (re-exported)


def release_files(dataset_yaml):
    """{(release, table or None): file name} for every release in dataset.yaml."""
    out = {}
    ds = dataset_yaml
    for r in ds.get("releases", []):
        for t in r.get("tables") or [None]:
            tab = t["id"] if t else None
            out[(r["id"], tab)] = file_name(ds["id"], r["id"], tab)
    return out


def data_source(root, release, table=None, format=None):
    """The data file a release (or table) is built from: its source of kind data in sources.yaml.

    dataset.yaml lists each release's (or table's) sources; when several are data files
    (FARS ships CSV and SAS), `format` picks one. Returns the source entry.
    """
    root = Path(root)
    ds = yaml.safe_load((root / "dataset.yaml").read_text())
    sources = {s["id"]: s for s in yaml.safe_load((root / "sources.yaml").read_text())["sources"]}
    r = next(r for r in ds["releases"] if r["id"] == release)
    ids = next(t for t in r["tables"] if t["id"] == table).get("sources", r["sources"]) if table else r["sources"]
    found = [sources[i] for i in ids if i in sources and sources[i]["kind"] == "data"
             and (format is None or sources[i].get("format") == format)]
    if len(found) != 1:
        raise ValueError(f"{release}/{table}: {len(found)} data sources"
                         + (f" of format {format}" if format else "") + f": {[f['id'] for f in found]}")
    return found[0]


def variables_path(root, release, table=None):
    base = Path(root) / "metadata" / "releases" / release
    return base / table / "variables.jsonl" if table else base / "variables.jsonl"


def corrected_records(repo, release, table):
    """{name: record with corrections applied}, and [{id, confidence, name}] of those applied."""
    records, applied = {}, []
    for r in repo.tables[release][table]:
        fixed, done = apply_corrections(r, release, table, repo.corrections)
        records[r["name"]] = fixed
        applied += [{"id": a["id"], "confidence": a["confidence"], "variable": r["name"]} for a in done]
    return records, applied


def check_terms(dataset, source):
    """Why this data may not go in a data release, or None if it may."""
    terms = dataset.get("terms", {}).get("data")
    if terms != "ship":
        return f"terms.data is {terms!r}; only `ship` data goes in a data release (STANDARD.md §9)"
    if source.get("redistribution") != "ship":
        return (f"source {source['id']!r} has redistribution {source.get('redistribution')!r}; "
                "only `ship` sources go in a data release (STANDARD.md §9)")
    return None


def write_one(root, repo, release, table, raw, source_id, log=print):
    root = Path(root)
    sources = {s["id"]: s for s in yaml.safe_load((root / "sources.yaml").read_text())["sources"]}
    refusal = check_terms(repo.dataset, sources.get(source_id, {"id": source_id}))
    records, applied = corrected_records(repo, release, table)
    missing = [n for n in records if n not in raw.columns]
    if missing:
        raise ValueError(f"{release}/{table}: variables with records but not in the data: {missing}")
    raw = raw[list(records)]
    table_df = add_empty_code_columns(data.split(raw, records), records)
    identity = release_identity(root, repo, release, table, source_id, sources, applied, refusal)
    identity["round_trip"] = ROUND_TRIP
    out = root / PROCESSED / file_name(repo.dataset["id"], release, table)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f".{out.name}.tmp")     # the file gets its name only after the round trip
    try:
        data.write(table_df, tmp, identity)
        back = data.read(tmp)
        rebuilt = data.rebuild(back, records)
        if not data.same_cells(raw.reset_index(drop=True), rebuilt.reset_index(drop=True)):
            raise ValueError(f"{out.name}: the round trip changed some cells; nothing written")
        tmp.replace(out)
    finally:
        if tmp.exists():
            tmp.unlink()
    codes = sum(1 for c in back.columns if c.endswith(data.CODE_SUFFIX))
    log(f"  {out.relative_to(root)}: {len(back):,} rows, {len(records)} variables, "
        f"{codes} code columns, {len(applied)} corrections; round trip exact"
        + (f"; local only, not for release: {refusal}" if refusal else ""))
    return out


def add_empty_code_columns(table_df, records):
    """A code column for every variable whose records list missing or unresolved codes, even
    when none occurs in this file, so every release has the same columns as its dictionary."""
    for name, rec in records.items():
        col = name + data.CODE_SUFFIX
        if col not in table_df.columns and any(v.get("kind") != "valid" for v in rec.get("values") or []):
            at = table_df.columns.get_loc(name) + 1
            texts = [data.code_text(v["code"]) for v in rec["values"] if v.get("kind") != "valid"]
            table_df.insert(at, col, pd.Series(pd.Categorical([None] * len(table_df), categories=texts),
                                               index=table_df.index))
    return table_df


def release_identity(root, repo, release, table, source_id, sources, applied, refusal):
    """The file's identity (STANDARD.md §8): what it was built from, so a stale file can be told."""
    identity = {
        "dataset": repo.dataset["id"],
        "release": release,
        "standard_version": repo.dataset.get("standard_version"),
        "metadata_sha256": data.metadata_sha256(variables_path(root, release, table)),
        "source": source_id,
        "source_sha256": sources.get(source_id, {}).get("sha256"),
        "corrections_sha256": data.metadata_sha256(root / "metadata" / "corrections.jsonl")
        if (root / "metadata" / "corrections.jsonl").exists() else None,
        # Shared code lists (STANDARD.md §4.5) are part of the records the file was split with.
        "code_lists_sha256": data.metadata_sha256(root / "metadata" / "code_lists.jsonl")
        if (root / "metadata" / "code_lists.jsonl").exists() else None,
        "corrections": applied,
    }
    if refusal:
        identity["local_only"] = refusal
    if table:
        identity["table"] = table
    return identity


BATCH_COLUMNS = 300     # variables per batch: 300 GSS columns read in about 0.5 GB
CHUNK_CELLS = 25_000_000   # cells per row chunk (and per row group, which spans every column)
MIN_ROWS, MAX_ROWS = 1024, 65536


def chunk_rows(n_variables):
    """Rows per chunk: about CHUNK_CELLS cells, counting a code column per variable. The full GSS
    (6,943 variables) gets 1,800 rows; ATUS activity (9) gets 65,536; ATUS summary (456), 27,412."""
    return max(MIN_ROWS, min(MAX_ROWS, CHUNK_CELLS // max(1, 2 * n_variables)))


ROUND_TRIP = "verified"  # identity["round_trip"]: the file was checked cell by cell before it got its name


def row_chunks(got, rows):
    """Consecutive row chunks of exactly `rows` rows (the last may be shorter), from a whole
    frame or from an iterator of frames (a reader that streams rows, e.g. read_csv(chunksize=))."""
    if isinstance(got, pd.DataFrame):
        for start in range(0, len(got), rows):
            yield got.iloc[start:start + rows].reset_index(drop=True)
        if len(got) == 0:
            yield got
        return
    buffer = None
    for frame in got:
        frame = frame.reset_index(drop=True)
        buffer = frame if buffer is None else pd.concat([buffer, frame], ignore_index=True)
        while len(buffer) >= rows:
            yield buffer.iloc[:rows].reset_index(drop=True)
            buffer = buffer.iloc[rows:].reset_index(drop=True)
    if buffer is not None and (len(buffer) or rows):
        yield buffer


def combined_dtype(name, dtypes):
    """The dtype split() would give the whole column, from the dtypes it gave each chunk."""
    found = set(dtypes) - {"object"}
    if not found:
        return "object"
    if found == {"Int64", "Float64"}:
        return "Float64"         # some chunk has a number that isn't whole (or too big for Int64)
    if len(found) == 1:
        return found.pop()
    raise ValueError(f"{name}: values of mixed types across the file; give its record a storage_type")


def write_batched(root, repo, release, table, read, log=print, batch_size=BATCH_COLUMNS, rows=None):
    """Write one release's (or table's) common-format file in column batches and row chunks,
    so memory follows a batch, not the file (Task 58: the full GSS as one frame needed 13-15 GB;
    ATUS activity has 5 million rows).

    read(names) -> (raw, source id), or None from the first call when the reader can't read the
    source (then nothing is written). raw is a frame of those columns, or an iterator of frames,
    consecutive rows, for a reader that streams.

    Pass 1, per column batch: the rows are split in chunks of about CHUNK_CELLS cells, each chunk
    checked by a round trip against its raw cells and written to a part file in row groups of
    `rows` rows (default chunk_rows(): a row group spans every column, so a wide file gets short
    ones). Pass 2: each column gets the dtype and code categories split() gives the whole column,
    and the parts are written as one file, row group by row group, then compared with the parts.
    The file is written under a temporary name and renamed only then, with
    identity["round_trip"] = "verified". It has the same columns, order, types and metadata as
    write_one gives.
    """
    import json
    import shutil

    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    root = Path(root)
    sources = {s["id"]: s for s in yaml.safe_load((root / "sources.yaml").read_text())["sources"]}
    records, applied = corrected_records(repo, release, table)
    names = list(records)
    rows = rows or chunk_rows(len(names))
    out = root / PROCESSED / file_name(repo.dataset["id"], release, table)
    out.parent.mkdir(parents=True, exist_ok=True)
    work = out.with_name(f".{out.name}.parts")
    tmp = out.with_name(f".{out.name}.tmp")
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir()
    n_batches = -(-len(names) // batch_size)
    try:
        tokens, source_id, n_rows = {}, None, None
        batches = []   # per column batch: column order, chunk size, dtypes and codes seen
        for b, start in enumerate(range(0, len(names), batch_size)):
            cols = names[start:start + batch_size]
            got = read(cols)
            if got is None:
                if b == 0:
                    return None
                raise ValueError(f"{release}/{table}: the reader gave nothing for batch {b}")
            raw_all, source_id = got
            del got
            batch_records = {n: records[n] for n in cols}
            # Pass-1 chunks are a whole number of row groups, so pass 2 reads whole row groups.
            split_rows = max(rows, CHUNK_CELLS // (2 * len(cols)) // rows * rows)
            info = {"order": None, "split_rows": split_rows, "parts": 0, "dtypes": {}, "codes": {}, "observed": {}}
            offset = 0
            for c, raw in enumerate(row_chunks(raw_all, split_rows)):
                missing = [n for n in cols if n not in raw.columns]
                if missing:
                    raise ValueError(f"{release}/{table}: variables with records but not in the data: {missing}")
                raw = raw[cols]
                part_df = add_empty_code_columns(data.split(raw, batch_records), batch_records)
                part_df[data.ROW] = part_df[data.ROW] + offset
                chunk_tokens = part_df.attrs.get("pdt_tokens", {})
                rebuilt = data.rebuild(part_df, batch_records, chunk_tokens)
                if not data.same_cells(raw, rebuilt.reset_index(drop=True)):
                    raise ValueError(f"{out.name}: the round trip changed some cells in batch {b}, rows "
                                     f"{offset} to {offset + len(raw) - 1} ({cols[0]} to {cols[-1]}); nothing written")
                del rebuilt
                for name, texts in chunk_tokens.items():
                    tokens[name] = sorted(set(tokens.get(name, [])) | set(texts))
                for col in part_df.columns:
                    if col == data.ROW:
                        continue
                    if col.endswith(data.CODE_SUFFIX):
                        info["observed"].setdefault(col, set()).update(part_df[col].dropna().astype(str).tolist())
                        info["codes"].setdefault(col, [str(x) for x in part_df[col].cat.categories])
                    else:
                        info["dtypes"].setdefault(col, set()).add(str(part_df[col].dtype))
                if info["order"] is None:
                    info["order"] = list(part_df.columns)
                else:   # a code column a later chunk has, placed after its variable
                    for col in part_df.columns:
                        if col not in info["order"]:
                            info["order"].insert(info["order"].index(col[:-len(data.CODE_SUFFIX)]) + 1, col)
                pq.write_table(pa.Table.from_pandas(part_df, preserve_index=False),
                               work / f"{b:05d}-{c:06d}.parquet", row_group_size=rows)
                offset += len(raw)
                info["parts"] = c + 1
                del raw, part_df
            del raw_all
            if n_rows is None:
                n_rows = offset
            elif offset != n_rows:
                raise ValueError(f"{release}/{table}: batch {b} has {offset} rows, not {n_rows}")
            if b > 0:
                info["order"].remove(data.ROW)     # _row once, first, as write_one has it
            batches.append(info)
            if n_batches > 1:
                log(f"    batch {b + 1}/{n_batches}: {len(cols)} variables, {n_rows:,} rows, round trip exact")

        # The dtype and categories split() gives each whole column.
        final = {}
        for info in batches:
            for col, dtypes in info["dtypes"].items():
                final[col] = combined_dtype(col, dtypes)
            for col in info["codes"]:
                observed = info["observed"].get(col, set())
                final[col] = sorted(observed) if observed else info["codes"][col]

        files = {}

        def template(b):
            """Batch b's final columns, empty: from_pandas gives the arrow types and pandas metadata
            write_one's from_pandas gives the whole column."""
            cols = {}
            for col in batches[b]["order"]:
                if col == data.ROW:
                    cols[col] = pd.Series([], dtype="int64")
                elif col.endswith(data.CODE_SUFFIX):
                    cols[col] = pd.Series(pd.Categorical([], categories=final[col]))
                else:
                    cols[col] = pd.Series([], dtype=final[col])
            return pa.Table.from_pandas(pd.DataFrame(cols), preserve_index=False)

        templates = [template(b) for b in range(len(batches))]

        def finished(b, g):
            """Row group g of column batch b, with the whole column's types and categories (in arrow:
            a value column is cast only when its chunk's type differs, and a code column's indices
            are mapped to the whole column's categories)."""
            info, schema_b = batches[b], templates[b].schema
            part, k = divmod(g * rows, info["split_rows"])
            key = (b, part)
            if key not in files:
                files.clear()     # one batch's file open at a time is enough
                files[key] = pq.ParquetFile(work / f"{b:05d}-{part:06d}.parquet")
            chunk = files[key].read_row_group(k // rows)
            arrays = []
            for field in schema_b:
                col = field.name
                arr = chunk.column(col).combine_chunks() if col in chunk.column_names else None
                if col.endswith(data.CODE_SUFFIX):
                    if arr is None:
                        arr = pa.nulls(chunk.num_rows, field.type)
                    else:
                        if isinstance(arr, pa.ChunkedArray):
                            arr = arr.combine_chunks()
                        position = {text: n for n, text in enumerate(final[col])}
                        mapping = pa.array([position[x] for x in arr.dictionary.to_pylist()],
                                           type=field.type.index_type)
                        arr = pa.DictionaryArray.from_arrays(pc.take(mapping, arr.indices),
                                                             pa.array(final[col], type=field.type.value_type))
                elif not arr.type.equals(field.type):
                    arr = pc.cast(arr, field.type)      # e.g. a chunk of whole numbers in a Float64 column
                arrays.append(arr)
            return pa.Table.from_arrays(arrays, schema=schema_b)

        tokens = {n: tokens[n] for n in names if n in tokens}     # in column order, as split() lists them
        refusal = check_terms(repo.dataset, sources.get(source_id, {"id": source_id}))
        identity = release_identity(root, repo, release, table, source_id, sources, applied, refusal)
        identity["round_trip"] = ROUND_TRIP
        pandas_meta = json.loads(templates[0].schema.metadata[b"pandas"])
        pandas_meta["columns"] = [col for t in templates for col in json.loads(t.schema.metadata[b"pandas"])["columns"]]
        pandas_meta["attributes"] = {"pdt_tokens": tokens}
        metadata = {b"pandas": json.dumps(pandas_meta).encode(),
                    data.META_KEY: json.dumps({**identity, "tokens": tokens,
                                               "pdt_version": data.__version__}).encode()}
        schema = pa.schema([f for t in templates for f in t.schema], metadata=metadata)
        n_groups = max(1, -(-n_rows // rows))
        with pq.ParquetWriter(tmp, schema) as writer:
            for g in range(n_groups):
                parts = [finished(b, g) for b in range(len(batches))]
                writer.write_table(pa.Table.from_arrays([col for t in parts for col in t.columns], schema=schema))
                del parts
        # The file holds what the checked parts hold, row group by row group.
        written = pq.ParquetFile(tmp)
        for g in range(n_groups):
            for b in range(len(batches)):
                part = finished(b, g)
                # compared as pandas frames: a dictionary read back from parquet may list only the
                # categories that occur, and the pandas metadata restores the rest
                back = written.read_row_group(g, columns=part.schema.names)
                if not back.replace_schema_metadata(part.schema.metadata).to_pandas().equals(part.to_pandas()):
                    raise ValueError(f"{out.name}: row group {g}, batch {b} differs from its checked part; "
                                     "nothing written")
        files.clear()
        tmp.replace(out)
    finally:
        shutil.rmtree(work, ignore_errors=True)
        if tmp.exists():
            tmp.unlink()
    codes = sum(1 for f in schema if f.name.endswith(data.CODE_SUFFIX))
    log(f"  {out.relative_to(root)}: {n_rows:,} rows, {len(records)} variables, "
        f"{codes} code columns, {len(applied)} corrections; round trip exact"
        + (f" in {len(batches)} column batches" if len(batches) > 1 else "")
        + (f"; local only, not for release: {refusal}" if refusal else ""))
    return out


def write_release(root, reader, releases=None, log=print, batch_size=BATCH_COLUMNS):
    """Write every release (and table) the reader can read. Returns the paths written.

    reader(release, table, names) -> (raw frame, source id), or None to skip. It's called
    once per batch of `batch_size` variables (write_batched), so a reader that reads only the
    columns asked for keeps memory to a batch.
    """
    root = Path(root)
    repo = Repo.load(root)
    written = []
    for (release, table) in release_files(repo.dataset):
        if releases and release not in releases:
            continue
        names = [r["name"] for r in repo.tables[release][table]]
        path = write_batched(root, repo, release, table,
                             lambda cols, release=release, table=table: reader(release, table, cols),
                             log=log, batch_size=batch_size)
        if path is None:
            log(f"  skipped {release}" + (f"/{table}" if table else "") + ": the reader can't read its source")
            continue
        written.append(path)
    return written


RELEASE = Path("data") / "release"


def package(root, log=print):
    """Assemble the data release asset: publisher's data files, common-format files, SHA256SUMS.

    Refuses, before writing anything, if terms.data isn't ship, if any common-format
    file is local_only or missing, or if a publisher data file isn't ship or is missing.
    Nothing is uploaded; a person publishes the directory as a GitHub release.
    """
    import hashlib
    import shutil
    root = Path(root)
    repo = Repo.load(root)
    problems = []
    terms = check_terms(repo.dataset, {"id": "-", "redistribution": "ship"})
    if terms:
        problems.append(terms)
    sources = {s["id"]: s for s in yaml.safe_load((root / "sources.yaml").read_text())["sources"]}
    files = []
    for (release, table), name in release_files(repo.dataset).items():
        path = root / PROCESSED / name
        if not path.exists():
            problems.append(f"{name} is missing; run make data")
            continue
        ident = data.identity_of(path)
        if ident.get("local_only"):
            problems.append(f"{name}: {ident['local_only']}")
        src = sources.get(ident.get("source"))
        if src is None:
            problems.append(f"{name}: its source {ident.get('source')!r} isn't in sources.yaml")
            continue
        files.append(path)
        # every publisher data file of the release (or table), e.g. a .dat and its .dct
        r = next(r for r in repo.dataset["releases"] if r["id"] == release)
        ids = next(t for t in r["tables"] if t["id"] == table).get("sources", r["sources"]) if table else r["sources"]
        for sid in dict.fromkeys([src["id"]] + [i for i in ids if sources.get(i, {}).get("kind") == "data"]):
            s = sources[sid]
            refusal = check_terms(repo.dataset, s)
            if refusal:
                problems.append(f"{sid}: {refusal}")
            publisher = root / s["path"] if s.get("path") else None
            if publisher is None or not publisher.exists():
                problems.append(f"{sid}: {s.get('path')} is missing")
            else:
                files.append(publisher)
    if problems:
        raise ValueError("not packaged, nothing written:\n  " + "\n  ".join(dict.fromkeys(problems)))
    out = root / RELEASE / f"{repo.dataset['id']}-data"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    sums = []
    for f in dict.fromkeys(files):
        target = out / f.name
        shutil.copyfile(f, target)
        sums.append(f"{hashlib.sha256(target.read_bytes()).hexdigest()}  {f.name}")
        log(f"  {target.relative_to(root)}")
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    return out

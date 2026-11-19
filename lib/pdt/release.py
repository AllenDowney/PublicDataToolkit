"""Write a release's data in the common format (STANDARD.md §8) and prove it lossless.

A dataset repo supplies only a reader for the publisher's format. Its
`scripts/build_data.py` calls `write_release(root, reader)`, where

    reader(release_id, table_id) -> (raw DataFrame, source id)

returns the publisher's file as a raw frame: every cell is a value or, for the
publisher's own missing tokens (Stata's ".d", SAS's "."), a `pdt.data.Code`. The
source id names the file in `sources.yaml`, whose SHA-256 goes in the file's identity.

For each release, or each table of a release with tables, this writes
`data/processed/<dataset>-<release>[-<table>].parquet` holding the variables the
repo has records for, then reads the file back, rebuilds the raw cells, and
compares them with the reader's frame. A mismatch is an error and the file is removed.
"""

from pathlib import Path

import yaml

from . import data
from .check import Repo

PROCESSED = Path("data") / "processed"


def file_name(dataset, release, table=None):
    return f"{dataset}-{release}" + (f"-{table}" if table else "") + ".parquet"


def release_files(dataset_yaml):
    """{(release, table or None): file name} for every release in dataset.yaml."""
    out = {}
    ds = dataset_yaml
    for r in ds.get("releases", []):
        for t in r.get("tables") or [None]:
            tab = t["id"] if t else None
            out[(r["id"], tab)] = file_name(ds["id"], r["id"], tab)
    return out


def variables_path(root, release, table=None):
    base = Path(root) / "metadata" / "releases" / release
    return base / table / "variables.jsonl" if table else base / "variables.jsonl"


def write_one(root, repo, release, table, raw, source_id, log=print):
    root = Path(root)
    records = {r["name"]: r for r in repo.tables[release][table]}
    missing = [n for n in records if n not in raw.columns]
    if missing:
        raise ValueError(f"{release}/{table}: variables with records but not in the data: {missing}")
    raw = raw[list(records)]
    table_df = data.split(raw, records)
    sources = {s["id"]: s for s in yaml.safe_load((root / "sources.yaml").read_text())["sources"]}
    identity = {
        "dataset": repo.dataset["id"],
        "release": release,
        "standard_version": repo.dataset.get("standard_version"),
        "metadata_sha256": data.metadata_sha256(variables_path(root, release, table)),
        "source": source_id,
        "source_sha256": sources.get(source_id, {}).get("sha256"),
    }
    if table:
        identity["table"] = table
    out = root / PROCESSED / file_name(repo.dataset["id"], release, table)
    out.parent.mkdir(parents=True, exist_ok=True)
    data.write(table_df, out, identity)

    back = data.read(out)
    rebuilt = data.rebuild(back, records)
    if not data.same_cells(raw.reset_index(drop=True), rebuilt.reset_index(drop=True)):
        out.unlink()
        raise ValueError(f"{out.name}: the round trip changed some cells; file removed")
    codes = sum(1 for c in back.columns if c.endswith(data.CODE_SUFFIX))
    log(f"  {out.relative_to(root)}: {len(back):,} rows, {len(records)} variables, "
        f"{codes} code columns; round trip exact")
    return out


def write_release(root, reader, releases=None, log=print):
    """Write every release (and table) the reader can read. Returns the paths written."""
    root = Path(root)
    repo = Repo.load(root)
    written = []
    for (release, table) in release_files(repo.dataset):
        if releases and release not in releases:
            continue
        raw, source_id = reader(release, table)
        written.append(write_one(root, repo, release, table, raw, source_id, log=log))
    return written

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

Only data whose terms allow it is packaged: terms.data and the source's redistribution
must both be `ship` (STANDARD.md §9). `local=True` builds the files anyway, for use on
this machine (by extract.py, say); their identity says `local_only`, and the upload
step refuses them.

For each release, or each table of a release with tables, this writes
`data/processed/<dataset>-<release>[-<table>].parquet` holding the variables the
repo has records for, then reads the file back, rebuilds the raw cells, and
compares them with the reader's frame. A mismatch is an error and the file is removed.
"""

from pathlib import Path

import yaml

from . import data
from .check import Repo
from .search import apply_corrections

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


def write_one(root, repo, release, table, raw, source_id, log=print, local=False):
    root = Path(root)
    sources = {s["id"]: s for s in yaml.safe_load((root / "sources.yaml").read_text())["sources"]}
    refusal = check_terms(repo.dataset, sources.get(source_id, {"id": source_id}))
    if refusal and not local:
        raise ValueError(f"{release}" + (f"/{table}" if table else "") + f": {refusal}; nothing written "
                         "(use local=True to build it for this machine only)")
    records, applied = corrected_records(repo, release, table)
    missing = [n for n in records if n not in raw.columns]
    if missing:
        raise ValueError(f"{release}/{table}: variables with records but not in the data: {missing}")
    raw = raw[list(records)]
    table_df = data.split(raw, records)
    identity = {
        "dataset": repo.dataset["id"],
        "release": release,
        "standard_version": repo.dataset.get("standard_version"),
        "metadata_sha256": data.metadata_sha256(variables_path(root, release, table)),
        "source": source_id,
        "source_sha256": sources.get(source_id, {}).get("sha256"),
        "corrections_sha256": data.metadata_sha256(root / "metadata" / "corrections.jsonl")
        if (root / "metadata" / "corrections.jsonl").exists() else None,
        "corrections": applied,
    }
    if refusal:
        identity["local_only"] = refusal
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
        f"{codes} code columns, {len(applied)} corrections; round trip exact"
        + ("; LOCAL ONLY, not for release" if refusal else ""))
    return out


def write_release(root, reader, releases=None, log=print, local=False):
    """Write every release (and table) the reader can read. Returns the paths written."""
    root = Path(root)
    repo = Repo.load(root)
    refusal = check_terms(repo.dataset, {"id": "-", "redistribution": "ship"})
    if refusal and not local:
        raise ValueError(f"{refusal}; nothing written (use local=True to build for this machine only)")
    written = []
    for (release, table) in release_files(repo.dataset):
        if releases and release not in releases:
            continue
        names = [r["name"] for r in repo.tables[release][table]]
        got = reader(release, table, names)
        if got is None:
            log(f"  skipped {release}" + (f"/{table}" if table else "") + ": the reader can't read its source")
            continue
        raw, source_id = got
        written.append(write_one(root, repo, release, table, raw, source_id, log=log, local=local))
    return written

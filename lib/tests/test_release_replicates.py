"""Replicate weights named by design.replicates go in the common-format file without records
(STANDARD.md §2.1): write_release adds them to the columns it reads and writes."""

import json

import pandas as pd
import pytest

from pdt import data, release
from pdt.check import Repo, run as run_all
from test_check import DATASET, VARIABLES, make_repo

PUBLISHER = {"origin": "publisher", "source": "cb"}
RECORDS = [dict(VARIABLES[0], storage_type="integer"),
           {"dataset": "toy", "release": "r1", "name": "wt", "label": "Weight", "storage_type": "float",
            "measure": "weight", "provenance": {"record": PUBLISHER}}]


def raw(n_reps=3, prefix="W"):
    frame = pd.DataFrame({"q1": [1, 9, 1, 1], "wt": [1.5, 2.0, 0.5, 1.0]}).astype(object)
    for i in range(1, n_reps + 1):
        frame[f"{prefix}{i}"] = [1.0 * i, 2.0, 0.25, 4.0]
    return frame


def repo_with(tmp_path, replicates, records=RECORDS):
    ds = json.loads(json.dumps(DATASET))
    ds["design"] = {"weights": ["wt"], "replicates": replicates}
    return make_repo(tmp_path, dataset=ds, variables=records, groups=[], corrections=[])


def write(root, frame):
    seen = []

    def reader(rel, tab, names):
        seen.append(list(names))
        return frame[[n for n in names if n in frame.columns]], "cb"
    paths = release.write_release(root, reader, log=lambda *a: None)
    return paths, seen


def test_prefix_replicates_are_written_without_records(tmp_path):
    root = repo_with(tmp_path, {"prefix": "W", "n": 3, "method": "brr"})
    assert release.replicate_extras(Repo.load(root), "r1", None, {r["name"]: r for r in RECORDS}) == ["W1", "W2", "W3"]
    (path,), seen = write(root, raw())
    assert seen[0] == ["q1", "wt", "W1", "W2", "W3"]
    back = data.read(path)
    assert [c for c in back.columns if c.startswith("W")] == ["W1", "W2", "W3"]
    assert back["W1"].tolist() == [1.0, 2.0, 0.25, 4.0]
    assert data.identity_of(path)["round_trip"] == "verified"
    result = run_all(root, views=False)
    assert not [f for f in result.failures if f.startswith("C3")], result.failures


def test_named_replicates(tmp_path):
    root = repo_with(tmp_path, {"variables": ["RA", "RB"], "method": "jk1"})
    frame = raw(0).assign(RA=[1.0, 1.0, 1.0, 1.0], RB=[2.0, 2.0, 2.0, 2.0])
    (path,), seen = write(root, frame)
    assert seen[0][-2:] == ["RA", "RB"] and list(data.read(path).columns)[-2:] == ["RA", "RB"]


def test_replicates_with_records_add_nothing(tmp_path):
    """ATUS keeps records for its zero-padded TUFNWGTP001..: those are the columns, nothing more."""
    reps = [{"dataset": "toy", "release": "r1", "name": f"W00{i}", "storage_type": "float", "measure": "weight",
             "provenance": {"record": PUBLISHER}} for i in (1, 2, 3)]
    root = repo_with(tmp_path, {"prefix": "W", "n": 3, "method": "sdr"}, RECORDS + reps)
    records = {r["name"]: r for r in RECORDS + reps}
    assert release.replicate_extras(Repo.load(root), "r1", None, records) == []


def test_replicates_in_another_table_add_nothing_here(tmp_path):
    root = repo_with(tmp_path, {"prefix": "W", "n": 3, "method": "sdr", "table": "repwgt", "key": ["q1"]})
    assert release.replicate_extras(Repo.load(root), "r1", None, {r["name"]: r for r in RECORDS}) == []


def test_missing_replicates_are_an_error(tmp_path):
    root = repo_with(tmp_path, {"prefix": "W", "n": 4, "method": "brr"})
    with pytest.raises(ValueError, match="replicate weights design.replicates names"):
        write(root, raw(3))
    assert not list((root / "data" / "processed").glob("*.parquet"))


def test_write_one_adds_them_too(tmp_path):
    root = repo_with(tmp_path, {"prefix": "W", "n": 3, "method": "brr"})
    path = release.write_one(root, Repo.load(root), "r1", None, raw(), "cb", log=lambda *a: None)
    assert [c for c in data.read(path).columns if c.startswith("W")] == ["W1", "W2", "W3"]


def test_a_table_without_records_is_skipped(tmp_path):
    """A fresh repo (empty variables.jsonl) writes nothing and doesn't fail (red's report)."""
    root = make_repo(tmp_path, variables=[])
    logged = []
    assert release.write_release(root, lambda rel, tab, names: (raw(), "cb"), log=logged.append) == []
    assert logged == ["  skipped r1: no records"]
    assert release.write_batched(root, Repo.load(root), "r1", None, lambda cols: (raw(), "cb")) is None

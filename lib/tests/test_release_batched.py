"""Task 58: write_release reads, splits, writes and checks in column batches, and the result
is the same file write_one makes from the whole frame (in row groups of a few thousand rows)."""

import json

import pandas as pd
import pyarrow.parquet as pq
import pytest

from pdt import data, release
from pdt.check import Repo

from test_check import PUBLISHER, make_repo

MISSING = {"kind": "missing", "missing_types": ["no_answer"], "origin": PUBLISHER}


def var(name, values=None):
    r = {"dataset": "toy", "release": "r1", "name": name, "label": name, "provenance": {"record": PUBLISHER}}
    if values is not None:
        r["values"] = values
    return r


VARIABLES = [
    var("q1", [{"code": 1, "label": "yes", "kind": "valid"}, {"code": 9, "label": "NA", **MISSING}]),
    var("q2"),                                                                  # strings, no codes
    var("q3", [{"code": 98, "label": "DK", **MISSING}]),                       # a code that never occurs
    var("q4", [{"code": ".d", "label": "dk", **MISSING}]),                     # a publisher token
    var("q5"),                                                                  # plain numbers
]


def raw_frame():
    return pd.DataFrame({
        "q1": [1, 9, data.Code("."), 1, 1, 9, 1],
        "q2": ["x", None, "y", "z", "w", "v", None],
        "q3": [3, 4, 5, None, 6, 7, 8],
        "q4": [2, data.Code(".d"), 2, 3, data.Code(".d"), 4, 5],
        "q5": [1.5, 2.5, None, 4.0, 5.5, 6.0, 7.25],
        "extra": [0] * 7}, dtype=object)


def subdir(tmp_path, name):
    (tmp_path / name).mkdir()
    return tmp_path / name


def test_batched_file_is_the_file_write_one_makes(tmp_path):
    whole = make_repo(subdir(tmp_path, "whole"), variables=VARIABLES)
    path_a = release.write_one(whole, Repo.load(whole), "r1", None, raw_frame(), "cb", log=lambda *a: None)

    batched = make_repo(subdir(tmp_path, "batched"), variables=VARIABLES)
    calls = []

    def read(cols):
        calls.append(list(cols))
        return raw_frame()[cols], "cb"

    path_b = release.write_batched(batched, Repo.load(batched), "r1", None, read,
                                   log=lambda *a: None, batch_size=2, rows=3)
    assert calls == [["q1", "q2"], ["q3", "q4"], ["q5"]]                  # read in batches

    a, b = pq.read_schema(path_a), pq.read_schema(path_b)
    assert a.names == b.names and a.types == b.types                       # same columns, order, types
    assert json.loads(a.metadata[b"pandas"]) == json.loads(b.metadata[b"pandas"])
    assert data.identity_of(path_a) == data.identity_of(path_b)            # identity and tokens
    assert data.read(path_a).equals(data.read(path_b))
    assert pq.ParquetFile(path_b).metadata.num_row_groups == 3              # 7 rows in groups of 3
    assert not list(path_b.parent.glob(".*"))                               # parts and temp file gone


def test_write_release_batches_and_skips(tmp_path):
    root = make_repo(tmp_path, variables=VARIABLES)
    seen = []

    def reader(rel, tab, names):
        seen.append(len(names))
        return raw_frame(), "cb"

    path, = release.write_release(root, reader, log=lambda *a: None, batch_size=2)
    assert seen == [2, 2, 1]
    assert data.read(path)["q4__code"].astype(object).tolist()[1] == ".d"
    assert release.write_release(root, lambda rel, tab, names: None, log=lambda *a: None) == []


def test_a_batch_that_does_not_round_trip_writes_nothing(tmp_path, monkeypatch):
    root = make_repo(tmp_path, variables=VARIABLES)
    real = data.rebuild

    def broken(table, records=None, tokens=None):
        out = real(table, records, tokens)
        if "q3" in out.columns:
            out["q3"] = out["q3"].map(lambda x: 0 if x == 3 else x)
        return out

    monkeypatch.setattr(data, "rebuild", broken)
    with pytest.raises(ValueError, match="batch 1"):
        release.write_release(root, lambda rel, tab, names: (raw_frame(), "cb"), log=lambda *a: None,
                              batch_size=2)
    assert not (root / "data" / "processed" / "toy-r1.parquet").exists()
    assert not list((root / "data" / "processed").glob(".*"))


@pytest.mark.parametrize("chunk_cells", [release.CHUNK_CELLS, 12])
def test_streaming_reader_and_chunk_differences(tmp_path, monkeypatch, chunk_cells):
    """A reader that yields 2-row frames; a column that's whole numbers until a late chunk; a
    code column that first appears in the last chunk. The file equals write_one's."""
    variables = VARIABLES + [var("q6"), var("q7")]

    def frame():
        f = raw_frame()
        f["q6"] = pd.Series([1, 2, 3, 4, 5, 6, 7.5], dtype=object)            # Float64 only in the last chunk
        f["q7"] = pd.Series([1, 2, 3, 4, 5, 6, data.Code(".")], dtype=object)  # a token only in the last chunk
        return f

    whole = make_repo(subdir(tmp_path, "whole"), variables=variables)
    path_a = release.write_one(whole, Repo.load(whole), "r1", None, frame(), "cb", log=lambda *a: None)
    streamed = make_repo(subdir(tmp_path, "streamed"), variables=variables)

    def read(cols):
        f = frame()[cols]
        return (f.iloc[i:i + 2] for i in range(0, len(f), 2)), "cb"

    monkeypatch.setattr(release, "CHUNK_CELLS", chunk_cells)   # 12: pass-1 chunks of 3 rows each
    path_b = release.write_batched(streamed, Repo.load(streamed), "r1", None, read,
                                   log=lambda *a: None, batch_size=3, rows=3)
    a, b = pq.read_schema(path_a), pq.read_schema(path_b)
    assert a.names == b.names and a.types == b.types
    assert json.loads(a.metadata[b"pandas"]) == json.loads(b.metadata[b"pandas"])
    assert data.identity_of(path_a) == data.identity_of(path_b)
    assert data.read(path_a).equals(data.read(path_b))
    assert str(data.read(path_b)["q6"].dtype) == "Float64"
    assert data.identity_of(path_b)["round_trip"] == "verified"
    assert data.read(path_b)["_row"].tolist() == list(range(7))


def test_unverified_file_is_skipped_by_the_data_checks(tmp_path):
    from test_check import run
    root = make_repo(tmp_path, variables=VARIABLES)
    path, = release.write_release(root, lambda rel, tab, names: (raw_frame(), "cb"), log=lambda *a: None)
    assert not [r for r in run(root).reports if "no record of a verified round trip" in r]
    # A file without the marker (an older pdt, or an interrupted run) isn't trusted.
    table = pq.read_table(path)
    meta = dict(table.schema.metadata)
    ident = json.loads(meta[data.META_KEY])
    ident.pop("round_trip")
    meta[data.META_KEY] = json.dumps(ident).encode()
    pq.write_table(table.replace_schema_metadata(meta), path)
    assert [r for r in run(root).reports if "no record of a verified round trip" in r]


def test_read_sas_system_missing_is_a_code(monkeypatch):
    """pandas' where() dropped the Code subclass; a plain "." then split as a value."""
    from pdt import readers
    monkeypatch.setattr(readers.pd, "read_sas",
                        lambda *a, **k: pd.DataFrame({"INCOME": [1.0, float("nan"), 3.0], "X": ["a", "b", "c"]}))
    raw = readers.read_sas("unused.sas7bdat", ["INCOME"])
    cells = raw["INCOME"].tolist()
    assert cells[0] == 1.0 and isinstance(cells[1], data.Code) and str(cells[1]) == "."

"""Tests for the data checks in `pdt check` (C3, C4, C5, C12): a small two-table repo
with common-format files, and each kind of breakage."""

import pandas as pd
import pytest

from pdt import data
from pdt.check import processed_name, run
from pdt.release import file_name

from test_check import DATASET, README, SOURCES, write_jsonl
import yaml

PUB = {"origin": "publisher", "source": "cb"}
YEARS = [{"wave": 2020}, {"wave": 2021}]


def var(name, values=None, availability=YEARS, **extra):
    r = {"dataset": "toy", "release": "r1", "name": name, "provenance": {"record": PUB},
         "availability": availability, **extra}
    if values is not None:
        r["values"] = values
    return r


def crash_records(**changes):
    recs = [var("ID", measure="identifier"),
            var("YEAR", measure="continuous"),
            var("LIGHT", measure="categorical",
                values=[{"code": 1, "label": "Day", "kind": "valid"},
                        {"code": 2, "label": "Dark", "kind": "valid"},
                        {"code": 9, "label": "Unknown", "kind": "missing", "missing_types": ["unknown"],
                         "origin": PUB}])]
    for name, change in changes.items():
        recs = [dict(r, **change) if r["name"] == name else r for r in recs]
    return [dict(r, table="crash") for r in recs]


def person_records(availability=YEARS):
    return [dict(r, table="person", availability=availability) for r in
            [var("ID", measure="identifier"), var("PNO", measure="identifier"),
             var("PTYPE", measure="categorical",
                 values=[{"code": 1, "label": "Occupant", "kind": "valid"},
                         {"code": 5, "label": "Pedestrian", "kind": "valid"}])]]


CRASH = pd.DataFrame({"ID": [1, 2, 3, 4], "YEAR": [2020, 2020, 2021, 2021], "LIGHT": [1, 2, 9, 1]})
PERSON = pd.DataFrame({"ID": [1, 1, 2, 7], "PNO": [1, 2, 1, 1], "PTYPE": [1, 1, 1, 5]})
TABLES = [{"id": "crash", "label": "Crashes", "key": ["ID"]},
          {"id": "person", "label": "People", "key": ["ID", "PNO"],
           "references": [{"columns": ["ID"], "table": "crash", "when": {"column": "PTYPE", "in": [1]}}]}]


def make_data_repo(root, crash=CRASH, person=PERSON, crash_recs=None, tables=TABLES, write=("crash", "person"),
                   person_avail=YEARS):
    root.mkdir(parents=True, exist_ok=True)
    dataset = dict(DATASET, dimensions={"wave": {"label": "year", "column": "YEAR"}},
                   releases=[dict(DATASET["releases"][0], tables=tables)])
    (root / "dataset.yaml").write_text(yaml.safe_dump(dataset))
    (root / "sources.yaml").write_text(yaml.safe_dump(SOURCES))
    (root / "README.md").write_text(README)
    (root / "CLAUDE.md").write_text("# toy\n")
    (root / "EXTENSIONS.md").write_text("# Extensions\n")
    records = {"crash": crash_recs or crash_records(), "person": person_records(person_avail)}
    frames = {"crash": crash, "person": person}
    for table, recs in records.items():
        path = root / "metadata" / "releases" / "r1" / table / "variables.jsonl"
        write_jsonl(path, recs)
        if table in write:
            out = root / "data" / "processed" / processed_name("toy", "r1", table)
            out.parent.mkdir(parents=True, exist_ok=True)
            raw = frames[table].astype(object)
            data.write(data.split(raw, {r["name"]: r for r in recs}), out,
                       {"dataset": "toy", "release": "r1", "metadata_sha256": data.metadata_sha256(path)})
    return root


def failures(result, check):
    return [f for f in result.failures if f.startswith(check)]


def reports(result, check):
    return [r for r in result.reports if r.startswith(check)]


def test_file_name_matches_pdt_release():
    assert processed_name("toy", "r1", "crash") == file_name("toy", "r1", "crash")
    assert processed_name("toy", "r1") == file_name("toy", "r1")


def test_valid_data_passes(tmp_path):
    result = run(make_data_repo(tmp_path))
    assert result.ok, result.failures
    assert not reports(result, "C3-C5") and not reports(result, "C4") and not reports(result, "C12")
    # person has no wave column and two waves: C5 can't tell which rows are which.
    assert reports(result, "C5") == ["C5: r1/person: skipped, no wave column (YEAR) and several waves declared"]


def test_skipped_without_data_files(tmp_path):
    result = run(make_data_repo(tmp_path, write=()))
    assert result.ok
    assert any("no data file" in r for r in reports(result, "C3-C5, C12"))


def test_skipped_when_built_from_other_records(tmp_path):
    root = make_data_repo(tmp_path)
    path = root / "metadata" / "releases" / "r1" / "crash" / "variables.jsonl"
    path.write_text(path.read_text() + "\n")
    result = run(root)
    assert any("built from other records" in r for r in reports(result, "C3-C5, C12"))
    assert not failures(result, "C3")


def test_c3_record_without_column(tmp_path):
    recs = crash_records() + [dict(var("EXTRA"), table="crash")]
    result = run(make_data_repo(tmp_path, crash_recs=recs, crash=CRASH.assign(EXTRA=[1, 2, 3, 4])))
    assert result.ok  # written with the column
    # Now drop the column from the file but keep the record.
    root = make_data_repo(tmp_path / "b", crash_recs=crash_records())
    rec_path = root / "metadata" / "releases" / "r1" / "crash" / "variables.jsonl"
    write_jsonl(rec_path, recs)
    frame = data.read(root / "data" / "processed" / "toy-r1-crash.parquet")
    data.write(frame, root / "data" / "processed" / "toy-r1-crash.parquet",
               {"dataset": "toy", "release": "r1", "metadata_sha256": data.metadata_sha256(rec_path)})
    assert any("EXTRA" in f for f in failures(run(root), "C3"))


def test_c4_code_not_in_values(tmp_path):
    root = make_data_repo(tmp_path)
    rec_path = root / "metadata" / "releases" / "r1" / "crash" / "variables.jsonl"
    # The file has code 9; the records no longer list it.
    recs = crash_records(LIGHT={"values": crash_records()[2]["values"][:2]})
    write_jsonl(rec_path, recs)
    path = root / "data" / "processed" / "toy-r1-crash.parquet"
    frame = data.read(path)
    data.write(frame, path, {"dataset": "toy", "release": "r1", "metadata_sha256": data.metadata_sha256(rec_path)})
    assert any("LIGHT: codes not in values: 9" in f for f in failures(run(root), "C4"))


def test_c4_unlisted_valid_value_is_reported(tmp_path):
    result = run(make_data_repo(tmp_path, crash=CRASH.assign(LIGHT=[1, 2, 3, 1])))
    assert result.ok
    assert any("LIGHT: valid values not listed in values: 3" in r for r in reports(result, "C4"))


def test_c5_waves_warn(tmp_path):
    recs = crash_records(LIGHT={"availability": [{"wave": 2020}, {"wave": 2022}]})
    result = run(make_data_repo(tmp_path, crash_recs=recs))
    assert result.ok  # C5 warns
    msgs = reports(result, "C5")
    assert any("LIGHT" in m and "no non-missing values: 2022" in m for m in msgs)
    assert any("LIGHT" in m and "not in availability: 2021" in m for m in msgs)


def test_c5_one_wave_per_file_without_wave_column(tmp_path):
    # person has no YEAR column; with one wave declared, the file is that wave (NSFG, FARS).
    one = [{"wave": 2020}]
    root = make_data_repo(tmp_path, crash_recs=[dict(r, availability=one) for r in crash_records()],
                          crash=CRASH.assign(YEAR=2020), person_avail=one)
    assert not reports(run(root), "C5")
    # A wave declared but empty is still caught without the column.
    root = make_data_repo(tmp_path / "b", crash_recs=[dict(r, availability=one) for r in crash_records()],
                          crash=CRASH.assign(YEAR=2020), person_avail=one,
                          person=PERSON.assign(PTYPE=None))
    assert any("PTYPE" in m and "no non-missing values: 2020" in m for m in reports(run(root), "C5"))


def test_c12_duplicate_and_blank_keys(tmp_path):
    person = pd.DataFrame({"ID": [1, 1, 2, None], "PNO": [1, 1, 1, 1], "PTYPE": [1, 1, 1, 5]})
    msgs = failures(run(make_data_repo(tmp_path, person=person)), "C12")
    assert any("1 duplicate keys" in m for m in msgs)
    assert any("1 rows with a blank key" in m for m in msgs)


def test_c12_reference_respects_when(tmp_path):
    # ID 7 has PTYPE 5, outside `when`, so it needn't match a crash.
    assert not failures(run(make_data_repo(tmp_path)), "C12")
    person = PERSON.assign(PTYPE=[1, 1, 1, 1])
    msgs = failures(run(make_data_repo(tmp_path / "b", person=person)), "C12")
    assert any("-> crash when PTYPE in [1]: 1 of 4 rows without a match" in m for m in msgs)


def test_checks_use_corrected_records(tmp_path):
    # The record lists code 3 as unresolved; a correction makes it valid, and the file
    # is split with the corrected record, so 3 is in the value column.
    unresolved = {"code": 3, "label": "", "kind": "unresolved", "origin": PUB}
    valid = {"code": 3, "label": "Dusk", "kind": "valid"}
    values = crash_records()[2]["values"] + [unresolved]
    recs = crash_records(LIGHT={"values": values})
    corrected = crash_records(LIGHT={"values": crash_records()[2]["values"] + [valid]})
    root = make_data_repo(tmp_path, crash_recs=recs, crash=CRASH.assign(LIGHT=[1, 2, 3, 1]))
    correction = {"id": "light-3", "target": {"name": "LIGHT", "table": "crash", "field": "/values/3"},
                  "original": unresolved, "corrected": valid, "problem": "Undocumented.",
                  "evidence": [{"citation": "Data"}], "confidence": "inferred",
                  "upstream": {"status": "not_filed"}, "author": "Tester", "date": "2026-11-19"}
    write_jsonl(root / "metadata" / "corrections.jsonl", [correction])
    path = root / "data" / "processed" / "toy-r1-crash.parquet"
    rec_path = root / "metadata" / "releases" / "r1" / "crash" / "variables.jsonl"
    data.write(data.split(CRASH.assign(LIGHT=[1, 2, 3, 1]).astype(object), {r["name"]: r for r in corrected}), path,
               {"dataset": "toy", "release": "r1", "metadata_sha256": data.metadata_sha256(rec_path)})
    result = run(root)
    assert result.ok, result.failures
    assert not reports(result, "C4")

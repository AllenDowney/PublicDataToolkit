"""C2 for code_of (STANDARD.md §4.1) and for design.replicates in another table (§2.1)."""

import copy

import pandas as pd

from test_check import TABLED_DATASET, make_tabled_repo, run, tabled
from test_code_lists import OCC, RECORDS, failures, repo_with_lists


def minutes(name, code_list, code):
    return {"dataset": "toy", "release": "r1", "name": name, "label": name,
            "code_of": {"code_list": code_list, "code": code}, "provenance": {"record": {"origin": "publisher"}}}


def test_code_of_passes_when_list_and_code_exist(tmp_path):
    result = run(repo_with_lists(tmp_path, records=RECORDS + [minutes("t10", "occ-2010", 10)]))
    assert not failures(result, "C2")


def test_code_of_unknown_list_or_code_fails(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(), b.mkdir()
    assert any("unknown code list occ-1980" in f
               for f in failures(run(repo_with_lists(a, records=RECORDS + [minutes("t10", "occ-1980", 10)])), "C2"))
    assert any("code 99 isn't in code list occ-2010" in f
               for f in failures(run(repo_with_lists(b, records=RECORDS + [minutes("t99", "occ-2010", 99)])), "C2"))


# ------------------------------------------------------------------ replicates in another table

def dataset_with_replicates(**rep):
    ds = copy.deepcopy(TABLED_DATASET)
    tables = ds["releases"][0]["tables"]
    tables.append({"id": "reps", "label": "Replicate weights", "key": ["CASEID"],
                   "references": [{"columns": ["CASEID"], "table": "female"}]})
    replicates = dict({"table": "reps", "key": ["CASEID"], "prefix": "R", "n": 2, "method": "fay", "fay_factor": 0.5},
                      **rep)
    tables[0]["design"] = {"weights": ["W", {"name": "W20", "waves": [2020]}], "replicates": replicates}
    return ds


def rep_tables(names=("R001", "R002")):
    from test_check import TABLED
    return dict(TABLED, female=TABLED["female"] + [tabled("female", "W"), tabled("female", "W20")],
                reps=[tabled("reps", "CASEID")] + [tabled("reps", n) for n in names])


def test_replicates_in_another_table_pass(tmp_path):
    result = run(make_tabled_repo(tmp_path, dataset=dataset_with_replicates(), tables=rep_tables()))
    assert not failures(result, "C2"), result.failures
    assert not failures(result, "C1"), result.failures   # weights in object form are valid


def test_replicates_unknown_table_missing_key_or_columns_fail(tmp_path):
    cases = {
        "isn't a table": (dataset_with_replicates(table="nope"), rep_tables()),
        "needs a key": (dataset_with_replicates(key=None), rep_tables()),
        "names 2 columns; found 1": (dataset_with_replicates(), rep_tables(("R001",))),
    }
    for i, (expect, (ds, tables)) in enumerate(cases.items()):
        if ds["releases"][0]["tables"][0]["design"]["replicates"].get("key") is None:
            del ds["releases"][0]["tables"][0]["design"]["replicates"]["key"]
        root = tmp_path / str(i)
        root.mkdir()
        assert any(expect in f for f in failures(run(make_tabled_repo(root, dataset=ds, tables=tables)), "C2")), expect


def test_replicate_columns_without_records_are_found_in_the_data_file(tmp_path):
    root = make_tabled_repo(tmp_path, dataset=dataset_with_replicates(), tables=rep_tables(()))
    assert any("found 0" in f for f in failures(run(root), "C2"))
    out = root / "data" / "processed" / "toy-r1-reps.parquet"
    out.parent.mkdir(parents=True)
    pd.DataFrame({"CASEID": [1], "R001": [1.0], "R002": [2.0]}).to_parquet(out)
    assert not any("design.replicates" in f for f in failures(run(root), "C2"))

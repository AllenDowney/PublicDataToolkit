"""C2 and C12 for design.table and design.key (STANDARD.md §2.1): strata and PSU in another table."""

import copy

import pandas as pd

from test_check import TABLED_DATASET, make_tabled_repo, run, tabled
from test_code_lists import failures


def dataset(**design):
    ds = copy.deepcopy(TABLED_DATASET)
    t = ds["releases"][0]["tables"]
    t.append({"id": "py", "label": "Person-year", "key": ["CASEID", "YEAR"],
              "references": [{"columns": ["CASEID"], "table": "female"}],
              "design": dict({"weights": ["W"], "strata": "VSTRAT", "psu": "VPSU", "table": "female", "key": ["CASEID"]},
                             **design)})
    return ds


def tables(extra_female=("VSTRAT", "VPSU")):
    from test_check import TABLED
    return dict(TABLED, female=TABLED["female"] + [tabled("female", n) for n in extra_female],
                py=[tabled("py", "CASEID"), tabled("py", "YEAR"), tabled("py", "W")])


def test_design_in_another_table_passes(tmp_path):
    result = run(make_tabled_repo(tmp_path, dataset=dataset(), tables=tables()))
    assert not failures(result, "C2"), result.failures


def test_design_table_problems_fail(tmp_path):
    cases = {"isn't a table": (dataset(table="nope"), tables()),
             "VPSU, which has no record": (dataset(), tables(("VSTRAT",)))}
    for i, (expect, (ds, tbls)) in enumerate(cases.items()):
        root = tmp_path / str(i)
        root.mkdir()
        assert any(expect in f for f in failures(run(make_tabled_repo(root, dataset=ds, tables=tbls)), "C2")), expect


def test_design_join_in_the_data(tmp_path):
    from pdt.check import Result, Repo, check_design_joins
    root = make_tabled_repo(tmp_path, dataset=dataset(), tables=tables())
    repo = Repo.load(root)
    frames = {("r1", "py"): (pd.DataFrame({"CASEID": [1, 2, 3], "YEAR": [1, 1, 1], "W": [1, 1, 1]}), []),
              ("r1", "female"): (pd.DataFrame({"CASEID": [1, 2], "VSTRAT": [1, 1], "VPSU": [1, 2]}), [])}
    result = Result()
    check_design_joins(repo, frames, result)
    assert any("1 of 3 rows without a match" in f for f in result.failures)

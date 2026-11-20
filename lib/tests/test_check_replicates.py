"""C3 and design.replicates: a replicate-weight column needs no record (STANDARD.md §2.1)."""

import yaml

from test_check_data import CRASH, failures, make_data_repo, run


def with_design(root, design):
    ds = yaml.safe_load((root / "dataset.yaml").read_text())
    ds["design"] = design
    (root / "dataset.yaml").write_text(yaml.safe_dump(ds))
    return root


REPS = CRASH.assign(W1=[1.0, 2.0, 1.5, 0.5], W2=[0.5, 1.0, 2.0, 1.5])


def test_replicate_columns_need_no_record(tmp_path):
    root = with_design(make_data_repo(tmp_path, crash=REPS),
                       {"weights": ["ID"], "replicates": {"prefix": "W", "n": 2, "method": "sdr", "table": "crash"}})
    assert not failures(run(root), "C3"), run(root).failures


def test_without_a_design_they_fail_and_another_table_doesnt_count(tmp_path):
    plain = make_data_repo(tmp_path / "a", crash=REPS)
    assert failures(run(plain), "C3") == ["C3: r1/crash: columns without a record: W1, W2"]
    elsewhere = with_design(make_data_repo(tmp_path / "b", crash=REPS),
                            {"replicates": {"variables": ["W1", "W2"], "method": "fay", "table": "person"}})
    assert failures(run(elsewhere), "C3") == ["C3: r1/crash: columns without a record: W1, W2"]


def test_unset_table_means_any_table_with_the_design(tmp_path):
    root = with_design(make_data_repo(tmp_path, crash=REPS),
                       {"replicates": {"prefix": "W", "n": 2, "method": "brr"}})
    assert not failures(run(root), "C3")

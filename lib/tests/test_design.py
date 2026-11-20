"""pdt.design: the effective design, weight names and replicate columns (STANDARD.md §2.1)."""

from pdt.design import effective_design, replicate_columns, replicate_key, weight_names

ATUS = {"weights": ["TUFNWGTP", {"name": "TU20FWGT", "waves": [2020]}],
        "replicates": {"table": "replicates", "key": ["TUCASEID"], "prefix": "TUFNWGTP", "n": 3,
                       "method": "fay", "fay_factor": 0.5}}


def test_effective_design_most_specific_wins():
    dataset = {"design": {"weights": ["W0"]},
               "releases": [{"id": "r1", "design": {"weights": ["W1"]},
                             "tables": [{"id": "a", "design": {"weights": ["WA"]}}, {"id": "b"}]},
                            {"id": "r2", "tables": [{"id": "a"}]}]}
    assert effective_design(dataset, "r1", "a") == {"weights": ["WA"]}
    assert effective_design(dataset, "r1", "b") == {"weights": ["W1"]}
    assert effective_design(dataset, "r1") == {"weights": ["W1"]}
    assert effective_design(dataset, "r2", "a") == {"weights": ["W0"]}
    assert effective_design({"releases": []}, "r1", "a") is None


def test_weight_names_plain_and_by_wave():
    assert weight_names(ATUS) == ["TUFNWGTP", "TU20FWGT"]
    assert weight_names(ATUS, wave=2020) == ["TUFNWGTP", "TU20FWGT"]
    assert weight_names(ATUS, wave="2019") == ["TUFNWGTP"]
    assert weight_names(None) == []
    assert weight_names({"weights": ["WTSSPS"]}, wave=1972) == ["WTSSPS"]


def test_replicate_columns_padded_and_unpadded():
    cols = ["TUCASEID", "TUFNWGTP", "TUFNWGTP003", "TUFNWGTP001", "TUFNWGTP002", "TUFNWGTP004"]
    assert replicate_columns(ATUS, cols) == ("replicates", ["TUFNWGTP001", "TUFNWGTP002", "TUFNWGTP003"])
    pisa = {"replicates": {"prefix": "W_FSTURWT", "n": 2, "method": "fay", "fay_factor": 0.5}}
    assert replicate_columns(pisa, ["W_FSTURWT1", "W_FSTURWT2", "W_FSTURWT10"]) == (None, ["W_FSTURWT1", "W_FSTURWT2"])
    assert replicate_columns(pisa) == (None, ["W_FSTURWT1", "W_FSTURWT2"])
    listed = {"replicates": {"variables": ["R1", "R2"], "method": "brr"}}
    assert replicate_columns(listed, ["X"]) == (None, ["R1", "R2"])
    assert replicate_columns({"weights": ["W"]}) == (None, [])


def test_replicate_key():
    assert replicate_key(ATUS) == ["TUCASEID"]
    assert replicate_key({"replicates": {"prefix": "R", "n": 2, "method": "brr"}}) == []

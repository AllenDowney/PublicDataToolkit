"""pdt.readers.read_sas_input: fixed-width text laid out by a SAS input program (CDC's YRBSS)."""

import pytest

from pdt import data, readers

PROGRAM = """\
/* a comment with input and label words in it */
data dataout.x;
infile datain lrecl=900;
input
sitecode $ 1-5
year 6-13
weight 14-23
q26 $ 24-24
qn26 25-27
;
format
q26 $H26S.
;
label
sitecode="Site code"
year="4-digit Year of survey"
q26="Sad or hopeless"
;
run;
"""

ROWS = [
    "XX       1991    0.5060" + "1" + "  1",
    "XX       2023   12.0000" + " " + "  .",
    "XX       2023    0.0231" + "2" + "   ",
]


@pytest.fixture
def files(tmp_path):
    sas, dat = tmp_path / "input.sas", tmp_path / "data.dat"
    sas.write_text(PROGRAM)
    dat.write_text("\r\n".join(ROWS) + "\r\n")
    return dat, sas


def test_parse_layout_and_labels(files):
    _, sas = files
    layout = readers.parse_sas_input(sas)
    assert list(layout) == ["sitecode", "year", "weight", "q26", "qn26"]
    assert layout["sitecode"] == (0, 5, True, "Site code")
    assert layout["q26"] == (23, 24, True, "Sad or hopeless")
    assert layout["qn26"] == (24, 27, False, None)


def test_text_kept_numbers_parsed_missing_is_code(files):
    dat, sas = files
    raw = readers.read_sas_input(dat, sas, ["year", "weight", "q26", "qn26", "sitecode"])
    assert list(raw.columns) == ["year", "weight", "q26", "qn26", "sitecode"]
    assert raw["year"].tolist() == [1991, 2023, 2023]
    assert raw["weight"].tolist() == [0.506, 12.0, 0.0231]
    assert raw["q26"].tolist() == ["1", " ", "2"]                     # a blank is text, not a token
    assert not any(isinstance(c, data.Code) for c in raw["q26"])
    cells = raw["qn26"].tolist()
    assert cells[0] == 1 and all(isinstance(c, data.Code) and c == "." for c in cells[1:])  # "." and blank
    assert raw["sitecode"].tolist() == ["XX   "] * 3


def test_round_trip_through_the_common_format(files):
    dat, sas = files
    raw = readers.read_sas_input(dat, sas, ["q26", "qn26"])
    records = {"q26": {"name": "q26", "storage_type": "string",
                       "values": [{"code": " ", "kind": "missing", "missing_types": ["no_answer"]},
                                  {"code": "1", "kind": "valid"}, {"code": "2", "kind": "valid"}]},
               "qn26": {"name": "qn26", "storage_type": "integer",
                        "values": [{"code": 1, "kind": "valid"},
                                   {"code": ".", "kind": "missing", "missing_types": ["no_answer"]}]}}
    table = data.split(raw, records)
    codes = lambda col: [None if data.is_null(c) else c for c in table[col].astype(object)]  # noqa: E731
    assert codes("q26__code") == [None, " ", None]
    assert codes("qn26__code") == [None, ".", "."]
    assert data.same_cells(raw, data.rebuild(table, records))


def test_unknown_column(files):
    dat, sas = files
    with pytest.raises(KeyError, match="nope"):
        readers.read_sas_input(dat, sas, ["year", "nope"])

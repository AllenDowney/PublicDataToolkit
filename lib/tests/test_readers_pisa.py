"""pdt.readers.read_sav and read_sas_input's LENGTH statement (the OECD's PISA files)."""

import pandas as pd
import pytest

from pdt import data, readers

pyreadstat = pytest.importorskip("pyreadstat")


@pytest.fixture
def sav(tmp_path):
    """A tiny .sav like PISA's: a country code, an item with user-missing 95-99, a score."""
    frame = pd.DataFrame({"CNT": ["USA", "JPN", "USA", "FRA"],
                          "ST034Q01TA": [1.0, 99.0, float("nan"), 2.0],
                          "BELONG": [0.25, -1.5, 99.0, 1.0]})
    path = tmp_path / "stu.sav"
    pyreadstat.write_sav(frame, str(path),
                         variable_value_labels={"ST034Q01TA": {1.0: "Strongly agree", 2.0: "Agree", 99.0: "No Response"}},
                         missing_ranges={"ST034Q01TA": [{"lo": 95.0, "hi": 99.0}], "BELONG": [{"lo": 95.0, "hi": 99.0}]})
    return path


def test_read_sav_keeps_user_missing_codes_and_tokens_system_missing(sav):
    raw = readers.read_sav(sav, ["ST034Q01TA", "BELONG", "CNT"])
    assert list(raw.columns) == ["ST034Q01TA", "BELONG", "CNT"]
    cells = raw["ST034Q01TA"].tolist()
    assert cells[0] == 1 and isinstance(cells[0], int) and cells[1] == 99
    assert isinstance(cells[2], data.Code) and cells[2] == "."
    assert raw["BELONG"].tolist() == [0.25, -1.5, 99, 1]
    assert raw["CNT"].tolist() == ["USA", "JPN", "USA", "FRA"]


def test_read_sav_rows_and_round_trip(sav):
    raw = readers.read_sav(sav, ["ST034Q01TA"], rows={"CNT": ["USA", "JPN"]})
    assert len(raw) == 3 and list(raw.columns) == ["ST034Q01TA"]
    rec = {"name": "ST034Q01TA", "storage_type": "integer",
           "values": [{"code": 1, "kind": "valid"}, {"code": 99, "kind": "missing", "missing_types": ["no_answer"]},
                      {"code": ".", "kind": "missing", "missing_types": ["unspecified"]}]}
    table = data.split(raw, {"ST034Q01TA": rec})
    assert data.same_cells(raw, data.rebuild(table, {"ST034Q01TA": rec}))
    with pytest.raises(KeyError, match="nope"):
        readers.read_sav(sav, ["nope"])


PROGRAM_2012 = """\
data STU;
length
CNT $3
StIDStd $5
ST87Q01 3
;
input
CNT 1 - 3
StIDStd 4 - 8
ST87Q01 9 - 9
;
label
CNT         = "Country code 3-character"
STIDSTD     = "Student ID"
ST87Q01     = "Sense of Belonging - Feel Like Outsider "
;
run;
"""


def test_text_types_from_a_length_statement(tmp_path):
    sas, dat = tmp_path / "stu.sas", tmp_path / "stu.txt"
    sas.write_text(PROGRAM_2012.replace("\n", "\r\n"))
    dat.write_text("USA000011\r\nJPN000027\r\nUSA00003 \r\n")
    layout = readers.parse_sas_input(sas)
    assert layout["CNT"] == (0, 3, True, "Country code 3-character")
    assert layout["StIDStd"] == (3, 8, True, "Student ID")                 # label matched ignoring case
    assert layout["ST87Q01"][2] is False
    raw = readers.read_sas_input(dat, sas, ["CNT", "StIDStd", "ST87Q01"])
    assert raw["CNT"].tolist() == ["USA", "JPN", "USA"]
    assert raw["StIDStd"].tolist() == ["00001", "00002", "00003"]          # text keeps its zeros
    assert raw["ST87Q01"].tolist()[:2] == [1, 7] and raw["ST87Q01"].tolist()[2] == "."

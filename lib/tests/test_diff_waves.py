"""pdt diff --waves: changes between waves inside one record (STANDARD.md §4.1)."""

from pdt.diff import main, wave_changes

REC = {"name": "YSAQ-360C",
       "availability": [{"wave": 2010}, {"wave": 2011}, {"wave": 2013}],
       "questions": [{"text": "Have you smoked since the last interview?", "waves": [2010, 2011]},
                     {"text": "Have you smoked within the past twelve months?", "waves": [2013]}],
       "universe": [{"text": "All", "waves": [2010]}, {"text": "R answered smoking questions before", "waves": [2011, 2013]}],
       "values": [{"code": 1, "label": "Yes", "kind": "valid", "n": 3, "counts": [{"wave": 2010, "n": 1}, {"wave": 2011, "n": 1}, {"wave": 2013, "n": 1}]},
                  {"code": 2, "label": "Sometimes", "kind": "valid", "n": 1, "counts": [{"wave": 2010, "n": 1}]}]}


def test_wave_changes_wording_universe_codes():
    out = wave_changes(REC)
    assert [(c["from"], c["to"]) for c in out] == [(2010, 2011), (2011, 2013)]
    first, second = out[0]["changes"], out[1]["changes"]
    assert set(first) == {"universe", "codes"} and first["codes"] == {"added": [], "dropped": [2]}
    assert set(second) == {"question"} and "twelve months" in second["question"]["to"]


def test_no_changes_for_plain_records():
    plain = {"name": "q", "availability": [{"wave": 1}, {"wave": 2}], "questions": [{"text": "Same?"}],
             "universe": "All", "values": [{"code": 1, "label": "yes", "kind": "valid"}]}
    assert wave_changes(plain) == []


def test_cli_waves_needs_one_release(tmp_path, capsys):
    from test_check import make_repo, write_jsonl
    root = make_repo(tmp_path)
    write_jsonl(root / "metadata" / "releases" / "r1" / "variables.jsonl", [dict(REC, dataset="toy", release="r1",
                                                                                 provenance={"record": {"origin": "publisher"}})])
    assert main([str(root), "r1", "--waves"]) == 0
    text = capsys.readouterr().out
    assert "2011 -> 2013: question changed" in text and "dropped [2]" in text

"""Shared code lists (STANDARD.md §4.5): expansion in Repo.load, C1/C2/C7, corrections to a list,
the data identity, pdt diff, and retired codes in the views."""

import copy

import yaml

from pdt import data
from pdt.check import Repo
from pdt.diff import code_list_changes
from pdt.export import code_label
from pdt.search import apply_corrections
from pdt.site import retired_note

from test_check import DATASET, PUBLISHER, make_repo, run, write_jsonl
from test_check_data import CRASH, crash_records, make_data_repo, reports

OCC = {"id": "occ-2010", "label": "Census 2010 occupations", "origin": PUBLISHER,
       "codes": [{"code": 10, "label": "chief executives", "kind": "valid"},
                 {"code": 20, "label": "general managers", "kind": "valid"},
                 {"code": 30, "label": "legislators", "kind": "valid", "retired": True,
                  "waves": {"from": 2010, "to": 2018}}]}


def occ_record(name, missing):
    return {"dataset": "toy", "release": "r1", "name": name, "label": name, "code_list": "occ-2010",
            "values": [{"code": c, "label": c, "kind": "missing", "missing_types": ["inap"], "origin": PUBLISHER}
                       for c in missing],
            "provenance": {"record": PUBLISHER}}


RECORDS = [occ_record("occ10", [".i", ".n"]), occ_record("paocc10", [".d", ".i"])]


def repo_with_lists(root, lists=(OCC,), records=RECORDS, corrections=()):
    make_repo(root, variables=list(records), groups=[], corrections=list(corrections))
    write_jsonl(root / "metadata" / "code_lists.jsonl", list(lists))
    return root


def failures(result, check):
    return [f for f in result.failures if f.startswith(check)]


def test_records_expand_list_first_then_own_codes(tmp_path):
    root = repo_with_lists(tmp_path)
    repo = Repo.load(root)
    occ, pa = repo.tables["r1"][None]
    assert [v["code"] for v in occ["values"]] == [10, 20, 30, ".i", ".n"]
    assert [v["code"] for v in pa["values"]] == [10, 20, 30, ".d", ".i"]
    assert [len(r.get("values", [])) for r in repo.stored["r1"][None]] == [2, 2]   # as on disk
    result = run(root)
    assert result.ok, result.failures


def test_c2_unknown_list_duplicate_code_and_overlap(tmp_path):
    bad = dict(RECORDS[0], code_list="occ-1980")
    assert any("unknown code list occ-1980" in f for f in failures(run(repo_with_lists(tmp_path, records=[bad])), "C2"))

    dupe = dict(OCC, codes=OCC["codes"] + [{"code": 10, "label": "again", "kind": "valid"}])
    sub = tmp_path / "b"
    sub.mkdir()
    assert any("duplicate codes 10" in f for f in failures(run(repo_with_lists(sub, lists=[dupe])), "C2"))

    overlap = copy.deepcopy(RECORDS[0])
    overlap["values"].append({"code": 20, "label": "general managers", "kind": "valid"})
    sub = tmp_path / "c"
    sub.mkdir()
    assert any("both in list occ-2010 and in values: 20" in f
               for f in failures(run(repo_with_lists(sub, records=[overlap])), "C2"))

    twice = tmp_path / "d"
    twice.mkdir()
    assert any("duplicate code list id occ-2010" in f
               for f in failures(run(repo_with_lists(twice, lists=[OCC, OCC])), "C2"))


CORRECTION = {"id": "occ-20-label", "target": {"code_list": "occ-2010", "field": "/codes/1/label"},
              "original": "general managers", "corrected": "general and operations managers",
              "problem": "Truncated.", "evidence": [{"citation": "Census list"}], "confidence": "verified",
              "upstream": {"status": "not_filed"}, "author": "Tester", "date": "2026-11-19"}


def test_correction_to_a_list_applies_to_every_record_that_uses_it(tmp_path):
    root = repo_with_lists(tmp_path, corrections=[CORRECTION])
    result = run(root)
    assert result.ok, result.failures
    repo = Repo.load(root)
    for r in repo.tables["r1"][None]:
        fixed, applied = apply_corrections(r, "r1", None, repo.corrections)
        assert fixed["values"][1]["label"] == "general and operations managers"
        assert applied[0]["field"] == "/values/1/label"
    # Upstream fixed: the original is gone from the list, so C7 fails.
    fixed_list = copy.deepcopy(OCC)
    fixed_list["codes"][1]["label"] = "general and operations managers"
    sub = tmp_path / "b"
    sub.mkdir()
    assert failures(run(repo_with_lists(sub, lists=[fixed_list], corrections=[CORRECTION])), "C7")
    bad = dict(CORRECTION, target={"code_list": "occ-1950", "field": "/codes/1/label"})
    sub = tmp_path / "c"
    sub.mkdir()
    assert any("unknown code list occ-1950" in f
               for f in failures(run(repo_with_lists(sub, corrections=[bad])), "C2"))


def test_data_file_built_from_another_list_is_stale(tmp_path):
    light = {"id": "light", "label": "Light", "origin": PUB_LIST,
             "codes": [{"code": 1, "label": "Day", "kind": "valid"}, {"code": 2, "label": "Dark", "kind": "valid"}]}
    recs = crash_records(LIGHT={"code_list": "light", "values": crash_records()[2]["values"][2:]})
    root = make_data_repo(tmp_path, crash_recs=recs)
    lists = root / "metadata" / "code_lists.jsonl"
    write_jsonl(lists, [light])
    # Rebuild the crash file with the list in its identity, as pdt.release does.
    rec_path = root / "metadata" / "releases" / "r1" / "crash" / "variables.jsonl"
    expanded = Repo.load(root).tables["r1"]["crash"]
    data.write(data.split(CRASH.astype(object), {r["name"]: r for r in expanded}),
               root / "data" / "processed" / "toy-r1-crash.parquet",
               {"dataset": "toy", "release": "r1", "round_trip": "verified", "metadata_sha256": data.metadata_sha256(rec_path),
                "code_lists_sha256": data.metadata_sha256(lists)})
    result = run(root)
    assert result.ok, result.failures
    assert not any("crash" in r for r in reports(result, "C3-C5, C12"))
    write_jsonl(lists, [dict(light, label="Light condition")])
    assert any("toy-r1-crash.parquet" in r and "code lists" in r for r in reports(run(root), "C3-C5, C12"))


PUB_LIST = {"origin": "publisher", "source": "cb"}


def test_diff_compares_lists_once(tmp_path):
    occ2 = copy.deepcopy(OCC)
    occ2["id"] = "occ-2010b"
    occ2["codes"][0]["label"] = "chief executive officers"
    occ2["codes"][1]["retired"] = True
    occ2["codes"].append({"code": 40, "label": "advertising managers", "kind": "valid"})
    dataset = dict(DATASET, releases=DATASET["releases"] + [dict(DATASET["releases"][0], id="r2", label="Release 2")])
    root = repo_with_lists(tmp_path, lists=[OCC, occ2])
    (root / "dataset.yaml").write_text(yaml.safe_dump(dataset))
    write_jsonl(root / "metadata" / "releases" / "r2" / "variables.jsonl",
                [dict(r, release="r2", code_list="occ-2010b") for r in RECORDS])
    [change] = code_list_changes(Repo.load(root), "r1", "r2")
    assert change["from"] == "occ-2010" and change["to"] == "occ-2010b"
    assert change["variables"] == ["occ10", "paocc10"]
    assert (change["added"], change["dropped"], change["relabeled"], change["retired"]) == ([40], [], [10], [20])
    assert not change["same_content"]


def test_retired_codes_in_views():
    assert code_label({"label": "legislators", "retired": True}) == "legislators (retired)"
    assert code_label({"label": "legislators"}) == "legislators"
    assert "retired, in use 2010–2018" in retired_note(OCC["codes"][2])
    assert retired_note(OCC["codes"][0]) == ""

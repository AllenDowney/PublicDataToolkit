"""Tests for `pdt diff`, the release comparison."""

import json

import pytest

from pdt import diff
from pdt.check import Repo
from pdt.cli import main
from test_check import DATASET, VARIABLES, make_repo, write_jsonl

PUB = {"origin": "publisher", "source": "cb"}


def rec(release, name, label, values=(), question=None, universe=None, waves=()):
    r = {"dataset": "toy", "release": release, "name": name, "label": label,
         "values": [dict(v) for v in values], "provenance": {"record": PUB},
         "availability": [{"wave": w} for w in waves]}
    if question:
        r["questions"] = [{"text": question}]
    if universe:
        r["universe"] = universe
    return r


V = lambda code, label, kind="valid", **kw: {"code": code, "label": label, "kind": kind, **kw}
MISSING = {"missing_types": ["dk"], "origin": PUB}


@pytest.fixture
def repo(tmp_path):
    dataset = dict(DATASET, releases=[
        {"id": "r1", "label": "R1", "status": "superseded", "sources": ["cb"]},
        {"id": "r2", "label": "R2", "status": "current", "sources": ["cb"]}])
    a = [rec("r1", "same", "Same", [V(1, "Yes"), V(2, "No")], "Agree?", waves=[2017]),
         rec("r1", "light", "Light", [V(1, "Daylight"), V(9, "Unknown", "missing", **MISSING)], waves=[2017]),
         rec("r1", "weather", "Weather", [V(1, "Clear"), V(9, "Unknown", "missing", **MISSING)], waves=[2017]),
         rec("r1", "dash", "Dash", [V(2, "Dark - Not Lighted")], waves=[2017]),
         rec("r1", "item", "IC-9 Importance", [V(1, "Very")], "IC-9 How important?", waves=[2017]),
         rec("r1", "kind", "Kind", [V(8, "Other"), V(9, "Unknown", "unresolved", origin=PUB)], waves=[2017]),
         rec("r1", "Wgt2017", "Final weight for 2017", [], waves=[2017]),
         rec("r1", "gone", "Dropped", [V(1, "x")], waves=[2017])]
    b = [rec("r2", "same", "Same", [V(1, "Yes"), V(2, "No")], "Agree?", waves=[2024]),
         rec("r2", "light", "Light", [V(1, "Daylight"), V(9, "Reported as Unknown", "missing", **MISSING)],
             waves=[2024]),
         rec("r2", "weather", "Weather", [V(1, "Clear"), V(99, "Unknown", "missing", **MISSING)], waves=[2024]),
         rec("r2", "dash", "Dash", [V(2, "Dark – Not Lighted")], waves=[2024]),
         rec("r2", "item", "IC-7 Importance", [V(1, "Very")], "IC-7 How important?", "All", waves=[2024]),
         rec("r2", "KIND", "Kind", [V(8, "Other"), V(9, "Unknown", "missing", **MISSING)], waves=[2024]),
         rec("r2", "Wgt2024", "Final weight for 2024", [], waves=[2024]),
         rec("r2", "new", "Added", [V(1, "y")], waves=[2024])]
    root = make_repo(tmp_path, dataset=dataset, variables=[], groups=[], corrections=[])
    write_jsonl(root / "metadata" / "releases" / "r1" / "variables.jsonl", a)
    write_jsonl(root / "metadata" / "releases" / "r2" / "variables.jsonl", b)
    return root


def entries(result):
    return {e["from"]: e for e in result["tables"][0]["in_both"]}


def test_compare_text():
    assert diff.compare_text("a", "a") == "same"
    assert diff.compare_text("Dark - Not Lighted", "dark – not lighted") == "text_only"
    assert diff.compare_text("IC-9 How important", "IC-7 How important") == "reference_only"
    assert diff.compare_text("R's age", "R's age (FC A-2b)") == "reference_only"
    assert diff.compare_text("Ever married", "Ever married to an opposite-sex spouse") == "changed"


def test_diff_categories(repo):
    result = diff.diff(Repo.load(repo), "r1", "r2")
    t = result["tables"][0]
    e = entries(result)
    assert e["same"]["relations"] == ["same_item"] and e["same"]["changes"] == {}
    assert e["light"]["relations"] == ["labels_changed"]
    assert e["light"]["changes"]["codes"]["relabeled"] == [{"code": 9, "from": "Unknown", "to": "Reported as Unknown"}]
    assert e["weather"]["relations"] == ["codes_changed"]
    assert [c["code"] for c in e["weather"]["changes"]["codes"]["added"]] == [99]
    assert e["dash"]["relations"] == ["same_item"]
    assert e["dash"]["changes"]["codes"]["relabeled_text_only"][0]["code"] == 2
    assert e["item"]["relations"] == ["universe_changed"]           # label and question: reference only
    assert e["item"]["changes"]["label"]["how"] == "reference_only"
    assert e["kind"]["name_case_changed"] and e["kind"]["relations"] == ["codes_changed"]
    assert e["kind"]["changes"]["codes"]["kind_changed"][0]["from"][0] == "unresolved"
    assert t["only_in_from"] == ["Wgt2017", "gone"] and t["only_in_to"] == ["Wgt2024", "new"]
    assert [(c["from"], c["to"]) for c in t["rename_candidates"]] == [("Wgt2017", "Wgt2024")]   # not gone -> new


def test_proposals(repo, tmp_path):
    r = Repo.load(repo)
    result = diff.diff(r, "r1", "r2")
    n_links, n_hist = diff.write_proposals(r, result, tmp_path / "out")
    links = [json.loads(l) for l in (tmp_path / "out" / "links.jsonl").read_text().splitlines()]
    assert n_links == len(links) == 6
    assert all(l["origin"]["rule"] == "release_diff" for l in links)
    hists = {h["name"]: h for h in map(json.loads, (tmp_path / "out" / "histories.jsonl").read_text().splitlines())}
    assert sorted(hists) == ["light", "weather"]
    assert hists["weather"]["attributes"] == [{"label": "Clear", "codes": [1, 1]},
                                              {"label": "Unknown", "codes": [9, 99]}]      # same answer, new code
    assert hists["light"]["attributes"][1:] == [{"label": "Unknown", "codes": [9, None]},
                                                {"label": "Reported as Unknown", "codes": [None, 9]}]
    assert hists["light"]["periods"] == [{"from": 2017, "to": 2017}, {"from": 2024, "to": 2024}]


def test_never_writes_metadata(repo):
    r = Repo.load(repo)
    with pytest.raises(SystemExit):
        diff.write_proposals(r, diff.diff(r, "r1", "r2"), repo / "metadata" / "proposals")


def test_cli(repo, capsys):
    assert main(["diff", str(repo), "r1", "r2"]) == 0
    out = capsys.readouterr().out
    assert "toy: r1 -> r2" in out and "rename candidate: Wgt2017 -> Wgt2024" in out
    assert "codes relabeled: 9 'Unknown' -> 'Reported as Unknown'" in out
    with pytest.raises(SystemExit):
        main(["diff", str(repo), "r1", "nope"])


def test_merge_candidate(tmp_path):
    dataset = dict(DATASET, releases=[
        {"id": "r1", "label": "R1", "status": "superseded", "sources": ["cb"]},
        {"id": "r2", "label": "R2", "status": "current", "sources": ["cb"]}])
    codes = [V(1, "Very biased"), V(2, "Somewhat"), V(3, "Not biased")]
    root = make_repo(tmp_path, dataset=dataset, variables=[], groups=[], corrections=[])
    write_jsonl(root / "metadata" / "releases" / "r1" / "variables.jsonl",
                [rec("r1", "strvbias", "Bias", codes), rec("r1", "strvbiasy", "Bias (year)", codes)])
    write_jsonl(root / "metadata" / "releases" / "r2" / "variables.jsonl", [rec("r2", "strvbias", "Bias", codes)])
    t = diff.diff(Repo.load(root), "r1", "r2")["tables"][0]
    assert t["merge_split_candidates"] == [{"kind": "merge", "from": "strvbiasy", "to": "strvbias",
                                            "score": t["merge_split_candidates"][0]["score"]}]


def test_codes_in_range_and_without_cases(tmp_path):
    dataset = dict(DATASET, releases=[
        {"id": "r1", "label": "R1", "status": "superseded", "sources": ["cb"]},
        {"id": "r2", "label": "R2", "status": "current", "sources": ["cb"]}])
    age_a = rec("r1", "age", "Age", [V(15, "15", n=100)])
    age_a["valid_range"] = {"min": 15, "max": 50}
    age_b = rec("r2", "age", "Age", [V(15, "15", n=90), V(49, "49", n=80)])
    order_a = rec("r1", "order", "Order", [V(1, "1", n=3000), V(2, "2", n=2000)])
    order_b = rec("r2", "order", "Order", [V(1, "1", n=2500), V(2, "2", n=1500), V(3, "3", n=1)])
    stat_a = rec("r1", "stat", "Status", [V(1, "Married", n=1000), V(6, "Never married", n=2800)])
    stat_b = rec("r2", "stat", "Status", [V(1, "Married", n=1100)])
    root = make_repo(tmp_path, dataset=dataset, variables=[], groups=[], corrections=[])
    write_jsonl(root / "metadata" / "releases" / "r1" / "variables.jsonl", [age_a, order_a, stat_a])
    write_jsonl(root / "metadata" / "releases" / "r2" / "variables.jsonl", [age_b, order_b, stat_b])
    plain = entries(diff.diff(Repo.load(root), "r1", "r2"))
    assert plain["age"]["relations"] == ["same_item"]                          # 49 is in r1's valid range
    assert plain["age"]["changes"]["codes"]["in_other_range"][0]["code"] == 49
    assert plain["order"]["relations"] == ["codes_changed"]
    assert plain["order"]["changes"]["codes"]["added"] == [{"code": 3, "label": "3", "kind": "valid", "n": 1}]
    omitted = entries(diff.diff(Repo.load(root), "r1", "r2", omitted_codes_have_no_cases=True))
    assert omitted["order"]["relations"] == ["same_item"]                      # 1 case: zero in r1 is chance
    assert omitted["stat"]["relations"] == ["codes_changed"]                   # 2,800 cases can't vanish by chance


def test_sources_list_only_occurring_codes(tmp_path):
    import yaml
    dataset = dict(DATASET, releases=[
        {"id": "r1", "label": "R1", "status": "superseded", "sources": ["cb"]},
        {"id": "r2", "label": "R2", "status": "current", "sources": ["cb"]}])
    a = rec("r1", "order", "Order", [V(1, "1", n=3000)])
    b = rec("r2", "order", "Order", [V(1, "1", n=2500), V(2, "2", n=1)])
    for r in (a, b):
        r["source_location"] = {"source": "cb"}
    root = make_repo(tmp_path, dataset=dataset, variables=[], groups=[], corrections=[])
    write_jsonl(root / "metadata" / "releases" / "r1" / "variables.jsonl", [a])
    write_jsonl(root / "metadata" / "releases" / "r2" / "variables.jsonl", [b])
    assert entries(diff.diff(Repo.load(root), "r1", "r2"))["order"]["relations"] == ["codes_changed"]
    sources = yaml.safe_load((root / "sources.yaml").read_text())
    sources["sources"][0]["lists_only_occurring_codes"] = True
    (root / "sources.yaml").write_text(yaml.safe_dump(sources))
    e = entries(diff.diff(Repo.load(root), "r1", "r2"))["order"]
    assert e["relations"] == ["same_item"] and e["changes"]["codes"]["no_cases_in_other"][0]["code"] == 2


def test_valid_range_question_number_and_links(tmp_path):
    dataset = dict(DATASET, releases=[
        {"id": "r1", "label": "R1", "status": "superseded", "sources": ["cb"]},
        {"id": "r2", "label": "R2", "status": "current", "sources": ["cb"], "reference_period": "2021"}])
    cut_a = rec("r1", "cut", "Poverty cutoff", [V(-1, "NIU")])
    cut_a["valid_range"] = {"min": 1, "max": 60000}
    cut_b = rec("r2", "cut", "Poverty cutoff", [V(-1, "NIU")])
    cut_b["valid_range"] = {"min": 1, "max": 99999}
    age_a = rec("r1", "age", "Age", [V(-1, "NIU")])
    age_a["valid_range"] = {"min": 15, "max": 17}
    age_b = rec("r2", "age", "Age", [V(15, "15"), V(16, "16"), V(17, "17")])    # the same span, listed
    num_a = rec("r1", "num", "Num", [V(1, "Yes")], "Agree?")
    num_a["questions"][0]["number"] = "Q26"
    num_b = rec("r2", "num", "Num", [V(1, "Yes")], "Agree?")
    num_b["questions"][0]["number"] = "Q27"
    # renumbered: r1 q26 is r2 q27; r2 q26 is new
    q26_a = rec("r1", "q26", "Considered suicide", [V(1, "Yes")])
    q27_b = rec("r2", "q27", "Considered suicide", [V(1, "Yes")])
    q26_b = rec("r2", "q26", "Sad or hopeless", [V(1, "Yes")])
    root = make_repo(tmp_path, dataset=dataset, variables=[], groups=[], corrections=[])
    write_jsonl(root / "metadata" / "releases" / "r1" / "variables.jsonl", [cut_a, age_a, num_a, q26_a])
    write_jsonl(root / "metadata" / "releases" / "r2" / "variables.jsonl", [cut_b, age_b, num_b, q27_b, q26_b])
    write_jsonl(root / "metadata" / "links.jsonl", [
        {"from": {"release": "r1", "name": "q26"}, "to": {"release": "r2", "name": "q27"},
         "relations": ["same_item", "renamed"], "origin": {"origin": "publisher", "source": "cb"}}])
    result = diff.diff(Repo.load(root), "r1", "r2")
    t = result["tables"][0]
    e = entries(result)
    assert e["cut"]["relations"] == ["range_changed"] and e["cut"]["changes"]["valid_range"]["to"]["max"] == 99999
    assert e["cut"]["changes"]["valid_range"]["how"] == "documented"
    assert "valid_range" not in e["age"]["changes"]
    assert e["num"]["relations"] == ["same_item"]
    assert e["num"]["changes"]["question_number"] == {"how": "reference_only", "from": ["Q26"], "to": ["Q27"]}
    assert e["q26"]["to"] == "q27" and e["q26"]["paired_by"] == "link" and e["q26"]["link_agrees"]
    assert e["q26"]["relations"] == ["same_item"]
    assert t["only_in_to"] == ["q26"]
    assert t["name_conflicts"] == [{"name": "q26", "from_linked_to": "q27", "to_linked_from": None}]
    assert result["reference_periods"] == {"r1": None, "r2": "2021"}
    assert "name conflict: q26" in diff.summary(result)


def test_observed_and_identifier_ranges(tmp_path):
    dataset = dict(DATASET, releases=[
        {"id": "r1", "label": "R1", "status": "superseded", "sources": ["cb"]},
        {"id": "r2", "label": "R2", "status": "current", "sources": ["cb"]}])
    data_prov = {"record": PUB, "fields": {"valid_range": {"origin": "data_file", "source": "cb"}}}
    def ranged(rel, name, lo, hi, measure="continuous", prov=None, top=None):
        r = rec(rel, name, name, [V(-1, "NIU")])
        r["measure"] = measure
        r["valid_range"] = {"min": lo, "max": hi, **({"top_coded": top} if top is not None else {})}
        if prov:
            r["provenance"] = prov
        return r
    root = make_repo(tmp_path, dataset=dataset, variables=[], groups=[], corrections=[])
    write_jsonl(root / "metadata" / "releases" / "r1" / "variables.jsonl", [
        ranged("r1", "modyear", 1927, 2018, prov=data_prov), ranged("r1", "case", 10001, 560105, "identifier"),
        ranged("r1", "age", 18, 89, prov=data_prov, top=False)])
    write_jsonl(root / "metadata" / "releases" / "r2" / "variables.jsonl", [
        ranged("r2", "modyear", 1929, 2025, prov=data_prov), ranged("r2", "case", 10001, 560102, "identifier"),
        ranged("r2", "age", 18, 89, prov=data_prov, top=True)])
    e = entries(diff.diff(Repo.load(root), "r1", "r2"))
    assert e["modyear"]["relations"] == ["same_item"] and e["modyear"]["changes"]["valid_range"]["how"] == "observed"
    assert e["case"]["changes"] == {}
    assert e["age"]["relations"] == ["range_changed"]                      # top coding changed


def tabled_repo(tmp_path, releases, tables_by_release, records, links=()):
    """A repo whose releases have tables: tables_by_release {release: [table ids]}."""
    dataset = dict(DATASET, releases=[
        {"id": r, "label": r, "status": "current", "sources": ["cb"],
         "tables": [{"id": t, "label": t, "sources": ["cb"]} for t in tables_by_release[r]]} for r in releases])
    root = make_repo(tmp_path, dataset=dataset, variables=[], groups=[], corrections=[])
    for (rel, tab), recs in records.items():
        write_jsonl(root / "metadata" / "releases" / rel / tab / "variables.jsonl",
                    [dict(r, release=rel) for r in recs])
    write_jsonl(root / "metadata" / "links.jsonl", list(links))
    return root


def link(ra, ta, na, rb, tb, nb, rels):
    return {"from": {"release": ra, "table": ta, "name": na}, "to": {"release": rb, "table": tb, "name": nb},
            "relations": rels, "origin": PUB}


def test_across_tables_by_links_and_by_map(tmp_path):
    root = tabled_repo(tmp_path, ["2018", "2019"], {"2018": ["samadult", "person"], "2019": ["adult"]}, {
        ("2018", "samadult"): [rec("2018", "DEP_1", "Depressed"), rec("2018", "WT", "Weight")],
        ("2018", "person"): [rec("2018", "PHSTAT", "Health status", [V(1, "Excellent")])],
        ("2019", "adult"): [rec("2019", "DEPFREQ_A", "Depressed"), rec("2019", "WT", "Weight"),
                            rec("2019", "PHSTAT_A", "Health status", [V(1, "Excellent")])]},
        [link("2018", "samadult", "DEP_1", "2019", "adult", "DEPFREQ_A", ["same_item", "renamed"])])
    r = Repo.load(root)
    assert diff.table_pairs(r, "2018", "2019")[0] == ("samadult", "adult")                    # by links
    result = diff.diff(r, "2018", "2019")
    sam = next(t for t in result["tables"] if t["from_table"] == "samadult")
    assert sam["table"] == "adult" and {(e["from"], e["to"]) for e in sam["in_both"]} == {
        ("DEP_1", "DEPFREQ_A"), ("WT", "WT")}
    assert "[samadult → adult]" in diff.summary(result)
    person = next(t for t in result["tables"] if t["from_table"] == "person")
    assert person["only_table"] == "from"                                           # no links, no map
    merged = diff.diff(r, "2018", "2019", table_map={"person": "adult"})
    tabs = {t["from_table"]: t for t in merged["tables"]}
    assert tabs["person"]["table"] == "adult"
    assert [(c["from"], c["to"]) for c in tabs["person"]["rename_candidates"]] == [("PHSTAT", "PHSTAT_A")]
    assert tabs["samadult"]["only_in_to"] == ["PHSTAT_A"] and tabs["person"]["only_in_to"] == []   # listed once
    links = diff.proposed_links(merged)
    assert {"release": "2018", "table": "samadult", "name": "DEP_1"} in [l["from"] for l in links]


def test_gaps_follow_links_and_names(tmp_path):
    years = ["2019", "2020", "2021", "2022"]
    root = tabled_repo(tmp_path, years, {y: ["adult"] for y in years}, {
        ("2019", "adult"): [rec("2019", "PHQ", "Depression", [V(1, "None")]), rec("2019", "SEX", "Sex")],
        ("2020", "adult"): [rec("2020", "SEX", "Sex")],
        ("2021", "adult"): [rec("2021", "SEX", "Sex"), rec("2021", "K6", "Distress")],
        ("2022", "adult"): [rec("2022", "PHQ", "Depression", [V(1, "None"), V(2, "Mild")]),
                            rec("2022", "SEX", "Sex"), rec("2022", "K6NEW", "* Distress")]},
        [link("2021", "adult", "K6", "2022", "adult", "K6NEW", ["same_item", "renamed"])])
    entries = diff.gaps(Repo.load(root))
    assert [(e["from"], e["from_release"], e["to_release"], e["paired_by"]) for e in entries] == [
        ("PHQ", "2019", "2022", "name")]                    # SEX is consecutive; K6 -> K6NEW skips nothing
    assert entries[0]["skipped"] == ["2020", "2021"] and entries[0]["relations"] == ["codes_changed"]
    assert "PHQ 2019 → adult.PHQ 2022 (skips 2020, 2021)" in diff.gaps_summary("x", entries)


def test_cli_gaps_and_ignore(repo, capsys):
    from pdt.cli import main
    assert main(["diff", str(repo), "--gaps"]) == 0
    assert "variables whose next appearance skips releases (0)" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        main(["diff", str(repo), "r1"])
    assert main(["diff", str(repo), "r1", "r2", "--ignore", r"Reported as\s*", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    light = next(e for e in result["tables"][0]["in_both"] if e["from"] == "light")
    assert light["relations"] == ["same_item"] and result["ignore"] == [r"Reported as\s*"]

"""Tests for C5's count comparison (Task 71): the publisher's counts in a record (values[].n,
availability[].n) against the common-format file, at warn level."""

from test_check_data import CRASH, TABLES, crash_records, make_data_repo, reports, run

# CRASH: LIGHT is 1, 2, 9, 1 (9 missing); YEAR 2020, 2020, 2021, 2021.
LIGHT_N = {1: 2, 2: 1, 9: 1}
AVAIL_N = [{"wave": 2020, "n": 2}, {"wave": 2021, "n": 1}]


def counted(light_n=LIGHT_N, avail=AVAIL_N):
    recs = crash_records()
    for r in recs:
        if r["name"] == "LIGHT":
            r["values"] = [dict(v, n=light_n[v["code"]]) for v in r["values"] if v["code"] in light_n]
            r["availability"] = avail
    return recs


def counts_warnings(result):
    return [m for m in reports(result, "C5: warning") if "counts differ" in m]


def test_matching_counts_pass_quietly(tmp_path):
    result = run(make_data_repo(tmp_path, crash_recs=counted()))
    assert result.ok, result.failures
    assert not counts_warnings(result)
    assert not [m for m in result.not_run if "counts" in m]


def test_code_count_mismatch_warns_with_code_and_counts(tmp_path):
    result = run(make_data_repo(tmp_path, crash_recs=counted(light_n={1: 3, 2: 1, 9: 0})))
    assert result.ok                                    # a warning, not a failure
    assert counts_warnings(result) == [
        "C5: warning: r1/crash/LIGHT: code counts differ from the data: "
        "1 (Day): codebook 3, data 2, 9 (Unknown): codebook 0, data 1"]


def test_availability_count_mismatch_warns_per_wave(tmp_path):
    avail = [{"wave": 2020, "n": 2}, {"wave": 2021, "n": 2}]
    msgs = counts_warnings(run(make_data_repo(tmp_path, crash_recs=counted(avail=avail))))
    assert msgs == ["C5: warning: r1/crash/LIGHT: non-missing counts differ from the data: "
                    "2021: availability 2, data 1"]


def test_no_counts_is_recorded_as_not_run(tmp_path):
    result = run(make_data_repo(tmp_path))
    assert any("counts not run, because there are no codebook counts" in m for m in result.not_run)
    assert not counts_warnings(result)


def test_data_waves_skips_code_counts_and_checks_kept_waves(tmp_path):
    # The file holds 2020 only; the records count both years.
    tables = [dict(TABLES[0], data_waves=["2020"]), TABLES[1]]
    kept = CRASH[CRASH["YEAR"] == 2020]
    avail = [{"wave": 2020, "n": 2}, {"wave": 2021, "n": 5}]
    result = run(make_data_repo(tmp_path, crash=kept, tables=tables, crash_recs=counted(avail=avail)))
    assert not counts_warnings(result)                  # 2021 isn't in the file; 2020 matches
    assert any("code counts (values[].n) not run, because the file holds only some waves" in m
               for m in result.not_run)
    avail = [{"wave": 2020, "n": 3}, {"wave": 2021, "n": 5}]
    result = run(make_data_repo(tmp_path / "b", crash=kept, tables=tables, crash_recs=counted(avail=avail)))
    assert counts_warnings(result) == ["C5: warning: r1/crash/LIGHT: non-missing counts differ from the data: "
                                       "2020: availability 3, data 2"]


def test_data_rows_skips_counts(tmp_path):
    tables = [dict(TABLES[0], data_rows={"column": "ID", "in": [1, 2]}), TABLES[1]]
    kept = CRASH[CRASH["ID"].isin([1, 2])]
    result = run(make_data_repo(tmp_path, crash=kept, tables=tables, crash_recs=counted()))
    assert not counts_warnings(result)
    assert any("r1/crash: counts not run, because the file holds only some rows" in m for m in result.not_run)


def test_qualified_availability_counts_are_not_run(tmp_path):
    # Counts by form (or geography, as BRFSS's state modules) can't be matched to rows.
    avail = [{"wave": 2020, "form": "A", "n": 7}, {"wave": 2021, "n": 1}]
    result = run(make_data_repo(tmp_path, crash_recs=counted(avail=avail)))
    assert not counts_warnings(result)
    assert any("r1/crash: 1 availability counts by form/geography/mode/phase/sample not run" in m
               for m in result.not_run)

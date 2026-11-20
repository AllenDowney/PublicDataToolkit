"""`pdt check` says which checks, or parts of checks, didn't run, and why (planning/daaf.md, step 3)."""

from pdt.check import Result, run
from pdt.cli import main
from test_check import VARIABLES, make_repo


def not_run(result, check):
    return [r for r in result.not_run if r.startswith(check + ":")]


def test_skipped_reports_are_not_run():
    r = Result()
    r.report("C5", "r1/person: skipped, no wave column (YEAR) and several waves declared")
    r.report("C6", "3 unresolved codes")
    r.skip("C7", "not run, because there are no corrections")
    assert r.not_run == ["C5: r1/person: skipped, no wave column (YEAR) and several waves declared",
                         "C7: not run, because there are no corrections"]
    assert len(r.reports) == 3 and r.ok


def test_checks_that_dont_apply_say_why(tmp_path):
    result = run(make_repo(tmp_path, corrections=[]))
    assert not_run(result, "C7") == ["C7: not run, because there are no corrections"]
    assert not_run(result, "C10") == ["C10: not run, because no record has extensions"]
    assert not_run(result, "C5") == ["C5: not run, because no record has availability"]
    assert not_run(result, "C12") == ["C12: not run, because no table declares a key or references"]
    assert any("no data file" in r for r in not_run(result, "C3-C5, C12"))
    assert any("docs/ doesn't exist here" in r for r in not_run(result, "C8"))
    assert any("export/daaf/: not run, because it isn't exported here" in r for r in not_run(result, "C8"))
    assert not_run(run(tmp_path, views=False), "C8") == [
        "C8: not run, because the caller asked for no view checks (views=False)"]


def test_checks_that_run_arent_listed(tmp_path):
    records = [dict(VARIABLES[0], availability=[{"wave": 1990}], extensions={"toy": {"x": 1}}), VARIABLES[1]]
    root = make_repo(tmp_path, variables=records, extensions="# Extensions\n\n- `toy.x`: a test.\n")
    result = run(root)
    assert not not_run(result, "C7") and not not_run(result, "C10") and not not_run(result, "C5")


def test_reference_to_another_dataset_is_not_run():
    import pandas as pd
    from pdt.check import check_keys_in_data
    tables = [{"id": "t", "key": ["q1"], "references": [{"dataset": "other", "table": "codes", "columns": ["q1"]}]}]
    result = Result()
    check_keys_in_data("r1", tables, {("r1", "t"): (pd.DataFrame({"q1": [1]}), [])}, result)
    assert result.not_run == ["C12: r1/t -> codes: not run, because the target is in another dataset"]


def test_cli_prints_not_run_once(tmp_path, capsys):
    root = make_repo(tmp_path, corrections=[])
    main(["check", str(root)])
    out = capsys.readouterr().out
    assert "not run C7: because there are no corrections" in out
    assert "report C7:" not in out

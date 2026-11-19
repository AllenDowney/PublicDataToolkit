"""Tests for pdt.compare, the shared text comparison."""

import pytest

from pdt.compare import compare_text, is_change, norm, strip_refs


@pytest.mark.parametrize("a, b, how", [
    ("Never married", "Never married", "same"),
    ("NEVER MARRIED", "Never married", "text_only"),
    ("Dark - Not Lighted", "Dark – Not Lighted", "text_only"),
    ("Child Restraint System  - Rear Facing", "Child Restraint System - Rear Facing", "text_only"),
    ("IC-9 How important is religion", "IC-7 How important is religion", "reference_only"),
    ("R's age at interview", "R's age at interview (FC A-2b)", "reference_only"),
    ("JB-4 Attendance", "JB-3 attendance", "reference_only"),
    ("R's age at interview", "R's age at interview (Computed in FC A-2b)", "reference_only"),
    ("Current religious affiliation (RECODE)", "Current religious affiliation", "reference_only"),
    ("Formal (legal) marital status  (RECODE)", "Formal (legal) marital status relative to opposite-sex spouses",
     "changed"),
    ("Whether R was ever married", "Ever married to an opposite-sex spouse (computed in FC A-17)", "changed"),
    ("15 years", "15", "changed"),
    ("since covid-19", "since covid-20", "changed"),
    (None, "", "same"),
])
def test_compare_text(a, b, how):
    assert compare_text(a, b) == how
    assert is_change(how) == (how == "changed")


def test_helpers():
    assert norm("  A — b ") == "a-b"
    assert strip_refs("IC-9 How (FC A-2b) important") == "how important"


def test_absent_by_chance():
    from pdt.compare import absent_by_chance, total_cases
    assert absent_by_chance(1, 8000, 10000)                 # PREGORDR 15: 1 case
    assert not absent_by_chance(2820, 6000, 5500)            # MARSTAT 6: a recoding
    assert not absent_by_chance(None, 10, 10) and not absent_by_chance(3, 0, 10)
    assert total_cases({"values": [{"n": 2}, {"n": 3}, {}]}) == 5

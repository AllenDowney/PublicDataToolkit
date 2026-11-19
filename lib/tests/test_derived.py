from pdt.derived import SCALE_SIGNATURE_RULE, SCALE_SIGNATURE_VERSION, scale_signature, scale_signatures, valid_labels


def record(labels, name="v", release="r1", table=None, **extra):
    r = {"dataset": "d", "release": release, "name": name,
         "values": [{"code": i, "label": lab, "kind": "valid"} for i, lab in enumerate(labels, 1)]
         + [{"code": 9, "label": "Unknown", "kind": "missing", "missing_types": ["unknown"]}], **extra}
    if table:
        r["table"] = table
    return r


def test_each_dataset_table_entry():
    assert scale_signature(record(["No", "Yes"])) == "yes_no"            # FARS order
    assert scale_signature(record(["Yes", "No"])) == "yes_no"            # NSFG
    assert scale_signature(record(["yes", "no"])) == "yes_no"            # GSS
    assert scale_signature(record(["Favor", "Oppose"])) == "favor_oppose"  # ANES
    assert scale_signature(record(["too little", "about right", "too much"])) == "spending_3"


def test_case_and_whitespace_ignored_order_and_missing_codes_not():
    assert scale_signature(record(["YES", " No "])) == "yes_no"          # NSFG 2017-2019 PMARPREG
    assert scale_signature(record(["too much", "about right", "too little"])) is None
    assert scale_signature(record(["Yes", "No", "Maybe"])) is None
    assert scale_signature(record([])) is None


def test_thermometer_from_valid_range():
    r = record([], valid_range={"min": 0, "max": 100, "note": "0-100 Degrees"})
    assert scale_signature(r) == "thermometer"
    assert scale_signature(record([], valid_range={"min": 0, "max": 100})) is None


def test_lines_per_release_name_table_and_release():
    recs = [record(["Yes", "No"], name="a", release="r1", table="t"),
            record(["Yes", "No"], name="a", release="r2", table="t"),
            record(["x"], name="b", release="r1", table="t")]
    lines = scale_signatures(recs)
    assert [line["target"] for line in lines] == [{"release": "r1", "table": "t", "variable": "a"},
                                                   {"release": "r2", "table": "t", "variable": "a"}]
    assert lines[0]["rule"] == SCALE_SIGNATURE_RULE and lines[0]["rule_version"] == SCALE_SIGNATURE_VERSION
    assert lines[0]["property"] == "scale_signature" and lines[0]["value"] == "yes_no"


def test_lines_once_per_variable():
    recs = [record(["x"], name="a", release="r1"),           # no signature in r1
            record(["Yes", "No"], name="a", release="r2"),
            record(["Yes", "No"], name="a", release="r3")]
    assert [line["target"] for line in scale_signatures(recs, per_release=False)] == [{"variable": "a"}]


def test_valid_codes_without_labels():
    """YRBSS qn variables: codes 1 and 2 are valid and unlabeled (label is optional in the schema)."""
    qn = {"dataset": "d", "release": "r1", "name": "qn26",
          "values": [{"code": 1, "kind": "valid"}, {"code": 2, "kind": "valid"},
                     {"code": ".", "kind": "missing", "missing_types": ["no_answer"]}]}
    assert valid_labels(qn) == (None, None)
    assert scale_signature(qn) is None
    half = record(["Yes"])
    half["values"].insert(1, {"code": 2, "kind": "valid"})
    assert valid_labels(half) == ("yes", None)
    assert scale_signature(half) is None
    assert scale_signatures([qn, half, record(["Yes", "No"], name="a")])[0]["target"]["variable"] == "a"

"""Derived properties computed by named, versioned rules (STANDARD.md §6).

Every dataset build calls these instead of keeping its own copy, so a rule
means the same thing in every repo.

Rule `scale_signature_from_valid_labels`: a name for a common response format,
from a variable's valid labels, in order. Labels match ignoring case and
surrounding whitespace. A variable whose valid range is in degrees (an ANES
feeling thermometer, "0-100 degrees") is a `thermometer`.

Version history:
- 0.1: four copies, one per dataset build, each with its own table and exact,
  case-sensitive matching.
- 0.2: one shared table (the union of the four), matched ignoring case; the
  thermometer test from the ANES build.
"""

SCALE_SIGNATURE_RULE = "scale_signature_from_valid_labels"
SCALE_SIGNATURE_VERSION = "0.2"

# Valid labels, lowercased, in the publisher's order -> signature. Both orders of
# yes/no occur (GSS and NSFG list yes first, FARS lists no first).
SCALE_SIGNATURES = {
    ("yes", "no"): "yes_no",                                   # GSS, NSFG
    ("no", "yes"): "yes_no",                                   # FARS
    ("favor", "oppose"): "favor_oppose",                       # ANES
    ("too little", "about right", "too much"): "spending_3",   # GSS
}


def valid_labels(record):
    """The record's valid labels, lowercased and stripped, in order."""
    return tuple(v["label"].strip().lower() for v in record.get("values", []) if v.get("kind") == "valid")


def scale_signature(record):
    """The record's scale signature, or None."""
    if "degree" in (record.get("valid_range") or {}).get("note", "").lower():
        return "thermometer"
    return SCALE_SIGNATURES.get(valid_labels(record))


def scale_signatures(records, per_release=True):
    """Derived-property lines (schema/derived.schema.json) for every record that has a signature.

    With per_release, each release's record gets its own line, and the target
    names the release. Without it, there's one line per (table, name), from the
    first record that has a signature; use that when a variable's valid labels
    are the same in every release.
    """
    out, seen = [], set()
    for r in records:
        value = scale_signature(r)
        if value is None:
            continue
        key = (r.get("table"), r["name"])
        if not per_release:
            if key in seen:
                continue
            seen.add(key)
        target = {**({"release": r["release"]} if per_release else {}),
                  **({"table": r["table"]} if "table" in r else {}),
                  "variable": r["name"]}
        out.append({"target": target, "property": "scale_signature", "value": value,
                    "rule": SCALE_SIGNATURE_RULE, "rule_version": SCALE_SIGNATURE_VERSION})
    return out

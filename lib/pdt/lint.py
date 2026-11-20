"""A lint for labels that look like a parser's leftovers (pdt check C6, report only).

Parsing a PDF or HTML codebook goes wrong in ways that leave the label looking like part of
the page instead of a label: a table row's counts, a column gap, a soft hyphen, a count where
the label should be. Building BRFSS (Task 30), checks like these found five parser bugs.
They are heuristics: each hit is worth a look, not an error, so the check only reports.
Running headers are particular to each publisher, so a build checks for its own.
"""

import re

PATTERNS = [
    ("a frequency and percentages", re.compile(r"\d{1,3}(?:,\d{3})+\s+\d+\.\d+\b")),
    ("a column gap", re.compile(r"\S {4,}\S")),
    ("a code and a column gap at the start", re.compile(r"^-?\d[\d.,]*\s{2,}\S")),
    ("a soft hyphen", re.compile("\xad")),
    ("a replacement or control character", re.compile("[�\x00-\x08\x0b\x0c\x0e-\x1f]")),
    ("a codebook keyword", re.compile(r"(?:^|\s)(?:Notes|SAS Variable Name|Value Label|Frequency)\s*:")),
]
COUNT = re.compile(r"^\d{1,3}(?:,\d{3})+$|^\d{2,}$")   # one digit is often real (GSS "0" for code 1)


def label_problem(label, code=None):
    """Why a label looks like a parser's leftover, or None."""
    if not isinstance(label, str) or not label.strip():
        return None
    text = label.strip()
    if COUNT.match(text) and (code is None or str(code) != text.replace(",", "")):
        return "a number other than its code"
    for why, pattern in PATTERNS:
        if pattern.search(label):
            return why
    return None


def label_problems(records):
    """(where, label, why) for each suspicious label in the records."""
    out = []
    for r in records:
        where = "/".join(str(x) for x in (r.get("release"), r.get("table"), r.get("name")) if x)
        why = label_problem(r.get("label"))
        if why:
            out.append((where, r["label"], why))
        for v in r.get("values") or []:
            why = label_problem(v.get("label"), v.get("code"))
            if why:
                out.append((f"{where} code {v.get('code')}", v["label"], why))
    return out

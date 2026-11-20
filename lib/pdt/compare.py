r"""Compare two texts from documentation: is a difference a change, or only how it's written?

    compare_text(a, b) -> "same" | "text_only" | "reference_only" | "changed"

- `text_only`: equal once case, whitespace and dash variants are folded. The FARS records
  write "Dark - Not Lighted" where the manual has "Dark – Not Lighted"; the NSFG's
  2017-2019 codebook writes "NEVER MARRIED" where 2022-2023 writes "Never married".
- `reference_only`: equal once questionnaire item references are removed as well:
  "IC-9 How important..." vs "IC-7 How important...", "R's age at interview" vs
  "R's age at interview (FC A-2b)" or "(Computed in FC A-2b)". Item numbers move with
  the questionnaire's layout. A parenthesized variable-type marker, "(RECODE)" as the
  NSFG's 2017-2019 labels have it, is removed too: the record's variable_type holds it.

A dataset can also name formatting markers to ignore, as regular expressions: NHIS's
codebook prints "* " before interviewer instructions from 2022, unevenly
("* Read if necessary: ..."). compare_text(a, b, ignore=[r"(?:^|(?<=\s))\*\s"]) removes them
from both texts first, and a difference that disappears then is also `text_only`.

None of these is a change of meaning. Rules that write links (`same_item` vs `labels_changed`)
and `pdt diff` use these classes, so they agree on what counts as a change.
"""

import re

DASHES = re.compile(r"[‐-―−]")
ITEM_REF = re.compile(r"\((?i:computed in )?(?:[A-Z]{1,3} )?[A-Z]{1,3}-\d+[a-z]?\)"
                      r"|\b(?:[A-Z]{1,3} )?[A-Z]{1,3}-\d+[a-z]?\b"
                      r"|\((?i:recode|computed|raw)\)")


def norm(text):
    """Text for comparison: case, whitespace and dash variants folded."""
    text = DASHES.sub("-", str(text or ""))
    text = re.sub(r"\s*-\s*", "-", text)
    return " ".join(text.lower().split())


def strip_refs(text):
    """norm(), with questionnaire item references (IC-9, JB-4, FC A-2b) removed."""
    return norm(ITEM_REF.sub(" ", str(text or "")))


def strip_markers(text, ignore):
    """text with every match of the ignore patterns replaced by a space."""
    text = str(text or "")
    for pattern in ignore:
        text = (pattern if hasattr(pattern, "sub") else re.compile(pattern)).sub(" ", text)
    return text


def compare_text(a, b, ignore=()):
    """'same'; 'text_only' (case, whitespace, dashes, or ignored markers); 'reference_only'
    (item references); 'changed'. ignore: regular expressions for a dataset's formatting markers."""
    if (a or "") == (b or ""):
        return "same"
    if norm(a) == norm(b):
        return "text_only"
    if ignore:
        a, b = strip_markers(a, ignore), strip_markers(b, ignore)
        if norm(a) == norm(b):
            return "text_only"
    return "reference_only" if strip_refs(a) == strip_refs(b) else "changed"


def is_change(how):
    """Whether a compare_text result is a change of meaning."""
    return how == "changed"


# ---------------------------------------------------------------- codes on one side only

EXPECTED_MAX = 5      # P(0 cases | Poisson mean 5) is under 1%


def absent_by_chance(n, total_here, total_there, expected_max=EXPECTED_MAX):
    """Could a code with n cases here have had none there, by chance?

    For documentation that lists only codes that occur (sources.yaml
    `lists_only_occurring_codes`), a code missing from the other release either had no
    cases there or no longer exists. Scale n to the other release's total for the
    variable: if fewer than expected_max cases would be expected, zero is plausible.
    NSFG PREGORDR 15 (1 case) passes; MARSTAT 6 "Never been married" (2,820 cases,
    then recoded away) doesn't. Without counts, nothing can be said: returns False.
    """
    if n is None or not total_here or not total_there:
        return False
    return n * total_there / total_here < expected_max


def total_cases(record):
    """The cases the record's codes account for, from values[].n (0 if none has n)."""
    return sum(v.get("n") or 0 for v in record.get("values") or [])

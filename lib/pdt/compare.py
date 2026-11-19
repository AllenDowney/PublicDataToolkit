"""Compare two texts from documentation: is a difference a change, or only how it's written?

    compare_text(a, b) -> "same" | "text_only" | "reference_only" | "changed"

- `text_only`: equal once case, whitespace and dash variants are folded. The FARS records
  write "Dark - Not Lighted" where the manual has "Dark – Not Lighted"; the NSFG's
  2017-2019 codebook writes "NEVER MARRIED" where 2022-2023 writes "Never married".
- `reference_only`: equal once questionnaire item references are removed as well:
  "IC-9 How important..." vs "IC-7 How important...", "R's age at interview" vs
  "R's age at interview (FC A-2b)" or "(Computed in FC A-2b)". Item numbers move with
  the questionnaire's layout. A parenthesized variable-type marker, "(RECODE)" as the
  NSFG's 2017-2019 labels have it, is removed too: the record's variable_type holds it.

Neither is a change of meaning. Rules that write links (`same_item` vs `labels_changed`)
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


def compare_text(a, b):
    """'same'; 'text_only' (case, whitespace or dashes); 'reference_only' (item references); 'changed'."""
    if (a or "") == (b or ""):
        return "same"
    if norm(a) == norm(b):
        return "text_only"
    return "reference_only" if strip_refs(a) == strip_refs(b) else "changed"


def is_change(how):
    """Whether a compare_text result is a change of meaning."""
    return how == "changed"

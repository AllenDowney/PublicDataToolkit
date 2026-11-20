"""The standard's vocabularies, for the generated views: origins, missing types, completeness
labels and link relations, with their meanings as STANDARD.md's tables give them (markdown).

STANDARD.md isn't installed with the library, so the tables are copied here.
lib/tests/test_vocab.py checks them against STANDARD.md and the schemas' enums, so they can't
drift apart.
"""

# The toolkit's home, linked from every dataset site's About page; `pdt views --toolkit-url` overrides it.
TOOLKIT_URL = "https://github.com/AllenDowney/PublicDataToolkit"

# STANDARD.md §3, "Origins": (origin, meaning).
ORIGINS = [
    ("publisher", "read from the publisher's documentation"),
    ("upstream_package", "read from a third-party package that redistributes the publisher's documentation (gssrdoc)"),
    ("data_file", "read from the data file's own metadata: Stata or SPSS labels, extended missing values"),
    ("rule", "computed by a named rule from other fields"),
    ("hand", "a judgment entered through a hand-written build input, by a person or an agent. `author` names who "
             "made it: a person, or the agent and its task (\"Claude (PublicDataToolkit Task 35)\"), never a person "
             "who didn't make or check it"),
    ("model", "drafted by an LLM"),
]

# STANDARD.md §4.2, "Missing types": (type, meaning, examples).
MISSING_TYPES = [
    ("dk", "The respondent didn't know or couldn't choose", "GSS `.d`; ANES 98 \"DK\""),
    ("refused", "The respondent refused", "GSS `.r`"),
    ("no_answer", "No answer recorded, reason unknown", "GSS `.n`; ANES 99 \"NA\""),
    ("inap", "Not applicable: outside the universe or skipped by design", "GSS `.i` \"iap\""),
    ("skipped", "The respondent skipped it (self-administered modes)", "GSS `.s` \"skipped on web\""),
    ("not_asked", "Not asked of this respondent's wave, form or interview, including a panel round the respondent "
                  "missed", "GSS `.y` \"not available in this year\"; ANES \"no Post IW\"; NLSY -5 \"non-interview\""),
    ("not_available", "Asked, but not released in this file", "GSS `.x` \"not available in this release\""),
    ("uncodeable", "Answered, but couldn't be coded or imputed", "GSS `.u`, `.p`"),
    ("unknown", "The source records the value as unknown. For administrative and coded data, where no respondent "
                "was asked", "FARS \"Unknown\", \"Reported as Unknown\""),
    ("unspecified", "The source marks the code missing but gives no reason", "GSS `.z` \"see codebook\""),
    ("other", "Anything else; say what in the label", ""),
]

# STANDARD.md §4.2: a code's kind (the schema's enum; the meanings are the section's text).
KINDS = [
    ("valid", "an answer or value, as the publisher classifies it"),
    ("missing", "a missing-value code, with one or more missing types saying why"),
    ("unresolved", "a code the sources don't explain; never recoded by missing type unless asked"),
]

# STANDARD.md §7, "What the completeness labels promise": (label, the result is, allowed in the filter).
COMPLETENESS = [
    ("complete", "every record in scope that matches the filter, with nothing else",
     "only fields whose origin is `publisher`, `upstream_package`, `data_file` or `hand`, and groups with those "
     "origins"),
    ("complete_by_rule", "the same, but the filter also uses derived properties or rule-made groups",
     "the above, plus derived properties and `origin: rule` groups, each with its rule version"),
    ("approximate", "anything else: text search, annotations, or a result an agent assembled itself", "anything"),
]

# STANDARD.md §5, link relations: (relation, meaning). The standard's table puts split_from and
# merged_into in one row.
RELATIONS = [
    ("same_item", "The same question, asked the same way"),
    ("renamed", "The name changed"),
    ("wording_changed", "The question text changed"),
    ("codes_changed", "The value set changed"),
    ("range_changed", "The valid range or a top code moved while every code kept its meaning (Pulse TBIRTH_YEAR's "
                      "yearly top code; THHLD_NUMPER 1–10 → 1–40)"),
    ("labels_changed", "The variable label or value labels changed (e.g. a corrected label). When the codes changed "
                       "too, the link also lists `codes_changed`"),
    ("universe_changed", "Who was asked changed"),
    ("data_revised", "The same item, but its values in the data were revised between releases: recoded missing "
                     "codes, restored or corrected data, reassigned cases. Release notes are the usual source"),
    ("derived_from", "`from` is built from `to`, as a cumulative-file variable is built from single-year items"),
    ("split_from", "One variable became several, or several became one"),
    ("merged_into", "One variable became several, or several became one"),
    ("rescaled", "The same construct, but the scale was re-estimated, so values aren't comparable across the pair "
                 "without the publisher's trend or linking file. PISA's ESCS and BELONG are re-estimated each cycle"),
]


def meanings(table):
    """{term: meaning} for one of the tables above."""
    return {row[0]: row[1] for row in table}

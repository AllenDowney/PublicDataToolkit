# Religion keys for the full releases

For a rerun of the `religion` question once a dataset repo covers a whole release. Built 2026-11-19, before any repo holds more than a slice, so no search tool could shape them.

| Key | Release | Variables | Candidates | Hits | Neutral |
|---|---|---|---|---|---|
| [`gss_religion.yaml`](gss_religion.yaml) | GSS `7224r3a` (gssrdoc) | 6,904 | 762 | 241 | 327 |
| [`anes_cdf_religion.yaml`](anes_cdf_religion.yaml) | ANES CDF `20260205` | 1,029 | 27 | 13 | 12 |
| [`nsfg_religion.yaml`](nsfg_religion.yaml) | NSFG `2022-2023`, three files | 3,178 | 20 | 17 | 3 |

## Method

1. **Candidates** from the publisher's documentation in each repo's `data/raw/`: every variable whose label or question text matches a religion keyword. In the GSS, also every variable with the publisher subject Religion, Jews or Prayer In School, or in a religion module. In the NSFG, also every item in the religion section.
2. **Each candidate read by hand** and sorted by the rule below. The GSS decisions are the `HIT` and `NEUTRAL` lists in [`build_gss_religion.py`](build_gss_religion.py), which writes the key.
3. **Checked** against CultureWar's [`religion_inventory.md`](../../../../CultureWar/notebooks/inventories/religion_inventory.md) and `secularization_inventory.md`: every GSS name there that's about religion is in the key.

## The rule

| Status | What |
|---|---|
| `hit` | The respondent's own religion: affiliation or identity (now or when growing up, including switching), attendance and participation, practice (prayer, meditation, religious media, rites), the importance of religion to them, and religious belief or experience. |
| `neutral` | About religion, but not the respondent's own: other people's religion (spouse, parents, friends, network), attitudes toward religious groups, religion in public life and tolerance, giving and volunteering, ratings of a congregation, religion and science, vignettes, and the clergy-misconduct module. In the GSS, anything the publisher tagged Religion that isn't a hit. |
| out | Matched a keyword but isn't about religion ("mass transportation", "faith in" a level of government). |

The neutral band is wide on purpose: those items are defensible either way, and the score ignores them.

## Limits

- A key built from candidates can't contain a variable no candidate rule caught: an on-topic item with no religion keyword, subject or module. The GSS subject list covers most of the religion modules, which limits this.
- One reader made the decisions. A second reader on a sample of the GSS hits and neutrals would show how stable the boundary is.
- The GSS key uses gssrdoc, which documents release R2 (the gss thread's finding); variables new in R3a would be missing.

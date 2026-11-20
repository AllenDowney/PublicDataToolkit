# Task 64 — A MEPS slice

**Status:** `DOING (blue)`, claimed 2026-11-20.

The Medical Expenditure Panel Survey, Household Component (AHRQ) in `~/pdt-meps`, from the Copier template:
- the full-year consolidated file and one event file (office-based visits), for two or three recent years;
- tables keyed and referenced on the linking id `DUPERSID`;
- the design variables `VARSTR`, `VARPSU` and `PERWTyyF`.

Stop at any bot check. AHRQ's terms are recorded for Allen. Memory cap.

**Files:** `~/pdt-meps/`, this file and the Task 64 block on the board.

## Done (2026-11-20)

`~/pdt-meps`: commits `ba11f64` (records) and `bf3d3be` (agent/ and export/; docs/ gitignored). `pdt check`: 0 failures.

**What it holds.** Releases `2022`, `2023` and `2024`, each with two tables (247 records in all):

| Table | AHRQ files | Content | Key | References |
|---|---|---|---|---|
| `fyc` | HC-243, HC-251, HC-256 | 37 variables from the full-year consolidated file: ids, `VARSTR`, `VARPSU`, `PERWTyyF`, demographics, perceived health, three diagnoses, the K6 (`ADNERV42`, `ADHOPE42`, `K6SUM42`) and PHQ-2 (`ADDPRS42`, `PHQ242`) items, use and expenditure | `DUPERSID` | — |
| `ob` | HC-239G, HC-248G, HC-254G | the office-based medical provider visits file, whole | `EVNTIDX` | `DUPERSID` → `fyc` |

There are 19 sources with hashes: each file's Stata zip, codebook and documentation, and a saved download page. `design` is set per release.

**Findings**
- **The codebooks match the data.** In all six files, every column has a codebook entry, every value is listed or inside a listed range, and every unweighted count equals the data's. The expenditure bins print as "$9,668 - $1,246,195", which the parser reads as ranges.
- **Keys and references hold**, checked by hand. `DUPERSID` is unique in `fyc`, `EVNTIDX` is unique in `ob`, and every visit's person is in that year's `fyc`.
- **AHRQ marks its missing codes,** in a table of reserved codes in each file's documentation (section 2.2), with definitions. So codes take `origin: publisher`, with types read from the definitions:

  | Code | Label | Type |
  |---|---|---|
  | -1 | Inapplicable | `inap` |
  | -2 | Determined in previous round | `not_asked` |
  | -7 | Refused | `refused` |
  | -8 | Don't know or not ascertained | `dk` and `no_answer` |
  | -10 | Top coded | `not_available` |
  | -15 | Cannot be computed | `uncodeable` |

  - **A documentation gap:** the 2022 tables don't list -15, yet four 2022 variables use it (`EMPST53`, `VSTCTGRY`, `MEDPRESC`, `FFBEF22`). Those four codes stay `unresolved`. A correction, or an earlier year's table, could settle them.
  - An unlabeled negative value is a value: `FAMINC23` lists a family income of -230.
- **Links (164) by rule `meps_year_suffix`,** from AHRQ's naming convention (documentation section 2.4): a name ending in the year's digits (`TOTEXP23` → `TOTEXP24`) is the same item next year. An alteration adds `_Myy`, which the rule doesn't match. The links split as:

  | Table | `same_item` | `same_item` + `renamed` |
  |---|---|---|
  | `fyc` | 46 | 28 |
  | `ob` | 64 | 26 |

- **There's no question text.** The codebooks have labels only. The documentation's Appendix 1 gives each variable's questionnaire item, and the wording is in the HC questionnaires, which aren't fetched yet.

**For Allen: the terms.** It's AHRQ's Data Use Agreement (documentation section A), quoted in `dataset.yaml`:
- statistical use only;
- no attempt to identify anyone;
- no linking except MEPS with NHIS, and only in a data center;
- a request to cite AHRQ and MEPS.

It says nothing about redistributing the files, and there's no login or click-through. All four fields are `unknown`.

**Not done:**
- Question text, from Appendix 1 and the questionnaires.
- `make data`.

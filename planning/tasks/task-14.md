# Task 14 — Agent views: `agent/` index and shards

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE` (views thread, 2026-11-19; not pushed)

Build the LLM-facing view from STANDARD.md §7 in a new library module. It generates, for a dataset repo:
- `agent/index.md`;
- shards by group, by table and by scale signature, each under about 20k tokens, in two forms: JSONL, and one line per variable for reading;
- corrections applied and marked.

Search results label themselves `complete`, `complete_by_rule` or `approximate`, by the rules in §7. Spike step 5 needs this.

**Files:** new `lib/pdt/views.py` (or `lib/pdt/agent.py`), `lib/tests/test_views.py`, and `agent/` in the dataset repos (generated). A `make views` target in each dataset repo's Makefile.

**Done when:** the four dataset repos have `agent/`, the tests pass, and an agent given only `agent/` can find every GSS abortion item and say the answer is `complete`.

**Progress (2026-11-19, views thread):**
- **Built.** [`lib/pdt/views.py`](../../lib/pdt/views.py) writes `agent/`: `index.md`, `SKILL.md`, `manifest.json`, and shards by release/table, group, publisher subject, scale signature and topic annotation. Each shard comes as `.txt` (one line per variable) and `.jsonl` (corrected records with a `view` block), and is split into parts above about 20k tokens. [`lib/pdt/search.py`](../../lib/pdt/search.py) holds the filter language and assigns the completeness label. Every shard is a filter result, and a test reruns each shard's filter. CLI: `pdt views [PATH]` and `pdt search PATH --filter JSON`. Tests: [`lib/tests/test_views.py`](../../lib/tests/test_views.py).
- **All four dataset repos** have `make views` and a generated `agent/`, and `pdt check` passes in each.
- **Blind test passed.** A fresh agent given only a copy of `pdt-gss/agent/` found the 7 abortion items, labeled the list `complete` with respect to NORC's subject list and the 50 variables in scope, and read about 3,000 tokens. It went SKILL.md → index.md → `shards/subject/abortion.txt`.
- **Fixed from the blind test.** The agent read the gap in `1972-1985,1987-2024` as "no survey in 1986". The index now lists each release's waves and says that a gap means the variable wasn't available in those waves.

**Decisions and findings:**
- **Publisher subjects are groups** (Task 25 decision, f3d70d9). The `subject` filter and subject shards use groups of kind `subject`, and topic annotations are always `approximate`.
- **JSONL header:** the first line is `{"shard": {...}}`, and `agent/manifest.json` holds the input hash (now in §7). `views.is_current(root)` is ready for C8 when Task 17 wants it.
- **Size:** JSONL costs about 1,200 tokens per GSS variable (availability 36%, provenance and origins 36%). The line form costs about 60. Recorded as open in Task 25.
- **Non-surveys:** FARS has no question text, so the line form falls back to `notes`, marked `[notes]`. If Task 25 adds a definition field, the line form should use it.
- **Redundant shards:** in the GSS slice, `subject-abortion` and `battery-abdefect` have the same members, labeled `complete` and `complete_by_rule`. SKILL.md says to cite the one with the better label.
- **`cli.py` is shared:** Tasks 15 and 16 will add subcommands too, so whoever goes next should check for conflicts there.

**After the Task 25 answers (a995a31):**
- **Compact JSONL** (§7). `availability` maps each form, or `all`, to runs of waves, and `n` is dropped. `origins` gives each field's origin as a short string, and `origins.codes` holds the origin the codes share; a code without its own origin falls back to `provenance.codes`. Each shard header's `full_records` names the canonical files in `metadata/`. The GSS cost fell from about 1,200 to about 480 tokens per variable (all 50: 61k to 24k; Abortion: 8.4k to 3.3k).
- **Line form** uses question text, else `[description]`, else `[notes]`.
- **SKILL.md** now uses §7's wording: when two filters return the same set, report the stronger label.

**Blind tests on `pdt-gss/agent/`** (Sonnet, given only a copy of `agent/`; questions: the abortion items with years and ballots, `abany`'s codes and their origin, and from test 3 on, whether `abany` was asked in 1986):

| Test | Shards | Tokens read | Result |
|---|---|---|---|
| 1 | full JSONL | about 3,000 | 7 items, `complete`; said "1986 has no survey" (wrong) |
| 2 | compact JSONL | about 8,000 (also read JSONL for codes) | all correct except "the release has no 1986 wave" (wrong again) |
| 3 | line form with waves by form and `(not 1986)` | about 6,000 | all correct: 1986 is a release wave and `abany` skipped it; asked of everyone through 1987, forms A and C from 1988 |

Remaining friction from test 3: the agent first misread the release's wave list (`1982-1991`) and then corrected itself; it isn't sure which of two identical shards to cite until it reads SKILL.md; and `abany` also sits in the "Split Ballots" subject shard, which looks off-topic.

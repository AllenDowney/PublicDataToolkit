# Task 26 — The full GSS release

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE` — 2026-11-19 (blue, formerly gss)

Build all of release 7224r3a in `pdt-gss`, not just the 50-variable slice. Eval's topic test needs a full release: on the slices, agents just read everything (Task 23).

- **All 6,943 variables,** from gssrdoc 0.9 (pinned, Task 21). For the 40 names it lacks, use the fallback deferred from Task 21: labels and codes from the R3a Stata file, and text from the R3a codebook where it has an entry.
- **Groups:** batteries by rule and subject groups over the whole file. Battery groups no longer need the slice's "all members present" rule.
- **Links:** the 477 pending note-derived links can now be written, where both releases have records. 7224r3 should also be full.
- **The slice:** keep its 50 variables identifiable, because eval's slice keys refer to them. Ideally `build/slice.yaml` stays as a named subset, and the full build is the default.
- **Checks:** `pdt check` passes, `pdt views` runs (watch shard sizes and counts), and `build/report.md` covers C3–C5 for the whole file.
- **Then** tell the coordinator, so views + site regenerates the views and eval reruns the topic test with its full keys (`eval/keys/full/`, to be rebuilt from 0.9).

**Files:** `../pdt-gss/` only (not its `agent/` or `docs/`).

## Findings (2026-11-19, blue)

pdt-gss commits: `bd67680` (records) and `cf22b43` (agent/ and export/; docs/ untracked). `pdt check`: 0 failures.

**What was built**

| | 7224r3 | 7224r3a |
|---|---|---|
| Records | 6,942 | 6,943 |
| With question text | 6,930 | 6,931 |
| With a stem/item split | 3,172 | 3,172 |
| Not in gssrdoc 0.9 | 0 | 2 (`vote_ts`, `pres_ts`) |

- **Source of the records.** `build/build_records.py` (formerly `build_slice.py`) builds every variable from gssrdoc 0.9 and each release's Stata file. `build/releases.yaml` lists the releases.
- **The fallback is needed for 2 names, not 40.** gssrdoc 0.9 already covers the 38 names that 0.8.2 lacked. `vote_ts` and `pres_ts` take their labels and codes from the Stata file, and their description and notes from the 2024 codebook (p. 457), with `origin: publisher` and the page. `make codebook` runs pdftotext on the codebook.
- **Groups.**
  - 485 batteries by rule (2 to 84 members).
  - 168 subject groups from gssrdoc.
  - The slice is the group `slice-snake-case` (kind `other`, origin hand). `build/slice.yaml` stays the named subset, with its hand-entered measures.
- **Scale signatures.** 1,341, from the shared rule `pdt.derived` (Task 27, `per_release=False`).
- **Links.** 6,974 are written: 53 from NORC's notes and 6,921 by rule `gss_same_name_same_item`. 425 are still pending: R1→R2 and R2→R3 links need R1 or R2 records, which pdt-gss doesn't have.
- **Missing codes.**
  - Rule `gss_extended_missing_types` 0.3 adds "can't choose" (ISSP items) as `dk`. That resolves 863 codes, and C5's false count differences fell from 184 to 24.
  - When gssrdoc gives no label for a missing code that occurs, the Stata label is used, with its own `data_file` origin.
  - 12–14 codes per release are still unresolved because neither source labels them. About 360 valid codes are marked unresolved because their label looks like a missing code, e.g. occ80 998 "dk".

**C3–C5 in `build/report.md`** (per release; the report lists 40 examples of each kind)
- C3: about 360 suspect valid codes and 12–14 unlabeled missing codes.
- C4: 1,177 variables have values that occur with no label. Most are numeric variables, such as counts and codes, whose measure isn't set.
- C5: 24–25 count differences, mostly vote/pres items where gssrdoc excludes code 4 "refused". 196 ballot differences, e.g. 2006 ballot D. 2–4 year differences.

**Views (pdt views).** It takes about 2.5 minutes.

| Directory | Size | Contents | Committed? |
|---|---|---|---|
| `agent/` | 60 MB | 659 shards in 1,888 files; median 10 KB, max 78 KB | yes |
| `export/` | 16 MB | data-dict YAML | yes |
| `docs/` | 7,605 files | the site | no: gitignored, published to Pages (coordinator, `a8237e4`) |

**Build.** About 7–10 minutes. Two things dominate:
- pyreadstat's per-read cost. Each chunk is read twice, plain and with user-missing letters, which is faster than parsing mixed columns.
- Building about 14,000 records.

**Also done here**
- `design` in `dataset.yaml`: weights, `vstrat`, `vpsu`.
- Authors, following Allen's rule (STANDARD §3):
  - slice facts: `Claude (PublicDataToolkit Task 5)`;
  - release-notes transcription: `Claude (PublicDataToolkit Task 21)`;
  - partyid's measure: Allen Downey's decision, with his note.
- Makefile targets `download`, `data` and `package` (Task 18 follow-up).

**Not done**
- `questions[].number` isn't set; gssrdoc has no item numbers.
- C4's unlabeled values mostly need a `measure` or `valid_range` per variable, which needs a decision per variable. Left for later.

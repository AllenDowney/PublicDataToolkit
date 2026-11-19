# Task 5 — snake_case spike

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DOING` — step 1 drafted 2026-11-19. Scope in [`planning/plan.md`](../../planning/plan.md) §9, decided 2026-11-19: GSS, ANES and MTF.

1. Write `STANDARD.md` and `schema/`.
2. GSS slice (30–50 variables) from CultureWar's extracted JSON.
3. ANES CDF slice (30–50 variables).
4. MTF slice: one 12th-grade year, two or three forms, and items whose V-number changes. Needs an ICPSR login and a terms check first.
5. Generate the three forms for all three slices. Run one structural and one topic query against hand-built answer keys.
6. Prepare the 2-minute demo.
7. Optional, if a teammate joins: an open-portal dataset in parallel.

Record what ended up in dataset-specific extensions and where the agent got stuck. Those notes are the main result.

**Progress (2026-11-19), step 1:** [`STANDARD.md`](../../STANDARD.md) v0.1 and nine JSON Schemas in [`schema/`](../../schema/), with real GSS and ANES example records in [`schema/examples/`](../../schema/examples/). [`schema/check_examples.py`](../../schema/check_examples.py) validates them and confirms five bad records are rejected; all pass.

Changes from plan §3–4, made while writing the standard:
- **New `dataset.yaml`** next to `sources.yaml`, for the dataset's terms, releases and what "wave" and "form" mean in it.
- **Terms and acquisition are separate fields.** The plan listed `ship`, `build-only` and `manual` as one set of values. Now each source has `redistribution` (`ship`, `build-only` or `unknown`) and `acquisition` (`automated` or `manual`). `unknown` blocks shipping.
- **Corrections aren't applied to source records.** `variables.jsonl` keeps the publisher's text, and the library applies `corrections.jsonl` when it builds the views.
- **`questions` is a list.** ANES VCF0803 has three wordings, by year and mode.
- **Codes can be strings,** for Stata extended missing values such as `.d`.
- **Each missing code needs its own origin**: publisher, data file, rule or hand.
- **Nine missing types:** `dk`, `refused`, `no_answer`, `inap`, `skipped`, `not_asked`, `not_available`, `uncodeable`, `other`. One code can have several (GSS `.m` "dk, na, iap").
- **Link relations are a list,** so one pair can be both renamed and reworded. Links can't come from a model.

Findings:
- **The ANES codebook lists VCF0803 code 9, "DK; haven't thought much," as valid.** The standard keeps the publisher's classification, so it's stored as valid. A label regex would have called it missing.
- **gssrdoc's MIT license covers its code, not NORC's documentation,** so the gssrdoc source takes the GSS terms. The GSS terms are still unreviewed.
- **No Python environment for the toolkit yet.** The base Python lacks `jsonschema`; the check ran with a temporary install. The shared library (`lib/`) will need a `pyproject.toml`.
- **Still open:** how to choose release ids (`7224r3a` from the GSS file name, `20260205` from the ANES release date). Listed in STANDARD.md §10 with the other provisional parts.

**Progress (2026-11-19), step 2, the GSS slice:** a new local repo, `pdt-gss`, next to this one; not pushed. It has 45 variables from release 7224r3a:
- design variables;
- the abortion battery (7) and the core spending battery (18), both complete;
- two ballot-split items (`natracey`, `natfarey`);
- the race items with corrections (`racopen`, `racfew`, `rachaf`, `racmost`, `racschol`);
- `grass` (marijuana, for the cross-survey topic query) and five others.

`build/build_slice.py` builds the records from gssrdoc (question text, value labels, years and ballots) and the Stata file (variable labels, and which missing codes occur), using only pandas' public API. Four corrections from gssrdoc issue #1 are in `corrections.jsonl`. `tests/check_metadata.py` runs C1, C2, C6, C7, C9 and C10, and all pass; C7 was confirmed to fail on a stale correction. The build runs C3–C5 against the data.

GSS terms, decided by Allen on 2026-11-19: everything `ship`. The 2024 R3a codebook grants MIT-style rights, provided NORC's notice is included (`pdt-gss/NOTICE.md`). The data goes in a GitHub release when `pdt-gss` is published.

Findings from the GSS slice:
- **gssrdoc doesn't match release 7224r3a.** Its 2024 counts differ from the data: `racopen` 462 vs 981, `grass` 867 vs 862. So gssrdoc was scraped from an earlier 2024 release. Ballots and years match exactly for every other variable.
- **Missing codes per variable come from the data.** gssrdoc lists the same twelve `NA(x)` codes for every variable. The data shows which occur: `.d`, `.i` and `.n` in 41 of 45 variables, `.s` in 32, `.y` in 8, and none of the others.
- **gssrdoc doubles every apostrophe** ("DON''T") in 239 variables. It's handled by a recorded parser rule rather than 239 corrections. STANDARD.md rule 3 should say that systemic source artifacts may be fixed by a named rule.
- **`.z` "see codebook" has no missing type,** but the data file says it's missing. The schema can't say "missing, reason unknown"; `other` is the closest. `unresolved` doesn't fit, because the kind is known.
- **The shared-stem rule for batteries is fragile.** `natrace` was left out until the rule accepted an item letter right after "?". The rule also merges the Y and Z wording versions, which NORC fields on different ballots, into one 26-item group, and it can't see the `racfew`/`rachaf`/`racmost` chain, which has no shared stem. The build writes a group only when all its members are in the slice, and reports partial ones.
- **gssrdoc has no yearly counts for weights,** so the build counted `wtssps`'s availability in the data and labeled that field `origin: data_file`.
- **Per-code provenance is bulky.** Every missing code repeats the same long origin. A default origin for missing codes per variable would shrink the records a lot, which matters for files LLMs read.
- **A possible documentation error, not verified:** the spending stem repeats a clause ("name some of these problems, and for each one I'd like you to name some of these problems…").
- **Only one extension so far:** `gss.modules`. Every slice variable is `Core`, so a module group would say nothing.

**Progress (2026-11-19), step 3, the ANES CDF slice:** a new local repo, `pdt-anes-cdf`, not pushed. It has 32 variables from the February 5, 2026 release:
- design variables;
- ten thermometers;
- ideology scales;
- abortion, gay-rights and death-penalty items;
- pre- and post-election vote items.

`build/build_slice.py` parses the HTML codebook's Valid, Missing, Sources and Notes sections, with block regexes taken from ExtractANES. Unlike the old script, it keeps the codebook's own valid/missing split, types each missing code, and doesn't compute a valid range from listed codes. The Stata file is read only through pandas' public API. The same `check_metadata.py` passes, with no extensions needed.

ANES terms, decided by Allen on 2026-11-19: everything `ship`. electionstudies.org is behind a Cloudflare bot check, so neither the agent nor a headless browser could read the terms (an archive.org request was blocked as a way around the check). Allen saved the three pages from a browser; they're kept in `pdt-anes-cdf/data/raw/terms/` and recorded as source `anes-terms-pages`. They say:
- use the data only for research or statistical purposes, make no use of respondents' identities, and cite ANES;
- public release datasets are "public goods," and derived datasets may be shared with a link back to the original;
- no login is needed any more.

They don't address mirroring the original files or LLM processing; Allen decided both may ship. The README links back to the original dataset, as the FAQ asks.

**For the instructions:** when a publisher's site blocks scripts, the agent asks the person to save the terms pages from a browser, stores them in `data/raw/terms/`, records them as a source, and quotes them in `dataset.yaml`. That worked here, and it keeps the evidence for each terms decision.

Findings from the ANES slice:
- **The checks against the data find codebook errors:**
  - VCF0878 (gays adopting) has 1,130 cases of code 2, which the codebook doesn't list, and 2016 has data but is missing from its Sources. It looks like 2016 was coded 1/2 instead of 1/5; CultureWar's `harmonize_vcf0878_adopt` recodes 5 to 2 for the same reason.
  - VCF0704 (presidential vote) has 2016 data, but 2016 is missing from its Sources.
  - VCF0104 and VCF0301 have 1954 data that isn't in their Sources; VCF0830 has 2012 data that isn't.
  - There are undocumented codes: `-1` in VCF0806 and VCF9236 (245 cases each), `-8` in VCF0218 and VCF0224, `-4` in VCF0206. They're marked `unresolved`.

  These are candidates for `corrections.jsonl` once checked against the PDF codebook and the ANES errata.
- **The standard fits without extensions.** Three wordings by year and mode (VCF0803), INAP as Stata's system missing (`.`), codes listed under Valid that look like DK (VCF0803 code 9, VCF0876 code 8), and ranges with labeled codes beyond them (thermometers 0–96 plus 97) all fit the schema.
- **Missing labels mix several reasons in one code** ("NA; no Post IW; form III,IV (1972)"). Splitting at ";" and typing each part works. Parts the rule can't type ("don't recognize", "breakoff", "'other' vote") are listed in the build report.
- **Pre/post phase is mostly not recorded.** Only one variable's notes say "This is a pre var." The rest is implied by labels ("no Post IW"), so `phase` is nearly empty.
- **No marijuana item in the CDF,** so the cross-survey topic query (spike step 5) needs another subject. Abortion, gay rights and the death penalty are in both the GSS and ANES slices.
- **No groups.** The CDF has 92 thermometers whose shared question text sits in a preamble before VCF0201, which the variable parser doesn't see. A `thermometer` scale signature, from the "Degrees" range, supports the structural query instead (`complete_by_rule`).
- **The shared library is overdue.** `check_metadata.py` was copied from `pdt-gss` into `pdt-anes-cdf`, which is exactly the drift between repos the plan warned about. It should move into `lib/` here before MTF.

**Progress (2026-11-19), the shared check:** `check_metadata.py` moved into the shared library, as `lib/pdt/check.py` with `pdt check` as the command. `pyproject.toml` packages it as `publicdatatoolkit` with `schema/` bundled, so there's one copy of the schemas.
- It implements C1, C2, C6, C7, C9, C10 and C11 (README sections and CLAUDE.md). C3–C5 still run in each repo's build, because they need the data and the code to read it; C8 waits for the views.
- Two hacks in the copied script were replaced: the regex scan for source ids and the count of unreviewed model output now walk the records.
- `lib/tests/test_check.py` has 14 tests: a small valid repo passes, and each check catches its own kind of breakage. All pass.
- Both dataset repos dropped their copy. Their `make check` runs `python -m pdt check .` against the toolkit checkout next to them, so nothing is installed into the conda env. Both pass, with the same reports as before.
- `schema/check_examples.py` uses the shared validators too.

# Instructions: building or improving a dataset repo

For an agent (or a person) turning a public dataset into a repository that meets [`STANDARD.md`](../STANDARD.md). The procedure is the eight steps of [plan §5](../planning/plan.md#5-the-procedure-an-agent-follows), one file each. Each step says what to do, which parts of the standard apply, what to check before moving on, and when to stop and ask a person.

| Step | File | Result |
|---|---|---|
| 1 | [Survey the dataset](01-survey.md) | a decision to build, the release ids, the tables, a terms question for a person |
| 2 | [Sources and download](02-sources-and-download.md) | `dataset.yaml`, `sources.yaml`, files in `data/raw/` with hashes |
| 3 | [Parse the documentation](03-parse-documentation.md) | `build/` that writes `variables.jsonl`, checked against the data |
| 4 | [Type the missing codes](04-missing-codes.md) | every code `valid`, `missing` with types, or `unresolved`, each with an origin |
| 5 | [Record availability](05-availability.md) | waves, forms and phases, checked against the data |
| 6 | [Links and corrections](06-links-and-corrections.md) | `links.jsonl`, `corrections.jsonl`, histories if the publisher has them |
| 7 | [Generate the views](07-generate-views.md) | `agent/`, `docs/`, `export/` |
| 8 | [Publish and check](08-publish-and-check.md) | `pdt check` passes; README and CLAUDE.md; a data release if the terms allow |

The parsers for each kind of source are skills, in [`skills/`](../skills/): an upstream package, an HTML codebook, a PDF or text codebook, the data file's own labels, and release notes.

**Improving an existing repo** (adding variables, a release, a source): read the repo's CLAUDE.md and `build/report.md` first, start at the step the change belongs to, and redo the checks of every later step. Adding variables to a slice is step 3 onward; a new release is step 2 onward; a new erratum is step 6. To bring a repo up to a newer toolkit release, run `copier update` in it, then `make views` and `make check` ([`templates/README.md`](../templates/README.md#updating-a-repo-from-a-newer-template), STANDARD.md §2.4).

**Using a finished repo** to find variables is a different job. Each repo's generated `agent/SKILL.md` covers it; don't write another version.

## The four builds these instructions come from

Every example below is a real trap from one of these, checked out next to this repo:

| Repo | Documentation | Data | What it taught |
|---|---|---|---|
| [`pdt-gss`](../../pdt-gss/) | gssrdoc (an R package that scrapes GSS Data Explorer) | Stata | an upstream package can document a different release from the data |
| [`pdt-anes-cdf`](../../pdt-anes-cdf/) | HTML codebook | Stata | checks against the data find codebook errors; the site blocks scripts |
| [`pdt-nsfg`](../../pdt-nsfg/) | PDF codebooks as text | SAS, three tables | no missing-code markings; page-break headers; a correction in a margin box |
| [`pdt-fars`](../../pdt-fars/) | an 823-page manual covering 1975–2024 | CSV with label columns, four tables | code matrices by year range; conditional references between tables |

Read their build scripts in `build/` and their `build/report.md` before writing a new build. They are short, and most of what a new build needs is in one of them.

## Rules that hold at every step

- **Stop and ask a person** about:
  - terms of use;
  - logins;
  - a site that blocks scripts (after trying a headless browser once, and stopping at any bot check);
  - which upstream source or version to pin;
  - anything that would ship data or documentation.

  Write the question down where the person will see it (the project board, or a message to the coordinating thread) and carry on with work that doesn't depend on the answer.
- **Never decide terms yourself.** `unknown` blocks shipping (STANDARD.md §8). Recording what a page says is fine; deciding what it permits isn't.
- **Check every source against the data.** Each of the four builds found documentation that didn't match the data file: gssrdoc documented an older release; the ANES codebook omitted years and codes; NSFG names differ in case; the FARS manual's labels differ from the CSV's. The data file is the arbiter of what exists; the documentation is the arbiter of what it means.
- **Never hand-edit generated files** (`metadata/releases/`, `groups.jsonl`, `derived/`, `docs/`, `agent/`). Change the build, a hand-written build input (`build/slice.yaml`), or `corrections.jsonl` (STANDARD.md §2).
- **Write a build report.** Each build writes `build/report.md`: counts, coverage, codes and labels to look at, and the data checks. Read it after every build; it's where problems show up first.
- **Keep the record of what you did.** Findings and decisions go in the task's file, `planning/tasks/task-NN.md`, with its short entry on the [project board](../PROJECT_BOARD.md) kept current.

## What exists today, and what doesn't yet

| In the standard | Today |
|---|---|
| `pdt check` C3–C5 (coverage, codes, availability against the data) | Not in `pdt check` yet. Each build runs them and writes the results in `build/report.md` |
| C12, keys and references against the data | In the standard, not yet in `pdt check` (Task 17). The FARS build verifies every key and reference and lists the results in its report; the NSFG pregnancy → female reference was checked against the data by hand. Script it, as FARS does |
| `scripts/download.py`, the data release | Working (Task 18): `pdt download`, wrapped by `scripts/download.py` and `make download`; `pdt.release` writes the common-format files. The template includes `download.py`; `make data` needs a reader for each dataset |
| `scripts/extract.py` | Working: `pdt.extract` (Task 19), wrapped by the template's `scripts/extract.py`, which reads the releases and tables from `dataset.yaml` and refuses, with the fix, when `data/processed/` is empty |
| `templates/` and Copier | Working: `copier copy` from a tagged toolkit release, and `copier update` to a later one ([`templates/`](../templates/README.md); `copier.yml` is at the toolkit's root) |
| `pdt views`, `pdt search`, `pdt check` | Working. Run from the dataset repo with `PYTHONPATH=../PublicDataToolkit/lib python -m pdt <command> .` They need only the base install (`pyyaml`, `jsonschema`, `referencing`); the data files (`pdt.data`, `make data`, `extract.py`, the data checks) need the `data` extra: `pip install -e "../PublicDataToolkit[data]"` (pandas, numpy, pyarrow) |

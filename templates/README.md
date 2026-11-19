# The dataset repo template

A [Copier](https://copier.readthedocs.io/) template for starting a dataset repo (STANDARD.md §2, §2.4). It holds what the four existing repos share:
- `dataset.yaml` and `sources.yaml` skeletons that pass the schemas, with every term `unknown`;
- the Makefile targets `download`, `build`, `views` and `check`, with `scripts/download.py` (a wrapper for `pdt.download`, Task 18);
- README and CLAUDE.md skeletons, with the README sections of §2.3;
- `EXTENSIONS.md` and `.gitignore`;
- a `build/` stub: `build_records.py`, with the C3–C5 checks and the report, and `slice.yaml`.

## Use

Install Copier in its own environment (`pip install copier`), then, from the directory that holds this toolkit:

```bash
copier copy PublicDataToolkit/templates pdt-<dataset-id>
```

It asks for the dataset id, title, publisher, terms URL, first release and first source. Use an absolute path, or a URL once the toolkit is published, because Copier records the path in `.copier-answers.yml`.

## What a new repo needs next

`pdt check` on a fresh repo fails one check, C6: the first source hasn't been fetched yet. That's step 2 of [`instructions/`](../instructions/02-sources-and-download.md). After that:

1. **A person decides the terms.** Until then, commit nothing under `metadata/`: C9 fails when records are tracked while `terms.metadata` is `unknown`.
2. **Write the parser.** `build/build_records.py` raises `NotImplementedError` in `parse_documentation()` and `read_data()` until you do ([`skills/`](../skills/)).
3. **Add tables** to `dataset.yaml` by hand if a release has several files (§2.1; see pdt-nsfg and pdt-fars).
4. **Add `make data`** (the common-format release) when the terms allow it. It needs a reader for the publisher's data format; see pdt-nsfg's `scripts/build_data.py`.

## Updating a repo from a newer template

`copier update` needs the template's version, which Copier takes from a git tag. It finds one only when `copier.yml` is at the root of the toolkit's git repo. Here, `copier.yml` is in `templates/`, so generated repos record no `_commit` and **can't be updated yet**. A test with `copier.yml` at a repo root and `_subdirectory: templates/template` recorded the tag, and `copier update` brought a template change forward while keeping a local edit. Moving `copier.yml` to the root, and tagging releases as §2.4 says, is a proposal to the coordinator (Task 28).

## Test

```bash
COPIER=/path/to/copier pytest templates/
```

[`test_template.py`](test_template.py) renders the template, runs the build stub and `pdt check`, and checks the expected C6 failure. It then fills in the source and terms and expects `pdt check` to pass. It's skipped when Copier isn't installed.

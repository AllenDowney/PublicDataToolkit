# The dataset repo template

A [Copier](https://copier.readthedocs.io/) template for starting a dataset repo (STANDARD.md §2, §2.4). Its files are in [`template/`](template/); its questions are in [`copier.yml`](../copier.yml), at the toolkit's root (below). It holds what the four existing repos share:
- `dataset.yaml` and `sources.yaml` skeletons that pass the schemas, with every term `unknown`;
- the Makefile targets `download`, `build`, `views` and `check`, with `scripts/download.py` (a wrapper for `pdt.download`, Task 18);
- README and CLAUDE.md skeletons, with the README sections of §2.3;
- `EXTENSIONS.md` and `.gitignore`;
- a `build/` stub: `build_records.py`, with the C3–C5 checks and the report, and `slice.yaml`.

## Use

Install Copier in its own environment (`pip install copier`). Then copy from the toolkit's root, at a release tag, giving the toolkit by absolute path (or by URL, once the toolkit is published):

```bash
copier copy --vcs-ref v0.2.0 /abs/path/to/PublicDataToolkit pdt-<dataset-id>
```

It asks for the dataset id, title, publisher, terms URL, first release and first source. Copier records the path and the tag in `.copier-answers.yml`, and `copier update` needs both. A relative path breaks `copier update` from inside the new repo. Without `--vcs-ref`, Copier uses the latest tag.

## What a new repo needs next

`pdt check` on a fresh repo fails one check, C6: the first source hasn't been fetched yet. That's step 2 of [`instructions/`](../instructions/02-sources-and-download.md). After that:

1. **A person decides the terms.** Until then, records may be committed locally but not published. With no git remote, C9 reports tracked records whose terms are `unknown`; once the repo has a remote, it fails on them (STANDARD.md §9).
2. **Write the parser.** `build/build_records.py` raises `NotImplementedError` in `parse_documentation()` and `read_data()` until you do ([`skills/`](../skills/)).
3. **Add tables** to `dataset.yaml` by hand if a release has several files (§2.1; see pdt-nsfg and pdt-fars).
4. **Run `make data`** (the common-format files in `data/processed/`) under the memory cap. `scripts/build_data.py` reads Stata, SAS and SPSS files by their `format` in `sources.yaml`; for another format (a CSV in a zip, fixed-width text), write the reader call there using `pdt.readers`. `pdt check` then runs the data checks (C3–C5, C12) on the files.

## Updating a repo from a newer template

From inside a dataset repo, with its changes committed:

```bash
copier update
```

It moves the repo to the toolkit's latest tag (or `--vcs-ref vX.Y.Z`), applying the template's changes and keeping local edits. Where they conflict, it leaves conflict markers to resolve. Then run `make views` and `make check` (STANDARD.md §2.4).

This works only because `copier.yml` is at the toolkit's root, with `_subdirectory: templates/template`. Copier takes the template's version from a git tag, and it finds one only when `copier.yml` is at a git repo's root. **A change to `templates/template/` reaches dataset repos only in a tagged release** of the toolkit, as §2.4 says. Tags are made locally and pushed by Allen.

## Test

```bash
COPIER=/path/to/copier pytest templates/
```

The tests copy with `--vcs-ref HEAD`, so they test the working tree, uncommitted changes included, rather than the last tag.

[`test_template.py`](test_template.py) renders the template, runs the build stub and `pdt check`, and checks the expected C6 failure. It then fills in the source and terms and expects `pdt check` to pass. It's skipped when Copier isn't installed.

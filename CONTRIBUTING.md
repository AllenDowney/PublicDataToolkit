# Contributing to PublicDataToolkit

Thanks for helping. PublicDataToolkit is a draft: the standard, the library and the instructions are all open to change, and outside review is the most useful contribution right now.

The toolkit holds instructions, agent skills, a template and a small library (`pdt`) for building one repository per public dataset. Those repositories hold the metadata. This repository holds no data.

## Kinds of contribution

| You have | Open | What to include |
|---|---|---|
| A dataset you'd like covered | a [new dataset](https://github.com/AllenDowney/PublicDataToolkit/issues/new?template=new-dataset.yml) issue | the publisher, where the documentation and data are, and the terms of use as the publisher states them |
| An error in a publisher's documentation | a [documentation error](https://github.com/AllenDowney/PublicDataToolkit/issues/new?template=documentation-error.yml) issue | the dataset and release, the text as published, what it should say, and the evidence (the data, another document, the questionnaire) |
| A correction to a dataset repo's records | a pull request to that dataset's repo | the change in `metadata/corrections.jsonl`, with evidence and your name as author |
| A proposal for the standard | a [standard proposal](https://github.com/AllenDowney/PublicDataToolkit/issues/new?template=standard-proposal.yml) issue | the problem, a dataset where it shows up, and the change you suggest to [`STANDARD.md`](STANDARD.md) or [`schema/`](schema/) |
| A bug in `pdt` or the template | a [bug](https://github.com/AllenDowney/PublicDataToolkit/issues/new?template=bug.yml) issue, or a pull request with a test | the command, what you expected, what happened, and the dataset repo if it's public |
| Library code | a pull request | a test in `lib/tests/` for any change in behavior |

A documentation error is a fact about the publisher's documentation. A correction is a record in a dataset repo that fixes it. Report the error first. A correction cites it, and the report to the publisher goes in the correction's `upstream` field.

## The rules that matter

These come from the standard ([`STANDARD.md`](STANDARD.md) §3 and §8). A pull request that breaks one won't be merged, however useful it is otherwise.

1. **A person reviews the terms.** Every dataset's terms of use are read and decided by a person, recorded in its `dataset.yaml` with who decided and when. An agent can quote the terms, but it never decides them. Nothing built from a dataset ships while its terms are `unknown`.
2. **No microdata in git.** Data files never go in a repository. When the terms allow it, a dataset repo publishes the data as a release asset with checksums. When they don't, it ships a download script and the steps for getting the data from the publisher.
3. **Source facts and derived facts stay distinguishable.** Each fact records its origin: the publisher's documentation, the data file, an upstream package, a named and versioned rule, a person, or a model. Corrections are separate records, never edits to the source facts.
4. **Hand facts name their author.** A judgment made by a person or an agent says who made it and when (`origin: hand`, with `author` and `date`). Model output says which model, and whether a person has reviewed it.
5. **Links are asserted by the publisher, not inferred.** A link between variables in two releases cites the publisher's statement: release notes, a crosswalk, a documented naming convention, or the publisher's build code. Similarity alone doesn't make a link.

## Running the checks and tests

The library needs Python 3.10 or later.

```
git clone https://github.com/AllenDowney/PublicDataToolkit
cd PublicDataToolkit
pip install -e ".[data,test]"
```

Run the library's tests:

```
pytest lib/tests
```

Check a dataset repository against the standard:

```
pdt check path/to/pdt-dataset
```

`pdt check` reports each failure with its check number (C1 to C12, defined in [`STANDARD.md`](STANDARD.md) §9), and lists the checks it didn't run and why. A dataset repo is done when it reports no failures. After changing records, regenerate the views with `pdt views path/to/pdt-dataset` (or `make views` in the repo) before checking.

Start a new dataset repo from the template with [Copier](https://copier.readthedocs.io/), then follow the steps in [`instructions/`](instructions/):

```
copier copy --vcs-ref v0.2.0 https://github.com/AllenDowney/PublicDataToolkit pdt-dataset
```

## Pull requests

- Keep each pull request to one change, with a sentence saying why.
- Run `pytest lib/tests`. If you changed the schema or the standard, also run `python schema/check_examples.py`.
- Write documentation the way the existing files do: plain, specific sentences, tables for comparisons and short lists for steps.
- By contributing, you agree that your code is released under the MIT License and your documentation under CC BY 4.0, as described in the [README](README.md#license).

## Related work

The toolkit's records export to [data-dict](https://data-dict.tidyverse.org/). The open discussion of labelled numbers and typed missing codes there is [tidyverse/data-dict#9](https://github.com/tidyverse/data-dict/issues/9), and a first proposal for labels on number columns is [tidyverse/data-dict#268](https://github.com/tidyverse/data-dict/pull/268).

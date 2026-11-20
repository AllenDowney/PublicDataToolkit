# Task 74 — "About" and "Using this site" pages on every dataset site

**Status:** `DONE (purple)`, 2026-11-20. Assigned by the coordinator and approved by Allen. Red's Task 73 is the toolkit's own site.

**Files:**
- [`lib/pdt/vocab.py`](../../lib/pdt/vocab.py) (new): the standard's vocabularies.
- `lib/pdt/site.py`: the two pages, the nav and the footer.
- `lib/pdt/views.py`: `vocab.py` added to `GENERATOR_MODULES`.
- `lib/pdt/cli.py`: `pdt views --toolkit-url`.
- Tests: [`lib/tests/test_vocab.py`](../../lib/tests/test_vocab.py) and [`lib/tests/test_site_about.py`](../../lib/tests/test_site_about.py).

## What every dataset site now has

| Page | Content |
|---|---|
| `docs/about.html` | What the repository is. What it isn't: the publisher's site, the data, or analysis decisions. The terms notice, prominent, with the publisher's terms, the decisions and the license. How to cite the data and the metadata. The three forms (site, records, agent/). A link to the toolkit. How to report an error in the publisher's documentation or in the records. The repo's `AGENT_NOTES.md`, when it has one, as "Notes". |
| `docs/using.html` | How to find a variable and read its page, section by section. The origins, the kinds of code, the missing types, the link relations and the completeness labels, each table with its counts in this repository. Spans and changes across releases. Availability by wave and form. Getting the data, which follows `terms.data` and mentions `scripts/extract.py` only where it exists. The value and `__code` columns, `pdt.data.rebuild` and `pdt.common_format`. The records from Python (`Repo`, `Index`, `search`) and `pdt search`. The agent views with an LLM. |
| Every page | About and Using this site in the nav. In the footer, the terms notice verbatim, or the terms URL when there's no notice, and "not by the publisher". |

## Decisions

- **The vocabularies:** STANDARD.md isn't installed with the library, so `pdt.vocab` copies its tables verbatim: origins (§3), missing types (§4.2), completeness labels (§7) and link relations (§5). `test_vocab.py` parses STANDARD.md and the schemas' enums and fails if they differ. The meanings of the three kinds of code (valid, missing, unresolved) are §4.2's prose, so the test checks only their names.
- **URLs:** the toolkit URL defaults to `vocab.TOOLKIT_URL`, and `pdt views --toolkit-url` overrides it. The repo's URL comes from its git remote, as in the DAAF export. Without one, "report an error" names the repository's issue tracker by name.
- **`AGENT_NOTES.md`:** a small markdown renderer (`md_blocks`) handles headings, nested lists, fenced code, `code`, bold, italics and links, with no dependency.
- **Regeneration:** `vocab.py` is in `GENERATOR_MODULES`, so C8 asks every repo to regenerate its views.

## Result

- **pytest:** HEAD plus these changes gives 339 passed, 4 skipped. The working tree also has someone's uncommitted `release.py` changes, which fail 19 tests. They aren't part of this task.
- **Checked in a headless browser:** the About and Using pages for pdt-nhis, and About with Notes for pdt-nlsy97.

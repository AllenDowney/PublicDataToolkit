# Task 66 — Two data-dict PRs: integer enums and typed missing codes

**Status:** `DOING (red)`

On [tidyverse/data-dict#9](https://github.com/tidyverse/data-dict/issues/9), Hadley replied to our comment ([7042301177](https://github.com/tidyverse/data-dict/issues/9#issuecomment-7042301177)): "Make sense! I'd be happy to review a PR with the details." The comment asked for two separable capabilities:

1. integer enums with labels, and whether the codes are nominal, ordinal or quantities;
2. typed missing codes: a variable's missing codes, each with a label and one or more types from a shared vocabulary.

This task:
1. Clone tidyverse/data-dict into `~/data-dict` (no fork). Read AGENTS.md, README.md, `schema.yaml`, `schema-field.yaml`, the Rust code that validates enums, the site docs, issue #9 (including nathanj3's proposal) and any contributing notes. Find how it's built and tested.
2. Write the plan here: one PR or two, the exact spec changes (YAML, with abany, polviews and age as examples), the validator changes, tests, docs, and how `lib/pdt/export.py` would use them. Keep it consistent with what we posted, and don't insist on our parquet layout.
3. Stop and report. Nothing is forked, pushed or opened; that's outward-facing, and Allen approves it.

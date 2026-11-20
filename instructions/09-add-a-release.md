# Step 9. Add a release to an existing dataset repo

**Goal:** a new release (a new cycle, year or wave file) is in the repo, built the same way as the others, linked to the one before it, with its data written and `pdt check` passing, without changing what the earlier releases say.

**Standard:** §2.1 (releases and tables), §2.2 (sources), §4 (records), §5.2 (links), §5.3 (corrections), §8 (the common format).

Written from extending pdt-nsfg from two releases to ten ([Task 75](../planning/tasks/task-75.md)), for the next NSFG release ([Task 76](../planning/tasks/task-76.md)).

## Do

1. **Find what the publisher released**, and what changed: the data files, the documentation (codebook, setup programs, dictionaries), and any notes on changes ("summary of questionnaire changes", release notes, errata). Record anything the publisher says changed; those statements become links (step 6).
2. **Fetch the files unchanged**, into `data/raw/` with the others, and add each to `sources.yaml`:
   - `url`, `path`, `releases`, `fetched_on`, `sha256`, `bytes`;
   - `redistribution` as the terms already decided say;
   - `convert` for a PDF read as text.

   A file that needs explaining gets a `note`. Examples: the 1982 NSFG file mixes record types; 1988's has no line breaks.
3. **Add the release to `dataset.yaml`:**
   - `id` as the publisher names it;
   - `label`, `status`, `sources`;
   - `tables` with `key` and `references`;
   - `design` (weights, strata, PSU), with a note when something isn't in the slice yet.

   Then add the same variables to the build's slice spec. Use the names **as this release spells them** (2022-2023's `mar1diss` is lower case), and add a measure for any new name.
4. **Parse its documentation the way the repo already does.** If the publisher's format changed, add a parser for the new one beside the old (pdt-nsfg has three: NCHS codebooks, ICPSR section codebooks, SAS setup programs). Don't change how earlier releases are parsed unless they're wrong. Check the new parser on the whole file, not just the slice: how many variables it finds, and how many have labels and value labels.
   - **Read commented-out statements.** Publishers ship parts of a program commented out; 2015-2017's PROC FORMAT and FORMAT statements are inside `/* */`, and they still hold the value labels.
   - **Check every column position against the data** when the documentation gives positions. 1982's setup gives F22_1CM as 622-628, overlapping the variable before it; the data has it in 625-628. Fix the layout in the slice spec, with the evidence in a comment and in the record's notes, and consider reporting it.
5. **Build, and read the report:**
   - **Unresolved codes:** if most are values of a continuous variable that the documentation labels only at its special codes (dates, weights), the build is misreading them. Treat unlabeled values of a quantity as values, with the range from the data (origin data_file). If they're codes of a categorical variable, they stay unresolved. In 2002, NCHS's setup programs don't define 8 and 9 (refused, don't know) for some variables.
   - **Blanks:** when the documentation doesn't say what a blank means, record it as unresolved, and classify it with an `inferred` correction only when the publisher says what it means elsewhere (the NSFG labels "." INAPPLICABLE in 2002 and 2017-2019).
   - **Counts:** where the documentation prints them, they must match the data; a mismatch is a parsing error until shown otherwise. Where it prints none, availability comes from the data, labeled so.
6. **Link it to the previous release:**
   - the publisher's statements first (`origin: publisher`, with the quote);
   - then the repo's rule for identical documentation;
   - `pdt diff OLD NEW` as a cross-check.

   Expect few rule links where the two releases' documentation differs in kind: 2015-2017's setup program has labels only, 2017-2019's codebook has question text and universes, so the rule links none of them. Don't relax the rule to get links. Leave them unlinked and say why in the task file.
7. **Keep analysis choices out.** A user's own recodes (harmonizing codes across cycles, dividing by 10, guessing a degree from years of school) aren't facts about the release. They aren't records, links or corrections; note them for the user's project.
8. **Write the data:** `make data` under the memory cap (`systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 --quiet ...`). Check that every table's round trip is exact and its row count matches the publisher's sample size.
9. **Regenerate the views and check:** `make views`, `make check`. Read the warnings as well as the failures.
10. **Update the README** (the release list, what documentation each release has) and the task file, then commit by path. If the repo is public, a person reviews and pushes.

## Check before moving on

- [ ] The earlier releases' records are unchanged, except where the new release taught you they were wrong, and that change is described.
- [ ] Every new file is in `sources.yaml` with its checksum; every new table has a key.
- [ ] `pdt check`: no failures; unresolved codes explained in the task file.
- [ ] Links to the previous release: the publisher's, then the rule's; the unlinked ones listed with the reason.
- [ ] `make data`: every round trip exact, row counts as the publisher states.

## Stop and ask a person

- When the release changes the terms, or the publisher's terms page changed.
- Before reporting a documentation error to the publisher.
- Before pushing a public repo.

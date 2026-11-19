# Step 1. Survey the dataset

**Goal:** know what you're building before writing any code. That means the publisher, the releases, the files, the documentation and its format, the terms, and any tool that already does the job.

**Standard:** §1 (what a repo is, its name), §2.1 (release ids, tables, dimensions), §8 (terms).

## Do

1. **Name the dataset and the repo.** One repo per dataset across all its releases: `pdt-<dataset-id>`, lowercase, starting with the name people use (`pdt-gss`, `pdt-anes-cdf`). Add a qualifier only to tell apart two products of one study (§1).
2. **List the releases** and choose ids by §2.1: the publisher's own name, lowercased (`7224r3a` from NORC's file name, `20260205` from the ANES version date, `2022-2023` for the NSFG cycle, `2024` for a FARS data year), else the date as `YYYYMMDD`.
3. **List the files in a release.** If there are several data files that share a key (NSFG female/male/pregnancy; FARS accident/vehicle/person/...), the release has **tables** (§2.1). Note each table's key columns, and how the tables refer to each other.
4. **Find every piece of documentation**: codebooks, questionnaires, user guides, release notes, errata pages, crosswalks. Note each one's format, because the format decides the skill:

   | Format | Skill | Example |
   |---|---|---|
   | An existing package with structured metadata | [`from-upstream-package`](../skills/from-upstream-package/SKILL.md) | gssrdoc for the GSS |
   | HTML codebook | [`from-html-codebook`](../skills/from-html-codebook/SKILL.md) | ANES CDF |
   | PDF, or text converted from PDF | [`from-pdf-codebook`](../skills/from-pdf-codebook/SKILL.md) | NSFG codebooks, FARS manual |
   | Labels in the data file | [`from-data-labels`](../skills/from-data-labels/SKILL.md) | every dataset; the cross-check for all the others |
   | Release notes | [`from-release-notes`](../skills/from-release-notes/SKILL.md) | GSS release notes |

5. **Work out what a wave and a form are** for this dataset (`dimensions` in `dataset.yaml`): the GSS's wave is a year and its form a ballot; the ANES has pre and post phases; FARS has data years and no forms; a cross-section like one NSFG cycle has one wave.
6. **Read the terms pages** and record what they say, quoted, with URLs, in a draft for the person. Cover the four questions in §8: may the data, the documentation and the metadata be redistributed, and may the documentation's text be sent to a hosted LLM?
7. **Look for existing tools** (IPUMS, an R or Python package, a data-dictionary site). If one already does what a repo would, say so and stop. If it does part (gssrdoc has the GSS's question text), it may be a source (step 2).

## Check before moving on

- [ ] Release ids follow §2.1, and you know which releases the first build covers.
- [ ] Tables, keys and references are listed for any multi-file release.
- [ ] Every documentation file has a format and a skill.
- [ ] The terms are quoted for a person, and **a person has decided them**. Until then, `dataset.yaml` says `unknown`.

## Stop and ask a person

- **Terms, always.** The decision is theirs, and goes in `dataset.yaml` with `reviewed_by` and `reviewed_on`. Examples of what came up:
  - gssrdoc's MIT license covers its code, not NORC's documentation, so the gssrdoc source takes the GSS terms;
  - NHTSA's manual has a disclaimer and no license;
  - ICPSR's LLM policy may forbid sending MTF codebook text to a hosted model at all.

  If `llm_processing` may not be `allowed`, stop before reading the documentation yourself. The instructions have to work for a person running the parsers then.
- **Sites that block scripts.** electionstudies.org, nhtsa.gov and icpsr.umich.edu all return 403 or a bot check, even to a headless browser. Try a headless browser once. Stop at any bot check: don't try to get around it, for example through an archive. Ask the person to save the pages from their browser. The ANES terms pages were saved this way, to `data/raw/terms/`, and recorded as a source.
- **Logins** (ICPSR): the person downloads, and `sources.yaml` records the manual steps.
- **Whether to build at all**, when an existing tool covers the dataset.

# Skills

Claude Code skills for reading the source formats met so far into PublicDataToolkit records. Each is `skills/<name>/SKILL.md`, with `name` and `description` frontmatter: how to probe the source, the traps the four builds hit, and how to verify against the data. The procedure they fit into is in [`instructions/`](../instructions/).

| Skill | Source | Built from |
|---|---|---|
| [`from-upstream-package`](from-upstream-package/SKILL.md) | a package that redistributes the publisher's metadata | GSS via gssrdoc |
| [`from-html-codebook`](from-html-codebook/SKILL.md) | HTML codebooks | ANES CDF |
| [`from-pdf-codebook`](from-pdf-codebook/SKILL.md) | PDF codebooks and manuals, via `pdftotext -layout` | NSFG codebooks; the FARS manual |
| [`from-data-labels`](from-data-labels/SKILL.md) | Stata, SAS and CSV label columns | all four; the check on every other source |
| [`from-release-notes`](from-release-notes/SKILL.md) | release notes and crosswalks, into links | GSS release notes, R1 to R3a |

**To use them from Claude Code** in a dataset repo, copy or symlink a skill directory into that repo's `.claude/skills/`, or into `~/.claude/skills/`.

**Not written yet**, for want of a real case (plan §6):
- `from-ddi-xml`, for ICPSR's DDI; it waits on MTF;
- `from-open-data-portal`, for Socrata, CKAN and ArcGIS Hub;
- `release-diff`, comparing two releases' records. FARS's code histories (STANDARD.md §5.4) are the first input for it.

**Using a finished repo** isn't a skill here. `pdt views` generates `agent/SKILL.md` in each dataset repo, for example [`pdt-gss/agent/SKILL.md`](../../pdt-gss/agent/SKILL.md), so it stays in step with the library.

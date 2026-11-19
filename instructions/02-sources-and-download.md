# Step 2. Write `dataset.yaml`, `sources.yaml` and the download

**Goal:** every file the repo depends on is listed, fetched or documented, and hashed. The terms are recorded.

**Standard:** §2 (layout), §2.1 (`dataset.yaml`), §2.2 (`sources.yaml`), §8 (terms and data). Schemas: [`schema/dataset.schema.json`](../schema/dataset.schema.json), [`schema/sources.schema.json`](../schema/sources.schema.json).

## Do

1. **Make the repo** next to this one from the template ([`templates/`](../templates/README.md)):

   ```bash
   copier copy /path/to/PublicDataToolkit/templates pdt-<dataset-id>
   ```

   That gives:
   - `dataset.yaml` and `sources.yaml` skeletons, with every term `unknown`;
   - the Makefile targets (`download`, `build`, `views`, `check`) and `scripts/download.py`;
   - README and CLAUDE.md skeletons;
   - `EXTENSIONS.md` and `.gitignore`;
   - a `build/` stub that writes `build/report.md`.

   `pdt check` on the new repo fails only C6, until the first source is fetched (below). Don't commit `metadata/` until a person has decided the terms, because C9 fails while records are tracked and `terms.metadata` is `unknown`.
2. **Fill in `dataset.yaml`:** the id, publisher, the terms the person decided (§8), `dimensions`, and the releases with their tables, keys and references. Example: [`pdt-fars/dataset.yaml`](../../pdt-fars/dataset.yaml) has four tables and two conditional references.
3. **Fill in `sources.yaml`:** one entry for every data file, codebook, questionnaire, release-notes PDF, errata page, terms page and upstream package. Each one gets:
   - `kind`, `format`, `path` (under `data/raw/`), `releases`;
   - `redistribution` (per file; never looser than the dataset's terms);
   - `acquisition`: `automated` with a `url`, or `manual` with `manual_steps` that a stranger could follow;
   - once fetched: `fetched_on`, `bytes`, `sha256`;
   - for an upstream package: `version`, the tag or commit it's pinned to (§2.2).
4. **Fetch what can be fetched** into `data/raw/` and never edit it. Intermediate files (pdftotext output, a JSON conversion) go in `data/interim/`. `make download ARGS=--accept-terms` fetches every automated source in `sources.yaml` and verifies its SHA-256; `ARGS=--check` reports what's present without the network, and manual sources print their steps. It refuses to fetch without `--accept-terms`, so read the terms first. A source that needs a conversion step (pdt-gss's gssrdoc `.rda` to JSON) can keep its own Makefile rule.
5. **Save errata and update pages** as sources too. They're evidence for corrections in step 6. pdt-anes-cdf keeps ANES's "CDF Updates & Errata" page in `data/raw/errata/`.

## Traps from the four builds

- **A URL can be wrong though it looks right.** The NSFG cycle 12 files are under `/NCHS/NSFG/` on the CDC FTP site, not `/Datasets/NSFG/`. Fetch from every URL you record.
- **An upstream package's version is not its release.** gssrdoc 0.8.2 documented GSS Release 2; the repo's data was Release 3a. Record the version, then confirm which release it documents by comparing names and counts with the data (step 3). Say so in `sources.yaml` when they differ.
- **Manual downloads drift.** When a person downloads for you (FARS, MTF), record exactly what they downloaded (file names, page titles, dates) and hash it immediately.
- **Data never goes in git**, whatever the terms. `data/` is ignored.

## Check before moving on

- [ ] `pdt check` passes C1 and C6 for the files written so far: schemas validate, and every fetched source has `fetched_on` and `sha256`.
- [ ] Every file in `data/raw/` is in `sources.yaml`, and every source with `acquisition: automated` was actually fetched from its URL.
- [ ] Terms in `dataset.yaml` were decided by a person, with `reviewed_by` and `reviewed_on`. `unknown` is allowed, but it blocks shipping.

## Stop and ask a person

- Terms, logins and blocked downloads, as in step 1.
- **Which upstream source or version to pin**, when there's a choice. For the GSS: stay on gssrdoc pinned per release, build from NORC's PDFs, or a hybrid. Allen chose the hybrid (plan §10.3). Lay out the options with what each means for the records and what it costs, and recommend one.

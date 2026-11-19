---
name: from-open-data-portal
description: Build PublicDataToolkit records for a table on an open-data portal (Socrata; the same steps fit CKAN and ArcGIS Hub) from the portal's metadata API, its code-list datasets and its own aggregate queries. Covers defining a release for a table that changes daily, columns the portal adds, code lists published as separate datasets, availability without downloading every row, and the traps of leading zeros and dead links.
---

# From an open-data portal

A portal table isn't a survey. It has no questions and no waves, and it changes every day. But the portal describes it in a structured API: every column's name, display name, description and type. Code lists are often their own datasets, and the portal will count rows for you.

Example: Chicago's "Crimes - 2001 to Present" (Socrata `ijzp-q8t2`) in [`pdt-chicago-crimes`](../../../pdt-chicago-crimes/), [`build/build_records.py`](../../../pdt-chicago-crimes/build/build_records.py) ([Task 33](../../planning/tasks/task-33.md)).

## Probe first

1. **The view metadata:** `https://<portal>/api/views/<id>.json`. Read `columns` (`fieldName`, `name`, `description`, `dataTypeName`, `id`), `description`, `attribution`, `license`, `metadata.custom_fields`, and the timestamps `rowsUpdatedAt` and `viewLastModified`. No version history is kept, only these two times.
2. **Which column names the data uses.** The SODA API (`/resource/<id>.csv`) uses `fieldName` (`case_number`). The portal's "Export" uses display names (`Case Number`). Use the API and `fieldName`, and keep the display name as the `label`.
3. **Columns the portal adds.** `:@computed_region_*` columns are boundaries the portal computes for its own maps. They aren't in the API's output or the export. Leave them out, and say so in the build.
4. **Code lists.** Read each column's description for links to other datasets. Chicago's `iucr` says "See the list of IUCR codes at .../d/c7ck-438e", and that list is a dataset of its own, with `active` marking retired codes. Fetch its rows too.
5. **Related views.** Search the catalog: `https://api.us.socrata.com/api/catalog/v1?domains=<portal>&q=<id>`. Per-year datasets ("Crimes - 2024") may be *filtered views* of the same table. Check their `tableId` and `modifyingViewUid`: they move with the main table, so they aren't frozen snapshots.
6. **Change notes.** Search the catalog with `only=story`. Chicago's notes ("Crimes With No Known Location - 9/8/2026") are the only record of data revisions. Their pages render in the browser, but `/api/views/<story id>.json` has the title and description.
7. **Terms.** The portal's license field often says only "See Terms of Use". Find that page and quote it in `dataset.yaml`. A person decides the terms; until then every term is `unknown`, the repo has no remote, and the build stays local (C9).

## Define the release

The table has no versions, so a release is a **dated snapshot**. On one date, fetch the metadata, the code lists, the counts and the rows you need, and record each file's SHA-256. The release id is the date (`20261119`; STANDARD.md §2.1). Put the files under `data/raw/<release>/`, so later snapshots sit beside it. A later download won't match the checksums, because it's a new snapshot.

## Build

- **Records from the metadata,** one per public column. `label` is the display name, and `description` is the column's description, verbatim. Name the rule that maps Socrata types to `storage_type`: `text` is string, `calendar_date` is datetime, and `number` is integer when every value is whole. `checkbox` and `location` have no storage type in the standard, so leave it empty and report it.
- **A code list is a table.** Give it its own table in the release, with `key`, and a `reference` from the column that uses it. `pdt check`'s C12 then tests every code in the data against the list. Also list the codes in that column's `values`. Keep retired codes, and name the rule if the label joins two of the list's fields.
- **Availability without every row.** Ask the portal to count: `$select=year,count(col1) as n_col1,...&$group=year`. One query gives each column's non-null count by year. That's `origin: data_file` with the query as a source. Some column types (`location`) make the query fail with HTTP 500; leave those out.
- **Read the data as text.** Codes have leading zeros (IUCR `0110`, beat `0322`, district `003`). Read every column as a string, then convert by the record's `storage_type`. An empty cell is null; portals have no missing codes.
- **One slice of rows.** The whole table is too big (8 million rows), so fetch one year with `$where=year=2024&$order=id&$limit=...`. Order by the key, so the file is the same if fetched twice on one day.

## Traps we hit

- **The key isn't the obvious one.** `case_number` repeats: homicides have one row per victim. `id` is the key.
- **Columns that start later.** `ward` and `community_area` are about 1% filled in 2001. Availability's `n` shows it.
- **Dead code-list links.** `fbi_code`'s description points to a CPD page that now asks for a sign-in. Leave the values empty and report it (rule 4). Don't take labels from elsewhere without a source.
- **Big queries fail.** Retry with fewer columns before concluding a column can't be counted.

## Verify against the data

- [ ] **Columns (C3):** the metadata's public columns match the CSV header exactly.
- [ ] **Codes (C4, C12):** every code in the data is in the code list. In Chicago's 2024 rows, all 341 IUCR codes used are on the list.
- [ ] **Counts:** the portal's count for the slice's year equals the rows fetched (259,696 for 2024).
- [ ] **Availability (C5):** the file holds one year, so C5 warns about every other year in the records. That's expected until the standard can say a data file is a subset of rows ([Task 33](../../planning/tasks/task-33.md)).

## Stop and ask

Terms: a person decides. Fetching with `pdt download --accept-terms` stands for that person's acceptance, so say who accepted and when. A page that needs a sign-in, or a bot check, goes to a person too.

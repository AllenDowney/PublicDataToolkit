# Task 77 — QA of the published sites

**Status:** `DOING (purple)`; stopped at the wrap-up on 2026-11-20. Assigned by the coordinator: a QA pass over the toolkit site and the 16 dataset sites on GitHub Pages, fixing what's in the generator.

**Tools** (in the session scratchpad; not committed):
- **`crawl_sites.py`:** a breadth-first crawl from each site's home page, one request at a time, 0.2 s apart, with a generic user agent. It checks broken internal links and redirects, the required pages, the terms notice in footers and the search index's paths, and checks each GitHub or toolkit link once.
- **`render_check.py`:** Playwright on the local `docs/` (the same generated HTML) at 1100 and 390 px wide. It checks horizontal overflow and console errors, and whether search returns hits.

## Found and fixed (site.py, with tests)

1. **Links to `NAME@release` pages were broken** on 8 sites: brfss, ces, hints, nhanes, nlsy97, nsfg, pisa and pulse, with 703 such files.
   - A page for a lineage that ends in an older release under a reused name is named `NAME@release`. `file_name()` escaped the `@`, so the file on disk was literally `ADDEPEV2%402016.html`. The link held the same text, which a browser decodes to `ADDEPEV2@2016.html`, a file that doesn't exist. Four files with `!` had the same problem.
   - Fix: file names keep the characters a URL path allows (`PATH_SAFE`: `@!$&'()*+,;=-._~`). `href()` percent-encodes every link, alias redirect and search-index path, so a `%` left in a file name (from an escaped `/` or space) is `%25`, and the browser asks for the file's real name.
   - Test: [`lib/tests/test_site_links.py`](../../lib/tests/test_site_links.py) builds a site with a reused name, a `!` and a `/`. It checks that every href, meta refresh and search-index path, decoded as a browser does, is a file.
2. **About and Using overflowed at phone width** (390 px): a long URL by 12 px and a long `<code>` path by 89 px. Fix: `a, code { overflow-wrap: anywhere; }`.

**Both fixes need `make views` in the repos** (the generator hash changed). Per the coordinator, that's the step before each push.

## Crawl results so far

| Site | Pages | Broken internal links | Footers without the notice | Missing pages | Search index | External links |
|---|---|---|---|---|---|---|
| toolkit | 7 | 0 | (not checked) | — | — | 54 OK; **CultureWar 404**; 8 `blob/` pages 503 |
| anes-cdf | 44 | 0 | 0 | 0 | 39 rows, 0 dead | repo, issues, toolkit OK |
| atus | 667 | 0 | 0 | 0 | 641 rows, 0 dead | OK |

- **CultureWar 404:** the toolkit's home page links to https://github.com/AllenDowney/CultureWar, which returns 404 (presumably private). That's content (`pages/build.py` or its sources), not the dataset sites. It's for the coordinator or red to decide; not changed here.
- **The 503s:** all eight are `github.com/.../blob/main/...` files linked from `guides.html` and `standard.html`. They're probably GitHub throttling HEAD requests to `blob/` pages. Recheck them with GET, slowly, before treating them as broken.
- **anes-cdf and atus show no broken `@` links** because neither has a page with `@` in its name. The 8 sites listed in finding 1 are where the crawl would find them.

## Rendering checks (local docs)

- **anes-cdf and atus:** search finds the first index entry (1 hit each), and there are no console errors. The only overflow is the one fixed above.
- **The other 14 sites weren't checked:** the script stopped at brfss's first `@` page, which is how finding 1 came to light.

## Stopped here

What's left:
1. **Crawl the other 13 live sites:** brfss, ces, chicago-crimes, cps-asec, fars, hints, meps, nhanes, nhis, nlsy97, nsduh, nsfg and yrbss (pisa and pulse are published too), after their views are regenerated with this fix. Command: `python -I crawl_sites.py OUT.json <site> ...`. At 0.2 s a request, hints (1,162 pages) takes about 15 minutes.
2. **Rerun the rendering checks** on all 16 sites; the script needs `unquote` on manifest paths.
3. **Recheck the 8 `blob/` links** with GET, and decide about the CultureWar link.
4. **Check `pages/build.py`** (the toolkit site) against the same list: the footer, and links to repos that aren't public.

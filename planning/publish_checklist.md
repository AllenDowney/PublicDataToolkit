# Publishing checklist

A read-only review (Task 52, 2026-11-20) of what's ready to publish, what to fix first, and the steps in order. Nothing has been pushed, tagged or created. The commands at the end are for Allen to run.

**Allen's decisions (2026-11-20):**
- **Version:** v0.2.0.
- **Licenses:** MIT for code; CC BY 4.0 for our metadata, documents and views; publisher files keep their terms. Committed in 19f0e6e: the toolkit README, `templates/template/LICENSE.jinja`, a License section in the template README, and a copier question `copyright_holder` (default "Allen Downey").
- **NSFG terms:** confirmed, with a notice (pdt-nsfg bc9d6a8, 743bf75; `pdt check` 0 failures).
- **NHIS terms:** decided, everything ships (pdt-nhis 71bbf37, 7837c82; `pdt check` 0 failures).
- **BRFSS:** green is still committing.
- **The final push:** Allen runs it himself, from the clean clone (steps A–D).

## Summary

| Repo | Verdict | Before publishing |
|---|---|---|
| PublicDataToolkit | **Ready once its history is cleaned** | §5 is fixed in the files (a0947e3), but 36 unpushed commits still hold the private version: push a rewritten branch (below); bump the version |
| pdt-gss | **Ready** | Its site needs the Pages workflow added by hand (not made from the template) |
| pdt-anes-cdf | **Ready** | |
| pdt-nsfg | **Ready** | Terms confirmed by Allen (bc9d6a8, 743bf75) |
| pdt-fars | **Ready** | |
| pdt-chicago-crimes | **Ready** | |
| pdt-yrbss | **Ready** | |
| pdt-cps-asec | **Ready** | |
| pdt-pisa | **Ready** | |
| pdt-brfss | **Not ready** | Uncommitted record changes; views stale (C8) |
| pdt-nhis | **Ready** | Terms decided, everything ships (71bbf37, 7837c82); `pdt check` 0 failures, per the coordinator |

**Every dataset repo needs a LICENSE** (decided: MIT for code, CC BY 4.0 for metadata, documents and views):
- **By `copier update` after the v0.2.0 tag** (made from the template; they also get the README's License section): pdt-chicago-crimes, pdt-yrbss, pdt-cps-asec, pdt-pisa, pdt-nhis, and pdt-brfss when it's ready.
- **By hand** (not made from the template): pdt-gss, pdt-anes-cdf, pdt-nsfg, pdt-fars. Render the template's `LICENSE.jinja` with `copyright_holder` "Allen Downey", and add a License section to each README (step 4b). **Done 2026-11-20 for anes-cdf (f13c989), nsfg (c72c70b) and fars (87f5f4e); gss waits for orange's rebuild.**

## The toolkit

164 commits since `origin/main` (63739da), 229 tracked files, pack 91 KB. Checked at HEAD and in every commit message since `origin/main`:

| Check | Result |
|---|---|
| Absolute paths (`/home/...`), session ids, `/tmp/claude` paths, sockets | none |
| Secrets (keys, tokens, passwords) | none (only `tokens_read` counts in `eval/runs`) |
| Files over 500 KB, or large blobs in the new history | none |
| Data files (`.parquet`, `.dta`, `.sas7bdat`, `.csv`, `.zip`, …) | none; `.gitignore` covers them |
| Eval run files with local paths (`config.local.json`, `prompt.local.md`, `log.jsonl`) | not tracked |
| Email addresses | public contacts only: nsfg@cdc.gov, anes-project@umich.edu, icpsr-help@umich.edu, mtfinformation@umich.edu |
| `PROPOSAL.md` | unchanged since `origin/main`; no internal details |
| Commit author | "Allen Downey <downey@allendowney.com>" on all 164; fine if that's the intended public address |

**To fix:**
1. **`planning/data_dict.md` §5.** **Decided and fixed in the files** (a0947e3, by the coordinator): the summary of Hadley's private reply moved to `~/pdt-private/`, and §5 now holds only the public discussion. **But the history still has it:** the private version is one blob (`d1212fb`), present in 36 commits, from 2c4eef0 to just before a0947e3. Pushing `main` as it is would publish it. "Keeping §5 out of the pushed history" below gives the plan, verified on a throwaway clone. `v0.1.0` predates 2c4eef0, so pushing that tag is safe.
2. **The version:** `pyproject.toml` and `lib/pdt/__init__.py` both say 0.1.0. Set them to the release's version before tagging.
3. **Other threads' uncommitted work** (CLAUDE.md, eval/, planning task files at the time of the review): a push sends only commits, but run `git status` first.

## The dataset repos

`pdt check` was run as it will run once a remote is added (`has_remote` patched to True), so C9 fails rather than reports. Other checks: tracked files against each source's `redistribution`, tracked data-like files, size, NOTICE.

| Repo | Commits | Tracked | `pdt check` with a remote | Terms (data, documentation, metadata, llm) | Notes |
|---|---|---|---|---|---|
| pdt-gss | 23 | 1,938 files, 120 MB (19.5 MB packed) | 0 failures | ship, ship, ship, allowed | `NOTICE.md` (NORC's notice). `docs/` gitignored (7,605 files, built for Pages). The largest files are `metadata/releases/*/variables.jsonl` (21 and 19 MB) and the data-dict exports (8 MB each): under GitHub's 100 MB limit, though GitHub warns above 50 MB |
| pdt-anes-cdf | 29 | 74 files, 0.6 MB | 0 failures | ship, ship, ship, allowed | 3 sources `unknown` (saved terms and errata pages under `data/`): not tracked, not packaged |
| pdt-nsfg | 34 | 153 files, 1.1 MB | 0 failures | ship, ship, ship, allowed | Terms summary: "recorded here from that review, pending his confirmation for this repo" (reviewed 2026-11-10, for MarriageNSFG) |
| pdt-fars | 27 | 112 files, 1.4 MB | 0 failures | ship, ship, ship, allowed | |
| pdt-chicago-crimes | 6 | 62 files, 0.5 MB | 0 failures | ship, ship, ship, allowed | City of Chicago notice in `terms.notice` |
| pdt-yrbss | 8 | 127 files, 0.7 MB | 0 failures | ship, ship, ship, allowed | CDC notice in `terms.notice` |
| pdt-cps-asec | 8 | 171 files, 1.6 MB | 0 failures | ship, ship, ship, allowed | Census notice in `terms.notice` |
| pdt-pisa | 4 | 315 files, 2.9 MB | 0 failures | ship, ship, ship, allowed | OECD notice in `terms.notice` |
| pdt-brfss | 1 | 615 files, 3.5 MB | 3 failures (C8: agent/, docs/, export/ out of date) | ship, ship, ship, allowed | Uncommitted: `build/`, `metadata/releases/2011/` (green's work in progress) |
| pdt-nhis | 2 | 12 files | 2 failures (C8: no views) | unknown × 4 | Uncommitted `dataset.yaml`, `sources.yaml` (yellow's work in progress) |

Common to all: no microdata tracked, no tracked file whose source isn't `ship`, and README sections pass C11. All ten have `standard_version: 0.1`. None has a remote yet.

## What v0.1.1 should contain

Everything committed since `v0.1.0` (5d0a992), 116 commits:
- **New modules:** `catalog`, `chains`, `common_format`, `compare`, `diff`, `extract`.
- **Larger changes:**
  - one site page per variable across releases;
  - `agent/variables.txt`;
  - C8 complete;
  - `pdt download` with `convert` and live sources;
  - `pdt package`;
  - the `data` extra.
- **Schemas:** `code_list` is new; there are new optional fields (`values[].n`, `questions[].number`, `flag_for`, `implied_decimals`, `reference_period`, `lists_only_occurring_codes`, `convert`, `live`, `kind`, `data_waves`, `revisions`, …).
- **Template:** the Pages workflow, and `VIEWS_ARGS`.

**Version: v0.2.0** (decided). STANDARD.md §2.4 makes additive changes a minor bump, and the template and schemas gained files; the license files (19f0e6e) are part of it. `standard_version: 0.1` in the dataset repos stays valid either way, because nothing is required that wasn't before.

## Keeping §5 out of the pushed history

**Plan:** push a rewritten copy of the unpushed commits from a separate clone. In every commit since `origin/main` (63739da), three files are cleaned:
- `planning/data_dict.md`: where it's the private blob `d1212fb`, it's replaced by the cleaned file `e9614a3` (after a0947e3);
- `planning/publish_checklist.md` and `planning/tasks/task-48.md`: every version goes through a sed script that removes what they quoted or reported from the private reply. The checklist used to quote the reply's phrases as grep patterns; task-48 reported an offer from it. The phrases and the script are outside the repo: `~/pdt-private/publish_phrases.txt` and `~/pdt-private/publish_clean.sed`.

Nothing else changes: the same commits, messages, authors and dates. The working repo's files were cleaned the same way before the snapshot, so the final tree is the same too. The real `main` isn't rewritten until other threads are paused (step D).

**Done (2026-11-20, red), in `~/pdt-publish`:** steps A and B were run at a snapshot taken after the version-0.2.0 commit and this cleanup. The snapshot and the `publish` SHAs are in `~/pdt-publish/.git/SNAPSHOT` and in the report to the coordinator. Step C is Allen's.

**A. Make the rewritten branch** in a fresh clone (not the working repo). The filter is `~/pdt-private/publish_filter.sh`:

```bash
cd ~ && rm -rf pdt-publish && git clone --no-hardlinks ~/PublicDataToolkit pdt-publish && cd pdt-publish
SNAP=$(git rev-parse HEAD); echo $SNAP > .git/SNAPSHOT     # step D needs it
git branch publish $SNAP
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f --index-filter "sh ~/pdt-private/publish_filter.sh" -- 63739da..publish
```

If `planning/data_dict.md` changes again before this is run, check that `CLEAN` in the filter is still the blob you want: `git rev-parse HEAD:planning/data_dict.md`.

**B. Verify before pushing** (each line must print as shown):

```bash
SNAP=$(cat .git/SNAPSHOT)
git diff --quiet publish $SNAP && echo "trees identical"
[ "$(git rev-list --count 63739da..publish)" = "$(git rev-list --count 63739da..$SNAP)" ] && echo "same commit count"
diff <(git log --format='%an|%ae|%ad|%B' $SNAP) <(git log --format='%an|%ae|%ad|%B' publish) && echo "same messages, authors, dates"
git log -p 63739da..publish | grep -c -f ~/pdt-private/publish_phrases.txt          # 0, in any file of any commit
git rev-list --objects 63739da..publish | grep -c d1212fb34722a05724a179709dc58a24fe039e6d   # 0
```

**C. Turn on Pages, then push from the clone, and tag on the rewritten history** (Allen). Pages comes first, so the workflow's first run can deploy:

```bash
gh api -X POST repos/AllenDowney/PublicDataToolkit/pages -f build_type=workflow     # Pages source: GitHub Actions
cd ~/pdt-publish
git remote set-url origin git@github.com:AllenDowney/PublicDataToolkit.git
git fetch origin
git merge-base --is-ancestor origin/main publish && echo "fast-forward"             # must print
git push origin publish:main
git tag -a v0.2.0 publish -m "PublicDataToolkit 0.2.0"
git push origin v0.1.0 v0.2.0
gh run list --repo AllenDowney/PublicDataToolkit --workflow pages.yml --limit 1      # then https://allendowney.github.io/PublicDataToolkit/
```

**D. Bring the working repo onto the published history,** with the other threads paused. Their commits since the snapshot are replayed unchanged on top. The trees at the snapshot are identical, so there are no conflicts:

```bash
cd ~/PublicDataToolkit
git status                                                # other threads paused; their uncommitted edits are stashed and restored
git fetch origin --tags
SNAP=$(cat ~/pdt-publish/.git/SNAPSHOT)
git rebase --autostash --onto origin/main $SNAP main
git log --oneline origin/main..main                       # only the commits made after the snapshot
git rev-list --objects main | grep -c d1212fb34722a05724a179709dc58a24fe039e6d   # 0
git push origin main                                      # a fast-forward now
rm -rf ~/pdt-publish
```

Until step D, a plain `git push` from `~/PublicDataToolkit` is refused as non-fast-forward, which is a useful guard. Don't force it. The original commits stay in the working repo's reflog, which is never pushed.

**E. The pilot dataset repos: pdt-nsfg, pdt-fars, pdt-anes-cdf** (after C). Each commits `docs/`, so Pages serves `main:/docs`. A dataset site's links to its repository and issues come from the git remote, so the views are regenerated after the remote is added and before the push. The toolkit link on each site's About page is the toolkit's GitHub repo (`pdt.vocab.TOOLKIT_URL`), which is right once C is done:

```bash
for r in nsfg fars anes-cdf; do
  ( cd ~/pdt-$r && git status --short && \
    gh repo create AllenDowney/pdt-$r --public --source . --remote origin \
       --description "$(python -c 'import yaml; print(yaml.safe_load(open("dataset.yaml"))["title"])'): metadata, built with PublicDataToolkit" && \
    gh repo edit AllenDowney/pdt-$r --add-topic publicdatatoolkit && \
    make views && make check && \
    git add agent docs export && git commit -m "Views with the repository's URL" ; \
    git push -u origin main && \
    gh api -X POST repos/AllenDowney/pdt-$r/pages -f "source[branch]=main" -f "source[path]=/docs" )
done
```

`make check` must print 0 failures before the push (C9 now runs as for a published repo; all three have terms ship). Then add each repo to the toolkit's Datasets page, in `pages/datasets.yaml`: `repo: https://github.com/AllenDowney/pdt-<id>` and `site: https://allendowney.github.io/pdt-<id>/`, commit and push the toolkit.

## The steps, in order

Run from a shell with `gh` logged in as AllenDowney. Replace `0.2.0` with the version chosen above.

**1. Version the toolkit** (§5 is fixed in the files; its history is handled by "Keeping §5 out of the pushed history" above, which replaces step 2):

```bash
cd ~/PublicDataToolkit
git status                      # nothing half-done that should be in the release
sed -i 's/^version = "0.1.0"/version = "0.2.0"/' pyproject.toml
sed -i 's/^__version__ = "0.1.0"/__version__ = "0.2.0"/' lib/pdt/__init__.py
python -m pytest -q lib/tests
git commit -m "Version 0.2.0" -- pyproject.toml lib/pdt/__init__.py
```

**2. Push the toolkit and its tags:** steps A–D above, not `git push origin main` from the working repo. `v0.1.0` is local only and predates the private commits; template-made repos record it in `.copier-answers.yml`, so push it too.

**3. Regenerate the views with the new version** in each ready repo. C8 only reports a version difference, but the headers should name the release:

```bash
for r in gss anes-cdf nsfg fars chicago-crimes yrbss cps-asec pisa; do
  (cd ~/pdt-$r && make views && make check && git add agent export docs 2>/dev/null; \
   git commit -m "Regenerate views with pdt 0.2.0" -- agent export docs)
done
```

**4. Template-made repos: bring the template forward** (adds `.github/workflows/pages.yml` and the `VIEWS_ARGS` Makefile line). Review each diff before committing:

```bash
for r in chicago-crimes yrbss cps-asec pisa nhis; do (cd ~/pdt-$r && copier update --vcs-ref v0.2.0 && git status); done
```

**4b. LICENSE in the four repos not made from the template.** **Done locally (2026-11-20, red) for pdt-anes-cdf (f13c989), pdt-nsfg (c72c70b) and pdt-fars (87f5f4e):** LICENSE rendered with "Allen Downey", the template's License section appended to each README, `pdt views` and `pdt check` run (0 failures; the views didn't change), committed, not pushed. **Still to do: pdt-gss**, after orange commits its rebuild:

```bash
for r in gss; do
  sed 's/{{ copyright_holder }}/Allen Downey/' ~/PublicDataToolkit/templates/template/LICENSE.jinja > ~/pdt-$r/LICENSE
  # add the README's License section by hand, as in templates/template/README.md.jinja
  (cd ~/pdt-$r && git add LICENSE && git commit -m "LICENSE: MIT for code, CC BY 4.0 for metadata and views" -- LICENSE)
done
```

**5. The GSS's site.** `docs/` is gitignored and the GSS wasn't made from the template, so copy the workflow and pin the tag in it. In the copy, replace the "Read the toolkit version" step with a fixed `ref: v0.2.0`:

```bash
mkdir -p ~/pdt-gss/.github/workflows
cp ~/PublicDataToolkit/templates/template/.github/workflows/pages.yml ~/pdt-gss/.github/workflows/
# edit: ref: v0.2.0 instead of ${{ steps.toolkit.outputs.tag }}, and drop the step that reads it
```

The GSS Makefile's `views` target needs `$(VIEWS_ARGS)` too (one line, as in the template).

**6. Create each GitHub repo, add the remote, check, and push.** `pdt check` now runs with a remote, so C9 fails rather than reports:

```bash
for r in gss anes-cdf nsfg fars chicago-crimes yrbss cps-asec pisa; do
  (cd ~/pdt-$r && gh repo create AllenDowney/pdt-$r --public --source . --remote origin \
     && make check && git push -u origin main)
done
```

**7. Turn on Pages.**
- **Repos that commit `docs/`** (all except the GSS): Settings > Pages > Source "Deploy from a branch", `main`, `/docs`. Or:

  ```bash
  for r in anes-cdf nsfg fars chicago-crimes yrbss cps-asec pisa; do
    gh api -X POST repos/AllenDowney/pdt-$r/pages -f "source[branch]=main" -f "source[path]=/docs"
  done
  ```

- **The GSS:** Source "GitHub Actions" (`gh api -X POST repos/AllenDowney/pdt-gss/pages -f build_type=workflow`). Its workflow then builds and deploys `docs/` on each push.

**8. Data releases** (terms ship for every ready repo). `make data` writes the common-format files, and `pdt package` refuses anything that isn't ship. Then upload, and record the release in `dataset.yaml`'s `data_release`:

```bash
for r in gss anes-cdf nsfg fars chicago-crimes yrbss cps-asec pisa; do
  (cd ~/pdt-$r && make data && python -m pdt package . \
     && gh release create data-2026-11-20 data/release/$r-data/* \
          --repo AllenDowney/pdt-$r --title "Data, 2026-11-20" \
          --notes "Publisher files and the common-format parquet files; SHA256SUMS included.")
done
```

The `make data` and `pdt package` targets exist in nsfg, anes-cdf and the template-made repos. In gss and fars, run `python scripts/build_data.py` and `python -m pdt package .`.

**9. Later:** pdt-brfss once green commits and its views are current (C8).

The loops in steps 3, 6, 7 and 8 list the ready repos as of 2026-11-19. Add `nhis` to each, now that its terms are decided.

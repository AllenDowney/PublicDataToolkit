# Task 52 — Pre-publish review

**Status:** `DONE (red)` (see "Resumed 2026-11-20" below)

Read only. Allen will soon push the toolkit (unpushed since 63739da) and some dataset repos, and tag v0.1.1. The result is [`planning/publish_checklist.md`](../publish_checklist.md):

a. **The toolkit:** everything committed since `origin/main`. Flag anything that shouldn't be public: personal details, private emails or drafts (correspondence lives in `~/pdt-private`), internal session ids, absolute paths under `/home`, secrets, large files, microdata. `PROPOSAL.md` must stay free of internal details. List what to fix.
b. **Each dataset repo** (gss, anes-cdf, nsfg, fars, chicago-crimes, yrbss, cps-asec, and brfss, pisa, nhis when done):
   - terms decided and consistent (`dataset.yaml`, `sources.yaml`, README, notice);
   - no build-only or unknown files tracked, and no microdata;
   - repo size;
   - README sections (§2.3);
   - `pdt check` as it would run with a remote (C9 failing, not just reported).

   One ready / not ready line per repo, with reasons.
c. **What v0.1.1 should contain,** and the steps to publish in order (push the toolkit and the tag, create the GitHub repos, push, enable Pages, create data releases with `pdt package`), as commands Allen can run. Run nothing that publishes.

**Files:** `planning/publish_checklist.md`, this file. Nothing else changes.

## Stopped here (2026-11-19, Allen leaving to travel)

**Done (part a, the toolkit), read only; nothing changed:**
- 164 commits since `origin/main` (63739da), all authored "Allen Downey <downey@allendowney.com>"; 229 tracked files; pack size 91 KB.
- **Clean:** no absolute `/home` paths, no session ids, sockets or `/tmp/claude` paths in tracked files or commit messages; no secrets (only `tokens_read` counts in `eval/runs`); no file over 500 KB at HEAD and no large blob in the history since `origin/main`; no data files (`.gitignore` covers them). The eval runs' `config.local.json`, `prompt.local.md` and `log.jsonl`, which do hold local paths and session scratchpad paths, are not tracked. Email addresses in the repo are public contacts only (nsfg@cdc.gov, anes-project@umich.edu, icpsr-help@umich.edu, mtfinformation@umich.edu). `PROPOSAL.md` is unchanged since `origin/main` and has no internal details.
- **Must fix before pushing:** `planning/data_dict.md` §5, "Hadley's answers (2026-11-19)" (added in 2c4eef0, not yet public), summarizes Hadley Wickham's private reply to Allen in detail. Either get Hadley's agreement, or move §5 to `~/pdt-private/` and keep in the repo only what's public (the GitHub issues #9 and #196 and our own conclusions). `planning/tasks/task-06.md` line 19 points to it.
- **Note for Allen:** commits carry downey@allendowney.com as author; fine if that's the intended public address.
- **Before pushing:** other threads have uncommitted work in the toolkit (CLAUDE.md, eval/, planning/tasks/task-30.md at the time of the review). A push sends only commits, but check `git status` first so nothing half-done is expected to be in.

**Not done:**
- **Part (b), the dataset repos.** A read-only script was written and stopped before finishing. It lives in the red session's scratchpad (`prepublish.py`) and may be gone after a reboot. Per repo, it records: commits, remote, uncommitted files, tracked file count and size, the largest tracked files, tracked data-like files, `terms` (data, documentation, metadata, llm_processing, reviewed_by, notice), tracked files whose source isn't `ship`, NOTICE and README, whether `docs/` is gitignored, and `pdt check` with `check.has_remote` patched to return True, so C9 fails rather than reports. It should run on gss, anes-cdf, nsfg, fars, chicago-crimes, yrbss, cps-asec, brfss, pisa and nhis. The GSS takes several minutes; run it in the background.
- **Part (c),** v0.1.1's contents and the publishing commands.
- **`planning/publish_checklist.md`** isn't written yet.

**Next step:** rerun the script per repo, write `planning/publish_checklist.md` (one ready / not ready line per repo; the toolkit fix above; the v0.1.1 contents; the commands in order: fix §5, push the toolkit, tag and push v0.1.1, create each GitHub repo, add the remote, run `pdt check` (C9 now fails rather than reports), push, set Pages source to GitHub Actions, run `pdt package` and `gh release create` per ship repo). Run nothing that publishes.

## Resumed 2026-11-20: done

**Status:** `DONE (red)`. Everything is in [`planning/publish_checklist.md`](../publish_checklist.md). Nothing was pushed, tagged or created, and no repo was changed.

**Part (b), the dataset repos** (read-only script; `pdt check` with `has_remote` patched to True):

| Repo | Verdict |
|---|---|
| gss | ready: 0 failures; 120 MB tracked (19.5 MB packed); `docs/` gitignored, so its Pages workflow must be added by hand |
| anes-cdf, fars, chicago-crimes, yrbss, cps-asec, pisa | ready: 0 failures |
| nsfg | ready once Allen confirms its terms (the summary says "pending his confirmation for this repo") |
| brfss | not ready: uncommitted record changes, so C8 fails |
| nhis | not ready: terms `unknown`, no views |

None of the repos has a LICENSE (a decision for Allen), and none has the Pages workflow yet: it came after `v0.1.0`, and `copier update` brings it to the template-made repos.

**Part (c):**
- **v0.1.1's contents:** 116 commits since `v0.1.0`. STANDARD.md §2.4 would call this a minor bump (0.2.0), because the schemas gained a file and new optional fields; I recommend v0.2.0. `pyproject.toml` and `__version__` still say 0.1.0.
- **Publishing commands,** in order, in the checklist.

**§5's history** (after the coordinator's a0947e3): the private version is one blob of `planning/data_dict.md` (`d1212fb`), in 36 unpushed commits. The plan, in the checklist, rewrites a copy of the unpushed history in a separate clone, replacing that blob with the cleaned file. It was verified on a throwaway clone:
- the same 177 commits, messages and authors;
- an identical final tree;
- none of the reply's phrases in any commit;
- the private blob unreachable from the branch to push.

Allen pushes that branch. The working repo is then rebased onto it, with the threads paused. `v0.1.0` predates the private commits.

**Item 3** (the GSS search returning both releases) was handed to blue by the coordinator. The measurements went to blue: every GSS search doubles, e.g. the Religion subject gives 810 rows (~21.7k tokens) against 405 for 7224r3a alone.

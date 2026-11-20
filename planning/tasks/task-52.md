# Task 52 — Pre-publish review

**Status:** `DOING (red)`

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

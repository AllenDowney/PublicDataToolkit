# Task 65 — An NLSY slice

**Status:** `DOING (yellow)` — started 2026-11-20 by the thread "yellow".

The National Longitudinal Surveys of Youth 1979 or 1997 (BLS) in `~/pdt-nlsy`: a small panel extract, the first test of a panel's rounds as waves. Data come through BLS's Investigator tool, so the sources are probably manual. Record the terms for Allen. Memory cap applies. The coordinator: stop at any login and say what it needs.

**Files:** `~/pdt-nlsy/` (new, no remote); this file; the Task 65 block on the board.

## Progress

### 2026-11-20: access, without a login

- **Cohort:** NLSY97 (born 1980–84; rounds 1–21, 1997–2023).
- **The NLS Investigator** (https://www.nlsinfo.org/investigator/) doesn't need a login: "It is not necessary to get an account to browse data, but an account is necessary to save datasets online" (https://www.nlsinfo.org/content/getting-started/accessing-data).
  - But its pages and scripts return 403 to anything that isn't a browser session.
  - Its System Use Notification (https://www.nlsinfo.org/system-use-notification) says "Any attempt to exceed these limitations or gain additional functionality is prohibited" and cites the Computer Fraud and Abuse Act.
  - So I didn't script it. Its "Downloads" page only lists extracts a user has built.
- **Whole-cohort downloads** are published as direct links on https://www.nlsinfo.org/content/access-data-investigator/accessing-data-cohorts, for "users who have the capacity to utilize extremely large data files". Each zip has the data (.dat and .csv), a codebook (.cdb), SAS and R read programs, and a tagset of reference numbers.
  - NLSY97: https://nlsinfo.org/cohort-data/nlsy97_all_1997-2023.zip (475 MB, updated 2026-01-23 per Last-Modified);
  - NLSY79: nlsy79_all_1979-2022.zip (450 MB).
  - curl fetches them with no login. This slice uses the NLSY97 file, read in batches under the memory cap.
- **Terms, for Allen:**
  - NLS public data are free. The citation page (https://www.nlsinfo.org/bibliography/citing-nls-data) gives "Bureau of Labor Statistics, U.S. Department of Labor. National Longitudinal Survey of Youth 1997 cohort, 1997-2023 (rounds 1-21). Produced and distributed by the Center for Human Resource Research (CHRR), The Ohio State University. Columbus, OH: …".
  - No redistribution statement found yet. Terms stay `unknown`.
- `~/pdt-nlsy` was created from the template (7d8196f). Release `1997-2023`; the wave is the round.

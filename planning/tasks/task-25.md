# Task 25 — Standard changes from the findings

Moved from [`PROJECT_BOARD.md`](../../PROJECT_BOARD.md) on 2026-11-19. The board has the current status; this file holds the task's description, progress, findings and decisions.


**Status:** `DONE` (2026-11-19) — main thread

Findings that need a decision or a change to STANDARD.md and the schemas:
- **A definition field:** FARS and data-dict both have one; FARS definitions are in `notes` for now.
- **Variable type** (raw, recode, computed, imputation flag), now the NSFG extension `nsfg.variable_type`.
- **Publisher corrections printed in the documentation,** such as NSFG's margin box.
- **Missing types for non-surveys:** "Unknown" in a police report isn't "don't know".
- **"Missing, reason unknown":** GSS `.z`.
- **Rules for release ids.**
- **The size of per-code provenance.**
- **Systemic source artifacts fixed by a named rule:** gssrdoc's doubled apostrophes.
- **Conditional references between tables:** a FARS person's `VEH_NO` refers to a vehicle in transport, a parked vehicle, or nothing (non-motorists).
- **Histories inside one label:** FARS writes "Unknown/Reported as Unknown (Since 2018)" for a code whose meaning changed. The record for a single year should probably say only what that year means.

**Files:** `STANDARD.md`, `schema/`, and the `lib/` code that enforces them.

**Decided (2026-11-19):**
- **Publisher subject lists are groups,** of kind `subject` (STANDARD.md §5.1). Proposed by the views thread (Task 14), with Allen's approval of the direction. The main thread chose groups over "complete-capable annotations", so the rule stays simple: annotations never support completeness, and publisher groups can. `pdt-gss` now emits gssrdoc's subjects as `subject` groups instead of annotations.
- **Headers for generated JSONL** (§7): the first line is a `{"shard": {...}}` object, and `agent/manifest.json` holds the input hashes. This was the views thread's convention.
- **The rest, decided 2026-11-19.** Allen chose the first three; the main thread decided the others. All are in STANDARD.md, the schemas, `pdt check` (68 library tests) and the dataset repos.
  - **Missing types:** new `unknown`, for administrative and coded data such as FARS's "Reported as Unknown", and `unspecified`, for codes marked missing without a reason, such as GSS `.z`. The FARS and GSS rules went to version 0.2.
  - **Corrections the publisher prints** go in the field, with the superseded text in `notes`: NSFG `MFLASTP`'s universe.
  - **Conditional references:** a reference may have `when: {column, in}`. FARS declares person → vehicle when `PER_TYP` is 1, 2 or 9; that holds for all 78,880 such rows.
  - **`description`** holds the publisher's definition (FARS).
  - **`variable_type`:** response, recode, computed, imputation_flag, weight, design, administrative or other. The NSFG maps its types by the rule `nsfg_variable_type`, and the extension is gone.
  - **Release ids** use the publisher's own name for the release, lowercased; otherwise the date (`YYYYMMDD`).
  - **Systemic source artifacts** may be fixed by a named, versioned rule (rule 3).
  - **`provenance.codes`** is a default origin for a record's missing codes; `pdt check` requires that each code has one or the other. The GSS uses it, and its records are 13% smaller.
  - **One release's labels:** a record uses the release-specific label when a source gives one. FARS now takes labels from the 2024 CSV.
  - **Views thread's questions:**
    - shards may use a compact JSONL form, while `metadata/` stays canonical;
    - `description` exists now, so the line form can use it;
    - when two filters return the same set, report the stronger label (§7).

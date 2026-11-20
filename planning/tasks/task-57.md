# Task 57 — Design: topic annotation vs. belief-module groups

**Status:** `DOING (blue)`. The design is written and waits for the coordinator's review. Nothing is built.

Assigned by the coordinator on 2026-11-20, after Task 53: design the §7.5 comparison of a religion topic annotation versus belief-module groups, and how to measure it. Don't build it until the design has been read.

**The design:** [`planning/topic_annotation_design.md`](../topic_annotation_design.md).

**Findings:**
- **Modules don't help religion.** Of the 242 GSS hits, the religion modules cover 143, all already in the publisher's subject "Religion" (205), and they add 64 variables outside the key.
- **Variant groups by rule help a little.** `-v`/`-nv` experiment versions and `_next` follow-ons take coverage from 0.86 to 0.90.
- **About 25 hits need an annotation.** They have no subject, module or battery.
- **The key's candidate rules make a keyword annotation circular,** so the design uses a model annotation blind to the key, adjudicates every new item, samples 300 non-candidates to estimate what the key misses, and adds a second topic.

**Decisions needed** (from the design):
1. Variant groups: a group kind, or a link relation? (coordinator)
2. A budget and a model for annotating 6,943 records, about 1M input tokens. (Allen)
3. The second topic, and its key's reader.
4. Whether to include the ANES and NSFG slices.

**Files:** `planning/topic_annotation_design.md` and this file. Building would add files in pdt-gss's `metadata/annotations/` and `metadata/groups.jsonl` (through its build), and in `eval/`.

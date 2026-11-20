# Task 76 — pdt-nsfg: the release expected on 2026-12-01

**Status:** `TODO`, waiting for NCHS. Allen has a watch set and will say when the release is out.

Follow the Task 75 runbook:
1. Add the release to `dataset.yaml` and `sources.yaml`; download data, codebooks, questionnaires and the "what's new" notes.
2. Run the codebook parser; fix it for any layout change (2022–2023 switched names to upper case).
3. Records for the slice (all Task 75 variables that exist), links from 2022–2023 by rule and `pdt diff`, checked against NCHS's notes; corrections where the documentation is wrong.
4. `make data`, `make views`, `make check` (0 failures); the new release `current`, 2022–2023 earlier.
5. The coordinator reviews and pushes; the site updates.

## Progress

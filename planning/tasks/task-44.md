# Task 44 — One line per variable across releases

**Status:** `DOING (red)`

Task 42's proposal 2, accepted by the coordinator.

- **In the catalog,** collapse a variable's lines across releases by its links (`same_item`, `renamed`, and relabels), and show its release span and names: "BRFSS ADDEPEV2 2011–2018 → ADDEPEV3 2019–2023".
- **A change of meaning** (`universe_changed`, `codes_changed`) keeps lines separate, but shows them together with the relation.
- **In each repo's agent index,** use the same collapse if it fits, keeping the per-release detail.

Rerun Task 42's three test questions, and report the line counts before and after.

**Files:** a new `lib/pdt/chains.py` and its tests; `lib/pdt/catalog.py`; `lib/pdt/views.py` if the agent index uses it; this file.

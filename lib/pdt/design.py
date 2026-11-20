"""The survey design in dataset.yaml (STANDARD.md §2.1): which design applies, and its weights
and replicate weights as plain column names.

`design` can be set for the dataset, a release or a table; the most specific one applies,
whole (a table's design replaces the release's; they aren't merged).

    effective_design(dataset, "2003-2025", "summary")   -> the design dict, or None
    weight_names(design)                -> ["TUFNWGTP", "TU20FWGT"]
    weight_names(design, wave=2020)     -> ["TUFNWGTP", "TU20FWGT"]   (a plain name applies to every wave)
    weight_names(design, wave=2019)     -> ["TUFNWGTP"]               ({name: TU20FWGT, waves: [2020]})
    replicate_columns(design, columns)  -> ("replicates", ["TUFNWGTP001", ..., "TUFNWGTP160"])

A weight is a name or {name, waves[, note]}. Replicates are named by `variables`, or by a
`prefix` and a count `n`; the numbers may be zero-padded (TUFNWGTP001) or not (W_FSTURWT1), so
replicate_columns matches the prefix against the table's actual columns when it has them.
"""

import re


def effective_design(dataset, release_id=None, table_id=None):
    """The design that applies to a table: its own, else its release's, else the dataset's."""
    release = next((r for r in dataset.get("releases", []) if r.get("id") == release_id), None)
    if release is not None and table_id is not None:
        table = next((t for t in release.get("tables", []) if t.get("id") == table_id), None)
        if table is not None and table.get("design") is not None:
            return table["design"]
    if release is not None and release.get("design") is not None:
        return release["design"]
    return dataset.get("design")


def _waves_match(waves, wave):
    return wave is None or any(str(w) == str(wave) for w in waves)


def weight_names(design, wave=None):
    """The weights' names, in order. With `wave`, only those that apply to it."""
    out = []
    for w in (design or {}).get("weights", []):
        if isinstance(w, str):
            out.append(w)
        elif _waves_match(w.get("waves", []), wave):
            out.append(w["name"])
    return out


def replicate_columns(design, columns=None):
    """(table or None, [names]) of the replicate weights.

    `table` is design.replicates.table: None means the same table as the design. With
    `columns` (the names in that table: records or data), prefix + n matches the columns that
    are the prefix followed by a number 1..n, padded or not, in numeric order. Without it, the
    names are generated unpadded (prefix1 ... prefixn)."""
    rep = (design or {}).get("replicates")
    if not rep:
        return None, []
    table = rep.get("table")
    if rep.get("variables"):
        return table, list(rep["variables"])
    prefix, n = rep["prefix"], rep["n"]
    if columns is None:
        return table, [f"{prefix}{i}" for i in range(1, n + 1)]
    pattern = re.compile(re.escape(prefix) + r"(\d+)")
    found = []
    for c in columns:
        m = pattern.fullmatch(c)
        if m and 1 <= int(m.group(1)) <= n:
            found.append((int(m.group(1)), c))
    return table, [c for _, c in sorted(found)]


def replicate_key(design):
    """design.replicates.key: the columns the replicate table joins on, or []."""
    return list(((design or {}).get("replicates") or {}).get("key") or [])

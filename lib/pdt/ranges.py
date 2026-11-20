"""A record's valid ranges (STANDARD.md §4.1, `valid_range`).

`valid_range` is one range, `{"min", "max", ...}`, or, when the valid values form several
ranges with different meanings, a list of them, each with its `label` (BRFSS ALCDAY5:
101-107 days per week, 201-230 days in the past 30). Every reader goes through these
functions so it handles both forms.
"""

FLAGS = ("top_coded", "bottom_coded")


def valid_ranges(record):
    """The record's valid ranges as a list of dicts; [] when it has none."""
    vr = record.get("valid_range")
    if not vr:
        return []
    return [r for r in (vr if isinstance(vr, list) else [vr]) if isinstance(r, dict)]


def bounds(r):
    """(min, max) when both are numbers, else None."""
    lo, hi = r.get("min"), r.get("max")
    if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) \
            and not isinstance(lo, bool) and not isinstance(hi, bool):
        return lo, hi
    return None


def in_valid_range(record, x):
    """True if x is a number inside any of the record's valid ranges."""
    if isinstance(x, (str, bool)) or not isinstance(x, (int, float)):
        try:
            x = float(x)
        except (TypeError, ValueError):
            return False
    return any(b is not None and b[0] <= x <= b[1] for b in map(bounds, valid_ranges(record)))


def span(record):
    """(min, max) over all the record's ranges with numeric bounds, or None."""
    bs = [b for b in map(bounds, valid_ranges(record)) if b]
    if not bs:
        return None
    return min(b[0] for b in bs), max(b[1] for b in bs)


def comparable(record):
    """The ranges without notes, for comparing two releases: a list of tuples."""
    return [(r.get("min"), r.get("max"), r.get("label"), *(bool(r.get(f)) for f in FLAGS))
            for r in valid_ranges(record)]


def without_notes(record):
    """valid_range as stored, minus notes: a dict, a list of dicts, or None."""
    vr = record.get("valid_range")
    if not vr:
        return None
    strip = lambda r: {k: v for k, v in r.items() if k != "note"}
    return [strip(r) for r in vr] if isinstance(vr, list) else (strip(vr) or None)


def range_text(r):
    """One range for people: "101-107 (days per week), top-coded"."""
    text = f"{r.get('min', '')}–{r.get('max', '')}"
    if r.get("label"):
        text += f" ({r['label']})"
    flags = [f.replace("_", "-") for f in FLAGS if r.get(f)]
    if flags:
        text += ", " + ", ".join(flags)
    return text


def notes(record):
    """The ranges' notes, in order."""
    return [r["note"] for r in valid_ranges(record) if r.get("note")]

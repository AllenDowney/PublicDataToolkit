"""A record's universe (STANDARD.md §4.1): a string, or a list of {text, waves} when it differs by
wave (NLSY97 YSAQ-363: "All" in 1997, then only those who hadn't answered as of the last interview).

    universe_text(rec["universe"])        -> one string for display or comparison
    universe_at(rec["universe"], 2004)    -> the universe in that wave, or None
    universe_by_wave(rec["universe"])     -> [(text, waves)]; waves is None for a plain string
"""


def universe_by_wave(universe):
    if not universe:
        return []
    if isinstance(universe, str):
        return [(universe, None)]
    return [(u.get("text", ""), list(u.get("waves") or [])) for u in universe]


def universe_text(universe):
    """'All (1997); R did not answer ... (1998, 1999)', or the string itself."""
    parts = universe_by_wave(universe)
    if len(parts) == 1 and parts[0][1] is None:
        return parts[0][0]
    return "; ".join(f"{text} ({', '.join(map(str, waves))})" if waves else text for text, waves in parts)


def universe_at(universe, wave):
    """The universe in one wave: the string, or the entry whose waves include it."""
    for text, waves in universe_by_wave(universe):
        if waves is None or any(str(w) == str(wave) for w in waves):
            return text
    return None

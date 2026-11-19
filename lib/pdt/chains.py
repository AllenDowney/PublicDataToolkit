"""A variable across releases: chains of records joined by links.

A chain is the records of one variable in several releases, joined by links whose
relations say it continued with the same meaning: `same_item`, `renamed`,
`labels_changed`, `data_revised`. BRFSS ADDEPEV2 (2011-2018) and ADDEPEV3 (2019-2023)
are one chain, shown as "ADDEPEV2 2011-2018 -> ADDEPEV3 2019-2023".

A link that says the meaning changed (`codes_changed`, `wording_changed`,
`universe_changed`) doesn't join chains. It relates them, so a view can show them
together, with the relation. Links that aren't one to one (`derived_from`, `split_from`,
`merged_into`) and links within one release are left out.
"""

from dataclasses import dataclass, field

from .views import release_order

SAME_MEANING = {"same_item", "renamed", "labels_changed", "data_revised"}
CHANGED_MEANING = {"codes_changed", "wording_changed", "universe_changed"}
NOT_ONE_TO_ONE = {"derived_from", "split_from", "merged_into"}


@dataclass
class Chain:
    members: list                       # [(release, table, name)], oldest release first
    related: list = field(default_factory=list)     # [(relations, other Chain, "to" or "from")]

    @property
    def table(self):
        tables = {t for _, t, _ in self.members}
        return tables.pop() if len(tables) == 1 else None

    @property
    def last(self):
        return self.members[-1]

    @property
    def id(self):
        rel, tab, name = self.members[0]
        return (f"{tab}/" if tab else "") + f"{name}@{rel}"


def span(ids, order):
    """Release ids as runs over the releases in order: 2011-2018, or 2017-2019, 2022-2023."""
    pos = {r: i for i, r in enumerate(order)}
    ids = sorted(ids, key=lambda r: pos[r])
    runs, start, prev = [], ids[0], ids[0]
    for r in ids[1:]:
        if pos[r] == pos[prev] + 1:
            prev = r
            continue
        runs.append((start, prev))
        start = prev = r
    runs.append((start, prev))
    return ", ".join(a if a == b else f"{a}–{b}" for a, b in runs)


def names_text(chain, order):
    """ADDEPEV2 2011–2018 → ADDEPEV3 2019–2023; one name: ADDEPEV2 2011–2023.
    With one release in order, just the name (or names, if a link renamed it)."""
    if len(order) == 1:
        return " \u2192 ".join(dict.fromkeys(n for _, _, n in chain.members))
    groups = []
    for rel, _, name in chain.members:
        if groups and groups[-1][0] == name:
            groups[-1][1].append(rel)
        else:
            groups.append([name, [rel]])
    return " → ".join(f"{name} {span(rels, order)}" for name, rels in groups)


def build(repo, releases=None):
    """Chains over the given releases (all by default), in release order then name.

    Returns (chains, order): order is the releases, oldest first."""
    order = [r for r in release_order(repo.dataset) if releases is None or r in releases]
    nodes = [(rel, tab, rec["name"]) for rel in order for tab, recs in repo.tables.get(rel, {}).items()
             for rec in recs]
    known = set(nodes)
    parent = {n: n for n in nodes}

    def find(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    related = []
    for link in repo.links:
        f, t = link["from"], link["to"]
        a = (f.get("release"), f.get("table"), f["name"])
        b = (t.get("release"), t.get("table"), t["name"])
        rels = set(link["relations"])
        if a not in known or b not in known or a[0] == b[0] or rels & NOT_ONE_TO_ONE:
            continue
        if rels <= SAME_MEANING:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra
        else:
            related.append((sorted(rels), a, b))

    pos = {r: i for i, r in enumerate(order)}
    groups = {}
    for n in nodes:
        groups.setdefault(find(n), []).append(n)
    chains = {}
    for members in groups.values():
        members.sort(key=lambda n: (pos[n[0]], str(n[1]), n[2]))
        chain = Chain(members)
        for n in members:
            chains[n] = chain
    for rels, a, b in related:
        ca, cb = chains[a], chains[b]
        if ca is not cb:
            older, newer = (ca, cb) if pos[a[0]] <= pos[b[0]] else (cb, ca)
            older.related.append((rels, newer, "to"))
            newer.related.append((rels, older, "from"))
    unique = list({id(c): c for c in chains.values()}.values())
    unique.sort(key=lambda c: (pos[c.members[0][0]], str(c.table), c.members[0][2]))
    return unique, order


def ordered_with_related(chains):
    """Chains in order, each chain related to an earlier one placed right after it.

    Returns [(chain, relation to the chain above it or None)]."""
    out, placed = [], set()

    def place(chain, relation):
        if id(chain) in placed:
            return
        placed.add(id(chain))
        out.append((chain, relation))
        for rels, other, direction in chain.related:
            if direction == "to":
                place(other, rels)

    for chain in chains:
        if not any(d == "from" for _, _, d in chain.related):
            place(chain, None)
    for chain in chains:                       # a cycle of relations, if any
        place(chain, None)
    return out

"""Generate the human-readable site of a dataset repo, `docs/` (STANDARD.md §7).

Plain static HTML, no build tool and no dependencies, so it opens from disk and
GitHub Pages serves `docs/` as it is:

    docs/index.html                        the dataset, its releases, groups and corrections; search
    docs/releases/<release>[-<table>].html every variable in a release or table
    docs/variables/<release>/[<table>/]<name>.html   one page per variable
    docs/groups/<id>.html                  one page per group
    docs/changes/<old>--<new>.html         what changed between adjacent releases
    docs/search-index.js, style.css, .nojekyll, manifest.json

Every page starts with a comment naming the library version and the input hash, and
docs/manifest.json lists the files, as agent/ does; `is_current` checks it.
"""

import html
import json
import shutil
from pathlib import Path
from urllib.parse import quote

from . import __version__
from .check import Repo
from .search import Index
from .ranges import notes as range_notes, range_text, valid_ranges
from .views import (AVAIL_DIMS, generator_hash, inputs_hash, natural, origin_text, release_order, sort_key, wave_list,
                    wave_summary, when_text)
from .universe import universe_by_wave, universe_text

DIRECTORY = "docs"


def esc(value):
    return html.escape("" if value is None else str(value))


def retired_note(value):
    """" (retired)", with the years in use when the publisher gives them (STANDARD.md §4.2)."""
    waves = value.get("waves")
    span = f"{waves['from']}–{waves.get('to', '')}" if waves else ""
    if value.get("retired"):
        return f' <span class="origin">(retired{", in use " + esc(span) if span else ""})</span>'
    return f' <span class="origin">(in use {esc(span)})</span>' if span else ""


def text_block(value):
    return f'<div class="text">{esc(value)}</div>'


def file_name(name):
    """A variable name as a file name: kept as published, unsafe characters escaped."""
    return quote(str(name), safe="") + ".html"


class Site:
    def __init__(self, root, out):
        self.root = Path(root)
        self.out = Path(out)
        self.repo = Repo.load(self.root)
        self.index = Index.from_repo(self.repo)
        self.digest = inputs_hash(self.root)
        self.files = []
        self.ds = self.repo.dataset
        self.dims = self.ds.get("dimensions", {})
        self.waves = {}
        for rel, ts in self.repo.tables.items():
            found = {a["wave"] for recs in ts.values() for rec in recs
                     for a in rec.get("availability") or [] if "wave" in a}
            self.waves[rel] = sorted(found, key=sort_key)
        self.corrections = {c["id"]: c for c in self.repo.corrections}
        self.histories = {}
        hist = self.root / "metadata" / "histories.jsonl"
        if hist.exists():
            for line in hist.read_text().splitlines():
                if line.strip():
                    h = json.loads(line)
                    self.histories[(h.get("table"), h["name"])] = h
        # One page per variable across releases: a lineage (pdt.chains), the runs of records joined
        # by links that keep the meaning, and the one-to-one links that change it between runs. A
        # page is named after the lineage's latest name; when two lineages end in the same name,
        # the one ending in the older release gets "@<release>". Other names get an alias page.
        from . import chains as chains_mod
        self.chains, self.order = chains_mod.build(self.repo)
        self.lineages = chains_mod.lineages(self.chains, self.order)
        self.records = {(rel, tab, rec["name"]): rec for rel, tab, rec in self.index.entries}
        # code_of (STANDARD.md §4.1): (code list, code) -> the variables that stand for that code,
        # and code list -> the variables whose values come from it, for links both ways.
        self.code_of = {}
        self.uses_list = {}
        for (rel, tab, name), rec in self.records.items():
            if rec.get("code_of"):
                key = (rec["code_of"]["code_list"], str(rec["code_of"]["code"]))
                self.code_of.setdefault(key, []).append((rel, tab, name))
            if rec.get("code_list"):
                self.uses_list.setdefault(rec["code_list"], []).append((rel, tab, name))
        pos = {r: i for i, r in enumerate(self.order)}
        self.page_of, self.chain_of, self.lineage_page, taken = {}, {}, {}, set()
        for lineage in sorted(self.lineages, key=lambda l: -pos[l.latest.last[0]]):
            rel, tab, name = lineage.latest.last
            stem = "/".join(["variables"] + ([tab] if tab else []))
            path = f"{stem}/{file_name(name)}"
            if path.lower() in taken:
                path = f"{stem}/{file_name(f'{name}@{rel}')}"
            taken.add(path.lower())
            self.lineage_page[id(lineage)] = path
            for chain in lineage.chains:
                for m in chain.members:
                    self.page_of[m] = path
                    self.chain_of[m] = chain
        # Alias pages: a lineage's other names (ADDEPEV2 for ADDEPEV3), where no page has the name.
        self.aliases = {}
        for lineage in self.lineages:
            target = self.lineage_page[id(lineage)]
            for _, tab, name in lineage.members:
                stem = "/".join(["variables"] + ([tab] if tab else []))
                path = f"{stem}/{file_name(name)}"
                if path.lower() not in taken and path not in self.aliases:
                    self.aliases[path] = target
        self.signature = {}
        for d in self.repo.derived:
            for rel, tab, rec in self.index.entries:
                t = d["target"]
                if (rec["name"] == t.get("variable") and t.get("release") in (None, rel)
                        and t.get("table") in (None, tab)):
                    self.signature.setdefault((rel, tab, rec["name"]), {})[d["property"]] = d

    # ------------------------------------------------------------ paths

    def var_path(self, release, table, name):
        """The page of a variable's record: its chain's page (one per variable across releases)."""
        return self.page_of[(release, table, name)]

    def release_path(self, release, table):
        return f"releases/{release}{'-' + table if table else ''}.html"

    def group_path(self, gid):
        return f"groups/{file_name(gid)}"

    def link(self, here, target, text):
        depth = here.count("/")
        return f'<a href="{"../" * depth}{target}">{esc(text)}</a>'

    def dim_label(self, dim):
        return self.dims.get(dim, {}).get("label", dim)

    # ------------------------------------------------------------ writing

    def page(self, path, title, body, crumbs=()):
        depth = path.count("/")
        up = "../" * depth
        nav = [f'<a href="{up}index.html">{esc(self.ds.get("title", self.ds.get("id")))}</a>']
        nav += [self.link(path, target, text) for target, text in crumbs]
        doc = f"""<!-- Generated by pdt {__version__} from inputs sha256:{self.digest}. Do not edit; run `make views`. -->
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<link rel="stylesheet" href="{up}style.css">
</head>
<body>
<nav>{" › ".join(nav)}</nav>
<main>
<h1>{esc(title)}</h1>
{body}
</main>
<footer>Generated by the PublicDataToolkit library {__version__} from this repository's
metadata. Corrected values are marked <span class="corrected">corrected</span>.</footer>
</body>
</html>
"""
        self.write(path, doc)

    def write(self, path, text):
        target = self.out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        self.files.append(path)

    # ------------------------------------------------------------ build

    def build(self):
        if self.out.exists():
            if any(self.out.iterdir()) and not (self.out / "manifest.json").exists():
                raise FileExistsError(f"{self.out} exists and wasn't generated by pdt; not overwriting")
            shutil.rmtree(self.out)
        self.out.mkdir(parents=True)
        self.write(".nojekyll", "")
        self.write("style.css", STYLE)
        self.home()
        for r in self.ds.get("releases", []):
            for tab, recs in self.repo.tables.get(r["id"], {}).items():
                self.release_page(r, tab, recs)
        for lineage in self.lineages:
            self.variable_page(lineage)
        for path, target in sorted(self.aliases.items()):
            self.alias_page(path, target)
        for g in self.repo.groups:
            self.group_page(g)
        for old, new in self.changed_pairs():
            self.changes_page(old, new)
        self.search_index()
        manifest = {"pdt_version": __version__, "inputs_sha256": self.digest,
                    "generator_sha256": generator_hash(),
                    "dataset": self.ds.get("id"), "files": sorted(self.files)}
        (self.out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
        return manifest

    # ------------------------------------------------------------ pages

    def home(self):
        ds, here = self.ds, "index.html"
        body = []
        if ds.get("description"):
            body.append(f"<p>{esc(' '.join(ds['description'].split()))}</p>")
        pub = ds.get("publisher", {})
        facts = [("Publisher", f'<a href="{esc(pub.get("url", ""))}">{esc(pub.get("name"))}</a>'
                  if pub.get("url") else esc(pub.get("name"))),
                 ("Dataset", f'<a href="{esc(ds.get("url"))}">{esc(ds.get("url"))}</a>'
                  if ds.get("url") else "-")]
        terms = ds.get("terms", {})
        if terms:
            facts.append(("Terms", f'<a href="{esc(terms.get("url"))}">{esc(terms.get("url"))}</a>'
                          f'<br>{esc(" ".join((terms.get("summary") or "").split()))}'))
        if ds.get("citation"):
            facts.append(("Citation", esc(" ".join(ds["citation"].split()))))
        for dim, d in self.dims.items():
            facts.append((f"<code>{esc(dim)}</code>", esc(d.get("label", dim))
                          + (f" — {esc(' '.join(d['note'].split()))}" if d.get("note") else "")))
        body.append(dl(facts))

        body.append('<h2>Find a variable</h2>\n<input id="q" type="search" '
                    'placeholder="Name, label or question text" autofocus>\n<ul id="hits"></ul>')

        body.append("<h2>Releases</h2>")
        rows = []
        for r in ds.get("releases", []):
            for tab, recs in self.repo.tables.get(r["id"], {}).items():
                rows.append([self.link(here, self.release_path(r["id"], tab),
                                       r["id"] + (f" / {tab}" if tab else "")),
                             esc(r.get("label")), esc(r.get("status", "")), str(len(recs)),
                             esc(wave_list(self.waves.get(r["id"], [])).replace(",", ", "))])
        body.append(table(["Release", "Label", "Status", "Variables", self.dim_label("wave")], rows))

        if self.repo.groups:
            body.append("<h2>Groups</h2>")
            rows = [[self.link(here, self.group_path(g["id"]), g.get("label") or g["id"]),
                     esc(g["kind"]), str(len(g["members"])), esc(origin_text(g["origin"]))]
                    for g in sorted(self.repo.groups, key=lambda g: (g["kind"], g.get("label") or g["id"]))]
            body.append(table(["Group", "Kind", "Members", "Origin"], rows))

        if self.index.corrected:
            body.append("<h2>Corrections</h2>\n<p>Errors in the source documentation that this "
                        "repository corrects. The source records keep the original.</p>")
            rows = []
            for (rel, tab, name), applied in sorted(self.index.corrected.items(), key=lambda kv: str(kv[0])):
                for a in applied:
                    rows.append([self.link(here, self.var_path(rel, tab, name), name),
                                 f"<code>{esc(a['field'])}</code>", esc(a["problem"]),
                                 esc(a["confidence"])])
            body.append(table(["Variable", "Field", "Problem", "Confidence"], rows))

        releases = release_order(ds)
        if len(releases) > 1:
            changed = self.changed_pairs()
            body.append("<h2>Changes between releases</h2><ul>" + "".join(
                f"<li>{self.link(here, f'changes/{a}--{b}.html', f'{a} → {b}')}</li>"
                for a, b in changed) + "</ul>")
            same = [(a, b) for a, b in zip(releases, releases[1:]) if (a, b) not in changed]
            if same:
                body.append("<p>No variable changed between: " + esc(", ".join(f"{a} → {b}" for a, b in same))
                            + ".</p>")
        body.append('<script src="search-index.js"></script>\n<script>' + SEARCH_JS + "</script>")
        self.page(here, ds.get("title", ds.get("id")), "\n".join(body))

    def release_page(self, r, tab, recs):
        here = self.release_path(r["id"], tab)
        title = f"{r['id']}" + (f" / {tab}" if tab else "")
        body = [f"<p>{esc(r.get('label'))}</p>"]
        if tab:
            t = next(t for t in r["tables"] if t["id"] == tab)
            facts = [("Table", esc(t.get("label", tab)))]
            if t.get("key"):
                facts.append(("Key", ", ".join(self.column(here, r["id"], tab, k) for k in t["key"])))
            refs = [self.reference(here, r["id"], tab, ref) for ref in t.get("references") or []]
            if refs:
                facts.append(("Refers to", "<br>".join(refs)))
            back = [(other, ref) for other in r["tables"] for ref in other.get("references") or []
                    if ref.get("table") == tab and not ref.get("dataset")]
            if back:
                facts.append(("Referred to by", "<br>".join(
                    self.reference(here, r["id"], other["id"], ref, source=True) for other, ref in back)))
            body.append(dl(facts))
            if t.get("description"):
                body.append(f"<p>{esc(' '.join(t['description'].split()))}</p>")
        if r.get("sources"):
            body.append(dl([("Sources", ", ".join(f"<code>{esc(s)}</code>" for s in r["sources"]))]))
        if r.get("revisions"):
            body.append("<h2>Revisions</h2><p>The publisher reissued this release's files without "
                        "a new release.</p>" + table(
                            ["Date", "What changed", "Source"],
                            [[esc(v["date"]), esc(" ".join(v["description"].split())),
                              f"<code>{esc(v['source'])}</code>" if v.get("source") else ""]
                             for v in r["revisions"]]))
        rows = []
        for rec in recs:
            key = (r["id"], tab, rec["name"])
            name = self.link(here, self.var_path(*key), rec["name"])
            if key in self.index.corrected:
                name += ' <span class="corrected">corrected</span>'
            rows.append([name, esc(rec.get("label")), esc(availability_line(rec, self.waves[r["id"]], self.dim_label("form"))),
                         esc(self.signature.get(key, {}).get("scale_signature", {}).get("value", ""))])
        body.append(table(["Name", "Label", self.dim_label("wave") + "s", "Scale"], rows))
        self.page(here, title, "\n".join(body), crumbs=[])

    def column(self, here, rel, tab, name):
        """A column name, linked to its variable page when the repo has a record for it."""
        if any(r == rel and t == tab and rec["name"] == name for r, t, rec in self.index.entries):
            return f"<code>{self.link(here, self.var_path(rel, tab, name), name)}</code>"
        return f"<code>{esc(name)}</code>"

    def reference(self, here, rel, tab, ref, source=False):
        """ "ST_CASE, VEH_NO → vehicle, when PER_TYP is 3", with links."""
        cols = ", ".join(self.column(here, rel, tab, c) for c in ref.get("columns", []))
        target = ref.get("table", "?")
        if ref.get("dataset"):
            other = esc(f"{ref['dataset']}: {target}")
        elif source:
            other = self.link(here, self.release_path(rel, tab), tab)
        else:
            other = self.link(here, self.release_path(rel, target), target)
        text = f"{other}: {cols}" if source else f"{cols} → {other}"
        if ref.get("when"):
            when = ref["when"]
            col = self.column(here, rel, tab, when.get("column", ""))
            text += f", when {col}{esc(when_text(when)[len(str(when.get('column', ''))):])}"
        return text

    def code_of_text(self, here, rec):
        """'code 010101, Sleeping, in list atus-lexicon-0325', linked to the code's row on the page
        of a variable whose values come from that list."""
        ref = rec["code_of"]
        cl = next((c for c in self.repo.code_lists if c["id"] == ref["code_list"]), None)
        label = next((c.get("label") for c in (cl or {}).get("codes", []) if str(c["code"]) == str(ref["code"])), None)
        text = f"code <code>{esc(ref['code'])}</code>" + (f", {esc(label)}" if label else "") \
            + f", in code list <code>{esc(ref['code_list'])}</code>"
        users = self.uses_list.get(ref["code_list"], [])
        if users:
            rel, tab, name = users[0]
            text += " (see " + self.link(here, f"{self.var_path(rel, tab, name)}#code-{ref['code']}", name) + ")"
        return text

    def columns_for_code(self, here, code_list, code):
        """Links to the variables that stand for this code of a shared list (code_of)."""
        if not code_list:
            return ""
        found = self.code_of.get((code_list, str(code)), [])
        if not found:
            return ""
        return '<br><span class="origin">Column: ' + ", ".join(
            self.link(here, self.var_path(rel, tab, name), name) for rel, tab, name in found) + "</span>"

    def variable_page(self, lineage):
        chain = lineage.latest
        rel, tab, name = chain.last
        rec = self.records[chain.last]
        here = self.var_path(rel, tab, rec["name"])
        key = (rel, tab, rec["name"])
        applied = {a["field"]: a for a in self.index.corrected.get(key, [])}
        body = []
        if rec.get("label"):
            body.append(f'<p class="label">{esc(rec["label"])}{mark(applied, "/label")}</p>')

        facts = [("Release", self.link(here, self.release_path(rel, tab), rel + (f" / {tab}" if tab else "")))]
        for field in ("storage_type", "measure", "variable_type", "units"):
            if rec.get(field):
                facts.append((field.replace("_", " ").capitalize(), esc(rec[field])))
        for prop, d in sorted(self.signature.get(key, {}).items()):
            facts.append((prop.replace("_", " ").capitalize(),
                          f"{esc(d['value'])} <span class=\"origin\">rule {esc(d['rule'])} "
                          f"{esc(d['rule_version'])}</span>"))
        if rec.get("code_of"):
            facts.append(("Stands for", self.code_of_text(here, rec)))
        loc = rec.get("source_location") or {}
        if loc.get("url"):
            facts.append(("Publisher's page", f'<a href="{esc(loc["url"])}">{esc(loc["url"])}</a>'))
        elif loc:
            rest = ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in loc.items() if k != "source")
            facts.append(("Source", f"<code>{esc(loc.get('source', ''))}</code>"
                          + (f", {esc(rest)}" if rest else "")))
        body.append(dl(facts))

        if rec.get("description"):
            body.append(f"<h2>Description{mark(applied, '/description')}</h2>{text_block(rec['description'])}")
        if rec.get("universe"):
            parts = universe_by_wave(rec["universe"])
            if len(parts) == 1 and parts[0][1] is None:
                body.append(f"<h2>Universe{mark(applied, '/universe')}</h2>{text_block(parts[0][0])}")
            else:  # a universe by wave (STANDARD.md §4.1)
                body.append(f"<h2>Universe{mark(applied, '/universe')}</h2>")
                body.append(table([self.dim_label("wave").capitalize() + "s", "Universe"],
                                  [[esc(", ".join(map(str, w or []))), esc(t)] for t, w in parts]))

        if rec.get("questions"):
            body.append("<h2>Question</h2>")
            for i, q in enumerate(rec["questions"]):
                where = []
                for dim, k in (("wave", "waves"), ("form", "forms"), ("mode", "modes")):
                    if q.get(k):
                        where.append(f"{self.dim_label(dim)}s {', '.join(map(str, q[k]))}")
                if len(rec["questions"]) > 1 or where:
                    body.append(f"<h3>Wording {i + 1}{': ' + esc('; '.join(where)) if where else ''}</h3>")
                body.append(text_block(q.get("text", "")) + mark(applied, f"/questions/{i}/text"))
                if q.get("instructions") or q.get("note"):
                    body.append(dl([(k.capitalize(), esc(q[k])) for k in ("instructions", "note") if q.get(k)]))

        values = rec.get("values") or []
        if values:
            default = (rec.get("provenance") or {}).get("codes")
            body.append("<h2>Codes</h2>")
            cl = next((c for c in self.repo.code_lists if c["id"] == rec.get("code_list")), None)
            if cl is not None:
                n_list = len(cl["codes"])
                body.append(f'<p>The first {n_list:,} codes are the shared code list <code>{esc(cl["id"])}</code>, '
                            f'{esc(cl["label"])}, used by every variable that names it'
                            + (f' (<span class="origin">{esc(origin_text(cl["origin"]))}</span>)' if cl.get("origin") else "")
                            + "; the rest are this variable's own.</p>")
            counts = any("n" in v for v in values)
            rows = []
            for i, v in enumerate(values):
                origin = v.get("origin") or (default if v.get("kind") != "valid" else None)
                anchor = f' id="code-{esc(v.get("code"))}"' if cl is not None else ""  # code_of links here
                row = [f"<code{anchor}>{esc(v.get('code'))}</code>",
                       esc(v.get("label")) + mark(applied, f"/values/{i}/label") + retired_note(v)
                       + self.columns_for_code(here, rec.get("code_list"), v.get("code"))
                       + (f'<br><span class="origin">Note: {esc(v["note"])}</span>' if v.get("note") else ""),
                       f'<span class="kind-{esc(v.get("kind"))}">{esc(v.get("kind"))}</span>',
                       esc(", ".join(v.get("missing_types") or [])),
                       f'<span class="origin">{esc(origin_text(origin))}</span>' if origin else ""]
                if counts:
                    row.insert(2, f'<span class="num">{v["n"]:,}</span>' if isinstance(v.get("n"), int) else "")
                rows.append(row)
            headers = ["Code", "Label", "Kind", "Missing types", "Classified by"]
            if counts:
                headers.insert(2, "Cases")
            body.append(table(headers, rows))
            if counts:
                body.append('<p class="origin">Cases: how many the publisher\'s codebook counts for each '
                            "code in this release.</p>")
        if valid_ranges(rec):
            rs = valid_ranges(rec)
            items = [("Valid range" if len(rs) == 1 else "Valid ranges",
                      "<br>".join(esc(range_text(r)) for r in rs))]
            if range_notes(rec):
                items.append(("Range note", "<br>".join(esc(n) for n in range_notes(rec))))
            body.append(dl(items))

        if rec.get("availability"):
            body.append(f"<h2>Availability</h2><p>{esc(availability_line(rec, self.waves[rel], self.dim_label("form")))}</p>")
            body.append(self.availability_table(rec, self.waves[rel]))

        history = self.histories.get((tab, rec["name"]))
        if history:
            body.append(self.history_table(history))

        if rec.get("notes"):
            notes = rec["notes"] if isinstance(rec["notes"], list) else [rec["notes"]]
            body.append(f"<h2>Notes{mark(applied, '/notes')}</h2>" + "".join(text_block(n) for n in notes))

        if applied:
            body.append("<h2>Corrections</h2>")
            for a in applied.values():
                c = self.corrections[a["id"]]
                ev = "".join(f"<li>{esc(e.get('citation'))}"
                             + (f' — <a href="{esc(e["url"])}">{esc(e["url"])}</a>' if e.get("url") else "")
                             + (f'<blockquote>{esc(e["quote"])}</blockquote>' if e.get("quote") else "")
                             + "</li>" for e in c.get("evidence", []))
                up = c.get("upstream") or {}
                upstream = esc(up.get("status", "")) + (
                    f' — <a href="{esc(up["url"])}">{esc(up["url"])}</a>' if up.get("url") else "")
                body.append(f'<div class="correction"><p><code>{esc(c["target"]["field"])}</code>: '
                            f'{esc(c["problem"])}</p>'
                            + dl([("Original", text_block(c["original"])),
                                  ("Corrected", text_block(c["corrected"])),
                                  ("Confidence", esc(c["confidence"])),
                                  ("Evidence", f"<ul>{ev}</ul>"),
                                  ("Reported upstream", upstream),
                                  ("By", f"{esc(c.get('author'))}, {esc(c.get('date'))}")])
                            + "</div>")

        groups = [g for g in self.repo.groups if any(
            m.get("name") == rec["name"] and m.get("table") in (None, tab) and m.get("release") in (None, rel)
            for m in g["members"])]
        if groups:
            body.append("<h2>Groups</h2><ul>" + "".join(
                f"<li>{self.link(here, self.group_path(g['id']), g.get('label') or g['id'])} "
                f"({esc(g['kind'])})</li>" for g in groups) + "</ul>")

        if len(lineage.members) > 1:
            body.append(self.lineage_section(here, lineage))

        links = [x for m in lineage.members for x in self.links_for(*m, here=here)]
        if links:
            body.append("<h2>Other links</h2><ul>" + "".join(dict.fromkeys(links)) + "</ul>")

        topics = sorted({(a["value"], origin_text(a["origin"])) for a in self.index.topics
                         if a["target"].get("variable") == rec["name"]
                         and a["target"].get("release") in (None, rel)
                         and a["target"].get("table") in (None, tab)})
        if topics:
            body.append("<h2>Topics</h2><p>Annotations, for finding variables; not facts about "
                        "the data.</p><ul>" + "".join(
                            f'<li>{esc(v)} <span class="origin">{esc(o)}</span></li>' for v, o in topics)
                        + "</ul>")

        prov = rec.get("provenance") or {}
        rows = []
        if prov.get("record"):
            rows.append(["record", esc(origin_text(prov["record"])), esc(prov["record"].get("note", ""))])
        if prov.get("codes"):
            rows.append(["codes (default)", esc(origin_text(prov["codes"])), esc(prov["codes"].get("note", ""))])
        for f, o in (prov.get("fields") or {}).items():
            rows.append([esc(f), esc(origin_text(o)), esc(o.get("note", ""))])
        if rows:
            body.append("<h2>Provenance</h2>" + table(["Field", "Origin", "Note"], rows))
        if rec.get("extensions"):
            body.append("<h2>Extensions</h2><pre>" + esc(json.dumps(rec["extensions"], indent=1,
                                                                 ensure_ascii=False)) + "</pre>")
        crumbs = [(self.release_path(rel, tab), rel + (f" / {tab}" if tab else ""))]
        self.page(here, rec["name"], "\n".join(body), crumbs)

    def releases_section(self, here, chain):
        """The variable in each release: name, waves, and what differs from the latest release."""
        from .chains import names_text
        from .diff import compare_pair
        current = self.records[chain.last]
        cur_rel = chain.last[0]
        rows, details = [], []
        for m in chain.members:
            rel, tab, name = m
            rec = self.records[m]
            changes = {} if m == chain.last else compare_pair(rec, current)
            real = {k: v for k, v in changes.items()
                    if not (isinstance(v, dict) and v.get("how") in ("text_only", "reference_only", "observed"))}
            codes = real.get("codes", {})
            if "codes" in real:
                kinds = [k for k in ("added", "dropped", "relabeled", "kind_changed") if codes.get(k)]
                if not kinds:
                    real.pop("codes")
            what = ("current" if m == chain.last else
                    ", ".join(k.replace("_", " ") for k in real) or f"same as {cur_rel}")
            if self.index.corrected.get(m):
                what += ' <span class="corrected">corrected</span>'
            rows.append([self.link(here, self.release_path(rel, tab), rel), f"<code>{esc(name)}</code>",
                         esc(availability_line(rec, self.waves[rel], self.dim_label("form"))), what])
            if real:
                parts = []
                for field in ("label", "question", "universe", "description"):
                    if field in real:
                        before = real[field]["from"]
                        before = universe_text(before) if field == "universe" else before
                        parts.append((field.capitalize(), text_block(before or "")))
                if rec.get("values") or current.get("values"):
                    diff_items = code_diff(rec.get("values") or [], current.get("values") or [])
                    if diff_items != ["order or other code fields changed"]:
                        parts.append((f"Codes, compared with {esc(cur_rel)}",
                                      '<ul class="diff">' + "".join(f"<li>{d}</li>" for d in diff_items) + "</ul>"))
                if "valid_range" in real:
                    parts.append(("Valid range", "<br>".join(
                        esc(range_text(r)) for r in valid_ranges({"valid_range": real["valid_range"].get("from")})) or "none"))
                for field in ("measure", "implied_decimals"):
                    if field in real:
                        parts.append((field.replace("_", " ").capitalize(), esc(real[field].get("from"))))
                details.append(f"<details><summary>{esc(rel)}: {esc(name)}, what differs from "
                               f"{esc(cur_rel)}</summary>" + dl(parts) + "</details>")
        out = []
        if len(chain.members) > 1:
            out += [table(["Release", "Name", self.dim_label("wave") + "s", "Differs from " + cur_rel], rows)]
            out += details
        return "\n".join(out)

    def lineage_section(self, here, lineage):
        """The variable's runs: releases with the same meaning, oldest first, and the change
        between runs (the link's relations and evidence). The record above is the latest run's."""
        from .chains import names_text, span
        latest = lineage.latest
        out = ["<h2>Releases</h2>"]
        if len(lineage.chains) == 1:
            out.append("<p>This variable in each release, joined by the links between releases. "
                       f"The record above is {esc(latest.last[0])}'s; the rest list only what differs.</p>")
            out.append(self.releases_section(here, latest))
            return "\n".join(out)
        out.append(f"<p>This variable runs over {len(lineage.chains)} spans of releases. Within a span "
                   "the links say the meaning stayed the same; between spans, a link says what changed. "
                   f"The record above is {esc(latest.last[0])}'s.</p>")
        for chain in lineage.chains:
            for link, earlier in lineage.changes(chain):
                out.append(self.change_between(link, earlier, chain))
            rels = [m[0] for m in chain.members]
            heading = f"{span(rels, self.order)}: {names_text(chain, self.order)}"
            out.append(f'<h3 class="run">{esc(heading)}' + (" (current)" if chain is latest else "") + "</h3>")
            if chain is not latest:
                rec = self.records[chain.last]
                if rec.get("label"):
                    out.append(f'<p class="label">{esc(rec["label"])}</p>')
                for q in rec.get("questions") or []:
                    out.append(text_block(q.get("text", "")))
                if rec.get("values"):
                    out.append('<p class="origin">Codes: ' + esc("; ".join(
                        f"{v.get('code')} {v.get('label') or ''}".strip() for v in rec["values"])) + "</p>")
                if valid_ranges(rec):
                    out.append('<p class="origin">Valid range: ' + esc("; ".join(
                        range_text(r) for r in valid_ranges(rec))) + "</p>")
            out.append(self.releases_section(here, chain))
        return "\n".join(out)

    def change_between(self, link, earlier, later):
        """One change between runs: the link's relations, origin, note and evidence."""
        rel_a, _, name_a = earlier.last
        rel_b, _, name_b = later.members[0]
        ev = "".join(f"<li>{esc(e.get('citation'))}"
                     + (f' — <a href="{esc(e["url"])}">{esc(e["url"])}</a>' if e.get("url") else "")
                     + (f'<blockquote>{esc(e["quote"])}</blockquote>' if e.get("quote") else "")
                     + "</li>" for e in link.get("evidence", []))
        parts = [f'<div class="change"><p><strong>Changed</strong> from {esc(rel_a)} ({esc(name_a)}) to '
                 f"{esc(rel_b)} ({esc(name_b)}): {esc(', '.join(link['relations']))} "
                 f'<span class="origin">{esc(origin_text(link["origin"]))}</span></p>']
        if link.get("note"):
            parts.append(f"<p>{esc(link['note'])}</p>")
        if ev:
            parts.append(f"<ul>{ev}</ul>")
        return "".join(parts) + "</div>"

    def alias_page(self, path, target):
        """A page at an older name that sends the reader to the variable's page."""
        depth = path.count("/")
        href = "../" * depth + target
        name = path.rsplit("/", 1)[-1].removesuffix(".html")
        self.write(path, f"""<!-- Generated by pdt {__version__} from inputs sha256:{self.digest}. Do not edit; run `make views`. -->
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={href}">
<title>{esc(name)}</title><link rel="canonical" href="{href}"></head>
<body><p>{esc(name)} is an earlier name of this variable: <a href="{href}">{esc(target)}</a>.</p></body></html>
""")

    def changed_pairs(self):
        """Adjacent releases with any difference: a variable added, removed or changed."""
        if not hasattr(self, "_changed_pairs"):
            releases = release_order(self.ds)
            self._changed_pairs = [(a, b) for a, b in zip(releases, releases[1:]) if any(self.changes(a, b))]
        return self._changed_pairs

    def changes(self, old, new):
        """(added, removed, changed) between two releases, by name and table."""
        def records(rel):
            return {(t, rec["name"]): rec for r, t, rec in self.index.entries if r == rel}
        a, b = records(old), records(new)
        added = sorted(set(b) - set(a), key=str)
        removed = sorted(set(a) - set(b), key=str)
        changed = []
        for k in sorted(set(a) & set(b), key=str):
            fields = [f for f in ("label", "questions", "values", "universe", "description")
                      if a[k].get(f) != b[k].get(f)]
            if fields:
                changed.append((k, fields))
        return added, removed, changed

    def availability_table(self, rec, all_waves):
        """Waves down, forms (and other dimensions) across; cells hold n when known.

        Release waves inside the variable's span that it skipped get a row too, so a
        gap reads as "not in this wave", not as a missing survey.
        """
        cols, cells = [], {}
        for a in rec["availability"]:
            col = ", ".join(f"{self.dim_label(d)} {a[d]}" for d in AVAIL_DIMS if d in a)
            col = col or "all"
            if col not in cols:
                cols.append(col)
            cells[(a.get("wave"), col)] = a.get("n")
        cols.sort(key=lambda c: (c != "all", c))
        present = {w for w, _ in cells if w is not None}
        order = [w for w in all_waves if w in present]
        span = all_waves[all_waves.index(order[0]):all_waves.index(order[-1]) + 1] if order else []
        waves = span + ([None] if (None, "all") in cells or any(w is None for w, _ in cells) else [])
        rows = []
        for w in waves:
            if w is not None and w not in present:
                rows.append([esc(w), f'<span class="origin gap">not in this {esc(self.dim_label("wave"))}</span>']
                            + [""] * (len(cols) - 1))
                continue
            row = [esc(w if w is not None else "-")]
            for c in cols:
                if (w, c) in cells:
                    n = cells[(w, c)]
                    row.append(f"{n:,}" if isinstance(n, int) else "✓")
                else:
                    row.append("")
            rows.append(row)
        note = '<p class="origin">Cells give the number of non-missing responses when known.</p>'
        return table([self.dim_label("wave")] + cols, rows, numeric=True) + note

    def history_table(self, h):
        """The publisher's code history (STANDARD.md §5.4): periods across, attributes down."""
        def period(p):
            if "to" not in p:
                return f"{p['from']}–"
            return str(p["from"]) if p["to"] == p["from"] else f"{p['from']}–{p['to']}"
        rows = [[esc(a["label"])] + [f"<code>{esc(c)}</code>" if c is not None else "—" for c in a["codes"]]
                for a in h.get("attributes", [])]
        parts = [f"<h2>Code history</h2><p>Codes by {esc(self.dim_label('wave'))} range, as the "
                 f"publisher documents them; — where it shows none. "
                 f'<span class="origin">{esc(origin_text(h["origin"]))}'
                 f'{", " + esc(h["origin"]["location"]) if h["origin"].get("location") else ""}</span></p>']
        renamed = [n for n in h.get("names", []) if n.get("name") != h["name"]]
        if renamed:
            parts.append(dl([("Earlier names", esc("; ".join(
                f"{n['name']} ({period(n['waves'])})" for n in renamed)))]))
        if h.get("note"):
            parts.append(f"<p>{esc(h['note'])}</p>")
        parts.append(table(["Attribute"] + [period(p) for p in h.get("periods", [])], rows))
        return "\n".join(parts)

    def links_for(self, rel, tab, name, here=None, skip=()):
        """Links from or to this record that leave its page (renames and continuations are the page)."""
        out = []
        here = here or self.var_path(rel, tab, name)
        for link in self.repo.links:
            for this, other in (("from", "to"), ("to", "from")):
                ref = link[this]
                if ref.get("name") == name and ref.get("release") == rel and ref.get("table") in (None, tab):
                    o = link[other]
                    target = self.var_path(o["release"], o.get("table"), o["name"])
                    text = f"{o['release']}: {o['name']}"
                    exists = (o["release"], o.get("table"), o["name"]) in self.page_of
                    if exists and self.var_path(o["release"], o.get("table"), o["name"]) in {here, *skip}:
                        continue                                  # this variable (Releases) or a related one
                    a = self.link(here, target, text) if exists else esc(text)
                    out.append(f"<li>{a} — {esc(', '.join(link['relations']))} "
                               f'<span class="origin">{esc(origin_text(link["origin"]))}</span></li>')
        return out

    def group_page(self, g):
        here = self.group_path(g["id"])
        body = [dl([("Kind", esc(g["kind"])), ("Id", f"<code>{esc(g['id'])}</code>"),
                    ("Origin", esc(origin_text(g["origin"]))
                     + (f"<br>{esc(g['origin']['note'])}" if g["origin"].get("note") else ""))]
                   + ([("Releases", esc(", ".join(g["releases"])))] if g.get("releases") else []))]
        if g.get("stem"):
            body.append("<h2>Shared stem</h2>" + text_block(g["stem"]))
        if g.get("parent"):
            body.append(dl([("Part of", self.link(here, self.group_path(g["parent"]), g["parent"]))]))
        rows = []
        for m in g["members"]:
            hits = [(r, t, rec) for r, t, rec in self.index.entries
                    if rec["name"] == m["name"] and m.get("release") in (None, r)
                    and m.get("table") in (None, t) and (not g.get("releases") or r in g["releases"])]
            for r, t, rec in hits:
                rows.append([self.link(here, self.var_path(r, t, rec["name"]), rec["name"]),
                             esc(rec.get("label")), esc(r + (f" / {t}" if t else "")),
                             esc(availability_line(rec, self.waves[r], self.dim_label("form")))])
            if not hits:
                rows.append([esc(m["name"]), "<em>no record in this repository</em>", "", ""])
        body.append(f"<h2>Members{' (in order)' if g.get('ordered') else ''}</h2>")
        body.append(table(["Name", "Label", "Release", self.dim_label("wave") + "s"], rows))
        self.page(here, g.get("label") or g["id"], "\n".join(body))

    def changes_page(self, old, new):
        here = f"changes/{old}--{new}.html"
        def records(rel):
            return {(t, rec["name"]): rec for r, t, rec in self.index.entries if r == rel}
        a, b = records(old), records(new)
        added, removed, changed = self.changes(old, new)
        def name(rel, k):
            t, n = k
            return self.link(here, self.var_path(rel, t, n), (f"{t}." if t else "") + n)
        body = [f"<p>Variables in {esc(new)} compared with {esc(old)}, by name"
                " (and table). Links between releases are on each variable's page.</p>"]
        body.append(f"<h2>Added ({len(added)})</h2><ul>" + "".join(f"<li>{name(new, k)}</li>" for k in added) + "</ul>")
        body.append(f"<h2>Removed ({len(removed)})</h2><ul>" + "".join(f"<li>{name(old, k)}</li>" for k in removed) + "</ul>")
        def show(rec, f):
            v = rec.get(f)
            if f == "questions":
                v = " / ".join(q.get("text", "") for q in v or [])
            elif f == "values":
                v = "; ".join(f"{c.get('code')} {c.get('label')}" for c in v or [])
            text = " ".join(str(v if v is not None else "—").split())
            return esc(text if len(text) <= 160 else text[:157] + "...")
        rows = []
        for k, fields in changed:
            for i, f in enumerate(fields):
                first = name(new, k) if i == 0 else ""
                if f == "values":
                    diff = code_diff(a[k].get("values") or [], b[k].get("values") or [])
                    rows.append([first, "codes", '<ul class="diff">' + "".join(
                        f"<li>{d}</li>" for d in diff) + "</ul>"])
                else:
                    rows.append([first, esc(f), f"{show(a[k], f)}<br>→ {show(b[k], f)}"])
        body.append(f"<h2>Changed ({len(changed)})</h2>" + table(
            ["Variable", "Field", f"{esc(old)} → {esc(new)}"], rows))
        self.page(here, f"Changes from {old} to {new}", "\n".join(body))

    def search_index(self):
        """One row per variable page: its latest name, label, releases and question text."""
        from .chains import names_text
        rows = []
        for lineage in self.lineages:
            chain = lineage.latest
            rel, tab, name = chain.last
            rec = self.records[chain.last]
            q = " ".join(q.get("text", "") for q in rec.get("questions") or [])
            names = ("; ".join(names_text(c, self.order) for c in lineage.chains)
                     if len(self.order) > 1 else rel)
            rows.append([name, rec.get("label") or "", (f"{tab}: " if tab else "") + names,
                         self.var_path(rel, tab, name), " ".join(q.split())[:400]])
        self.write("search-index.js", "window.PDT_INDEX = " + json.dumps(rows, ensure_ascii=False) + ";\n")


# ---------------------------------------------------------------- helpers

def code_diff(old, new):
    """Code-by-code differences between two value lists, as HTML list items."""
    def key(v):
        return (isinstance(v["code"], str), str(v["code"]))
    a, b = {key(v): v for v in old}, {key(v): v for v in new}
    out = []
    for k in sorted(set(a) | set(b), key=lambda k: (k[0], natural_code(k[1]))):
        x, y = a.get(k), b.get(k)
        code = f"<code>{esc(k[1])}</code>"
        if x is None:
            out.append(f"added {code} {esc(y.get('label'))} <span class=\"origin\">{esc(y.get('kind'))}</span>")
        elif y is None:
            out.append(f"removed {code} {esc(x.get('label'))}")
        else:
            parts = []
            if x.get("label") != y.get("label"):
                parts.append(f"{esc(x.get('label'))} → {esc(y.get('label'))}")
            if x.get("kind") != y.get("kind") or x.get("missing_types") != y.get("missing_types"):
                kx = x.get("kind", "") + (f" ({', '.join(x['missing_types'])})" if x.get("missing_types") else "")
                ky = y.get("kind", "") + (f" ({', '.join(y['missing_types'])})" if y.get("missing_types") else "")
                parts.append(f"{esc(kx)} → {esc(ky)}")
            if parts:
                out.append(f"{code} " + "; ".join(parts))
    return out or ["order or other code fields changed"]


def natural_code(text):
    try:
        return (0, float(text), "")
    except ValueError:
        return (1, 0.0, text)


def availability_line(rec, all_waves, form_label="form"):
    """The agent view's wave summary, with the dataset's word for a form and room to wrap."""
    text = wave_summary(rec, all_waves)
    if form_label != "form":
        text = text.replace("form ", f"{form_label} ")
    return text.replace(",", ", ")


def mark(applied, field):
    return ' <span class="corrected">corrected</span>' if field in applied else ""


def dl(items):
    return "<dl>" + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in items) + "</dl>"


def table(headers, rows, numeric=False):
    cls = ' class="numeric"' if numeric else ""
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f'<div class="scroll"><table{cls}><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def build(root, out=None):
    """Write docs/ for the dataset repo at root. Returns the manifest."""
    root = Path(root)
    return Site(root, Path(out) if out else root / DIRECTORY).build()


def is_current(root):
    """True if docs/ was generated by this library version from the current inputs."""
    path = Path(root) / DIRECTORY / "manifest.json"
    if not path.exists():
        return False
    m = json.loads(path.read_text())
    return (m.get("pdt_version") == __version__ and m.get("inputs_sha256") == inputs_hash(root)
            and m.get("generator_sha256") == generator_hash())


SEARCH_JS = """
(function () {
  var q = document.getElementById('q'), hits = document.getElementById('hits');
  var index = window.PDT_INDEX || [];
  function show() {
    var s = q.value.trim().toLowerCase();
    hits.innerHTML = '';
    if (!s) return;
    var exact = [], name = [], other = [];
    index.forEach(function (r) {
      var n = r[0].toLowerCase();
      if (n === s) exact.push(r);
      else if (n.indexOf(s) === 0) name.push(r);
      else if ((r[1] + ' ' + r[4]).toLowerCase().indexOf(s) >= 0) other.push(r);
    });
    exact.concat(name, other).slice(0, 50).forEach(function (r) {
      var li = document.createElement('li'), a = document.createElement('a');
      a.href = r[3]; a.textContent = r[0];
      li.appendChild(a);
      li.appendChild(document.createTextNode(' — ' + r[1] + ' (' + r[2] + ')'));
      hits.appendChild(li);
    });
  }
  q.addEventListener('input', show);
  q.addEventListener('keydown', function (e) {
    var first = hits.querySelector('a');
    if (e.key === 'Enter' && first) location.href = first.href;
  });
})();
"""

STYLE = """:root {
  --bg: #ffffff; --fg: #1d1d1f; --muted: #5f6368; --line: #dadce0; --accent: #1a5fb4;
  --head: #f3f4f6; --warn-bg: #fff4d6; --warn-fg: #7a4d00; --missing: #8a3b12;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #17181a; --fg: #e8e8ea; --muted: #a0a4ab; --line: #3a3d42; --accent: #8ab4f8;
    --head: #222428; --warn-bg: #3d2f0d; --warn-fg: #f5d68a; --missing: #f2a37b;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
nav, main, footer { max-width: 960px; margin: 0 auto; padding: 0 16px; }
nav { padding-top: 16px; color: var(--muted); font-size: 14px; }
footer { padding: 32px 16px; color: var(--muted); font-size: 13px; }
a { color: var(--accent); }
h1 { font-size: 28px; margin: 12px 0 4px; word-break: break-word; }
h2 { font-size: 20px; margin: 28px 0 8px; border-bottom: 1px solid var(--line); padding-bottom: 4px; }
h3 { font-size: 16px; margin: 16px 0 4px; }
.label { font-size: 18px; color: var(--muted); margin-top: 0; }
.text { white-space: pre-wrap; background: var(--head); padding: 8px 12px; border-radius: 6px; }
dl { display: grid; grid-template-columns: max-content 1fr; gap: 4px 16px; }
dt { color: var(--muted); }
dd { margin: 0; min-width: 0; overflow-wrap: anywhere; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { background: var(--head); position: sticky; top: 0; }
table.numeric td + td, table.numeric th + th { text-align: right; font-variant-numeric: tabular-nums; }
@media (max-width: 600px) {
  dl { grid-template-columns: 1fr; gap: 0; }
  dt { margin-top: 8px; }
}
code { font-size: 90%; }
.origin { color: var(--muted); font-size: 13px; }
.gap { white-space: nowrap; }
.num { font-variant-numeric: tabular-nums; }
ul.diff { margin: 0; padding-left: 18px; }
blockquote { margin: 4px 0 8px; padding: 4px 10px; border-left: 3px solid var(--line);
  color: var(--muted); white-space: pre-wrap; }
.corrected { background: var(--warn-bg); color: var(--warn-fg); font-size: 12px; padding: 1px 6px;
  border-radius: 4px; }
.kind-missing { color: var(--missing); }
.kind-unresolved { color: var(--warn-fg); background: var(--warn-bg); padding: 0 4px; }
.correction { border-left: 3px solid var(--warn-fg); padding-left: 12px; margin: 12px 0; }
input[type=search] { width: 100%; font-size: 16px; padding: 8px 10px; border: 1px solid var(--line);
  border-radius: 6px; background: var(--bg); color: var(--fg); }
#hits { padding-left: 20px; }
pre { overflow-x: auto; background: var(--head); padding: 8px; }
"""

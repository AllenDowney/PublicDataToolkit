"""Generate the LLM-facing view of a dataset repo, `agent/` (STANDARD.md §7).

    agent/index.md          what the dataset is, how the shards are organized, a table of shards
    agent/SKILL.md          how an agent should use the shards and label its answers
    agent/manifest.json     library version, input hash and every file written, for code
    agent/shards/<kind>/<slug>.jsonl   one record per line, corrections applied
    agent/shards/<kind>/<slug>.txt     one line per variable, for reading

Every shard is the result of a search filter (search.py), so it carries the filter and
the completeness label the search assigns. The first line of each JSONL shard is
{"shard": {...}} with that information; the .txt form has it in `#` header lines.

Shards are split into parts when one would exceed about MAX_TOKENS tokens, estimated
as characters / 4.
"""

import hashlib
import json
import re
import shutil
from pathlib import Path

from . import __version__
from .check import Repo
from .search import Index, search

MAX_TOKENS = 20_000
CHARS_PER_TOKEN = 4
QUESTION_CHARS = 200

KIND_TITLES = {
    "table": "By release and table",
    "group": "By group",
    "scale": "By scale signature",
    "subject": "By publisher subject",
    "topic": "By annotation (approximate)",
}


def inputs_hash(root):
    """SHA-256 over dataset.yaml and everything under metadata/."""
    root = Path(root)
    h = hashlib.sha256()
    paths = [root / "dataset.yaml"] + sorted(p for p in (root / "metadata").rglob("*") if p.is_file())
    for p in paths:
        h.update(str(p.relative_to(root)).encode() + b"\0")
        h.update(p.read_bytes() + b"\0")
    return h.hexdigest()


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-") or "x"


def tokens(text):
    return -(-len(text) // CHARS_PER_TOKEN)


# ---------------------------------------------------------------- shard specs

STATUS_ORDER = {"withdrawn": 0, "superseded": 1, "current": 2}


def release_order(dataset):
    """Release ids oldest first: withdrawn and superseded before current; file order within a status."""
    releases = dataset.get("releases", [])
    ranked = sorted(enumerate(releases), key=lambda ir: (STATUS_ORDER.get(ir[1].get("status"), 3), ir[0]))
    return [r["id"] for _, r in ranked]


def default_scope(dataset):
    """The releases that cross-cutting shards cover: the current ones, when a repo has several."""
    releases = dataset.get("releases", [])
    if len(releases) < 2:
        return None
    current = [r["id"] for r in releases if r.get("status") == "current"]
    return current or None


def shard_specs(repo, index):
    """Every shard to write: [(kind, slug, title, basis, filter)].

    Release and table shards cover each release. Group, subject, scale and topic shards
    cover the current release(s) when the repo has several, so a variable appears once.
    """
    specs = []
    scope = default_scope(repo.dataset)
    scoped = (lambda f: {"release": scope if len(scope) > 1 else scope[0], **f}) if scope else (lambda f: f)
    note = f" in the current release ({', '.join(scope)})" if scope else ""
    for r in repo.dataset.get("releases", []):
        tables = [t["id"] for t in r.get("tables") or []]
        if tables:
            for t in tables:
                specs.append(("table", slug(f"{r['id']}-{t}"), f"Release {r['id']}, table {t}",
                              "every variable in the table", {"release": r["id"], "table": t}))
        else:
            specs.append(("table", slug(r["id"]), f"Release {r['id']}",
                          "every variable in the release", {"release": r["id"]}))

    for g in repo.groups:
        origin = g["origin"].get("source") or g["origin"]["origin"]
        title = g.get("label") or g["id"]
        if g["kind"] == "subject":
            specs.append(("subject", slug(title), f"Subject: {title}",
                          f"the publisher's subject list, from {origin}{note}", scoped({"subject": title})))
        else:
            specs.append(("group", slug(g["id"]), f"{g['kind']}: {title}",
                          f"members of group {g['id']} (origin {g['origin']['origin']}){note}",
                          scoped({"group": g["id"]})))

    signatures = sorted({d["value"] for d in repo.derived if d["property"] == "scale_signature"},
                        key=str)
    for s in signatures:
        specs.append(("scale", slug(s), f"Scale signature: {s}",
                      f"variables with this scale signature{note}",
                      scoped({"derived": {"scale_signature": s}})))

    by_value = {}
    for a in index.topics:
        by_value.setdefault(a["value"].lower(), []).append(a)
    for _, tags in sorted(by_value.items()):
        value = tags[0]["value"]
        sources = sorted({a["origin"].get("source") or a["origin"]["origin"] for a in tags})
        specs.append(("topic", slug(value), f"Topic: {value}",
                      f"topic annotations from {', '.join(sources)}{note}", scoped({"topic": value})))
    return specs


# ---------------------------------------------------------------- rendering

def runs(waves, all_waves):
    """Waves as runs over the release's ordered waves: 1972-1985,1987-2024."""
    order = [w for w in all_waves if w in waves]
    if not order:
        return "-"
    pos = {w: i for i, w in enumerate(all_waves)}
    out, start, prev = [], order[0], order[0]
    for w in order[1:]:
        if pos[w] == pos[prev] + 1:
            prev = w
            continue
        out.append((start, prev))
        start = prev = w
    out.append((start, prev))
    return ",".join(str(a) if a == b else f"{a}-{b}" for a, b in out)


MAX_GAPS_NAMED = 3


def wave_summary(record, all_waves):
    """A record's waves for the line form: runs by form, and the waves missing in its span.

    "1972-1985,1987-2024 (not 1986)" when every entry has only a wave;
    "all 1972-1987; form A,C 1988-2024 (not 1986)" when forms differ by wave.
    """
    avail = record.get("availability") or []
    waves = {a["wave"] for a in avail if "wave" in a}
    if not waves:
        return "-"
    compact = compact_availability(avail, all_waves)
    if list(compact) == ["all"]:
        text = compact["all"]
        if len(waves) == len(all_waves) and len(all_waves) > 1:
            return text + " (all)"
    else:
        by_runs = {}
        for key, r in compact.items():
            by_runs.setdefault(r, []).append(key)
        pieces = []
        for r, keys in by_runs.items():
            forms = [k[len("form "):] for k in keys if k.startswith("form ") and "," not in k]
            others = [k for k in keys if k not in {f"form {f}" for f in forms}]
            labels = others + ([f"form {','.join(forms)}"] if forms else [])
            pieces.append(f"{'; '.join(labels)} {r}" if len(labels) == 1
                          else f"{' / '.join(labels)} {r}")
        text = "; ".join(pieces)
    order = [w for w in all_waves if w in waves]
    lo, hi = all_waves.index(order[0]), all_waves.index(order[-1])
    gaps = [w for w in all_waves[lo:hi + 1] if w not in waves]
    if gaps:
        named = ",".join(map(str, gaps)) if len(gaps) <= MAX_GAPS_NAMED else f"{len(gaps)} waves"
        text += f" (not {named})"
    return text


AVAIL_DIMS = ("form", "sample", "mode", "phase")


def compact_availability(availability, all_waves):
    """Availability as runs of waves, keyed by the other dimensions.

    {"all": "1972-1987"} for entries with only a wave; {"form A": "1988-2024", ...} for the
    rest. Counts (`n`) are dropped; the full records keep them.
    """
    groups = {}
    for a in availability or []:
        key = ", ".join(f"{d} {a[d]}" for d in AVAIL_DIMS if d in a) or "all"
        groups.setdefault(key, set())
        if "wave" in a:
            groups[key].add(a["wave"])
    return {k: runs(v, all_waves) if v else "-" for k, v in groups.items()}


def origin_text(origin):
    """One origin as a short string: upstream_package:gssrdoc-json, rule:gssrdoc_text@0.1."""
    kind = origin.get("origin", "?")
    if kind == "rule":
        return f"rule:{origin.get('rule')}@{origin.get('rule_version')}"
    if kind in ("hand", "model"):
        who = origin.get("author") or origin.get("model")
        text = f"{kind}:{who}" if who else kind
        if kind == "model" and not origin.get("reviewed"):
            text += " (unreviewed)"
        return text
    return f"{kind}:{origin['source']}" if origin.get("source") else kind


def compact_values(values, default):
    """Codes with their origins resolved: one shared origin, or one per code.

    A missing or unresolved code without its own origin takes the record's
    provenance.codes. Returns (values, shared origin text or None).
    """
    resolved = []
    for v in values:
        origin = v.get("origin") or (default if v.get("kind") != "valid" else None)
        resolved.append((v, origin))
    texts = {origin_text(o) for _, o in resolved if o}
    shared = texts.pop() if len(texts) == 1 else None
    out = []
    for v, o in resolved:
        c = {k: val for k, val in v.items() if k != "origin"}
        if o and shared is None:
            c["origin"] = origin_text(o)
            if o.get("note"):
                c["origin_note"] = o["note"]
        out.append(c)
    return out, shared


def wave_list(waves):
    """All of a release's waves as runs of consecutive integers, e.g. 1972-1978,1980."""
    if not waves:
        return "none recorded"
    runs, start, prev = [], waves[0], waves[0]
    for w in waves[1:]:
        if isinstance(w, int) and isinstance(prev, int) and w == prev + 1:
            prev = w
            continue
        runs.append((start, prev))
        start = prev = w
    runs.append((start, prev))
    return ",".join(str(a) if a == b else f"{a}-{b}" for a, b in runs)


def when_text(when):
    """A reference's condition: "PER_TYP is 1, 2 or 9"."""
    if not when:
        return ""
    values = [str(v) for v in when.get("in", [])]
    listed = values[0] if len(values) == 1 else ", ".join(values[:-1]) + " or " + values[-1]
    return f"{when.get('column')} is {listed}"


def reference_text(ref):
    """A table reference in words: "ST_CASE, VEH_NO -> vehicle when PER_TYP is 3"."""
    target = ref.get("table", "?")
    if ref.get("dataset"):
        target = f"{ref['dataset']}:{target}"
    text = f"{', '.join(ref.get('columns', []))} -> {target}"
    if ref.get("when"):
        text += f" when {when_text(ref['when'])}"
    return text


def sort_key(value):
    return (isinstance(value, str), value)


STEM_CHARS = 60


def line_question(record):
    """The first wording, with a battery's shared stem shortened so the item text shows."""
    questions = record.get("questions") or []
    if not questions:
        for key in ("description", "notes"):
            text = record.get(key)
            if isinstance(text, list):
                text = " ".join(map(str, text))
            if text:
                return f"[{key}] {text}"
        return ""
    q = questions[0]
    if q.get("stem") and q.get("item"):
        stem = re.sub(r"\s+", " ", q["stem"]).strip()
        if len(stem) > STEM_CHARS:
            stem = stem[:STEM_CHARS - 3].rstrip() + "..."
        text = f"{stem} {q['item']}"
    else:
        text = q.get("text", "")
    if len(questions) > 1:
        text += f" [+{len(questions) - 1} other wording(s)]"
    return text


def one_line(release, table, record, ctx):
    name = record["name"]
    if table is not None:
        name = f"{table}.{name}"
    if ctx["multi_release"]:
        name = f"{release}/{name}"
    if (release, table, record["name"]) in ctx["index"].corrected:
        name += "*"
    waves = wave_summary(record, ctx["waves"][release])
    sig = ctx["signature"].get((release, table, record["name"]), "-")
    q = re.sub(r"\s+", " ", line_question(record)).strip()
    if len(q) > QUESTION_CHARS:
        q = q[:QUESTION_CHARS - 3].rstrip() + "..."
    return " | ".join([name, waves, str(sig), record.get("label") or "-", q or "-"])


def view_record(release, table, record, ctx):
    """The record as it appears in a JSONL shard: corrected, compact, with a `view` block.

    Compact (STANDARD.md §7): availability as runs by form, origins as short strings,
    and one origin for the codes when they share one. Notes on origins and the
    per-wave counts are left out; the full record in metadata/ is canonical.
    """
    key = (release, table, record["name"])
    out = {k: v for k, v in record.items() if k not in ("dataset", "release", "provenance")}
    if record.get("availability"):
        out["availability"] = compact_availability(record["availability"], ctx["waves"][release])
    prov = record.get("provenance") or {}
    origins = {"record": origin_text(prov["record"])} if prov.get("record") else {}
    origins.update({f: origin_text(o) for f, o in (prov.get("fields") or {}).items()})
    if record.get("values"):
        out["values"], shared = compact_values(record["values"], prov.get("codes"))
        if shared:
            origins["codes"] = shared
    out["origins"] = origins
    view = {"release": release}
    if table is not None:
        view["table"] = table
    applied = ctx["index"].corrected.get(key)
    if applied:
        view["corrected"] = applied
    derived = {d["property"]: d["value"] for d in ctx["repo"].derived
               if d["target"].get("variable") == record["name"]
               and d["target"].get("release") in (None, release)
               and d["target"].get("table") in (None, table)}
    if derived:
        view["derived"] = derived
    groups = [g["id"] for g in ctx["repo"].groups
              if any(m.get("name") == record["name"] and m.get("table") in (None, table)
                     and m.get("release") in (None, release) for m in g["members"])]
    if groups:
        view["groups"] = groups
    topics = sorted({a["value"] for a in ctx["index"].topics
                     if a["target"].get("variable") == record["name"]
                     and a["target"].get("release") in (None, release)
                     and a["target"].get("table") in (None, table)})
    if topics:
        view["topics"] = topics
    return {**out, "view": view}


def split(items, render, budget_tokens):
    """Split rendered items into parts of at most budget_tokens (at least one item each)."""
    parts, current, size = [], [], 0
    for item in items:
        text = render(item)
        t = tokens(text) + 1
        if current and size + t > budget_tokens:
            parts.append(current)
            current, size = [], 0
        current.append(text)
        size += t
    parts.append(current)
    return parts


# ---------------------------------------------------------------- build

def build(root, out=None):
    """Write agent/ for the dataset repo at root. Returns the manifest."""
    root = Path(root)
    out = Path(out) if out else root / "agent"
    repo = Repo.load(root)
    index = Index.from_repo(repo)
    digest = inputs_hash(root)

    waves = {}
    for rel, ts in repo.tables.items():
        found = {a["wave"] for recs in ts.values() for rec in recs
                 for a in rec.get("availability") or [] if "wave" in a}
        waves[rel] = sorted(found, key=sort_key)
    ctx = {
        "repo": repo,
        "index": index,
        "waves": waves,
        "multi_release": len(repo.tables) > 1,
        "signature": {},
    }
    for d in repo.derived:
        if d["property"] == "scale_signature":
            t = d["target"]
            for rel, tab, rec in index.entries:
                if (rec["name"] == t.get("variable") and t.get("release") in (None, rel)
                        and t.get("table") in (None, tab)):
                    ctx["signature"][(rel, tab, rec["name"])] = d["value"]

    if out.exists():
        if any(out.iterdir()) and not (out / "manifest.json").exists():
            raise FileExistsError(f"{out} exists and wasn't generated by pdt; not overwriting")
        shutil.rmtree(out)
    (out / "shards").mkdir(parents=True)

    header = {"pdt_version": __version__, "inputs_sha256": digest}
    shards = []
    for kind, name, title, basis, filt in shard_specs(repo, index):
        result = search(index, filt)
        meta = {
            "kind": kind,
            "title": title,
            "basis": basis,
            "full_records": full_records(repo, result),
            "completeness": result.label,
            "filter": filt,
            "releases": result.releases,
            "n_in_scope": result.n_in_scope,
            "rule_versions": result.rule_versions,
            "notes": result.notes,
            "count": len(result.matches),
        }
        directory = out / "shards" / kind
        directory.mkdir(exist_ok=True)
        files = []
        for form, render in [
            ("jsonl", lambda m: json.dumps(view_record(*m, ctx), ensure_ascii=False)),
            ("txt", lambda m: one_line(*m, ctx)),
        ]:
            parts = split(result.matches, render, MAX_TOKENS - 500)
            for i, lines in enumerate(parts, 1):
                part = {"part": i, "of": len(parts)} if len(parts) > 1 else {}
                stem = name if len(parts) == 1 else f"{name}.part{i}"
                path = directory / f"{stem}.{form}"
                if form == "jsonl":
                    first = json.dumps({"shard": {**meta, **part, **header}}, ensure_ascii=False)
                    text = "\n".join([first] + lines) + "\n"
                else:
                    text = txt_header(meta, part, header) + "\n".join(lines) + "\n"
                path.write_text(text)
                files.append({"path": str(path.relative_to(out)), "form": form,
                              "variables": len(lines), "tokens": tokens(text)})
        shards.append({**meta, "files": files})

    manifest = {**header, "dataset": repo.dataset.get("id"), "max_tokens": MAX_TOKENS,
                "shards": shards}
    (out / "index.md").write_text(render_index(repo, index, shards, header, ctx["waves"]))
    (out / "SKILL.md").write_text(render_skill(repo, header))
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    return manifest


def full_records(repo, result):
    """The metadata files that hold the full records of a result's variables."""
    paths = set()
    for rel, tab, _ in result.matches:
        base = f"metadata/releases/{rel}"
        paths.add(f"{base}/{tab}/variables.jsonl" if tab else f"{base}/variables.jsonl")
    return sorted(paths)


def is_current(root):
    """True if agent/ was generated by this library version from the current inputs."""
    path = Path(root) / "agent" / "manifest.json"
    if not path.exists():
        return False
    m = json.loads(path.read_text())
    return m.get("pdt_version") == __version__ and m.get("inputs_sha256") == inputs_hash(root)


def txt_header(meta, part, header):
    lines = [
        f"# {meta['title']}" + (f" (part {part['part']} of {part['of']})" if part else ""),
        f"# completeness: {meta['completeness']}  ({meta['basis']})",
        f"# filter: {json.dumps(meta['filter'], ensure_ascii=False)}",
        f"# {meta['count']} of {meta['n_in_scope']} variables in releases {', '.join(meta['releases'])}",
    ]
    if meta["rule_versions"]:
        lines.append("# rules: " + ", ".join(f"{k} {v}" for k, v in meta["rule_versions"].items()))
    for note in meta["notes"]:
        lines.append(f"# note: {note}")
    lines += [
        "# columns: name | waves by form (\"not\" = release waves it skipped) | scale signature | label | question text (else [description], else [notes]), truncated",
        "# name* = a field was corrected; the JSONL form says which, with the original",
        f"# generated by pdt {header['pdt_version']} from inputs sha256:{header['inputs_sha256'][:16]}; "
        "do not edit",
        "",
    ]
    return "\n".join(lines)


GENERATED = ("<!-- Generated by pdt {pdt_version} from inputs sha256:{inputs_sha256}. "
             "Do not edit; run `make views`. -->\n\n")


def render_index(repo, index, shards, header, waves):
    ds = repo.dataset
    terms = ds.get("terms", {})
    dims = ds.get("dimensions", {})
    out = [GENERATED.format(**header), f"# {ds.get('title', ds.get('id'))}: agent index\n"]
    if ds.get("description"):
        out.append(" ".join(ds["description"].split()) + "\n")
    out.append(f"Publisher: {ds.get('publisher', {}).get('name', '-')}. "
               f"Dataset id: `{ds.get('id')}`. Records follow PublicDataToolkit "
               f"standard {ds.get('standard_version', '?')}.\n")
    if terms:
        out.append(f"Terms: {terms.get('url', '-')}. LLM processing: "
                   f"`{terms.get('llm_processing', 'not recorded')}`.\n")
    if dims:
        out.append("Dimensions: " + "; ".join(
            f"`{k}` is the {v.get('label', k)}" for k, v in dims.items()) + ".\n")

    out.append("## Releases\n")
    out.append("| Release | Table | Variables | Label |\n|---|---|---|---|")
    for r in ds.get("releases", []):
        for tab, recs in repo.tables.get(r["id"], {}).items():
            out.append(f"| `{r['id']}` | {tab or '-'} | {len(recs)} | {r.get('label', '')} |")
    out.append("")
    for r in ds.get("releases", []):
        if not r.get("tables"):
            continue
        out.append(f"Tables in `{r['id']}`: the key identifies a row; a reference says which "
                   "columns join to another table, and when.\n")
        for t in r["tables"]:
            line = f"- `{t['id']}`: {t.get('label', '')}"
            if t.get("key"):
                line += f". Key: {', '.join(t['key'])}"
            refs = [reference_text(ref) for ref in t.get("references") or []]
            if refs:
                line += ". References: " + "; ".join(refs)
            out.append(line)
        out.append("")

    if index.corrected:
        out.append("## Corrections applied\n")
        out.append("These records had an error in the source documentation. The shards show the "
                   "corrected value; the JSONL `view.corrected` block gives the original, the "
                   "problem and the confidence.\n")
        for (rel, tab, name), applied in sorted(index.corrected.items(), key=lambda kv: str(kv[0])):
            for a in applied:
                out.append(f"- `{name}` {a['field']} ({a['confidence']}): {a['problem']}")
        out.append("")

    out.append("## How the shards are organized\n")
    out.append(
        "Every shard is the result of a filter over the records, and its header says which "
        "filter and what completeness label it supports. Each shard comes in two forms with the "
        "same variables: `.txt`, one line per variable, for scanning; and `.jsonl`, the "
        "records with corrections applied, for details. The first JSONL line is the shard's "
        "header (`{\"shard\": ...}`); every later line is a variable. A shard too big to read "
        f"at once (about {MAX_TOKENS:,} tokens) is split into parts.\n")
    out.append("The JSONL records are compact: `availability` maps each form (or `all`) to runs "
               "of waves, `origins` gives where each field came from as `kind:source` or "
               "`rule:name@version`, and `origins.codes` is the origin the codes share (a code "
               "lists its own when they differ). Per-wave counts and the notes on origins are "
               "left out. The full records in `metadata/` are canonical; each shard header's "
               "`full_records` names the files.\n")
    out.append("Line form: `name | waves by form | scale signature | label | question text`. "
               "A run like `1972-1978` means every wave of the release in that span. "
               "`1972-1985,1987-2024 (not 1986)` means the release has a 1986 wave and the "
               "variable wasn't in it. `all 1972-1987; form A,C 1988-2024` means everyone was "
               "asked through 1987 and only forms A and C from 1988. The release's waves "
               "are: " + "; ".join(f"`{rel}`: {wave_list(ws)}" for rel, ws in waves.items()) + ". "
               "A trailing `*` on a name means a field "
               "was corrected.\n")
    out.append("`SKILL.md` says how to label an answer drawn from these files.\n")

    for kind, title in KIND_TITLES.items():
        rows = [s for s in shards if s["kind"] == kind]
        if not rows:
            continue
        out.append(f"## {title}\n")
        out.append("| Shard | Variables | Completeness | Tokens (txt / jsonl) | Basis |")
        out.append("|---|---|---|---|---|")
        for s in rows:
            txt = [f for f in s["files"] if f["form"] == "txt"]
            js = [f for f in s["files"] if f["form"] == "jsonl"]
            link = txt[0]["path"]
            tok = f"{sum(f['tokens'] for f in txt):,} / {sum(f['tokens'] for f in js):,}"
            if len(js) > 1 or len(txt) > 1:
                tok += f" ({len(txt)} / {len(js)} parts)"
            out.append(f"| [{s['title']}]({link}) | {s['count']} | `{s['completeness']}` | "
                       f"{tok} | {s['basis']} |")
        out.append("")
    return "\n".join(out)


SKILL = """{generated}# Using the {title} metadata

These files describe the variables of {title} (`{id}`). Use them to find variables, read their
question text, codes and missing codes, and see which waves and forms asked them.

## Steps

1. Read `index.md`. It lists every shard with its size and the completeness label it supports.
2. Pick the shard that matches the question: a publisher subject, a group (battery, section),
   a scale signature, or the release/table shard for everything. Read its `.txt` form first.
3. For codes, missing codes, full question text and per-wave availability, read the same
   variables in the shard's `.jsonl` form.
4. Answer with the completeness label (below), and cite the shard and filter you used.

## Completeness labels

Every list of variables you report must say how it was produced, with one of these labels.
The label describes the method, not your confidence. Don't upgrade it.

| Label | When to use it |
|---|---|
| `complete` | You report exactly the variables of one shard whose header says `complete`, or a filter `pdt search` labeled `complete`. |
| `complete_by_rule` | The same, for a shard or search labeled `complete_by_rule`. Name the rules and versions from its header. |
| `approximate` | Anything else: you searched text, used `topic` (annotation) shards, combined or pruned shards by judgment, or picked variables by reading them. |

Combining shards keeps the worst label among them only if the combination is itself a filter
(an AND or OR of the shards' filters); state that filter. If you drop or add any variable by
judgment, the result is `approximate`.

With every result, give what's needed to rerun it: the release(s) in scope, the number of
variables in scope, the filter (from the shard header), and the rule versions.

A `complete` result is complete with respect to the records in scope: if the repo covers
part of a release, say so, using the scope in the shard header. Subject shards are complete
with respect to the publisher's own subject list, which may miss items a reader would
consider on-topic; say so when it matters. If a subject shard and a group shard give the
same variables, report the stronger label (`complete`, then `complete_by_rule`, then
`approximate`) and cite that shard.

## Searching with code

If the shared library is installed, `pdt search PATH --filter '<json>'` runs a filter and
prints a labeled result, e.g. `--filter '{{"subject": "Abortion"}}'`. Filter keys: `release`,
`table`, `name`, `group`, `subject`, `topic`, `derived`, `available`, `field`, `text`.
Several keys in one filter must all match.

For a question about when or to whom a variable was asked ("every item on form A in 1988",
"thermometers asked in 1978"), use `available`, not your own reading of the shards:

    pdt search PATH --filter '{{"available": {{"wave": 1988, "form": "A"}}}}'
    pdt search PATH --filter '{{"derived": {{"scale_signature": "thermometer"}}, "available": {{"wave": 1978}}}}'

`available` matches a variable with an availability entry for that wave on that form, or with
no form (everyone in that wave was asked); leave out `form` for "asked at all in that wave".
It is `complete` when availability comes from the publisher or the data file. Picking the
same variables by reading a shard gives the same list but is `approximate`, because you made
the selection; if you can't run `pdt search`, say so and label it `approximate`.

## Rules

- Names are as the publisher spells them{case_note}.
- Fields marked corrected (`*` in the line form, `view.corrected` in JSONL) differ from the
  source; mention the correction when you quote the text.
- Never treat an `approximate` source as complete: `topic` shards are annotations.
- These files are generated; don't edit them.
"""


def render_skill(repo, header):
    ds = repo.dataset
    naming = ds.get("naming", {})
    case_note = f" ({naming['case']}case in this dataset)" if naming.get("case") else ""
    return SKILL.format(generated=GENERATED.format(**header), title=ds.get("title", ds.get("id")),
                        id=ds.get("id"), case_note=case_note)

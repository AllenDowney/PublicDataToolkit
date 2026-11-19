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

def shard_specs(repo, index):
    """Every shard to write: [(kind, slug, title, basis, filter)]."""
    specs = []
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
                          f"the publisher's subject list, from {origin}", {"subject": title}))
        else:
            specs.append(("group", slug(g["id"]), f"{g['kind']}: {title}",
                          f"members of group {g['id']} (origin {g['origin']['origin']})",
                          {"group": g["id"]}))

    signatures = sorted({d["value"] for d in repo.derived if d["property"] == "scale_signature"},
                        key=str)
    for s in signatures:
        specs.append(("scale", slug(s), f"Scale signature: {s}",
                      "variables with this scale signature", {"derived": {"scale_signature": s}}))

    by_value = {}
    for a in index.topics:
        by_value.setdefault(a["value"].lower(), []).append(a)
    for _, tags in sorted(by_value.items()):
        value = tags[0]["value"]
        sources = sorted({a["origin"].get("source") or a["origin"]["origin"] for a in tags})
        specs.append(("topic", slug(value), f"Topic: {value}",
                      f"topic annotations from {', '.join(sources)}", {"topic": value}))
    return specs


# ---------------------------------------------------------------- rendering

def wave_summary(record, all_waves):
    """Compress a record's waves into runs over the release's ordered waves, plus forms."""
    avail = record.get("availability") or []
    waves = {a["wave"] for a in avail if "wave" in a}
    forms = sorted({str(a["form"]) for a in avail if "form" in a})
    if not waves:
        text = "-"
    else:
        order = [w for w in all_waves if w in waves]
        pos = {w: i for i, w in enumerate(all_waves)}
        runs, start, prev = [], order[0], order[0]
        for w in order[1:]:
            if pos[w] == pos[prev] + 1:
                prev = w
                continue
            runs.append((start, prev))
            start = prev = w
        runs.append((start, prev))
        text = ",".join(str(a) if a == b else f"{a}-{b}" for a, b in runs)
        if len(waves) == len(all_waves) and len(all_waves) > 1:
            text += " (all)"
    if forms:
        text += f"; forms {','.join(forms)}"
    return text


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


def sort_key(value):
    return (isinstance(value, str), value)


STEM_CHARS = 60


def line_question(record):
    """The first wording, with a battery's shared stem shortened so the item text shows."""
    questions = record.get("questions") or []
    if not questions:
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
    """The record as it appears in a JSONL shard: corrected, with a `view` block."""
    key = (release, table, record["name"])
    view = {}
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
    return {**record, "view": view}


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
        "# columns: name | waves; forms | scale signature | label | question text, truncated",
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
        "same variables: `.txt`, one line per variable, for scanning; and `.jsonl`, the full "
        "records with corrections applied, for details. The first JSONL line is the shard's "
        "header (`{\"shard\": ...}`); every later line is a variable. A shard too big to read "
        f"at once (about {MAX_TOKENS:,} tokens) is split into parts.\n")
    out.append("Line form: `name | waves; forms | scale signature | label | question text`. "
               "A run like `1972-1978` means every wave of the release in that span; a gap "
               "between runs (`1972-1985,1987-2024`) means the variable wasn't available in "
               "the waves between, even though the release has them. The release's waves "
               "are: " + "; ".join(f"`{rel}`: {wave_list(ws)}" for rel, ws in waves.items()) + ". "
               "`forms A,C` lists every form the variable was on in any wave; the JSONL "
               "`availability` gives wave by form. A trailing `*` on a name means a field "
               "was corrected.\n")
    out.append("Read `SKILL.md` before answering a question from these files.\n")

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
same variables, prefer the one with the better label and cite it.

## Searching with code

If the shared library is installed, `pdt search PATH --filter '<json>'` runs a filter and
prints a labeled result, e.g. `--filter '{{"subject": "Abortion"}}'`. Filter keys: `release`,
`table`, `name`, `group`, `subject`, `topic`, `derived`, `field`, `text`.

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

"""A catalog across dataset repos: `pdt catalog` and `pdt search --catalog`.

    pdt catalog ~ --out ~/pdt-catalog            every dataset repo under ~ (directories with dataset.yaml)
    pdt catalog ../pdt-gss ../pdt-nsfg --out DIR  just these
    pdt search --catalog ~ --filter '{"text": ["sad", "depress"]}'

Which repos go in: a directory is a dataset repo when it has dataset.yaml. One is
included only when its terms.metadata is `ship` and its records load; the others are
listed, with the reason, in the catalog's index and manifest. A `pdt-*` directory
without dataset.yaml is listed as left out, and nothing in it is read. Only metadata is
read: records, dataset.yaml, sources.yaml. No data file.

What it writes in --out:
    index.html              the datasets: title, publisher, kind, terms, releases, waves, variables
    agent/index.md          the same for agents, how to search, and what was left out
    agent/<dataset>.txt     one line per variable of the releases in scope, split at ~20k tokens:
                            release[/table].name | waves | label | question text, truncated
    catalog.jsonl           the same, one JSON object per variable
    manifest.json           pdt version, and each repo's path and input hash

Scope: each dataset's current releases (status current; all of them when none is
marked), since a superseded release repeats its successor. --all-releases includes all.

Search across repos runs pdt.search's filter in each repo and labels the result with
the weakest label any repo's part got (STANDARD.md §7): `complete` only if every
dataset's part is. A filter key a dataset doesn't have (a subject or group id) means no
match there, noted. `text` is a term or a list of terms (any of them), each matched at the
start of a word in the name, label or question text: "depress" finds "depressed" and
"depression", and "sad" doesn't find "disadvantaged". `text_in` limits where: any of
"name", "label", "question" (all three by default). A label says what a variable
measures; question text often mentions a concept in passing (185 GSS questions mention
marriage; a handful measure marital status). Text search is always approximate.
Subjects, groups and derived properties are each dataset's own: "Religion" in the GSS's
subject list says nothing about NSFG variables.
"""

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

from . import __version__
from .check import Repo
from .search import Index, question_text, search, worst
from .views import MAX_TOKENS, inputs_hash, line_question, sort_key, split, tokens, wave_list, wave_summary

QUESTION_CHARS = 160


# ---------------------------------------------------------------- repos

def discover(paths, skip=()):
    """Repos named, or found one level under a directory (skip: the catalog's own output)."""
    skip = {Path(p).expanduser().resolve() for p in skip}
    out = []
    for p in map(Path, paths):
        p = p.expanduser()
        if (p / "dataset.yaml").exists():
            out.append(p)
            continue
        if not p.is_dir():
            raise SystemExit(f"{p}: not a directory")
        for child in sorted(p.iterdir()):
            if child.resolve() in skip:
                continue
            if child.is_dir() and ((child / "dataset.yaml").exists() or child.name.startswith("pdt-")):
                out.append(child)
    seen, unique = set(), []
    for p in out:
        if p.resolve() not in seen:
            seen.add(p.resolve())
            unique.append(p)
    return unique


def load(paths, skip=()):
    """(included [(path, Repo)], left out [(path, reason)])."""
    included, left_out = [], []
    for path in discover(paths, skip):
        if not (path / "dataset.yaml").exists():
            left_out.append((path, "no dataset.yaml (not a dataset repo; nothing in it was read)"))
            continue
        try:
            ds = yaml.safe_load((path / "dataset.yaml").read_text())
        except Exception as e:                                   # report, don't stop the catalog
            left_out.append((path, f"dataset.yaml doesn't load: {e}"))
            continue
        terms = (ds.get("terms") or {}).get("metadata")
        if terms != "ship":
            left_out.append((path, f"terms.metadata is {terms!r}; only `ship` metadata goes in the catalog"))
            continue
        try:
            included.append((path, Repo.load(path)))
        except Exception as e:
            left_out.append((path, f"its records don't load: {type(e).__name__}: {e}"))
    return included, left_out


def releases_in_scope(dataset, all_releases=False):
    releases = [r["id"] for r in dataset.get("releases", [])]
    if all_releases:
        return releases
    current = [r["id"] for r in dataset.get("releases", []) if r.get("status") == "current"]
    return current or releases


def release_waves(repo):
    out = {}
    for rel, ts in repo.tables.items():
        found = {a["wave"] for recs in ts.values() for rec in recs
                 for a in rec.get("availability") or [] if "wave" in a}
        out[rel] = sorted(found, key=sort_key)
    return out


# ---------------------------------------------------------------- catalog

def entries(repo, all_releases=False):
    """One dict per variable of the releases in scope."""
    ds = repo.dataset
    waves = release_waves(repo)
    index = Index.from_repo(repo)
    scope = set(releases_in_scope(ds, all_releases))
    for rel, tab, rec in index.entries:
        if rel not in scope:
            continue
        q = " ".join(line_question(rec).split())
        yield {"dataset": ds["id"], "release": rel, "table": tab, "name": rec["name"],
               "label": rec.get("label"), "measure": rec.get("measure"),
               "waves": sorted({a["wave"] for a in rec.get("availability") or [] if "wave" in a}, key=sort_key),
               "waves_text": wave_summary(rec, waves[rel]),
               "question": q[:QUESTION_CHARS - 3] + "..." if len(q) > QUESTION_CHARS else q}


def line(entry):
    where = entry["release"] + (f"/{entry['table']}" if entry["table"] else "")
    return " | ".join([f"{where}.{entry['name']}", entry["waves_text"], entry["label"] or "-", entry["question"] or "-"])


def build(paths, out, all_releases=False):
    """Write the catalog in out. Returns the manifest."""
    out = Path(out).expanduser()
    included, left_out = load(paths, skip=[out])
    if out.exists():
        if any(out.iterdir()) and not (out / "manifest.json").exists():
            raise SystemExit(f"{out} exists and wasn't written by pdt catalog; not overwriting")
        for child in out.iterdir():
            if child.name != ".git":
                shutil.rmtree(child) if child.is_dir() else child.unlink()
    (out / "agent").mkdir(parents=True, exist_ok=True)

    datasets, all_entries = [], []
    for path, repo in included:
        ds = repo.dataset
        rows = list(entries(repo, all_releases))
        all_entries += rows
        parts = split(rows, line, MAX_TOKENS - 500)
        files = []
        for i, lines in enumerate(parts, 1):
            name = f"{ds['id']}.txt" if len(parts) == 1 else f"{ds['id']}.part{i}.txt"
            text = (f"# {ds.get('title', ds['id'])}" + (f" (part {i} of {len(parts)})" if len(parts) > 1 else "")
                    + f"\n# columns: release[/table].name | waves | label | question text, truncated"
                    + f"\n# generated by pdt {__version__} from {path}; do not edit\n" + "\n".join(lines) + "\n")
            (out / "agent" / name).write_text(text)
            files.append({"path": f"agent/{name}", "variables": len(lines), "tokens": tokens(text)})
        waves = release_waves(repo)
        scope = releases_in_scope(ds, all_releases)
        datasets.append({
            "id": ds["id"], "title": ds.get("title"), "kind": ds.get("kind"), "path": str(path),
            "publisher": (ds.get("publisher") or {}).get("name"),
            "terms": {k: (ds.get("terms") or {}).get(k) for k in ("url", "data", "metadata", "llm_processing")},
            "wave_label": ((ds.get("dimensions") or {}).get("wave") or {}).get("label", "wave"),
            "releases": [{"id": r, "status": next((x.get("status") for x in ds["releases"] if x["id"] == r), None),
                          "waves": wave_list(waves.get(r, [])).replace(",", ", "),
                          "variables": sum(len(v) for v in repo.tables.get(r, {}).values())} for r in scope],
            "variables": len(rows), "files": files, "inputs_sha256": inputs_hash(path),
        })
    with open(out / "catalog.jsonl", "w") as f:
        for row in all_entries:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest = {"pdt_version": __version__, "all_releases": all_releases, "datasets": datasets,
                "left_out": [{"path": str(p), "reason": r} for p, r in left_out]}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    (out / "agent" / "index.md").write_text(render_index(manifest))
    (out / "index.html").write_text(render_html(manifest))
    return manifest


def render_index(m):
    out = [f"<!-- Generated by pdt {m['pdt_version']} catalog. Do not edit; rerun `pdt catalog`. -->", "",
           "# Catalog of PublicDataToolkit datasets", "",
           "One line per variable of each dataset's "
           + ("releases" if m["all_releases"] else "current releases")
           + ", for finding which datasets have a concept and in which waves. Each dataset's own "
             "`agent/` in its repo has the full records, shards and completeness labels.", "",
           "| Dataset | Kind | Releases | Waves | Variables | File(s), tokens |", "|---|---|---|---|---|---|"]
    for d in m["datasets"]:
        files = ", ".join(f"[{Path(f['path']).name}]({Path(f['path']).name}) ({f['tokens']:,})" for f in d["files"])
        rels = ", ".join(f"`{r['id']}`" for r in d["releases"])
        waves = "; ".join(f"{r['waves']}" for r in d["releases"])
        out.append(f"| {d['title']} (`{d['id']}`) | {d['kind'] or '-'} | {rels} | {d['wave_label']}s {waves} "
                   f"| {d['variables']:,} | {files} |")
    out += ["", "## Searching", "",
            "Read the line files with grep, or search with the library across the repos:", "",
            "    pdt search --catalog ~ --filter '{\"text\": [\"sad\", \"depress\"]}'", "",
            "The result carries a completeness label, as in each repo (`complete`, `complete_by_rule`, "
            "`approximate`); across datasets it is the weakest of the datasets' labels. Text search is "
            "always `approximate`. Subjects, groups and scale signatures are each dataset's own, so a "
            "subject filter finds only datasets whose publisher uses that subject.", "",
            "A concept can have different names in different datasets (\"sad or hopeless\" vs "
            "\"depressed\"; MARSTAT vs marital), so search for several terms and read the lines.", ""]
    if m["left_out"]:
        out += ["## Left out", "", "| Repo | Why |", "|---|---|"]
        out += [f"| `{x['path']}` | {x['reason']} |" for x in m["left_out"]]
        out.append("")
    return "\n".join(out)


def render_html(m):
    e = html.escape
    rows = []
    for d in m["datasets"]:
        rels = "<br>".join(f"<code>{e(r['id'])}</code> ({e(str(r['status']))}): {e(d['wave_label'])}s "
                           f"{e(r['waves'])}, {r['variables']:,} variables" for r in d["releases"])
        terms = d["terms"]
        rows.append(f"<tr><td><strong>{e(d['title'] or d['id'])}</strong><br><code>{e(d['id'])}</code></td>"
                    f"<td>{e(d['publisher'] or '')}</td><td>{e(d['kind'] or '')}</td>"
                    f"<td>{rels}</td>"
                    f"<td><a href=\"{e(terms.get('url') or '')}\">terms</a><br>data: {e(str(terms.get('data')))}"
                    f"<br>metadata: {e(str(terms.get('metadata')))}</td>"
                    f"<td><a href=\"file://{e(d['path'])}/docs/index.html\">site</a></td></tr>")
    left = "".join(f"<tr><td><code>{e(x['path'])}</code></td><td>{e(x['reason'])}</td></tr>" for x in m["left_out"])
    return f"""<!-- Generated by pdt {e(m['pdt_version'])} catalog. Do not edit; rerun `pdt catalog`. -->
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dataset catalog</title>
<style>
:root {{ --bg:#fff; --fg:#1d1d1f; --muted:#5f6368; --line:#dadce0; --head:#f3f4f6; --accent:#1a5fb4; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#17181a; --fg:#e8e8ea; --muted:#a0a4ab; --line:#3a3d42;
  --head:#222428; --accent:#8ab4f8; }} }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:16px/1.5 system-ui, sans-serif; }}
main {{ max-width:1100px; margin:0 auto; padding:16px; }}
a {{ color:var(--accent); }} .scroll {{ overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; font-size:14px; }}
th, td {{ text-align:left; padding:6px 8px; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ background:var(--head); }} p.note {{ color:var(--muted); }}
</style></head><body><main>
<h1>Dataset catalog</h1>
<p>Datasets built to the PublicDataToolkit standard whose metadata may be shared. Each links to its own site.
For agents: <a href="agent/index.md">agent/index.md</a>, and one line per variable in <code>agent/</code>.</p>
<div class="scroll"><table><thead><tr><th>Dataset</th><th>Publisher</th><th>Kind</th><th>Releases</th>
<th>Terms</th><th>Site</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
{('<h2>Left out</h2><div class="scroll"><table><thead><tr><th>Repo</th><th>Why</th></tr></thead><tbody>'
  + left + '</tbody></table></div>') if left else ''}
<p class="note">Generated by pdt {e(m['pdt_version'])}. Metadata only; no data.</p>
</main></body></html>
"""


# ---------------------------------------------------------------- search

def search_catalog(paths, filt, all_releases=False):
    """Run a filter in every included repo. Returns a dict like pdt search's, across datasets."""
    included, left_out = load(paths)
    labels, parts, notes, results, in_scope = [], [], [], [], 0
    filt = dict(filt)
    fields = filt.pop("text_in", ["name", "label", "question"])
    unknown = set(fields) - {"name", "label", "question"}
    if unknown:
        raise ValueError(f"text_in takes name, label and question, not {sorted(unknown)}")
    terms = filt.get("text")
    if isinstance(terms, str):
        terms = [terms]
    pattern = re.compile("|".join(r"\b" + re.escape(t) for t in terms), re.IGNORECASE) if terms else None
    for path, repo in included:
        ds = repo.dataset
        f = dict(filt)
        if "release" not in f:
            f["release"] = releases_in_scope(ds, all_releases)
        index = Index.from_repo(repo)
        f.pop("text", None)
        try:
            r = search(index, f)
            matches, result_label, n_scope, rule_versions = r.matches, r.label, r.n_in_scope, r.rule_versions
            if pattern:
                matches = [(rel, tab, rec) for rel, tab, rec in matches
                           if pattern.search(" ".join(
                               {"name": rec["name"], "label": rec.get("label") or "",
                                "question": question_text(rec)}[k] for k in fields))]
                result_label = "approximate"
        except ValueError as e:
            notes.append(f"{ds['id']}: {e}; no match there")
            continue
        labels.append(result_label)
        in_scope += n_scope
        parts.append({"dataset": ds["id"], "completeness": result_label, "count": len(matches),
                      "n_in_scope": n_scope, "rule_versions": rule_versions})
        results += [{"dataset": ds["id"], "release": rel, "table": tab, "name": rec["name"],
                     "label": rec.get("label")} for rel, tab, rec in matches]
    return {"completeness": worst(*labels) if labels else "complete", "filter": filt,
            "datasets": parts, "n_in_scope": in_scope, "notes": notes, "count": len(results),
            "results": results, "left_out": [{"path": str(p), "reason": r} for p, r in left_out]}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pdt catalog", description="Build a catalog across dataset repos.")
    parser.add_argument("paths", nargs="+", help="dataset repos, or directories holding them")
    parser.add_argument("--out", required=True, help="where to write the catalog (outside any repo)")
    parser.add_argument("--all-releases", action="store_true", help="include superseded releases too")
    args = parser.parse_args(argv)
    m = build(args.paths, args.out, args.all_releases)
    for d in m["datasets"]:
        print(f"  {d['id']:16} {d['variables']:7,} variables in {', '.join(r['id'] for r in d['releases'])}")
    for x in m["left_out"]:
        print(f"  left out {x['path']}: {x['reason']}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

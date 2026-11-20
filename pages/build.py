"""Build the toolkit's GitHub Pages site from the repository's own documents.

    python pages/build.py [--out _site]
    python pages/build.py --refresh-datasets ../pdt-*      # update pages/datasets.yaml

The pages are generated, not written by hand: the home page from README.md, the proposal,
the standard and the contribution guide from their files, the guides page from the step and
skill tables in instructions/README.md and skills/README.md, and the datasets page from
pages/datasets.yaml. Links to files that aren't pages go to the file on GitHub. Links to
internal working notes (planning/ and the project board) are dropped with the sentence that
holds them, since the site is public-facing; the build lists what it dropped.

Needs `markdown` and `pyyaml` (pip install markdown pyyaml).
"""

import argparse
import html
import posixpath
import re
import shutil
import sys
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "pages"
REPO_URL = "https://github.com/AllenDowney/PublicDataToolkit"

PAGES = {  # source file -> (page, nav title)
    "README.md": ("index.html", "Home"),
    "PROPOSAL.md": ("proposal.html", "Proposal"),
    "STANDARD.md": ("standard.html", "Standard"),
    "guides": ("guides.html", "Guides"),
    "datasets": ("datasets.html", "Datasets"),
    "CONTRIBUTING.md": ("contributing.html", "Contribute"),
}
INTERNAL = re.compile(r"^(planning/|PROJECT_BOARD\.md)")
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z*`\[(])")

dropped = []


# ---------------------------------------------------------------- markdown sources

def resolve(target, source):
    """A link target as a path from the repo root, or None for an external or anchor-only link."""
    if re.match(r"^[a-z]+:", target) or target.startswith("#"):
        return None
    path, _, anchor = target.partition("#")
    full = posixpath.normpath(posixpath.join(posixpath.dirname(source), path))
    if path.endswith("/"):
        full += "/"
    return full, anchor


def is_internal(target, source):
    r = resolve(target, source)
    return r is not None and bool(INTERNAL.match(r[0]))


def strip_internal(text, source):
    """Drop links to internal notes: a parenthetical that is only such a link, else its sentence."""
    out = []
    for line in text.splitlines():
        line = re.sub(r"\s*\(\[[^\]]*\]\(([^)\s]+)\)[^()]*\)",
                      lambda m: "" if is_internal(m.group(1), source) else m.group(0), line)
        if not any(is_internal(t, source) for _, t in LINK.findall(line)):
            out.append(line)
            continue
        prefix = re.match(r"^(\s*(?:[-*]|\d+\.)\s+|\s*)", line).group(0)
        body = line[len(prefix):]
        kept = []
        for sentence in SENTENCE_END.split(body):
            if any(is_internal(t, source) for _, t in LINK.findall(sentence)):
                dropped.append(f"{source}: {sentence.strip()}")
            else:
                kept.append(sentence)
        if kept:
            out.append(prefix + " ".join(kept))
    return "\n".join(out)


def rewrite_links(text, source):
    """Point links at the site's pages, or at the file on GitHub."""
    def repl(m):
        label, target = m.group(1), m.group(2)
        r = resolve(target, source)
        if r is None:
            return m.group(0)
        path, anchor = r
        if path in PAGES:
            return f"[{label}]({PAGES[path][0]}{'#' + anchor if anchor else ''})"
        kind = "tree" if path.endswith("/") or (ROOT / path).is_dir() else "blob"
        return f"[{label}]({REPO_URL}/{kind}/main/{path.rstrip('/')}{'#' + anchor if anchor else ''})"
    return LINK.sub(repl, text)


def render(text, source, toc=False):
    text = rewrite_links(strip_internal(text, source), source)
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"],
                           extension_configs={"toc": {"toc_depth": "2-3"}})
    body = md.convert(text)
    return body, (md.toc if toc else "")


def first_table(text):
    """The first markdown table in a file: its contiguous lines starting with '|'."""
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("|"))
    end = start
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    return "\n".join(lines[start:end])


# ---------------------------------------------------------------- pages

def page(name, title, body, toc=""):
    current = ' aria-current="page"'
    nav = " ".join(f'<a href="{p}"{current if p == name else ""}>{t}</a>' for p, t in PAGES.values())
    side = f'<aside class="toc"><h2>Contents</h2>{toc}</aside>' if toc else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · PublicDataToolkit</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header><a class="brand" href="index.html">PublicDataToolkit</a><nav>{nav} <a href="{REPO_URL}">GitHub</a></nav></header>
<div class="wrap{' with-toc' if toc else ''}">{side}<main>
{body}
</main></div>
<footer>Generated from the <a href="{REPO_URL}">PublicDataToolkit repository</a>.
Code under the MIT License; the standard, instructions and skills under CC BY 4.0.</footer>
</body>
</html>
"""


def guides_body():
    steps = (ROOT / "instructions" / "README.md").read_text()
    skills = (ROOT / "skills" / "README.md").read_text()
    text = "\n\n".join([
        "# Guides",
        "An agent, or a person, builds a dataset repository by following eight steps. Each step says "
        "what to do, which parts of the [standard](STANDARD.md) apply, what to check before moving on, "
        "and when to stop and ask a person.",
        "## The steps",
        rewrite_links(first_table(steps), "instructions/README.md"),
        "## Skills",
        "Skills for reading the source formats met so far: how to probe the source, the traps earlier "
        "builds hit, and how to verify against the data.",
        rewrite_links(first_table(skills), "skills/README.md"),
        "## The template",
        "A new dataset repository starts from the [Copier](https://copier.readthedocs.io/) template in "
        "[`templates/`](templates/), and `copier update` brings an existing one up to a later version. "
        "See [Contribute](CONTRIBUTING.md) for the commands.",
    ])
    return render(text, "guides.md")[0]


def datasets_body():
    data = yaml.safe_load((HERE / "datasets.yaml").read_text())
    rows = []
    for d in data["datasets"]:
        name = html.escape(d["title"])
        if d.get("site"):
            name = f'<a href="{html.escape(d["site"])}">{name}</a>'
        repo = (f'<a href="{html.escape(d["repo"])}"><code>pdt-{html.escape(d["id"])}</code></a>' if d.get("repo")
                else f'<code>pdt-{html.escape(d["id"])}</code><br><span class="muted">not yet published</span>')
        releases = d.get("releases", [])
        rel = f"{len(releases)}: {html.escape(', '.join(releases[:3]))}{', …' if len(releases) > 3 else ''}"
        rows.append(f"<tr><td>{name}</td><td>{html.escape(d['publisher'])}</td>"
                    f"<td>{html.escape(d.get('kind', ''))}</td><td>{rel}</td><td>{repo}</td></tr>")
    intro = render(data["intro"], "datasets.md")[0]
    return (f"<h1>Datasets</h1>\n{intro}\n<div class=\"scroll\"><table><thead><tr><th>Dataset</th>"
            f"<th>Publisher</th><th>Kind</th><th>Releases</th><th>Repository</th></tr></thead><tbody>"
            + "".join(rows) + "</tbody></table></div>")


def build(out):
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for source, (name, title) in PAGES.items():
        if source == "guides":
            body, toc = guides_body(), ""
        elif source == "datasets":
            body, toc = datasets_body(), ""
        else:
            body, toc = render((ROOT / source).read_text(), source, toc=source == "STANDARD.md")
        (out / name).write_text(page(name, title, body, toc))
    shutil.copy(HERE / "style.css", out / "style.css")
    (out / ".nojekyll").write_text("")
    print(f"{out}: {', '.join(p for p, _ in PAGES.values())}")
    for d in dropped:
        print(f"  dropped (links to internal notes): {d}")


# ---------------------------------------------------------------- datasets.yaml

def refresh_datasets(repos):
    """Update pages/datasets.yaml from each repo's dataset.yaml, keeping the repo and site links."""
    path = HERE / "datasets.yaml"
    data = yaml.safe_load(path.read_text())
    old = {d["id"]: d for d in data["datasets"]}
    new = []
    for repo in sorted(repos):
        f = Path(repo) / "dataset.yaml"
        if not f.exists():
            continue
        ds = yaml.safe_load(f.read_text())
        entry = {"id": ds["id"], "title": ds["title"], "publisher": ds["publisher"]["name"],
                 "kind": ds.get("kind", "survey"),
                 "releases": [str(r["id"]) for r in ds.get("releases", [])]}
        for key in ("repo", "site"):
            if old.get(ds["id"], {}).get(key):
                entry[key] = old[ds["id"]][key]
        new.append(entry)
    data["datasets"] = sorted(new, key=lambda d: d["title"].lower())
    intro = "intro: |\n" + "".join(f"  {line}\n" if line else "\n" for line in data["intro"].rstrip().splitlines())
    path.write_text(HEADER + intro
                    + yaml.safe_dump({"datasets": data["datasets"]}, sort_keys=False, allow_unicode=True, width=200))
    print(f"{path}: {len(new)} datasets")


HEADER = """# The dataset repositories listed on the site's Datasets page.
# Refreshed from each repo's dataset.yaml by `python pages/build.py --refresh-datasets ../pdt-*`,
# which keeps `repo` and `site`. Add those two by hand when a repository is published.
"""


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", default=str(ROOT / "_site"))
    p.add_argument("--refresh-datasets", nargs="+", metavar="REPO")
    args = p.parse_args(argv)
    if args.refresh_datasets:
        refresh_datasets(args.refresh_datasets)
    else:
        build(args.out)


if __name__ == "__main__":
    sys.exit(main())

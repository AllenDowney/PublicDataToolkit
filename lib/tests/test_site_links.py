"""Every internal link the site writes resolves to a file, as a browser decodes it (Task 77: pages
named NAME@release were written as NAME%40release.html, and their links decoded to a missing file)."""

import json
import re
from pathlib import Path
from urllib.parse import unquote, urldefrag

from pdt import site
from test_check import DATASET, VARIABLES, make_repo, write_jsonl

PUBLISHER = {"origin": "publisher", "source": "cb"}


def var(name, release, label=None):
    return {"dataset": "toy", "release": release, "name": name, "label": label or name,
            "questions": [{"text": f"{name}?"}], "provenance": {"record": PUBLISHER}}


def repo(tmp_path):
    ds = json.loads(json.dumps(DATASET))
    ds["releases"] = [{"id": "r1", "label": "One", "status": "superseded", "sources": ["cb"]},
                      {"id": "r2", "label": "Two", "status": "current", "sources": ["cb"]}]
    r1 = [var("q1", "r1", "Old item"), var("odd!name", "r1"), var("a/b c", "r1"), VARIABLES[1] | {"release": "r1"}]
    r2 = [var("q1", "r2", "New item"), var("odd!name", "r2"), var("a/b c", "r2")]
    root = make_repo(tmp_path, dataset=ds, variables=r1, groups=[], corrections=[])
    write_jsonl(root / "metadata" / "releases" / "r2" / "variables.jsonl", r2)
    # odd!name and a/b c continue; q1 is reused for a different item, so its r1 page is q1@r1
    links = [{"from": {"release": "r1", "name": n}, "to": {"release": "r2", "name": n}, "relations": ["same_item"],
              "origin": {"origin": "hand", "author": "Tester", "date": "2026-11-20"}} for n in ("odd!name", "a/b c")]
    write_jsonl(root / "metadata" / "links.jsonl", links)
    return root


def targets(page, text):
    """Every internal link on a page: hrefs, the meta refresh, and the search index's paths."""
    out = [h for h in re.findall(r'href="([^"]+)"', text)]
    out += re.findall(r'url=([^"]+)"', text)
    return [h for h in out if not re.match(r"[a-z]+:", h) and not h.startswith("#")]


def test_every_internal_link_resolves(tmp_path):
    root = repo(tmp_path)
    m = site.build(root, repo_url="")
    docs = root / "docs"
    names = {f for f in m["files"]}
    assert "variables/q1@r1.html" in names and "variables/odd!name.html" in names
    assert "variables/a%2Fb%20c.html" in names              # "/" and " " escaped in the file name
    for f in m["files"]:
        if not f.endswith(".html"):
            continue
        for h in targets(f, (docs / f).read_text()):
            path, _ = urldefrag(h)
            resolved = (docs / Path(f).parent / unquote(path)).resolve()
            assert resolved.exists(), f"{f}: {h} -> {resolved}"
    index = json.loads((docs / "search-index.js").read_text().split("=", 1)[1].rstrip().rstrip(";"))
    for row in index:
        assert (docs / unquote(row[3])).exists(), row[3]


def test_hrefs_keep_safe_characters():
    assert site.href("variables/q1@r1.html") == "variables/q1@r1.html"
    assert site.href("variables/a%2Fb%20c.html") == "variables/a%252Fb%2520c.html"
    assert site.file_name("odd!name") == "odd!name.html"

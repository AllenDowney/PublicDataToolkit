"""The About and Using this site pages, the nav links and the terms notice in every footer (Task 74)."""

import json

import pytest

from pdt import site, vocab
from pdt.site import md_blocks
from test_check import DATASET, make_repo, write_jsonl

NOTICE = "Source: Toy Publisher, Toy Survey. Not endorsed by Toy Publisher."


def dataset(**changes):
    d = json.loads(json.dumps(DATASET))
    d["terms"]["notice"] = NOTICE
    d["citation"] = "Toy Publisher. Toy Survey, 2024."
    d.update(changes)
    return d


@pytest.fixture
def root(tmp_path):
    r = make_repo(tmp_path, dataset=dataset())
    write_jsonl(r / "metadata" / "links.jsonl", [])
    return r


def build(root, **kw):
    kw.setdefault("repo_url", "")
    return site.build(root, **kw)


def read(root, path):
    return (root / "docs" / path).read_text()


def test_pages_exist_and_every_page_links_them(root):
    m = build(root)
    assert "about.html" in m["files"] and "using.html" in m["files"]
    pages = [f for f in m["files"] if f.endswith(".html")]
    for f in pages:
        text = read(root, f)
        up = "../" * f.count("/")
        assert f'<a href="{up}about.html">About</a>' in text, f
        assert f'<a href="{up}using.html">Using this site</a>' in text, f
        assert NOTICE in text.split("<footer>")[1], f            # the notice in every footer


def test_footer_without_notice_gives_the_terms_page(tmp_path):
    root = make_repo(tmp_path)
    build(root)
    assert 'Terms of use: <a href="https://example.org/terms">' in read(root, "index.html").split("<footer>")[1]


def test_about(root):
    build(root)
    text = read(root, "about.html")
    assert "isn't the publisher's site" in text and "makes no analysis decisions" in text
    assert f'<div class="notice-box">{NOTICE}</div>' in text
    assert "Toy Publisher. Toy Survey, 2024." in text and "pdt-toy, PublicDataToolkit metadata" in text
    assert vocab.TOOLKIT_URL in text
    assert "the issue tracker of the repository <code>pdt-toy</code>" in text
    assert "<h2>Notes</h2>" not in text


def test_about_urls_are_configurable(root):
    build(root, toolkit_url="https://example.org/pdt", repo_url="https://github.com/someone/pdt-toy")
    text = read(root, "about.html")
    assert "https://example.org/pdt" in text and vocab.TOOLKIT_URL not in text
    assert 'href="https://github.com/someone/pdt-toy/issues"' in text


def test_agent_notes_are_about_notes(root):
    (root / "AGENT_NOTES.md").write_text("# Rounds\n\n*By a tester.*\n\n- Rounds were **annual**:\n"
                                         "  1. first\n  2. second\n- See [NLS](https://example.org/nls).\n")
    build(root)
    text = read(root, "about.html")
    assert "<h2>Notes</h2>" in text and "<h3>Rounds</h3>" in text and "<em>By a tester.</em>" in text
    assert "<ol><li>first</li><li>second</li></ol>" in text and '<a href="https://example.org/nls">NLS</a>' in text
    assert "AGENT_NOTES.md" in read(root, "using.html")


def test_using_has_the_standard_vocabularies(root):
    build(root)
    text = read(root, "using.html")
    for table in (vocab.ORIGINS, vocab.MISSING_TYPES, vocab.COMPLETENESS, vocab.RELATIONS, vocab.KINDS):
        for row in table:
            assert f"{row[0]}</" in text, row[0]
    # counts from this repo: q1's code 9 is the one dk code
    row = text.split("<code>dk</code>")[1].split("</tr>")[0]
    assert row.rstrip().endswith("<td>1</td>")
    assert "<code>&lt;name&gt;__code</code>" in text and "pdt.data.rebuild" in text
    assert "agent/SKILL.md" in text and "from pdt.search import Index, search" in text


def test_using_data_section_follows_the_terms(tmp_path):
    for d in ("a", "b"):
        (tmp_path / d).mkdir()
    root = make_repo(tmp_path / "a", dataset=dataset())
    build(root)
    assert "let the common-format files be shared" in read(root, "using.html")
    d = dataset()
    d["terms"]["data"] = "build-only"
    root = make_repo(tmp_path / "b", dataset=d)
    build(root)
    text = read(root, "using.html")
    assert "don't let the data be shared here" in text and "scripts/extract.py" not in text
    (root / "scripts").mkdir()
    (root / "scripts" / "extract.py").write_text("")
    build(root)
    assert "python scripts/extract.py --release r1" in read(root, "using.html")


def test_md_blocks():
    assert md_blocks("Plain `x` and *it*.\n\nNext.") == "<p>Plain <code>x</code> and <em>it</em>.</p>\n<p>Next.</p>"
    assert md_blocks("```\n<a>\n```") == "<pre>&lt;a&gt;</pre>"
    assert md_blocks("- a\n  continued\n- b") == "<ul><li>a continued</li><li>b</li></ul>"


def test_vocab_is_a_generator_module():
    from pdt.views import GENERATOR_MODULES
    assert "vocab.py" in GENERATOR_MODULES

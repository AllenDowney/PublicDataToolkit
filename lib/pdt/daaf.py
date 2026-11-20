"""Export a dataset repo as a DAAF data-source skill (`pdt export daaf`; Task 68).

DAAF (https://github.com/DAAF-Contribution-Community/daaf) is a Claude Code framework for data
analysis. Each data source it knows is a skill, `.claude/skills/<domain>-data-source-<id>/`,
written to its template (agent_reference/DATA_SOURCE_SKILL_TEMPLATE.md):

    export/daaf/manifest.json                      library version, hashes and files, for C8
    export/daaf/<skill>/SKILL.md                   the 12 mandatory sections, in DAAF's order
    export/daaf/<skill>/references/columns*.md     one line per variable across releases
    export/daaf/<skill>/references/coded-values.md each set of non-valid codes, and unresolved codes
    export/daaf/<skill>/references/data-quality.md corrections, unresolved codes, revised data
    export/daaf/<skill>/references/variable-definitions*.md   groups, and changes across releases
    export/daaf/<skill>/references/analytical-context.md      releases, design, terms
    export/daaf/<skill>/references/agent/          a copy of agent/ (or of its index and .txt
                                                   shards, within AGENT_BUDGET), so the skill
                                                   stands alone

Rules (planning/tasks/task-68.md):
- Terms first: the export refuses (TermsError) unless terms.metadata and terms.documentation are
  `ship` (the skill copies question text) and terms.llm_processing is `allowed` (DAAF is an LLM
  framework). The terms notice heads SKILL.md's Terms of Use section and every reference file.
- No analysis decisions: generated text states what the records say. Quoted text (the
  publisher's, in blockquotes and tables of records) is the publisher's; `advice_lines` finds
  advice words in everything else, and the tests use it.
- Provenance: every file carries the generated header; the manifest records the inputs hash
  and this module's generator hash, which C8 compares where export/daaf/ exists.
- On request only: `pdt export daaf`, not part of `pdt views`. The skill name's prefix is
  dataset.yaml's `domain`, or `--domain`.
"""

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path

from . import __version__
from .chains import CHANGED_MEANING, build as build_chains, lineages, names_text, span
from .check import Repo
from .common_format import CODE_SUFFIX, PROCESSED, code_text, file_name
from .design import effective_design, replicate_columns, weight_names
from .export import MISSING_TYPES
from .search import Index
from .views import build as build_agent, generator_hash as views_generator_hash, inputs_hash, release_order, tokens, when_text

DIRECTORY = Path("export") / "daaf"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DESCRIPTION_CHARS = 1024
SKILL_MAX_LINES = 500
PART_TOKENS = 20_000            # a reference file longer than this is split into parts
AGENT_BUDGET = 2_000_000        # bytes of agent/ copied into the skill when the whole is larger
TOP_GROUPS = 20
LICENSE = ("CC-BY-4.0 for this repository's metadata and generated views; the publisher's "
           "terms apply to its data and documentation")

# Words that would make generated text an analysis decision. Quoted publisher text is exempt.
ADVICE = re.compile(r"\b(should|recommend\w*|exclude|drop|recode|avoid|always use|never use|"
                    r"do not use|don't use|must use|prefer)\b", re.I)


class TermsError(ValueError):
    """The dataset's terms don't allow this export."""


def generator_hash():
    """The views' generator hash, plus this module's source: C8 compares it for export/daaf/."""
    h = hashlib.sha256(views_generator_hash().encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def check_terms(dataset):
    """Raise TermsError naming each term that blocks the export."""
    terms = dataset.get("terms") or {}
    blocked = [f"terms.{k} is {terms.get(k, 'missing')!s}, not {need}"
               for k, need in (("metadata", "ship"), ("documentation", "ship"), ("llm_processing", "allowed"))
               if terms.get(k) != need]
    if blocked:
        raise TermsError("the DAAF export copies the documentation's text into an LLM framework, "
                         "so it needs metadata and documentation `ship` and llm_processing `allowed`: "
                         + "; ".join(blocked))


def advice_lines(text):
    """Lines of generated text with advice words.

    Skips what quotes the records: blockquotes, `code`, "quoted text", **names**, and table
    rows, whose cells are the publisher's labels, except in Common Pitfalls, which is ours."""
    out, section = [], ""
    for line in text.splitlines():
        if line.startswith("## "):
            section = line
        if line.lstrip().startswith(">") or line.startswith("<!--"):
            continue
        if line.startswith("|") and section != "## Common Pitfalls":
            continue
        bare = re.sub(r"`[^`]*`", "", line)
        bare = re.sub(r"\"[^\"]*\"", "", bare)
        bare = re.sub(r"\*\*[^*]*\*\*", "", bare)
        if ADVICE.search(bare):
            out.append(line)
    return out


def one_line(text):
    return " ".join(str(text or "").split())


def cell(text, n=None):
    """Text for a markdown table cell: one line, pipes escaped, cut to n characters."""
    text = one_line(text).replace("|", "\\|")
    return text if n is None or len(text) <= n else text[: n - 1].rstrip() + "…"


def git_remote(root):
    try:
        done = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"],
                              capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    url = done.stdout.strip()
    if done.returncode or not url:
        return None
    m = re.match(r"git@github\.com:(.+?)(\.git)?$", url)
    return f"https://github.com/{m.group(1)}" if m else re.sub(r"\.git$", "", url)


class Exporter:
    def __init__(self, root, out, domain=None, repo_url=None, today=None):
        self.root = Path(root)
        self.out = Path(out)
        self.repo = Repo.load(self.root)
        self.ds = self.repo.dataset
        check_terms(self.ds)
        self.id = self.ds["id"]
        domain = domain or self.ds.get("domain")
        if not domain:
            raise ValueError("no domain: set `domain` in dataset.yaml (STANDARD.md §2.1), or pass --domain")
        self.name = f"{domain}-data-source-{self.id}"
        if not NAME_RE.match(self.name) or len(self.name) > 64:
            raise ValueError(f"skill name {self.name!r} isn't lowercase letters, digits and single hyphens, "
                             "at most 64 characters (DAAF's frontmatter rule)")
        self.domain = domain
        self.repo_url = repo_url or git_remote(self.root)
        self.today = today or date.today().isoformat()
        self.digest = inputs_hash(self.root)
        self.index = Index.from_repo(self.repo)
        self.order = release_order(self.ds)
        self.chains, _ = build_chains(self.repo)
        self.lineages = lineages(self.chains, self.order)
        self.records = {(rel, tab, rec["name"]): rec for rel, tab, rec in self.index.entries}
        self.title = self.ds.get("title") or self.id
        self.short = re.search(r"\(([^)]+)\)\s*$", self.title)
        self.short = self.short.group(1) if self.short else self.id.upper()
        self.notice = one_line((self.ds.get("terms") or {}).get("notice"))
        self.files = []

    # ------------------------------------------------------------ writing

    def header(self):
        return (f"<!-- Generated by pdt {__version__} from inputs sha256:{self.digest} "
                f"(`pdt export daaf`). Do not edit; the records in the dataset repository's "
                f"metadata/ are canonical. -->\n")

    def notice_block(self):
        return (f"> **Terms:** {self.notice}\n\n" if self.notice else "")

    def write(self, rel_path, text):
        path = self.out / self.name / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        self.files.append(f"{self.name}/{rel_path}")

    def write_parts(self, stem, title, intro, lines):
        """references/<stem>.md, split into <stem>-NN.md parts over PART_TOKENS; returns the file names."""
        head = self.header() + "\n" + f"# {title}\n\n" + self.notice_block() + intro + "\n"
        body = "\n".join(lines) + "\n"
        table_head = lines[:2] if len(lines) > 1 and lines[1].startswith("|---") else []
        lines = lines[len(table_head):]
        if tokens(head + body) <= PART_TOKENS:
            self.write(f"references/{stem}.md", head + body)
            return [f"{stem}.md"]
        parts, current, size = [], [], 0
        for line in lines:
            t = tokens(line + "\n")
            if current and size + t > PART_TOKENS - 500:
                parts.append(current)
                current, size = [], 0
            current.append(line)
            size += t
        if current:
            parts.append(current)
        names = []
        for i, part in enumerate(parts, 1):
            name = f"{stem}-{i:02d}.md"
            names.append(name)
            self.write(f"references/{name}", self.header() + "\n" + f"# {title}, part {i} of {len(parts)}\n\n"
                       + self.notice_block() + "\n".join(table_head + part) + "\n")
        listing = [f"| `{n}` | {cell(first_word(p[0]))} … {cell(first_word(p[-1]))} |"
                   for n, p in zip(names, parts)]
        self.write(f"references/{stem}.md", head + f"\nThis list is in {len(parts)} parts:\n\n"
                   "| File | From … to |\n|---|---|\n" + "\n".join(listing) + "\n")
        return [f"{stem}.md"] + names

    # ------------------------------------------------------------ build

    def build(self):
        old = self.out / "manifest.json"
        self.authored = (json.loads(old.read_text()).get("authored") if old.exists() else None) or self.today
        if self.out.exists():
            if any(self.out.iterdir()) and not (self.out / "manifest.json").exists():
                raise FileExistsError(f"{self.out} exists and wasn't generated by pdt; not overwriting")
            shutil.rmtree(self.out)
        self.out.mkdir(parents=True)
        self.parts = {}
        self.parts["columns"] = self.columns_md()
        self.parts["coded-values"] = self.coded_values_md()
        self.parts["data-quality"] = self.data_quality_md()
        self.parts["variable-definitions"] = self.variable_definitions_md()
        self.parts["analytical-context"] = self.analytical_context_md()
        self.agent = self.copy_agent()
        skill = self.skill_md()
        self.write("SKILL.md", skill)
        manifest = {"pdt_version": __version__, "inputs_sha256": self.digest,
                    "generator_sha256": generator_hash(), "dataset": self.id, "skill": self.name,
                    "authored": self.authored, "date": self.today, "repo_url": self.repo_url, "agent_copy": self.agent["mode"],
                    "files": sorted(self.files)}
        (self.out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
        return manifest

    # ------------------------------------------------------------ facts

    def nonvalid(self, rec):
        return [v for v in rec.get("values") or [] if v.get("kind") != "valid"]

    def latest_records(self):
        rel = self.order[-1] if self.order else None
        return rel, [(tab, rec) for r, tab, rec in self.index.entries if r == rel]

    def missing_type_counts(self):
        c = Counter()
        for _, _, rec in self.index.entries:
            for t in {t for v in self.nonvalid(rec) for t in v.get("missing_types") or []}:
                c[t] += 1
        return c

    def unresolved(self):
        return [(rel, tab, rec["name"], v) for rel, tab, rec in self.index.entries
                for v in rec.get("values") or [] if v.get("kind") == "unresolved"]

    def meaning_changes(self):
        """[(link, relations)] for links whose relations change the meaning (or rescale)."""
        out = []
        for link in self.repo.links:
            rels = set(link.get("relations") or [])
            hit = rels & (CHANGED_MEANING | {"rescaled"})
            if hit:
                out.append((link, sorted(hit)))
        return out

    def unjoined_names(self):
        """Names in chains over disjoint releases that no link joins: the records don't say
        whether they're the same item (HHX 2016-2018 and HHX 2019-2024 in NHIS)."""
        by_name = {}
        for c in self.chains:
            rels = frozenset(r for r, _, _ in c.members)
            for name in {n for _, _, n in c.members}:
                by_name.setdefault(name, []).append(rels)
        return sorted(n for n, sets in by_name.items()
                      if any(not (a & b) for i, a in enumerate(sets) for b in sets[i + 1:]))

    def groups_by_size(self, kinds=None):
        gs = [g for g in self.repo.groups if kinds is None or g.get("kind") in kinds]
        return sorted(gs, key=lambda g: (-len(g.get("members") or []), g["id"]))

    def designs(self):
        """[(design, [(release, table)])] for each distinct design, in release order."""
        out = {}
        for rel in self.order:
            r = next(x for x in self.ds["releases"] if x["id"] == rel)
            for t in r.get("tables") or [None]:
                tab = t["id"] if t else None
                d = effective_design(self.ds, rel, tab)
                if d:
                    key = json.dumps(d, sort_keys=True)
                    out.setdefault(key, (d, []))[1].append((rel, tab))
        return list(out.values())

    def release_span(self):
        return span(self.order, self.order) if self.order else ""

    # ------------------------------------------------------------ SKILL.md

    def description(self):
        pub = (self.ds.get("publisher") or {}).get("name", "")
        waves = ((self.ds.get("dimensions") or {}).get("wave") or {}).get("label") or "release"
        designs = [d for d, _ in self.designs()]
        design = ""
        if designs:
            parts = [k for k, has in (("weights", any(d.get("weights") for d in designs)),
                                      ("strata", any(d.get("strata") for d in designs)),
                                      ("PSU", any(d.get("psu") for d in designs)),
                                      ("replicate weights", any(d.get("replicates") for d in designs))) if has]
            design = f" and the survey design ({', '.join(parts)})" if parts else " and the survey design"
        head = (f"{self.title}, {pub}, releases {self.release_span()}: the publisher's documentation "
                f"as records. Question text, codes with typed missing codes, availability by {waves}, "
                f"links across releases{design}. Use when finding {self.short} variables, reading "
                f"their codes, or checking what changed between releases.")
        tail = (f" Metadata only, from the PublicDataToolkit repository pdt-{self.id}; it makes no "
                "analysis decisions. Not for other surveys.")
        topics = [one_line(g.get("label") or g.get("stem") or g["id"])
                  for g in self.groups_by_size({"subject", "section"})][:5]
        if not topics:
            topics = sorted({one_line(t.get("label") or t["id"]) for r in self.ds["releases"]
                             for t in r.get("tables") or []})[:5]
        text = head + (f" Covers {', '.join(topics)}." if topics else "") + tail
        while len(text) > DESCRIPTION_CHARS and topics:
            topics.pop()
            text = head + (f" Covers {', '.join(topics)}." if topics else "") + tail
        text = text.replace("<", "(").replace(">", ")")
        return text[:DESCRIPTION_CHARS]

    def frontmatter(self):
        terms = self.ds.get("terms") or {}
        terms_line = (f"metadata {terms.get('metadata')}, documentation {terms.get('documentation')}, "
                      f"data {terms.get('data')}, llm_processing {terms.get('llm_processing')}; "
                      f"reviewed {terms.get('reviewed_on', 'n/a')}; {terms.get('url', '')}").strip()
        meta = {"audience": "any-agent", "domain": "data-source",
                "skill-authored": self.authored, "skill-last-updated": self.today,
                "data-provenance": "real",
                "pdt-version": __version__, "pdt-inputs-sha256": self.digest,
                "pdt-generator-sha256": generator_hash(),
                "pdt-standard-version": str(self.ds.get("standard_version", "")),
                "pdt-terms": terms_line, "pdt-license": LICENSE}
        if self.repo_url:
            meta["pdt-repository"] = self.repo_url
        lines = ["---", f"name: {self.name}", "description: >-"]
        lines += ["  " + l for l in wrap(self.description(), 100)]
        lines.append("metadata:")
        lines += [f"  {k}: {json.dumps(v, ensure_ascii=False)}" for k, v in meta.items()]
        lines.append("---")
        return "\n".join(lines) + "\n"

    def encoding_block(self):
        rel, recs = self.latest_records()
        picked, covered = [], set()
        counts = self.missing_type_counts()
        for mtype, _ in counts.most_common():
            for tab, rec in recs:
                nv = self.nonvalid(rec)
                types = {t for v in nv for t in v.get("missing_types") or []}
                if mtype in types and mtype not in covered and all(rec is not p for _, p in picked):
                    picked.append((tab, rec))
                    covered |= types
                    break
            if len(picked) == 3:
                break
        lines = ["> **CRITICAL: Value Encoding**", ">",
                 f"> {self.short}'s files store missing answers as codes, the same type as the answers: "
                 "a number in a numeric column. This repository records each code's kind (valid, "
                 "missing, unresolved) and the missing types the publisher's labels state. The "
                 "PublicDataToolkit common-format files hold valid answers in `<name>` and the "
                 "non-valid codes, as text, in `<name>__code`.", ">"]
        if picked:
            lines.append("> | Context | " + " | ".join(f"`{rec['name']}`" for _, rec in picked) + " |")
            lines.append("> |---------|" + "---|" * len(picked))
            row = []
            for _, rec in picked:
                valid = [v for v in rec.get("values") or [] if v.get("kind") == "valid"][:2]
                row.append(", ".join(f"`{code_text(v['code'])}` {cell(v.get('label'), 20)}" for v in valid)
                           or "a value")
            lines.append("> | **Valid answers (examples)** | " + " | ".join(row) + " |")
            row = [", ".join(f"`{code_text(v['code'])}` {'/'.join(v.get('missing_types') or [v.get('kind')])}"
                             for v in self.nonvalid(rec)[:3]) for _, rec in picked]
            lines.append(f"> | **Missing codes, as in the publisher's file ({rel})** | " + " | ".join(row) + " |")
            row = [f"`{rec['name']}` null; `{rec['name']}{CODE_SUFFIX}` = "
                   f"`\"{code_text(self.nonvalid(rec)[0]['code'])}\"`" for _, rec in picked]
            lines.append("> | **Common-format files** | " + " | ".join(row) + " |")
        else:
            lines.append("> The records mark no codes as missing.")
        lines += [">", "> See `./references/coded-values.md` for every set of codes, and "
                       "`./references/variable-definitions.md` for groups and changes across releases."]
        return "\n".join(lines) + "\n"

    def terms_section(self):
        terms = self.ds.get("terms") or {}
        lines = ["## Terms of Use", ""]
        if self.notice:
            lines += [f"> {self.notice}", ""]
        lines += [f"The publisher's terms: {terms.get('url', 'not recorded')}. "
                  f"Reviewed by {terms.get('reviewed_by', 'no one yet')}"
                  + (f" on {terms['reviewed_on']}" if terms.get("reviewed_on") else "") + ".", "",
                  "| What | Decision |", "|---|---|"]
        for k, what in (("metadata", "Metadata built from the documentation"),
                        ("documentation", "The publisher's documentation"),
                        ("data", "The publisher's data files"),
                        ("llm_processing", "Sending the documentation's text to a hosted LLM")):
            lines.append(f"| {what} | `{terms.get(k)}` |")
        lines += ["", "What the terms say, as recorded:", "", f"> {one_line(terms.get('summary'))}", "",
                  "License: this repository's metadata and the files generated from it, this skill "
                  "included, are CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). The "
                  "publisher's terms, above, apply to the data and the documentation.", ""]
        return "\n".join(lines)

    def what_is(self):
        pub = self.ds.get("publisher") or {}
        dims = self.ds.get("dimensions") or {}
        wave = dims.get("wave") or {}
        n_records = len(self.index.entries)
        rows = [f"- **Producer:** {pub.get('name', 'not recorded')}" + (f" ({pub['url']})" if pub.get("url") else ""),
                f"- **Kind:** {self.ds.get('kind', 'survey')}",
                f"- **Releases here:** {len(self.order)} ({self.release_span()}), "
                f"{sum(1 for r in self.ds['releases'] if r.get('status') == 'current')} current",
                f"- **Variables:** {n_records:,} records; {len(self.lineages):,} variables across releases",
                f"- **Wave:** {wave.get('label', 'release')}" + (f". {one_line(wave.get('note'))}" if wave.get("note") else "")]
        if self.ds.get("url"):
            rows.append(f"- **Publisher's page:** {self.ds['url']}")
        if self.ds.get("citation"):
            rows.append(f"- **Citation:** {one_line(self.ds['citation'])}")
        rows.append("- **Canonical source of these facts:** "
                    + (f"{self.repo_url} (`metadata/`)" if self.repo_url else f"the repository pdt-{self.id} (`metadata/`)")
                    + (f", data release `{self.ds['data_release'].get('tag')}`" if self.ds.get("data_release") else ""))
        return ("## What is the " + self.title + "?\n\n" + one_line(self.ds.get("description")) + "\n\n"
                + "\n".join(rows) + "\n")

    def reference_table(self):
        rows = [("columns.md", "One line per variable across releases: names, releases, label, table",
                 "Finding a variable, or which releases have it"),
                ("coded-values.md", "Each set of non-valid codes with its missing types; unresolved codes",
                 "Reading or filtering codes"),
                ("data-quality.md", "Corrections to the documentation, unresolved codes, revised data",
                 "Checking whether a record was corrected"),
                ("variable-definitions.md", "Groups (batteries, subjects) and changes across releases, with evidence",
                 "Comparing releases; finding related items"),
                ("analytical-context.md", "Releases, tables, survey design, terms", "Joining tables; weights")]
        lines = ["## Reference File Structure", "", "| File | Purpose | When to Read |", "|------|---------|--------------|"]
        for f, p, w in rows:
            n = len(self.parts.get(f[:-3], [])) - 1
            lines.append(f"| `{f}` | {p}" + (f" (in {n} parts)" if n > 0 else "") + f" | {w} |")
        a = self.agent
        lines.append(f"| `agent/` | {a['note']} | Searching by group or subject; completeness labels |")
        return "\n".join(lines) + "\n"

    def decision_trees(self):
        types = [t for t, _ in self.missing_type_counts().most_common()]
        return ("## Decision Trees\n\n"
                "### Which release has the variable?\n\n```\n"
                "Variable name or topic\n"
                "├─ Name known → references/columns.md (every release it appears in)\n"
                "│   └─ Different name in another release? → the same line (renames are joined)\n"
                "├─ Topic only → Topic Index below → references/variable-definitions.md\n"
                "└─ Meaning changed between releases? → references/variable-definitions.md, 'Changes'\n"
                "```\n\n"
                "### Is this code an answer or missing?\n\n```\n"
                "Code in the publisher's file\n"
                "├─ Listed as valid in the record → an answer\n"
                "├─ Listed with missing types (" + (", ".join(types) or "none here") + ") → missing, for that reason\n"
                "├─ Listed as unresolved → not classified; references/data-quality.md\n"
                "└─ Not listed → absent from the documentation; references/coded-values.md\n"
                "```\n\n"
                "### Is a search result complete?\n\n```\n"
                "Shard or search in references/agent/\n"
                "├─ completeness: complete → every variable that matches the filter\n"
                "├─ completeness: complete_by_rule → complete under a named rule (see the shard header)\n"
                "└─ completeness: approximate → a model's or annotator's judgment; may miss items\n"
                "```\n")

    def quick_reference(self):
        lines = [f"## Quick Reference: {self.short} Releases and Codes", "", "### Releases", "",
                 "| Release | Label | Status | Tables |", "|---|---|---|---|"]
        for rel in self.order:
            r = next(x for x in self.ds["releases"] if x["id"] == rel)
            tabs = ", ".join(t["id"] for t in r.get("tables") or []) or "one"
            lines.append(f"| `{rel}` | {cell(r.get('label'), 80)} | {r.get('status')} | {tabs} |")
        lines += ["", "### Key Identifiers", ""]
        keys = {}
        for r in self.ds["releases"]:
            for t in r.get("tables") or []:
                if t.get("key"):
                    keys.setdefault((t["id"], tuple(t["key"])), []).append(r["id"])
        if keys:
            lines += ["| Table | Key | Releases |", "|---|---|---|"]
            for (tab, key), rels in keys.items():
                lines.append(f"| `{tab}` | {', '.join(f'`{k}`' for k in key)} | {span(rels, self.order)} |")
        else:
            lines.append("No table keys are recorded; each release is one table, one row per record.")
        counts = self.missing_type_counts()
        lines += ["", "### Missing Data Codes", ""]
        if counts:
            lines += ["| Missing type | Meaning | Records with it |", "|---|---|---|"]
            for t, n in counts.most_common():
                lines.append(f"| `{t}` | {MISSING_TYPES.get(t, t)} | {n:,} |")
        else:
            lines.append("No codes are typed as missing.")
        groups = self.groups_by_size()
        if groups:
            lines += ["", "### Largest Groups", "", "| Group | Kind | Members |", "|---|---|---|"]
            for g in groups[:10]:
                lines.append(f"| {cell(g.get('label') or g.get('stem') or g['id'], 70)} | {g.get('kind')} "
                             f"| {len(g.get('members') or [])} |")
        return "\n".join(lines) + "\n"

    def data_access(self):
        terms = self.ds.get("terms") or {}
        rel, recs = self.latest_records()
        r = next((x for x in self.ds["releases"] if x["id"] == rel), {})
        tab = (r.get("tables") or [{}])[0].get("id")
        names = [rec["name"] for t, rec in recs if t == tab][:3]
        path = (PROCESSED / file_name(self.id, rel, tab)).as_posix()
        where = self.repo_url or f"pdt-{self.id}"
        lines = ["## Data Access", "", "### Dataset Paths", ""]
        if terms.get("data") == "ship":
            dr = self.ds.get("data_release") or {}
            lines.append("The publisher's terms let the common-format files be redistributed. "
                         + (f"They are in the data release `{dr.get('tag')}`: {dr.get('url')}. "
                            f"Or build them from the publisher's files in the repository ({where}):"
                            if dr.get("tag") else
                            f"The repository ({where}) builds them from the publisher's files:"))
        else:
            lines.append(f"The publisher's terms (`data: {terms.get('data')}`) don't let the data be "
                         f"redistributed, so it comes from the publisher. The repository ({where}) "
                         "fetches and converts it:")
        lines += ["", "```bash", f"git clone {where}" if self.repo_url else f"# in a checkout of pdt-{self.id}",
                  "make download ARGS=--accept-terms   # the publisher's files, after reading their terms",
                  "make data                           # data/processed/*.parquet, the common format", "```", "",
                  f"One file per release and table: `data/processed/{self.id}-<release>[-<table>].parquet`, "
                  f"for example `{path}`.", "", "### Codebooks", ""]
        docs = [s for s in (self.repo.sources.get("sources") or []) if s.get("kind") != "data" and s.get("url")]
        for s in docs[:8]:
            lines.append(f"- `{s['id']}`: {s['url']}")
        if len(docs) > 8:
            lines.append(f"- … {len(docs) - 8} more in the repository's `sources.yaml`")
        if not docs:
            lines.append("Listed in the repository's `sources.yaml`.")
        cols = ", ".join(json.dumps(n) for n in names)
        lines += ["", "### Example Fetch", "", "```python",
                  "# The common-format file: valid answers in <name>, non-valid codes as text in <name>__code",
                  "import polars as pl",
                  f"df = pl.read_parquet({json.dumps(path)})",
                  f"df.select([{cols}])" if cols else "df.columns",
                  "", "# Or with the PublicDataToolkit library, which reports what each code means:",
                  "from pdt.extract import extract",
                  f"result = extract(\".\", {json.dumps(rel)}, [{cols}]" + (f", table={json.dumps(tab)}" if tab else "") + ")",
                  "print(\"\\n\".join(result.report))", "```", "", "```r",
                  f"df <- arrow::read_parquet({json.dumps(path)})", "```", "",
                  "### Filtering", "", "```python",
                  "# Rows where the answer is valid, and rows with a given missing code",
                  ]
        if names:
            n = names[-1]
            lines += [f"df.filter(pl.col({json.dumps(n)}).is_not_null())",
                      f"df.filter(pl.col({json.dumps(n + CODE_SUFFIX)}).is_not_null())   # if the variable has non-valid codes"]
        lines += ["```", ""]
        return "\n".join(lines)

    def pitfalls(self):
        rows = []
        counts = self.missing_type_counts()
        if counts:
            n = sum(1 for _, _, rec in self.index.entries if self.nonvalid(rec))
            rows.append(("Missing codes read as answers",
                         f"{n:,} records have codes the documentation marks as missing "
                         f"({', '.join(t for t, _ in counts.most_common())}); in the publisher's file they "
                         "are numbers like the answers.",
                         "The common-format files put them in `<name>__code`; `coded-values.md` lists each set."))
        changes = self.meaning_changes()
        if changes:
            c = Counter(r for _, rels in changes for r in rels)
            rows.append(("Same name, changed meaning",
                         f"{len(changes)} links record a change between releases: "
                         + ", ".join(f"{k} {v}" for k, v in c.most_common()) + ".",
                         "`variable-definitions.md`, 'Changes', gives each with its evidence."))
        renamed = [l for l in self.repo.links if "renamed" in (l.get("relations") or [])]
        if renamed:
            rows.append(("Renamed variables",
                         f"{len(renamed)} variables have different names in different releases.",
                         "`columns.md` puts each on one line, with its names by release."))
        unjoined = self.unjoined_names()
        if unjoined:
            rows.append(("Same name, not joined",
                         f"{len(unjoined)} names appear in different releases with no link joining them, e.g. "
                         + ", ".join(f"`{n}`" for n in unjoined[:3])
                         + "; the records don't say whether they are the same item.",
                         "`columns.md` gives each run its own line."))
        partial = [l for l in self.lineages if len({m[0] for m in l.members}) < len(self.order)]
        if partial and len(self.order) > 1:
            rows.append(("Not in every release",
                         f"{len(partial):,} of {len(self.lineages):,} variables are missing from some releases.",
                         "`columns.md` lists the releases for each."))
        revised = [l for l in self.repo.links if "data_revised" in (l.get("relations") or [])]
        if revised:
            rows.append(("Revised data", f"{len(revised)} links record that the publisher revised a variable's "
                         "data between releases, under the same name.",
                         "`data-quality.md`, 'Revised data between releases'."))
        derived = [l for l in self.repo.links if {"derived_from", "split_from", "merged_into"} & set(l.get("relations") or [])]
        if derived:
            rows.append(("Built from other variables", f"{len(derived)} links record a variable derived from, "
                         "split from or merged into others; they don't join lines in `columns.md`.",
                         "The links are in the repository's `metadata/links.jsonl`."))
        unresolved = self.unresolved()
        if unresolved:
            rows.append(("Unclassified codes",
                         f"{len(unresolved)} codes appear in the data but the documentation doesn't say what they are.",
                         "`data-quality.md` lists them."))
        if self.repo.corrections:
            rows.append(("Corrected documentation",
                         f"{len(self.repo.corrections)} facts in the publisher's documentation were corrected here.",
                         "`data-quality.md` gives the original, the correction and the evidence."))
        pv = [g for g in self.repo.groups if g.get("kind") == "plausible_values"]
        if pv:
            rows.append(("Plausible values", f"{len(pv)} groups are sets of plausible values, one score in several columns.",
                         "`variable-definitions.md` lists each group's members."))
        if any((d.get("replicates") for d, _ in self.designs())):
            rows.append(("Replicate weights", "The design has replicate weights, columns that are weights, not answers.",
                         "'Survey Design' below names them and the method."))
        if self.ds.get("data_rows") or any(r.get("data_rows") for r in self.ds["releases"]):
            rows.append(("Rows kept", "The common-format files keep only some of the publisher's rows (`data_rows`).",
                         "`analytical-context.md` says which."))
        lines = ["## Common Pitfalls", "", "Each row is a fact the records hold, with where to read it.", "",
                 "| Pitfall | Issue | Solution |", "|---------|-------|----------|"]
        lines += [f"| {a} | {cell(b)} | {c} |" for a, b, c in rows]
        return "\n".join(lines) + "\n"

    def survey_design(self):
        designs = self.designs()
        if not designs:
            return ""
        lines = ["## Survey Design", "", "As recorded in the repository's `dataset.yaml`. DAAF's `svy` "
                 "skill covers the syntax.", ""]
        for d, where in designs:
            places = {}
            for rel, tab in where:
                places.setdefault(tab, []).append(rel)
            lines.append("### " + "; ".join((f"`{t}` " if t else "") + span(rels, self.order) for t, rels in places.items()))
            lines.append("")
            ws = weight_names(d)
            if ws:
                lines.append("- **Weights:** " + ", ".join(f"`{w}`" for w in ws))
            for k in ("strata", "psu"):
                if d.get(k):
                    lines.append(f"- **{k.upper() if k == 'psu' else k.capitalize()}:** `{d[k]}`")
            rep = d.get("replicates")
            if rep:
                table, names = replicate_columns(d)
                desc = (f"`{rep['prefix']}1`–`{rep['prefix']}{rep['n']}`" if rep.get("prefix")
                        else f"{len(names)} named")
                lines.append(f"- **Replicate weights:** {desc}, method `{rep.get('method')}`"
                             + (f", Fay factor {rep['fay_factor']}" if rep.get("fay_factor") is not None else "")
                             + (f", in table `{table}` joined on {', '.join(f'`{k}`' for k in rep.get('key') or [])}"
                                if table else ""))
            if d.get("note"):
                lines.append(f"- **Note:** {one_line(d['note'])}")
            lines.append("")
        return "\n".join(lines)

    def multi_file(self):
        structures = {}
        for rel in self.order:
            r = next(x for x in self.ds["releases"] if x["id"] == rel)
            ts = r.get("tables") or []
            if len(ts) < 2:
                continue
            sig = json.dumps([[t["id"], t.get("key"), t.get("references")] for t in ts], sort_keys=True)
            structures.setdefault(sig, (ts, []))[1].append(rel)
        if not structures:
            return ""
        lines = ["## Multi-File Structure", ""]
        for ts, rels in structures.values():
            lines += [f"### Releases {span(rels, self.order)}", "", "| Table | Label | Key | References |", "|---|---|---|---|"]
            for t in ts:
                refs = "; ".join(
                    f"`{ref.get('table')}` on {', '.join(ref['columns'])}"
                    + (f" (dataset {ref['dataset']})" if ref.get("dataset") else "")
                    + (f" when {when_text(ref['when'])}" if ref.get("when") else "")
                    for ref in t.get("references") or []) or "none"
                lines.append(f"| `{t['id']}` | {cell(t.get('label'), 60)} | "
                             f"{', '.join(t.get('key') or []) or 'none'} | {refs} |")
            lines.append("")
        return "\n".join(lines)

    def topic_index(self):
        lines = ["## Topic Index", "", "| Topic | Reference File |", "|---|---|",
                 "| Variables by release | `./references/columns.md` |",
                 "| Missing and non-valid codes | `./references/coded-values.md` |",
                 "| Corrections and unclassified codes | `./references/data-quality.md` |",
                 "| Groups and changes across releases | `./references/variable-definitions.md` |",
                 "| Releases, tables, survey design, terms | `./references/analytical-context.md` |",
                 "| Search shards with completeness labels | `./references/agent/index.md` |"]
        for g in self.groups_by_size({"subject", "section", "plausible_values"})[:TOP_GROUPS]:
            lines.append(f"| {cell(g.get('label') or g['id'], 60)} | `./references/variable-definitions.md` |")
        return "\n".join(lines) + "\n"

    def skill_md(self):
        body = [self.frontmatter(), self.header(),
                f"# {self.short} Data Source Reference\n",
                f"{one_line(self.ds.get('description'))} This skill was generated from the "
                f"PublicDataToolkit repository for the {self.title}: {len(self.index.entries):,} variable records in "
                f"{len(self.order)} releases, with the publisher's question text and codes, the kind of each "
                "code, where each fact came from, and the links between releases. It describes the "
                "documentation and makes no analysis decisions.\n",
                self.encoding_block(),
                self.terms_section(),
                self.what_is(), self.reference_table(), self.decision_trees(), self.quick_reference(),
                self.data_access(), self.pitfalls()]
        for optional in (self.survey_design(), self.multi_file()):
            if optional:
                body.append(optional)
        body += ["## Related Data Sources\n\nThe records relate no other dataset. Other PublicDataToolkit "
                 "repositories, and DAAF's other data-source skills, are separate.\n",
                 self.topic_index()]
        text = "\n".join(body)
        n = text.count("\n")
        if n > SKILL_MAX_LINES:
            raise ValueError(f"SKILL.md has {n} lines, over DAAF's {SKILL_MAX_LINES}")
        return text

    # ------------------------------------------------------------ references

    def columns_md(self):
        lines = ["| Variable (names by release) | Table | Label |", "|---|---|---|"]
        for lin in self.lineages:
            for c in lin.chains:
                rec = self.records.get(c.last)
                tables = " → ".join(dict.fromkeys(str(t) for _, t, _ in c.members if t))
                lines.append(f"| {cell(names_text(c, self.order))} | {tables} | "
                             f"{cell((rec or {}).get('label'), 100)} |")
        intro = (f"One line per variable across releases ({len(self.order)} releases, oldest first: "
                 f"{', '.join(self.order)}). A name changes where the publisher renamed the variable; a "
                 "variable whose meaning changed has a line for each run, together. The full records "
                 "are in the repository's `metadata/releases/` and in `agent/` shards.\n")
        return self.write_parts("columns", f"{self.short} columns", intro, lines)

    def coded_values_md(self):
        sets = {}
        for rel, tab, rec in self.index.entries:
            nv = self.nonvalid(rec)
            if not nv:
                continue
            key = tuple((code_text(v["code"]), one_line(v.get("label")), v.get("kind"),
                         tuple(v.get("missing_types") or [])) for v in nv)
            sets.setdefault(key, []).append((rel, tab, rec["name"]))
        lines = []
        for i, (key, members) in enumerate(sorted(sets.items(), key=lambda kv: -len(kv[1])), 1):
            names = list(dict.fromkeys(n for _, _, n in members))
            rels = sorted({r for r, _, _ in members}, key=self.order.index)
            lines += [f"## Code set {i}: {len(members):,} records", "",
                      f"Releases {span(rels, self.order)}. Variables: "
                      + ", ".join(f"`{n}`" for n in names[:12]) + (f", and {len(names) - 12:,} more" if len(names) > 12 else ""),
                      "", "| Code | Label (publisher's) | Kind | Missing types |", "|---|---|---|---|"]
            lines += [f"| `{c}` | {cell(lab, 80)} | {k} | {', '.join(t) or ''} |" for c, lab, k, t in key]
            lines.append("")
        intro = ("Every set of non-valid codes (missing or unresolved), with the records that use it, "
                 "largest first. Valid codes are in each record (the repository's `metadata/` and "
                 "`agent/` shards). Missing types:\n\n"
                 + "\n".join(f"- `{t}`: {MISSING_TYPES.get(t, t)}" for t in sorted(self.missing_type_counts())) + "\n")
        return self.write_parts("coded-values", f"{self.short} coded values", intro, lines)

    def data_quality_md(self):
        lines = ["## Corrections", ""]
        if self.repo.corrections:
            for c in self.repo.corrections:
                t = c.get("target") or {}
                where = "/".join(str(t[k]) for k in ("release", "table", "name") if t.get(k))
                ev = "; ".join(e.get("citation", "") + (f" ({e['url']})" if e.get("url") else "")
                               for e in c.get("evidence") or [])
                lines += [f"### `{where}` {t.get('field', '')}", "",
                          "- Problem, as the correction states it:", f"  > {cell(c.get('problem'), 400)}",
                          "- Original:", f"  > {cell(c.get('original'), 400)}",
                          "- Corrected:", f"  > {cell(c.get('corrected'), 400)}",
                          f"- Confidence: {c.get('confidence')}; evidence: {ev or 'none recorded'}",
                          f"- Reported to the publisher: {(c.get('upstream') or {}).get('status', 'not recorded')}", ""]
        else:
            lines += ["None recorded.", ""]
        lines += ["## Unclassified codes", ""]
        un = self.unresolved()
        if un:
            lines += ["| Release | Table | Variable | Code | Label |", "|---|---|---|---|---|"]
            lines += [f"| {r} | {t or ''} | `{n}` | `{code_text(v['code'])}` | {cell(v.get('label'), 80)} |"
                      for r, t, n, v in un]
        else:
            lines.append("None recorded.")
        revised = [l for l in self.repo.links if "data_revised" in (l.get("relations") or [])]
        lines += ["", "## Revised data between releases", ""]
        if revised:
            lines += ["| From | To | Note |", "|---|---|---|"]
            lines += [f"| {ref(l['from'])} | {ref(l['to'])} | {cell(l.get('note') or (l.get('origin') or {}).get('note'), 200)} |"
                      for l in revised]
        else:
            lines.append("None recorded.")
        return self.write_parts("data-quality", f"{self.short} data quality",
                                "What this repository records about errors and revisions in the publisher's "
                                "documentation and files.\n", lines + [""])

    def variable_definitions_md(self):
        lines = ["## Changes across releases", ""]
        changes = self.meaning_changes()
        if changes:
            lines += ["| From | To | Relations | Evidence |", "|---|---|---|---|"]
            for link, rels in changes:
                o = link.get("origin") or {}
                ev = "; ".join(e.get("citation", "") for e in link.get("evidence") or []) or \
                     one_line(" ".join(x for x in (o.get("source"), o.get("location"), o.get("note")) if x))
                lines.append(f"| {ref(link['from'])} | {ref(link['to'])} | {', '.join(rels)} | {cell(ev, 300)} |")
        else:
            lines.append("No link records a change of meaning.")
        lines += ["", "## Groups", ""]
        groups = self.groups_by_size()
        if groups:
            for g in groups:
                members = [m["name"] for m in g.get("members") or []]
                head = g.get("label") or g["id"]
                lines.append(f"- **{cell(head, 100)}** ({g.get('kind')}, {len(members)}): "
                             + ", ".join(f"`{m}`" for m in members[:30]) + (" …" if len(members) > 30 else "")
                             + (f". Stem: \"{cell(g['stem'], 200)}\"" if g.get("stem") else ""))
        else:
            lines.append("No groups recorded.")
        return self.write_parts("variable-definitions", f"{self.short} variable definitions",
                                "Changes between releases that the links record, and the groups the records "
                                "define. Each variable's codes and question text are in the agent shards.\n",
                                lines + [""])

    def analytical_context_md(self):
        terms = self.ds.get("terms") or {}
        lines = ["## What this repository is", "",
                 "A record of the publisher's documentation, with corrections and links between releases, "
                 "each fact labeled by where it came from (the publisher, the data file, a rule, a person "
                 "or a model). It makes no analysis decisions: which cases, weights or codes an analysis "
                 "uses depends on the question, and the records only state what the publisher documents.", "",
                 "## Releases", "", "| Release | Label | Status | Tables |", "|---|---|---|---|"]
        for rel in self.order:
            r = next(x for x in self.ds["releases"] if x["id"] == rel)
            lines.append(f"| `{rel}` | {cell(r.get('label'), 100)} | {r.get('status')} | "
                         + (", ".join(f"`{t['id']}`" for t in r.get("tables") or []) or "one") + " |")
        wave = (self.ds.get("dimensions") or {}).get("wave") or {}
        if wave.get("note"):
            lines += ["", f"Waves ({wave.get('label', 'wave')}): {one_line(wave['note'])}"]
        rows = self.ds.get("data_rows")
        if rows:
            lines += ["", f"Rows kept in the common-format files: `{json.dumps(rows)}`."]
        lines += ["", self.survey_design() or "## Survey Design\n\nNone recorded.\n",
                  self.multi_file() or "",
                  "## Terms", "", f"Publisher's terms: {terms.get('url')}.", "",
                  f"> {one_line(terms.get('summary'))}", ""]
        return self.write_parts("analytical-context", f"{self.short} analytical context",
                                "Descriptive context from `dataset.yaml`.\n", lines)

    # ------------------------------------------------------------ agent/

    def copy_agent(self):
        """Generate agent/ into a temporary directory and copy it, or the part within AGENT_BUDGET."""
        dest = self.out / self.name / "references" / "agent"
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "agent"
            m = build_agent(self.root, out=src)
            files = sorted(p for p in src.rglob("*") if p.is_file() and p.name != "manifest.json")
            total = sum(p.stat().st_size for p in files)
            if total <= AGENT_BUDGET:
                chosen, mode = files, "all"
            else:
                mode = "part"
                chosen = [src / "index.md", src / "SKILL.md"]
                size = sum(p.stat().st_size for p in chosen)
                groups = [[src / f["path"] for f in m.get("across_releases", []) if f["path"].endswith(".txt")]]
                kinds = ["table", "group", "subject", "scale", "topic"]
                for kind in kinds:
                    for s in m["shards"]:
                        if s["kind"] == kind:
                            groups.append([src / f["path"] for f in s["files"] if f["path"].endswith(".txt")])
                for g in groups:
                    n = sum(p.stat().st_size for p in g)
                    if g and size + n <= AGENT_BUDGET:
                        chosen += g
                        size += n
            for p in chosen:
                rel = p.relative_to(src)
                name = "agent-guide.md" if rel.as_posix() == "SKILL.md" else rel.as_posix()
                target = dest / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, target)
                self.files.append(f"{self.name}/references/agent/{name}")
        where = (self.repo_url + "/tree/main/agent") if self.repo_url else f"pdt-{self.id}'s agent/"
        if mode == "all":
            note = ("A copy of the repository's agent views (`agent-guide.md` is its SKILL.md): "
                    "shards by release, group and subject, with completeness labels")
        else:
            note = (f"Part of the repository's agent views, {len(chosen)} of {len(files)} files: the index, "
                    f"`agent-guide.md` (its SKILL.md) and the .txt shards that fit; all are at {where}")
        return {"mode": mode, "note": note, "copied": len(chosen), "total": len(files)}


def first_word(line):
    m = re.search(r"`([^`]+)`|\|\s*([^|]+?)\s*\|", line)
    return (m.group(1) or m.group(2)) if m else line[:40]


def ref(r):
    return "`" + "/".join(str(r[k]) for k in ("release", "table", "name") if r.get(k)) + "`"


def wrap(text, width):
    out, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            out.append(line)
            line = word
        else:
            line = f"{line} {word}" if line else word
    if line:
        out.append(line)
    return out


def build(root, domain=None, out=None, repo_url=None, today=None):
    root = Path(root)
    return Exporter(root, Path(out) if out else root / DIRECTORY, domain, repo_url, today).build()


def is_current(root):
    path = Path(root) / DIRECTORY / "manifest.json"
    if not path.exists():
        return False
    m = json.loads(path.read_text())
    return (m.get("pdt_version") == __version__ and m.get("inputs_sha256") == inputs_hash(root)
            and m.get("generator_sha256") == generator_hash())


def main(argv=None):
    import argparse
    import sys
    p = argparse.ArgumentParser(prog="pdt export daaf",
                                description="Write export/daaf/<domain>-data-source-<id>/, a DAAF data-source skill")
    p.add_argument("path", nargs="?", default=".", help="the dataset repo (default: .)")
    p.add_argument("--domain",
                   help="the subject prefix of DAAF's skill name, as in education-data-source-ccd "
                        "(default: dataset.yaml's `domain`)")
    p.add_argument("--out", help="where to write (default: <path>/export/daaf)")
    p.add_argument("--repo-url", help="the dataset repo's URL (default: its git remote origin)")
    p.add_argument("--date", help="skill-authored and skill-last-updated (default: today)")
    args = p.parse_args(argv)
    try:
        m = build(args.path, args.domain, args.out, args.repo_url, args.date)
    except (TermsError, ValueError) as e:
        print(f"pdt export daaf: {e}", file=sys.stderr)
        return 1
    print(f"export/daaf/{m['skill']}/: {len(m['files'])} files (agent copy: {m['agent_copy']})")
    return 0

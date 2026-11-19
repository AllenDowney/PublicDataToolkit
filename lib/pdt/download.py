"""Fetch a dataset repo's sources, as `sources.yaml` lists them (STANDARD.md §2.2, §8).

    pdt download [PATH] --accept-terms        fetch every automated source that's missing or stale
    pdt download [PATH] --check               what's present and whether it matches; no network
    pdt download [PATH] --source ID ...       only these sources
    pdt download [PATH] --release R           only sources of this release

A dataset repo's `scripts/download.py` calls this. It refuses to fetch until the user
passes --accept-terms, after printing the publisher's terms from `dataset.yaml`, as
MarriageNSFG's `--i-accept-nchs-terms` does: the obligation is the user's.

For each source with a `url` and a `path`:
- present with the recorded SHA-256: nothing to do;
- missing: fetched to a temporary file, checked, then moved into place;
- present but different: reported, and not overwritten unless --force.
A fetched file whose checksum differs from the record is kept beside the target as
`<path>.new`, so a person can decide whether the publisher changed it.

Manual sources (`acquisition: manual`) are never fetched; their `manual_steps` are printed.

Converted sources: a source's `convert` names the converter and its version, e.g.
"pdftotext -layout (poppler 24.02)" (STANDARD.md §8). The download is kept beside the
path (a PDF as <path stem>.pdf) and converted to the path; the checksum is of the result.
Only known converters run (pdftotext); the installed version is compared with the
recorded one, since a different version can change the output.
"""

import argparse
import hashlib
import re
import shlex
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import yaml

CHUNK = 1 << 20


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


CONVERTERS = {"pdftotext"}


def parse_convert(text):
    """'pdftotext -layout (poppler 24.02)' -> (['pdftotext', '-layout'], '24.02')."""
    m = re.match(r"\s*([^()]+?)\s*(?:\(\s*\S+\s+([^)]+?)\s*\))?\s*$", text or "")
    if not m:
        raise ValueError(f"can't read convert: {text!r}")
    args = shlex.split(m.group(1))
    if not args or args[0] not in CONVERTERS:
        raise ValueError(f"convert {text!r}: only {sorted(CONVERTERS)} can run; convert it by hand")
    return args, m.group(2)


def installed_version(tool):
    out = subprocess.run([tool, "-v"], capture_output=True, text=True)
    m = re.search(r"version\s+(\S+)", out.stdout + out.stderr)
    return m.group(1) if m else None


def status(root, src):
    """(state, detail) for one source: ok, missing, mismatch, unverified, no_path."""
    if not src.get("path"):
        return "no_path", "no path recorded (an upstream package or a web page)"
    target = Path(root) / src["path"]
    if not target.exists():
        return "missing", str(src["path"])
    if target.is_dir():
        n = sum(1 for f in target.rglob("*") if f.is_file())
        return "ok", f"{src['path']} (a directory of {n} file(s); no checksum)"
    want = src.get("sha256")
    if not want:
        return "unverified", f"present, no sha256 recorded (it is {sha256(target)})"
    got = sha256(target)
    if got != want:
        return "mismatch", f"sha256 {got}, recorded {want}"
    return "ok", str(src["path"])


def terms_text(dataset):
    terms = dataset.get("terms", {})
    pub = dataset.get("publisher", {}).get("name", "the publisher")
    lines = [f"{dataset.get('title', dataset.get('id'))} is distributed by {pub} under its terms of use.",
             f"Read them before downloading: {terms.get('url', '(no URL recorded)')}", ""]
    if terms.get("summary"):
        lines += [" ".join(terms["summary"].split()), ""]
    lines.append("If you have read and accept them, run again with --accept-terms.")
    return "\n".join(lines)


def fetch(url, dest):
    """Download url to dest through a temporary file in the same directory."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    # urllib's own User-Agent: www.cdc.gov refuses custom and browser ones (403) but accepts it.
    request = urllib.request.Request(url)
    with tempfile.NamedTemporaryFile(delete=False, dir=dest.parent, suffix=".part") as tmp:
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                shutil.copyfileobj(response, tmp, CHUNK)
        except BaseException:
            Path(tmp.name).unlink(missing_ok=True)
            raise
    umask = os.umask(0)
    os.umask(umask)
    os.chmod(tmp.name, 0o666 & ~umask)              # a temporary file is private; the result shouldn't be
    Path(tmp.name).replace(dest)


def convert(src, downloaded, out, log=print):
    """Run the source's converter on the downloaded file, writing out."""
    args, version = parse_convert(src["convert"])
    if not shutil.which(args[0]):
        raise RuntimeError(f"{args[0]} is needed to convert {downloaded.name} ({src['convert']})")
    have = installed_version(args[0])
    if version and have and have != version:
        log(f"  note      {src['id']}: {args[0]} {have} is installed; the checksum was recorded "
            f"with {version}, so it may not match")
    subprocess.run([*args, str(downloaded), str(out)], check=True)


def get(root, src, force=False, log=print):
    """Fetch one automated source. Returns its state afterwards."""
    root = Path(root)
    target = root / src["path"]
    state, detail = status(root, src)
    if state == "ok":
        log(f"  ok        {src['id']}: {detail}")
        return "ok"
    if state in ("mismatch", "unverified") and not force:
        log(f"  {state:9} {src['id']}: {detail}; not overwritten (use --force)")
        return state
    log(f"  fetching  {src['id']}: {src['url']}")
    staged = target.with_name(target.name + ".new")
    if src.get("convert"):
        suffix = Path(src["url"].split("?")[0]).suffix or ".download"
        downloaded = target.with_suffix(suffix)
        fetch(src["url"], downloaded)
        convert(src, downloaded, staged, log=log)
    else:
        fetch(src["url"], staged)
    got, want = sha256(staged), src.get("sha256")
    if want and got != want:
        log(f"  MISMATCH  {src['id']}: fetched sha256 {got}, recorded {want}; kept as {staged.name}")
        return "mismatch"
    if target.is_symlink():
        target.unlink()
    staged.replace(target)
    if not want:
        log(f"  fetched   {src['id']}: no sha256 recorded; record sha256: {got} and bytes: "
            f"{target.stat().st_size} in sources.yaml")
        return "unverified"
    log(f"  fetched   {src['id']}: sha256 matches")
    return "ok"


def select(sources, ids=None, release=None):
    out = []
    for s in sources:
        if ids and s["id"] not in ids:
            continue
        if release and release not in (s.get("releases") or []):
            continue
        out.append(s)
    if ids:
        unknown = set(ids) - {s["id"] for s in sources}
        if unknown:
            raise SystemExit(f"no source with id {sorted(unknown)} in sources.yaml")
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(prog="download", description="Fetch the sources in sources.yaml.")
    parser.add_argument("path", nargs="?", default=".", help="the dataset repo (default: .)")
    parser.add_argument("--accept-terms", action="store_true",
                        help="you have read and accept the publisher's terms (required to fetch)")
    parser.add_argument("--check", action="store_true", help="report what's present; no network")
    parser.add_argument("--source", nargs="+", metavar="ID", help="only these sources")
    parser.add_argument("--release", help="only sources of this release")
    parser.add_argument("--force", action="store_true", help="replace files whose checksum differs")
    args = parser.parse_args(argv)

    root = Path(args.path)
    dataset = yaml.safe_load((root / "dataset.yaml").read_text())
    sources = select(yaml.safe_load((root / "sources.yaml").read_text())["sources"],
                     args.source, args.release)

    if args.check:
        counts = {"missing": 0, "manual": 0, "mismatch": 0}
        for s in sources:
            state, detail = status(root, s)
            if s.get("acquisition") == "manual" and state == "missing":
                state, detail = "manual", f"missing; {' '.join((s.get('manual_steps') or 'see sources.yaml').split())}"
            print(f"  {state:10} {s['id']}: {detail}")
            if state in counts:
                counts[state] += 1
        missing = counts["missing"] + counts["manual"]
        print(f"\n{len(sources)} source(s): {missing} missing ({counts['manual']} to fetch by hand), "
              f"{counts['mismatch']} mismatched")
        return 1 if missing or counts["mismatch"] else 0

    if not args.accept_terms:
        print(terms_text(dataset), file=sys.stderr)
        return 2

    failed = 0
    for s in sources:
        if s.get("acquisition") == "manual":
            state, detail = status(root, s)
            steps = " ".join((s.get("manual_steps") or "see sources.yaml").split())
            print(f"  {'ok' if state == 'ok' else 'manual':9} {s['id']}: "
                  + (detail if state == "ok" else steps))
            continue
        if not s.get("url") or not s.get("path"):
            print(f"  skipped   {s['id']}: no url or path")
            continue
        try:
            if get(root, s, force=args.force) == "mismatch":
                failed += 1
        except Exception as e:                          # report and go on to the next source
            print(f"  FAILED    {s['id']}: {e}")
            failed += 1
    print(f"\n{len(sources)} source(s), {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

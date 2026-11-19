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

Converted sources: when the URL is a PDF and the path isn't (NSFG's codebooks, recorded
as the text of `pdftotext -layout`), the PDF is fetched next to the path and converted;
the checksum is of the text. The schema doesn't record conversions yet, so this is
inferred from the two suffixes (proposed for Task 25).
"""

import argparse
import hashlib
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


def is_converted(src):
    """A PDF fetched and kept as its text (pdftotext -layout)."""
    url, path = src.get("url") or "", src.get("path") or ""
    return url.lower().split("?")[0].endswith(".pdf") and not path.lower().endswith(".pdf")


def status(root, src):
    """(state, detail) for one source: ok, missing, mismatch, unverified, no_path."""
    if not src.get("path"):
        return "no_path", "no path recorded (an upstream package or a web page)"
    target = Path(root) / src["path"]
    if not target.exists():
        return "missing", str(src["path"])
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


def pdftotext(pdf, txt):
    if not shutil.which("pdftotext"):
        raise RuntimeError("pdftotext (poppler-utils) is needed to convert " + str(pdf))
    subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=True)


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
    if is_converted(src):
        pdf = target.with_suffix(".pdf")
        fetch(src["url"], pdf)
        pdftotext(pdf, staged)
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
        bad = 0
        for s in sources:
            state, detail = status(root, s)
            if s.get("acquisition") == "manual" and state == "missing":
                state, detail = "manual", f"missing; {' '.join((s.get('manual_steps') or 'see sources.yaml').split())}"
            print(f"  {state:10} {s['id']}: {detail}")
            if state in ("missing", "mismatch"):
                bad += 1
        print(f"\n{len(sources)} source(s), {bad} missing or mismatched")
        return 1 if bad else 0

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

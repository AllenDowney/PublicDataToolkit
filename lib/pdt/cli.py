"""Command line: `pdt check [PATH]`, `pdt views [PATH]`, `pdt search PATH --filter JSON`."""

import argparse
import json
import sys

from . import __version__
from .check import run


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pdt", description="PublicDataToolkit tools")
    parser.add_argument("--version", action="version", version=f"pdt {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="check a dataset repo against the standard")
    check.add_argument("path", nargs="?", default=".", help="the dataset repo (default: .)")
    views = sub.add_parser("views", help="generate agent/ for a dataset repo")
    views.add_argument("path", nargs="?", default=".", help="the dataset repo (default: .)")
    search = sub.add_parser("search", help="search a dataset repo's records; prints a labeled result")
    search.add_argument("path", help="the dataset repo")
    search.add_argument("--filter", required=True, help='a JSON filter, e.g. \'{"topic": "Abortion"}\'')
    args = parser.parse_args(argv)

    if args.command == "views":
        from .views import build
        manifest = build(args.path)
        n = sum(len(s["files"]) for s in manifest["shards"])
        print(f"agent/: {len(manifest['shards'])} shards, {n} files")
        return 0
    if args.command == "search":
        from .check import Repo
        from .search import Index, search as run_search
        result = run_search(Index.from_repo(Repo.load(args.path)), json.loads(args.filter))
        print(json.dumps(result.to_dict(), indent=1, ensure_ascii=False))
        return 0

    if args.command == "check":
        result = run(args.path)
        for line in result.reports:
            print("report", line)
        for line in result.failures:
            print("FAIL  ", line)
        print(f"\n{len(result.failures)} failure(s)")
        return 0 if result.ok else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())

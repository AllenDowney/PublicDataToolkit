"""Command line: `pdt check [PATH]`, `pdt views [PATH] [--only agent|site|export]`, `pdt search PATH --filter JSON`."""

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
    views = sub.add_parser("views", help="generate agent/, docs/ and export/ for a dataset repo")
    views.add_argument("path", nargs="?", default=".", help="the dataset repo (default: .)")
    views.add_argument("--only", choices=["agent", "site", "export"], help="generate just one of them")
    search = sub.add_parser("search", help="search a dataset repo's records; prints a labeled result")
    search.add_argument("path", help="the dataset repo")
    search.add_argument("--filter", required=True, help='a JSON filter, e.g. \'{"topic": "Abortion"}\'')
    download = sub.add_parser("download", help="fetch a dataset repo's sources (see pdt download -h)",
                              add_help=False)
    download.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    if args.command == "download":
        from .download import main as download_main
        return download_main(args.rest)

    if args.command == "views":
        if args.only in (None, "agent"):
            from .views import build
            manifest = build(args.path)
            n = sum(len(s["files"]) for s in manifest["shards"])
            print(f"agent/: {len(manifest['shards'])} shards, {n} files")
        if args.only in (None, "site"):
            from .site import build as build_site
            manifest = build_site(args.path)
            print(f"docs/: {len(manifest['files'])} files")
        if args.only in (None, "export"):
            from .export import build as build_export
            manifest = build_export(args.path)
            print(f"export/data-dict/: {', '.join(manifest['files'])}")
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

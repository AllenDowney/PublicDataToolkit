"""Command line: `pdt check [PATH]`, `pdt views [PATH] [--only agent|site|export]`, `pdt search PATH --filter JSON [--release ID|all] [--names] [--limit N --offset N]`, `pdt search --catalog PATHS --filter JSON`,
`pdt catalog PATHS --out DIR`, `pdt export daaf [PATH] --domain D`."""

import argparse
import json
import sys

from . import __version__
from .check import run


def dumps(result):
    """JSON with one key per line, but a `names` list on a single line, to keep it short."""
    names = result.pop("names", None)
    text = json.dumps(result, indent=1, ensure_ascii=False)
    if names is None:
        return text
    return text[:-2] + ',\n "names": ' + json.dumps(names, ensure_ascii=False) + "\n}"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pdt", description="PublicDataToolkit tools")
    parser.add_argument("--version", action="version", version=f"pdt {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="check a dataset repo against the standard")
    check.add_argument("path", nargs="?", default=".", help="the dataset repo (default: .)")
    views = sub.add_parser("views", help="generate agent/, docs/ and export/ for a dataset repo")
    views.add_argument("path", nargs="?", default=".", help="the dataset repo (default: .)")
    views.add_argument("--only", choices=["agent", "site", "export"], help="generate just one of them")
    views.add_argument("--release-shards", type=int, default=12, metavar="N",
                       help="with more releases than N, agent table shards cover every release, one line per "
                            "variable, instead of one shard per release (default 12)")
    search = sub.add_parser("search", help="search a dataset repo's records; prints a labeled result")
    search.add_argument("path", nargs="+", help="the dataset repo; with --catalog, repos or directories holding them")
    search.add_argument("--filter", required=True, help='a JSON filter, e.g. \'{"topic": "Abortion"}\'')
    search.add_argument("--catalog", action="store_true",
                        help="search across every included dataset repo (see pdt catalog)")
    search.add_argument("--all-releases", action="store_true", help="with --catalog: superseded releases too")
    search.add_argument("--release", help="releases to search: an id, ids separated by commas, or `all`; "
                                          "default: the current release(s)")
    search.add_argument("--names", action="store_true", help="print only the names of the matches")
    search.add_argument("--limit", type=int, help="print at most this many matches (the total is always given)")
    search.add_argument("--offset", type=int, default=0, help="skip this many matches first")
    cat = sub.add_parser("catalog", help="build a catalog across dataset repos (see pdt catalog -h)", add_help=False)
    cat.add_argument("rest", nargs=argparse.REMAINDER)
    dif = sub.add_parser("diff", help="compare two releases' records (see pdt diff -h)", add_help=False)
    dif.add_argument("rest", nargs=argparse.REMAINDER)
    pkg = sub.add_parser("package", help="assemble the data release asset in data/release/ (ship data only)")
    pkg.add_argument("path", nargs="?", default=".", help="the dataset repo (default: .)")
    exp = sub.add_parser("export", help="export a dataset repo for another tool: `pdt export daaf -h`",
                         add_help=False)
    exp.add_argument("format", choices=["daaf"], help="daaf: a DAAF data-source skill in export/daaf/")
    exp.add_argument("rest", nargs=argparse.REMAINDER)
    download = sub.add_parser("download", help="fetch a dataset repo's sources (see pdt download -h)",
                              add_help=False)
    download.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    if args.command == "diff":
        from .diff import main as diff_main
        return diff_main(args.rest)
    if args.command == "package":
        from .release import package
        try:
            out = package(args.path)
        except ValueError as e:
            print(e, file=sys.stderr)
            return 1
        print(f"wrote {out}; publish it as a GitHub release by hand")
        return 0
    if args.command == "export":
        from .daaf import main as daaf_main
        return daaf_main(args.rest)
    if args.command == "download":
        from .download import main as download_main
        return download_main(args.rest)

    if args.command == "views":
        if args.only in (None, "agent"):
            from .views import build
            manifest = build(args.path, release_shards=args.release_shards)
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
    if args.command == "catalog":
        from .catalog import main as catalog_main
        return catalog_main(args.rest)
    if args.command == "search" and args.catalog:
        from .catalog import search_catalog
        all_releases = args.all_releases or args.release == "all"
        result = search_catalog(args.path, json.loads(args.filter), all_releases,
                                names=args.names, limit=args.limit, offset=args.offset)
        print(dumps(result))
        return 0
    if args.command == "search":
        if len(args.path) != 1:
            parser.error("search takes one repo; use --catalog to search several")
        args.path = args.path[0]
        from .check import Repo
        from .search import Index, default_releases, search as run_search
        repo = Repo.load(args.path)
        filt, note = json.loads(args.filter), None
        if args.release and "release" in filt:
            parser.error("give the release in --release or in the filter, not both")
        if args.release and args.release != "all":
            filt["release"] = args.release.split(",")
        elif not args.release and "release" not in filt:
            scope = default_releases(repo.dataset)
            if len(scope) < len(repo.dataset.get("releases", [])):
                filt["release"] = scope
                note = (f"scope: the current release ({', '.join(scope)}) by default; "
                        "--release all searches every release")
        result = run_search(Index.from_repo(repo), filt)
        print(dumps(result.to_dict(names=args.names, limit=args.limit, offset=args.offset,
                                   scope_note=note)))
        return 0

    if args.command == "check":
        result = run(args.path)
        skipped = set(result.not_run)
        for line in result.reports:
            if line not in skipped:
                print("report", line)
        for line in result.not_run:
            print("not run", line.replace("not run, because ", "because "))
        for line in result.failures:
            print("FAIL  ", line)
        print(f"\n{len(result.failures)} failure(s)")
        return 0 if result.ok else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())

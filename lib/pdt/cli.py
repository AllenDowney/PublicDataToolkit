"""Command line: `pdt check [PATH]`."""

import argparse
import sys

from . import __version__
from .check import run


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pdt", description="PublicDataToolkit tools")
    parser.add_argument("--version", action="version", version=f"pdt {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="check a dataset repo against the standard")
    check.add_argument("path", nargs="?", default=".", help="the dataset repo (default: .)")
    args = parser.parse_args(argv)

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

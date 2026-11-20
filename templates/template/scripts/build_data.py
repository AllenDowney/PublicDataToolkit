#!/usr/bin/env python3
"""Write this dataset's data in the common format (STANDARD.md §8): one file per release and table.

    make data                       # every release
    make data RELEASES="2022 2024"  # some releases

Reads each release's data file in data/raw (its source of kind data in sources.yaml) and
writes data/processed/, holding the variables this repo has records for. Each file is read
back and every cell compared with the source, so the conversion is lossless; only a file
that passes gets its name. Run it under the memory cap the repo's CLAUDE.md gives.

read() picks a reader from pdt.readers by the source's format. For another format (a CSV in
a zip, fixed-width text with a Stata .dct or a SAS input program), write the call here: the
readers in pdt.readers cover those too.
"""

import sys
from pathlib import Path

try:
    from pdt.readers import read_sas, read_sav, read_stata
    from pdt.release import data_source, write_release
except ImportError:
    sys.exit("Needs the PublicDataToolkit library with its data extra: "
             "pip install -e '../PublicDataToolkit[data]', or run through `make data`.")

ROOT = Path(__file__).resolve().parent.parent
READERS = {"stata": read_stata, "sas": read_sas, "spss": read_sav}


def read(release, table, names):
    """The raw frame for these columns, and the source id; None to skip the release."""
    try:
        source = data_source(ROOT, release, table)
    except ValueError as e:
        print(f"  {e}")
        return None
    path = ROOT / source["path"]
    if not path.exists():
        print(f"  {path} is missing; see python scripts/download.py --check")
        return None
    reader = READERS.get(source.get("format"))
    if reader is None:
        print(f"  {source['id']}: no reader for format {source.get('format')!r}; write one in scripts/build_data.py")
        return None
    return reader(path, names), source["id"]


if __name__ == "__main__":
    write_release(ROOT, read, releases=sys.argv[1:] or None)

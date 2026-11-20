"""Names and code texts of the common data format, without pandas (STANDARD.md §8).

The parts of the common format that metadata tools need: the export's column names,
pdt check's metadata checks, the catalog. They're here so those tools run on a plain
install. Reading and writing the parquet files is pdt.data, which needs the `data` extra
(pip install "publicdatatoolkit[data]": pandas, numpy, pyarrow).
"""

import numbers
from pathlib import Path

CODE_SUFFIX = "__code"
ROW = "_row"
PROCESSED = Path("data") / "processed"


def file_name(dataset, release, table=None):
    """The common-format file of a release (or a table of one): <dataset>-<release>[-<table>].parquet."""
    return f"{dataset}-{release}" + (f"-{table}" if table else "") + ".parquet"


def is_number(x):
    """A number, and not a bool (Python's or numpy's)."""
    return isinstance(x, numbers.Number) and not isinstance(x, bool) and type(x).__name__ != "bool_"


def as_float(x):
    """A number as a Python float; a float32 goes through its shortest repr, so 0.1 stays 0.1."""
    dtype = getattr(x, "dtype", None)
    if dtype is not None and dtype.kind == "f" and dtype.itemsize < 8:
        return float(str(x))
    return float(x)


def code_text(code):
    """The text form of a code: integers without a decimal point, other numbers in shortest form."""
    if isinstance(code, str):
        return str(code)
    number = as_float(code)
    return str(int(number)) if number.is_integer() else repr(number)

"""The two commands an agent may use: `read` and `search`. Every call is logged.

Usage (through the shims setup_run.py writes):
    read PATH [FIRST LAST]       a file under the sandbox, or lines FIRST..LAST; a directory is listed
    search DATASET FILTER_JSON [--names] [--limit N] [--offset N] [--release ID|all]
                                 pdt search on that dataset's repo
    search catalog FILTER_JSON   pdt search --catalog across the repos (catalog questions)

Configuration comes from the run's config.json, named by $EVAL_CONFIG:
    sandbox  directory holding <dataset>/agent/
    repos    dataset -> repo path, for search
    pdt_lib  the lib/ directory holding pdt
    python   the interpreter for pdt
    log      the JSONL log
    budget   tokens allowed (characters / 4)
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path


def tokens(text):
    return len(text) // 4


def load():
    with open(os.environ["EVAL_CONFIG"]) as f:
        return json.load(f)


def spent(log):
    if not Path(log).exists():
        return 0
    with open(log) as f:
        return sum(e["tokens"] for e in map(json.loads, f) if e.get("printed"))


def emit(cfg, call, args, text):
    used = spent(cfg["log"])
    n = tokens(text)
    printed = used + n <= cfg["budget"]
    entry = {"time": time.time(), "call": call, "args": args, "chars": len(text),
             "tokens": n, "printed": printed, "spent_after": used + (n if printed else 0)}
    with open(cfg["log"], "a") as f:
        f.write(json.dumps(entry) + "\n")
    if printed:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")
        return 0
    sys.stdout.write(f"REFUSED: this output is {n} tokens and you have "
                     f"{cfg['budget'] - used} of {cfg['budget']} left. Nothing was printed.\n")
    return 3


def do_read(cfg, args):
    if not args:
        return emit(cfg, "read", args, "usage: read PATH [FIRST LAST]")
    root = Path(cfg["sandbox"]).resolve()
    path = (root / args[0]).resolve()
    if root not in path.parents and path != root:
        return emit(cfg, "read", args, f"error: {args[0]} is outside the sandbox")
    if not path.exists():
        return emit(cfg, "read", args, f"error: no such file or directory: {args[0]}")
    if path.is_dir():
        names = sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir())
        return emit(cfg, "read", args, "\n".join(names))
    lines = path.read_text().splitlines(keepends=True)
    if len(args) == 3:
        first, last = int(args[1]), int(args[2])
        lines = lines[first - 1:last]
    return emit(cfg, "read", args, "".join(lines))


# pdt search's output options (Task 53), passed through as given.
OPTIONS = {"--names": 0, "--limit": 1, "--offset": 1, "--release": 1}


def split_options(rest):
    """(options, error) from the arguments after DATASET FILTER_JSON."""
    out, i = [], 0
    while i < len(rest):
        opt = rest[i]
        if opt not in OPTIONS:
            return None, f"unknown option {opt}; options: {', '.join(OPTIONS)}"
        n = OPTIONS[opt]
        if n and i + n >= len(rest):
            return None, f"{opt} needs a value"
        out += rest[i:i + 1 + n]
        i += 1 + n
    return out, None


def do_search(cfg, args):
    opts, err = split_options(args[2:]) if len(args) >= 2 else ([], None)
    if err:
        return emit(cfg, "search", args, "error: " + err)
    args = args[:2] + opts
    if len(args) >= 2 and args[0] == "catalog" and cfg.get("catalog"):
        env = dict(os.environ, PYTHONPATH=cfg["pdt_lib"])
        proc = subprocess.run([cfg["python"], "-m", "pdt", "search", "--catalog", cfg["catalog"],
                               "--filter", args[1], *opts], capture_output=True, text=True, env=env)
        text = proc.stdout if proc.returncode == 0 else "error: " + proc.stderr.strip().splitlines()[-1]
        return emit(cfg, "search", args, text)
    if len(args) < 2 or args[0] not in cfg["repos"]:
        return emit(cfg, "search", args,
                    f"usage: search DATASET FILTER_JSON; datasets: {', '.join(cfg['repos'])}")
    env = dict(os.environ, PYTHONPATH=cfg["pdt_lib"])
    proc = subprocess.run([cfg["python"], "-m", "pdt", "search", cfg["repos"][args[0]],
                           "--filter", args[1], *opts], capture_output=True, text=True, env=env)
    text = proc.stdout if proc.returncode == 0 else "error: " + proc.stderr.strip().splitlines()[-1]
    return emit(cfg, "search", args, text)


def main():
    cfg = load()
    call, args = sys.argv[1], sys.argv[2:]
    return {"read": do_read, "search": do_search}[call](cfg, args)


if __name__ == "__main__":
    sys.exit(main())

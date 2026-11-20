"""Set up one run: a sandbox with copies of agent/, the command shims, and the run directory.

Usage: python eval/harness/setup_run.py RUN_ID QUESTION SANDBOX_BASE [--budget N] [--repos DIR]

--repos DIR runs against copies of the repos in DIR (e.g. `git archive HEAD` of each, with a
COMMITS file naming the commits, which the run's config records), instead of the working
trees next to this repo. Task 51 uses it so that work in progress in a repo can't leak in.

Creates SANDBOX_BASE/RUN_ID/<dataset>/agent/ and SANDBOX_BASE/RUN_ID/bin/{read,search},
and eval/runs/RUN_ID/ with config.json and prompt.md (the words given to the agent, with the
sandbox path replaced by <sandbox>). The *.local.* files hold the real paths and aren't committed.
"""

import argparse
import json
import shutil
import stat
import sys
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1]
PDT = EVAL.parent
DATASETS = {"gss": "pdt-gss", "anes-cdf": "pdt-anes-cdf", "nsfg": "pdt-nsfg", "catalog": "pdt-catalog"}

RELIGION = (
    "Find every variable, in all three datasets (GSS, ANES CDF and NSFG), about religion: "
    "religious affiliation or preference, how often the respondent attends religious services, "
    "how important religion is to them, prayer, or religious belief (for example, views about "
    "the Bible). In the NSFG, a variable that appears in several tables counts once per table.")
BALLOT_A = ("In the GSS, list every variable that was asked of (or has a value for) respondents who "
            "got ballot A in 1988.")

# The question text, word for word as in PROTOCOL.md.
QUESTIONS = {
    "religion": (["gss", "anes-cdf", "nsfg"], RELIGION),
    "gss_ballot_a_1988": (["gss"], BALLOT_A),
    "anes_therm_1978": (
        ["anes-cdf"],
        "In the ANES CDF, list every feeling thermometer that was asked in 1978."),
    # Task 51: the same questions on the full GSS release, and two new ones.
    "religion_full": (["gss", "anes-cdf", "nsfg"], RELIGION),
    "gss_ballot_a_1988_full": (["gss"], BALLOT_A),
    "gss_spending_2024": (
        ["gss"],
        "In the GSS, list every variable asked in 2024 that asks whether we're spending too much, "
        "too little or about the right amount on something."),
    # Task 57: the second topic, with a key built blind by an agent.
    "gss_mental_health_full": (
        ["gss"],
        "In the GSS, find every variable about the respondent's own mental health: how often they "
        "felt sad, depressed, anxious, stressed or lonely, their mental-health diagnoses, days of "
        "poor mental health, and treatment or help they sought for emotional problems."),
    "catalog_sadness": (
        ["catalog"],
        "Which datasets ask about sadness or hopelessness, and in which years? List every variable, "
        "in any dataset in the catalog, that asks whether or how often the respondent felt sad, "
        "depressed, down or hopeless, with the years it was asked."),
}

def key_version(question):
    """The current key's version (keys/<question>.yaml `version`, 1 if it has none)."""
    import yaml
    path = Path(__file__).resolve().parents[1] / "keys" / f"{question}.yaml"
    return yaml.safe_load(path.read_text()).get("version", 1) if path.exists() else None


CATALOG_RULES = """- The catalog is in `{sandbox}/catalog/agent/`. Start with its `index.md`.
- Read files ONLY with `{sandbox}/bin/read PATH [FIRST LAST]` (PATH relative to `{sandbox}`;
  FIRST and LAST are line numbers; a directory path lists it). Search ONLY with
  `{sandbox}/bin/search catalog FILTER_JSON [OPTIONS]`, which runs `pdt search --catalog` across
  every dataset in the catalog; OPTIONS are `--names`, `--limit N` and `--offset N` (see index.md). Run them with the Bash tool. Don't use cat, grep, ls, the Read tool or
  any other way of looking at files, and don't look anywhere else on disk."""


PROMPT = """You are being evaluated on finding survey variables using generated metadata files.

## Question

{question}

## Rules

- The metadata is in `{sandbox}`, which holds {dirs}. Start with each `agent/SKILL.md`.
- Read files ONLY with `{sandbox}/bin/read PATH [FIRST LAST]` (PATH relative to `{sandbox}`;
  FIRST and LAST are line numbers; a directory path lists it). Search ONLY with
  `{sandbox}/bin/search DATASET FILTER_JSON [OPTIONS]`, where DATASET is one of {datasets} and
  OPTIONS are `pdt search`'s `--names`, `--limit N`, `--offset N` and `--release ID|all` (see
  SKILL.md). Run them with
  the Bash tool. Don't use cat, grep, ls, the Read tool or any other way of looking at files, and
  don't look anywhere else on disk.
- Everything these commands print counts against a budget of {budget:,} tokens (characters / 4).
  A call that would go over is refused. Spend the budget as you see fit.
- When done, write your answer with the Write tool to `{answer}`, as JSON:

```json
{{"question": "{qid}",
 "label": "complete | complete_by_rule | approximate",
 "items": [{{"dataset": "gss", "table": null, "name": "relig"}}],
 "sources": ["the shards and searches you relied on"],
 "notes": "anything you were unsure about, and why you chose the label"}}
```

`dataset` is one of {datasets}. `table` is the NSFG table (female, male or pregnancy), else null.
The label applies to the whole answer and must follow the rules in SKILL.md.

Finish with a short message giving the number of items, the label, and every command you ran.
"""


def make_shim(path, call, config):
    path.write_text(f"#!/bin/sh\nEVAL_CONFIG='{config}' exec '{sys.executable}' "
                    f"'{EVAL / 'harness/tool.py'}' {call} \"$@\"\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run_id")
    p.add_argument("question", choices=QUESTIONS)
    p.add_argument("sandbox_base")
    p.add_argument("--budget", type=int, default=40_000)
    p.add_argument("--repos", help="directory holding copies of the repos (see the docstring)")
    a = p.parse_args()
    repos_base = Path(a.repos).resolve() if a.repos else PDT.parent

    datasets, question = QUESTIONS[a.question]
    sandbox = Path(a.sandbox_base).resolve() / a.run_id
    run = EVAL / "runs" / a.run_id
    if sandbox.exists() or run.exists():
        sys.exit(f"{sandbox} or {run} exists already")
    run.mkdir(parents=True)
    corpus = {}
    for ds in datasets:
        src = repos_base / DATASETS[ds] / "agent"
        shutil.copytree(src, sandbox / ds / "agent")
        corpus[ds] = sum(len(f.read_text()) // 4 for f in src.rglob("*") if f.is_file())
    (sandbox / "bin").mkdir()
    config = {
        "run_id": a.run_id, "question": a.question, "sandbox": str(sandbox),
        "repos": {ds: str(repos_base / DATASETS[ds]) for ds in datasets if ds != "catalog"},
        "catalog": str(repos_base) if "catalog" in datasets else None,
        "commits": ((repos_base / "COMMITS").read_text().splitlines()
                    if (repos_base / "COMMITS").exists() else None),
        "pdt_lib": str(PDT / "lib"), "python": sys.executable,
        "log": str(run / "log.jsonl"), "budget": a.budget, "corpus_tokens": corpus,
        # The version of the key the run will be scored against (score.py); never shown to the agent.
        "key_version": key_version(a.question),
    }
    (run / "config.local.json").write_text(json.dumps(config, indent=1) + "\n")
    public = {k: v for k, v in config.items()
              if k in ("run_id", "question", "budget", "corpus_tokens", "commits", "key_version")}
    (run / "config.json").write_text(json.dumps(public, indent=1) + "\n")
    for call in ("read", "search"):
        make_shim(sandbox / "bin" / call, call, run / "config.local.json")
    prompt = PROMPT.format(
        question=question, sandbox=sandbox, budget=a.budget, qid=a.question,
        dirs=", ".join(f"`{ds}/agent/`" for ds in datasets),
        datasets=", ".join(f"`{ds}`" for ds in datasets), answer=run / "answer.json")
    if "catalog" in datasets:
        # Across datasets: the catalog's rules, any dataset id, and the years for each item.
        rules = prompt.split("## Rules\n\n", 1)[1].split("- Everything these commands", 1)[0]
        prompt = prompt.replace(rules, CATALOG_RULES.format(sandbox=sandbox) + "\n")
        prompt = prompt.replace("must follow the rules in SKILL.md.",
                                "must follow the rules in the catalog's index.md.")
        prompt = prompt.replace(
            '"items": [{"dataset": "gss", "table": null, "name": "relig"}],',
            '"items": [{"dataset": "gss", "table": null, "name": "sad", "waves": [1996]}],')
        prompt = prompt.replace(
            "`dataset` is one of `catalog`. `table` is the NSFG table (female, male or pregnancy), else null.",
            "`dataset` is the dataset's id in the catalog. `table` is the table, if the dataset has "
            "tables, else null. `waves` are the years the variable was asked.")
    (run / "prompt.local.md").write_text(prompt)
    (run / "prompt.md").write_text(
        prompt.replace(str(run), "<run>").replace(str(sandbox), "<sandbox>"))
    print(run / "prompt.local.md")


if __name__ == "__main__":
    main()

# Evaluation of agent search

Task 23 on the [board](../PROJECT_BOARD.md). Measures whether an agent that reads only a dataset repo's `agent/` directory, with `pdt search`, finds what a question asks for, labels it correctly, and how much it reads.

| Path | What |
|---|---|
| [`PROTOCOL.md`](PROTOCOL.md) | questions, hits, budget, scores; written before any run |
| [`keys/`](keys/) | answer keys, one YAML file per question |
| [`keys/build_structural.py`](keys/build_structural.py) | builds the structural keys from `metadata/` |
| [`keys/full/`](keys/full/) | religion keys for the full releases, for when the repos cover them |
| [`harness/`](harness/) | `setup_run.py` makes a sandbox and prompt; `tool.py` is the logged `read` and `search` |
| [`score.py`](score.py) | recall, precision, tokens read, label check |
| [`runs/`](runs/) | one directory per run: prompt, log, answer, score |
| [`RESULTS.md`](RESULTS.md) | scores and findings |

## Running

```bash
python eval/harness/setup_run.py RUN_ID QUESTION SANDBOX_DIR   # prints the prompt file
# give the prompt to a fresh agent; it writes eval/runs/RUN_ID/answer.json
python eval/score.py eval/runs/RUN_ID
pytest eval/
```

Use the `CultureWar` conda env (it has PyYAML). The dataset repos must be checked out next to this one.

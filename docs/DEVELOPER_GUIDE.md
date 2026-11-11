# ridi-check developer guide

For developers who connect an assistant to ridi-check, put it in a pipeline, or change the tool.
Arabic version: [DEVELOPER_GUIDE.ar.md](DEVELOPER_GUIDE.ar.md). Users start with the
[user guide](USER_GUIDE.md).

## Install and test

```bash
pip install -e ".[test]"
```

```bash
pytest
```

Python 3.10 or later. No runtime dependencies. The tests need no network and no API key.

## How it fits together

```
questions.csv ─┐
current  ──────┼─ run ──> raw_outputs.jsonl ──> results.csv ──┬─ report ──> summary.json
proposed ──────┘          run_manifest.json                   │             review_cases.csv
                                                              │             report.html
                                         (or made by hand) ───┴─ gate ────> exit status
```

| Module | Job |
|---|---|
| `adapters.py` | Turn a system definition into `answer(question)`. Python, command and http. |
| `runner.py` | `run`: plan the calls, record every attempt, resume, write `results.csv`. |
| `contract.py` | Read and validate `results.csv`. Every rejection names the row. |
| `analysis.py` | Case states and first-run rates. The only place the rules live. |
| `scoring.py` | Exact match after normalisation, or a user function. No model judge. |
| `report.py`, `strings.py`, `report_template.html` | The three report files. The page does no analysis. |
| `gate.py` | Counts against limits. |
| `cli.py` | Arguments, `ridi-check.json`, `demo`, `init`. |
| `web/` | The browser version: `core.js` is a port of the analysis, `app.js` the page. `python tools/build_web.py` builds `web/ridi-update-check.html`. `tests/test_web.py` runs `core.js` in Node against the Python on random files. |

## Connecting an assistant

The interface is one function:

```python
def answer(question: str) -> dict:
    return {"answer": "text", "context": ["doc-12", "doc-40"]}   # context may be None
```

Returning a plain string is accepted. Anything else is recorded as a failed call.

| Definition | Use it when | Notes |
|---|---|---|
| `python:module:function` | You can import the assistant | Called from `--concurrency` threads. The current folder is importable. No timeout can be enforced on a Python function. |
| `command:<shell command>` | The assistant is a program in any language | Question on stdin, UTF-8. Stdout, also UTF-8, is JSON with `answer` (and `context`), or plain text. Non-zero exit is a failed call. `RIDI_CHECK_CASE_ID`, `RIDI_CHECK_VERSION` and `RIDI_CHECK_RUN` are set. |
| `http://…` or `https://…` | The assistant is a service | POSTs `{"question": …}`, reads `answer` and `context` from the JSON reply. |
| `path/to/system.json` | The request or reply has another shape | See below. |

Ready-made adapters for an OpenAI-compatible HTTP API, the Claude API and a shell command are in
[examples/adapters](../examples/adapters/README.md). A JSON definition for an OpenAI-style chat endpoint:

```json
{
  "type": "http",
  "url": "https://example.internal/v1/chat/completions",
  "headers": {"Authorization": "Bearer ${MY_API_KEY}"},
  "request": {"model": "my-model", "messages": [{"role": "user", "content": "{question}"}]},
  "answer_path": "choices.0.message.content",
  "context_path": "sources.*.title",
  "timeout": 60
}
```

`{question}` is replaced inside any string of `request`. Paths are dotted; a number indexes a list
and `*` maps over one. `${NAME}` is read from the environment when the run starts. The definition
is copied into `run_manifest.json` as given, so a literal key in it would be copied too: ridi-check
warns when a credential-like header holds a literal value.

A function or command that fails should raise, or exit non-zero: the call is recorded as failed and tried
again. From a Python function you can tell the runner more by setting attributes on the exception you
raise: `retry_after` (seconds to wait before the next attempt; no other call starts meanwhile),
`retryable = False` (do not try this call again) and `service_failure = True` (the service is refusing
every call; ten of these in a row stop the run). The http adapter sets them from the status code and the
`Retry-After` header; see the [reference](REFERENCE.md#ridi-check-run).

The two versions must differ only in what the update changes. A typical Python adapter:

```python
def ask(question, version):
    model = "model-2025" if version == "current" else "model-2026"
    reply = client.chat(model=model, system=PROMPT, user=question)
    return reply.text, [s.title for s in reply.sources]
```

## Settings file

`ridi-check run` reads `ridi-check.json` from the current folder (or `--config FILE`). Keys are the
long option names with underscores: `questions`, `current`, `proposed`, `out`, `runs`, `limit`,
`concurrency`, `retries`, `retry_wait`, `timeout`, `scorer`, `current_label`, `proposed_label`,
`report`, `similarity`, `open`. Command-line options win. Paths are relative to the file's folder;
ridi-check changes into that folder before running.

## Scoring

With `expected` in the questions file, each answer gets 0 or 1. Default: equal after lower-casing,
replacing punctuation by spaces and collapsing whitespace. Your own:

```python
def scorer(answer: str, expected: str) -> bool:
    return expected.lower() in answer.lower()
```

Pass it as `--scorer module:function`. Model-based judging is out of scope: a judge adds its own
error, and the tool would then measure the judge as well as the assistant.

## Files

**`raw_outputs.jsonl`**, one line per attempt, appended and flushed as it completes, never rewritten:

```json
{"case_id": "q07", "version": "proposed", "run": 2, "attempt": 1, "max_attempts": 3, "status": "ok",
 "answer": "…", "context": ["…"], "error": null, "started_at": "…", "ended_at": "…"}
```

`status` is `ok` or `failed`. A call counts as done when it has one `ok` line. On restart those are
skipped and the rest are tried again. A line cut short by a kill is left in place and ignored.

**`run_manifest.json`**: SHA-256 of the questions file, both definitions as given (and the hash of a
definition file or of the Python source file), run count, concurrency, retries, scorer, tool version
and one entry per invocation with its timestamps and counts. A second run into the same folder with
a different questions file or definition is refused; changed Python source is reported, not refused,
because fixing a broken adapter and resuming is a normal thing to do.

**`results.csv`**: the contract in the [reference](REFERENCE.md#resultscsv). `run` writes it only after
an invocation finishes. You can also write it yourself and use `report` and `gate` alone.

**`summary.json`**: `mode`, `cases`, `cases_compared`, `runs_per_version`, `states` (count per state),
`case_ids`, `first_run` (`change_between_versions`, `rerun_variation_current`,
`rerun_variation_proposed`, each as `{count, n, rate}`; in answer-key mode also the accuracies,
`regressions`, `improvements`, `changes_visible_in_mean_accuracy`,
`changes_cancelled_in_mean_accuracy`), `any_run_disagreement`, `judgments` or
`wrong_both_answer_changed` and `correct_both_answer_changed` (case ids whose score is equal and whose
answer is not), and `notes`.

**`review_cases.csv`**: every case that is not same / correct in both, with all its runs under their
contract column names, so the file can be read back by `report`.

## The rules, exactly

Per case, with the runs of each version as a list (`analysis.classify`):

1. Any run of a version differs from that version's first run: `unstable`.
2. Else the first runs of the two versions are equal: `correct_both`, `wrong_both`, or `same`.
3. Else `stable_regression` (1 to 0), `stable_improvement` (0 to 1) or `stable_change`. With one run
   of either version the label is `*_unconfirmed`.

"Equal" is equal correctness in answer-key mode and equal normalised answers otherwise. With
`--similarity X` below 1, answers also count as equal when their word sets overlap by at least X
(Jaccard) and they contain the same numbers and agree on whether a negation word is present.

Rates use first runs. Change between versions is the share of cases whose first runs differ; in
answer-key mode it equals regressions plus improvements, the mean accuracy moves by their
difference, and `2 × min(regressions, improvements)` changes cancel out in the mean. Re-run
variation is run 1 against run 2 of the same version, reported for both versions. The tool never
subtracts a re-run variation from the change and reports no test or interval; `summary.json` has the
counts if you want to compute your own.

Additions to the browser prototype: `incomplete` (a first-run call failed; left out of every rate),
`any_run_disagreement`, and the flag for a `wrong_both` case whose answer changed.

## Use it in CI

A complete workflow to copy is in [examples/ci/ridi-check.yml](../examples/ci/ridi-check.yml). The steps:

```yaml
- run: pip install ridi-check
- run: ridi-check run --config check/ridi-check.json --out "ridi-out-${{ github.sha }}"
  env:
    MY_API_KEY: ${{ secrets.MY_API_KEY }}
- run: ridi-check gate "check/ridi-out-${{ github.sha }}/results.csv" --max-stable-regressions 0
- uses: actions/upload-artifact@v4
  if: always()
  with: { name: ridi-report, path: check/ridi-out-* }
```

| Exit status | `run` | `report` | `gate` |
|---|---|---|---|
| 0 | all calls recorded | written | every count within its limit |
| 1 | finished, some calls failed | – | a limit was exceeded |
| 2 | bad input, or the first calls all failed | bad input | bad input |
| 130 | interrupted; resume by running again | – | – |

The gate prints counts and offending cases. It never prints a verdict about the system.

## Use it as a library

```python
from ridi_check.contract import read_results
from ridi_check.analysis import analyse
from ridi_check.report import build_summary, write_report

cases, mode = read_results("results.csv")          # mode is "key" or "nokey"
analysis = analyse(cases, mode, threshold=1.0)
print(analysis.counts, analysis.ids("stable_regression"))
summary = build_summary(analysis)
write_report("results.csv", "out")                  # the three report files
```

`ridi_check.runner.run(RunConfig(...))` runs the calls; `ridi_check.gate.evaluate(analysis)` returns
the gate lines and whether a limit was exceeded. The API may change before 1.0.

## Changing the tool

- A new state or rate goes in `analysis.py` with a test, and in `web/core.js`; the parity test fails until
  both agree. The report page written by `report` must not compute anything.
- Text shown to people goes in `strings.py`, in English and Arabic, and follows the wording rules:
  without an answer key or a judgment a difference is a "change", never a "regression"; a passage
  with no relevance grade is "ungraded"; nothing says or implies safe, certified or approved; where
  "stable" is explained, say that two runs is a thin estimate. `tests/test_report_gate.py` checks these.
- A new adapter type is a function in `adapters.py` returning `answer(question, meta)`, plus a branch
  in `parse_definition` and `build_adapter`.
- `examples/toy_assistant.py` and `src/ridi_check/demo/toy_assistant.py` are the same file; a test
  fails if they differ.

## How it is tested

`pytest` covers a 40-case synthetic fixture in both modes, every CSV rejection, resume after
an interruption, recorded failed calls, the three adapters (http against a local server), the report
and gate wording, the first-use commands, and seeded random files checked against invariants
(states partition the cases; "stable" implies two runs of both versions; changed = regressions +
improvements; `review_cases.csv` reads back to the same states).

## Known limits

- A Python adapter that hangs is not interrupted. Put a timeout inside your function.
- `python:` adapters are called from several threads. Use `--concurrency 1` if yours is not thread-safe.
- Answers are written to CSV as they are. A spreadsheet program may treat a cell that starts with
  `=` as a formula; open untrusted results as text.
- CI runs the tests on Linux, macOS and Windows with Python 3.10 and 3.13.
- Agents that use tools or keep state, statistical tests and model-based judging are out of scope.

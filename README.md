# ridi-check

A new model or an edited prompt can change what your assistant or agent answers without anyone noticing:
average accuracy barely moves while individual answers flip. ridi-check runs the old and the new version on
the same questions, more than once, and shows which answers changed and which changes hold on re-run.

## Stop a silent change in CI

```yaml
- run: pip install git+https://github.com/adeebnoor/ridi-check
- run: ridi-check run --config ridi-check.json     # calls both versions, writes ridi-out/results.csv
- run: ridi-check gate ridi-out/results.csv        # exits 1 on a stable regression
```

A complete workflow to copy: [examples/ci/ridi-check.yml](examples/ci/ridi-check.yml).
**No install:** the browser version is one file, [web/ridi-update-check.html](web/ridi-update-check.html).
Download it, open it, paste your results (CSV text or cells copied from a spreadsheet). Nothing leaves the page.

It works with or without an answer key, in English and Arabic, and follows the RIDI method.

## Start in one minute

Python 3.10 or later, no dependencies. The demo needs no network and no API key; its data is synthetic.

```bash
pip install git+https://github.com/adeebnoor/ridi-check
```

```bash
ridi-check demo --open
```

Then check your own assistant:

```bash
ridi-check init my-check
```

It writes `questions.csv`, `my_assistant.py` (one function to fill in), `ridi-check.json` and
`ASK_YOUR_AI.md`, a prompt that lets your AI coding assistant do the wiring. Then, in that folder,
`ridi-check run --limit 5` for a first try and `ridi-check run` for everything.

**Guides:** [user guide](docs/USER_GUIDE.md) · [use cases](docs/USE_CASES.md) ·
[developer guide](docs/DEVELOPER_GUIDE.md) · بالعربية: [دليل الاستخدام](docs/USER_GUIDE.ar.md) ·
[حالات الاستخدام](docs/USE_CASES.ar.md) · [دليل المطورين](docs/DEVELOPER_GUIDE.ar.md)

## Commands

**`ridi-check run`** calls both versions `--runs N` times (default 2) on every question and writes
`raw_outputs.jsonl` (every attempt, as it completes), `run_manifest.json` and `results.csv`. A failed call is
recorded as failed and its case stays in the file. Run the same command again to resume: recorded calls are
skipped, failed ones are retried, nothing is deleted. Settings come from the command line or from
`ridi-check.json`: `--questions`, `--current`, `--proposed`, `--out`, `--limit`, `--concurrency 4`,
`--retries 2`, `--timeout`, `--scorer module:function`, `--report`, `--open`.
The questions file is CSV or JSONL with `case_id`, `question` and optionally `expected`. With `expected`,
answers are scored by exact match after normalisation, or by your `scorer(answer, expected)`. No model judge.

**`ridi-check report results.csv`** writes `summary.json`, `review_cases.csv` (every case that is not
same / correct in both, with all its runs) and `report.html`: one file, offline, English and Arabic.
Options: `--mode nokey`, `--similarity 0.9`, `--judgments judgments.csv`, `--lang ar`, `--open`. Without an
answer key you judge only the stable changes: in the report, or in a `judgments.csv` with `case_id` and
`judgment` (`worse|better|same_meaning|unsure`).

**`ridi-check gate results.csv`** is for a deploy script. It prints counts and one line per offending case,
and exits 1 when stable regressions exceed `--max-stable-regressions` (default 0), when, with no answer key,
unjudged stable changes exceed `--max-unjudged-changes` (default 0), or when cases could not be compared
(`--max-incomplete`, default 0). Exit 2 means the file was not usable.

**`ridi-check demo`** and **`ridi-check init`** create the example and the starter folder shown above.
`init --by-hand` writes a results template for people who already have the answers in a spreadsheet.

## Writing an adapter

A system is one function: `answer(question: str) -> {"answer": str, "context": list[str] | None}`.
`context` holds the ids or titles of the passages the answer used, if any. Pass a system as
`python:module:function`, `command:<shell command>` (question on stdin, JSON or text on stdout), an
`http://` URL (POSTs `{"question": ...}`), or a JSON definition file for other request shapes.
Keep secrets in `${ENV_VARS}`. Details and examples: [developer guide](docs/DEVELOPER_GUIDE.md).

## `results.csv`

One row per question. You can also make this file by hand and skip `run`.

| Column | Required | Meaning |
|---|---|---|
| `case_id` | yes | unique |
| `question`, `expected` | no | shown in the report |
| `baseline_answer`, `updated_answer` | yes, unless the `_correct` columns are given | first run of the current and the proposed version |
| `baseline_repeat_answer`, `updated_repeat_answer` | no | second run; then `baseline_repeat2_answer`, and so on |
| `baseline_correct`, `updated_correct` | no | 0 or 1; present means answer-key mode |
| `baseline_repeat_correct`, `updated_repeat_correct` | no | 0 or 1 for the repeats |
| `baseline_context`, `updated_context` | no | passage ids or titles separated by ` \| ` |
| `run_errors` | no | written by `run` when a call failed; such a case is `incomplete` |

Missing or duplicate `case_id`, non-binary `_correct` values and files with neither answers nor correctness
are rejected, with the row.

## How cases are labelled

With an answer key two runs are equal when their correctness is equal; without one, when the answers match
after lower-casing, removing punctuation and collapsing spaces (or share `--similarity` of their words).

1. Any run of a version differs from that version's first run: `unstable`.
2. Else the first runs of the two versions are equal: `correct_both` / `wrong_both`, or `same`.
3. Else `stable_regression` / `stable_improvement`, or `stable_change` without a key. With a single run of
   either version the label is `*_unconfirmed`: "stable" needs at least two runs of both versions.

The rates use first runs: change between versions, and the re-run variation of each version (run 1 against
run 2). Both variations are always shown and neither is subtracted from the change.

## Limits

- It finds change, not correctness. Cases wrong in both versions are listed separately.
- Without an answer key or your judgment, a difference is a change, not a regression.
- Passages are shown as they differ and are not graded; an ungraded passage can still carry the evidence.
- Two runs is a thin estimate of re-run variation. More runs make the stable label firmer.
- It is not a safety certificate. No output says a system is fit to deploy; the gate prints counts.
- Not in this version: agents that use tools or keep state, model-based judging, statistical tests.

## Licence

MIT. See [LICENSE](LICENSE).

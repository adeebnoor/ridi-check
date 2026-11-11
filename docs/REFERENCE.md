# ridi-check reference

Every command, file and rule in one place. New here? Start with the
[README](https://github.com/adeebnoor/ridi-check#readme) or the [user guide](USER_GUIDE.md).

- [Commands](#commands)
- [Settings file](#settings-file)
- [Questions file](#questions-file)
- [`results.csv`](#resultscsv)
- [How cases are labelled](#how-cases-are-labelled)
- [Files written](#files-written)
- [Exit status](#exit-status)

## Commands

### `ridi-check demo [DIR]`

Creates a folder (default `ridi-demo`) with a toy assistant in two versions, runs the check and writes the
report. Synthetic data, no network, no API key. `--open` opens the report in your browser.

### `ridi-check init [DIR]`

Writes a starter folder: `questions.csv`, `my_assistant.py` (one function to fill in), `ridi-check.json` and
`ASK_YOUR_AI.md`, a prompt that lets an AI coding assistant do the wiring. Existing files are left as they
are. `--by-hand` writes only `results_template.csv`, for people who already have the answers in a spreadsheet.

### `ridi-check run`

Calls the current and the proposed version on every question, `--runs` times each, and writes
`raw_outputs.jsonl`, `run_manifest.json` and `results.csv`. A failed call is recorded as failed and its case
stays in the file. Run the same command again to resume: recorded calls are skipped, failed ones are retried,
nothing is deleted.

| Option | Default | Meaning |
|---|---|---|
| `--questions FILE` | – | CSV or JSONL with `case_id`, `question` and optionally `expected` |
| `--current SYSTEM`, `--proposed SYSTEM` | – | the two versions; see [adapters](DEVELOPER_GUIDE.md#connecting-an-assistant) |
| `--out DIR` | – | output directory |
| `--config FILE` | `ridi-check.json` if present | settings file; command-line options win |
| `--runs N` | 2 | runs per version; "stable" needs at least 2 |
| `--limit N` | all | use only the first N questions, for a cheap first try |
| `--concurrency N` | 4 | calls in flight at once |
| `--retries N` | 2 | extra attempts after a failed call |
| `--retry-wait SECONDS` | 1 | wait before the first retry; doubles each time |
| `--timeout SECONDS` | 120 | limit for one command or http call |
| `--scorer MODULE:FUNCTION` | exact match | `scorer(answer, expected)` returns true when correct |
| `--current-label TEXT`, `--proposed-label TEXT` | – | shown in the report |
| `--report` | off | also write the report files |
| `--similarity X` | 1 | with `--report`; see `report` |
| `--open` | off | with `--report`: open it in your browser |

`run` stops early when the first calls all fail, so a broken connection does not burn through every question.

### `ridi-check report RESULTS.csv`

Writes `summary.json`, `review_cases.csv` and `report.html` next to the results file (or in `--out DIR`).

| Option | Default | Meaning |
|---|---|---|
| `--mode auto\|key\|nokey` | auto | `nokey` ignores the correctness columns and compares the answers |
| `--similarity X` | 1 | without an answer key, count two answers as the same when they share this share of their words (for example 0.9), contain the same numbers and agree on negation |
| `--judgments FILE` | – | your calls on the stable changes: `case_id`, `judgment` (`worse`, `better`, `same_meaning`, `unsure`) |
| `--current-label TEXT`, `--proposed-label TEXT` | from the manifest | shown in the report |
| `--lang en\|ar` | reader's language | language the report opens in |
| `--open` | off | open the report in your browser |

### `ridi-check gate RESULTS.csv`

Prints the counts and one line per offending case. It prints no verdict about the system.

| Option | Default | Meaning |
|---|---|---|
| `--max-stable-regressions N` | 0 | with an answer key: stable regressions allowed. Without one: stable changes you judged worse |
| `--max-unjudged-changes N` | 0 | without an answer key: stable changes with no judgment, or judged unsure |
| `--max-incomplete N` | 0 | cases that could not be compared because a call failed |
| `--mode`, `--similarity`, `--judgments` | as for `report` | |

## Settings file

`ridi-check run` reads `ridi-check.json` from the current folder, or the file given with `--config`. Its keys
are the long option names with underscores: `questions`, `current`, `proposed`, `out`, `runs`, `limit`,
`concurrency`, `retries`, `retry_wait`, `timeout`, `scorer`, `current_label`, `proposed_label`, `report`,
`similarity`, `open`. Paths are relative to the file's folder.

```json
{
  "questions": "questions.csv",
  "current": "python:my_assistant:answer_current",
  "proposed": "python:my_assistant:answer_proposed",
  "runs": 2,
  "out": "ridi-out",
  "report": true
}
```

## Questions file

CSV (comma, tab or semicolon separated) or JSONL, one question per row.

| Column | Required | Meaning |
|---|---|---|
| `case_id` | yes | short and unique |
| `question` | yes | what is sent to both versions |
| `expected` | no | a reference answer; if present, it must be filled for every row |

With `expected`, each answer is scored 0 or 1: equal after lower-casing, replacing punctuation by spaces and
collapsing whitespace, or by your `--scorer`. No model judges the answers.

## `results.csv`

One row per question. `run` writes it; you can also make it by hand and use `report` and `gate` alone.

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
are rejected, with the row number as a spreadsheet shows it.

## How cases are labelled

With an answer key two runs are equal when their correctness is equal; without one, when the answers match
after lower-casing, removing punctuation and collapsing spaces (or under `--similarity`).

1. Any run of a version differs from that version's first run: `unstable`.
2. Else the first runs of the two versions are equal: `correct_both` / `wrong_both`, or `same`.
3. Else `stable_regression` / `stable_improvement`, or `stable_change` without a key. With a single run of
   either version the label is `*_unconfirmed`: "stable" needs at least two runs of both versions.

A case whose first-run call failed is `incomplete` and is left out of every rate. A `wrong_both` case whose
wrong answer changed keeps its state and is flagged, because correctness counting alone does not see it.

The rates use first runs: the change between versions, and the re-run variation of each version (run 1
against run 2). Both variations are always shown and neither is subtracted from the change. With an answer
key the change equals regressions plus improvements, mean accuracy moves by their difference, and
`2 × min(regressions, improvements)` changes cancel out in the mean.

## Files written

| File | Written by | Holds |
|---|---|---|
| `raw_outputs.jsonl` | `run` | one line per attempt, appended as it completes, never rewritten |
| `run_manifest.json` | `run` | hash of the questions file, both definitions, settings, one entry per invocation |
| `results.csv` | `run` | the table above |
| `summary.json` | `report` | counts per state, case ids, first-run rates |
| `review_cases.csv` | `report` | every case that is not same / correct in both, with all its runs; can be read back by `report` |
| `report.html` | `report` | one self-contained page, English and Arabic, light and dark |

Field-by-field descriptions are in the [developer guide](DEVELOPER_GUIDE.md#files).

## Exit status

| Status | `run` | `report` | `gate` |
|---|---|---|---|
| 0 | all calls recorded | written | every count within its limit |
| 1 | finished, some calls failed | – | a limit was exceeded |
| 2 | bad input, or the first calls all failed | bad input | bad input |
| 130 | interrupted; resume by running again | – | – |

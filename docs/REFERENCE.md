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
- [Input files: what is read and what is refused](#input-files-what-is-read-and-what-is-refused)
- [Measured limits](#measured-limits)
- [How the comparison rules behave](#how-the-comparison-rules-behave)

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

**When the service limits or refuses calls** (the http adapter, or your own function, see the
[developer guide](DEVELOPER_GUIDE.md#connecting-an-assistant)):

- HTTP 429, 408, 409, 425 and every 5xx are tried again, up to `--retries` times. HTTP 400, 401, 402, 403,
  404 and the other 4xx are not: a used-up quota or a wrong key does not get better in a few seconds.
  The exception is a refusal that carries a `Retry-After` header, whatever its status: the service says
  when to come back, so the call is tried again then. Some services limit free use this way with a 402.
- A `Retry-After` header is obeyed when it asks for up to 120 seconds, and during that wait no other call
  is started either. A longer wait is not made: the call is recorded as failed, to be retried by running
  the same command again later.
- When ten calls in a row fail because the service refused them (401, 402, 403, 429 after its retries) or
  nothing is listening at the address, the run stops, exit status 2. The remaining calls are not made, no
  results file is written from that part, and the same command continues from there later. Calls that fail
  for a reason of their own, such as a 400, a 500 or a timeout, never stop the run.

A failed call is never compared: its case is `incomplete` and is left out of every rate.

This was tried live against one free public model service, with six and then eight calls in flight. Its
limit arrived as HTTP 402 with a `Retry-After` header. In the run made after that was handled, 48 calls
all finished: 43 on the first attempt, four after waits of 3 to 42 seconds that the service asked for, and
one after a timeout. An earlier run of 24 calls, interrupted by the limit, was completed by running the
same command again, which made only the five missing calls. One service on one day is not a survey of
providers.

### `ridi-check report RESULTS.csv`

Writes `summary.json`, `review_cases.csv` and `report.html` next to the results file (or in `--out DIR`).

| Option | Default | Meaning |
|---|---|---|
| `--mode auto\|key\|nokey` | auto | `nokey` ignores the correctness columns and compares the answers |
| `--similarity X` | 1 | without an answer key, count two answers as the same when they share this share of their words (for example 0.9), contain the same numbers and agree on negation |
| `--judgments FILE` | – | your calls on the stable changes: `case_id`, `judgment` (`worse`, `better`, `same_meaning`, `unsure`) |
| `--check-scores` | off | with an answer key: score every answer in the file again against its `expected` answer and say where the score in the file is another one. See [checking the scores](#checking-the-scores-of-a-file-made-by-hand) |
| `--scorer MODULE:FUNCTION` | exact match | with `--check-scores`: the scorer to check against, as in `run` |
| `--current-label TEXT`, `--proposed-label TEXT` | from the manifest | shown in the report |
| `--lang en\|ar` | reader's language | language the report opens in |
| `--open` | off | open the report in your browser |

### `ridi-check gate RESULTS.csv`

Prints the counts and one line per offending case. It prints no verdict about the system.

| Option | Default | Meaning |
|---|---|---|
| `--max-stable-regressions N` | 0 | with an answer key: stable regressions allowed. Without one: stable changes you judged worse |
| `--max-unjudged-changes N` | 0 | without an answer key: stable changes with no judgment, or judged unsure |
| `--strict` | off | every limit at zero unless you give it a value: the three above that are zero already, `--max-unstable`, `--max-unconfirmed`, `--max-case-only` and, with an answer key, `--max-answer-changes`; and `--min-runs 2`. The setting for a release check where a wrong answer is costly. It cannot be combined with `--similarity` below 1, because word overlap can count an answer with an added condition as the same answer |
| `--min-runs N` | not checked | every case must have at least N runs of each version. Without it, a file with one run passes when nothing changed in it, although nothing was re-run |
| `--max-case-only N` | not checked | cases whose answers differ only in letter case, which is not counted as a change |
| `--max-unconfirmed N` | not checked | regressions seen in a single run (without an answer key: changes seen in a single run). With one run nothing is confirmed, so by default these are reported on standard error and not counted |
| `--max-answer-changes N` | not checked | with an answer key: cases whose score stayed the same while the answer changed, between the versions or from one run to the next. `--max-answer-changes 0` belongs in a release check where the wording itself matters |
| `--max-unstable N` | not checked | cases whose answers did not hold on re-run. Give it to make the gate count them; `--max-unstable 0` is the setting for a release check where a wrong answer is costly |
| `--max-incomplete N` | 0 | cases that could not be compared because a call failed |
| `--check-scores`, `--scorer` | off | as for `report`; here every scored run that does not have the score the scorer gives counts against a limit of zero. `--strict` does not turn this on: scores given by a person need not follow a function |
| `--mode`, `--similarity`, `--judgments` | as for `report` | |

### `ridi-check verify DIR`

Builds `results.csv` again from `raw_outputs.jsonl`, the way `run` builds it, and compares it with the
file cell by cell: answers, scores, passages and errors. It prints each cell that differs, for example a
score or an answer edited by hand, and a case that was added or removed. Exit status 0 when the table
agrees with the record, 1 when a cell differs, 2 when the folder does not hold what `run` wrote.

It checks the table against the record, not the record against the assistant: it cannot tell whether a
recorded answer is right. On its own it also cannot tell whether `raw_outputs.jsonl` was changed together
with the table: the two would still agree. For that, `run` prints the SHA-256 of the record when it
finishes, and `verify` prints it again. Keep the line somewhere the folder's owner cannot edit, such as a
CI log or a registered protocol, and give it back with `--raw-sha256 HEX` (its first 16 characters are
enough): `verify` then exits 1 when the record no longer has that fingerprint. When the questions file of
the run is no longer there unchanged, the questions and expected answers are taken from `results.csv`
and are not themselves checked; when the run's own scorer cannot be loaded, the scores are not checked.
Both are said on standard error.

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
| `baseline_context`, `updated_context` | no | passage ids or titles separated by ` \| `, in the order they were retrieved: the first is rank 1 |
| `baseline_context_scores`, `updated_context_scores` | no | the retrieval score of each passage, in the same order and separated the same way; `-` where a passage has none |
| `baseline_context_hashes`, `updated_context_hashes` | no | a short hash of each passage's content, in the same order; `-` where a passage has none |
| `run_errors` | no | written by `run` when a call failed; such a case is `incomplete` |

Missing or duplicate `case_id`, non-binary `_correct` values and files with neither answers nor correctness
are rejected, with the row number as a spreadsheet shows it.

`report` and `gate` never score an answer. With `_correct` columns they use the 0 and 1 values as they are
in the file, whoever put them there, and `expected` is only shown. Scoring against `expected` happens in
`run`, which writes the `_correct` columns. `--mode nokey` leaves the `_correct` columns out on purpose
and compares the answers.

### Checking the scores of a file made by hand

Because the scores of a file made by hand come from somewhere else, two checks say when they do not hang
together. Neither changes a label or a count.

- Always, with an answer key: a case whose runs hold the same answer text scored both 1 and 0 is named in
  the printed summary, in the report, in `summary.json` (`same_text_scored_differently`) and on standard
  error by `gate`. One text cannot be both correct and wrong, so the key or the scorer is not consistent
  there.
- When asked with `--check-scores`: every run that has answer text, in every case that has an `expected`
  answer, is scored again, by exact match after normalisation or by the function given with `--scorer`,
  and compared with the score in the file. `report` prints how many runs disagree and the first ten, and
  writes the result to `summary.json` (`score_check`) and into the report; it still exits 0. `gate` counts
  the runs that disagree against a limit of zero and exits 1 when there are any. Cases without an expected
  answer and runs without answer text are left out and counted as that. When there is nothing to check,
  the exit status is 2.

Agreement shows that the scores in the file are the ones this scorer gives. It does not show that the
answer key is right, and scores given by a person need not agree with any function. For a folder that `run` wrote, `verify`
already scores again with the run's own scorer.

## How cases are labelled

With an answer key two runs are equal when their correctness is equal; without one, when the answers match
after lower-casing, removing punctuation and collapsing spaces (or under `--similarity`).

The signs that carry meaning are not removed: every mathematical symbol (`<`, `>`, `=`, `+`, `±`, `≤`,
`≥`, `≠`, `~` and the like), currency sign and other symbol (`$`, `€`, `✓`, `✗`, `°`), a point or a comma
between two digits, which stays inside its number (`2.5`, `1,000`), a percent sign after a digit, `/` and `*` between two letters or digits
(`mg/kg`), `!` before `=`, and a hyphen that is a sign: before a digit when nothing stands in front of it
(`-5`), or right after a letter or digit when none follows (`HIV-`). So "< 5 mg" and "> 5 mg" are two
answers, and so are "10%" and "10". A hyphen inside a word (`x-ray`, `5-10`) and all other punctuation
still make no difference. The same rule is used when answers are scored against `expected` by exact match.

1. Any run of a version differs from that version's first run: `unstable`.
2. Else the first runs of the two versions are equal: `correct_both` / `wrong_both`, or `same`.
3. Else `stable_regression` / `stable_improvement`, or `stable_change` without a key. With a single run of
   either version the label is `*_unconfirmed`: "stable" needs at least two runs of both versions.

Lower-casing makes "5 mg" and "5 Mg" one answer, and "Yes" and "yes". That stays so. Because the case of a
letter can carry meaning, every case whose answers are equal after lower-casing and not before it is named
in the printed summary, in the report and in `summary.json` (`differ_only_in_letter_case`).

A case whose first-run call failed is `incomplete` and is left out of every rate. A `wrong_both` case whose
wrong answer changed keeps its state and is flagged, because correctness counting alone does not see it.
A `correct_both` case whose answer changed is flagged the same way, without changing any count: the answer
key accepts both answers, and the wording may still matter to you. In the report it has a card of its own,
after the cases whose score changed.

The flag has three values: `stable` (the answer changed between the versions and held on re-run),
`unconfirmed` (it changed and there was one run) and `varied` (a version gave different answers from one
run to the next, though each was scored the same). With an answer key, "unstable" and `--max-unstable`
speak of the score only; `varied` is where the text did not hold. `gate --max-answer-changes N` counts all
three.

With an answer key and answer text in the file, the report also shows the two readings side by side in one
table: each row is what the score did (the state of the case) and each column what the answer text did, by
the rule used without a key (`stable_change`, `change_unconfirmed`, `unstable`, `same`, and
`no_answer_text` for a case that lacks the text of a run). The counts are cases, each row adds up to the
count of its state, and no case changes its state. The table is printed by `report`, drawn in the report
and written to `summary.json` (`score_and_answer_text`); in `review_cases.csv` the column `answer_state`
holds the column of each case. A score that changed with the same answer, and an answer that changed with
the same score, are the cells to read.

When the file lists passages (`baseline_context`, `updated_context`), the report also counts the cases
whose passages differ between the versions, in total and per state (`passages` in `summary.json`). It is a
count of where retrieval changed. It does not say that the passages caused a change in the answer. The
count compares which passages were retrieved; cases where the same passages come in another order or
another number of times are counted apart (`reordered`) and marked on their cards.

A passage is known by its name. Its rank is its place in the cell. When the file also gives scores and
content hashes, the card of a case lists each passage that both versions retrieved and what changed about
it: its rank ("rank 2 → 1"), its score ("score 0.71 → 0.92") and whether its content changed, which is
when both versions give a hash for it and the hashes differ. Cases with such a passage are counted
(`content_changed`). `run` fills these columns when the assistant returns passages as objects with an
`id`, a `score` and a `text`; the text itself is never written, only a twelve-character hash of it with
spacing ignored. None of this is graded: a rank or a score says where a passage stood, not whether it held
the evidence. When
the passages differ in every case, or in none, the report says that in one sentence instead of a count per
state. The built-in demo is such a case: its proposed version splits the handbook differently, so every
passage has a new name.

Under `--similarity`, two answers are never counted as the same when they differ

- in a negation word;
- in the signs that normalisation keeps: the same signs, in the same order;
- in their numbers: the runs of digits in order, so `5mg` and `50mg` differ, and so do "2 tablets of 5 mg"
  and "5 tablets of 2 mg"; and each number with its unit, so `5 mg` and `5 g` differ, and "30 days" and
  "30 weeks";
- by one word put in the place of another, or in the order of the same words: two answers with the same
  number of words are the same only when they are the same text, so "major interaction" is not "minor
  interaction", and "A is allowed and B is not" is not "B is allowed and A is not".

These guards catch a swapped word and a swapped order. They cannot catch an added clause that changes the meaning, such as
"allowed" against "allowed only under supervision". Word overlap does not know which word matters: where
one word decides, as with a dose or a verdict, use exact match (the default), or an answer key with a
scorer written for the subject. Every case that the threshold labels differently from exact match is
named in the printed summary, in the report and in `summary.json` (`labelled_by_similarity`), so that it
can be read.

The rates use first runs: the change between versions, and the re-run variation of each version (run 1
against run 2). Both variations are always shown and neither is subtracted from the change. Each rate
comes with a 95% Wilson interval (`interval_95` in `summary.json`). The interval treats the cases as a
random sample of what users ask, which a hand-picked set of questions is not, and it says nothing about
one case's own re-run variation. No test is applied, and no label or gate decision depends on it. With an answer
key the change equals regressions plus improvements, mean accuracy moves by their difference, and
`2 × min(regressions, improvements)` changes cancel out in the mean.

## Files written

| File | Written by | Holds |
|---|---|---|
| `raw_outputs.jsonl` | `run` | one line per attempt, appended as it completes, never rewritten |
| `run_manifest.json` | `run` | hash of the questions file, both definitions, settings, one entry per invocation |
| `results.csv` | `run` | the table above |
| `summary.json` | `report` | counts per state, case ids, first-run rates |
| `review_cases.csv` | `report` | every case that is not same / correct in both, and every case correct in both whose answer changed, with all its runs; can be read back by `report` |
| `report.html` | `report` | one self-contained page, English and Arabic, light and dark |

Field-by-field descriptions are in the [developer guide](DEVELOPER_GUIDE.md#files).

## Exit status

| Status | `run` | `report` | `gate` |
|---|---|---|---|
| 0 | all calls recorded | written | every count within its limit |
| 1 | finished, some calls failed | – | a limit was exceeded |
| 2 | bad input, the first calls all failed, or the service kept refusing calls | bad input | bad input |
| 130 | interrupted; resume by running again | – | – |

## Input files: what is read and what is refused

The questions file, `results.csv` and the judgments file are read the same way.

- **Encoding.** UTF-8, with or without a byte-order mark, and UTF-16 with a byte-order mark (what Excel
  writes as "Unicode Text"). A file in a local code page, such as Windows-1256 or Latin-1, cannot be told
  apart from damaged text and is refused with the way to fix it: save it as "CSV UTF-8".
- **Shape.** Comma, tab or semicolon separated, chosen from the header line. Any line ending. Blank lines
  are skipped and still counted, so a row number is the one a spreadsheet shows.
- **Cells.** Quotes, commas, line breaks, Arabic and other scripts, emoji and markup inside a quoted cell
  are kept as they are and shown as text in the report; markup in an answer is never run. One cell can hold
  up to 67,108,864 characters.

Each of these is refused with exit status 2 and one line that says what is wrong. Nothing is written.

| File | Message |
|---|---|
| Empty, a header and no rows, or blank lines only | `No rows found in the file.` |
| The same `case_id` twice | `Row 5: case_id 'a' appears more than once (first in row 2).` |
| No `case_id` column | `The file needs a case_id column.` |
| No column for one of the versions | `The file needs baseline_correct and updated_correct (0 or 1), or baseline_answer and updated_answer.` |
| A `_correct` value that is not 0 or 1 | `Row 3 (case 2): baseline_correct must be 0 or 1, got 'true'.` |
| A row cut short, or an empty first run | `Row 3 (case 2): updated_correct is empty. It must be 0 or 1.` |
| An empty `case_id` | `Row 2: case_id is missing.` |
| The same column twice | `Column 'updated_correct' appears more than once.` |
| Not UTF-8 | `The file is not UTF-8 text (first unreadable byte at position 52). Save it as UTF-8 and try again: in Excel, File > Save As > "CSV UTF-8 (Comma delimited)".` |
| Null characters, for example UTF-16 saved without its byte-order mark | `The file holds null characters, so it is not plain UTF-8 text. Save it as UTF-8 and try again: …` |
| A cell above the size limit, or a quotation mark that is never closed in a very large file | `Near line 3: one cell holds more than 67,108,864 characters, the most this tool reads in a cell. …` |
| A folder, or a file that is not there | `The file could not be read: …` |

A file with **one run of each version** is accepted. Every difference is then labelled `*_unconfirmed`,
never stable; the re-run variation is shown as "no second run"; and `gate` exits 0, because it only counts
confirmed regressions, and says on standard error that nothing could be confirmed.

A spreadsheet program reads a cell that starts with `=`, `+`, `-` or `@` as a formula. In `results.csv` and
`review_cases.csv`, and in what the browser version copies, such a cell is written with an apostrophe in
front (`'=1+1`), so that opening the file never runs text that came from an assistant. The apostrophe is
taken off again when a file is read, so the tool reads back exactly what it wrote; `raw_outputs.jsonl`
always holds the answer as it was given. A null character in an answer is dropped when a CSV is written.

## Measured limits

Measured on one machine: a 4-core cloud Linux container (Intel Xeon, 2.1 GHz), Python 3.13 and Chromium,
at the commit that last changed this section. Read the numbers as an order of magnitude, not as a promise.
Nothing was measured above 100,000 cases, and nothing on Windows or macOS.

**`report` and `gate`**, on a synthetic `results.csv` with three runs of each version, answers, correctness
and passages (about 670 bytes a case):

| Cases | File | Command | Time | Peak memory |
|---|---|---|---|---|
| 10,000 | 6.6 MB | `report` | 0.9 s | 61 MB |
| 100,000 | 66.7 MB | `report` | 9 s | 354 MB |
| 100,000 | 66.7 MB | `gate` | 6 s | 235 MB |
| 100,000 | 66.7 MB | `report --mode nokey` | 8.5 s | 348 MB |
| 100,000 | 66.7 MB | `report --mode nokey --similarity 0.9` | 9 s | 346 MB |

The times varied by about a second from one run to the next, and by more from one day to the next on this
shared machine; the memory figures did not vary.

The cases are held in memory: allow five to six times the size of the file for `report` and three to four
times for `gate`. Answers that repeat from run to run, and passage names that repeat from case to case, are kept once,
so a file with little repetition needs more.

**The files `report` writes** at 100,000 cases, of which 14,769 were not "correct in both":
`report.html` 18.5 MB, `review_cases.csv` 20.9 MB, `summary.json` 0.6 MB. At 10,000 cases: 1.9 MB, 2.0 MB
and 0.07 MB.

**Opening `report.html`** in Chromium on the same machine:

| Cases | Cards to review | Opens in | A filter click | Switching language |
|---|---|---|---|---|
| 10,000 | 1,447 | 0.2 s | 0.06 s | 0.15 s |
| 100,000 | 14,769 | 0.7 s | 0.07 s | 0.15 s |

The page draws the cards fifty at a time, with "Show 50 more" and "Show all", and a filter starts again at
the first fifty. Above 2,000 cases the one-cell-per-case strip is drawn as one bar that shows each state's
share, and the list of cases wrong in both versions shows its first 500. "Show all" draws every card at
once and is slow when there are thousands. Printing the page prints the cards that are drawn.

**The browser version** in Chromium on the same machine: a 10,000-case file is read and shown in 0.5 s; the
100,000-case file in 3 s, with about 270 MB of memory in use by the page. The page cuts each cell out of
the text of the file and reads one row at a time; before that it built every cell character by character,
and the same file took 13 s and about 1.4 GB on the same day. A file above two million characters is
checked without being copied into the text box and is not kept across a refresh.

**`run`**: 20,000 questions, two versions, three runs each, calling a Python function that answers at
once, so the time is the tool's own: 120,000 calls recorded and reported in 12 s with a peak of 262 MB.
`raw_outputs.jsonl` was 34.9 MB. Running the same command again, with nothing left to call, took 3 s
and 141 MB. With a real assistant the calls themselves take nearly all of the time.

## How the comparison rules behave

[`benchmarks/transitions`](https://github.com/adeebnoor/ridi-check/tree/main/benchmarks/transitions) holds
1,131 constructed pairs of answers, in English and in Arabic, each labelled by how it was built: the second
answer either says something else, or says the same thing in another surface form. The measured table is
in [RESULTS.md](https://github.com/adeebnoor/ridi-check/blob/main/benchmarks/transitions/RESULTS.md), and a
test fails when it is out of date. In short:

- Exact match, the default, saw 738 of the 782 pairs that say something else. The 44 it missed are all of
  one kind: a letter case that matters, such as `mg` and `Mg`, which lower-casing hides. They are not
  counted as a change, and they are not lost: every case whose answers differ only in letter case is named
  in the report (`differ_only_in_letter_case`), all 44 of these among them, and `gate --strict` stops on them.
- Exact match also called a change 167 of the 349 pairs that a reader would call the same answer: an added
  courtesy, a list in another order, another word for the same thing. These are what the owner judges.
- Word overlap at 0.9 accepted 24 of the 58 added courtesies, and missed 16 of the 69 pairs where a
  condition was added to the answer.

The labels follow from the construction and were not judged by independent raters. The rates say how the
rules behave on each kind of change, not how often such changes happen in use, and they are not a
comparison with any other tool.


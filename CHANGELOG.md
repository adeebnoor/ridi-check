# Changelog

Notable changes to ridi-check. Versions follow [semantic versioning](https://semver.org/); before 1.0 the
library API may change between minor versions.

## 0.10.1

### Changed
- `gate --check-scores` no longer passes what it could not check. A case with no expected answer and a
  scored run with no answer text each count against a limit of zero; before, they were named in a note
  and the gate could still pass. `report --check-scores` is unchanged: it counts them as not checked.

### Added
- `gate --strict` on a file with an answer key and no `run_manifest.json` beside it says on standard error
  that it takes the scores as they are, and names `--check-scores`.
- A run that uses a scorer of your own records the SHA-256 of the file the function lives in
  (`scorer_source_sha256` in `run_manifest.json`), `verify` says when that file has changed since, and a
  score check made with such a scorer records the same fingerprint in `summary.json`.

## 0.10.0

### Added
- With an answer key and answer text in the file, one table counts the cases by what the score did (the
  rows) and by what the answer text did (the columns): printed by `report`, drawn in the report and in the
  browser version, and written to `summary.json` (`score_and_answer_text`). `review_cases.csv` has a new
  column `answer_state`, the label the answer text of a case has without the key. No state and no count
  changes.
- A case whose runs hold the same answer text scored both 1 and 0 is named in the printed summary, in the
  report, in `summary.json` (`same_text_scored_differently`) and on standard error by `gate`.
- `report --check-scores` and `gate --check-scores`, with `--scorer MODULE:FUNCTION`: score every answer of
  a results file again against its `expected` answer and say where the score in the file is another one.
  `report` lists the runs that disagree; `gate` counts them against a limit of zero. For a file made by
  hand, whose scores come from somewhere else. `--strict` does not turn it on.

### Changed
- The report and the browser version have a new look, with the same content and the same numbers: a band
  that names the page and holds its controls, the ledger and the case strip in one board, each rate drawn
  with its 95% interval on one scale, the cells of the score and answer-text table that are worth reading
  set apart, and filters that show how many cases each holds.
- On a case card, the words where the first-run answers of the two versions differ are highlighted. It is a
  word-by-word comparison for the eye; nothing is counted from it.
- In the browser version a file can be dropped on the page as well as chosen.
- The browser version cuts each cell out of the text of the file and reads one row at a time. On the
  100,000-case file it now takes about 3 s and 270 MB where it took 13 s and 1.4 GB on the same machine and
  day. What it reads is unchanged: it was compared with the earlier reader on 400,000 random texts and with
  the Python reader on 60,000.

### Fixed
- In the browser version at phone width, the example selector no longer makes the page wider than the
  screen.
- The measured limits in the reference and on the front page were made again for this version. The memory
  figures printed there for `report` and `gate` (318 MB and 207 MB) were measured before passage scores and
  hashes were added in 0.8.0; they are 354 MB and 235 MB.

## 0.9.1

### Changed
- `gate --strict` refuses `--similarity` below 1, with exit status 2. Before, word overlap could count an
  answer with an added condition ("allowed" and "allowed only under supervision") as the same answer, and
  the strict gate let it pass.

### Added
- `examples/ci/ridi-check-strict.yml`: a workflow with the strict policy pinned: two runs of each version,
  `verify`, and `gate --strict --min-runs 2` with exact match.

## 0.9.0

### Added
- Every case whose answers differ only in letter case, such as "5 mg" and "5 Mg", is named in the printed
  summary, in the report and in `summary.json` (`differ_only_in_letter_case`). It is still not counted as
  a change. `gate --max-case-only N` counts these cases.
- `gate --min-runs N`: every case must have at least N runs of each version.
- `run` prints the SHA-256 of `raw_outputs.jsonl` when it finishes, `verify` prints it again, and
  `verify --raw-sha256 HEX` exits 1 when the record no longer has a fingerprint that was kept elsewhere.
  Without that, a record and a table that were changed together still agree.

### Changed
- `gate --strict` also asks for two runs of each version and counts answers that differ only in letter
  case. A file with one run of each version no longer passes it because nothing changed in that run.

### Fixed
- "in all 1 cases" in the line about passages is "in the one case".

## 0.8.0

### Added
- Retrieved passages can carry a score and a content hash. An assistant may return each passage as an
  object with `id`, `score` and `text` (or `hash`); `run` writes `baseline_context_scores`,
  `updated_context_scores`, `baseline_context_hashes` and `updated_context_hashes` next to the names, and a
  file made by hand can hold the same columns. The text of a passage is never written, only a short hash.
- For each passage that both versions retrieved, a case's card says what changed about it: its rank, its
  score, and whether its content changed. Cases where a passage kept its name while its content changed
  are counted (`passages.content_changed` in `summary.json`).
- The second example in the browser version has made-up scores and content hashes, to show this.

### Changed
- An object with an `id`, a `title` or a `name` in an assistant's `context` is now a passage with that
  name. Before, the whole object was written out as the passage's name.

## 0.7.0

### Changed
- Normalisation keeps the signs that carry meaning, each as a word of its own: every mathematical symbol
  (`<`, `>`, `=`, `+`, `≤`, `≥`, `≠`, `~` ...), currency sign and other symbol (`$`, `✓`, `°`), a percent
  sign after a digit, `/` and `*` between two letters or digits, `!` before `=`, and a hyphen that is a
  sign (`-5`, `HIV-`). A point or a comma between two digits stays inside its number (`2.5`, `1,000`).
  Before, all of them became a space, so "< 5 mg" and "> 5 mg" were the same answer under the default
  exact match. Other punctuation and hyphens inside words still make no difference. This also changes
  exact-match scoring against `expected`, and it is a deliberate difference from the prototype.
- Under `--similarity`, two answers with the same number of words are the same only when they are the
  same text, so the same words in another order are a change; and the signs that normalisation keeps
  must be the same, in the same order.

### Added
- A 95% Wilson interval for each of the three rates, in `summary.json` (`interval_95`), in the printed
  summary and in the report. No test is applied and no label or gate decision depends on it.
- `ridi-check verify DIR`: builds `results.csv` again from `raw_outputs.jsonl` and prints every cell that
  differs, for example a score edited by hand.
- `gate --strict`: every limit at zero unless a value is given for it.
- `gate --max-unconfirmed N`: an optional limit on regressions (without an answer key: changes) seen in a
  single run. By default these are still reported on standard error and not counted.
- With `--max-answer-changes`, cases that hold scores and no answer text count against the limit, because
  a changed answer cannot be seen in them.
- Cases where the same passages come in another order or another number of times are counted
  (`passages.reordered` in `summary.json`) and marked on their cards.
- `benchmarks/transitions`: 1,131 constructed pairs of answers in English and Arabic, labelled by how they
  were built, with the measured behaviour of the comparison rules for each kind of change. A test fails
  when the measured table is out of date, and the browser version is checked against Python on every pair.
- The tests also run on Python 3.14.

## 0.6.0

### Added
- `gate --max-answer-changes N`, for answer-key mode: an optional limit on cases whose score stayed the
  same while the answer changed, between the versions or from one run to the next.
- A case whose score held on re-run while its answer did not is flagged `varied`, shown as a card and
  written to `review_cases.csv`. Before, only an answer that changed between the versions was flagged.
- Under `--similarity`, every case that the threshold labels differently from exact match is named in the
  printed summary, in the report and in `summary.json` (`labelled_by_similarity`).

### Security
- A key that a service repeats in an error message is not kept: the values of credential headers, and of
  environment variables whose names say they are secrets, are removed from `raw_outputs.jsonl`,
  `results.csv` and what is printed. A credential written out in a definition file is left out of
  `run_manifest.json`; it used to be copied there with a warning.

### Fixed
- Under `--similarity`, two long answers that differed only in a unit ("5mg" and "5g", "5 mg" and "5 g") or
  by one word put in the place of another ("major" and "minor", "increase" and "decrease") were counted as
  the same. A number is now compared together with its unit, and two answers with the same number of
  words and not the same words are never the same.
- "1 cases" in the report's and the browser version's source line is "1 case".

### Changed
- Large files need much less memory. A `results.csv` is read one record at a time, repeated answers and
  passage names are kept once, and `run` keeps only the answer and the passages of each recorded call. At
  100,000 cases with three runs: `gate` 207 MB (was 552 MB), `report` 318 MB (was 552 MB); `run` with
  120,000 calls 260 MB (was 469 MB). The results are unchanged.
- The report and the browser version draw the cards fifty at a time, with "Show 50 more" and "Show all".
  Above 2,000 cases the strip is one bar of each state's share, and the list of cases wrong in both
  versions shows its first 500. A report for 100,000 cases opens in 0.6 s (was 7 s).
- Browser version: a file above two million characters is checked without being copied into the text box.
- When the retrieved passages differ in every case that lists them, or in none, the report and the printed
  summary say so in one sentence instead of giving a count per state that is the same for every state. The
  built-in demo is such a case. `summary.json` is unchanged.

## 0.5.1

### Changed
- Browser version: the second example is named "Invented drug names (illustration only)" in the list and
  in its note, in English and in Arabic. The data is unchanged.

### Fixed
- The language button has its own font stack with the Arabic fonts that systems ship, and its label is in
  the page itself, so it is not empty before the script runs.

## 0.5.0

### Added
- When the file lists passages, the report counts the cases whose retrieved passages differ between the
  versions, in total and per state (`passages` in `summary.json`, one line in the printed summary and in
  the report). It is a count, not a cause.
- Browser version: a second synthetic example, about made-up medicines, in which mean accuracy rises by one
  answer while three answers break in every run; and a short explanation of why each version is run more
  than once, with the rule that is applied.
- The user guide and the CI example say when to add `gate --max-unstable 0`.
- README: what happens when a provider limits or refuses calls, including what a live run against a real
  service showed; opening the CSV files in a spreadsheet; and the measured size limits with the platforms
  they were not measured on.

### Fixed
- A refusal that carries a `Retry-After` header is tried again after that wait, whatever its status. A
  live run against a free model service showed its limit arriving as HTTP 402 with `Retry-After`, which
  0.4.0 did not try again.

### Changed
- A case that is correct in both versions and whose answer changed now has a card of its own in the report
  and in the browser version, after the cases whose score changed, instead of a separate list.

## 0.4.0

### Added
- `run` and services that limit or refuse calls: a `Retry-After` header is obeyed (up to 120 seconds) and
  no other call starts during that wait; HTTP 400, 401, 402, 403 and 404 are not tried again; and the run
  stops, exit status 2, when ten calls in a row are refused (a used-up quota, a missing key, a rate limit)
  or nothing is listening, instead of failing every remaining question. Running the same command again
  continues from there. A Python adapter can ask for the same treatment through attributes on the
  exception it raises.
- `examples/adapters/agent_adapter.py`: the pattern for an agent that uses tools and keeps state between
  turns, shown on a stand-in agent. A conversation is one case, and tool calls are returned as `context`.
- User guide: "Stable does not mean correct".
- `CODE_OF_CONDUCT.md`, a short adaptation of the Contributor Covenant 2.1. Reports go through GitHub's
  private reporting; no mailbox is published.

- In answer-key mode, a case that is correct in both versions and whose answer changed is listed: in the
  printed summary, in `summary.json` (`correct_both_answer_changed`), in `review_cases.csv` and in a
  separate list in the report. Its state and every count stay as they were.
- `gate --max-unstable N`: an optional limit on cases whose answers did not hold on re-run.
- Browser version: what you paste is kept until the tab is closed, so a refresh does not lose it; the copy
  buttons confirm on the button; "Clear my judgments"; UTF-16 files are read and other encodings are
  refused in words.
- Files saved by a spreadsheet as UTF-16 ("Unicode Text" in Excel) are read.
- `docs/REFERENCE.md`: what is read and what is refused, with each message, and the limits measured at
  100,000 cases.
- Tests for edge-case inputs, for 20,000 cases with three runs, and for behaviour that had none: an
  unreachable or slow HTTP assistant, a reply that is not JSON, the exit status of `run` when calls fail
  or the run is interrupted, `gate --max-incomplete`, a scorer that raises, and a missing or damaged manifest.
- CI measures statement and branch coverage and fails when it falls below the measured floor.
- CI scans the source with Bandit and the dependencies with pip-audit; `SECURITY.md` lists the two
  findings that are accepted on purpose and why.

### Security
- A cell that a spreadsheet would read as a formula (it starts with `=`, `+`, `-` or `@`) is written with
  an apostrophe in front in `results.csv`, `review_cases.csv` and the browser version's copies, and read
  back without it.

### Fixed
- Under `--similarity`, answers that differ only in a number attached to a unit ("5mg" and "50mg"), or in
  the order of their numbers, were counted as the same. Numbers are now compared as digit runs, in order.
- `report --mode nokey` on a file with correctness columns said that the file had none; it now says that
  they were left out on purpose.
- A file that is not UTF-8 is refused with the way to save it, instead of a decoder message.
- A cell above the size limit ended in a traceback; it is now refused in one line with exit status 2.
- A file with null characters is refused with the same message on every Python version; on 3.10 it used to
  end in a decoder message and on later versions it was read as it was.
- "1 cases" is "1 case".
- The printed summary lists at most twenty of the cases that are wrong in both versions with a changed answer.

### Changed
- Reports without an answer key are about five times faster on large files (33 s to 6.5 s at 100,000
  cases): normalised answers are remembered instead of recomputed. The results are unchanged.
- The README, the guides and the CI example install from PyPI (`pip install ridi-check`) and link to the
  hosted browser version. Installing from the repository remains the way to get the development version.

## 0.3.2

### Added
- A release workflow that publishes to PyPI through Trusted Publishing when a GitHub Release is published.
- `index.html` at the repository root, so that a hosted copy of the browser version has a short address.
- Adapter examples in `examples/adapters`: an OpenAI-compatible HTTP API, the Claude API through its
  official SDK, and a shell command. Each is tested against a local stand-in server.
- `docs/REFERENCE.md`: every command and option, the settings and questions files, `results.csv`, the
  labelling rules and exit status.
- `CONTRIBUTING.md`, `SECURITY.md`, issue forms and a pull request template.

### Changed
- The README is a front page, with a real screenshot of the demo report and the reference moved out.
- The browser version in `web/` uses the reader's own fonts and makes no network request.

### Fixed
- The address of an http system may come from the environment (`${BASE_URL}/path`).

## 0.3.1

First public release.

- `ridi-check run`, `report` and `gate`; `demo` and `init` for a first use.
- Python, command and http adapters; resumable runs that record every attempt.
- One self-contained HTML report in English and Arabic, a JSON summary and the cases to review as CSV.
- A browser version in `web/`, checked against the Python on random files.
- User guide, use cases and developer guide in English and Arabic.
- Tested on Linux, macOS and Windows with Python 3.10 and 3.13.

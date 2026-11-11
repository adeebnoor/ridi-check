# Changelog

Notable changes to ridi-check. Versions follow [semantic versioning](https://semver.org/); before 1.0 the
library API may change between minor versions.

## Unreleased

### Changed
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

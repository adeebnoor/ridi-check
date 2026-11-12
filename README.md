# ridi-check

**See what a model or prompt update really changed in your assistant's answers, before you ship it.**

[![tests](https://github.com/adeebnoor/ridi-check/actions/workflows/tests.yml/badge.svg)](https://github.com/adeebnoor/ridi-check/actions/workflows/tests.yml)
[![licence: MIT](https://raw.githubusercontent.com/adeebnoor/ridi-check/main/docs/img/badge-licence.svg)](https://github.com/adeebnoor/ridi-check/blob/main/LICENSE)
[![Python 3.10+](https://raw.githubusercontent.com/adeebnoor/ridi-check/main/docs/img/badge-python.svg)](https://github.com/adeebnoor/ridi-check/blob/main/pyproject.toml)

A new model or an edited prompt can change what your assistant or agent answers without anyone noticing:
average accuracy barely moves while individual answers flip. ridi-check runs the old and the new version on
the same questions, more than once, and shows which answers changed and which of those changes hold on
re-run. You need no test set, no answer key and no model judge.

**Try it in your browser, with nothing to install:** [adeebnoor.github.io/ridi-check](https://adeebnoor.github.io/ridi-check/).
It opens on two synthetic examples: a library handbook, and one with invented drug names (illustration
only) where mean accuracy rises while three answers break in every run.

![The report: where each case landed, and the change between versions against re-run variation](https://raw.githubusercontent.com/adeebnoor/ridi-check/main/docs/img/report.png)

[What you will see](#what-you-will-see) · [Who it is for](#who-it-is-for) · [Start in one minute](#start-in-one-minute) ·
[Use it in CI](#use-it-in-ci) · [Connect your assistant](#connect-your-assistant) · [FAQ](#faq) ·
[Roadmap](#roadmap) · [Limitations](#limitations) · [Reference](https://github.com/adeebnoor/ridi-check/blob/main/docs/REFERENCE.md)

## What you will see

**In your terminal or CI log**, `ridi-check gate` lists every answer that was right and is now wrong in
every run, and exits 1 so the pipeline stops:

```text
ridi-check gate: ridi-demo/ridi-out/results.csv, 30 cases, answer-key mode
stable_regression  case q02
stable_regression  case q09
stable_regression  case q18
stable_regression  case q25
counts: stable_regression=4 stable_improvement=1 regression_unconfirmed=0 improvement_unconfirmed=0 unstable=4 wrong_both=4 correct_both=17 incomplete=0
stable regressions: 4 (limit 0) - over the limit
gate: a limit was exceeded
```

**In the report**, each changed case shows the question, both answers, what the second run gave and the
passages only one version used:

![One case to review: a stable regression, both answers, and the passages that differ](https://raw.githubusercontent.com/adeebnoor/ridi-check/main/docs/img/report-case.png)

Every question ends in one group:

| Group | Meaning |
|---|---|
| Stable regression | right before, wrong after, in every run: an answer your update broke |
| Stable improvement | wrong before, right after, in every run |
| Stable change | no answer key: a different answer in every run, for you to judge |
| Unstable on re-run | a version disagreed with itself, so the difference is not evidence about the update |
| Wrong in both | no change, still wrong; listed separately |

The report is one self-contained HTML file. It works offline, on a phone, in light and dark, in English and
Arabic. The numbers above come from `ridi-check demo`, which uses synthetic data.

## Who it is for

- **You are about to swap the model, edit the prompt or change retrieval** and want to know which answers
  move, not only whether an average moved.
- **You have questions but no answer key.** The report shows what changed; you judge only the changes that
  held on re-run.
- **You want a CI check** that fails when an answer that was right becomes wrong in every run.
- **You only have answers in a spreadsheet.** The [browser version](https://adeebnoor.github.io/ridi-check/) reads pasted cells and
  needs no install.

It is **not** for proving that answers are correct or that a system is ready to deploy, or for explaining
why an answer changed. Agents that use tools or keep state can be wrapped, but that has not been tried on a
production agent. See
[Limitations](#limitations) and the [use cases](https://github.com/adeebnoor/ridi-check/blob/main/docs/USE_CASES.md).

## Start in one minute

Python 3.10 or later, no dependencies. The demo needs no network and no API key; its data is synthetic.

```bash
pip install ridi-check
```

```bash
ridi-check demo --open
```

Then check your own assistant:

```bash
ridi-check init my-check
```

It writes `questions.csv`, `my_assistant.py` (one function to fill in), `ridi-check.json` and
`ASK_YOUR_AI.md`, a prompt that lets your AI coding assistant do the wiring. In that folder, try five
questions with `ridi-check run --limit 5`, then run everything with `ridi-check run`. The
[user guide](https://github.com/adeebnoor/ridi-check/blob/main/docs/USER_GUIDE.md) walks through each step and how to read the report.

**No install at all:** open the [browser version](https://adeebnoor.github.io/ridi-check/) and paste your results (CSV
text or cells copied from a spreadsheet). Your data stays in the page: it sends nothing anywhere. To use it
offline, download the single file [web/ridi-update-check.html](https://github.com/adeebnoor/ridi-check/blob/main/web/ridi-update-check.html).

**Development version:** `pip install git+https://github.com/adeebnoor/ridi-check` installs the latest commit instead of the
latest release.

## Use it in CI

```yaml
- run: pip install ridi-check
- run: ridi-check run --config ridi-check.json     # calls both versions, writes ridi-out/results.csv
- run: ridi-check gate ridi-out/results.csv        # exits 1 on a stable regression
```

A complete GitHub Actions workflow to copy: [examples/ci/ridi-check.yml](https://github.com/adeebnoor/ridi-check/blob/main/examples/ci/ridi-check.yml).
Where a wrong answer is costly, copy [examples/ci/ridi-check-strict.yml](https://github.com/adeebnoor/ridi-check/blob/main/examples/ci/ridi-check-strict.yml)
instead: two runs of each version, the table checked against the record, and every limit at zero.
`gate` prints counts and the offending cases; it never prints a verdict about your system. By default it
does not count answers that did not hold on re-run, changes seen in a single run, or answers that changed
while their score stayed the same. Where a wrong answer is costly, use `ridi-check gate ... --strict`,
which puts every limit at zero and does not accept `--similarity`.
Limits such as `--max-stable-regressions 2` are in the [reference](https://github.com/adeebnoor/ridi-check/blob/main/docs/REFERENCE.md#ridi-check-gate-resultscsv).

## Connect your assistant

ridi-check has no model provider built in. Your assistant is the system under test, reached through one
function:

```python
def answer(question: str) -> dict:
    return {"answer": "text", "context": ["doc-12", "doc-40"]}   # context is optional
```

| Your assistant is… | Pass it as |
|---|---|
| importable from Python | `python:module:function` |
| a program in any language | `command:<shell command>` (question on stdin, JSON or text on stdout) |
| an HTTP service | `http://…`, or a JSON file that describes the request and the reply |

Ready-made examples in [examples/adapters](https://github.com/adeebnoor/ridi-check/blob/main/examples/adapters/README.md): an OpenAI-compatible HTTP
API (no code), the Claude API through its official SDK, and a shell command with `curl`. Each reads its key
from an environment variable and is tested against a local stand-in server.

The two versions should differ only in what the update changes. Details:
[developer guide](https://github.com/adeebnoor/ridi-check/blob/main/docs/DEVELOPER_GUIDE.md#connecting-an-assistant).

## FAQ

**Do I need a test set or an answer key?** No. Without an `expected` column the report shows which answers
differ and you judge only the stable changes. With one, it speaks of regressions and improvements.

**Does my data go anywhere?** No. ridi-check calls only your assistant and writes local files. The report
and the browser version make no network request.

**Does it use a model to judge answers?** No. A judge adds its own error. Scoring is exact match after
normalisation, or a function you write.

**I scored the answers myself. Does the tool check my scores?** Not unless you ask. `report` and `gate`
use the 0 and 1 in your file as they are. `--check-scores` scores every answer again against its `expected`
answer, by exact match or by your function with `--scorer`, and lists the runs whose score in the file is
another one. A case where the same answer text is scored both correct and wrong is always named. In `gate`,
a score that cannot be checked, for want of an expected answer or of the answer text, counts as well.

**How many questions and runs?** 30 to 100 real user questions is a good first set. Two runs per version is
the minimum for the stable label; use more when the decision is expensive. Calls = questions × 2 × runs.

**Almost everything is "unstable" or "changed". Why?** Your assistant words the same answer differently each
time. Add `expected` answers with a scoring function, or use `--similarity 0.9`. Word overlap does not
know which word matters, so do not use it where one word decides, such as a dose or a verdict.

**Which providers and frameworks does it support?** Any. It talks to a function, a command or an HTTP
endpoint, not to a provider.

**Can I use it on an agent?** Yes, wrapped as one function: a question or a whole scripted conversation goes
in, the final answer comes out, and the tool calls are returned as `context`, so the report shows which
calls only one version made. [examples/adapters](https://github.com/adeebnoor/ridi-check/blob/main/examples/adapters/README.md#an-agent-with-tools-and-memory)
has a working stand-in agent. It has not been tried on a production agent yet.

**What happens when my provider limits or refuses calls?** A `Retry-After` header is obeyed when it asks
for up to 120 seconds, and no other call starts during that wait. HTTP 400, 401, 402, 403 and 404 are not
tried again, unless the refusal itself carries `Retry-After`. After ten refusals in a row (a used-up quota,
a missing key, a rate limit) the run stops with exit status 2, and the same command continues from there
later. A failure that belongs to one question, such as a 400, a 500 or a timeout, is recorded and never
stops the run. This was tried live against one free public model service: its limit arrived as HTTP 402
with `Retry-After`, and 48 calls all finished, five of them on a second attempt after waits of 3 to 42
seconds. That is one service on one day; yours may behave differently.
[Details](https://github.com/adeebnoor/ridi-check/blob/main/docs/REFERENCE.md#ridi-check-run).

**How do I know the comparison rules can be trusted?** Read what they miss.
[benchmarks/transitions](https://github.com/adeebnoor/ridi-check/tree/main/benchmarks/transitions) holds 1,131
constructed pairs of answers in English and Arabic, with the measured result for each kind of change. Exact
match, the default, saw 738 of the 782 pairs that say something else; the 44 it missed differ only in a
letter case that matters, such as `mg` and `Mg`, and the report names every case of that kind. It also called a change 167 of the 349 pairs that a reader
would call the same answer, which is why the owner judges. The pairs are constructed and their labels were
not judged by independent raters, so this shows how the rules behave, not how often such changes happen.

**Can someone edit `results.csv` and pass the gate?** They can edit it; `ridi-check verify ridi-out`
builds the table again from the recorded calls and prints every cell that differs. To show later that the
record itself was not changed, keep the fingerprint that `run` prints and give it to `verify --raw-sha256`.

**Can I open the CSV files in Excel?** Yes. A cell that starts with `=`, `+`, `-` or `@` is written with an
apostrophe in front (`'=1+1`), so a spreadsheet does not run answer text as a formula. The tool takes the
apostrophe off again when it reads the file, and `raw_outputs.jsonl` keeps every answer as it was given.
Going the other way, save your sheet as "CSV UTF-8"; Excel's "Unicode Text" is read too, and other
encodings are refused with a message that says how to save the file.

## Roadmap

No dates and no promises; this is what is planned and what is not.

- **Done:** a release on [PyPI](https://pypi.org/project/ridi-check/), a hosted browser version, adapter
  examples for common APIs, intervals for the rates, a strict gate, a check of the results against the
  recorded calls, ranks, scores and content hashes of retrieved passages, and an open set of constructed
  answer pairs with the measured behaviour of the rules.
- **Next:** fixes and examples that real use asks for. Nothing else is scheduled.
- **Being considered:** multi-turn conversations, tool-using agents, more report languages.
- **Not planned:** model-based judging, or any hosted service that receives your data.

Tell us what you need in an [issue](https://github.com/adeebnoor/ridi-check/issues).

## Limitations

- It finds change, not correctness. A version that is wrong the same way every time looks stable, and
  cases wrong in both versions are listed separately.
- Without an answer key or your judgment, a difference is a change, not a regression.
- Passages are shown as they differ and are not graded; an ungraded passage can still carry the evidence.
- Two runs is a thin estimate of re-run variation. More runs make the stable label firmer.
- It is not a readiness or safety certificate. No output says a system is fit to deploy; the gate prints
  counts and the decision stays yours.
- Agents that use tools or keep state have a documented pattern and a stand-in example, but the tool has
  not been tried on a production agent. Not in this version: model-based judging, statistical tests.
- Size was measured on Linux with Python 3.13 and Chromium only, not on Windows or macOS. There, 100,000
  cases with three runs of each version take about 9 seconds and 354 MB in `report`; the HTML report for
  them is 18.5 MB and opens in under a second, fifty cards at a time; the browser version reads the same
  file in about 3 seconds and uses about 270 MB; and a cell above 64 MB is refused with a message. The
  [measured limits](https://github.com/adeebnoor/ridi-check/blob/main/docs/REFERENCE.md#measured-limits)
  have the full table.

## Documentation

- [User guide](https://github.com/adeebnoor/ridi-check/blob/main/docs/USER_GUIDE.md): step by step, and how to read the report
- [Use cases](https://github.com/adeebnoor/ridi-check/blob/main/docs/USE_CASES.md): thirteen situations and how to set each one up
- [Developer guide](https://github.com/adeebnoor/ridi-check/blob/main/docs/DEVELOPER_GUIDE.md): adapters, files, CI, library use
- [Reference](https://github.com/adeebnoor/ridi-check/blob/main/docs/REFERENCE.md): every command and option, `results.csv`, the labelling rules
- [Transition set](https://github.com/adeebnoor/ridi-check/tree/main/benchmarks/transitions): constructed answer pairs and what the comparison rules see and miss
- بالعربية: [دليل الاستخدام](https://github.com/adeebnoor/ridi-check/blob/main/docs/USER_GUIDE.ar.md) · [حالات الاستخدام](https://github.com/adeebnoor/ridi-check/blob/main/docs/USE_CASES.ar.md) ·
  [دليل المطورين](https://github.com/adeebnoor/ridi-check/blob/main/docs/DEVELOPER_GUIDE.ar.md)

ridi-check follows the RIDI method.

## Contributing

Bug reports, questions and pull requests are welcome: see [CONTRIBUTING.md](https://github.com/adeebnoor/ridi-check/blob/main/CONTRIBUTING.md) and the
[changelog](https://github.com/adeebnoor/ridi-check/blob/main/CHANGELOG.md). Everyone taking part follows the
[code of conduct](https://github.com/adeebnoor/ridi-check/blob/main/CODE_OF_CONDUCT.md). Report a vulnerability privately, as
[SECURITY.md](https://github.com/adeebnoor/ridi-check/blob/main/SECURITY.md) describes.

## Licence

MIT. See [LICENSE](https://github.com/adeebnoor/ridi-check/blob/main/LICENSE).

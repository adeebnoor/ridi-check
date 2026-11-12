# ridi-check user guide

For anyone who owns an AI assistant and is about to change it. You do not need a test set, an answer
key or a statistics background. Arabic version: [USER_GUIDE.ar.md](USER_GUIDE.ar.md).

## What it does

You built an assistant. You are about to change it: a new model, a new prompt, different documents.
ridi-check asks the version you have today and the version you want to ship the same questions,
asks each of them more than once, and shows you:

- which answers **changed**;
- which changes **hold** when each version is asked again, and which are only the assistant
  disagreeing with itself;
- if you have reference answers, which changes are **regressions** and which are **improvements**.

Why bother: an update can leave average accuracy almost the same while many individual answers
flip, because the answers that got worse and the ones that got better cancel out in the average.

## See it in one minute

```bash
pip install ridi-check
```

```bash
ridi-check demo --open
```

This creates a folder `ridi-demo` with a toy assistant in two versions, runs the check and opens the
report. The demo needs no network and no API key. Python 3.10 or later. For the development version,
install from the repository instead: `pip install git+https://github.com/adeebnoor/ridi-check`.

## Three ways to use it

| Your situation | What to do |
|---|---|
| You (or your AI coding assistant) can call the assistant from Python | `ridi-check init`, fill in one function, `ridi-check run` |
| The assistant is a web service or a command-line program | `ridi-check run` with an `http://` address or `command:` (see the developer guide) |
| You only have the answers, for example in a spreadsheet | Open the [browser version](https://adeebnoor.github.io/ridi-check/) and paste the cells; nothing is installed and your data stays in the page. Or: `ridi-check init --by-hand`, fill the table, `ridi-check report` |

## Check your own assistant, step by step

**1. Create a starter folder**

```bash
ridi-check init my-check
```

It writes four files: `questions.csv`, `my_assistant.py`, `ridi-check.json` and `ASK_YOUR_AI.md`.

**2. Write your questions** in `questions.csv`: one row per question, with a short unique `case_id`.
Use questions your users really ask. 30 to 100 is a good first set. If you have a trusted reference
answer for every question, add an `expected` column; if not, leave it out.

**3. Connect your assistant.** Open `my_assistant.py` and make `ask(question, version)` call your
assistant. `version` is `"current"` or `"proposed"`; use it to switch only what the update changes.
If you use an AI coding assistant, paste `ASK_YOUR_AI.md` into it and let it do this step.

**4. Try five questions first**

```bash
ridi-check run --limit 5
```

**5. Run all of them**

```bash
ridi-check run
```

The report is written to `ridi-out/report.html`. Nothing is lost if the run stops: run the same
command again and it continues where it stopped.

How many calls will it make? questions × 2 versions × runs. 50 questions with the default 2 runs is
200 calls to your assistant.

## With or without reference answers

- **With** an `expected` column, each answer is scored correct or wrong (exact match after ignoring
  case and punctuation, or your own scoring function). The report then speaks of regressions and
  improvements.
- **Without** it, the report shows which answers are different. Different is not worse: you read the
  changed answers and say for each one whether it is worse, better or the same meaning.

## Reading the report

**Where each case landed.** Every question ends in one group:

| Group | Meaning | What to do |
|---|---|---|
| Stable regression | Right before, wrong after, in every run | Read these first. Each is a concrete answer your update broke. |
| Stable improvement | Wrong before, right after, in every run | What the update bought you. |
| Stable change (no reference answers) | A different answer in every run | Read both answers and give your call. |
| Unstable on re-run | A version gave different results when asked again | Not evidence about the update. Many of these mean the assistant itself is inconsistent. |
| Wrong in both versions | No change, still wrong | The update did not fix these. Listed separately. |
| Correct in both, answer changed | The answer key accepts both answers, and the text differs | Not counted as a change. Its card comes after the others; read it if the wording matters, for example a number or a condition. |
| Correct in both / Same answer | No change | Nothing to do. |
| Not re-run | You ran each version only once | Nothing can be confirmed. Run twice. |
| Not compared | A call to your assistant failed | Run the same command again to retry. |

**Change between versions against re-run variation.** Three bars: how many answers differ between
the two versions, and how many differ when the *same* version is asked twice. If the first bar is no
longer than the others, the total tells you little: read the stable cases instead.

**Cases to review.** For each changed case: the question, both answers, what the second run gave,
and the passages that only one version used. The passages are shown, not judged.

## Stable does not mean correct

A version that gives the same wrong answer every time looks stable, and without reference answers the
report cannot tell you so. Three ways to cover that:

- Add an `expected` column for the questions where a wrong answer would hurt most. Those cases are then
  scored, and the ones wrong in both versions are listed separately in the report.
- Read a sample of the "same answer" cases yourself once, before you rely on the check.
- Keep whatever correctness evaluation you already have. ridi-check answers a different question: what did
  this update change?

## Giving your call (no reference answers)

In the report, each stable change has four buttons: Worse, Better, Same meaning, Not sure. When you
are done, press **Download judgments.csv**, put the file next to `results.csv`, and run:

```bash
ridi-check report ridi-out/results.csv --judgments ridi-out/judgments.csv
```

## Before you deploy

```bash
ridi-check gate ridi-out/results.csv
```

It prints the counts and one line per offending case, and fails (exit code 1) when there is a stable
regression, or a stable change you have not judged yet. Your deploy script can stop on that. You can
allow some with `--max-stable-regressions N`. The gate prints counts; the decision stays yours.

Answers that did not hold on re-run are not counted by default, because re-run variation is not a
regression. Where a wrong answer is costly, count them too: `ridi-check gate ridi-out/results.csv
--max-unstable 0` also fails when any case is unstable, since such a case is neither confirmed right nor
confirmed wrong.

With an answer key, a score can stay the same while the answer says something else; and with one run of
each version nothing is confirmed, so by default a change seen once is reported and not counted. Where a
wrong answer is costly, the strictest check is:

```bash
ridi-check gate ridi-out/results.csv --strict
```

To check first that nobody changed the table by hand, run `ridi-check verify ridi-out`: it builds
`results.csv` again from the recorded calls and prints every cell that differs.

`--strict` puts every limit at zero: stable regressions, changes you have not judged, cases not compared, unstable
cases, changes seen in a single run and, with an answer key, answers that changed while the score stayed
the same. A limit you give yourself, such as `--max-unstable 2`, stays as you gave it.

## Practical advice

- **Run each version at least twice.** Two runs is the minimum to call anything stable, and it is a
  thin estimate. Use `--runs 3` or more when a decision is expensive.
- **Change one thing at a time.** If the update changes the model and the prompt together, the
  report shows what changed but not which of the two caused it.
- **Changed your assistant's code?** Use a new output folder (`--out ridi-out-2`). Recorded answers
  are never overwritten, so an old folder keeps old answers.
- **Almost everything is "unstable" or "changed"?** Your assistant words the same answer differently
  each time. Either add `expected` answers with a scoring function, or count answers as the same
  when they share most of their words: `ridi-check report ridi-out/results.csv --similarity 0.9`.
  Do not use word overlap where one word decides, such as a dose or a yes-or-no verdict: it can still
  count "allowed" and "allowed only under supervision" as the same. The report names every case it
  labels differently from exact match.
- **Keys and passwords** belong in environment variables, never in the files.

## When something goes wrong

| You see | It means | Do this |
|---|---|---|
| `Stopped: the first calls all failed` | The connection to your assistant does not work yet | Read the error shown, fix `my_assistant.py`, run again |
| `Stopped: 10 calls in a row failed because the service refused them` | A used-up quota, a missing key or a rate limit: the rest would fail the same way | Wait, or fix the key or the plan, then run the same command again; only the missing calls are made |
| `N call(s) failed` | Some calls failed after 3 attempts | Run the same command again; only those are retried |
| `Nothing to call: every call is already recorded` | This folder already holds a finished run | Use a new `--out` folder if the assistant changed |
| `This output directory holds an earlier run with different inputs` | The questions or the versions changed | Use a new `--out` folder |
| `Row 7: case_id ... appears more than once` | A problem in your CSV, with the row | Fix that row |
| `The file is not UTF-8 text` | The spreadsheet saved the file in an older encoding | Save it again as "CSV UTF-8" (in Excel: File > Save As) |

Every message for a file that is refused, and how large a file was tried, is in the
[reference](REFERENCE.md#input-files-what-is-read-and-what-is-refused).

## What this check does not tell you

- It finds change, not correctness. A version that is wrong the same way every time looks stable.
- A changed answer is not always a worse one. With reference answers, the result is only as good as
  those answers.
- Two runs per version is a thin estimate of how much the assistant varies by itself.
- It is not a safety certificate, and it has not been tested on agents that use tools or keep state.

ridi-check follows the RIDI method.

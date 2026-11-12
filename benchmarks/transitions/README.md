# The transition set

`transitions.csv` holds 1,131 constructed pairs of answers, in English and in Arabic. Each pair is one
transition: what a current version said, and what a proposed version said. A pair is labelled `different`
when the second answer says something else, and `same` when it says the same thing in another surface
form.

| File | What it is |
|---|---|
| `generate.py` | builds the pairs from fragments and sentence frames; always writes the same file |
| `transitions.csv` | `pair_id`, `category`, `gold`, `language`, `length`, `answer_a`, `answer_b` |
| `measure.py` | runs the comparison rules on every pair and writes `RESULTS.md` |
| `RESULTS.md` | the measured table, per kind of change, for exact match and for word overlap |

```bash
python benchmarks/transitions/generate.py
python benchmarks/transitions/measure.py
```

## What it is for

It shows, kind of change by kind of change, what the comparison rules see and what they miss: a changed
sign, number, unit or negation; one word in the place of another; an added condition; and, on the other
side, a courtesy, a reordered list or another word for the same thing, which a reader would call the same
answer. A test in this repository fails when the measured table changes without the file being updated,
so a change to the rules shows up here.

## What it is not

- The labels follow from how each pair was built. No independent rater has judged them.
- The pairs are constructed, and the medicine names in them are invented. The rates say how the rules
  behave on each kind of change, not how often such a change happens in real use.
- It is not a comparison with any other tool, and it says nothing about whether an answer is correct.

The set is under the repository's licence. To add a kind of change, add it to `CATEGORIES` in
`generate.py`, run both scripts, and say in the pull request why the label follows from the construction.

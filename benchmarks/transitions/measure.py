"""Measures the comparison rules on transitions.csv and writes RESULTS.md.

For a pair whose gold label is "different", the rule is right when it does not call the two answers the
same. For a pair whose gold label is "same", it is right when it does. Three settings are measured: exact
match after normalisation (the default) and word overlap at 0.9 and at 0.75.

    python benchmarks/transitions/measure.py      # rewrites RESULTS.md
"""

from __future__ import annotations

import csv
import os

from ridi_check import __version__
from ridi_check.analysis import same_answer

HERE = os.path.dirname(os.path.abspath(__file__))
SETTINGS = [("exact match", 1.0), ("overlap 0.9", 0.9), ("overlap 0.75", 0.75)]


def load() -> list[dict]:
    with open(os.path.join(HERE, "transitions.csv"), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def measure(rows: list[dict]) -> dict[tuple[str, str], list]:
    """{(gold, category): [pairs, right at exact, right at 0.9, right at 0.75]} in file order."""
    table: dict[tuple[str, str], list] = {}
    for row in rows:
        cell = table.setdefault((row["gold"], row["category"]), [0, 0, 0, 0])
        cell[0] += 1
        for i, (_, threshold) in enumerate(SETTINGS, start=1):
            same = same_answer(row["answer_a"], row["answer_b"], threshold)
            cell[i] += same == (row["gold"] == "same")
    return table


def render(rows: list[dict]) -> str:
    table = measure(rows)
    out = [
        "# Results on the transition set",
        "",
        f"Measured with ridi-check {__version__} on `transitions.csv`: {len(rows)} constructed pairs, "
        f"{sum(r['language'] == 'en' for r in rows)} in English and {sum(r['language'] == 'ar' for r in rows)} in Arabic. "
        "This file is written by `measure.py`; a test fails when it is out of date.",
        "",
        "Read it for what it is. The pairs are made from fragments put into sentence frames, and each label",
        "follows from the fragment: nobody independent has judged them. The numbers say how the comparison",
        "rules behave on each kind of change. They do not say how often such changes happen in real use, and",
        "they are not a comparison with any other tool.",
        "",
    ]
    for gold, title, right in (("different", "Pairs that say something else", "seen as a change"),
                               ("same", "Pairs that say the same thing in another form", "seen as the same")):
        out += [f"## {title}", "", f"Right means: {right}.", "",
                "| Kind of change | Pairs | " + " | ".join(name for name, _ in SETTINGS) + " |", "|---|---|---|---|---|"]
        total = [0, 0, 0, 0]
        for (g, category), cell in table.items():
            if g != gold:
                continue
            total = [a + b for a, b in zip(total, cell)]
            out.append(f"| {category} | {cell[0]} | " + " | ".join(f"{c}/{cell[0]}" for c in cell[1:]) + " |")
        out += [f"| **all** | {total[0]} | " + " | ".join(f"**{c}/{total[0]}**" for c in total[1:]) + " |", ""]
    out += [
        "## What this shows",
        "",
        "- Exact match sees every change of a sign, a number, a unit, a negation or a word. It does not see a",
        "  change that lower-casing hides: a letter case that matters, as in `mg` and `Mg`.",
        "- Exact match also calls a change what a reader would not: a courtesy added to the answer, a list in",
        "  another order, another word for the same thing. Those are the cases the owner judges.",
        "- Word overlap accepts an added courtesy. It also accepts an added condition (\"allowed\" against",
        "  \"allowed only under supervision\") once the rest of the answer is long enough, which is why it must",
        "  not be used where one word or one clause decides.",
        "",
    ]
    return "\n".join(out)


if __name__ == "__main__":
    text = render(load())
    with open(os.path.join(HERE, "RESULTS.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text)

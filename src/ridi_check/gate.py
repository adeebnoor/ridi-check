"""`ridi-check gate`: counts against limits, for use before a deploy.

The gate prints counts and one line per offending case. It makes no statement about the system:
a count within its limit means only that the count is within its limit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .analysis import (
    INCOMPLETE, REGRESSION_UNCONFIRMED, STABLE_CHANGE, STABLE_REGRESSION, CHANGE_UNCONFIRMED, UNSTABLE, Analysis,
)
from .contract import KEY


@dataclass
class GateResult:
    exceeded: bool
    lines: list[str] = field(default_factory=list)       # stdout
    notes: list[str] = field(default_factory=list)       # stderr


def evaluate(
    a: Analysis, judgments: dict[str, str] | None = None, *, max_stable_regressions: int = 0,
    max_unjudged_changes: int = 0, max_incomplete: int = 0, max_unstable: int | None = None,
    max_answer_changes: int | None = None,
) -> GateResult:
    key = a.mode == KEY
    judgments = judgments or {}
    lines: list[str] = []
    notes: list[str] = []
    checks: list[tuple[str, int, int]] = []

    if key:
        offenders = a.ids(STABLE_REGRESSION)
        lines += [f"stable_regression\tcase {i}" for i in offenders]
        checks.append(("stable regressions", len(offenders), max_stable_regressions))
    else:
        stable = a.ids(STABLE_CHANGE)
        worse = [i for i in stable if judgments.get(i) == "worse"]
        unjudged = [i for i in stable if judgments.get(i) in (None, "unsure")]
        lines += [f"stable_change judged worse\tcase {i}" for i in worse]
        lines += [
            f"stable_change {'judged unsure' if judgments.get(i) == 'unsure' else 'not judged'}\tcase {i}"
            for i in unjudged
        ]
        checks.append(("stable changes judged worse by the owner", len(worse), max_stable_regressions))
        checks.append(("stable changes not yet judged", len(unjudged), max_unjudged_changes))
    if max_answer_changes is not None:
        if key:     # off unless asked for: the answer key scores both answers the same
            words = {"stable": "answer changed", "unconfirmed": "answer changed, not re-run", "varied": "answer varied on re-run"}
            state_of = {case.case_id: state for case, state in a.items}
            lines += [f"{state_of[i]}, {words[flag]}\tcase {i}" for i, flag in a.answer_change.items()]
            checks.append(("answers that changed while the score stayed the same", len(a.answer_change), max_answer_changes))
        else:
            notes.append("note: --max-answer-changes is for answer-key mode. Without a key every changed answer is "
                         "already counted: see --max-unjudged-changes.")
    if max_unstable is not None:      # off unless asked for: re-run variation is not a regression
        unstable = a.ids(UNSTABLE)
        lines += [f"unstable\tcase {i}" for i in unstable]
        checks.append(("unstable cases", len(unstable), max_unstable))
    incomplete = a.ids(INCOMPLETE)
    if incomplete:
        lines += [f"incomplete (a first-run call failed)\tcase {i}" for i in incomplete]
        checks.append(("cases not compared", len(incomplete), max_incomplete))

    lines.append("counts: " + " ".join(f"{state}={count}" for state, count in a.counts.items()))
    exceeded = False
    for name, count, limit in checks:
        over = count > limit
        exceeded = exceeded or over
        lines.append(f"{name}: {count} (limit {limit}){' - over the limit' if over else ''}")
    lines.append("gate: a limit was exceeded" if exceeded else "gate: every count is within its limit")

    if key and a.n_compared >= 3 and not a.correct_b and not a.correct_u:
        notes.append("note: no answer was scored correct in either version, so the scoring probably does not fit "
                     "the answers and no regression can show. Check the expected answers or the scorer.")
    unconfirmed = a.counts.get(REGRESSION_UNCONFIRMED, 0) + a.counts.get(CHANGE_UNCONFIRMED, 0)
    if unconfirmed:
        notes.append(
            f"note: {unconfirmed} change(s) have no second run of both versions. They are unconfirmed and are "
            "not counted against any limit. Run each version at least twice."
        )
    elif a.n_compared and not a.confirmable:
        notes.append(
            "note: this file has no second run of both versions, so no change can be confirmed "
            "and the stable counts are zero by construction."
        )
    return GateResult(exceeded=exceeded, lines=lines, notes=notes)

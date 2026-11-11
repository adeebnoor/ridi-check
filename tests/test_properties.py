"""Invariants that must hold for any results file, checked on seeded random files."""

import random

import pytest

from ridi_check.analysis import analyse
from ridi_check.contract import parse_results, run_column, to_csv
from ridi_check.report import build_summary, review_table

STABLE = {"stable_regression", "stable_improvement", "stable_change"}
UNCONFIRMED = {"regression_unconfirmed", "improvement_unconfirmed", "change_unconfirmed"}


def random_file(rng, key):
    runs_b, runs_u = rng.randint(1, 4), rng.randint(1, 4)
    header = ["case_id"]
    for kind in ("answer", "correct") if key else ("answer",):
        header += [run_column("baseline", k, kind) for k in range(1, runs_b + 1)]
        header += [run_column("updated", k, kind) for k in range(1, runs_u + 1)]
    rows = []
    noise = rng.choice([0, 0.1, 0.4])
    for i in range(rng.randint(1, 80)):
        row = {"case_id": f"c{i}"}
        for side, n in (("baseline", runs_b), ("updated", runs_u)):
            have = n if rng.random() < 0.8 else rng.randint(1, n)
            answer, correct = rng.choice("ABCD"), rng.randint(0, 1)
            for k in range(1, n + 1):
                flip = rng.random() < noise
                row[run_column(side, k, "answer")] = (rng.choice("ABCD") if flip else answer) if k <= have else ""
                if key:
                    row[run_column(side, k, "correct")] = str(correct ^ flip) if k <= have else ""
        rows.append([row[name] for name in header])
    return to_csv(header, rows)


@pytest.mark.parametrize("seed", range(60))
def test_invariants(seed):
    rng = random.Random(seed)
    key = seed % 2 == 0
    text = random_file(rng, key)
    cases, mode = parse_results(text)
    a = analyse(cases, mode)
    summary = build_summary(a)

    assert mode == ("key" if key else "nokey")
    assert sum(a.counts.values()) == a.n == a.n_compared == len(cases)
    assert 0 <= a.rerun_b <= a.any_run_b <= a.rerun_b_n <= a.n
    assert 0 <= a.rerun_u <= a.any_run_u <= a.rerun_u_n <= a.n
    assert a.confirmable <= min(a.rerun_b_n, a.rerun_u_n)

    for case, state in a.items:
        b, u = case.baseline, case.updated
        if state in STABLE:           # "stable" always means at least two runs of both versions
            assert len(b) >= 2 and len(u) >= 2
        if state in UNCONFIRMED:
            assert len(b) == 1 or len(u) == 1
    stable_or_unconfirmed = sum(a.counts.get(s, 0) for s in STABLE | UNCONFIRMED)
    assert stable_or_unconfirmed <= a.changed      # every such case differs on the first run

    if key:
        first = summary["first_run"]
        assert a.changed == a.regressions + a.improvements
        assert a.correct_u - a.correct_b == a.improvements - a.regressions
        assert (first["changes_visible_in_mean_accuracy"] + first["changes_cancelled_in_mean_accuracy"]
                == a.changed)
        # the feasible range of changed answers given the two accuracies
        assert abs(a.correct_u - a.correct_b) <= a.changed <= min(a.correct_b + a.correct_u,
                                                                 2 * a.n - a.correct_b - a.correct_u)

    # reading review_cases.csv back gives the same state for every case in it: the cases that changed,
    # and those correct in both versions whose answer changed all the same
    header, rows = review_table(a)
    if rows:
        again = analyse(*parse_results(to_csv(header, rows), mode))
        assert [(c.case_id, s) for c, s in again.items] == [
            (c.case_id, s) for c, s in a.items if s not in ("correct_both", "same") or c.case_id in a.answer_change]
        assert again.answer_change == a.answer_change

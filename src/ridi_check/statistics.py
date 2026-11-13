"""Execution floor as shipped: a comparison of rounded rates, not an exact test.

The manuscript under review describes an exact test for answer changes beyond a
repeated-run execution floor. This module does not implement that test, and it
does not return a p-value. It records the descriptive comparison already used
by ``report``:

- matched items are the cases compared on both versions;
- repeated runs supply a re-execution rate for each version (run 1 against run 2);
- the execution floor is the larger of those two rates;
- each rate is the value rounded to 6 decimal places;
- the change "exceeds the floor" only when the between-version rate is strictly
  greater than both re-run rates.

Neither re-run rate is subtracted from the change. A missing repeated run makes
the comparison undefined. The release gate does not read this comparison.

The exploratory McNemar p-values quoted in ``docs/research/`` were computed
outside this package. They test a different null (balanced improvements and
regressions) and are not this statistic. See ``docs/STATISTICS.md``.
"""

from __future__ import annotations

EXACT_TEST_IMPLEMENTED = False
RATE_DECIMALS = 6


def rounded_rate(count: int, n: int) -> float | None:
    """``count / n`` rounded to 6 decimal places, or None when ``n`` is 0."""
    if n <= 0:
        return None
    return round(count / n, RATE_DECIMALS)


def change_exceeds_execution_floor(
    change_rate: float,
    current_rerun_rate: float | None,
    proposed_rerun_rate: float | None,
) -> bool | None:
    """True when ``change_rate`` is strictly above both repeated-run rates.

    The rates are already rounded to 6 decimal places. None if either repeated-run
    rate is missing. This is not a p-value and not the manuscript's exact test.
    """
    if current_rerun_rate is None or proposed_rerun_rate is None:
        return None
    return change_rate > max(current_rerun_rate, proposed_rerun_rate)


def execution_floor_record(
    change_rate: float,
    current_rerun_rate: float | None,
    proposed_rerun_rate: float | None,
) -> dict:
    """The execution-floor block written to ``summary.json``."""
    exceeds = change_exceeds_execution_floor(change_rate, current_rerun_rate, proposed_rerun_rate)
    floor = None if exceeds is None else max(current_rerun_rate, proposed_rerun_rate)
    return {
        "name": "execution floor",
        "kind": "descriptive comparison of rates rounded to 6 decimal places",
        "exact_test_implemented": EXACT_TEST_IMPLEMENTED,
        "floor_rate": floor,
        "change_rate": change_rate,
        "change_exceeds_floor": exceeds,
        "current_rerun_rate": current_rerun_rate,
        "proposed_rerun_rate": proposed_rerun_rate,
        "note": (
            "The execution floor is the larger run-1 versus run-2 disagreement rate. "
            "The between-version rate is not reduced by it. No exact test is computed, "
            "and the release gate does not use this comparison."
        ),
    }

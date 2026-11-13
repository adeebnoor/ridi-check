"""Known answers for the shipped execution-floor comparison and the Wilson interval.

These lock the arithmetic that ``report`` already used. They are not the manuscript's
exact test, and they do not turn the exploratory McNemar figures into package output.
"""

import json
from math import comb

import pytest

from ridi_check.analysis import analyse
from ridi_check.contract import parse_results
from ridi_check.report import build_summary, wilson
from ridi_check.statistics import (
    EXACT_TEST_IMPLEMENTED,
    change_exceeds_execution_floor,
    execution_floor_record,
    rounded_rate,
)


def test_rounded_rate_known_values():
    assert rounded_rate(7, 40) == 0.175
    assert rounded_rate(2, 40) == 0.05
    assert rounded_rate(3, 40) == 0.075
    assert rounded_rate(1, 6) == 0.166667
    assert rounded_rate(166666, 1_000_000) == 0.166666
    assert rounded_rate(1, 3) == 0.333333
    assert rounded_rate(333333, 1_000_000) == 0.333333
    assert rounded_rate(0, 10) == 0.0
    assert rounded_rate(1, 0) is None


def test_execution_floor_known_comparisons():
    """Point estimates only. Strictly greater than the larger re-run rate."""
    # 7/40 against 2/40 and 3/40: 0.175 > 0.075.
    assert change_exceeds_execution_floor(0.175, 0.05, 0.075) is True
    # Equal to the larger re-run rate: does not exceed.
    assert change_exceeds_execution_floor(0.2, 0.2, 0.0) is False
    assert change_exceeds_execution_floor(0.2, 0.0, 0.2) is False
    # Below the larger re-run rate.
    assert change_exceeds_execution_floor(0.2, 0.0, 0.4) is False
    # A zero floor and a positive change.
    assert change_exceeds_execution_floor(0.25, 0.0, 0.0) is True
    # No change and no re-execution noise.
    assert change_exceeds_execution_floor(0.0, 0.0, 0.0) is False
    # A missing repeated run leaves the comparison undefined.
    assert change_exceeds_execution_floor(0.5, None, 0.0) is None
    assert change_exceeds_execution_floor(0.5, 0.0, None) is None
    assert change_exceeds_execution_floor(0.5, None, None) is None


def test_rounding_to_six_decimals_is_the_value_that_is_compared():
    """1/6 rounds up to 0.166667 and 166666/1000000 stays 0.166666, so the rounded
    change is above that component. 1/3 and 333333/1000000 round to the same rate,
    so neither exceeds the other."""
    assert change_exceeds_execution_floor(round(1 / 6, 6), round(166666 / 1_000_000, 6), 0.0) is True
    assert change_exceeds_execution_floor(round(1 / 3, 6), round(333333 / 1_000_000, 6), 0.1) is False


def test_floor_record_names_the_larger_rate_and_refuses_an_exact_test():
    record = execution_floor_record(0.175, 0.05, 0.075)
    assert record["name"] == "execution floor"
    assert record["floor_rate"] == 0.075
    assert record["change_exceeds_floor"] is True
    assert record["exact_test_implemented"] is False
    assert EXACT_TEST_IMPLEMENTED is False
    undefined = execution_floor_record(0.5, None, 0.1)
    assert undefined["floor_rate"] is None and undefined["change_exceeds_floor"] is None


def test_wilson_matches_the_formula_at_the_package_z():
    """Hand-checked with z = 1.959964. A z of 1.96 moves the 7/40 bounds past 5e-8,
    so this also locks the constant."""
    assert wilson(7, 40) == pytest.approx((0.08745413698495559, 0.3194999046130458), abs=1e-12)
    assert wilson(4, 24) == pytest.approx((0.06678676282131818, 0.3585307082129004), abs=1e-12)
    assert wilson(0, 24)[0] == 0.0
    assert wilson(0, 24)[1] == pytest.approx(0.1379762066, abs=1e-9)
    assert wilson(24, 24)[1] == pytest.approx(1.0, abs=1e-9)
    assert wilson(1, 1) == pytest.approx((0.2065493118, 1.0), abs=1e-9)
    low, high = wilson(500, 1000)
    assert low == pytest.approx(0.4690696001, abs=1e-9)
    assert high == pytest.approx(0.5309303999, abs=1e-9)
    # z = 1.96, the two-decimal shortcut, moves the 7/40 lower bound by about 1e-6.
    assert abs(wilson(7, 40)[0] - 0.08745302996883066) > 5e-8


def test_summary_floor_matches_the_fixture_and_has_no_p_value(fixture_text):
    summary = build_summary(analyse(*parse_results(fixture_text)))
    floor = summary["execution_floor"]
    assert floor["change_rate"] == 0.175
    assert floor["current_rerun_rate"] == 0.05
    assert floor["proposed_rerun_rate"] == 0.075
    assert floor["floor_rate"] == 0.075
    assert floor["change_exceeds_floor"] is True
    assert floor["exact_test_implemented"] is False
    assert "p_value" not in floor
    assert summary["first_run"]["change_exceeds_both_rerun_variations"] is True
    blob = json.dumps(summary)
    assert "0.7265625" not in blob
    assert summary["exact_conditional_test"]["status"] == (
        "implementation pending confirmation against the registered protocol"
    )


def test_change_inside_the_floor_stays_false_in_the_summary():
    text = (
        "case_id,baseline_correct,baseline_repeat_correct,updated_correct,updated_repeat_correct\n"
        "a,1,1,0,0\n"
        "b,1,1,1,0\n"
        "c,0,0,0,1\n"
        "d,1,1,1,1\n"
        "e,0,0,0,0\n"
    )
    summary = build_summary(analyse(*parse_results(text)))
    floor = summary["execution_floor"]
    # 1/5 = 0.2 against re-run rates 0 and 0.4. The floor is 0.4.
    assert floor["change_rate"] == 0.2
    assert floor["floor_rate"] == 0.4
    assert floor["change_exceeds_floor"] is False
    assert summary["first_run"]["change_exceeds_both_rerun_variations"] is False


def test_one_run_leaves_the_floor_undefined():
    text = "case_id,baseline_correct,updated_correct\na,1,0\nb,0,1\n"
    summary = build_summary(analyse(*parse_results(text)))
    assert summary["execution_floor"]["change_exceeds_floor"] is None
    assert summary["execution_floor"]["floor_rate"] is None
    assert summary["first_run"]["change_exceeds_both_rerun_variations"] is None


def test_three_gains_against_five_losses_is_not_reported_as_mcnemar():
    """Outside this package, the two-sided exact McNemar/binomial p-value for 3 versus 5
    discordant pairs is 186/256 = 0.7265625. The package still reports only the floor."""
    total = 2 ** 8
    threshold = comb(8, 3)
    p = sum(comb(8, k) for k in range(9) if comb(8, k) <= threshold) / total
    assert p == 0.7265625

    rows = ["case_id,baseline_correct,baseline_repeat_correct,updated_correct,updated_repeat_correct"]
    # Five stable regressions and three stable improvements. Every repeat agrees, so the floor is 0.
    for i in range(5):
        rows.append(f"r{i},1,1,0,0")
    for i in range(3):
        rows.append(f"g{i},0,0,1,1")
    summary = build_summary(analyse(*parse_results("\n".join(rows) + "\n")))
    assert summary["first_run"]["regressions"] == 5
    assert summary["first_run"]["improvements"] == 3
    assert summary["execution_floor"]["floor_rate"] == 0.0
    assert summary["execution_floor"]["change_rate"] == 1.0
    assert summary["execution_floor"]["change_exceeds_floor"] is True
    assert "0.7265625" not in json.dumps(summary)
    assert summary["execution_floor"]["exact_test_implemented"] is False
    # Eight between-version changes and no re-run disagreement. The floor test is not 3-versus-5.
    tested = summary["exact_conditional_test"]
    assert tested["n_items"] == 8
    assert tested["change_count"] == 8
    assert tested["exceeds_both"]["p_value_one_sided"]["display"] == "1/256"

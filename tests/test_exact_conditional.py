"""Known answers for the exact conditional test.

The rounded-rate comparison stays in test_statistics.py. These lock the binomial
tails, two small paired tables, and the gains-versus-losses figures from
docs/STATISTICS.md. Those two figures are a different null from the floor test.
"""

from decimal import Decimal
from fractions import Fraction

import pytest

from ridi_check.analysis import analyse
from ridi_check.cli import main
from ridi_check.contract import parse_results
from ridi_check.gate import evaluate
from ridi_check.report import build_summary, text_summary
from ridi_check.statistics import (
    PENDING_CONFIRMATION,
    _away_from_zero,
    binomial_p_at_least,
    binomial_two_sided_as_or_less_likely,
    clopper_pearson,
    exact_conditional_test,
    exact_conditional_test_from_analysis,
    ratio_fraction,
)


def test_one_sided_tails_are_exact_fractions():
    assert binomial_p_at_least(0, 5) == 1
    assert binomial_p_at_least(6, 5) == 0
    assert binomial_p_at_least(3, 3) == Fraction(1, 8)
    assert binomial_p_at_least(2, 2) == Fraction(1, 4)
    # 3 successes out of 4: C(4,3)+C(4,4) = 5, over 16.
    assert binomial_p_at_least(3, 4) == Fraction(5, 16)
    assert binomial_p_at_least(0, 0) == 1
    assert binomial_p_at_least(1, 0) == 0


def test_three_versus_five_and_sixteen_versus_six_are_the_exploratory_null():
    """Hand count of the two-sided 'as or less likely' binomial tail.

    3 versus 5 is 186/256 = 0.7265625. 16 versus 6 is 13757/262144, which is
    0.05248 when rounded half-even to 5 decimal places. Neither is the floor test.
    """
    assert binomial_two_sided_as_or_less_likely(3, 8) == Fraction(186, 256)
    assert binomial_two_sided_as_or_less_likely(5, 8) == Fraction(186, 256)
    assert binomial_two_sided_as_or_less_likely(6, 22) == Fraction(13757, 262144)
    assert binomial_two_sided_as_or_less_likely(16, 22) == Fraction(13757, 262144)
    rendered = (Decimal(13757) / Decimal(262144)).quantize(Decimal("0.00001"))
    assert rendered == Decimal("0.05248")
    assert binomial_two_sided_as_or_less_likely(0, 0) == 1


def test_two_changes_and_no_rerun_disagreement():
    """Four items, two between-version changes, neither version disagrees with itself.

    One-sided p = P(B >= 2) for two trials = 1/4.
    Effect = 2/4 = 1/2.
    For 2/2 the Clopper-Pearson lower bound is sqrt(0.025), and the paired
    difference interval is that bound transformed by (2*pi - 1) * (2/4).
    """
    record = exact_conditional_test([(1, 0, 0), (1, 0, 0), (0, 0, 0), (0, 0, 0)])
    assert record["status"] == PENDING_CONFIRMATION
    assert record["n_items"] == 4
    assert record["change_count"] == 2
    assert record["current_rerun_count"] == record["proposed_rerun_count"] == 0
    both = record["exceeds_both"]
    assert ratio_fraction(both["p_value_one_sided"]) == Fraction(1, 4)
    assert ratio_fraction(both["effect_change_minus_larger_rerun_rate"]) == Fraction(1, 2)
    assert both["larger_rerun"] == "tie"
    # 95% Clopper-Pearson for 2/2 starts at sqrt(0.025). The paired difference scales by 2/4.
    pi_low = Decimal("0.025").sqrt()
    closed_low = (2 * pi_low - 1) * (Decimal(2) / Decimal(4))
    arm = record["versus_current"]["interval_95"]
    reported_low = Decimal(arm["low"])
    assert reported_low <= closed_low
    assert closed_low - reported_low < Decimal("0.000000000002")
    assert arm["high"] == "0.500000000000"
    # The floor interval uses 97.5% on each arm. sqrt(0.0125) is that lower beta quantile.
    joint = Decimal("0.0125").sqrt()
    joint_low = (2 * joint - 1) * (Decimal(2) / Decimal(4))
    floor_low = Decimal(both["interval_95"]["low"])
    assert floor_low <= joint_low
    assert joint_low - floor_low < Decimal("0.000000000002")
    assert both["interval_95"]["high"] == "0.500000000000"
    assert record["versus_current"]["change_only"] == 2
    assert record["versus_current"]["floor_only"] == 0
    assert record["versus_current"]["concordant"] == 2


def test_three_change_only_and_one_floor_only():
    """b = 3, c = 1, N = 8. One-sided p = 5/16. Effect against each version = 1/4."""
    pairs = [(1, 0, 0)] * 3 + [(0, 1, 1)] + [(0, 0, 0)] * 4
    record = exact_conditional_test(pairs, comparison="answers")
    assert record["comparison"] == "answers"
    arm = record["versus_current"]
    assert (arm["change_only"], arm["floor_only"]) == (3, 1)
    assert ratio_fraction(arm["p_value_one_sided"]) == Fraction(5, 16)
    assert ratio_fraction(arm["effect_change_rate_minus_rerun_rate"]) == Fraction(1, 4)
    # The proposed re-run is the same pattern, so the floor effect is the same.
    assert ratio_fraction(record["exceeds_both"]["effect_change_minus_larger_rerun_rate"]) == Fraction(1, 4)
    point = Decimal(1) / Decimal(4)
    assert Decimal(arm["interval_95"]["low"]) <= point <= Decimal(arm["interval_95"]["high"])


def test_concordant_items_do_not_change_the_p_value():
    base = exact_conditional_test([(1, 0, 0), (1, 0, 0)])
    more = exact_conditional_test([(1, 0, 0), (1, 0, 0), (1, 1, 1), (0, 0, 0)])
    assert base["versus_current"]["p_value_one_sided"] == more["versus_current"]["p_value_one_sided"]
    assert ratio_fraction(base["exceeds_both"]["effect_change_minus_larger_rerun_rate"]) == 1
    assert ratio_fraction(more["exceeds_both"]["effect_change_minus_larger_rerun_rate"]) == Fraction(1, 2)


def test_no_discordant_items_leave_the_interval_undefined_and_the_p_value_at_one():
    record = exact_conditional_test([(1, 1, 0), (0, 0, 0)])
    # Current re-run matches the change on the one item that changed, so that arm has no discordant items.
    assert ratio_fraction(record["versus_current"]["p_value_one_sided"]) == 1
    assert record["versus_current"]["interval_95"] is None
    assert record["exceeds_both"]["interval_95"] is None
    assert ratio_fraction(record["exceeds_both"]["p_value_one_sided"]) == 1


def test_empty_input_is_not_a_computed_test():
    record = exact_conditional_test([], excluded_missing_second_run=3)
    assert record["n_items"] == 0
    assert record["excluded_missing_second_run"] == 3
    assert record["exceeds_both"] is None
    assert record["status"] == PENDING_CONFIRMATION


def test_closed_form_clopper_pearson_ends():
    """0 successes and all successes have closed forms. A middle count uses the beta quantile."""
    low, high = clopper_pearson(0, 10)
    assert low == 0
    expected_high = 1 - Decimal("0.025") ** (Decimal(1) / Decimal(10))
    assert abs(high - expected_high) < Decimal("1e-15")
    low, high = clopper_pearson(5, 5)
    assert high == 1
    expected_low = Decimal("0.025") ** (Decimal(1) / Decimal(5))
    assert abs(low - expected_low) < Decimal("1e-15")
    low, high = clopper_pearson(3, 8)
    assert Decimal(0) < low < Decimal(3) / Decimal(8) < high < Decimal(1)


def test_higher_confidence_moves_the_lower_bound_down():
    wider, _ = clopper_pearson(3, 8, confidence="0.975")
    narrower, _ = clopper_pearson(3, 8, confidence="0.95")
    assert wider < narrower


def test_rejected_inputs():
    with pytest.raises(ValueError):
        binomial_p_at_least(-1, 4)
    with pytest.raises(ValueError):
        binomial_two_sided_as_or_less_likely(3, 2)
    with pytest.raises(ValueError):
        clopper_pearson(1, 0)
    with pytest.raises(ValueError):
        clopper_pearson(1, 2, confidence="0")
    with pytest.raises(ValueError):
        clopper_pearson(2, 1)
    with pytest.raises(ValueError):
        exact_conditional_test([(1, 0, 0)], comparison="scores")
    with pytest.raises(ValueError):
        exact_conditional_test([(1, 0)])
    with pytest.raises(ValueError):
        exact_conditional_test([(1, 0, 2)])
    with pytest.raises(ValueError):
        exact_conditional_test([(True, 0, 0)])
    with pytest.raises(ValueError):
        exact_conditional_test([], excluded_missing_second_run=-1)
    assert _away_from_zero(Decimal(0)) == Decimal("1e-30")
    assert _away_from_zero(Decimal("0.2")) == Decimal("0.2")


def _rows(body: str) -> str:
    header = "case_id,baseline_correct,baseline_repeat_correct,updated_correct,updated_repeat_correct\n"
    return header + body


def test_analysis_uses_run_1_against_run_2_and_the_same_equality():
    text = _rows("a,1,1,0,0\nb,1,0,1,1\nc,0,0,0,1\n")
    summary = build_summary(analyse(*parse_results(text)))
    tested = summary["exact_conditional_test"]
    assert tested["comparison"] == "correctness"
    assert tested["n_items"] == 3
    # a changes and neither re-run disagrees. b does not change; the current re-run does.
    # c does not change; the proposed re-run does.
    assert tested["versus_current"]["change_only"] == 1
    assert tested["versus_current"]["floor_only"] == 1
    assert tested["versus_proposed"]["change_only"] == 1
    assert tested["versus_proposed"]["floor_only"] == 1
    # One change-only and one re-run-only: P(B >= 1) for two trials is 3/4.
    assert ratio_fraction(tested["versus_current"]["p_value_one_sided"]) == Fraction(3, 4)
    printed = text_summary(summary)
    assert PENDING_CONFIRMATION in printed
    assert "3/4" in printed
    # The rounded comparison is untouched: 1/3 against 1/3 and 1/3.
    assert summary["execution_floor"]["change_exceeds_floor"] is False
    assert summary["execution_floor"]["exact_test_implemented"] is False


def test_one_run_file_is_excluded_from_the_exact_test():
    text = "case_id,baseline_correct,updated_correct\na,1,0\n"
    summary = build_summary(analyse(*parse_results(text)))
    tested = summary["exact_conditional_test"]
    assert tested["n_items"] == 0
    assert tested["excluded_missing_second_run"] == 1
    assert "not computed" in text_summary(summary)


def test_gate_ignores_the_exact_test_unless_asked(tmp_path, capsys):
    path = tmp_path / "results.csv"
    path.write_text(_rows("a,1,1,0,0\nb,1,1,0,0\n"), encoding="utf-8")
    # Two stable regressions. A limit of 2 passes. p = 1/4, which is above 0.05 and equal to 0.25.
    assert main(["gate", str(path), "--max-stable-regressions", "2"]) == 0
    out = capsys.readouterr().out
    assert "exact conditional test" not in out
    assert main(["gate", str(path), "--max-stable-regressions", "2", "--exact-test"]) == 1
    failed = capsys.readouterr().out
    assert "p=1/4" in failed and "alpha=0.05" in failed and "over the limit" in failed
    assert main(["gate", str(path), "--max-stable-regressions", "2", "--exact-test", "--exact-test-alpha", "0.25"]) == 0
    assert main(["gate", str(path), "--max-stable-regressions", "2", "--exact-test", "--exact-test-alpha", "1/4"]) == 0
    assert main(["gate", str(path), "--exact-test-alpha", "0.05"]) == 2
    assert "--exact-test-alpha is used together with --exact-test" in capsys.readouterr().err
    for bad in ("0", "1", "no"):
        with pytest.raises(SystemExit) as stopped:
            main(["gate", str(path), "--exact-test", "--exact-test-alpha", bad])
        assert stopped.value.code == 2


def test_gate_fails_when_the_exact_test_cannot_be_computed(tmp_path, capsys):
    path = tmp_path / "results.csv"
    path.write_text("case_id,baseline_correct,updated_correct\na,1,1\n", encoding="utf-8")
    assert main(["gate", str(path), "--max-stable-regressions", "0", "--exact-test"]) == 1
    assert "not computed" in capsys.readouterr().out


def test_strict_does_not_turn_the_exact_test_on():
    text = _rows("a,1,1,0,0\nb,0,0,0,0\n")
    analysis = analyse(*parse_results(text))
    # One stable regression. Strict would fail that limit. With the limit raised, strict's other
    # limits are not this call; the exact test stays off when the flag is absent.
    plain = evaluate(analysis, max_stable_regressions=1)
    asked = evaluate(analysis, max_stable_regressions=1, exact_test=True)
    assert plain.exceeded is False
    assert asked.exceeded is True
    assert exact_conditional_test_from_analysis(analysis)["comparison"] == "correctness"

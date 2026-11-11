"""The fixture numbers, in both modes, and the classification rules."""

import pytest

from ridi_check.analysis import analyse, classify, normalise, same_answer
from ridi_check.contract import parse_results
from ridi_check.report import build_summary


def test_fixture_answer_key_mode(fixture_text):
    cases, mode = parse_results(fixture_text)
    assert mode == "key" and len(cases) == 40
    a = analyse(cases, mode)
    assert a.ids("stable_regression") == ["s05", "s17", "s29"]
    assert a.ids("stable_improvement") == ["s11", "s33"]
    assert a.ids("unstable") == ["s03", "s14", "s22", "s31", "s38"]
    assert a.counts["wrong_both"] == 6
    assert a.counts["correct_both"] == 24
    assert a.counts["regression_unconfirmed"] == a.counts["improvement_unconfirmed"] == a.counts["incomplete"] == 0
    assert sum(a.counts.values()) == 40
    # first run
    assert (a.correct_b, a.correct_u, a.n_compared) == (30, 29, 40)
    assert (a.regressions, a.improvements) == (4, 3)
    assert a.changed == 7
    assert (a.rerun_b, a.rerun_b_n) == (2, 40)
    assert (a.rerun_u, a.rerun_u_n) == (3, 40)


def test_fixture_no_key_mode(nokey_text):
    cases, mode = parse_results(nokey_text)
    assert mode == "nokey"
    a = analyse(cases, mode)
    assert a.ids("stable_change") == ["s05", "s11", "s17", "s24", "s29", "s33", "s40"]
    assert a.ids("unstable") == ["s03", "s14", "s22", "s31", "s38"]
    assert a.counts["same"] == 28
    assert a.counts["change_unconfirmed"] == a.counts["incomplete"] == 0
    assert a.changed == 9
    assert (a.rerun_b, a.rerun_b_n, a.rerun_u, a.rerun_u_n) == (2, 40, 3, 40)


def test_forcing_no_key_mode_on_the_full_fixture_gives_the_same_numbers(fixture_text, nokey_text):
    forced = analyse(*parse_results(fixture_text, "nokey"))
    dropped = analyse(*parse_results(nokey_text))
    assert forced.counts == dropped.counts and forced.changed == dropped.changed == 9


def test_a_changed_wrong_answer_stays_wrong_in_both_but_is_recorded(fixture_text):
    """Correctness counting does not see s24 and s40. Their state stays wrong_both; the change is flagged."""
    a = analyse(*parse_results(fixture_text))
    assert {"s24", "s40"} <= set(a.ids("wrong_both"))
    assert a.answer_change == {"s24": "stable", "s40": "stable"}
    summary = build_summary(a)
    assert summary["wrong_both_answer_changed"] == {"stable": ["s24", "s40"], "unconfirmed": []}
    assert summary["states"]["wrong_both"] == 6


def test_summary_rates(fixture_text):
    summary = build_summary(analyse(*parse_results(fixture_text)))
    first = summary["first_run"]
    assert first["change_between_versions"] == {"count": 7, "n": 40, "rate": 0.175}
    assert first["rerun_variation_current"] == {"count": 2, "n": 40, "rate": 0.05}
    assert first["rerun_variation_proposed"] == {"count": 3, "n": 40, "rate": 0.075}
    assert first["change_exceeds_both_rerun_variations"] is True
    assert first["accuracy_current"]["count"] == 30 and first["accuracy_proposed"]["count"] == 29
    assert not any("not larger" in note for note in summary["notes"])
    assert any("thin estimate" in note for note in summary["notes"])


def test_change_within_rerun_variation_is_said_so():
    """When the change between versions is no larger than a version's own variation, the summary says so."""
    text = ("case_id,baseline_correct,baseline_repeat_correct,updated_correct,updated_repeat_correct\n"
            "a,1,1,0,0\n"      # the only change between versions
            "b,1,1,1,0\nc,0,0,0,1\n"   # the proposed version disagrees with itself twice
            "d,1,1,1,1\ne,0,0,0,0\n")
    summary = build_summary(analyse(*parse_results(text)))
    first = summary["first_run"]
    assert first["change_between_versions"]["count"] == 1 and first["rerun_variation_proposed"]["count"] == 2
    assert first["change_exceeds_both_rerun_variations"] is False
    assert any("not larger" in note and "stable cases" in note for note in summary["notes"])


def test_single_run_gives_unconfirmed_labels_never_stable():
    key = "case_id,baseline_correct,updated_correct\na,1,0\nb,0,1\nc,1,1\nd,0,0\n"
    a = analyse(*parse_results(key))
    assert a.counts["regression_unconfirmed"] == 1 and a.counts["improvement_unconfirmed"] == 1
    assert a.counts["stable_regression"] == a.counts["stable_improvement"] == 0
    assert a.counts["correct_both"] == 1 and a.counts["wrong_both"] == 1
    summary = build_summary(a)
    assert summary["first_run"]["rerun_variation_current"] is None
    assert summary["first_run"]["change_exceeds_both_rerun_variations"] is None

    nokey = "case_id,baseline_answer,updated_answer\na,yes,no\nb,yes,yes\n"
    b = analyse(*parse_results(nokey))
    assert b.counts["change_unconfirmed"] == 1 and b.counts["stable_change"] == 0 and b.counts["same"] == 1


def test_stable_needs_two_runs_of_both_versions():
    text = ("case_id,baseline_answer,baseline_repeat_answer,updated_answer,updated_repeat_answer\n"
            "a,yes,yes,no,\n"       # proposed ran once
            "b,yes,yes,no,no\n"
            "c,yes,no,no,\n")       # current disagrees with itself
    cases, mode = parse_results(text)
    assert [classify(c, mode) for c in cases] == ["change_unconfirmed", "stable_change", "unstable"]


def test_a_later_run_makes_a_case_unstable_but_the_rate_uses_runs_one_and_two():
    text = ("case_id,baseline_answer,baseline_repeat_answer,baseline_repeat2_answer,"
            "updated_answer,updated_repeat_answer,updated_repeat2_answer\n"
            "a,yes,yes,no,yes,yes,yes\n"
            "b,yes,yes,yes,no,no,no\n")
    a = analyse(*parse_results(text))
    assert a.ids("unstable") == ["a"] and a.ids("stable_change") == ["b"]
    assert (a.rerun_b, a.rerun_b_n) == (0, 2)      # run 1 against run 2, by definition
    assert (a.any_run_b, a.any_run_u) == (1, 0)    # reported next to it, so the two do not contradict
    assert (a.max_runs_b, a.max_runs_u) == (3, 3)


def test_normalise_matches_the_prototype():
    assert normalise("  Hello,   WORLD!! ") == "hello world"
    assert normalise("don't") == "don t"
    assert normalise("NOT_ENOUGH_INFO") == "not enough info"
    assert normalise("نعم، صحيح.") == "نعم صحيح"
    assert same_answer("Paris.", "paris")
    assert not same_answer("Paris", "Lyon")


def test_word_overlap_threshold():
    a, b = "the loan period is three weeks for all books", "the loan period is three weeks for most books"
    assert not same_answer(a, b)            # exact by default
    assert same_answer(a, b, 0.75)          # 8 shared of 10 distinct words
    assert not same_answer(a, b, 0.9)


@pytest.mark.parametrize("a, b", [
    ("the treatment is effective for most adult patients in the trial",
     "the treatment is not effective for most adult patients in the trial"),
    ("return the book within 30 days of the loan date at any branch",
     "return the book within 45 days of the loan date at any branch"),
    ("العلاج فعّال لدى معظم المرضى البالغين في التجربة", "العلاج غير فعّال لدى معظم المرضى البالغين في التجربة"),
])
def test_a_threshold_never_merges_answers_that_differ_in_negation_or_numbers(a, b):
    assert not same_answer(a, b, 0.75)

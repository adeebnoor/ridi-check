"""`report` and `gate`: files written, numbers, wording rules, exit status."""

import csv
import json
import os
import re

import pytest

from ridi_check.cli import main
from ridi_check.contract import ContractError, read_results
from ridi_check.analysis import analyse
from ridi_check.report import read_judgments, write_report

from conftest import FIXTURE

FORBIDDEN = re.compile(r"\b(safe|safely|pass|passed|passes|certified|certif\w*|approved|approval)\b", re.I)


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def page_data(path):
    with open(path, encoding="utf-8") as f:
        html = f.read()
    blob = re.search(r'<script id="ridi-data" type="application/json">(.*?)</script>', html, re.S).group(1)
    return html, json.loads(blob)


def test_report_files_in_answer_key_mode(tmp_path):
    summary, paths, _, warnings = write_report(FIXTURE, str(tmp_path))
    assert warnings == []
    with open(tmp_path / "summary.json", encoding="utf-8") as f:
        on_disk = json.load(f)
    assert on_disk == summary
    assert on_disk["mode"] == "key" and on_disk["cases"] == 40
    assert on_disk["states"] == {
        "stable_regression": 3, "stable_improvement": 2, "regression_unconfirmed": 0, "improvement_unconfirmed": 0,
        "unstable": 5, "wrong_both": 6, "correct_both": 24, "incomplete": 0}
    assert on_disk["case_ids"]["stable_regression"] == ["s05", "s17", "s29"]
    assert on_disk["first_run"]["regressions"] == 4 and on_disk["first_run"]["improvements"] == 3

    review = read_csv(tmp_path / "review_cases.csv")
    assert len(review) == 16 and "correct_both" not in {r["state"] for r in review}
    assert [r["case_id"] for r in review if r["state"] == "wrong_both" and r["answer_change"] == "stable"] == ["s24", "s40"]


def test_report_files_without_an_answer_key(tmp_path, write, nokey_text):
    results = write("results.csv", nokey_text)
    summary, _, _, _ = write_report(results, str(tmp_path / "out"))
    assert summary["mode"] == "nokey"
    assert summary["states"] == {"stable_change": 7, "change_unconfirmed": 0, "unstable": 5, "same": 28, "incomplete": 0}
    assert summary["first_run"]["change_between_versions"]["count"] == 9
    assert summary["judgments"]["still_to_decide"] == 7
    review = read_csv(tmp_path / "out" / "review_cases.csv")
    assert [r["case_id"] for r in review] == ["s03", "s05", "s11", "s14", "s17", "s22", "s24", "s29", "s31", "s33", "s38", "s40"]


def test_review_cases_can_be_read_back_with_every_run(tmp_path):
    write_report(FIXTURE, str(tmp_path))
    cases, mode = read_results(str(tmp_path / "review_cases.csv"))
    assert mode == "key" and all(len(c.baseline) == 2 and len(c.updated) == 2 for c in cases)
    again = analyse(cases, mode)
    assert again.ids("stable_regression") == ["s05", "s17", "s29"]
    assert again.ids("unstable") == ["s03", "s14", "s22", "s31", "s38"]
    assert again.counts["wrong_both"] == 6 and again.counts["correct_both"] == 0


def test_report_html_is_self_contained_and_bilingual(tmp_path):
    write_report(FIXTURE, str(tmp_path), current_label="v1 <b>", proposed_label="v2")
    html, data = page_data(tmp_path / "report.html")
    assert html.startswith("<!doctype html>") and 'name="viewport"' in html
    assert not re.search(r"https?://", html)                       # nothing is fetched: it opens offline
    assert not re.search(r"<link|<img|<iframe|src=", html)
    assert "prefers-color-scheme: dark" in html and 'dir = state.lang === "ar" ? "rtl" : "ltr"' in html
    assert set(data["strings"]) == {"en", "ar"}
    assert set(data["strings"]["en"]) == set(data["strings"]["ar"])
    assert data["strings"]["ar"]["limits"] == "ما لا يخبرك به هذا الفحص"
    assert data["meta"]["labels"] == {"current": "v1 <b>", "proposed": "v2"} and "v1 <b>" not in html
    assert len(data["strip"]) == 40
    assert [c["id"] for c in data["cards"]] == ["s03", "s05", "s11", "s14", "s17", "s22", "s24", "s29", "s31", "s33", "s38", "s40"]
    assert [w[0] for w in data["wrong"]] == ["s08", "s19", "s24", "s27", "s35", "s40"]
    card = {c["id"]: c for c in data["cards"]}
    assert card["s24"]["state"] == "wrong_both" and card["s24"]["flag"] == "stable"
    assert [r["same"] for r in card["s03"]["u"]] == [True, False]


def test_report_html_shows_only_the_passages_that_differ(tmp_path, write):
    results = write("results.csv",
                    "case_id,baseline_answer,baseline_repeat_answer,updated_answer,updated_repeat_answer,"
                    "baseline_context,updated_context\n"
                    'x,yes,yes,no,no,p1 | p2 | p3,p2 | p9\n'
                    'y,</script><script>alert(1)</script>,a,b,b,,\n')
    write_report(results, str(tmp_path / "out"))
    html, data = page_data(tmp_path / "out" / "report.html")
    x = data["cards"][0]
    assert (x["rem"], x["add"], x["kept"]) == (["p1", "p3"], ["p9"], 1)
    assert "alert(1)" in data["cards"][1]["b"][0]["ans"]
    assert html.count("</script>") == 2 and "<script>alert" not in html     # answers cannot break out of the data block
    review = read_csv(tmp_path / "out" / "review_cases.csv")
    assert review[0]["passages_only_current"] == "p1 | p3" and review[0]["passages_only_proposed"] == "p9"


def test_wording_rules(tmp_path, write, nokey_text, capsys):
    # no answer key: a difference is a change, never a regression
    results = write("results.csv", nokey_text)
    assert main(["report", results, "--out", str(tmp_path / "nokey")]) == 0
    assert main(["gate", results]) == 1
    html, _ = page_data(tmp_path / "nokey" / "report.html")
    printed = capsys.readouterr()
    for text in (html, printed.out, printed.err, (tmp_path / "nokey" / "summary.json").read_text(encoding="utf-8")):
        assert "regress" not in text.lower() and "تراجع" not in text

    # in any mode: no verdict about the system, and passages are ungraded, not judged
    assert main(["report", FIXTURE, "--out", str(tmp_path / "key")]) == 0
    assert main(["gate", FIXTURE]) == 1
    assert main(["gate", FIXTURE, "--max-stable-regressions", "5"]) == 0
    printed = capsys.readouterr()
    _, key_data = page_data(tmp_path / "key" / "report.html")
    _, nokey_data = page_data(tmp_path / "nokey" / "report.html")
    for text in (printed.out, printed.err):
        assert not FORBIDDEN.search(text), FORBIDDEN.search(text).group(0)
    for data in (key_data, nokey_data):
        # everything the page can show: its string table and the notes in the summary
        text = json.dumps([data["strings"]["en"], data["summary"]["notes"]], ensure_ascii=False)
        visible = text.replace("not a safety certificate", "")       # the limits text says what it is not
        assert not FORBIDDEN.search(visible), FORBIDDEN.search(visible).group(0)
        assert not re.search(r"irrelevant|distractor", text, re.I)
        assert "ungraded" in text and "thin estimate" in text
        assert "ليس شهادة سلامة" in json.dumps(data["strings"]["ar"], ensure_ascii=False)


def test_judgments_are_counted_and_validated(tmp_path, write, nokey_text):
    results = write("results.csv", nokey_text)
    judgments = write("judgments.csv", "case_id,judgment\ns05,worse\ns17,same_meaning\ns03,better\ns24,\n")
    summary, _, _, warnings = write_report(results, str(tmp_path / "out"), judgments_path=judgments)
    assert summary["judgments"]["of_stable_changes"] == {
        "worse": 1, "better": 0, "same_meaning": 1, "unsure": 0, "unjudged": 5}
    assert summary["judgments"]["ignored_not_a_stable_change"] == ["s03"] and "s03" in warnings[0]
    review = {r["case_id"]: r["judgment"] for r in read_csv(tmp_path / "out" / "review_cases.csv")}
    assert review["s05"] == "worse" and review["s24"] == ""
    _, data = page_data(tmp_path / "out" / "report.html")
    assert data["judgments"] == {"s05": "worse", "s17": "same_meaning"}

    ids = {"s05", "s17", "s24"}
    for text, fragment in [
        ("case_id,judgment\ns05,terrible\n", "row 2 (case s05)"),
        ("case_id,judgment\ns05,worse\ns05,better\n", "row 3"),
        ("case_id,judgment\n999,worse\n", "'999' is not in the results file"),
        ("case,judgment\ns05,worse\n", "case_id and judgment columns"),
    ]:
        with pytest.raises(ContractError) as info:
            read_judgments(write("bad.csv", text), ids)
        assert fragment in str(info.value)


def test_gate_answer_key_mode(capsys):
    assert main(["gate", FIXTURE]) == 1
    out = capsys.readouterr().out.splitlines()
    assert "stable_regression\tcase s05" in out and "stable_regression\tcase s29" in out
    assert "stable regressions: 3 (limit 0) - over the limit" in out
    assert main(["gate", FIXTURE, "--max-stable-regressions", "3"]) == 0
    assert "stable regressions: 3 (limit 3)" in capsys.readouterr().out.splitlines()


def test_gate_without_an_answer_key(write, nokey_text, capsys):
    results = write("results.csv", nokey_text)
    assert main(["gate", results]) == 1
    out = capsys.readouterr().out
    assert out.count("stable_change not judged\tcase") == 7 and "stable changes not yet judged: 7 (limit 0)" in out
    assert main(["gate", results, "--max-unjudged-changes", "7"]) == 0

    judged = write("judgments.csv", "case_id,judgment\ns05,worse\ns11,better\ns17,better\ns29,same_meaning\n"
                   "s33,better\ns40,better\ns24,unsure\n")
    assert main(["gate", results, "--judgments", judged, "--max-unjudged-changes", "1"]) == 1
    out = capsys.readouterr().out
    assert "stable_change judged worse\tcase s05" in out and "stable_change judged unsure\tcase s24" in out
    assert "stable changes judged worse by the owner: 1 (limit 0) - over the limit" in out
    assert main(["gate", results, "--judgments", judged, "--max-unjudged-changes", "1",
                 "--max-stable-regressions", "1"]) == 0


def test_gate_says_when_nothing_can_be_confirmed(write, capsys):
    results = write("results.csv", "case_id,baseline_correct,updated_correct\na,1,0\nb,1,1\n")
    assert main(["gate", results]) == 0
    printed = capsys.readouterr()
    assert "regression_unconfirmed=1" in printed.out and "unconfirmed" in printed.err


def test_scoring_that_fits_nothing_is_pointed_out(write, capsys):
    results = write("results.csv", "case_id,baseline_answer,updated_answer,baseline_correct,updated_correct\n"
                    + "".join(f"c{i},a long answer,another answer,0,0\n" for i in range(4)))
    assert main(["report", results]) == 0
    assert "No answer was scored correct in either version" in capsys.readouterr().out
    assert main(["gate", results]) == 0
    assert "no regression can show" in capsys.readouterr().err


def test_bad_input_exits_with_status_2_and_names_the_row(write, capsys):
    results = write("results.csv", "case_id,baseline_correct,updated_correct\na,1,0\na,1,1\n")
    assert main(["report", results]) == 2
    assert main(["gate", results]) == 2
    assert "Row 3" in capsys.readouterr().err
    assert not os.path.exists(os.path.join(os.path.dirname(results), "report.html"))


def test_a_long_list_of_cases_is_cut_short_in_the_printed_summary(write, capsys):
    rows = "".join(f"c{i},wrong answer,another wrong answer,wrong answer,another wrong answer,0,0,0,0\n" for i in range(30))
    results = write("results.csv", "case_id,baseline_answer,updated_answer,baseline_repeat_answer,updated_repeat_answer,"
                    "baseline_correct,updated_correct,baseline_repeat_correct,updated_repeat_correct\n" + rows)
    assert main(["report", results]) == 0
    line = [text for text in capsys.readouterr().out.splitlines() if text.startswith("Wrong in both versions")][0]
    assert "c19, and 10 more." in line and "c20" not in line



CHANGED_WHILE_CORRECT = (
    "case_id,question,baseline_answer,baseline_repeat_answer,updated_answer,updated_repeat_answer,"
    "baseline_correct,baseline_repeat_correct,updated_correct,updated_repeat_correct\n"
    "kept,q1,Avoid the combination.,Avoid the combination.,Avoid the combination.,avoid the combination,1,1,1,1\n"
    "reworded,q2,Avoid the combination.,Avoid the combination.,Use with monitoring.,Use with monitoring.,1,1,1,1\n"
    "wavering,q3,Avoid the combination.,Avoid the combination.,Use with monitoring.,Avoid the combination.,1,1,1,1\n"
    "worse,q4,Avoid the combination.,Avoid the combination.,Use freely.,Use freely.,1,1,0,0\n"
)


def test_an_answer_that_changed_while_scored_correct_is_listed_and_keeps_its_state(tmp_path, write, capsys):
    results = write("results.csv", CHANGED_WHILE_CORRECT)
    assert main(["report", results]) == 0
    out = capsys.readouterr().out
    assert "correct_both                  3" in out and "stable_regression             1   cases: worse" in out
    assert ("Correct in both versions but with a changed answer: reworded, wavering (varied on re-run). The answer key "
            "scores both answers as correct; read them if the wording matters.") in out
    with open(tmp_path / "summary.json", encoding="utf-8") as f:
        summary = json.load(f)
    # counted as correct in both, as before; an answer that wavers between runs is listed as that
    assert summary["states"]["correct_both"] == 3 and summary["first_run"]["change_between_versions"]["count"] == 1
    assert summary["correct_both_answer_changed"] == {"stable": ["reworded"], "unconfirmed": [], "varied": ["wavering"]}
    assert summary["wrong_both_answer_changed"] == {"stable": [], "unconfirmed": [], "varied": []}
    rows = {row["case_id"]: row for row in read_csv(tmp_path / "review_cases.csv")}
    assert set(rows) == {"reworded", "wavering", "worse"}
    assert (rows["reworded"]["state"], rows["reworded"]["answer_change"]) == ("correct_both", "stable")
    assert (rows["wavering"]["state"], rows["wavering"]["answer_change"]) == ("correct_both", "varied")
    html, data = page_data(tmp_path / "report.html")
    # it has a card of its own, after the cases whose score changed, and the strip cell leads to it
    assert [(card["id"], card["state"], card["flag"]) for card in data["cards"]] == [
        ("worse", "stable_regression", None), ("reworded", "correct_both", "stable"), ("wavering", "correct_both", "varied")]
    assert data["cards"][1]["u"][0]["ans"] == "Use with monitoring."
    assert [cell for cell in data["strip"] if cell[0] in ("reworded", "kept")] == [["kept", "correct_both", -1],
                                                                                 ["reworded", "correct_both", 1]]
    assert data["strings"]["en"]["pill"]["correct_both_changed"] == "Correct in both, answer changed"
    assert data["strings"]["en"]["pill"]["correct_both_varied"] == "Correct in both, answer varied on re-run"
    assert main(["gate", results, "--max-stable-regressions", "1"]) == 0   # listing it changes no count the gate uses
    capsys.readouterr()
    # unless the gate is asked to count answers that changed while the score stayed the same
    assert main(["gate", results, "--max-stable-regressions", "1", "--max-answer-changes", "1"]) == 1
    out = capsys.readouterr().out
    assert "correct_both, answer changed\tcase reworded" in out and "correct_both, answer varied on re-run\tcase wavering" in out
    assert "answers that changed while the score stayed the same: 2 (limit 1) - over the limit" in out
    assert main(["gate", results, "--max-stable-regressions", "1", "--max-answer-changes", "2"]) == 0


def test_with_one_run_a_changed_correct_answer_is_marked_as_not_rerun(write, capsys):
    results = write("results.csv", "case_id,baseline_answer,updated_answer,baseline_correct,updated_correct\n"
                    "a,Avoid it.,Use with monitoring.,1,1\n")
    assert main(["report", results]) == 0
    assert "Correct in both versions but with a changed answer: a (not re-run)." in capsys.readouterr().out


def test_the_gate_can_limit_unstable_cases_when_asked(capsys):
    assert main(["gate", FIXTURE, "--max-stable-regressions", "3"]) == 0       # unstable cases are not checked by default
    assert "unstable cases" not in capsys.readouterr().out
    assert main(["gate", FIXTURE, "--max-stable-regressions", "3", "--max-unstable", "4"]) == 1
    out = capsys.readouterr().out
    assert out.count("unstable\tcase ") == 5 and "unstable cases: 5 (limit 4) - over the limit" in out
    assert main(["gate", FIXTURE, "--max-stable-regressions", "3", "--max-unstable", "5"]) == 0
    assert "unstable cases: 5 (limit 5)\n" in capsys.readouterr().out


def test_forcing_no_key_mode_says_the_scores_were_left_out_not_that_they_are_missing(tmp_path, capsys):
    assert main(["report", FIXTURE, "--mode", "nokey", "--out", str(tmp_path)]) == 0
    err = capsys.readouterr().err
    assert "because --mode nokey was given" in err and "left out on purpose" in err
    assert "no baseline_correct" not in err


MEDICINES = os.path.join(os.path.dirname(FIXTURE), "..", "..", "web", "sample_medicines.csv")


def test_the_second_example_is_made_up_and_shows_what_it_is_meant_to_show(tmp_path, capsys):
    """Invented drug names, illustration only: mean accuracy rises by one answer while three answers break in every run."""
    assert main(["report", MEDICINES, "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "First run accuracy: 7/12 to 8/12; regressions 3, improvements 4." in out
    assert "stable_regression             3   cases: m01, m02, m03" in out
    assert "Wrong in both versions but with a changed answer: m10." in out
    assert "Correct in both versions but with a changed answer: m11." in out
    with open(MEDICINES, encoding="utf-8") as f:
        text = f.read().lower()
    # no real medicine, enzyme or gene name: the page says the data is invented, and it has to be
    for real in ("statin", "warfarin", "cyp", "hla-", "mycin", "azole ", "pril ", "sartan", "fda", "cpic"):
        assert real not in text, real


def test_where_the_retrieved_passages_differ_is_counted_and_nothing_more(tmp_path, capsys):
    assert main(["report", MEDICINES, "--out", str(tmp_path)]) == 0
    assert ("Retrieved passages differ between the versions in 10/12 cases that list passages: stable_regression 3/3, "
            "stable_improvement 4/4, unstable 2/2, wrong_both 0/1, correct_both 1/2. This is a count, not a cause.") in capsys.readouterr().out
    with open(tmp_path / "summary.json", encoding="utf-8") as f:
        passages = json.load(f)["passages"]
    assert passages["cases_with_passages"] == 12 and passages["differ"] == 10
    assert passages["by_state"]["stable_regression"] == {"differ": 3, "n": 3}
    assert passages["by_state"]["wrong_both"] == {"differ": 0, "n": 1}

    # without an answer key the same count is given, in the words of that mode
    assert main(["report", MEDICINES, "--mode", "nokey", "--out", str(tmp_path / "nokey")]) == 0
    capsys.readouterr()
    html, data = page_data(tmp_path / "nokey" / "report.html")
    assert data["summary"]["passages"]["by_state"]["stable_change"] == {"differ": 8, "n": 9} and data["focus"] == "stable_change"
    assert "regress" not in html.lower()

    # a file that lists no passages says nothing about them
    assert main(["report", FIXTURE, "--out", str(tmp_path / "plain")]) == 0
    assert "Retrieved passages" not in capsys.readouterr().out
    with open(tmp_path / "plain" / "summary.json", encoding="utf-8") as f:
        assert "passages" not in json.load(f)


def test_a_passage_count_that_is_the_same_for_every_case_is_said_in_one_sentence(tmp_path, write, capsys):
    """The built-in example: the proposed version splits the handbook differently, so every passage has a new name."""
    library = os.path.join(os.path.dirname(FIXTURE), "..", "..", "web", "sample_results.csv")
    assert main(["report", library, "--out", str(tmp_path / "library")]) == 0
    out = capsys.readouterr().out
    assert ("Retrieved passages differ between the versions in all 30 cases that list passages, so this count does "
            "not set any group of cases apart.") in out
    assert "correct_both 17/17" not in out                      # no list of counts that are all "every case"
    with open(tmp_path / "library" / "summary.json", encoding="utf-8") as f:
        assert json.load(f)["passages"]["differ"] == 30         # the numbers are still in the file

    same = write("same.csv", "case_id,baseline_correct,updated_correct,baseline_context,updated_context\n"
                 "a,1,0,doc 1 | doc 2,doc 2 | doc 1\nb,1,1,doc 3,doc 3\n")
    assert main(["report", same, "--out", str(tmp_path / "same")]) == 0
    assert "Retrieved passages are the same in both versions in all 2 cases that list passages." in capsys.readouterr().out

    one = write("one.csv", "case_id,baseline_correct,updated_correct,baseline_context,updated_context\na,1,0,doc 1,doc 2\n")
    assert main(["report", one, "--out", str(tmp_path / "one")]) == 0
    assert "in 1/1 cases that list passages: regression_unconfirmed 1/1." in capsys.readouterr().out


SAME_SCORE_OTHER_ANSWER = (
    "case_id,question,expected,baseline_answer,baseline_repeat_answer,updated_answer,updated_repeat_answer,"
    "baseline_correct,baseline_repeat_correct,updated_correct,updated_repeat_correct\n"
    "rerun_differs,q1,not allowed,not allowed,fine to use,not allowed,not allowed,1,1,1,1\n"
    "versions_differ,q2,not allowed,not allowed,not allowed,fine with checks,fine with checks,1,1,1,1\n"
    "wrong_and_differ,q3,not allowed,fine,fine,risky,risky,0,0,0,0\n"
)


def test_a_score_that_holds_while_the_answer_does_not_is_shown_and_can_stop_the_gate(tmp_path, write, capsys):
    """Scores given in the file can agree while the text says something else. By the answer key these cases
    did not change; the report shows them all the same, and one option makes the gate count them."""
    results = write("results.csv", SAME_SCORE_OTHER_ANSWER)
    assert main(["report", results]) == 0
    out = capsys.readouterr().out
    assert "unstable                      0" in out                       # by the scores, nothing wavered
    assert "Correct in both versions but with a changed answer: versions_differ, rerun_differs (varied on re-run)." in out
    assert "Wrong in both versions but with a changed answer: wrong_and_differ." in out
    rows = {row["case_id"]: row["answer_change"] for row in read_csv(tmp_path / "review_cases.csv")}
    assert rows == {"rerun_differs": "varied", "versions_differ": "stable", "wrong_and_differ": "stable"}
    _, data = page_data(tmp_path / "report.html")
    assert sorted(card["id"] for card in data["cards"]) == ["rerun_differs", "versions_differ", "wrong_and_differ"]

    strict = ["gate", results, "--max-stable-regressions", "0", "--max-unstable", "0", "--max-incomplete", "0"]
    assert main(strict) == 0                                              # the answer key sees no change
    capsys.readouterr()
    assert main(strict + ["--max-answer-changes", "0"]) == 1
    assert "answers that changed while the score stayed the same: 3 (limit 0) - over the limit" in capsys.readouterr().out

    # without an answer key every changed answer is already counted, and the option says so
    assert main(["gate", results, "--mode", "nokey", "--max-answer-changes", "0"]) == 1
    printed = capsys.readouterr()
    assert "--max-answer-changes is for answer-key mode" in printed.err and "stable changes not yet judged: 2" in printed.out


def test_cases_that_only_word_overlap_calls_the_same_are_named(tmp_path, write, capsys):
    results = write("results.csv", "case_id,baseline_answer,baseline_repeat_answer,updated_answer,updated_repeat_answer\n"
                    "padded,the loan period is three weeks for every book in the main library,"
                    "the loan period is three weeks for every book in the main library,"
                    "the loan period is three weeks for every book in the main library today,"
                    "the loan period is three weeks for every book in the main library today\n"
                    "plain,yes,yes,yes,yes\n")
    assert main(["report", results, "--similarity", "0.9"]) == 0
    out = capsys.readouterr().out
    assert "same                          2" in out
    assert "1 case(s) are labelled as they are because of the word-overlap rule; exact match would label them differently: padded." in out
    with open(tmp_path / "summary.json", encoding="utf-8") as f:
        assert json.load(f)["labelled_by_similarity"] == ["padded"]
    assert main(["report", results]) == 0                                 # exact match: no such list
    assert "word-overlap rule" not in capsys.readouterr().out
    with open(tmp_path / "summary.json", encoding="utf-8") as f:
        assert "labelled_by_similarity" not in json.load(f)


def test_a_change_seen_in_a_single_run_passes_by_default_and_not_under_strict(write, capsys):
    """One run of each version confirms nothing. By default the gate says so and lets it through;
    --max-unconfirmed 0, or --strict, stops on it."""
    keyed = write("keyed.csv", "case_id,baseline_answer,baseline_correct,updated_answer,updated_correct\ns1,Major,1,Minor,0\n")
    plain = write("plain.csv", "case_id,baseline_answer,updated_answer\ns2,it is fine,it must not be used\n")
    for results, line in ((keyed, "regressions seen in a single run: 1 (limit 0) - over the limit"),
                          (plain, "changes seen in a single run: 1 (limit 0) - over the limit")):
        assert main(["gate", results]) == 0
        printed = capsys.readouterr()
        assert "unconfirmed" in printed.err and "--max-unconfirmed 0" in printed.err
        assert main(["gate", results, "--max-unconfirmed", "0"]) == 1
        assert line in capsys.readouterr().out
        assert main(["gate", results, "--strict"]) == 1
        assert line in capsys.readouterr().out
        assert main(["gate", results, "--strict", "--max-unconfirmed", "1"]) == 0      # a value given stays
        capsys.readouterr()


def test_strict_turns_on_every_limit(write, capsys):
    assert main(["gate", FIXTURE]) == 1                              # three stable regressions
    assert "unstable cases" not in capsys.readouterr().out
    assert main(["gate", FIXTURE, "--strict"]) == 1
    out = capsys.readouterr().out
    for line in ("stable regressions: 3 (limit 0) - over the limit", "unstable cases: 5 (limit 0) - over the limit",
                 "regressions seen in a single run: 0 (limit 0)", "answers that changed while the score stayed the same: 2 (limit 0)"):
        assert line in out, line
    clean = write("clean.csv", "case_id,baseline_answer,baseline_repeat_answer,updated_answer,updated_repeat_answer,"
                  "baseline_correct,baseline_repeat_correct,updated_correct,updated_repeat_correct\na,yes,yes,yes,yes,1,1,1,1\n")
    assert main(["gate", clean, "--strict"]) == 0
    assert "gate: every count is within its limit" in capsys.readouterr().out


def test_scores_without_answers_cannot_show_a_changed_answer_and_the_gate_says_so(write, capsys):
    scores = write("scores.csv", "case_id,baseline_correct,baseline_repeat_correct,updated_correct,updated_repeat_correct\ns3,1,1,1,1\n")
    assert main(["gate", scores]) == 0                               # by the scores alone nothing changed
    capsys.readouterr()
    for arguments in (["--max-answer-changes", "0"], ["--strict"]):
        assert main(["gate", scores] + arguments) == 1
        out = capsys.readouterr().out
        assert "no answer text in the file\tcase s3" in out
        assert "cases with no answer text, so a changed answer cannot be seen: 1 (limit 0) - over the limit" in out


def test_the_same_passages_in_another_order_or_number_are_counted_apart(tmp_path, write, capsys):
    results = write("results.csv", "case_id,baseline_answer,baseline_repeat_answer,updated_answer,updated_repeat_answer,"
                    "baseline_context,updated_context\n"
                    "order,yes,yes,no,no,A | B,B | A\nnumber,yes,yes,no,no,A | A | B,A | B | B\n"
                    "same,yes,yes,no,no,A | B,A | B\nother,yes,yes,no,no,A | B,A | C\n")
    assert main(["report", results]) == 0
    out = capsys.readouterr().out
    assert "Retrieved passages differ between the versions in 1/4 cases that list passages: stable_change 1/4." in out
    assert "In 2 case(s) the same passages come in another order or number." in out
    html, data = page_data(tmp_path / "report.html")
    assert data["summary"]["passages"] == {"cases_with_passages": 4, "differ": 1, "reordered": 2, "content_changed": 0,
                                           "by_state": {"stable_change": {"differ": 1, "n": 4}}}
    moves = {card["id"]: card["mov"] for card in data["cards"]}
    assert moves["order"] == [["A", 1, 2, None, None, False], ["B", 2, 1, None, None, False]]      # each passage and where it stood
    assert moves["number"] == [["B", 3, 2, None, None, False]] and moves["same"] == [] and moves["other"] == []
    assert {card["id"]: card["ord"] for card in data["cards"]} == {"order": True, "number": True, "same": False, "other": False}


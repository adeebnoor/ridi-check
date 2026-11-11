"""Edge-case and large results files through `report` and `gate`, as a person would run them.

Every refused file must end with exit status 2, one line that says what is wrong, no traceback
and no report written. Every accepted file must come back out unchanged.
"""

import csv
import json
import os
import re

import pytest

from ridi_check.cli import main
from ridi_check.contract import read_results

KEY_HEADER = "case_id,baseline_correct,baseline_repeat_correct,updated_correct,updated_repeat_correct\n"

REFUSED = [
    ("an empty file", "", "No rows found in the file."),
    ("a header and nothing else", KEY_HEADER, "No rows found in the file."),
    ("blank lines only", "\n\n  \n,,,\n", "No rows found in the file."),
    ("a case_id used twice", KEY_HEADER + "a,1,1,1,1\nb,1,1,1,1\n\na,1,1,0,0\n",
     "Row 5: case_id 'a' appears more than once (first in row 2)."),
    ("no case_id column", "id,baseline_correct,updated_correct\na,1,1\n", "The file needs a case_id column."),
    ("no column for the proposed version", "case_id,baseline_correct,baseline_repeat_correct\na,1,1\n",
     "The file needs baseline_correct and updated_correct (0 or 1), or baseline_answer and updated_answer."),
    ("a correctness value that is a word", KEY_HEADER + "1,1,1,1,1\n2,true,1,1,1\n",
     "Row 3 (case 2): baseline_correct must be 0 or 1, got 'true'."),
    ("a correctness value that is a fraction", KEY_HEADER + "1,1,1,0.5,1\n",
     "Row 2 (case 1): updated_correct must be 0 or 1, got '0.5'."),
    ("a row cut short", KEY_HEADER + "1,1,1,1,1\n2,1,1\n", "Row 3 (case 2): updated_correct is empty. It must be 0 or 1."),
    ("a case_id of spaces", KEY_HEADER + "   ,1,1,1,1\n", "Row 2: case_id is missing."),
    ("the same column twice", "case_id,baseline_correct,updated_correct,updated_correct\na,1,1,1\n",
     "Column 'updated_correct' appears more than once."),
]


@pytest.mark.parametrize("label, text, message", REFUSED, ids=[r[0] for r in REFUSED])
def test_refused_files_get_one_clear_line_and_exit_status_2(write, tmp_path, capsys, label, text, message):
    results = write("results.csv", text)
    for command in ("report", "gate"):
        assert main([command, results]) == 2
        printed = capsys.readouterr()
        assert printed.err.strip() == f"ridi-check: {message}"
        assert "Traceback" not in printed.err and printed.out == ""
    assert os.listdir(tmp_path) == ["results.csv"]          # no report from a file that was refused


def test_a_folder_or_a_missing_file_is_refused_the_same_way(tmp_path, capsys):
    for path in (str(tmp_path), str(tmp_path / "nothing_here.csv")):
        assert main(["report", path]) == 2
        err = capsys.readouterr().err
        assert err.startswith("ridi-check: The file could not be read:") and "Traceback" not in err


ARABIC_QUESTION = "ما مدة الإعارة؟\nوهل تُجدَّد؟"
ARABIC_BEFORE = '٢١ يوماً، "قابلة" للتجديد'
ARABIC_AFTER = "١٤ يوماً\r\n<b>لا</b> تُجدَّد 🙂 </script><script>alert(1)</script>"
FORMULA = "=1+1"


def _special_file(path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        out = csv.writer(f)
        out.writerow(["case_id", "question", "baseline_answer", "baseline_repeat_answer",
                      "updated_answer", "updated_repeat_answer"])
        out.writerow(["١", ARABIC_QUESTION, ARABIC_BEFORE, ARABIC_BEFORE, ARABIC_AFTER, ARABIC_AFTER])
        out.writerow(["tab\there", "a,b;c|d", FORMULA, FORMULA, "'quoted' & <tagged>", "'quoted' & <tagged>"])
        out.writerow(["same", "plain", "x", "x", "X.", " x "])


def test_arabic_symbols_markup_and_line_breaks_inside_cells_come_back_unchanged(tmp_path, capsys):
    results = str(tmp_path / "results.csv")
    _special_file(results)
    assert main(["report", results]) == 0
    assert "stable_change                 2   cases: ١, tab\there" in capsys.readouterr().out

    with open(tmp_path / "review_cases.csv", encoding="utf-8", newline="") as f:
        rows = {row["case_id"]: row for row in csv.DictReader(f)}
    assert set(rows) == {"١", "tab\there"}
    assert rows["١"]["baseline_answer"] == ARABIC_BEFORE and rows["١"]["updated_repeat_answer"] == ARABIC_AFTER
    assert rows["tab\there"]["baseline_answer"] == FORMULA      # written as given: see docs/REFERENCE.md

    with open(tmp_path / "report.html", encoding="utf-8") as f:
        html = f.read()
    # the answer that tries to close the data block and start a script does neither
    assert "<script>alert(1)</script>" not in html and "<b>لا</b>" not in html
    blob = re.search(r'<script id="ridi-data" type="application/json">(.*?)</script>', html, re.S).group(1)
    cards = {card["id"]: card for card in json.loads(blob)["cards"]}
    assert cards["١"]["q"] == ARABIC_QUESTION
    assert cards["١"]["u"][0]["ans"] == ARABIC_AFTER and cards["١"]["b"][1]["ans"] == ARABIC_BEFORE
    assert cards["tab\there"]["u"][0]["ans"] == "'quoted' & <tagged>"

    assert main(["gate", results, "--max-unjudged-changes", "2"]) == 0


def test_one_run_of_each_version_is_reported_as_unconfirmed_never_as_stable(write, tmp_path, capsys):
    results = write("results.csv", "case_id,baseline_correct,updated_correct\na,1,0\nb,0,1\nc,1,1\nd,0,0\n")
    assert main(["report", results]) == 0
    out = capsys.readouterr().out
    assert "4 cases, answer-key mode" in out and "regression_unconfirmed" in out and "improvement_unconfirmed" in out
    assert "re-run variation: current no second run, proposed no second run" in out
    with open(tmp_path / "summary.json", encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["states"]["stable_regression"] == 0 and summary["states"]["regression_unconfirmed"] == 1
    assert summary["confirmable_cases"] == 0 and summary["runs_per_version"] == {"current": 1, "proposed": 1}
    assert summary["first_run"]["rerun_variation_current"] is None

    assert main(["gate", results]) == 0          # nothing was confirmed, and the gate says so instead of failing
    printed = capsys.readouterr()
    assert "stable regressions: 0 (limit 0)" in printed.out and "unconfirmed" in printed.err


def test_one_case_is_one_case(write, capsys):
    results = write("results.csv", KEY_HEADER + "only,1,1,0,0\n")
    assert main(["report", results]) == 0
    assert capsys.readouterr().out.startswith("1 case, answer-key mode")
    assert main(["gate", results]) == 1
    assert ", 1 case, " in capsys.readouterr().out


SHEET = ("case_id\tquestion\tbaseline_answer\tbaseline_repeat_answer\tupdated_answer\tupdated_repeat_answer\r\n"
         "١\tما مدة الإعارة؟\t٢١ يوماً\t٢١ يوماً\t١٤ يوماً\t١٤ يوماً\r\n"
         "2\tplain\tyes\tyes\tyes\tyes\r\n")


@pytest.mark.parametrize("encoding", ["utf-16", "utf-16-le", "utf-16-be", "utf-8-sig", "utf-8"])
def test_spreadsheet_exports_are_read(tmp_path, encoding):
    """Excel's "Unicode Text" is tab-separated UTF-16 with a byte-order mark; "CSV UTF-8" is UTF-8 with one."""
    mark = {"utf-16-le": b"\xff\xfe", "utf-16-be": b"\xfe\xff"}.get(encoding, b"")
    path = tmp_path / "results.txt"
    path.write_bytes(mark + SHEET.encode(encoding))
    cases, mode = read_results(str(path))
    assert mode == "nokey" and [c.case_id for c in cases] == ["١", "2"]
    assert cases[0].question == "ما مدة الإعارة؟" and cases[0].updated[1].answer == "١٤ يوماً"


@pytest.mark.parametrize("encoding", ["cp1256", "latin-1"])
def test_a_file_in_a_local_code_page_is_refused_with_the_way_to_fix_it(tmp_path, capsys, encoding):
    text = "case_id,baseline_answer,updated_answer\n1,نعم,لا\n" if encoding == "cp1256" else \
        "case_id,baseline_answer,updated_answer\n1,café,thé\n"
    path = tmp_path / "results.csv"
    path.write_bytes(text.encode(encoding))
    for command in ("report", "gate"):
        assert main([command, str(path)]) == 2
        err = capsys.readouterr().err
        assert "is not UTF-8 text" in err and 'Save As > "CSV UTF-8 (Comma delimited)"' in err
        assert "codec" not in err and "Traceback" not in err


def test_the_other_input_files_get_the_same_reading_and_the_same_message(tmp_path, write, capsys):
    results = write("results.csv", "case_id,baseline_answer,baseline_repeat_answer,updated_answer,updated_repeat_answer\n"
                    "a,one,one,two,two\n")
    judged = tmp_path / "judgments.txt"
    judged.write_bytes("case_id\tjudgment\r\na\tworse\r\n".encode("utf-16"))
    assert main(["gate", results, "--judgments", str(judged)]) == 1
    assert "stable changes judged worse by the owner: 1" in capsys.readouterr().out
    judged.write_bytes("case_id,judgment\na,أسوأ\n".encode("cp1256"))
    assert main(["gate", results, "--judgments", str(judged)]) == 2
    assert "The judgments file is not UTF-8 text" in capsys.readouterr().err
    questions = tmp_path / "questions.csv"
    questions.write_bytes("case_id,question\n1,ما مدة الإعارة؟\n".encode("cp1256"))
    assert main(["run", "--questions", str(questions), "--current", "python:fake_systems:current",
                 "--proposed", "python:fake_systems:proposed", "--out", str(tmp_path / "out")]) == 2
    assert "The questions file is not UTF-8 text" in capsys.readouterr().err


def test_a_very_long_cell_does_not_stop_the_report(tmp_path, capsys):
    long_answer = "word " * 400_000                       # two million characters in one cell
    path = tmp_path / "results.csv"
    path.write_text("case_id,baseline_answer,baseline_repeat_answer,updated_answer,updated_repeat_answer\r\n"
                    f"a,{long_answer},{long_answer},{long_answer}end,{long_answer}end\r\n"
                    "b,same,same,same,same\r\n", encoding="utf-8", newline="")
    assert main(["report", str(path)]) == 0
    assert "stable_change                 1   cases: a" in capsys.readouterr().out


@pytest.mark.parametrize("data", [
    b"case_id,baseline_answer,updated_answer\na,with\x00null,with\x00null\n",
    "case_id,baseline_answer,updated_answer\na,yes,no\n".encode("utf-16-le"),      # UTF-16 without its mark
], ids=["a null character in a cell", "UTF-16 without a byte-order mark"])
def test_null_characters_are_refused_the_same_way_on_every_python(tmp_path, capsys, data):
    path = tmp_path / "results.csv"
    path.write_bytes(data)
    for command in ("report", "gate"):
        assert main([command, str(path)]) == 2
        err = capsys.readouterr().err
        assert "The file holds null characters, so it is not plain UTF-8 text. Save it as UTF-8" in err


def test_a_cell_above_the_size_limit_is_refused_in_words(write, capsys, monkeypatch):
    before = csv.field_size_limit(1000)
    try:
        results = write("results.csv", "case_id,baseline_answer,updated_answer\na,short,short\nb," + "x" * 2000 + ",y\n")
        for command in ("report", "gate"):
            assert main([command, results]) == 2
            err = capsys.readouterr().err
            assert "Near line 3: one cell holds more than 1,000 characters" in err and "Traceback" not in err
    finally:
        csv.field_size_limit(before)


def _large_file(path, n):
    """n cases, three runs of each version: a tenth each of stable regressions, stable improvements,
    cases whose proposed version does not hold on re-run, and cases wrong in both; the rest correct in both."""
    kinds = {0: ([1, 1, 1], [0, 0, 0]), 1: ([0, 0, 0], [1, 1, 1]), 2: ([1, 1, 1], [1, 0, 1]), 3: ([0, 0, 0], [0, 0, 0])}
    runs = ("", "_repeat", "_repeat2")
    with open(path, "w", encoding="utf-8", newline="") as f:
        out = csv.writer(f, lineterminator="\n")
        out.writerow(["case_id", "question", "expected"] + [f"baseline{r}_answer" for r in runs]
                     + [f"updated{r}_answer" for r in runs] + [f"baseline{r}_correct" for r in runs]
                     + [f"updated{r}_correct" for r in runs] + ["baseline_context", "updated_context"])
        for i in range(n):
            right, wrong = f"Item {i} is in section {i % 7}.", f"Item {i} is in section {(i + 3) % 7}."
            b, u = kinds.get(i % 10, ([1, 1, 1], [1, 1, 1]))
            out.writerow([f"case-{i:06d}", f"Where is item {i}?", right] + [right if x else wrong for x in b]
                         + [right if x else wrong for x in u] + b + u + [f"doc-{i % 500} | doc-{i % 501}"] * 2)


def test_twenty_thousand_cases_with_three_runs_give_exact_counts(tmp_path, capsys):
    n, tenth = 20_000, 2_000
    results = str(tmp_path / "results.csv")
    _large_file(results, n)

    assert main(["report", results]) == 0
    capsys.readouterr()
    with open(tmp_path / "summary.json", encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["cases"] == n and summary["runs_per_version"] == {"current": 3, "proposed": 3}
    assert summary["states"] == {"stable_regression": tenth, "stable_improvement": tenth, "regression_unconfirmed": 0,
                                 "improvement_unconfirmed": 0, "unstable": tenth, "wrong_both": tenth,
                                 "correct_both": n - 4 * tenth, "incomplete": 0}
    first = summary["first_run"]
    assert first["change_between_versions"]["count"] == 2 * tenth
    assert first["rerun_variation_current"]["count"] == 0 and first["rerun_variation_proposed"]["count"] == tenth
    assert first["accuracy_current"]["count"] == first["accuracy_proposed"]["count"] == n - 2 * tenth
    assert (first["regressions"], first["improvements"]) == (tenth, tenth)
    assert first["changes_cancelled_in_mean_accuracy"] == 2 * tenth      # equal accuracy, four thousand changed answers
    with open(tmp_path / "review_cases.csv", encoding="utf-8", newline="") as f:
        assert sum(1 for _ in csv.DictReader(f)) == 4 * tenth

    assert main(["gate", results]) == 1
    out = capsys.readouterr().out
    assert out.count("stable_regression\tcase ") == tenth and f"stable regressions: {tenth} (limit 0) - over the limit" in out
    assert main(["gate", results, "--max-stable-regressions", str(tenth)]) == 0
    capsys.readouterr()

    assert main(["report", results, "--mode", "nokey", "--out", str(tmp_path / "nokey")]) == 0
    with open(tmp_path / "nokey" / "summary.json", encoding="utf-8") as f:
        states = json.load(f)["states"]
    assert states == {"stable_change": 2 * tenth, "change_unconfirmed": 0, "unstable": tenth,
                      "same": n - 3 * tenth, "incomplete": 0}

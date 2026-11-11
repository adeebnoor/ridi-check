"""results.csv validation: every rejection says which row."""

import pytest

from ridi_check.contract import ContractError, parse_results, run_column

HEAD = "case_id,baseline_answer,updated_answer\n"


def rejects(text, *fragments, mode="auto"):
    with pytest.raises(ContractError) as info:
        parse_results(text, mode)
    message = str(info.value)
    for fragment in fragments:
        assert fragment in message, message
    return message


def test_empty_file_and_header_only():
    rejects("", "No rows")
    rejects(HEAD, "No rows")


def test_missing_case_id_column():
    rejects("id,baseline_answer,updated_answer\n1,a,b\n", "case_id column")


def test_missing_case_id_value_names_the_row():
    rejects(HEAD + "1,a,b\n,c,d\n", "Row 3", "case_id is missing")


def test_duplicate_case_id_names_both_rows():
    rejects(HEAD + "1,a,b\n2,c,d\n1,e,f\n", "Row 4", "'1'", "row 2")


def test_non_binary_correct_names_row_case_and_column():
    text = "case_id,baseline_correct,updated_correct\n1,1,0\n2,yes,0\n"
    rejects(text, "Row 3 (case 2)", "baseline_correct", "'yes'")
    text = ("case_id,baseline_correct,updated_correct,updated_repeat_correct\n"
            "1,1,0,0\n2,1,0,2\n")
    rejects(text, "Row 3 (case 2)", "updated_repeat_correct", "'2'")


def test_empty_first_run_correct_is_rejected():
    rejects("case_id,baseline_correct,updated_correct\n1,1,\n", "Row 2 (case 1)", "updated_correct is empty")


def test_neither_answers_nor_correctness():
    rejects("case_id,question\n1,why\n", "baseline_correct and updated_correct", "baseline_answer and updated_answer")
    rejects("case_id,baseline_answer,updated_correct\n1,a,1\n", "baseline_answer and updated_answer")


def test_empty_first_run_answer_is_rejected_without_an_answer_key():
    rejects(HEAD + "1,a,b\n2,,b\n", "Row 3 (case 2)", "baseline_answer is empty")


def test_answer_without_correctness_in_key_mode_is_rejected():
    text = ("case_id,baseline_answer,baseline_repeat_answer,updated_answer,baseline_correct,updated_correct\n"
            "1,a,a,b,1,0\n")
    rejects(text, "Row 2 (case 1)", "baseline_repeat_answer", "baseline_repeat_correct")


def test_duplicate_columns_are_rejected():
    rejects("case_id,baseline_answer,updated_answer,baseline_answer\n1,a,b,c\n", "more than once")
    rejects("case_id,baseline_answer,updated_answer,baseline_repeat_answer,baseline_repeat1_answer\n1,a,b,c,d\n",
            "same run")


def test_forced_modes_need_their_columns():
    rejects(HEAD + "1,a,b\n", "Answer-key mode needs", mode="key")
    rejects("case_id,baseline_correct,updated_correct\n1,1,0\n", "No-key mode needs", mode="nokey")


def test_reads_bom_quotes_spaces_blank_lines_and_mixed_case_headers():
    text = ('\ufeffCase_ID , Question, Baseline_Answer ,UPDATED_ANSWER,baseline_context\r\n'
            '\r\n'
            ' 7 ,"What, exactly?","line one\nline two", "say ""hi""" ,doc a | doc b |\r\n')
    cases, mode = parse_results(text)
    assert mode == "nokey" and len(cases) == 1
    case = cases[0]
    assert (case.case_id, case.row, case.question) == ("7", 3, "What, exactly?")   # the blank line is row 2
    assert case.baseline[0].answer == "line one\nline two"
    assert case.updated[0].answer == 'say "hi"'
    assert case.baseline_context == ["doc a", "doc b"]


def test_runs_are_ordered_by_number_and_missing_repeats_are_skipped():
    names = [run_column("baseline", k, "answer") for k in (1, 2, 3, 11)]
    assert names == ["baseline_answer", "baseline_repeat_answer", "baseline_repeat2_answer", "baseline_repeat10_answer"]
    text = ("case_id,baseline_repeat10_answer,baseline_repeat2_answer,baseline_answer,baseline_repeat_answer,updated_answer\n"
            "1,r11,r3,r1,r2,u1\n"
            "2,,r3,r1,,u1\n")
    cases, _ = parse_results(text)
    assert [r.answer for r in cases[0].baseline] == ["r1", "r2", "r3", "r11"]
    assert [r.answer for r in cases[1].baseline] == ["r1", "r3"]
    assert len(cases[0].updated) == 1


def test_cells_pasted_from_a_spreadsheet_and_semicolon_files_are_read():
    tabbed = "case_id\tbaseline_answer\tupdated_answer\n1\tyes, sir\tno\n"
    cases, mode = parse_results(tabbed)
    assert mode == "nokey" and cases[0].baseline[0].answer == "yes, sir" and cases[0].updated[0].answer == "no"
    semicolons = "case_id;baseline_correct;updated_correct\n1;1;0\n"
    cases, mode = parse_results(semicolons)
    assert mode == "key" and (cases[0].baseline[0].correct, cases[0].updated[0].correct) == (1, 0)


def test_written_csv_reads_back_whatever_the_cells_hold():
    from ridi_check.contract import to_csv
    answers = ['plain', 'a,b', 'say "hi"', 'two\nlines', 'old\rmac', '=1+1', 'نص عربي، بفاصلة']
    text = to_csv(["case_id", "baseline_answer", "updated_answer"], [[f"c{i}", a, a] for i, a in enumerate(answers)])
    cases, _ = parse_results(text)
    assert [c.baseline[0].answer for c in cases] == answers


def test_correctness_only_file_is_answer_key_mode():
    cases, mode = parse_results("case_id,baseline_correct,updated_correct\n1,1,0\n")
    assert mode == "key" and cases[0].baseline[0].correct == 1 and cases[0].updated[0].correct == 0

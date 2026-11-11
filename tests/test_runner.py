"""`ridi-check run`: recording, resume after an interruption, failed calls, the contract file."""

import csv
import json
import os

import pytest

import fake_systems
from ridi_check.analysis import analyse
from ridi_check.contract import read_results
from ridi_check.runner import RunConfig, RunError, load_raw, read_questions, run

QUESTIONS = "case_id,question\n1,question one\n2,question two\n3,question three\n"


@pytest.fixture(autouse=True)
def _reset():
    fake_systems.reset()
    yield
    fake_systems.reset()


def config(write, tmp_path, questions=QUESTIONS, **overrides):
    values = dict(
        questions=write("questions.csv", questions), current="python:fake_systems:current",
        proposed="python:fake_systems:proposed", out_dir=str(tmp_path / "out"), retry_wait=0, concurrency=2,
    )
    values.update(overrides)
    return RunConfig(**values)


def raw_records(out_dir):
    with open(os.path.join(out_dir, "raw_outputs.jsonl"), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def results_rows(out_dir):
    with open(os.path.join(out_dir, "results.csv"), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_run_writes_raw_outputs_manifest_and_results(write, tmp_path):
    cfg = config(write, tmp_path, current_label="prompt v3", proposed_label="prompt v4")
    outcome = run(cfg)
    assert (outcome.calls_planned, outcome.calls_ok, outcome.calls_failed, outcome.calls_skipped) == (12, 12, 0, 0)

    records = raw_records(cfg.out_dir)
    assert len(records) == 12
    assert {(r["case_id"], r["version"], r["run"]) for r in records} == {
        (c, v, k) for c in "123" for v in ("current", "proposed") for k in (1, 2)}
    for r in records:
        assert r["status"] == "ok" and r["error"] is None and r["attempt"] == 1
        assert r["started_at"] <= r["ended_at"] and r["answer"] and r["context"]

    rows = results_rows(cfg.out_dir)
    assert list(rows[0]) == ["case_id", "question", "baseline_answer", "baseline_repeat_answer", "updated_answer",
                             "updated_repeat_answer", "baseline_context", "updated_context"]
    assert rows[2]["baseline_answer"] == "old answer to question three"
    assert rows[2]["updated_repeat_answer"] == "new answer to question three"
    assert rows[0]["baseline_context"] == "doc 1 | doc 2" and rows[0]["updated_context"] == "doc 2 | doc 3"

    with open(os.path.join(cfg.out_dir, "run_manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    assert len(manifest["questions_sha256"]) == 64 and manifest["runs"] == 2 and manifest["tool_version"]
    assert manifest["concurrency"] == 2 and manifest["retries"] == 2
    current = dict(manifest["systems"]["current"])
    assert len(current.pop("python_source_sha256")) == 64
    assert current == {"definition": "python:fake_systems:current", "type": "python", "label": "prompt v3"}
    assert manifest["systems"]["proposed"]["label"] == "prompt v4"
    assert manifest["invocations"][0]["status"] == "completed" and manifest["invocations"][0]["started_at"]

    cases, mode = read_results(os.path.join(cfg.out_dir, "results.csv"))
    assert mode == "nokey" and analyse(cases, mode).ids("stable_change") == ["3"]


def test_first_pass_is_complete_before_any_repeat(write, tmp_path):
    cfg = config(write, tmp_path, concurrency=1)
    run(cfg)
    assert [r["run"] for r in raw_records(cfg.out_dir)] == [1] * 6 + [2] * 6


def test_resume_after_an_interrupted_run(write, tmp_path):
    cfg = config(write, tmp_path, concurrency=1)
    fake_systems.interrupt_after = 5
    first = run(cfg)
    assert first.interrupted and first.results_path is None
    assert not os.path.exists(os.path.join(cfg.out_dir, "results.csv"))
    raw_path = os.path.join(cfg.out_dir, "raw_outputs.jsonl")
    with open(raw_path, "rb") as f:
        before = f.read()
    assert len(raw_records(cfg.out_dir)) == 5 and first.recorded_ok == 5

    fake_systems.reset()
    second = run(cfg)
    assert not second.interrupted
    assert (second.calls_skipped, second.calls_ok) == (5, 7)
    assert len(fake_systems.calls) == 7                      # only the calls that were missing
    with open(raw_path, "rb") as f:
        after = f.read()
    assert after.startswith(before)                          # earlier output is kept, byte for byte
    assert len(raw_records(cfg.out_dir)) == 12
    assert len(results_rows(cfg.out_dir)) == 3

    with open(os.path.join(cfg.out_dir, "run_manifest.json"), encoding="utf-8") as f:
        statuses = [i["status"] for i in json.load(f)["invocations"]]
    assert statuses == ["interrupted", "completed"]

    fake_systems.reset()
    third = run(cfg)                                          # nothing left to do
    assert third.calls_skipped == 12 and fake_systems.calls == []


def test_resume_tolerates_a_line_cut_short_by_a_kill(write, tmp_path):
    cfg = config(write, tmp_path, concurrency=1)
    run(cfg)
    raw_path = os.path.join(cfg.out_dir, "raw_outputs.jsonl")
    with open(raw_path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines[:4]) + "\n" + lines[4][:30])   # five lines, the last one truncated
    fake_systems.reset()
    outcome = run(cfg)
    assert outcome.calls_skipped == 4 and outcome.calls_ok == 8 and len(fake_systems.calls) == 8
    ok, _, unreadable = load_raw(raw_path)
    assert len(ok) == 12 and unreadable == 1


def test_a_failed_call_is_recorded_as_failed_and_the_case_is_not_dropped(write, tmp_path):
    fake_systems.fail_questions.add("question two")
    cfg = config(write, tmp_path, retries=1)
    outcome = run(cfg)
    assert outcome.calls_failed == 4 and outcome.calls_ok == 8 and len(outcome.failed) == 4

    failed = [r for r in raw_records(cfg.out_dir) if r["status"] == "failed"]
    assert len(failed) == 8                                  # 4 calls, 2 attempts each, every attempt recorded
    assert {r["case_id"] for r in failed} == {"2"}
    assert all(r["error"] == "RuntimeError: backend down for 'question two'" and r["answer"] is None for r in failed)
    assert sorted({(r["attempt"], r["max_attempts"]) for r in failed}) == [(1, 2), (2, 2)]

    rows = results_rows(cfg.out_dir)
    assert [r["case_id"] for r in rows] == ["1", "2", "3"]
    assert rows[1]["baseline_answer"] == "" and "current#1: RuntimeError" in rows[1]["run_errors"]
    cases, mode = read_results(os.path.join(cfg.out_dir, "results.csv"))
    a = analyse(cases, mode)
    assert a.ids("incomplete") == ["2"] and a.n == 3 and a.n_compared == 2

    # the next invocation retries only the failed calls
    fake_systems.reset()
    again = run(cfg)
    assert again.calls_skipped == 8 and again.calls_ok == 4 and not again.failed
    assert "run_errors" not in results_rows(cfg.out_dir)[0]
    assert len([r for r in raw_records(cfg.out_dir) if r["status"] == "failed"]) == 8   # history kept


def test_retries_are_bounded_and_recorded(write, tmp_path):
    fake_systems.fail_first_attempts["question one"] = 1
    cfg = config(write, tmp_path, concurrency=1, runs=1)
    outcome = run(cfg)
    assert outcome.calls_failed == 0
    one = [r for r in raw_records(cfg.out_dir) if r["case_id"] == "1" and r["version"] == "current"]
    assert [(r["attempt"], r["status"]) for r in one] == [(1, "failed"), (2, "ok")]
    assert one[0]["error"] == "TimeoutError: slow backend"


def test_a_failed_repeat_leaves_the_case_unconfirmed(write, tmp_path):
    cfg = config(write, tmp_path, concurrency=1, retries=0)
    run(cfg)
    raw_path = os.path.join(cfg.out_dir, "raw_outputs.jsonl")
    kept = [r for r in raw_records(cfg.out_dir) if not (r["case_id"] == "3" and r["version"] == "proposed" and r["run"] == 2)]
    with open(raw_path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in kept)
    fake_systems.fail_questions.add("question three")
    outcome = run(cfg)
    assert outcome.calls_failed == 1
    cases, mode = read_results(os.path.join(cfg.out_dir, "results.csv"))
    assert analyse(cases, mode).ids("change_unconfirmed") == ["3"]


def test_expected_answers_give_answer_key_mode_with_scores(write, tmp_path):
    questions = "case_id,question,expected\n1,question one,old answer to question one\n3,question three,old answer to question three\n"
    cfg = config(write, tmp_path, questions=questions)
    run(cfg)
    rows = results_rows(cfg.out_dir)
    assert [(r["baseline_correct"], r["baseline_repeat_correct"], r["updated_correct"], r["updated_repeat_correct"])
            for r in rows] == [("1", "1", "1", "1"), ("1", "1", "0", "0")]
    cases, mode = read_results(os.path.join(cfg.out_dir, "results.csv"))
    assert mode == "key" and analyse(cases, mode).ids("stable_regression") == ["3"]


def test_custom_scorer(write, tmp_path):
    questions = "case_id,question,expected\n1,question one,OLD\n3,question three,OLD\n"
    cfg = config(write, tmp_path, questions=questions, scorer="fake_systems:scorer_contains")
    run(cfg)
    assert [r["updated_correct"] for r in results_rows(cfg.out_dir)] == ["1", "0"]
    with open(os.path.join(cfg.out_dir, "run_manifest.json"), encoding="utf-8") as f:
        assert json.load(f)["scorer"] == "fake_systems:scorer_contains"


def test_more_than_two_runs_use_the_repeat2_columns(write, tmp_path):
    cfg = config(write, tmp_path, runs=3)
    run(cfg)
    assert "baseline_repeat2_answer" in results_rows(cfg.out_dir)[0]
    cases, _ = read_results(os.path.join(cfg.out_dir, "results.csv"))
    assert len(cases[0].baseline) == 3 and len(cases[0].updated) == 3


def test_string_results_empty_answers_and_wrong_shapes(write, tmp_path):
    cfg = config(write, tmp_path, current="python:fake_systems:plain_string", proposed="fake_systems:empty", runs=1)
    run(cfg)
    row = results_rows(cfg.out_dir)[0]
    assert row["baseline_answer"] == "just text" and row["updated_answer"] == "(empty answer)"

    cfg = config(write, tmp_path, proposed="python:fake_systems:wrong_shape", runs=1, retries=0,
                 out_dir=str(tmp_path / "out2"))
    outcome = run(cfg)
    assert outcome.calls_failed == 3
    assert "must return" in [r for r in raw_records(cfg.out_dir) if r["status"] == "failed"][0]["error"]


def test_changed_inputs_are_refused_instead_of_mixed(write, tmp_path):
    cfg = config(write, tmp_path)
    run(cfg)
    with pytest.raises(RunError, match="questions file has changed"):
        run(config(write, tmp_path, questions=QUESTIONS + "4,question four\n"))
    with pytest.raises(RunError, match="proposed system definition has changed"):
        run(config(write, tmp_path, proposed="python:fake_systems:current"))
    assert len(raw_records(cfg.out_dir)) == 12               # nothing was added or removed


@pytest.mark.parametrize("text, name, fragment", [
    ("case_id,question\n1,a\n1,b\n", "q.csv", "row 3: case_id '1' appears more than once"),
    ("case_id,question\n1,a\n,b\n", "q.csv", "row 3: case_id is missing"),
    ("case_id,question\n1,\n", "q.csv", "row 2 (case 1): question is empty"),
    ("id,question\n1,a\n", "q.csv", "needs a case_id column"),
    ("case_id,question,expected\n1,a,x\n2,b,\n", "q.csv", "row 3 (case 2): expected is empty"),
    ('{"case_id": 1, "question": "a"}\nnot json\n', "q.jsonl", "line 2: not valid JSON"),
    ("", "q.csv", "empty"),
])
def test_bad_questions_files_say_which_row(write, text, name, fragment):
    with pytest.raises(RunError) as info:
        read_questions(write(name, text))
    assert fragment in str(info.value)


def test_questions_as_jsonl(write):
    path = write("q.jsonl", '{"case_id": 1, "question": "a", "expected": "x"}\n\n{"case_id": "b", "question": "c", "expected": "y"}\n')
    questions, has_expected = read_questions(path)
    assert [(q.case_id, q.question, q.expected) for q in questions] == [("1", "a", "x"), ("b", "c", "y")]
    assert has_expected


def test_bad_arguments(write, tmp_path):
    with pytest.raises(RunError, match="--runs"):
        run(config(write, tmp_path, runs=0))
    with pytest.raises(RunError, match="--proposed"):
        run(config(write, tmp_path, proposed="python:fake_systems:does_not_exist"))


def test_a_repeated_question_is_reported_not_removed(write, tmp_path):
    import io
    log = io.StringIO()
    cfg = config(write, tmp_path, questions=QUESTIONS + "4,Question  ONE!\n", runs=1)
    outcome = run(cfg, log=log)
    assert outcome.calls_ok == 8 and len(results_rows(cfg.out_dir)) == 4
    assert "1 question(s) appear under more than one case_id (1 = 4)" in log.getvalue()


def test_long_passages_are_cut_but_stay_distinguishable(write, tmp_path):
    cfg = config(write, tmp_path, current="python:fake_systems:long_passages",
                 proposed="python:fake_systems:long_passages", runs=1)
    run(cfg)
    first, second, third = results_rows(cfg.out_dir)[0]["baseline_context"].split(" | ")
    assert len(first) <= 120 and len(second) <= 120
    # the two passages are the same for their first 200 characters; the short hash keeps them apart
    assert first != second and first[:100] == second[:100] and "… #" in first
    assert third == "part a ¦ part b"      # a "|" inside a passage would otherwise split it in two


def test_a_scorer_that_raises_stops_the_run_and_names_the_case(write, tmp_path):
    cfg = config(write, tmp_path, questions="case_id,question,expected\n1,question one,one\n",
                 scorer="fake_systems:scorer_raises")
    with pytest.raises(RunError, match=r"The scorer failed on case 1 \(current, run 1\): ZeroDivisionError: no judge here"):
        run(cfg)
    # the answers were recorded before scoring, so the calls are not paid for twice
    assert len(raw_records(cfg.out_dir)) == 4


def test_answers_without_their_manifest_are_not_built_on(write, tmp_path):
    cfg = config(write, tmp_path)
    run(cfg)
    os.remove(os.path.join(cfg.out_dir, "run_manifest.json"))
    with pytest.raises(RunError, match="exists without run_manifest.json, so its inputs cannot be checked"):
        run(cfg)


def test_a_null_character_in_an_answer_does_not_make_a_file_that_cannot_be_read_back(write, tmp_path):
    cfg = config(write, tmp_path, current="python:fake_systems:with_null", proposed="python:fake_systems:with_null")
    run(cfg)
    assert "\\u0000" in open(os.path.join(cfg.out_dir, "raw_outputs.jsonl"), encoding="utf-8").read()   # kept as given
    cases, _ = read_results(os.path.join(cfg.out_dir, "results.csv"))
    assert cases[0].baseline[0].answer == "an answer with a null character" and cases[0].baseline_context == ["doc 1"]


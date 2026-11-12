"""`ridi-check run` from the command line: exit status when calls fail or the run is interrupted."""

import os
import subprocess
import sys

import pytest

import fake_systems
from ridi_check import __version__
from ridi_check.cli import main


@pytest.fixture(autouse=True)
def _reset():
    fake_systems.reset()
    yield
    fake_systems.reset()


@pytest.fixture
def run_args(write, tmp_path):
    questions = write("questions.csv", "case_id,question,expected\n1,question one,old answer to question one\n"
                      "2,question two,old answer to question two\n3,question three,old answer to question three\n")
    return ["run", "--questions", questions, "--current", "python:fake_systems:current",
            "--proposed", "python:fake_systems:proposed", "--out", str(tmp_path / "out"),
            "--retries", "0", "--retry-wait", "0", "--concurrency", "1"]


def test_failed_calls_give_exit_1_and_the_gate_counts_the_case_as_not_compared(run_args, tmp_path, capsys):
    fake_systems.fail_questions.add("question two")
    assert main(run_args) == 1
    printed = capsys.readouterr()
    assert "8 succeeded, 4 failed" in printed.out
    assert "4 call(s) failed and are recorded as failed" in printed.err

    results = str(tmp_path / "out" / "results.csv")
    assert main(["gate", results]) == 1                       # case 3 regressed, case 2 could not be compared
    out = capsys.readouterr().out
    assert "incomplete (a first-run call failed)\tcase 2" in out
    assert "cases not compared: 1 (limit 0) - over the limit" in out
    assert main(["gate", results, "--max-incomplete", "1", "--max-stable-regressions", "1"]) == 0
    assert "cases not compared: 1 (limit 1)\n" in capsys.readouterr().out

    # the same command again retries only the failed calls
    fake_systems.reset()
    assert main(run_args) == 0
    assert "8 already recorded, 4 succeeded, 0 failed" in capsys.readouterr().out
    assert len(fake_systems.calls) == 4


def test_an_interrupted_run_gives_exit_130_and_resumes(run_args, capsys):
    fake_systems.interrupt_after = 5
    assert main(run_args) == 130
    assert "Interrupted: 5 of 12 calls are recorded" in capsys.readouterr().err
    fake_systems.reset()
    assert main(run_args) == 0
    assert "12 planned, 5 already recorded, 7 succeeded, 0 failed" in capsys.readouterr().out


def test_the_package_runs_as_a_module():
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    done = subprocess.run([sys.executable, "-m", "ridi_check", "--version"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env, timeout=60)
    assert done.returncode == 0 and __version__ in done.stdout


@pytest.mark.parametrize("arguments, message", [
    (["report", "results.csv", "--similarity", "2"], "must be above 0 and at most 1 (1 means exact match)"),
    (["report", "results.csv", "--similarity", "high"], "expected a number, for example 0.9"),
    (["gate", "results.csv", "--max-stable-regressions", "-1"], "cannot be negative"),
    (["gate", "results.csv", "--max-incomplete", "a few"], "expected a whole number"),
])
def test_a_mistyped_option_is_explained_before_anything_is_read(arguments, message, capsys):
    with pytest.raises(SystemExit) as stopped:
        main(arguments)
    assert stopped.value.code == 2 and message in capsys.readouterr().err


def test_a_damaged_manifest_is_not_built_on(run_args, tmp_path, capsys):
    assert main(run_args) == 0
    (tmp_path / "out" / "run_manifest.json").write_text('{"cut short', encoding="utf-8")
    capsys.readouterr()
    assert main(run_args) == 2
    assert "run_manifest.json exists but cannot be read" in capsys.readouterr().err
    assert len(fake_systems.calls) == 12          # nothing was called again


def test_verify_agrees_with_an_untouched_run_and_finds_a_cell_edited_by_hand(run_args, tmp_path, capsys):
    """results.csv can be edited; raw_outputs.jsonl is the record. `verify` builds the table again and compares."""
    assert main(run_args) == 0
    out_dir = str(tmp_path / "out")
    capsys.readouterr()
    assert main(["verify", out_dir]) == 0
    assert "verify: results.csv agrees with raw_outputs.jsonl (3 cases, " in capsys.readouterr().out

    results = tmp_path / "out" / "results.csv"
    original = results.read_text(encoding="utf-8")
    # a score turned from wrong to right by hand
    lines = original.splitlines()
    assert lines[3].startswith("3,question three,") and lines[3].endswith(",1,1,0,0,doc 1 | doc 2,doc 2 | doc 3")
    results.write_text("\n".join(lines[:3] + [lines[3].replace(",1,1,0,0,", ",1,1,1,1,")]) + "\n", encoding="utf-8")
    assert main(["verify", out_dir]) == 1
    out = capsys.readouterr().out
    assert "case 3, updated_correct: the file has '1', the record gives '0'" in out and "verify: 2 difference(s)" in out
    assert main(["gate", str(results)]) == 0            # the edited table passes the gate; verify is what catches it
    capsys.readouterr()

    # an answer reworded by hand, and a case removed
    results.write_text(original.replace("new answer to question three", "old answer to question three", 1)
                       .replace("2,question two,", "9,question two,", 1), encoding="utf-8")
    assert main(["verify", out_dir]) == 1
    out = capsys.readouterr().out
    assert "case 3, updated_answer: the file has 'old answer to question three', the record gives 'new answer to question three'" in out
    assert "case 9: it is in results.csv and no call for it is on record" in out
    assert "case 2: calls for it are on record and it is not in results.csv" in out

    results.write_text(original, encoding="utf-8")
    assert main(["verify", out_dir]) == 0
    capsys.readouterr()


def test_verify_says_what_it_could_not_check(run_args, tmp_path, capsys):
    assert main(run_args) == 0
    os.remove(run_args[run_args.index("--questions") + 1])           # the questions file is gone
    capsys.readouterr()
    assert main(["verify", str(tmp_path / "out")]) == 0
    assert "questions and expected answers were taken from results.csv and are not themselves checked" in capsys.readouterr().err
    assert main(["verify", str(tmp_path / "nothing_here")]) == 2
    assert "`verify` needs the folder that `run` wrote" in capsys.readouterr().err


def test_verify_scores_again_with_the_runs_own_scorer_and_says_when_the_version_differs(run_args, tmp_path, capsys):
    import json
    assert main(run_args + ["--scorer", "fake_systems:scorer_contains"]) == 0
    out_dir = tmp_path / "out"
    capsys.readouterr()
    assert main(["verify", str(out_dir)]) == 0                      # scored again with the same function
    manifest = json.loads((out_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["scorer"] == "fake_systems:scorer_contains"
    manifest["scorer"], manifest["tool_version"] = "no_such_module:function", "0.1.0"
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    capsys.readouterr()
    assert main(["verify", str(out_dir)]) == 0                      # the answers still agree; the scores are not checked
    err = capsys.readouterr().err
    assert "could not be loaded" in err and "so the scores are not checked" in err
    assert "This run was written by ridi-check 0.1.0" in err



def test_a_fingerprint_kept_elsewhere_shows_a_record_that_was_changed_with_its_table(run_args, tmp_path, capsys):
    """`verify` compares the table with the record. When both are edited together they still agree; only a
    fingerprint of the record, kept somewhere else when the run ended, can show that."""
    import re
    assert main(run_args) == 0
    printed = re.search(r"sha256 ([0-9a-f]{64})  raw_outputs\.jsonl", capsys.readouterr().out)
    assert printed, "run prints the fingerprint of the record"
    fingerprint, out_dir = printed.group(1), tmp_path / "out"
    assert main(["verify", str(out_dir), "--raw-sha256", fingerprint]) == 0
    assert f"sha256 {fingerprint}  raw_outputs.jsonl" in capsys.readouterr().out
    assert main(["verify", str(out_dir), "--raw-sha256", fingerprint[:16]]) == 0          # its first sixteen characters are enough
    assert main(["verify", str(out_dir), "--raw-sha256", "abc"]) == 1                    # and three are not
    capsys.readouterr()

    # the same edit made to the record and to the table
    for name in ("raw_outputs.jsonl", "results.csv"):
        path = out_dir / name
        path.write_text(path.read_text(encoding="utf-8").replace("new answer to question three", "old answer to question three"), encoding="utf-8")
    (out_dir / "results.csv").write_text((out_dir / "results.csv").read_text(encoding="utf-8").replace(",1,1,0,0,", ",1,1,1,1,"), encoding="utf-8")
    assert main(["verify", str(out_dir)]) == 0                                            # they agree with each other
    capsys.readouterr()
    assert main(["verify", str(out_dir), "--raw-sha256", fingerprint]) == 1               # and not with what was kept
    assert "raw_outputs.jsonl does not have the fingerprint given" in capsys.readouterr().out

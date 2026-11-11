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

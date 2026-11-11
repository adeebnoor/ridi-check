"""First-use paths: demo, init, the settings file, --limit, and failing fast on a broken connection."""

import csv
import io
import json
import os
import sys
from importlib import resources

import pytest

import fake_systems
from ridi_check.cli import main
from ridi_check.runner import RunConfig, run

from conftest import ROOT


@pytest.fixture(autouse=True)
def _clean_modules():
    """Each test imports its own copy of the template modules."""
    fake_systems.reset()
    for name in ("toy_assistant", "my_assistant"):
        sys.modules.pop(name, None)
    yield
    for name in ("toy_assistant", "my_assistant"):
        sys.modules.pop(name, None)
    fake_systems.reset()


def test_demo_creates_a_working_example_from_the_installed_package(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["demo"]) == 0
    demo = tmp_path / "ridi-demo"
    for name in ("questions.csv", "toy_assistant.py", "ridi-check.json", "ridi-out/results.csv",
                 "ridi-out/report.html", "ridi-out/summary.json", "ridi-out/run_manifest.json"):
        assert (demo / name).stat().st_size > 0, name
    summary = json.loads((demo / "ridi-out" / "summary.json").read_text(encoding="utf-8"))
    assert summary["cases"] == 30 and summary["states"]["stable_regression"] == 4
    assert summary["labels"]["proposed"] == "handbook split into 13-word windows"
    out = capsys.readouterr().out
    assert "Open the report:" in out and "ridi-check init" in out

    # running it again calls nothing and says why
    monkeypatch.chdir(tmp_path)
    assert main(["demo"]) == 0
    assert "Nothing to call" in capsys.readouterr().err


def test_packaged_demo_files_match_the_examples_folder():
    for name in ("toy_assistant.py", "questions.csv"):
        packaged = resources.files("ridi_check").joinpath("demo", name).read_bytes()
        with open(os.path.join(ROOT, "examples", name), "rb") as f:
            assert f.read() == packaged, f"examples/{name} and src/ridi_check/demo/{name} differ"


def test_init_writes_a_starter_folder_and_never_overwrites(tmp_path, capsys):
    target = tmp_path / "check"
    assert main(["init", str(target)]) == 0
    assert sorted(p.name for p in target.iterdir()) == ["ASK_YOUR_AI.md", "my_assistant.py", "questions.csv",
                                                        "ridi-check.json"]
    assert "ridi-check run --limit 5" in capsys.readouterr().out
    (target / "questions.csv").write_text("case_id,question\nmine,my own question\n", encoding="utf-8")
    assert main(["init", str(target)]) == 0
    assert "my own question" in (target / "questions.csv").read_text(encoding="utf-8")
    assert "left as they are" in capsys.readouterr().out
    json.loads((target / "ridi-check.json").read_text(encoding="utf-8"))


def test_running_the_untouched_starter_stops_early_and_says_what_to_do(tmp_path, monkeypatch, capsys):
    target = tmp_path / "check"
    main(["init", str(target)])
    monkeypatch.chdir(target)
    capsys.readouterr()
    assert main(["run", "--retry-wait", "0"]) == 2
    err = capsys.readouterr().err
    assert "Stopped" in err and "make ask() call your assistant" in err
    assert not (target / "ridi-out" / "results.csv").exists()
    manifest = json.loads((target / "ridi-out" / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["invocations"][-1]["status"].startswith("stopped")
    records = [json.loads(line) for line in (target / "ridi-out" / "raw_outputs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert records and all(r["status"] == "failed" for r in records)       # every attempt is on record


def test_a_filled_in_starter_runs_from_the_settings_file(tmp_path, monkeypatch, capsys):
    target = tmp_path / "check"
    main(["init", str(target)])
    source = (target / "my_assistant.py").read_text(encoding="utf-8")
    start = source.index("    raise NotImplementedError(")
    end = source.index("def answer_current")
    (target / "my_assistant.py").write_text(
        source[:start] + '    return ("v2 " if version == "proposed" and "unique" in question else "") + "ok", ["doc"]\n\n\n'
        + source[end:], encoding="utf-8")
    monkeypatch.chdir(tmp_path)                      # run from elsewhere: paths follow the settings file
    assert main(["run", "--config", str(target / "ridi-check.json"), "--limit", "2"]) == 0
    out = capsys.readouterr().out
    assert "first try on 2 question(s)" in out and "Open the report:" in out
    with open(target / "ridi-out" / "results.csv", encoding="utf-8", newline="") as f:
        assert [r["case_id"] for r in csv.DictReader(f)] == ["q1", "q2"]

    monkeypatch.chdir(target)
    assert main(["run", "--runs", "3"]) == 0         # the command line wins over the file; earlier answers are reused
    out = capsys.readouterr().out
    assert "18 planned, 8 already recorded, 10 succeeded" in out
    summary = json.loads((target / "ridi-out" / "summary.json").read_text(encoding="utf-8"))
    assert summary["cases"] == 3 and summary["case_ids"]["stable_change"] == ["q3"]
    assert summary["runs_per_version"] == {"current": 3, "proposed": 3}
    assert summary["labels"]["current"] == "what is live today"


def test_init_by_hand_gives_a_results_template_that_reports(tmp_path, capsys):
    assert main(["init", str(tmp_path), "--by-hand"]) == 0
    assert [p.name for p in tmp_path.iterdir()] == ["results_template.csv"]
    assert main(["report", str(tmp_path / "results_template.csv")]) == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["states"] == {"stable_change": 1, "change_unconfirmed": 0, "unstable": 1, "same": 1, "incomplete": 0}


@pytest.mark.parametrize("settings, fragment", [
    ('{"questions": "q.csv", "colour": "red"}', "unknown setting 'colour'"),
    ('{"runs": "two"}', "'runs' must be a number"),
    ('{"report": "yes"}', "'report' must be bool"),
    ("[1, 2]", "must hold one JSON object"),
    ("{not json", "is not valid JSON"),
    ('{"questions": "q.csv"}', "Missing --current, --proposed, --out"),
])
def test_bad_settings_files_are_explained(tmp_path, monkeypatch, capsys, settings, fragment):
    (tmp_path / "ridi-check.json").write_text(settings, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["run"]) == 2
    assert fragment in capsys.readouterr().err


def test_run_without_settings_says_how_to_start(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["run"]) == 2
    assert "ridi-check init" in capsys.readouterr().err


def test_changed_code_between_invocations_is_pointed_out(tmp_path, write):
    module = tmp_path / "bot_under_test.py"
    module.write_text("def a(q):\n    return 'one'\n", encoding="utf-8")
    sys.path.insert(0, str(tmp_path))
    try:
        cfg = RunConfig(questions=write("q.csv", "case_id,question\n1,x\n"), current="python:bot_under_test:a",
                        proposed="python:bot_under_test:a", out_dir=str(tmp_path / "out"), runs=1)
        log = io.StringIO()
        run(cfg, log=log)
        assert "has changed" not in log.getvalue()
        module.write_text("def a(q):\n    return 'two'\n", encoding="utf-8")
        log = io.StringIO()
        outcome = run(cfg, log=log)
        assert outcome.calls_skipped == 2                      # nothing is called again...
        assert "code behind --current has changed" in log.getvalue() and "Nothing to call" in log.getvalue()
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("bot_under_test", None)


def test_cancelled_changes_are_counted(tmp_path):
    from ridi_check.report import write_report
    from conftest import FIXTURE
    summary, _, _, _ = write_report(FIXTURE, str(tmp_path))
    first = summary["first_run"]
    assert (first["regressions"], first["improvements"]) == (4, 3)
    assert first["changes_visible_in_mean_accuracy"] == 1 and first["changes_cancelled_in_mean_accuracy"] == 6
    assert (first["changes_visible_in_mean_accuracy"] + first["changes_cancelled_in_mean_accuracy"]
            == first["change_between_versions"]["count"])

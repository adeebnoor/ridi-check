"""The end-to-end example: one command, no network, no API key."""

import csv
import json
import os
import socket

from ridi_check.cli import main

from conftest import ROOT


def test_one_command_produces_results_and_report(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(ROOT)
    for name in list(os.environ):
        if name.upper().endswith("_API_KEY"):
            monkeypatch.delenv(name)

    def no_network(*args, **kwargs):
        raise AssertionError("the example must not open a network connection")

    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket.socket, "connect", no_network)

    out = tmp_path / "out"
    status = main([
        "run", "--questions", "examples/questions.csv",
        "--current", "python:examples.toy_assistant:answer_current",
        "--proposed", "python:examples.toy_assistant:answer_proposed",
        "--scorer", "examples.toy_assistant:contains_expected",
        "--out", str(out), "--report",
    ])
    assert status == 0
    for name in ("raw_outputs.jsonl", "run_manifest.json", "results.csv", "summary.json", "review_cases.csv",
                 "report.html"):
        assert (out / name).stat().st_size > 0, name

    with open(out / "results.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 30 and rows[0]["baseline_context"] and rows[0]["updated_context"]

    with open(out / "summary.json", encoding="utf-8") as f:
        summary = json.load(f)
    states = summary["states"]
    assert summary["mode"] == "key" and sum(states.values()) == 30
    # the toy is built to show every kind of case; its randomness is seeded
    assert states["stable_regression"] >= 1 and states["stable_improvement"] >= 1
    assert states["unstable"] >= 1 and states["wrong_both"] >= 1 and states["correct_both"] >= 1
    assert summary["first_run"]["rerun_variation_current"]["count"] == 0      # the current version is deterministic
    assert summary["first_run"]["rerun_variation_proposed"]["count"] >= 1     # the proposed one is not
    assert "stable_regression" in capsys.readouterr().out

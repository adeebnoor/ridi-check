"""examples/adapters/agent_adapter.py: a stand-in agent with tools and memory, wrapped as one function."""

import csv
import importlib
import json
import os
import socket
import sys

import pytest

from ridi_check.cli import main

from conftest import ROOT

ADAPTERS = os.path.join(ROOT, "examples", "adapters")


@pytest.fixture
def agent(monkeypatch):
    monkeypatch.syspath_prepend(ADAPTERS)
    sys.modules.pop("agent_adapter", None)
    yield importlib.import_module("agent_adapter")
    sys.modules.pop("agent_adapter", None)


def test_tool_calls_come_back_as_context_in_order(agent):
    reply = agent.answer_current("What is the fine for a book that is 9 days late?")
    assert reply == {"answer": "180 pence", "context": ["1. lookup(book_fine_pence)", "2. calculate(20 * 9)"]}
    assert agent.answer_proposed("What is the fine for a book that is 9 days late?") == {
        "answer": "160 pence", "context": ["1. lookup(book_fine_pence)"]}       # no calculator, and a wrong sum


def test_a_conversation_is_one_case_and_every_call_starts_a_new_session(agent):
    conversation = json.dumps(["I have a child card.", "What is the fine for a book that is 4 days late?"])
    assert agent.answer_current(conversation)["answer"] == "No fine"            # it remembered the first turn
    assert agent.answer_proposed(conversation)["answer"] == "80 pence"          # the update reads the last turn only
    # nothing leaks from that conversation into the next call
    assert agent.answer_current("What is the fine for a book that is 4 days late?")["answer"] == "80 pence"


def test_the_check_shows_what_the_agent_update_changed(tmp_path, monkeypatch, capsys, agent):
    def no_network(*args, **kwargs):
        raise AssertionError("the agent example must not open a network connection")

    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket.socket, "connect", no_network)
    out = tmp_path / "out"
    assert main(["run", "--questions", os.path.join(ADAPTERS, "agent_questions.csv"), "--out", str(out), "--report",
                 "--current", "python:agent_adapter:answer_current",
                 "--proposed", "python:agent_adapter:answer_proposed"]) == 0
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["case_ids"]["stable_regression"] == ["a06", "a09", "a10", "a11"]
    assert summary["case_ids"]["stable_improvement"] == ["a07"]
    assert summary["case_ids"]["unstable"] == ["a03"]                           # the seeded from-memory answer
    assert summary["states"]["wrong_both"] == 1 and summary["states"]["correct_both"] == 5
    assert summary["wrong_both_answer_changed"]["stable"] == ["a08"]
    assert summary["first_run"]["rerun_variation_current"]["count"] == 0

    with open(out / "review_cases.csv", encoding="utf-8", newline="") as f:
        review = {row["case_id"]: row for row in csv.DictReader(f)}
    # the tool calls that only one version made are what the report lists under each changed case
    assert review["a06"]["passages_only_current"] == "2. calculate(20 * 9)" and review["a06"]["passages_only_proposed"] == ""
    assert review["a11"]["passages_only_current"] == "1. lookup(film_loan_days)"
    assert review["a11"]["passages_only_proposed"] == "1. lookup(book_loan_days)"
    assert review["a10"]["updated_answer"] == "I need to know how many days late it is"   # the lost first turn
    assert main(["gate", str(out / "results.csv")]) == 1
    assert "stable_regression\tcase a09" in capsys.readouterr().out

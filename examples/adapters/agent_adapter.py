"""Wrapping an agent that uses tools and keeps state between turns.

ridi-check compares answers, so an agent is wrapped as one function: the question (or a whole
scripted conversation) goes in, the final answer comes out, and the tool calls it made are
returned as `context`. The report then shows, for every changed case, the tool calls that only
one version made.

Three things make this work for a real agent:

1. A new session for every call. Runs must not share memory, or a re-run is not a re-run.
2. A conversation is one case. Put the turns in the `question` cell as a JSON list,
   for example ["I have a child card.", "What is the fine for a late book?"].
3. Number the tool calls ("1. lookup(...)"), so that a changed order shows as a difference.

The agent below is a stand-in with fixed rules and made-up library facts. It needs no network
and no key; everything about it is synthetic. Its two versions differ the way real updates do:

  current   remembers earlier turns; has a defect in the film fine (it looks up the book rate)
  proposed  fixes that defect; reads only the last turn; multiplies in its head instead of
            calling the calculator, which goes wrong for larger numbers; and sometimes answers
            one question from memory instead of looking it up (seeded, so the example repeats)

    ridi-check run --questions agent_questions.csv --out ridi-out --report \\
        --current  python:agent_adapter:answer_current \\
        --proposed python:agent_adapter:answer_proposed

ridi-check has not been tried on a production agent. This file shows the pattern, not a result.
"""

from __future__ import annotations

import json
import random
import re
import threading
from collections import Counter

SEED = 3
FACTS = {
    "book_loan_days": 21, "film_loan_days": 7,
    "book_fine_pence": 20, "film_fine_pence": 100,
    "max_items": 12, "room_hours": 2,
}


class Session:
    """One conversation with the agent: its memory and the tool calls it made."""

    def __init__(self, version: str, nth_call: int = 0):
        self.version = version
        self.nth_call = nth_call
        self.memory: dict = {}
        self.calls: list[str] = []

    # ----- tools -----
    def lookup(self, key: str) -> int:
        self.calls.append(f"{len(self.calls) + 1}. lookup({key})")
        return FACTS[key]

    def calculate(self, a: int, b: int) -> int:
        self.calls.append(f"{len(self.calls) + 1}. calculate({a} * {b})")
        return a * b

    # ----- the agent -----
    def turn(self, text: str) -> str:
        text = text.lower()
        if self.version == "proposed":
            self.memory = {}                       # the update reads only the last turn
        if "child card" in text:
            self.memory["child_card"] = True
        if "film" in text:
            self.memory["item"] = "film"
        elif "book" in text and "book a" not in text:
            self.memory["item"] = "book"
        late = re.search(r"(\d+) days late", text)
        if late:
            self.memory["days_late"] = int(late.group(1))
        item = self.memory.get("item", "book")

        if "fine" in text or "owe" in text:
            if self.memory.get("child_card"):
                return "No fine"
            if "days_late" not in self.memory:
                return "I need to know how many days late it is"
            days = self.memory["days_late"]
            if self.version == "current":
                rate = self.lookup("book_fine_pence")           # the defect: the book rate, whatever the item
                return f"{self.calculate(rate, days)} pence"
            rate = self.lookup(f"{item}_fine_pence")
            in_its_head = rate * days if days < 7 else rate * days - rate   # no calculator: wrong for larger numbers
            return f"{in_its_head} pence"
        if "how many days" in text or "how long is" in text:
            return f"{self.lookup(f'{item}_loan_days')} days"
        if "how many items" in text:
            from_memory = self.version == "proposed" and random.Random(f"{SEED}|{self.nth_call}").random() < 0.5
            return "10 items" if from_memory else f"{self.lookup('max_items')} items"
        if "study room" in text:
            return f"{self.lookup('room_hours')} hours"
        return "Noted"


_calls: Counter = Counter()
_lock = threading.Lock()


def run_agent(question: str, version: str) -> dict:
    """One call: a fresh session, every turn of the case, the final answer and the tool calls."""
    turns = json.loads(question) if question.lstrip().startswith("[") else [question]
    with _lock:
        nth = _calls[(version, question)]
        _calls[(version, question)] += 1
    session = Session(version, nth)                 # never reuse a session between calls
    answer = ""
    for turn in turns:
        answer = session.turn(str(turn))
    return {"answer": answer, "context": session.calls}


def answer_current(question: str) -> dict:
    return run_agent(question, "current")


def answer_proposed(question: str) -> dict:
    return run_agent(question, "proposed")

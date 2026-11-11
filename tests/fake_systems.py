"""Stand-in assistants for the runner tests. Imported by `python:fake_systems:<name>`."""

import threading

calls = []                 # every (name, question) seen, in order
_lock = threading.Lock()
interrupt_after = None     # raise KeyboardInterrupt once this many calls were made
fail_questions = set()     # questions that always raise
fail_first_attempts = {}   # question -> number of attempts that fail before one succeeds
_attempts = {}


def reset():
    global interrupt_after
    with _lock:
        calls.clear()
        _attempts.clear()
        fail_questions.clear()
        fail_first_attempts.clear()
        interrupt_after = None


def _note(name, question):
    with _lock:
        if interrupt_after is not None and len(calls) >= interrupt_after:
            raise KeyboardInterrupt
        calls.append((name, question))
        _attempts[(name, question)] = _attempts.get((name, question), 0) + 1
        attempt = _attempts[(name, question)]
    if question in fail_questions:
        raise RuntimeError(f"backend down for {question!r}")
    if attempt <= fail_first_attempts.get(question, 0):
        raise TimeoutError("slow backend")


def current(question):
    _note("current", question)
    return {"answer": f"old answer to {question}", "context": ["doc 1", "doc 2"]}


def proposed(question):
    _note("proposed", question)
    changed = "three" in question
    return {"answer": f"{'new' if changed else 'old'} answer to {question}", "context": ["doc 2", "doc 3"]}


def plain_string(question):
    return "just text"


def empty(question):
    return {"answer": "   ", "context": None}


def wrong_shape(question):
    return {"text": "no answer key here"}


def scorer_contains(answer, expected):
    return expected.lower() in answer.lower()

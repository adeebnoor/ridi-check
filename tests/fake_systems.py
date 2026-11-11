"""Stand-in assistants for the runner tests. Imported by `python:fake_systems:<name>`."""

import threading
import time

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
        other_call_started.clear()


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


def long_passages(question):
    """Two passages that share their first 200 characters, and one that holds the column separator."""
    shared = "The handbook says in its section on returns that " * 4
    return {"answer": "an answer", "context": [shared + "books come back in two weeks.",
                                               shared + "films come back in one week.", "part a | part b"]}


class Busy(Exception):
    """What a hand-written adapter can raise: the runner reads these two attributes from any exception."""

    def __init__(self, message, retry_after=None, retryable=True):
        super().__init__(message)
        self.retry_after, self.retryable = retry_after, retryable


def asks_to_wait(question):
    _note("asks_to_wait", question)
    if _attempts[("asks_to_wait", question)] == 1:
        raise Busy("slow down", retry_after=0.3)
    return "an answer"


other_call_started = threading.Event()


def asks_for_a_long_wait(question):
    other_call_started.wait(10)     # so that the other call is under way before every call is told to wait
    raise Busy("slow down", retry_after=60)


def interrupts_soon(question):
    other_call_started.set()
    time.sleep(0.3)
    raise KeyboardInterrupt


def will_never_work(question):
    _note("will_never_work", question)
    raise Busy("this account is closed", retryable=False)


def repeats_its_key(question):
    import os
    raise RuntimeError(f"the service refused the key {os.environ['TOY_API_KEY']}")


def with_null(question):
    return {"answer": "an answer\x00 with a null character", "context": ["doc\x00 1"]}


def scorer_raises(answer, expected):
    raise ZeroDivisionError("no judge here")


def plain_string(question):
    return "just text"


def empty(question):
    return {"answer": "   ", "context": None}


def wrong_shape(question):
    return {"text": "no answer key here"}


def scorer_contains(answer, expected):
    return expected.lower() in answer.lower()

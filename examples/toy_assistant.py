"""A toy assistant in two versions, for trying ridi-check with no network and no API key.

It answers questions about a made-up library handbook by finding the best-matching sentence.

  answer_current   splits the handbook by section and reads the best section.
  answer_proposed  splits it into fixed windows of words, which can cut a sentence in half,
                   and reads the three best windows. Its retriever breaks ties at random,
                   so the same question can get a different answer on another run.

The randomness is seeded: the n-th call for a question always behaves the same way in a
fresh process, so the example gives the same report every time.

Both functions follow the adapter interface:
    answer(question: str) -> {"answer": str, "context": list[str] | None}
"""

from __future__ import annotations

import random
import re
import threading
from collections import Counter

SEED = 7
WINDOW_WORDS = 13

HANDBOOK = {
    "membership": (
        "Anyone who lives in the Harbour district can join the library free of charge. "
        "A membership card is issued at the front desk on the same day. "
        "Members under sixteen need a signature from a parent or guardian. "
        "A lost card is replaced for a fee of four pounds. "
        "Membership must be renewed every three years."
    ),
    "loans": (
        "Members may borrow up to twelve items at a time. "
        "Books are lent for twenty one days. "
        "Films and music are lent for seven days. "
        "A loan can be renewed twice unless another member has reserved the item. "
        "Reference books cannot be borrowed and must stay in the reading room."
    ),
    "fines": (
        "An overdue book costs twenty pence a day. "
        "An overdue film costs one pound a day. "
        "No fine is charged on items borrowed with a child card. "
        "Borrowing is suspended when unpaid fines reach fifteen pounds. "
        "Fines can be paid at the front desk or online."
    ),
    "rooms": (
        "The library has three study rooms on the second floor. "
        "A study room can be booked for up to two hours a day. "
        "Bookings open seven days in advance. "
        "A room is released if the group does not arrive within fifteen minutes of the start time. "
        "Food is not allowed in the study rooms but covered drinks are."
    ),
    "printing": (
        "Black and white printing costs ten pence a page. "
        "Colour printing costs forty pence a page. "
        "Scanning to email is free. "
        "Print jobs are deleted from the queue after twenty four hours. "
        "The printers accept payment by card only."
    ),
    "hours": (
        "The library opens at nine in the morning from Monday to Saturday. "
        "It closes at eight in the evening on weekdays and at five on Saturday. "
        "The library is closed on Sunday and on public holidays. "
        "The book drop at the side entrance is open at all hours."
    ),
    "digital": (
        "Members can borrow up to six ebooks at a time. "
        "An ebook is returned automatically after fourteen days. "
        "The newspaper archive can be read only on the computers inside the library. "
        "Free wifi is available to everyone and needs no password."
    ),
    "events": (
        "Story time for children is held every Wednesday at ten. "
        "The evening book club meets on the first Thursday of the month. "
        "Events are free but places at the writing workshop must be booked. "
        "The workshop takes at most twenty participants."
    ),
}

STOPWORDS = set(
    "a an and are at be by can do does for from how i in is it many may much of on or the to "
    "what when where which who with".split()
)


def _words(text: str) -> set[str]:
    out = set()
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if word in STOPWORDS:
            continue
        out.add(word[:-1] if len(word) > 3 and word.endswith("s") else word)
    return out


def _sections() -> list[tuple[str, str]]:
    return [(name, text) for name, text in HANDBOOK.items()]


def _windows() -> list[tuple[str, str]]:
    out = []
    for name, text in HANDBOOK.items():
        words = text.split()
        for start in range(0, len(words), WINDOW_WORDS):
            out.append((f"{name}[{start // WINDOW_WORDS + 1}]", " ".join(words[start:start + WINDOW_WORDS])))
    return out


def _retrieve(question: str, chunks: list[tuple[str, str]], k: int, rng: random.Random | None) -> list[tuple[str, str]]:
    asked = _words(question)
    scored = []
    for position, (name, text) in enumerate(chunks):
        score = len(asked & _words(text))
        tie_break = rng.random() if rng else -position / 1000
        scored.append((score, tie_break, name, text))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [(name, text) for _, _, name, text in scored[:k]]


def _best_passage(question: str, chunks: list[tuple[str, str]]) -> str:
    asked = _words(question)
    best, best_score = "", -1
    for _, text in chunks:
        for piece in re.split(r"(?<=[.!?])\s+", text):
            score = len(asked & _words(piece))
            if piece and score > best_score:
                best, best_score = piece, score
    return best


def answer_current(question: str) -> dict:
    chunks = _retrieve(question, _sections(), 1, None)
    return {"answer": _best_passage(question, chunks), "context": [name for name, _ in chunks]}


_calls: Counter = Counter()
_lock = threading.Lock()


def answer_proposed(question: str) -> dict:
    with _lock:
        nth = _calls[question]
        _calls[question] += 1
    rng = random.Random(f"{SEED}|{question}|{nth}")
    chunks = _retrieve(question, _windows(), 3, rng)
    return {"answer": _best_passage(question, chunks), "context": [name for name, _ in chunks]}


def contains_expected(answer: str, expected: str) -> bool:
    """Scorer for the example: the answer is correct when it contains the expected phrase."""
    squash = lambda text: " ".join(re.findall(r"[a-z0-9]+", text.lower()))  # noqa: E731
    return squash(expected) in squash(answer)

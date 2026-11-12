"""Case states and first-run rates. Same rules as the browser prototype.

Per case, with the runs of each version as a list:
1. any run of a version differs from that version's first run -> unstable
2. else the first runs of the two versions are equal -> correct_both / wrong_both / same
3. else stable_regression / stable_improvement / stable_change, or the *_unconfirmed label
   when either version has a single run. "Stable" needs at least two runs of both versions.

Three things are added to the prototype's rules, none of which changes its states or counts:
- `incomplete`, for a case whose first run of a version failed in `ridi-check run`. It is not
  compared and is left out of every rate.
- Under a word-overlap threshold, two answers are never counted as the same when they differ in a
  negation word, in their numbers (the digit runs in order, and each number with its unit), by one word
  put in the place of another, or in the order of the same words.
- Normalisation keeps the signs that carry meaning (< > = + - % / and other mathematical symbols), where
  the prototype turned every one of them into a space. With the default (exact match) this has no effect.
- In answer-key mode, a case that is wrong in both versions, or correct in both, is also checked for
  a changed answer (`answer_change`). Its state stays as it is; correctness counting alone does not see it.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable

from .contract import KEY, Case, Run

STABLE_REGRESSION = "stable_regression"
STABLE_IMPROVEMENT = "stable_improvement"
STABLE_CHANGE = "stable_change"
REGRESSION_UNCONFIRMED = "regression_unconfirmed"
IMPROVEMENT_UNCONFIRMED = "improvement_unconfirmed"
CHANGE_UNCONFIRMED = "change_unconfirmed"
UNSTABLE = "unstable"
WRONG_BOTH = "wrong_both"
CORRECT_BOTH = "correct_both"
SAME = "same"
INCOMPLETE = "incomplete"

KEY_STATES = [
    STABLE_REGRESSION, STABLE_IMPROVEMENT, REGRESSION_UNCONFIRMED, IMPROVEMENT_UNCONFIRMED,
    UNSTABLE, WRONG_BOTH, CORRECT_BOTH, INCOMPLETE,
]
NOKEY_STATES = [STABLE_CHANGE, CHANGE_UNCONFIRMED, UNSTABLE, SAME, INCOMPLETE]
UNCHANGED_STATES = {CORRECT_BOTH, SAME}

# "t" is what n't leaves behind once punctuation is removed (isn't -> isn t).
NUMBERS = re.compile(r"\d+")

NEGATIONS = frozenset(
    "not no never neither nor without none cannot t "
    "لا غير لم لن بدون ليس ليست".split()
)


@lru_cache(maxsize=None)    # one entry for each character ever seen: a text is mostly the same few dozen
def _kind(ch: str) -> str:
    """'w' for a letter or a number, 'd' for a decimal digit (also a 'w'), 'm' for a mathematical symbol, '' otherwise."""
    category = unicodedata.category(ch) if ch else "Zs"
    return "d" if category == "Nd" else "w" if category[0] in "LN" else "m" if category == "Sm" else ""


def _in_word(ch: str) -> bool:
    return _kind(ch) in ("w", "d")


def _is_digit(ch: str) -> bool:
    return _kind(ch) == "d"


@lru_cache(maxsize=8192)   # the same answer is compared several times within a case
def normalise(text: str) -> str:
    """Lower-case, punctuation to spaces, whitespace collapsed, as the prototype's `norm` does, except that
    the signs that carry meaning are kept, each as a word of its own: "< 5 mg" is not "> 5 mg".

    Kept: every mathematical symbol (< > = + ± × ÷ ≤ ≥ ≠ ∈ ~ ...); a percent sign after a digit; "/" and
    "*" between two letters or digits (mg/kg); "!" before "="; and a hyphen that is a sign: before a
    digit when no letter or digit stands in front of it (-5), or right after a letter or digit when none
    follows (HIV-). A hyphen inside a word (x-ray, 5-10) and all other punctuation become a space.
    """
    s = str(text).lower()
    last = len(s) - 1
    out = []
    for i, ch in enumerate(s):
        kind = _kind(ch)
        if kind in ("w", "d"):
            out.append(ch)
            continue
        if not kind and ch not in "%\u066a/*-!":      # ordinary punctuation and spaces: nothing to look at
            out.append(" ")
            continue
        before, after = (s[i - 1] if i else ""), (s[i + 1] if i < last else "")
        keep = (
            kind == "m"
            or (ch in "%\u066a" and _is_digit(before))
            or (ch in "/*" and _in_word(before) and _in_word(after))
            or (ch == "-" and ((_is_digit(after) and not _in_word(before)) or (_in_word(before) and not _in_word(after))))
            or (ch == "!" and after == "=")
        )
        out.append(f" {'-' if ch == chr(0x2212) else ch} " if keep else " ")
    return " ".join("".join(out).split())


def _number_contexts(words: list[str]) -> list[str]:
    """Every word that holds a digit; a bare number is taken together with the word after it (its unit)."""
    out = []
    for i, word in enumerate(words):
        if NUMBERS.search(word):
            follows = words[i + 1] if NUMBERS.fullmatch(word) and i + 1 < len(words) else ""
            out.append(f"{word} {follows}")
    return out


def same_answer(a: str, b: str, threshold: float = 1.0) -> bool:
    """Equal after normalisation, or word overlap (Jaccard) at or above the threshold."""
    x, y = normalise(a), normalise(b)
    if x == y:
        return True
    if threshold >= 1:
        return False
    list_x, list_y = x.split(" "), y.split(" ")
    words_x, words_y = set(list_x), set(list_y)
    if bool(words_x & NEGATIONS) != bool(words_y & NEGATIONS):
        return False  # "is effective" and "is not effective" share most of their words
    if NUMBERS.findall(x) != NUMBERS.findall(y):
        return False  # so do "within 30 days" and "within 45 days", and "5mg" and "50mg"
    if _number_contexts(list_x) != _number_contexts(list_y):
        return False  # and "5 mg" and "5 g", "5mg" and "5g", "30 days" and "30 weeks"
    if len(list_x) == len(list_y):
        # The same number of words and not the same text: one word was put in the place of another ("major"
        # for "minor"), or the same words stand in another order ("A is allowed and B is not" against "B is
        # allowed and A is not"). Word overlap sees a bag of words and cannot tell whether that matters.
        return False
    shared = len(words_x & words_y)
    union = len(words_x) + len(words_y) - shared
    return union > 0 and shared / union >= threshold


def make_eq(mode: str, threshold: float = 1.0) -> Callable[[Run, Run], bool]:
    if mode == KEY:
        return lambda r, s: r.correct == s.correct
    return lambda r, s: same_answer(r.answer, s.answer, threshold)


def classify(case: Case, mode: str, threshold: float = 1.0) -> str:
    if case.incomplete:
        return INCOMPLETE
    eq = make_eq(mode, threshold)
    b, u = case.baseline, case.updated
    stable_b = all(eq(r, b[0]) for r in b)
    stable_u = all(eq(r, u[0]) for r in u)
    if not stable_b or not stable_u:
        return UNSTABLE
    key = mode == KEY
    if eq(b[0], u[0]):
        if not key:
            return SAME
        return CORRECT_BOTH if b[0].correct else WRONG_BOTH
    confirmed = len(b) > 1 and len(u) > 1
    if not key:
        return STABLE_CHANGE if confirmed else CHANGE_UNCONFIRMED
    if b[0].correct:
        return STABLE_REGRESSION if confirmed else REGRESSION_UNCONFIRMED
    return STABLE_IMPROVEMENT if confirmed else IMPROVEMENT_UNCONFIRMED


@dataclass
class Analysis:
    mode: str
    threshold: float
    items: list[tuple[Case, str]] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    # wrong_both or correct_both case id -> stable | unconfirmed | varied: the score is equal, the answer is not
    # ("varied": the answer changed from one run to the next of the same version)
    answer_change: dict[str, str] = field(default_factory=dict)
    n: int = 0              # rows in the file
    n_compared: int = 0     # rows with a first run of both versions
    changed: int = 0        # first runs differ
    rerun_b: int = 0        # run 1 and run 2 of the current version differ
    rerun_b_n: int = 0      # cases with at least two runs of the current version
    rerun_u: int = 0
    rerun_u_n: int = 0
    any_run_b: int = 0      # any run of the current version differs from its first run
    any_run_u: int = 0
    confirmable: int = 0    # cases with at least two runs of both versions
    max_runs_b: int = 0
    max_runs_u: int = 0
    correct_b: int = 0      # key mode, first run
    correct_u: int = 0
    by_similarity: list[str] = field(default_factory=list)  # no-key mode under a threshold: see analyse
    regressions: int = 0    # key mode, first run, 1 -> 0
    improvements: int = 0   # key mode, first run, 0 -> 1

    def ids(self, state: str) -> list[str]:
        return [case.case_id for case, s in self.items if s == state]


def analyse(cases: list[Case], mode: str, threshold: float = 1.0) -> Analysis:
    key = mode == KEY
    eq = make_eq(mode, threshold)
    a = Analysis(mode=mode, threshold=threshold, n=len(cases))
    a.counts = {state: 0 for state in (KEY_STATES if key else NOKEY_STATES)}
    for case in cases:
        state = classify(case, mode, threshold)
        a.counts[state] += 1
        a.items.append((case, state))
        if state == INCOMPLETE:
            continue
        b, u = case.baseline, case.updated
        a.n_compared += 1
        a.max_runs_b = max(a.max_runs_b, len(b))
        a.max_runs_u = max(a.max_runs_u, len(u))
        if not eq(b[0], u[0]):
            a.changed += 1
        if len(b) > 1:
            a.rerun_b_n += 1
            a.rerun_b += 0 if eq(b[0], b[1]) else 1
            a.any_run_b += 0 if all(eq(r, b[0]) for r in b) else 1
        if len(u) > 1:
            a.rerun_u_n += 1
            a.rerun_u += 0 if eq(u[0], u[1]) else 1
            a.any_run_u += 0 if all(eq(r, u[0]) for r in u) else 1
        if state in (WRONG_BOTH, CORRECT_BOTH) and all(r.answer for r in b + u):
            by_answer = classify(case, "nokey", threshold)
            if by_answer == STABLE_CHANGE:
                a.answer_change[case.case_id] = "stable"
            elif by_answer == CHANGE_UNCONFIRMED:
                a.answer_change[case.case_id] = "unconfirmed"
            elif by_answer == UNSTABLE:      # the score held on re-run and the answer did not
                a.answer_change[case.case_id] = "varied"
        if not key and threshold < 1 and classify(case, mode, 1.0) != state:
            a.by_similarity.append(case.case_id)    # exact match would label this case differently
        if len(b) > 1 and len(u) > 1:
            a.confirmable += 1
        if key:
            a.correct_b += b[0].correct
            a.correct_u += u[0].correct
            a.regressions += 1 if b[0].correct and not u[0].correct else 0
            a.improvements += 1 if not b[0].correct and u[0].correct else 0
    return a


def duplicate_questions(pairs: list[tuple[str, str]]) -> list[list[str]]:
    """Groups of case ids whose question text is the same after normalisation."""
    groups: dict[str, list[str]] = {}
    for case_id, question in pairs:
        text = normalise(question)
        if text:
            groups.setdefault(text, []).append(case_id)
    return [ids for ids in groups.values() if len(ids) > 1]


def duplicate_note(groups: list[list[str]]) -> str:
    shown = "; ".join(" = ".join(ids) for ids in groups[:5]) + (f"; and {len(groups) - 5} more" if len(groups) > 5 else "")
    return (f"{len(groups)} question(s) appear under more than one case_id ({shown}). "
            "Each row still counts as one case, so a repeated question counts more than once in every rate.")

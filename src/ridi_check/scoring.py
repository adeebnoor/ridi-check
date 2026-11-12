"""Scoring against an expected answer. No model judge: a judge adds its own error."""

from __future__ import annotations

import inspect
from typing import Callable

from .analysis import normalise
from .contract import Case, ContractError, run_column
from .util import load_callable, sha256_file

EXACT_MATCH = "normalised exact match"


def exact_match(answer: str, expected: str) -> bool:
    return normalise(answer) == normalise(expected)


def load_scorer(spec: str | None) -> tuple[Callable[[str, str], object], str]:
    """Returns (scorer(answer, expected) -> truthy when correct, name for the manifest)."""
    if not spec:
        return exact_match, EXACT_MATCH
    return load_callable(spec, "scorer"), spec


def scorer_fingerprint(scorer: Callable[[str, str], object]) -> str | None:
    """SHA-256 of the file a scorer of your own lives in, when it can be found. The built-in exact match has
    none: it changes only with the tool, whose version is recorded."""
    if scorer is exact_match:
        return None
    try:
        return sha256_file(inspect.getsourcefile(scorer))
    except (TypeError, OSError):
        return None


def check_scores(cases: list[Case], scorer: Callable[[str, str], object], name: str) -> dict:
    """Score every answer in a results file again and compare with the score the file holds.

    A results file made by hand carries scores from somewhere else, and its `expected` column is not
    used to score anything. This says where the two disagree. A run with no answer text and a case with
    no expected answer cannot be checked and are counted as that. Agreement shows that the scores in the
    file are the ones this scorer gives; it does not show that the answer key is right.
    """
    checked = without_answer = 0
    without_expected: list[str] = []
    disagree: list[str] = []
    cases_that_disagree: list[str] = []
    for case in cases:
        if not case.expected:
            without_expected.append(case.case_id)
            continue
        before = len(disagree)
        for side, runs in (("baseline", case.baseline), ("updated", case.updated)):
            # an incomplete case has lost its first run, so its runs are not numbered here
            for k, r in enumerate(runs, 1):
                if r.correct is None:
                    continue
                if not r.answer:
                    without_answer += 1
                    continue
                checked += 1
                try:
                    given = 1 if scorer(r.answer, case.expected) else 0
                except Exception as exc:    # the user's scorer may fail in any way
                    raise ContractError(f"The scorer failed on case {case.case_id}: {type(exc).__name__}: {exc}") from exc
                if given != r.correct:
                    column = f"{side} run" if case.incomplete else run_column(side, k, "correct")
                    disagree.append(f"{case.case_id} {column}: the file has {r.correct}, the scorer gives {given}")
        if len(disagree) > before:
            cases_that_disagree.append(case.case_id)
    if not checked:
        raise ContractError(
            "--check-scores found nothing to check. It needs answer-key mode, an expected column and the answer "
            "text of the runs in the file."
        )
    out = {
        "scorer": name, "runs_checked": checked, "runs_that_disagree": len(disagree),
        "cases_that_disagree": cases_that_disagree, "first_disagreements": disagree[:50],
        "cases_without_expected": len(without_expected), "runs_without_answer_text": without_answer,
    }
    fingerprint = scorer_fingerprint(scorer)
    if fingerprint:     # which code gave these scores: the name alone does not say that it is still the same
        out["scorer_source_sha256"] = fingerprint
    return out


def score_check_lines(check: dict) -> list[str]:
    """What `report` prints for a score check."""
    n, bad, ids = check["runs_checked"], check["runs_that_disagree"], check["cases_that_disagree"]
    if bad:
        lines = [f"Score check against {check['scorer']}: {bad} of {n} scored runs do not have the score it gives, in "
                 f"{len(ids)} case(s): " + ", ".join(ids[:20]) + (f", and {len(ids) - 20} more" if len(ids) > 20 else "") + "."]
        lines += [f"  {line}" for line in check["first_disagreements"][:10]]
        if bad > 10:
            lines.append(f"  ... and {bad - 10} more; summary.json lists the first 50.")
    else:
        lines = [f"Score check against {check['scorer']}: all {n} scored runs have the score it gives. This shows "
                 "that the scores follow this scorer, not that the answer key is right."]
    skipped = [f"{check['cases_without_expected']} case(s) have no expected answer" if check["cases_without_expected"] else "",
               f"{check['runs_without_answer_text']} run(s) have no answer text" if check["runs_without_answer_text"] else ""]
    skipped = [part for part in skipped if part]
    if skipped:
        lines.append("Not checked: " + " and ".join(skipped) + ".")
    return lines

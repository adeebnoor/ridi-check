"""Scoring against an expected answer. No model judge: a judge adds its own error."""

from __future__ import annotations

from typing import Callable

from .analysis import normalise
from .util import load_callable

EXACT_MATCH = "normalised exact match"


def exact_match(answer: str, expected: str) -> bool:
    return normalise(answer) == normalise(expected)


def load_scorer(spec: str | None) -> tuple[Callable[[str, str], object], str]:
    """Returns (scorer(answer, expected) -> truthy when correct, name for the manifest)."""
    if not spec:
        return exact_match, EXACT_MATCH
    return load_callable(spec, "scorer"), spec

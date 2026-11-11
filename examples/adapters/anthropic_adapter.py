"""Adapter for an assistant built on the Claude API, using the official Anthropic SDK.

    pip install anthropic
    export ANTHROPIC_API_KEY=...            # read by the SDK; never written in a file

    ridi-check run --questions questions.csv --out ridi-out --report \\
        --current  python:anthropic_adapter:answer_current \\
        --proposed python:anthropic_adapter:answer_proposed

As written, the update under test is a model change: the two versions share the system prompt and
every setting, and differ in the model only. To test a prompt change instead, give both versions
the same model and two different system prompts.

Optional environment variables: RIDI_CURRENT_MODEL, RIDI_PROPOSED_MODEL, RIDI_EFFORT, and
ANTHROPIC_BASE_URL (read by the SDK) for a gateway or a test server.
"""

from __future__ import annotations

import os
import threading

import anthropic

CURRENT_MODEL = os.environ.get("RIDI_CURRENT_MODEL", "claude-opus-5")
PROPOSED_MODEL = os.environ.get("RIDI_PROPOSED_MODEL", "claude-opus-5-5")
# The default effort differs between models. Set it, so that the model is the only difference.
EFFORT = os.environ.get("RIDI_EFFORT", "medium")
SYSTEM = "You answer questions about our product. Be brief."

_client: anthropic.Anthropic | None = None
_lock = threading.Lock()


def _get_client() -> anthropic.Anthropic:
    """One client for all threads. Credentials come from the environment."""
    global _client
    with _lock:
        if _client is None:
            _client = anthropic.Anthropic()
        return _client


def ask(question: str, model: str) -> dict:
    response = _get_client().messages.create(
        model=model,
        max_tokens=16000,
        system=SYSTEM,
        thinking={"type": "adaptive"},
        output_config={"effort": EFFORT},
        messages=[{"role": "user", "content": question}],
    )
    # A refusal is an answer worth seeing in the report, not a failed call. No fallback model is
    # configured here: the check should measure the model you name. If your production code sends
    # `fallbacks`, send the same here, so that the check measures what you ship.
    if response.stop_reason == "refusal":
        category = response.stop_details.category if response.stop_details else None
        return {"answer": f"(refused: {category or 'no category given'})", "context": None}
    text = "".join(block.text for block in response.content if block.type == "text")
    if response.stop_reason == "max_tokens":
        text += " (cut off at max_tokens)"
    return {"answer": text, "context": None}


def answer_current(question: str) -> dict:
    return ask(question, CURRENT_MODEL)


def answer_proposed(question: str) -> dict:
    return ask(question, PROPOSED_MODEL)

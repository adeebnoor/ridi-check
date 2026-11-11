"""Connect your assistant to ridi-check.

ridi-check needs one thing from you: a way to ask each version of your assistant a question.
Fill in `ask` below. Nothing else in this file has to change.

Each function returns {"answer": str, "context": list[str] | None}.
`context` is optional: the ids or titles of the passages the answer was built from, if your
assistant retrieves documents. Leave it as None if it does not.
"""


def ask(question: str, version: str) -> tuple[str, list[str] | None]:
    """Return (answer text, passage ids or None) from one version of your assistant.

    `version` is "current" (what is live today) or "proposed" (the update you want to ship).
    Use it to switch whatever the update changes. For example:

        model = "the-model-you-use-today" if version == "current" else "the-new-model"
        prompt = OLD_PROMPT if version == "current" else NEW_PROMPT
        reply = my_app.answer(question, model=model, system_prompt=prompt)
        return reply.text, [doc.title for doc in reply.sources]

    Read keys from environment variables, not from this file.
    """
    raise NotImplementedError(
        "Open my_assistant.py and make ask() call your assistant. See the example in its docstring."
    )


def answer_current(question: str) -> dict:
    text, passages = ask(question, "current")
    return {"answer": text, "context": passages}


def answer_proposed(question: str) -> dict:
    text, passages = ask(question, "proposed")
    return {"answer": text, "context": passages}

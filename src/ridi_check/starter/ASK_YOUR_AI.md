# Let your AI coding assistant set this up

Paste the text below into the AI coding assistant you use, opened in the project that holds your
assistant. It has everything the AI needs to connect your assistant to ridi-check.

---

Set up ridi-check for this project. ridi-check is a command-line tool that runs the current and the
proposed version of an LLM assistant on the same questions, more than once, and reports which answers
changed and which changes hold on re-run.

What to do:

1. Find how this project answers a user question (the function, command or HTTP endpoint).
2. Edit `my_assistant.py` in this folder. Make `ask(question, version)` call the assistant and return
   `(answer_text, passage_ids_or_None)`. `version` is `"current"` or `"proposed"`: use it to switch
   only what the update changes (model, prompt, retriever, chunking, ...). Keep everything else equal.
3. Do not put API keys in any file. Read them from environment variables.
4. Put real user questions in `questions.csv` (columns `case_id`, `question`; add `expected` only if
   there is a trusted reference answer for every row).
5. Try five questions first: `ridi-check run --limit 5`. Then run all: `ridi-check run`.
6. Tell me where `report.html` is. Do not summarise the result as safe, passed or approved:
   ridi-check reports counts of changed answers, and the decision is mine.

Facts about the tool:

- Interface: `answer(question: str) -> {"answer": str, "context": list[str] | None}`.
- A system can also be `command:<shell command>` (question on stdin, JSON or text on stdout), an
  `http://` URL, or a JSON definition file. `ridi-check run --help` lists every option.
- `ridi-check.json` holds the settings, so `ridi-check run` needs no arguments in this folder.
- Runs are resumable: running the same command again continues and retries failed calls.
- After changing the assistant's code, use a new `out` directory. Recorded answers are never
  overwritten.
- `ridi-check gate ridi-out/results.csv` exits 1 when stable regressions exceed a limit; use it in CI.
- The function is called from several threads. If the assistant is not thread-safe, set
  `"concurrency": 1` in `ridi-check.json`.

# Adapter examples

Ready-made ways to connect an assistant to ridi-check. Copy the one that fits, change the model names
and the system prompt, and keep everything else equal between the two versions.

Keys are read from environment variables only. Nothing here holds a key, and none should be added.

| Your assistant uses… | Files | How ridi-check calls it |
|---|---|---|
| an OpenAI-compatible HTTP API (`/chat/completions`) | `openai_current.json`, `openai_proposed.json` | the built-in http adapter; no code |
| the Claude API | `anthropic_adapter.py` | a Python function that uses the official `anthropic` SDK |
| a command-line program, or `curl` | `shell_command.sh` | a shell command: question on stdin, answer on stdout |
| tools, or memory between turns (an agent) | `agent_adapter.py`, `agent_questions.csv` | a Python function that runs a whole conversation and returns the tool calls as `context` |

## OpenAI-compatible HTTP

```bash
export OPENAI_BASE_URL=https://your-endpoint.example/v1
```

```bash
export OPENAI_API_KEY=...
```

```bash
ridi-check run --questions questions.csv --out ridi-out --report --current openai_current.json --proposed openai_proposed.json
```

Edit `"model"` in each file. To test a prompt change, keep the model equal and change the system message
in `openai_proposed.json`. `${NAME}` in `url` and `headers` is read from the environment when the run
starts; the file itself is copied into `run_manifest.json`, the key is not.

## Claude API

```bash
pip install anthropic
```

```bash
export ANTHROPIC_API_KEY=...
```

```bash
ridi-check run --questions questions.csv --out ridi-out --report --current python:anthropic_adapter:answer_current --proposed python:anthropic_adapter:answer_proposed
```

Run it from this folder, or copy `anthropic_adapter.py` next to your `ridi-check.json`. The two versions
differ in the model only (`RIDI_CURRENT_MODEL`, `RIDI_PROPOSED_MODEL`). A refusal is returned as an answer,
so it shows in the report; no fallback model is configured, so the check measures the model you name.

## Shell command

```bash
ridi-check run --questions questions.csv --out ridi-out --report --current "command:sh shell_command.sh your-current-model" --proposed "command:sh shell_command.sh your-new-model"
```

Needs `curl` and `jq`. If your assistant is its own program, replace the script body with one line that
runs it; see the comment at the top of the file.

## An agent with tools and memory

```bash
ridi-check run --questions agent_questions.csv --out ridi-out --report --current python:agent_adapter:answer_current --proposed python:agent_adapter:answer_proposed
```

`agent_adapter.py` is a stand-in agent with fixed rules and made-up facts; it needs no network and no key.
It shows the pattern for a real one:

- **One function, one fresh session per call.** Runs must not share memory, or a re-run is not a re-run.
- **A conversation is one case.** Put the turns in the `question` cell as a JSON list:
  `["I have a child card.", "What is the fine for a late book?"]`. The adapter replays them and returns the
  last answer.
- **Tool calls go in `context`, numbered.** The report then lists, under each changed case, the calls only
  one version made. In the example, the update stops calling the calculator and loses earlier turns; both
  show up as stable regressions with the missing calls next to them.

ridi-check has not been tried on a production agent yet. If you try it on one, an issue saying what worked
and what did not is welcome.

## Before a full run

Try five questions first with `--limit 5`. Every call costs what your provider charges:
questions × 2 versions × runs. These examples are tested against a local stand-in server, so no real key
is needed to run the test suite; they have not been run against every provider.

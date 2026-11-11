"""Adapters: how ridi-check calls the assistant under test.

Every adapter is one function, answer(question) -> {"answer": str, "context": list[str] | None}.
No model provider is built in. The owner's assistant is the system under test.

A system definition is one of:
  python:module:function          an importable Python function (a bare module:function also works)
  command:<shell command>         reads the question on stdin, writes JSON or plain text on stdout
  http://... or https://...       POST {"question": ...}, reads "answer" and "context" from the reply
  path/to/system.json             the same three types with every option spelled out
"""

from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable

from .util import load_callable, sha256_file

DEFAULT_TIMEOUT = 120.0
ENV_REFERENCE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
SECRET_HEADER = re.compile(r"auth|key|token|secret|cookie", re.I)
BARE_PYTHON = re.compile(r"^[A-Za-z_][\w.]*:[A-Za-z_][\w.]*$")


class AdapterError(Exception):
    """A call to the system under test failed or returned the wrong shape.

    The runner reads three optional attributes from any exception a call raises, this one or your own:
    `retryable` (False: trying again will not help), `retry_after` (seconds the service asked to wait)
    and `service_failure` (True: the service itself is refusing or unreachable, not this one question).
    """

    def __init__(self, message: str, *, status: int | None = None, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after
        # 408 timeout, 409 conflict, 425 too early, 429 rate limit and every 5xx may pass on a later attempt.
        # So may any refusal that says when to come back: some services limit their free use with a 402
        # and a Retry-After header.
        self.retryable = (retry_after is not None or status is None or status in (408, 409, 425, 429)
                          or status >= 500)
        # A missing or refused key, a used-up quota, a rate limit: the next question would fail the same
        # way. A 400, a 404, a 500 or a timeout can be about one question only, so they do not count.
        self.service_failure = status in (401, 402, 403, 429)


def retry_after_seconds(value: str | None) -> float | None:
    """The Retry-After header: a number of seconds, or a date. None when absent or unreadable."""
    if not value:
        return None
    try:
        return max(0.0, float(value.strip()))
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(value)
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())
    except (TypeError, ValueError):
        return None


class DefinitionError(ValueError):
    """A system definition could not be understood."""


def normalise_output(out: Any) -> dict:
    """Coerce an adapter result to {"answer": str, "context": list[str] | None}."""
    if isinstance(out, str):
        return {"answer": out, "context": None}
    if not isinstance(out, dict) or "answer" not in out:
        raise AdapterError('the system must return {"answer": str, "context": list[str] | None} or a string')
    answer = out["answer"]
    if not isinstance(answer, str):
        raise AdapterError(f'"answer" must be a string, got {type(answer).__name__}')
    context = out.get("context")
    if context is None:
        return {"answer": answer, "context": None}
    if isinstance(context, str):
        context = [context]
    if not isinstance(context, (list, tuple)):
        raise AdapterError(f'"context" must be a list of strings or null, got {type(context).__name__}')
    return {
        "answer": answer,
        "context": [c if isinstance(c, str) else json.dumps(c, ensure_ascii=False) for c in context],
    }


def json_path(obj: Any, path: str) -> Any:
    """Follow a dotted path. Integers index lists; '*' maps over a list."""
    parts = [p for p in path.split(".") if p != ""]

    def walk(node: Any, i: int) -> Any:
        if i == len(parts):
            return node
        part = parts[i]
        if part == "*":
            if not isinstance(node, list):
                raise KeyError(path)
            return [walk(item, i + 1) for item in node]
        if isinstance(node, list):
            try:
                return walk(node[int(part)], i + 1)
            except (ValueError, IndexError):
                raise KeyError(path) from None
        if isinstance(node, dict) and part in node:
            return walk(node[part], i + 1)
        raise KeyError(path)

    return walk(obj, 0)


def _fill(template: Any, question: str) -> Any:
    if isinstance(template, str):
        return template.replace("{question}", question)
    if isinstance(template, list):
        return [_fill(item, question) for item in template]
    if isinstance(template, dict):
        return {k: _fill(v, question) for k, v in template.items()}
    return template


def _expand_env(value: str, what: str) -> str:
    def replace(match: re.Match) -> str:
        name = match.group(1)
        if name not in os.environ:
            raise DefinitionError(f"{what}: environment variable {name} is not set")
        return os.environ[name]

    return ENV_REFERENCE.sub(replace, value)


def python_adapter(target: str) -> tuple[Callable[[str, dict], dict], str | None]:
    """Returns (answer, SHA-256 of the file the function lives in, when it can be found)."""
    try:
        function = load_callable(target, "python adapter")
    except ValueError as exc:
        raise DefinitionError(str(exc)) from exc
    try:
        source = sha256_file(inspect.getsourcefile(function))
    except (TypeError, OSError):
        source = None
    return (lambda question, meta: normalise_output(function(question))), source


def command_adapter(command: str, timeout: float) -> Callable[[str, dict], dict]:
    if not command.strip():
        raise DefinitionError("command adapter: the command is empty")

    def answer(question: str, meta: dict) -> dict:
        env = dict(os.environ)
        env.update({f"RIDI_CHECK_{k.upper()}": str(v) for k, v in meta.items()})
        # The question goes out as UTF-8 and the reply is read as UTF-8, on every platform. A Python child
        # on Windows would otherwise use the local code page and garble any non-Latin question or answer.
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            # The command is the one the owner configured and is run through the shell on purpose.
            # Nothing from the questions file is put into it: the question goes in on stdin and the
            # case id in an environment variable, so data cannot change what is executed.
            done = subprocess.run(  # nosec B602
                command, shell=True, input=question, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=timeout, env=env,
            )
        except subprocess.TimeoutExpired:
            raise AdapterError(f"command timed out after {timeout:g}s") from None
        if done.returncode != 0:
            tail = done.stderr.strip()[-300:]
            raise AdapterError(f"command exited with status {done.returncode}" + (f": {tail}" if tail else ""))
        text = done.stdout.strip()
        try:
            parsed = json.loads(text)
        except ValueError:
            parsed = None
        if isinstance(parsed, dict) and "answer" in parsed:
            return normalise_output(parsed)
        return {"answer": text, "context": None}

    return answer


def http_adapter(config: dict, timeout: float) -> Callable[[str, dict], dict]:
    url = config.get("url")
    if not isinstance(url, str):
        raise DefinitionError('http adapter: needs "url"')
    url = _expand_env(url, "http adapter url")      # the address may come from the environment
    if not url.startswith(("http://", "https://")):
        raise DefinitionError("http adapter: \"url\" must start with http:// or https://")
    template = config.get("request", {"question": "{question}"})
    answer_path = config.get("answer_path", "answer")
    context_path = config.get("context_path", "context")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    for name, value in (config.get("headers") or {}).items():
        headers[name] = _expand_env(str(value), f"http adapter header {name}")

    def answer(question: str, meta: dict) -> dict:
        body = json.dumps(_fill(template, question), ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            # The address was checked above: only http:// and https:// reach this call.
            with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
                raw = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip()[:300]
            raise AdapterError(f"HTTP {exc.code}" + (f": {detail}" if detail else ""), status=exc.code,
                               retry_after=retry_after_seconds(exc.headers.get("Retry-After"))) from None
        except urllib.error.URLError as exc:
            failure = AdapterError(f"request failed: {exc.reason}")
            # Nobody is listening at the address: the next question would not be answered either.
            failure.service_failure = not isinstance(exc.reason, TimeoutError)
            raise failure from None
        except TimeoutError:
            raise AdapterError(f"request timed out after {timeout:g}s") from None
        try:
            reply = json.loads(raw)
        except ValueError:
            raise AdapterError(f"the reply is not JSON: {raw[:200]!r}") from None
        try:
            found = json_path(reply, answer_path)
        except KeyError:
            raise AdapterError(f"the reply has no value at answer_path {answer_path!r}") from None
        context = None
        if context_path:
            try:
                context = json_path(reply, context_path)
            except KeyError:
                context = None
        return normalise_output({"answer": found, "context": context})

    return answer


def parse_definition(text: str) -> dict:
    """Turn a definition string into a config dict with a "type"."""
    s = text.strip()
    if s.startswith("python:"):
        return {"type": "python", "target": s[len("python:"):].strip()}
    if s.startswith("command:"):
        return {"type": "command", "command": s[len("command:"):].strip()}
    if s.startswith(("http://", "https://")):
        return {"type": "http", "url": s}
    if os.path.isfile(s):
        try:
            with open(s, encoding="utf-8") as f:
                config = json.load(f)
        except (OSError, ValueError) as exc:
            raise DefinitionError(f"{s}: not a readable JSON system definition: {exc}") from exc
        if not isinstance(config, dict) or config.get("type") not in ("python", "command", "http"):
            raise DefinitionError(f'{s}: needs "type": "python", "command" or "http"')
        return config
    if BARE_PYTHON.match(s):
        return {"type": "python", "target": s}
    raise DefinitionError(
        f"cannot read system definition {text!r}: use python:module:function, command:<shell command>, "
        "an http(s) URL, or the path of a JSON definition file"
    )


def build_adapter(definition: str, timeout: float | None = None) -> tuple[Callable[[str, dict], dict], dict]:
    """Returns (answer(question, meta), description for the manifest)."""
    config = parse_definition(definition)
    limit = float(config.get("timeout", timeout if timeout is not None else DEFAULT_TIMEOUT))
    kind = config["type"]
    description: dict = {"definition": definition, "type": kind}
    if os.path.isfile(definition.strip()):
        description["definition_file_sha256"] = sha256_file(definition.strip())
        description["definition_file_content"] = config
    if kind == "python":
        if not isinstance(config.get("target"), str):
            raise DefinitionError('python adapter: needs "target": "module:function"')
        answer, source = python_adapter(config["target"])
        if source:
            description["python_source_sha256"] = source
        return answer, description
    if kind == "command":
        if not isinstance(config.get("command"), str):
            raise DefinitionError('command adapter: needs "command"')
        return command_adapter(config["command"], limit), description
    return http_adapter(config, limit), description


def literal_secret_headers(definition: str) -> list[str]:
    """Header names that look like credentials and hold a literal value (not ${ENV_VAR})."""
    try:
        config = parse_definition(definition)
    except DefinitionError:
        return []
    headers = config.get("headers") or {}
    return [
        name for name, value in headers.items()
        if SECRET_HEADER.search(name) and not ENV_REFERENCE.search(str(value))
    ]

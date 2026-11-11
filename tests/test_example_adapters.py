"""The adapter examples in examples/adapters, run against a stand-in server on 127.0.0.1.

No real key and no outside network: the server checks that each example sends the key it read from
the environment, in the header its API expects, and answers in that API's reply shape.
"""

import csv
import importlib
import json
import os
import re
import shutil
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from ridi_check.adapters import AdapterError, DefinitionError, build_adapter
from ridi_check.cli import main

from conftest import ROOT

ADAPTERS = os.path.join(ROOT, "examples", "adapters")
META = {"case_id": "c1", "version": "current", "run": 1}
KEY = "test-key-not-a-real-one"


class _StandIn(BaseHTTPRequestHandler):
    seen = []

    def _send(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8"))
        headers = {k.lower(): v for k, v in self.headers.items()}
        _StandIn.seen.append((self.path, headers, body))
        if self.path == "/v1/chat/completions":                      # OpenAI-compatible
            if headers.get("authorization") != f"Bearer {KEY}":
                return self._send(401, {"error": {"message": "bad key"}})
            question = body["messages"][-1]["content"]
            return self._send(200, {"choices": [{"message": {"role": "assistant",
                                                              "content": f"{body['model']}: {question}"}}]})
        if self.path == "/v1/messages":                               # Claude API
            sent_key = headers.get("x-api-key") or headers.get("authorization", "").removeprefix("Bearer ")
            if sent_key != KEY or "anthropic-version" not in headers:
                return self._send(401, {"type": "error", "error": {"type": "authentication_error", "message": "bad key"}})
            question = body["messages"][-1]["content"]
            if isinstance(question, list):
                question = "".join(part.get("text", "") for part in question)
            reply = {"id": "msg_standin", "type": "message", "role": "assistant", "model": body["model"],
                     "stop_sequence": None, "usage": {"input_tokens": 3, "output_tokens": 5}}
            if "refuse" in question:
                reply.update(content=[], stop_reason="refusal",
                             stop_details={"type": "refusal", "category": "cyber", "explanation": "declined"})
            else:
                reply.update(stop_reason="end_turn", content=[
                    {"type": "thinking", "thinking": "", "signature": "sig"},
                    {"type": "text", "text": f"{body['model']}: {question}"}])
            return self._send(200, reply)
        return self._send(404, {"error": "no such path"})

    def log_message(self, *args):
        pass


@pytest.fixture
def standin(monkeypatch):
    for name in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    _StandIn.seen = []
    httpd = HTTPServer(("127.0.0.1", 0), _StandIn)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def test_openai_compatible_definitions(standin, monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", standin + "/v1")
    monkeypatch.setenv("OPENAI_API_KEY", KEY)
    current, described = build_adapter(os.path.join(ADAPTERS, "openai_current.json"))
    proposed, _ = build_adapter(os.path.join(ADAPTERS, "openai_proposed.json"))
    assert current('What is "x"?\nSecond line', META) == {
        "answer": 'your-current-model: What is "x"?\nSecond line', "context": None}
    assert proposed("سؤال", META)["answer"] == "your-new-model: سؤال"
    path, headers, body = _StandIn.seen[0]
    assert path == "/v1/chat/completions" and headers["authorization"] == f"Bearer {KEY}"
    assert [m["role"] for m in body["messages"]] == ["system", "user"]
    assert KEY not in json.dumps(described)             # what goes into the manifest has no key in it

    monkeypatch.setenv("OPENAI_API_KEY", "wrong")
    rejected, _ = build_adapter(os.path.join(ADAPTERS, "openai_current.json"))
    with pytest.raises(AdapterError, match="HTTP 401"):
        rejected("q", META)
    monkeypatch.delenv("OPENAI_API_KEY")
    with pytest.raises(DefinitionError, match="OPENAI_API_KEY is not set"):
        build_adapter(os.path.join(ADAPTERS, "openai_current.json"))


def test_openai_compatible_end_to_end(standin, monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("OPENAI_BASE_URL", standin + "/v1")
    monkeypatch.setenv("OPENAI_API_KEY", KEY)
    questions = tmp_path / "questions.csv"
    questions.write_text("case_id,question\na,first\nb,second\n", encoding="utf-8")
    status = main(["run", "--questions", str(questions), "--out", str(tmp_path / "out"), "--report",
                   "--current", os.path.join(ADAPTERS, "openai_current.json"),
                   "--proposed", os.path.join(ADAPTERS, "openai_proposed.json")])
    assert status == 0
    with open(tmp_path / "out" / "results.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["baseline_answer"] == "your-current-model: first"
    assert rows[0]["updated_repeat_answer"] == "your-new-model: first"
    summary = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    assert summary["states"]["stable_change"] == 2
    manifest = (tmp_path / "out" / "run_manifest.json").read_text(encoding="utf-8")
    assert KEY not in manifest and "${OPENAI_API_KEY}" in manifest
    assert KEY not in (tmp_path / "out" / "raw_outputs.jsonl").read_text(encoding="utf-8")


def test_claude_api_adapter(standin, monkeypatch):
    pytest.importorskip("anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", KEY)
    monkeypatch.setenv("ANTHROPIC_BASE_URL", standin)
    for name in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE", "RIDI_CURRENT_MODEL", "RIDI_PROPOSED_MODEL", "RIDI_EFFORT"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.syspath_prepend(ADAPTERS)
    sys.modules.pop("anthropic_adapter", None)
    adapter = importlib.import_module("anthropic_adapter")
    try:
        assert adapter.answer_current("How long is the loan?") == {
            "answer": "claude-opus-5: How long is the loan?", "context": None}
        assert adapter.answer_proposed("How long is the loan?")["answer"] == "claude-opus-5-5: How long is the loan?"
        assert adapter.answer_proposed("please refuse this")["answer"] == "(refused: cyber)"   # an answer, not a crash

        path, headers, body = _StandIn.seen[0]
        assert path == "/v1/messages" and KEY in (headers.get("x-api-key"), headers.get("authorization", "")[7:])
        assert body["model"] == "claude-opus-5" and body["max_tokens"] == 16000
        assert body["thinking"] == {"type": "adaptive"} and body["output_config"] == {"effort": "medium"}
        assert "fallbacks" not in body                    # the check measures the model that was named
        # the two versions differ in the model and in nothing else
        assert {k: v for k, v in _StandIn.seen[1][2].items() if k != "model"} == {k: v for k, v in body.items() if k != "model"}

        # through ridi-check, as the README shows
        answer, _ = build_adapter("python:anthropic_adapter:answer_current")
        assert answer("q", META)["answer"] == "claude-opus-5: q"
    finally:
        sys.modules.pop("anthropic_adapter", None)


@pytest.mark.skipif(os.name == "nt" or not all(shutil.which(tool) for tool in ("sh", "curl", "jq")),
                    reason="needs sh, curl and jq")
def test_shell_command_adapter(standin, monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", standin + "/v1")
    monkeypatch.setenv("OPENAI_API_KEY", KEY)
    script = os.path.join(ADAPTERS, "shell_command.sh")
    answer, described = build_adapter(f'command:sh "{script}" your-current-model')
    assert described["type"] == "command"
    tricky = 'He said "hi" & left;\n$HOME `date` \\ سؤال'
    assert answer(tricky, META) == {"answer": "your-current-model: " + tricky, "context": None}
    assert _StandIn.seen[-1][2] == {"model": "your-current-model", "messages": [{"role": "user", "content": tricky}]}

    monkeypatch.setenv("OPENAI_API_KEY", "wrong")
    with pytest.raises(AdapterError, match="(?s)status 1.*bad key"):
        answer("q", META)
    monkeypatch.delenv("OPENAI_API_KEY")
    with pytest.raises(AdapterError, match="set OPENAI_API_KEY"):
        answer("q", META)
    no_model, _ = build_adapter(f'command:sh "{script}"')
    with pytest.raises(AdapterError, match="usage: shell_command.sh MODEL"):
        no_model("q", META)


def test_examples_hold_no_key_and_read_them_from_the_environment():
    secret = re.compile(r"sk-[A-Za-z0-9_\-]{8,}|Bearer +[A-Za-z0-9_\-\.]{16,}|api[_-]?key\s*[=:]\s*[\"'][^\"'$]{8,}[\"']", re.I)
    for name in sorted(os.listdir(ADAPTERS)):
        if not os.path.isfile(os.path.join(ADAPTERS, name)):
            continue
        with open(os.path.join(ADAPTERS, name), encoding="utf-8") as f:
            text = f.read()
        assert not secret.search(text), f"{name} looks as if it holds a key"
    for name in ("openai_current.json", "openai_proposed.json"):
        with open(os.path.join(ADAPTERS, name), encoding="utf-8") as f:
            definition = json.load(f)
        assert definition["headers"]["Authorization"] == "Bearer ${OPENAI_API_KEY}"
        assert definition["url"].startswith("${OPENAI_BASE_URL}")
    with open(os.path.join(ADAPTERS, "anthropic_adapter.py"), encoding="utf-8") as f:
        source = f.read()
    assert "anthropic.Anthropic()" in source and "api_key=" not in source

"""The three adapters. The http tests talk to a server on 127.0.0.1 only."""

import json
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from ridi_check.adapters import (
    AdapterError, DefinitionError, build_adapter, json_path, literal_secret_headers, normalise_output,
    parse_definition,
)

META = {"case_id": "c1", "version": "current", "run": 1}
PY = sys.executable


def test_python_adapter():
    answer, description = build_adapter("python:fake_systems:current")
    assert answer("q", META) == {"answer": "old answer to q", "context": ["doc 1", "doc 2"]}
    assert len(description.pop("python_source_sha256")) == 64
    assert description == {"definition": "python:fake_systems:current", "type": "python"}
    bare, _ = build_adapter("fake_systems:plain_string")
    assert bare("q", META) == {"answer": "just text", "context": None}


def test_python_adapter_errors():
    with pytest.raises(DefinitionError, match="cannot import"):
        build_adapter("python:no_such_module_anywhere:f")
    with pytest.raises(DefinitionError, match="no attribute"):
        build_adapter("python:fake_systems:missing")
    with pytest.raises(DefinitionError, match="cannot read system definition"):
        build_adapter("what is this")


def test_command_adapter_json_and_plain_text(tmp_path):
    script = tmp_path / "bot.py"
    script.write_text(
        "import json, os, sys\n"
        "q = sys.stdin.read()\n"
        "if q.startswith('plain'):\n"
        "    print('  plain reply  ')\n"
        "elif q.startswith('fail'):\n"
        "    sys.stderr.write('model overloaded'); sys.exit(3)\n"
        "else:\n"
        "    print(json.dumps({'answer': q.upper() + ' ' + os.environ['RIDI_CHECK_CASE_ID'], 'context': ['p1']}))\n",
        encoding="utf-8")
    answer, description = build_adapter(f'command:"{PY}" "{script}"')
    assert description["type"] == "command"
    assert answer("سؤال hello", META) == {"answer": "سؤال HELLO c1", "context": ["p1"]}
    assert answer("plain please", META) == {"answer": "plain reply", "context": None}
    with pytest.raises(AdapterError, match="status 3: model overloaded"):
        answer("fail now", META)


def test_command_adapter_timeout():
    answer, _ = build_adapter(f'command:"{PY}" -c "import time; time.sleep(5)"', timeout=0.3)
    with pytest.raises(AdapterError, match="timed out"):
        answer("q", META)


class _Handler(BaseHTTPRequestHandler):
    seen = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        _Handler.seen.append((self.path, dict(self.headers), body))
        if self.path == "/words":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<html>Sign in to continue</html>")
            return
        if self.path == "/slow":
            time.sleep(0.6)      # longer than the caller waits; it has hung up by now
            return
        if self.path == "/broken":
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"upstream exploded")
            return
        if self.path == "/chat":
            reply = {"choices": [{"message": {"content": "deep " + body["messages"][0]["content"]}}],
                     "sources": [{"title": "T1"}, {"title": "T2"}]}
        else:
            reply = {"answer": "echo " + body["question"], "context": ["a", "b"]}
        data = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def server(monkeypatch):
    for name in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    _Handler.seen = []
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def test_http_adapter_with_a_bare_url(server):
    answer, description = build_adapter(server + "/ask")
    assert description["type"] == "http"
    assert answer("why?", META) == {"answer": "echo why?", "context": ["a", "b"]}


def test_http_adapter_with_a_definition_file(server, tmp_path, monkeypatch):
    monkeypatch.setenv("TOY_KEY", "s3cret")
    definition = tmp_path / "proposed.json"
    definition.write_text(json.dumps({
        "type": "http", "url": server + "/chat",
        "headers": {"Authorization": "Bearer ${TOY_KEY}"},
        "request": {"model": "m", "messages": [{"role": "user", "content": "{question}"}]},
        "answer_path": "choices.0.message.content", "context_path": "sources.*.title",
    }), encoding="utf-8")
    answer, description = build_adapter(str(definition))
    assert answer('say "hi" {x}', META) == {"answer": 'deep say "hi" {x}', "context": ["T1", "T2"]}
    path, headers, body = _Handler.seen[-1]
    assert headers["Authorization"] == "Bearer s3cret" and body["model"] == "m"
    # the manifest gets the definition as given: the secret itself is not in it
    assert "s3cret" not in json.dumps(description) and len(description["definition_file_sha256"]) == 64
    assert literal_secret_headers(str(definition)) == []


def test_http_adapter_failures(server, tmp_path):
    broken, _ = build_adapter(server + "/broken")
    with pytest.raises(AdapterError, match="HTTP 500: upstream exploded"):
        broken("q", META)
    definition = tmp_path / "bad_path.json"
    definition.write_text(json.dumps({"type": "http", "url": server + "/ask", "answer_path": "result.text"}),
                          encoding="utf-8")
    missing, _ = build_adapter(str(definition))
    with pytest.raises(AdapterError, match="answer_path 'result.text'"):
        missing("q", META)


def test_http_adapter_says_what_went_wrong_when_no_usable_reply_comes_back(server):
    # a reply that is not JSON: the usual sign of a login page or a proxy error in front of the assistant
    words, _ = build_adapter(server + "/words")
    with pytest.raises(AdapterError, match="the reply is not JSON: '<html>Sign in"):
        words("q", META)
    # an assistant slower than the limit
    slow, _ = build_adapter(server + "/slow", timeout=0.2)
    with pytest.raises(AdapterError, match="timed out"):
        slow("q", META)
    # nothing listening at the address
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        free_port = probe.getsockname()[1]
    nobody, _ = build_adapter(f"http://127.0.0.1:{free_port}/ask", timeout=5)
    with pytest.raises(AdapterError, match="request failed"):
        nobody("q", META)


def test_http_address_can_come_from_the_environment(server, tmp_path, monkeypatch):
    monkeypatch.setenv("MY_BASE", server)
    definition = tmp_path / "env_url.json"
    definition.write_text(json.dumps({"type": "http", "url": "${MY_BASE}/ask"}), encoding="utf-8")
    answer, _ = build_adapter(str(definition))
    assert answer("hi", META)["answer"] == "echo hi"
    monkeypatch.setenv("MY_BASE", "ftp://nowhere")
    with pytest.raises(DefinitionError, match="must start with http"):
        build_adapter(str(definition))


def test_definition_file_problems(tmp_path, monkeypatch):
    bad = tmp_path / "bad.json"
    bad.write_text('{"type": "grpc"}', encoding="utf-8")
    with pytest.raises(DefinitionError, match='"type"'):
        parse_definition(str(bad))
    literal = tmp_path / "literal.json"
    literal.write_text(json.dumps({"type": "http", "url": "http://127.0.0.1:1/x", "headers": {"X-Api-Key": "abc"}}),
                       encoding="utf-8")
    assert literal_secret_headers(str(literal)) == ["X-Api-Key"]
    monkeypatch.delenv("MISSING_VAR_FOR_TEST", raising=False)
    unset = tmp_path / "unset.json"
    unset.write_text(json.dumps({"type": "http", "url": "http://127.0.0.1:1/x",
                                 "headers": {"Authorization": "${MISSING_VAR_FOR_TEST}"}}), encoding="utf-8")
    with pytest.raises(DefinitionError, match="MISSING_VAR_FOR_TEST is not set"):
        build_adapter(str(unset))


def test_output_shapes_and_json_path():
    assert normalise_output("text") == {"answer": "text", "context": None}
    assert normalise_output({"answer": "a", "context": "one"}) == {"answer": "a", "context": ["one"]}
    assert normalise_output({"answer": "a", "context": [{"id": 1}]})["context"] == ['{"id": 1}']
    for bad in (None, 3, {"context": []}, {"answer": 5}, {"answer": "a", "context": 7}):
        with pytest.raises(AdapterError):
            normalise_output(bad)
    data = {"a": [{"b": 1}, {"b": 2}]}
    assert json_path(data, "a.1.b") == 2 and json_path(data, "a.*.b") == [1, 2]
    with pytest.raises(KeyError):
        json_path(data, "a.5.b")

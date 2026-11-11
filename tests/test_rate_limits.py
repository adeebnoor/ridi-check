"""What `run` does when the service limits or refuses calls: HTTP 429 with Retry-After, a used-up quota
(402), a missing key (401). The assistant is a server on 127.0.0.1 whose replies each test scripts."""

import io
import json
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import fake_systems
from ridi_check.adapters import AdapterError, build_adapter, retry_after_seconds
from ridi_check.cli import main
from ridi_check.runner import MAX_RETRY_AFTER, SERVICE_FAILURES, RunConfig, run

META = {"case_id": "c1", "version": "current", "run": 1}


class Service:
    """`reply(n, question)` is called for request number n (from 1) and returns (status, headers, body)."""

    def __init__(self):
        self.reply = lambda n, question: (200, {}, {"answer": "answer to " + question})
        self.count = 0
        self.seen = []          # (monotonic time the request arrived, question, status sent)
        self.lock = threading.Lock()

    def handler(self):
        service = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                question = json.loads(self.rfile.read(int(self.headers["Content-Length"])))["question"]
                arrived = time.monotonic()
                with service.lock:
                    service.count += 1
                    n = service.count
                status, headers, body = service.reply(n, question)
                with service.lock:
                    service.seen.append((arrived, question, status))
                data = json.dumps(body).encode()
                self.send_response(status)
                for name, value in headers.items():
                    self.send_header(name, value)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        return Handler


@pytest.fixture
def service(monkeypatch):
    for name in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    fake = Service()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), fake.handler())
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    fake.url = f"http://127.0.0.1:{httpd.server_address[1]}/ask"
    yield fake
    httpd.shutdown()
    httpd.server_close()


def questions(write, n):
    return write("questions.csv", "case_id,question\n" + "".join(f"{i},question {i}\n" for i in range(1, n + 1)))


def config(write, tmp_path, service, n, **overrides):
    values = dict(questions=questions(write, n), current=service.url, proposed=service.url,
                  out_dir=str(tmp_path / "out"), runs=1, concurrency=2, retries=2, retry_wait=0)
    values.update(overrides)
    return RunConfig(**values)


def raw(out_dir):
    with open(os.path.join(out_dir, "raw_outputs.jsonl"), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_the_retry_after_header_is_read_as_seconds_or_as_a_date():
    assert retry_after_seconds("7") == 7 and retry_after_seconds(" 0.5 ") == 0.5 and retry_after_seconds("-3") == 0
    in_a_minute = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=60), usegmt=True)
    assert 55 <= retry_after_seconds(in_a_minute) <= 60
    assert retry_after_seconds("Wed, 21 Oct 2015 07:28:00 GMT") == 0          # a date in the past: no wait
    assert retry_after_seconds("Wed, 21 Oct 2015 07:28:00 -0000") == 0        # a date that names no time zone
    assert retry_after_seconds(None) is None and retry_after_seconds("soon") is None


def test_the_http_adapter_says_whether_trying_again_can_help(service):
    answer, _ = build_adapter(service.url)
    expected = {429: (True, True), 402: (False, True), 401: (False, True), 403: (False, True),
                400: (False, False), 404: (False, False), 500: (True, False), 503: (True, False)}
    for status, (retryable, service_failure) in expected.items():
        service.reply = lambda n, question, status=status: (status, {}, {"error": "FREE_LIMIT"})
        with pytest.raises(AdapterError, match=f"HTTP {status}") as caught:
            answer("q", META)
        assert (caught.value.retryable, caught.value.service_failure) == (retryable, service_failure), status
        assert caught.value.retry_after is None and caught.value.status == status
        # a refusal that says when to come back is worth trying again, whatever its status
        service.reply = lambda n, question, status=status: (status, {"Retry-After": "2"}, {"error": "FREE_LIMIT"})
        with pytest.raises(AdapterError) as caught:
            answer("q", META)
        assert caught.value.retryable and caught.value.retry_after == 2


def test_a_rate_limit_is_waited_out_and_no_other_call_starts_meanwhile(write, tmp_path, service):
    def reply(n, question):
        if n == 1:
            return 429, {"Retry-After": "0.5"}, {"error": "slow down"}
        if n == 2:
            time.sleep(0.15)        # the call that was already on its way comes back after the limit is known
        return 200, {}, {"answer": "answer to " + question}

    service.reply = reply
    log = io.StringIO()
    outcome = run(config(write, tmp_path, service, 3), log=log)
    assert (outcome.calls_ok, outcome.calls_failed, outcome.attempts) == (6, 0, 7)
    assert "the service asked to wait 0.5s; no call is started before then." in log.getvalue()
    limited = min(t for t, _, status in service.seen if status == 429)
    # at most one other call was already on its way when the limit arrived; none is started after it
    on_its_way = len([t for t, _, status in service.seen if status != 429 and t - limited < 0.4])
    assert on_its_way <= 1
    assert len([t for t, _, _ in service.seen if t - limited >= 0.4]) == 6 - on_its_way


def test_a_used_up_quota_is_not_tried_again(write, tmp_path, service):
    service.reply = lambda n, question: ((402, {}, {"error": "FREE_LIMIT"}) if question == "question 2"
                                         else (200, {}, {"answer": "answer to " + question}))
    cfg = config(write, tmp_path, service, 3)
    outcome = run(cfg, log=io.StringIO())
    assert (outcome.calls_ok, outcome.calls_failed) == (4, 2) and outcome.stopped_early is None
    refused = [r for r in raw(cfg.out_dir) if r["status"] == "failed"]
    assert [(r["attempt"], r["max_attempts"]) for r in refused] == [(1, 3), (1, 3)]      # one attempt each, not three
    assert all("HTTP 402" in r["error"] and "FREE_LIMIT" in r["error"] for r in refused)
    assert outcome.results_path and "current#1: AdapterError: HTTP 402" in open(outcome.results_path, encoding="utf-8").read()


def test_a_server_error_is_still_tried_again(write, tmp_path, service):
    service.reply = lambda n, question: ((500, {}, {"error": "oops"}) if n <= 2
                                         else (200, {}, {"answer": "answer to " + question}))
    outcome = run(config(write, tmp_path, service, 1, concurrency=1), log=io.StringIO())
    assert (outcome.calls_ok, outcome.calls_failed, outcome.attempts) == (2, 0, 4)


def test_a_wait_longer_than_the_run_will_make_ends_the_call_at_once(write, tmp_path, service):
    service.reply = lambda n, question: (429, {"Retry-After": str(int(MAX_RETRY_AFTER) + 1)}, {"error": "come back later"})
    started = time.monotonic()
    outcome = run(config(write, tmp_path, service, 1), log=io.StringIO())
    assert time.monotonic() - started < 10 and outcome.attempts == 2 and outcome.calls_failed == 2


def test_the_run_stops_when_the_service_keeps_refusing_and_resumes_later(write, tmp_path, service, capsys):
    service.reply = lambda n, question: ((200, {}, {"answer": "answer to " + question}) if n <= 6
                                         else (402, {}, {"error": "FREE_LIMIT"}))
    arguments = ["run", "--questions", questions(write, 12), "--current", service.url, "--proposed", service.url,
                 "--out", str(tmp_path / "out"), "--concurrency", "1", "--retry-wait", "0"]
    assert main(arguments) == 2
    err = capsys.readouterr().err
    assert f"Stopped: {SERVICE_FAILURES} calls in a row failed because the service refused them" in err
    assert "HTTP 402" in err and "6 of 48 calls are recorded" in err and "Run the same command again" in err
    # the remaining calls were never made (one may already have been on its way when the run stopped)
    assert 6 + SERVICE_FAILURES <= len(service.seen) <= 6 + SERVICE_FAILURES + 1
    assert not os.path.exists(tmp_path / "out" / "results.csv")      # nothing to compare was written from this part
    with open(tmp_path / "out" / "run_manifest.json", encoding="utf-8") as f:
        assert json.load(f)["invocations"][-1]["status"] == "stopped: the service kept refusing or failing"

    service.reply = lambda n, question: (200, {}, {"answer": "answer to " + question})    # the quota is back
    assert main(arguments) == 0
    assert "48 planned, 6 already recorded, 42 succeeded, 0 failed" in capsys.readouterr().out


def test_questions_that_fail_on_their_own_do_not_stop_the_run(write, tmp_path, service):
    """A block of questions the assistant rejects (HTTP 400) is about those questions, not about the service."""
    service.reply = lambda n, question: ((400, {}, {"error": "this question is not allowed"})
                                         if 2 <= int(question.split()[1]) <= 9 else (200, {}, {"answer": "fine"}))
    outcome = run(config(write, tmp_path, service, 10, concurrency=1), log=io.StringIO())
    assert outcome.stopped_early is None and (outcome.calls_ok, outcome.calls_failed) == (4, 16)
    assert outcome.results_path is not None


def test_a_hand_written_adapter_can_ask_for_the_same_treatment(write, tmp_path):
    fake_systems.reset()
    try:
        cfg = RunConfig(questions=questions(write, 1), current="python:fake_systems:asks_to_wait",
                        proposed="python:fake_systems:will_never_work", out_dir=str(tmp_path / "out"),
                        runs=1, concurrency=1, retries=2, retry_wait=0)
        started = time.monotonic()
        outcome = run(cfg, log=io.StringIO())
        assert time.monotonic() - started >= 0.25                      # the wait it asked for (0.3 s) was made
        calls = [name for name, _ in fake_systems.calls]
        assert calls.count("asks_to_wait") == 2 and calls.count("will_never_work") == 1
        assert (outcome.calls_ok, outcome.calls_failed) == (1, 1)
    finally:
        fake_systems.reset()


def test_an_interrupt_does_not_wait_out_a_rate_limit(write, tmp_path):
    fake_systems.reset()
    cfg = RunConfig(questions=questions(write, 1), current="python:fake_systems:asks_for_a_long_wait",
                    proposed="python:fake_systems:interrupts_soon", out_dir=str(tmp_path / "out"),
                    runs=1, concurrency=2, retries=2, retry_wait=0)
    started = time.monotonic()
    outcome = run(cfg, log=io.StringIO())
    assert outcome.interrupted and time.monotonic() - started < 20      # the wait asked for was 60 seconds


def test_a_free_limit_sent_as_402_with_retry_after_is_waited_out(write, tmp_path, service):
    """What a real free service was seen to send: HTTP 402, code FREE_LIMIT, Retry-After in seconds."""
    service.reply = lambda n, question: ((402, {"Retry-After": "0.4"}, {"error": {"code": "FREE_LIMIT"}}) if n in (2, 3)
                                         else (200, {}, {"answer": "answer to " + question}))
    log = io.StringIO()
    cfg = config(write, tmp_path, service, 2, concurrency=1)
    outcome = run(cfg, log=log)
    assert (outcome.calls_ok, outcome.calls_failed, outcome.attempts) == (4, 0, 6)
    assert "the service asked to wait 0.4s" in log.getvalue()
    refused = [r for r in raw(cfg.out_dir) if r["status"] == "failed"]
    assert len(refused) == 2 and all("HTTP 402" in r["error"] for r in refused)       # every attempt is on record


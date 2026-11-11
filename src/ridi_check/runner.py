"""`ridi-check run`: call both versions on every question, more than once, and record everything.

Outputs in the output directory:
  raw_outputs.jsonl   one line per attempt, appended as it completes; never rewritten
  run_manifest.json   what was run: inputs, definitions, settings, one entry per invocation
  results.csv         the contract file that `report` and `gate` read

Calls go in passes: run 1 of every case and version, then run 2, and so on. An interrupted run
therefore holds complete first passes before any repeats. On restart, calls already recorded as
successful are skipped and failed ones are tried again.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable, TextIO

from . import __version__
from .adapters import build_adapter, literal_secret_headers
from .analysis import duplicate_note, duplicate_questions
from .contract import read_records, run_column, to_csv
from .scoring import load_scorer
from .util import atomic_write_text, now_iso, sha256_file

RAW_OUTPUTS = "raw_outputs.jsonl"
MANIFEST = "run_manifest.json"
RESULTS = "results.csv"

VERSIONS = ("current", "proposed")
SIDE = {"current": "baseline", "proposed": "updated"}
EMPTY_ANSWER = "(empty answer)"
FAIL_FAST = 5  # stop when this many calls have failed and none has succeeded
CONTEXT_ITEM_LIMIT = 120


class RunError(ValueError):
    """The run cannot start or continue with these inputs."""


@dataclass
class Question:
    case_id: str
    question: str
    expected: str = ""


@dataclass
class RunConfig:
    questions: str
    current: str
    proposed: str
    out_dir: str
    runs: int = 2
    concurrency: int = 4
    retries: int = 2
    retry_wait: float = 1.0
    timeout: float | None = None
    scorer: str | None = None
    current_label: str = ""
    proposed_label: str = ""
    limit: int | None = None  # use only the first N questions: a cheap first try


@dataclass
class RunOutcome:
    out_dir: str
    results_path: str | None
    interrupted: bool = False
    calls_planned: int = 0
    calls_skipped: int = 0
    calls_ok: int = 0
    calls_failed: int = 0
    attempts: int = 0
    recorded_ok: int = 0  # planned calls with a successful record, this invocation or earlier
    stopped_early: str | None = None  # the error, when the first calls all failed and the run stopped
    cases: int = 0
    failed: list[dict] = field(default_factory=list)  # final record of each call that never succeeded


# ---------- questions ----------

def read_questions(path: str) -> tuple[list[Question], bool]:
    """Returns (questions, has_expected). Rejects bad rows and says which."""
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise RunError(f"The questions file could not be read: {exc}") from exc
    rows: list[tuple[str, dict]] = []
    if path.lower().endswith((".jsonl", ".ndjson")):
        for number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except ValueError as exc:
                raise RunError(f"Questions line {number}: not valid JSON ({exc.msg}).") from None
            if not isinstance(obj, dict):
                raise RunError(f"Questions line {number}: expected a JSON object.")
            rows.append((f"line {number}", {str(k).strip().lower(): v for k, v in obj.items()}))
        has_expected_column = any("expected" in obj for _, obj in rows)
    else:
        records = read_records(text)
        if not records:
            raise RunError("The questions file is empty.")
        header = [h.strip().lower() for h in records[0][1]]
        for name in ("case_id", "question"):
            if name not in header:
                raise RunError(f"The questions file needs a {name} column.")
        for number, record in records[1:]:
            rows.append((f"row {number}", dict(zip(header, record))))
        has_expected_column = "expected" in header
    if not rows:
        raise RunError("The questions file has no questions.")

    questions: list[Question] = []
    seen: dict[str, str] = {}
    for where, obj in rows:
        def text_of(name: str) -> str:
            value = obj.get(name)
            return "" if value is None else str(value).strip()

        case_id, question = text_of("case_id"), text_of("question")
        if not case_id:
            raise RunError(f"Questions {where}: case_id is missing.")
        if case_id in seen:
            raise RunError(f"Questions {where}: case_id {case_id!r} appears more than once (first in {seen[case_id]}).")
        seen[case_id] = where
        if not question:
            raise RunError(f"Questions {where} (case {case_id}): question is empty.")
        questions.append(Question(case_id, question, text_of("expected")))

    with_expected = [q for q in questions if q.expected]
    if has_expected_column and with_expected and len(with_expected) != len(questions):
        missing = next(q for q in questions if not q.expected)
        raise RunError(
            f"Questions {seen[missing.case_id]} (case {missing.case_id}): expected is empty. "
            "Fill expected for every question, or remove the column to run without an answer key."
        )
    return questions, bool(with_expected)


# ---------- raw outputs ----------

def load_raw(path: str) -> tuple[dict[tuple, dict], dict[tuple, dict], int]:
    """Returns (successful call records, last failed record per call, unreadable line count)."""
    ok: dict[tuple, dict] = {}
    failed: dict[tuple, dict] = {}
    unreadable = 0
    if not os.path.exists(path):
        return ok, failed, unreadable
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                key = (str(record["case_id"]), record["version"], int(record["run"]))
                status = record["status"]
            except (ValueError, KeyError, TypeError):
                unreadable += 1  # e.g. a line cut short by a kill; left in place, not counted
                continue
            if status == "ok":
                ok[key] = record
            else:
                failed[key] = record
    return ok, failed, unreadable


class RawWriter:
    """Appends one JSON line per attempt and flushes it at once."""

    def __init__(self, path: str):
        needs_newline = False
        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, "rb") as f:
                f.seek(-1, os.SEEK_END)
                needs_newline = f.read(1) != b"\n"
        self._file: TextIO = open(path, "a", encoding="utf-8")
        self._lock = threading.Lock()
        if needs_newline:
            self._file.write("\n")

    def write(self, record: dict) -> None:
        line = json.dumps(record, ensure_ascii=False)
        with self._lock:
            self._file.write(line + "\n")
            self._file.flush()

    def close(self) -> None:
        with self._lock:
            self._file.flush()
            try:
                os.fsync(self._file.fileno())
            except OSError:
                pass
            self._file.close()


# ---------- results.csv ----------

def context_cell(context: list[str] | None) -> str:
    """Passage ids or titles joined by ' | '. Long passages are cut and tagged with a short hash."""
    items = []
    for passage in context or []:
        flat = " ".join(str(passage).split()).replace("|", "¦")
        if len(flat) > CONTEXT_ITEM_LIMIT:
            digest = hashlib.sha256(flat.encode("utf-8")).hexdigest()[:8]
            flat = f"{flat[:CONTEXT_ITEM_LIMIT - 12].rstrip()}… #{digest}"
        if flat:
            items.append(flat)
    return " | ".join(items)


def build_results(
    questions: list[Question], ok: dict[tuple, dict], failed: dict[tuple, dict], runs: int,
    scorer: Callable[[str, str], object] | None,
) -> tuple[list[str], list[list[str]]]:
    key = scorer is not None
    any_context = any(r.get("context") for r in ok.values())
    any_error = any(
        (q.case_id, v, k) not in ok for q in questions for v in VERSIONS for k in range(1, runs + 1)
    )
    header = ["case_id", "question"] + (["expected"] if key else [])
    for version in VERSIONS:
        header += [run_column(SIDE[version], k, "answer") for k in range(1, runs + 1)]
    if key:
        for version in VERSIONS:
            header += [run_column(SIDE[version], k, "correct") for k in range(1, runs + 1)]
    if any_context:
        header += ["baseline_context", "updated_context"]
    if any_error:
        header += ["run_errors"]

    rows = []
    for q in questions:
        answers: dict[str, list[str]] = {}
        corrects: dict[str, list[str]] = {}
        errors = []
        for version in VERSIONS:
            answers[version], corrects[version] = [], []
            for k in range(1, runs + 1):
                record = ok.get((q.case_id, version, k))
                if record is None:
                    last = failed.get((q.case_id, version, k))
                    errors.append(f"{version}#{k}: {last['error'] if last else 'not run'}")
                    answers[version].append("")
                    corrects[version].append("")
                    continue
                answer = record.get("answer") or ""
                answers[version].append(answer if answer.strip() else EMPTY_ANSWER)
                if key:
                    try:
                        corrects[version].append("1" if scorer(answer, q.expected) else "0")
                    except Exception as exc:
                        raise RunError(
                            f"The scorer failed on case {q.case_id} ({version}, run {k}): "
                            f"{type(exc).__name__}: {exc}"
                        ) from exc
        row = [q.case_id, q.question] + ([q.expected] if key else [])
        row += answers["current"] + answers["proposed"]
        if key:
            row += corrects["current"] + corrects["proposed"]
        if any_context:
            for version in VERSIONS:
                first = ok.get((q.case_id, version, 1))
                row.append(context_cell(first.get("context")) if first else "")
        if any_error:
            row.append("; ".join(errors))
        rows.append(row)
    return header, rows


# ---------- the run ----------

def _check_same_inputs(previous: dict, questions_sha: str, systems: dict) -> None:
    problems = []
    if previous.get("questions_sha256") != questions_sha:
        problems.append("the questions file has changed")
    for version in VERSIONS:
        before = (previous.get("systems") or {}).get(version) or {}
        now = systems[version]
        if before.get("definition") != now["definition"] or before.get("definition_file_sha256") != now.get(
            "definition_file_sha256"
        ):
            problems.append(f"the {version} system definition has changed")
    if problems:
        raise RunError(
            "This output directory holds an earlier run with different inputs ("
            + "; ".join(problems)
            + "). Earlier output is never deleted or mixed: choose a new output directory."
        )


def run(config: RunConfig, log: TextIO | None = None) -> RunOutcome:
    log = log if log is not None else sys.stderr
    if config.runs < 1:
        raise RunError("--runs must be at least 1.")
    if config.concurrency < 1:
        raise RunError("--concurrency must be at least 1.")
    if config.retries < 0:
        raise RunError("--retries cannot be negative.")

    questions, has_expected = read_questions(config.questions)
    questions_sha = sha256_file(config.questions)
    if config.limit is not None:
        if config.limit < 1:
            raise RunError("--limit must be at least 1.")
        if config.limit < len(questions):
            print(f"note: --limit {config.limit}: using the first {config.limit} of {len(questions)} questions.", file=log)
            questions = questions[:config.limit]
    repeated = duplicate_questions([(q.case_id, q.question) for q in questions])
    if repeated:
        print(f"note: {duplicate_note(repeated)}", file=log)
    try:
        scorer, scorer_name = load_scorer(config.scorer) if has_expected else (None, None)
    except ValueError as exc:
        raise RunError(str(exc)) from exc
    if config.scorer and not has_expected:
        print("note: --scorer is ignored because the questions file has no expected answers.", file=log)

    adapters: dict[str, Callable[[str, dict], dict]] = {}
    systems: dict[str, dict] = {}
    labels = {"current": config.current_label, "proposed": config.proposed_label}
    for version, definition in (("current", config.current), ("proposed", config.proposed)):
        try:
            adapters[version], description = build_adapter(definition, config.timeout)
        except ValueError as exc:
            raise RunError(f"--{version}: {exc}") from exc
        description["label"] = labels[version]
        systems[version] = description
        for header in literal_secret_headers(definition):
            print(
                f"warning: --{version}: header {header!r} holds a literal value and is copied into "
                f"{MANIFEST}. Write it as ${{ENV_VAR}} to keep it out.", file=log,
            )

    os.makedirs(config.out_dir, exist_ok=True)
    raw_path = os.path.join(config.out_dir, RAW_OUTPUTS)
    manifest_path = os.path.join(config.out_dir, MANIFEST)
    results_path = os.path.join(config.out_dir, RESULTS)

    previous: dict = {}
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                previous = json.load(f)
        except (OSError, ValueError) as exc:
            raise RunError(f"{manifest_path} exists but cannot be read ({exc}). Choose a new output directory.") from exc
        _check_same_inputs(previous, questions_sha, systems)
        for version in VERSIONS:
            before = ((previous.get("systems") or {}).get(version) or {}).get("python_source_sha256")
            if before and systems[version].get("python_source_sha256") not in (None, before):
                print(f"note: the code behind --{version} has changed since this run started. Answers already "
                      "recorded here came from the earlier code. Use a new output directory for a clean run.", file=log)
    elif os.path.exists(raw_path) and os.path.getsize(raw_path) > 0:
        raise RunError(
            f"{raw_path} exists without {MANIFEST}, so its inputs cannot be checked. Choose a new output directory."
        )

    ok, failed, unreadable = load_raw(raw_path)
    if unreadable:
        print(f"note: {unreadable} unreadable line(s) in {RAW_OUTPUTS} were left in place and not counted.", file=log)

    planned = [(q, v, k) for k in range(1, config.runs + 1) for q in questions for v in VERSIONS]
    todo = [(q, v, k) for q, v, k in planned if (q.case_id, v, k) not in ok]
    outcome = RunOutcome(out_dir=config.out_dir, results_path=None, calls_planned=len(planned),
                         calls_skipped=len(planned) - len(todo), cases=len(questions))
    print(f"{len(questions)} questions x 2 versions x {config.runs} run(s) = {len(planned)} calls"
          + (f"; {outcome.calls_skipped} already recorded, {len(todo)} to make now." if outcome.calls_skipped else "."),
          file=log)
    if not todo and previous:
        print(f"Nothing to call: every call is already recorded in {config.out_dir} (run started "
              f"{previous.get('created_at', '?')[:16].replace('T', ' ')} UTC). If your assistant has changed since "
              "then, use a new output directory.", file=log)

    started_at = now_iso()
    invocation = {"started_at": started_at, "ended_at": None, "status": "running",
                  "calls_planned": len(planned), "calls_skipped_already_recorded": outcome.calls_skipped}
    manifest = {
        "tool": "ridi-check",
        "tool_version": __version__,
        "created_at": previous.get("created_at", started_at),
        "updated_at": started_at,
        "questions_file": config.questions,
        "questions_sha256": questions_sha,
        "cases": len(questions),
        "mode": "key" if has_expected else "nokey",
        "scorer": scorer_name,
        "systems": systems,
        "runs": config.runs,
        "concurrency": config.concurrency,
        "retries": config.retries,
        "retry_wait_seconds": config.retry_wait,
        "invocations": list(previous.get("invocations", [])) + [invocation],
    }
    if config.limit is not None:
        invocation["limit"] = config.limit

    def save_manifest() -> None:
        manifest["updated_at"] = now_iso()
        atomic_write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    save_manifest()

    writer = RawWriter(raw_path)
    stop = threading.Event()
    lock = threading.Lock()
    progress = {"done": 0, "shown": time.monotonic()}

    def call(q: Question, version: str, k: int) -> dict | None:
        record = None
        for attempt in range(1, config.retries + 2):
            if stop.is_set():
                return record
            meta = {"case_id": q.case_id, "version": version, "run": k}
            record = {"case_id": q.case_id, "version": version, "run": k, "attempt": attempt,
                      "max_attempts": config.retries + 1, "status": "ok", "answer": None, "context": None,
                      "error": None, "started_at": now_iso(), "ended_at": None}
            try:
                out = adapters[version](q.question, meta)
                record["answer"], record["context"] = out["answer"], out["context"]
            except Exception as exc:  # a failed call is a result to record, not a crash
                record["status"] = "failed"
                record["error"] = f"{type(exc).__name__}: {exc}"
            record["ended_at"] = now_iso()
            writer.write(record)
            with lock:
                outcome.attempts += 1
            if record["status"] == "ok":
                return record
            if attempt <= config.retries and stop.wait(config.retry_wait * (2 ** (attempt - 1))):
                return record
        return record

    interrupted = False
    pool = ThreadPoolExecutor(max_workers=config.concurrency, thread_name_prefix="ridi-check")
    try:
        for k in range(1, config.runs + 1):
            futures = {pool.submit(call, q, v, kk): (q, v, kk) for q, v, kk in todo if kk == k}
            for future in as_completed(futures):
                q, v, kk = futures[future]
                record = future.result()
                if record is None:
                    continue
                key = (q.case_id, v, kk)
                if record["status"] == "ok":
                    ok[key] = record
                    failed.pop(key, None)
                    outcome.calls_ok += 1
                else:
                    failed[key] = record
                    outcome.calls_failed += 1
                    print(f"failed: case {q.case_id}, {v}, run {kk}, after {record['attempt']} attempt(s): "
                          f"{record['error']}", file=log)
                    if not outcome.calls_ok and outcome.calls_failed >= FAIL_FAST and not stop.is_set():
                        outcome.stopped_early = record["error"]
                        stop.set()  # a broken connection would otherwise burn through every question
                progress["done"] += 1
                if time.monotonic() - progress["shown"] >= 2 and progress["done"] < len(todo):
                    progress["shown"] = time.monotonic()
                    print(f"  {progress['done']}/{len(todo)} calls done "
                          f"(ok {outcome.calls_ok}, failed {outcome.calls_failed})", file=log)
    except KeyboardInterrupt:
        interrupted = True
        stop.set()
        print("interrupted: waiting for calls in flight; they are recorded.", file=log)
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
        writer.close()

    outcome.interrupted = interrupted
    recorded, _, _ = load_raw(raw_path)
    outcome.recorded_ok = sum(1 for q, v, k in planned if (q.case_id, v, k) in recorded)
    invocation.update({
        "ended_at": now_iso(),
        "status": "interrupted" if interrupted else (
            "stopped: the first calls all failed" if outcome.stopped_early else "completed"),
        "calls_ok": outcome.calls_ok,
        "calls_failed": outcome.calls_failed,
        "attempts": outcome.attempts,
        "calls_recorded_ok_in_total": outcome.recorded_ok,
    })
    if interrupted or outcome.stopped_early:
        save_manifest()
        return outcome

    outcome.failed = [failed[(q.case_id, v, k)] for q, v, k in planned if (q.case_id, v, k) in failed
                      and (q.case_id, v, k) not in ok]
    header, rows = build_results(questions, ok, failed, config.runs, scorer)
    atomic_write_text(results_path, to_csv(header, rows))
    outcome.results_path = results_path
    save_manifest()
    return outcome

"""Command line: ridi-check demo | init | run | report | gate.

Exit status: 0 done; 1 a gate limit was exceeded, or `run` finished with failed calls;
2 the input was not usable; 130 interrupted.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import webbrowser
from importlib import resources

from . import __version__
from .analysis import analyse
from .contract import ContractError, read_results
from .gate import evaluate
from .report import read_judgments, text_summary, write_report
from .runner import RunConfig, RunError, run

CONFIG_NAME = "ridi-check.json"
# `run` settings: name -> (type, default). The same names are the keys of ridi-check.json.
RUN_SETTINGS: dict[str, tuple[type, object]] = {
    "questions": (str, None), "current": (str, None), "proposed": (str, None), "out": (str, None),
    "runs": (int, 2), "concurrency": (int, 4), "retries": (int, 2), "retry_wait": (float, 1.0),
    "timeout": (float, None), "scorer": (str, None), "current_label": (str, ""), "proposed_label": (str, ""),
    "limit": (int, None), "report": (bool, False), "similarity": (float, 1.0), "open": (bool, False),
}
STARTER_FILES = ("questions.csv", "my_assistant.py", CONFIG_NAME, "ASK_YOUR_AI.md")
DEMO_FILES = ("questions.csv", "toy_assistant.py", CONFIG_NAME)


def _threshold(text: str) -> float:
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError("expected a number, for example 0.9") from None
    if not 0 < value <= 1:
        raise argparse.ArgumentTypeError("must be above 0 and at most 1 (1 means exact match)")
    return value


def _non_negative(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("expected a whole number") from None
    if value < 0:
        raise argparse.ArgumentTypeError("cannot be negative")
    return value


def _add_analysis_options(p: argparse.ArgumentParser) -> None:
    p.add_argument("--similarity", type=_threshold, default=1.0, metavar="X",
                   help="no-key mode: count two answers as the same when they share this fraction of their "
                        "words (Jaccard), e.g. 0.9. Default 1: exact match after normalisation.")
    p.add_argument("--mode", choices=("auto", "key", "nokey"), default="auto",
                   help="auto (default): answer-key mode when baseline_correct and updated_correct exist. "
                        "nokey: ignore the correctness columns and compare answers.")
    p.add_argument("--judgments", metavar="FILE",
                   help="no-key mode: judgments.csv with case_id and judgment (worse|better|same_meaning|unsure)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ridi-check",
        description="What did an update to your assistant change, and which changes hold on re-run? "
                    "New here? Run `ridi-check demo`, then `ridi-check init`.",
    )
    parser.add_argument("--version", action="version", version=f"ridi-check {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="{demo,init,run,report,gate}")

    p = sub.add_parser("demo", help="see a full example in under a minute: no network, no API key",
                       description="Create a folder with a small example assistant in two versions, run the "
                                   "check on it and write the report. Edit the files and run again to explore.")
    p.add_argument("dir", nargs="?", default="ridi-demo", metavar="DIR", help="folder to create (default ridi-demo)")
    p.add_argument("--open", action="store_true", help="open the report in your browser")
    p.set_defaults(handler=_cmd_demo)

    p = sub.add_parser("init", help="create a starter folder for your own assistant",
                       description="Write questions.csv, my_assistant.py, ridi-check.json and ASK_YOUR_AI.md. "
                                   "Existing files are left as they are.")
    p.add_argument("dir", nargs="?", default=".", metavar="DIR", help="folder to write into (default: here)")
    p.add_argument("--by-hand", action="store_true",
                   help="you already have the answers (e.g. in a spreadsheet): write only results_template.csv")
    p.set_defaults(handler=_cmd_init)

    p = sub.add_parser("run", help="run both versions on the same questions, more than once",
                       description="Run the current and the proposed version on every question and write "
                                   "raw_outputs.jsonl, run_manifest.json and results.csv. Run it again with the "
                                   f"same arguments to resume. Settings can live in {CONFIG_NAME} (see `init`); "
                                   "options given here win.")
    p.add_argument("--config", metavar="FILE",
                   help=f"settings file (default: {CONFIG_NAME} in this folder, if it exists). "
                        "Paths in it are relative to its folder.")
    p.add_argument("--questions", metavar="FILE", help="CSV or JSONL with case_id, question and optionally expected")
    p.add_argument("--current", metavar="SYSTEM",
                   help="the current version: python:module:function, command:<shell command>, an http(s) URL, "
                        "or a JSON definition file")
    p.add_argument("--proposed", metavar="SYSTEM", help="the proposed version, same forms")
    p.add_argument("--out", metavar="DIR", help="output directory")
    p.add_argument("--runs", type=int, metavar="N", help="runs per version (default 2, minimum 1)")
    p.add_argument("--limit", type=int, metavar="N",
                   help="use only the first N questions: a cheap first try. Run again without it to do the rest.")
    p.add_argument("--concurrency", type=int, metavar="N", help="calls in flight at once (default 4)")
    p.add_argument("--retries", type=_non_negative, metavar="N", help="extra attempts after a failed call (default 2)")
    p.add_argument("--retry-wait", type=float, metavar="SECONDS",
                   help="wait before the first retry; doubles each time (default 1)")
    p.add_argument("--timeout", type=float, metavar="SECONDS", help="limit for one command or http call (default 120)")
    p.add_argument("--scorer", metavar="MODULE:FUNCTION",
                   help="scorer(answer, expected) -> true when correct. Default: normalised exact match.")
    p.add_argument("--current-label", metavar="TEXT", help="free text shown in the report")
    p.add_argument("--proposed-label", metavar="TEXT", help="free text shown in the report")
    p.add_argument("--report", action="store_true", default=None,
                   help="also write summary.json, review_cases.csv and report.html")
    p.add_argument("--similarity", type=_threshold, metavar="X", help="with --report: see `report --help`")
    p.add_argument("--open", action="store_true", default=None, help="with --report: open it in your browser")
    p.set_defaults(handler=_cmd_run)

    p = sub.add_parser("report", help="write summary.json, review_cases.csv and report.html from a results.csv",
                       description="Read a results.csv (from `run`, or made by hand) and write the report files.")
    p.add_argument("results", metavar="RESULTS.csv")
    p.add_argument("--out", metavar="DIR", help="where to write (default: next to the results file)")
    _add_analysis_options(p)
    p.add_argument("--current-label", default=None, metavar="TEXT")
    p.add_argument("--proposed-label", default=None, metavar="TEXT")
    p.add_argument("--lang", choices=("en", "ar"), default=None, help="language the report opens in")
    p.add_argument("--open", action="store_true", help="open the report in your browser")
    p.set_defaults(handler=_cmd_report)

    p = sub.add_parser("gate", help="exit non-zero when stable regressions exceed a limit",
                       description="Print counts and one line per offending case. Exit 1 when a limit is exceeded.")
    p.add_argument("results", metavar="RESULTS.csv")
    p.add_argument("--max-stable-regressions", type=_non_negative, default=0, metavar="N",
                   help="answer-key mode: stable regressions allowed. No-key mode: stable changes the owner "
                        "judged worse. Default 0.")
    p.add_argument("--max-unjudged-changes", type=_non_negative, default=0, metavar="N",
                   help="no-key mode: stable changes allowed with no judgment, or judged unsure. Default 0.")
    p.add_argument("--max-incomplete", type=_non_negative, default=0, metavar="N",
                   help="cases allowed that could not be compared because a call failed. Default 0.")
    _add_analysis_options(p)
    p.set_defaults(handler=_cmd_gate)
    return parser


# ---------- settings file ----------

def _load_settings(args: argparse.Namespace) -> None:
    """Fill unset `run` options from ridi-check.json, then from the defaults."""
    path = args.config or (CONFIG_NAME if os.path.isfile(CONFIG_NAME) else None)
    settings: dict = {}
    if path:
        try:
            with open(path, encoding="utf-8") as f:
                settings = json.load(f)
        except OSError as exc:
            raise RunError(f"The settings file could not be read: {exc}") from exc
        except ValueError as exc:
            raise RunError(f"{path} is not valid JSON: {exc}") from exc
        if not isinstance(settings, dict):
            raise RunError(f"{path} must hold one JSON object.")
        for key, value in settings.items():
            if key not in RUN_SETTINGS:
                raise RunError(f"{path}: unknown setting {key!r}. Known settings: {', '.join(RUN_SETTINGS)}.")
            kind = RUN_SETTINGS[key][0]
            good = (isinstance(value, (int, float)) and not isinstance(value, bool)) if kind is float else (
                isinstance(value, kind) and not (kind is int and isinstance(value, bool)))
            if value is not None and not good:
                raise RunError(f"{path}: {key!r} must be {'a number' if kind in (int, float) else kind.__name__}.")
        folder = os.path.dirname(os.path.abspath(path))
        if folder != os.getcwd():
            os.chdir(folder)  # paths and python: modules in the file are relative to the file
    for key, (kind, default) in RUN_SETTINGS.items():
        if getattr(args, key, None) is None:
            value = settings.get(key)
            setattr(args, key, default if value is None else (float(value) if kind is float else value))
    missing = [f"--{key}" for key in ("questions", "current", "proposed", "out") if not getattr(args, key)]
    if missing:
        raise RunError(
            f"Missing {', '.join(missing)}. Give them on the command line or in {CONFIG_NAME}. "
            "`ridi-check init` writes a starter folder with that file."
        )
    if not 0 < args.similarity <= 1:
        raise RunError("similarity must be above 0 and at most 1.")


# ---------- commands ----------

def _open(path: str) -> None:
    try:
        webbrowser.open("file://" + os.path.abspath(path))
    except Exception:  # no browser here: the path was printed, nothing else to do
        pass


def _print_report(results_path: str, similarity: float, open_it: bool = False, **extra) -> None:
    summary, paths, _, warnings = write_report(results_path, threshold=similarity, **extra)
    for warning in warnings:
        print(f"note: {warning}", file=sys.stderr)
    print(text_summary(summary))
    print("Wrote: " + ", ".join(paths.values()))
    print(f"Open the report: {os.path.abspath(paths['report.html'])}")
    if open_it:
        _open(paths["report.html"])


def _copy_templates(package_dir: str, names: tuple[str, ...], target: str) -> tuple[list[str], list[str]]:
    os.makedirs(target, exist_ok=True)
    written, kept = [], []
    for name in names:
        destination = os.path.join(target, name)
        if os.path.exists(destination):
            kept.append(name)
            continue
        data = resources.files("ridi_check").joinpath(package_dir, name).read_bytes()
        with open(destination, "wb") as f:
            f.write(data)
        written.append(name)
    return written, kept


def _cmd_init(args: argparse.Namespace) -> int:
    names = ("results_template.csv",) if args.by_hand else STARTER_FILES
    written, kept = _copy_templates("starter", names, args.dir)
    where = os.path.abspath(args.dir)
    if written:
        print(f"Wrote in {where}: {', '.join(written)}")
    if kept:
        print(f"Already there, left as they are: {', '.join(kept)}")
    go = "" if os.path.abspath(args.dir) == os.getcwd() else f"cd {args.dir}, then "
    if args.by_hand:
        print("Next:\n"
              "  1. Put your answers in results_template.csv: one row per question, the current version in\n"
              "     the baseline_ columns, the proposed version in the updated_ columns, a second run of\n"
              "     each in the _repeat_ columns.\n"
              f"  2. {go}ridi-check report results_template.csv --open")
    else:
        print("Next:\n"
              "  1. Put your own questions in questions.csv.\n"
              "  2. Open my_assistant.py and make ask() call your assistant.\n"
              "     Or paste ASK_YOUR_AI.md into your AI coding assistant and let it do this step.\n"
              f"  3. {go}ridi-check run --limit 5     (a first try on five questions)\n"
              "  4. ridi-check run               (all questions; the report is written at the end)")
    return 0


def _cmd_demo(args: argparse.Namespace) -> int:
    written, _ = _copy_templates("demo", DEMO_FILES, args.dir)
    if written:
        print(f"Wrote in {os.path.abspath(args.dir)}: {', '.join(written)}")
    run_args = build_parser().parse_args(["run", "--config", os.path.join(args.dir, CONFIG_NAME)])
    run_args.open = True if args.open else None
    status = _cmd_run(run_args)
    print("\nThis was a toy assistant about a made-up library handbook; all of its data is synthetic. Its proposed version splits the\n"
          "handbook differently, which cuts some sentences in half, and it does not always retrieve the\n"
          "same passages. Open the report to see which answers changed and which changes held on re-run.\n"
          "For your own assistant: ridi-check init")
    return status


def _cmd_run(args: argparse.Namespace) -> int:
    _load_settings(args)
    config = RunConfig(
        questions=args.questions, current=args.current, proposed=args.proposed, out_dir=args.out,
        runs=args.runs, concurrency=args.concurrency, retries=args.retries, retry_wait=args.retry_wait,
        timeout=args.timeout, scorer=args.scorer, current_label=args.current_label,
        proposed_label=args.proposed_label, limit=args.limit,
    )
    outcome = run(config)
    raw = os.path.join(args.out, "raw_outputs.jsonl")
    if outcome.interrupted:
        print(f"Interrupted: {outcome.recorded_ok} of {outcome.calls_planned} calls are recorded in {raw}. "
              "Run the same command again to resume.", file=sys.stderr)
        return 130
    if outcome.stopped_early:
        print(f"Stopped: the first {outcome.calls_failed} calls all failed, so the connection to your assistant "
              f"is probably not working yet.\n  Last error: {outcome.stopped_early}\n"
              f"Fix it and run the same command again. Every attempt is recorded in {raw}.", file=sys.stderr)
        return 2
    print(f"Calls: {outcome.calls_planned} planned, {outcome.calls_skipped} already recorded, "
          f"{outcome.calls_ok} succeeded, {outcome.calls_failed} failed ({outcome.attempts} attempts).")
    print(f"Wrote: {outcome.results_path}")
    if args.report:
        _print_report(outcome.results_path, args.similarity, bool(args.open))
    if args.limit:
        print(f"This was a first try on {outcome.cases} question(s). Run again without --limit for all of them; "
              "the answers recorded now are reused.")
    if outcome.failed:
        print(f"{len(outcome.failed)} call(s) failed and are recorded as failed. "
              "Run the same command again to retry only those.", file=sys.stderr)
        return 1
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    _print_report(args.results, args.similarity, args.open, out_dir=args.out, mode=args.mode,
                  judgments_path=args.judgments, current_label=args.current_label,
                  proposed_label=args.proposed_label, lang=args.lang)
    return 0


def _cmd_gate(args: argparse.Namespace) -> int:
    cases, mode = read_results(args.results, args.mode)
    analysis = analyse(cases, mode, args.similarity)
    judgments = {}
    if args.judgments:
        judgments = read_judgments(args.judgments, {c.case_id for c in cases})
        if mode == "key":
            print("note: --judgments is not used in answer-key mode; the answer key decides.", file=sys.stderr)
    result = evaluate(
        analysis, judgments, max_stable_regressions=args.max_stable_regressions,
        max_unjudged_changes=args.max_unjudged_changes, max_incomplete=args.max_incomplete,
    )
    print(f"ridi-check gate: {args.results}, {len(cases)} cases, "
          f"{'answer-key mode' if mode == 'key' else 'no answer key'}")
    print("\n".join(result.lines))
    for note in result.notes:
        print(note, file=sys.stderr)
    return 1 if result.exceeded else 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except (ContractError, RunError) as exc:
        print(f"ridi-check: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("ridi-check: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())

"""`ridi-check report`: summary.json, review_cases.csv and one self-contained report.html."""

from __future__ import annotations

import json
import os
from importlib import resources

from . import __version__
from .analysis import (
    CORRECT_BOTH, INCOMPLETE, STABLE_CHANGE, STABLE_REGRESSION, UNCHANGED_STATES, WRONG_BOTH, Analysis, analyse, duplicate_note,
    duplicate_questions,
    same_answer,
)
from .contract import (
    CONTEXT_SEPARATOR, KEY, NOKEY, Case, ContractError, read_records, read_results, run_column, to_csv,
)
from .strings import strings_for
from .util import atomic_write_text, now_iso, read_text, sha256_file

SUMMARY = "summary.json"
REVIEW_CASES = "review_cases.csv"
REPORT_HTML = "report.html"
JUDGMENTS = ("worse", "better", "same_meaning", "unsure")
NOTHING_CORRECT = (
    "No answer was scored correct in either version, so the scoring probably does not fit the answers. "
    "Exact match rarely fits free text: check the expected answers, pass a scorer, or use --mode nokey "
    "to compare the answers themselves."
)


def read_judgments(path: str, case_ids: set[str]) -> dict[str, str]:
    """judgments.csv: case_id, judgment in worse|better|same_meaning|unsure. Says which row is wrong."""
    try:
        records = read_records(read_text(path, "The judgments file"))
    except ValueError as exc:
        raise ContractError(str(exc)) from exc
    if not records:
        raise ContractError("The judgments file is empty.")
    header = [h.strip().lower() for h in records[0][1]]
    if "case_id" not in header or "judgment" not in header:
        raise ContractError("The judgments file needs case_id and judgment columns.")
    i_id, i_j = header.index("case_id"), header.index("judgment")
    out: dict[str, str] = {}
    for row, record in records[1:]:
        case_id = record[i_id].strip() if i_id < len(record) else ""
        judgment = record[i_j].strip().lower() if i_j < len(record) else ""
        if not case_id:
            raise ContractError(f"Judgments row {row}: case_id is missing.")
        if case_id in out:
            raise ContractError(f"Judgments row {row}: case_id {case_id!r} appears more than once.")
        if case_id not in case_ids:
            raise ContractError(f"Judgments row {row}: case_id {case_id!r} is not in the results file.")
        if judgment == "":
            continue  # left blank: not judged yet
        if judgment not in JUDGMENTS:
            raise ContractError(
                f"Judgments row {row} (case {case_id}): judgment must be one of {', '.join(JUDGMENTS)}; got {judgment!r}."
            )
        out[case_id] = judgment
    return out


def _rate(count: int, n: int) -> dict | None:
    if not n:
        return None
    return {"count": count, "n": n, "rate": round(count / n, 6)}


def build_summary(a: Analysis, judgments: dict[str, str] | None = None) -> dict:
    """The counts and rates. Rates use first runs; both re-run variations are always reported."""
    key = a.mode == KEY
    change = _rate(a.changed, a.n_compared) or {"count": 0, "n": 0, "rate": 0.0}
    rerun_b, rerun_u = _rate(a.rerun_b, a.rerun_b_n), _rate(a.rerun_u, a.rerun_u_n)
    exceeds = None
    if rerun_b and rerun_u:
        exceeds = change["rate"] > max(rerun_b["rate"], rerun_u["rate"])
    first_run: dict = {
        "change_between_versions": change,
        "rerun_variation_current": rerun_b,
        "rerun_variation_proposed": rerun_u,
        "change_exceeds_both_rerun_variations": exceeds,
    }
    if key:
        first_run.update({
            "accuracy_current": _rate(a.correct_b, a.n_compared),
            "accuracy_proposed": _rate(a.correct_u, a.n_compared),
            "regressions": a.regressions,
            "improvements": a.improvements,
            # changed = visible + cancelled: the mean moves by |I - R|; 2 min(R, I) changes offset each other
            "changes_visible_in_mean_accuracy": abs(a.improvements - a.regressions),
            "changes_cancelled_in_mean_accuracy": 2 * min(a.regressions, a.improvements),
        })
    summary: dict = {
        "tool": "ridi-check",
        "tool_version": __version__,
        "mode": a.mode,
        "equality": "equal correctness" if key else (
            "equal answers after normalisation" if a.threshold >= 1
            else f"equal after normalisation, or word overlap (Jaccard) >= {a.threshold:g} "
                 "with the same negation words and numbers"
        ),
        "similarity_threshold": a.threshold,
        "cases": a.n,
        "cases_compared": a.n_compared,
        "confirmable_cases": a.confirmable,
        "runs_per_version": {"current": a.max_runs_b, "proposed": a.max_runs_u},
        "states": dict(a.counts),
        "case_ids": {s: a.ids(s) for s in a.counts if s not in UNCHANGED_STATES},
        "first_run": first_run,
        "any_run_disagreement": {"current": a.any_run_b, "proposed": a.any_run_u},
    }
    listed = [(c, s) for c, s in a.items if s != INCOMPLETE and (c.baseline_context or c.updated_context)]
    if listed:      # a count of where the retrieved passages differ; it says nothing about cause
        differs = [(s, any(passage_difference(c)[:2])) for c, s in listed]
        summary["passages"] = {
            "cases_with_passages": len(listed),
            "differ": sum(d for _, d in differs),
            "by_state": {state: {"differ": sum(d for s, d in differs if s == state),
                                 "n": sum(1 for s, _ in differs if s == state)}
                         for state in a.counts if any(s == state for s, _ in differs)},
        }
    if key:
        state_of = {case.case_id: state for case, state in a.items}
        for name, state in (("wrong_both_answer_changed", WRONG_BOTH), ("correct_both_answer_changed", CORRECT_BOTH)):
            summary[name] = {
                flag: [i for i, f in a.answer_change.items() if f == flag and state_of[i] == state]
                for flag in ("stable", "unconfirmed")
            }
    else:
        judgments = judgments or {}
        stable = a.ids(STABLE_CHANGE)
        counts = {j: sum(1 for i in stable if judgments.get(i) == j) for j in JUDGMENTS}
        counts["unjudged"] = sum(1 for i in stable if i not in judgments)
        summary["judgments"] = {
            "of_stable_changes": counts,
            "still_to_decide": counts["unjudged"] + counts["unsure"],
            "ignored_not_a_stable_change": sorted(i for i in judgments if i not in set(stable)),
        }
    notes = []
    if exceeds is None:
        notes.append("No second run of both versions: re-run variation is unknown and no change is confirmed.")
    elif not exceeds:
        notes.append(
            "The change between versions is not larger than the larger of the two re-run variations. "
            "Read the stable cases, not the total."
        )
    notes.append(
        '"Stable" needs at least two runs of both versions. Two runs is a thin estimate of re-run variation.'
    )
    if key and a.n_compared >= 3 and not a.correct_b and not a.correct_u:
        notes.append(NOTHING_CORRECT)
    if a.counts.get(INCOMPLETE):
        notes.append(f"{a.counts[INCOMPLETE]} case(s) were not compared because a first-run call failed.")
    notes.append("This check finds change, not correctness. It does not say that a system is fit to deploy.")
    summary["notes"] = notes
    return summary


def review_table(a: Analysis, judgments: dict[str, str] | None = None) -> tuple[list[str], list[list[str]]]:
    """Every case that is not same / correct in both, with all of its runs.

    The run columns keep their contract names, so this file can be read back by `report`.
    """
    key = a.mode == KEY
    judgments = judgments or {}
    cases = [c for c, _ in a.items]
    runs_b = max((len(c.baseline) for c in cases), default=0) or 1
    runs_u = max((len(c.updated) for c in cases), default=0) or 1
    has = lambda attr: any(getattr(c, attr) for c in cases)  # noqa: E731
    any_answer = any(r.answer for c in cases for r in c.baseline + c.updated)
    header = ["case_id", "state"] + (["answer_change"] if key else ["judgment"])
    header += (["question"] if has("question") else []) + (["expected"] if has("expected") else [])
    sides = (("baseline", runs_b), ("updated", runs_u))
    if any_answer or not key:
        header += [run_column(side, k, "answer") for side, n in sides for k in range(1, n + 1)]
    if key:
        header += [run_column(side, k, "correct") for side, n in sides for k in range(1, n + 1)]
    with_context = has("baseline_context") or has("updated_context")
    if with_context:
        header += ["baseline_context", "updated_context", "passages_only_current", "passages_only_proposed"]
    if has("run_errors"):
        header += ["run_errors"]

    rows = []
    for case, state in a.items:
        if state in UNCHANGED_STATES and case.case_id not in a.answer_change:
            continue
        row = [case.case_id, state, a.answer_change.get(case.case_id, "") if key else judgments.get(case.case_id, "")]
        if "question" in header:
            row.append(case.question)
        if "expected" in header:
            row.append(case.expected)
        runs = {"baseline": case.baseline, "updated": case.updated}
        if any_answer or not key:
            for side, n in sides:
                row += [runs[side][k].answer if k < len(runs[side]) else "" for k in range(n)]
        if key:
            for side, n in sides:
                row += [
                    str(runs[side][k].correct) if k < len(runs[side]) and runs[side][k].correct is not None else ""
                    for k in range(n)
                ]
        if with_context:
            only_b, only_u, _ = passage_difference(case)
            row += [CONTEXT_SEPARATOR.join(case.baseline_context), CONTEXT_SEPARATOR.join(case.updated_context),
                    CONTEXT_SEPARATOR.join(only_b), CONTEXT_SEPARATOR.join(only_u)]
        if "run_errors" in header:
            row.append(case.run_errors)
        rows.append(row)
    return header, rows


def passage_difference(case: Case) -> tuple[list[str], list[str], int]:
    """(only in the current version, only in the proposed version, number in both). No interpretation."""
    in_b, in_u = set(case.baseline_context), set(case.updated_context)
    only_b = [p for p in case.baseline_context if p not in in_u]
    only_u = [p for p in case.updated_context if p not in in_b]
    return only_b, only_u, len(case.baseline_context) - len(only_b)


CSS_CLASS = {
    "stable_regression": "s-reg", "regression_unconfirmed": "s-reg",
    "stable_improvement": "s-imp", "improvement_unconfirmed": "s-imp",
    "stable_change": "s-chg", "change_unconfirmed": "s-chg",
    "unstable": "s-uns", "wrong_both": "s-wrong", "correct_both": "s-ok", "same": "s-ok", "incomplete": "s-inc",
}


def ledger_tiles(a: Analysis) -> list[str]:
    """Which state tiles the ledger shows, in order.

    Stable tiles are hidden only when no case has two runs of both versions, where a zero would
    read as a finding. Unconfirmed and incomplete tiles appear only when they have cases.
    """
    count = a.counts.get
    if a.mode == KEY:
        stable, unconfirmed = ["stable_regression", "stable_improvement"], ["regression_unconfirmed",
                                                                            "improvement_unconfirmed"]
        rest = ["unstable", "wrong_both", "correct_both"]
    else:
        stable, unconfirmed, rest = ["stable_change"], ["change_unconfirmed"], ["unstable", "same"]
    any_unconfirmed = any(count(s, 0) for s in unconfirmed)
    tiles = (stable if a.confirmable or not any_unconfirmed else []) + (unconfirmed if any_unconfirmed else [])
    return tiles + rest + ([INCOMPLETE] if count(INCOMPLETE, 0) else [])


def _runs_for_page(runs, key: bool, threshold: float) -> list[dict]:
    out = []
    for i, r in enumerate(runs):
        first = runs[0]
        if key:
            same = r.correct == first.correct and (
                not r.answer or not first.answer or same_answer(r.answer, first.answer, threshold)
            )
        else:
            same = same_answer(r.answer, first.answer, threshold)
        out.append({"ans": r.answer, "cor": r.correct, "same": bool(same) if i else True})
    return out


def page_data(
    a: Analysis, summary: dict, judgments: dict[str, str], *, file_name: str, report_id: str,
    labels: dict[str, str], lang: str | None, generated: str,
) -> dict:
    key = a.mode == KEY
    # Cases that are correct in both versions and whose answer changed get a card as well. Their cards come
    # after all the others, so that they never bury a case whose score changed.
    cards, late, strip, wrong = [], [], [], []
    for case, state in a.items:
        flag = a.answer_change.get(case.case_id)
        if (state not in UNCHANGED_STATES and (state != WRONG_BOTH or flag)) or (state == CORRECT_BOTH and flag):
            only_b, only_u, kept = passage_difference(case)
            (late if state == CORRECT_BOTH else cards).append({
                "id": case.case_id, "state": state, "flag": flag, "q": case.question, "expected": case.expected,
                "b": _runs_for_page(case.baseline, key, a.threshold),
                "u": _runs_for_page(case.updated, key, a.threshold),
                "rem": only_b, "add": only_u, "kept": kept, "err": case.run_errors,
            })
        strip.append([case.case_id, state, -1])
        if state == WRONG_BOTH:
            wrong.append([case.case_id, case.question, flag])
    cards += late
    position = {card["id"]: i for i, card in enumerate(cards)}
    for cell in strip:
        cell[2] = position.get(cell[0], -1)
    stable_changes = a.ids(STABLE_CHANGE)
    return {
        "meta": {
            "mode": a.mode, "threshold": a.threshold, "n": a.n, "file": file_name, "generated": generated,
            "tool_version": __version__, "report_id": report_id, "labels": labels, "lang": lang,
        },
        "summary": summary,
        "tiles": ledger_tiles(a),
        "acc": {"a": a.correct_b, "b": a.correct_u, "n": a.n_compared, "r": a.regressions, "i": a.improvements}
        if key and a.n_compared else None,
        "classes": {state: CSS_CLASS[state] for state in a.counts},
        "strip": strip,
        "cards": cards,
        "wrong": wrong,
        "focus": STABLE_REGRESSION if key else STABLE_CHANGE,    # the state the passage count is also given for
        "stable_change_ids": stable_changes,
        "judgments": {i: j for i, j in judgments.items() if i in set(stable_changes)},
        "strings": strings_for(a.mode),
    }


def render_html(data: dict) -> str:
    template = resources.files("ridi_check").joinpath("report_template.html").read_text(encoding="utf-8")
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    # Safe inside a <script> block whatever the answers contain.
    blob = blob.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    blob = blob.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return template.replace("__RIDI_DATA__", blob)


def labels_from_manifest(results_path: str) -> dict[str, str]:
    """Version labels recorded by `run`, if results.csv sits next to its run_manifest.json."""
    path = os.path.join(os.path.dirname(os.path.abspath(results_path)), "run_manifest.json")
    try:
        with open(path, encoding="utf-8") as f:
            systems = json.load(f).get("systems", {})
        return {v: str((systems.get(v) or {}).get("label") or "") for v in ("current", "proposed")}
    except (OSError, ValueError, AttributeError):
        return {"current": "", "proposed": ""}


def write_report(
    results_path: str, out_dir: str | None = None, *, mode: str = "auto", threshold: float = 1.0,
    judgments_path: str | None = None, current_label: str | None = None, proposed_label: str | None = None,
    lang: str | None = None,
) -> tuple[dict, dict[str, str], Analysis, list[str]]:
    """Returns (summary, written paths, analysis, warnings)."""
    cases, resolved = read_results(results_path, mode)
    a = analyse(cases, resolved, threshold)
    warnings: list[str] = []
    judgments: dict[str, str] = {}
    if judgments_path:
        judgments = read_judgments(judgments_path, {c.case_id for c in cases})
        if resolved == KEY:
            warnings.append("--judgments is not used in answer-key mode; the answer key decides.")
            judgments = {}
    summary = build_summary(a, judgments)
    repeated = duplicate_questions([(c.case_id, c.question) for c in cases])
    if repeated:
        warnings.append(duplicate_note(repeated))
    if resolved != KEY:
        ignored = summary["judgments"]["ignored_not_a_stable_change"]
        if ignored:
            warnings.append(
                f"{len(ignored)} judgment(s) are for cases that are not stable changes and were not counted: "
                + ", ".join(ignored)
            )
        if mode == NOKEY:
            warnings.append(
                "Read without an answer key because --mode nokey was given. Correctness columns, if the file "
                "has them, were left out on purpose."
            )
        elif any(c.expected for c in cases):
            warnings.append(
                "The file has an expected column but no baseline_correct / updated_correct columns, "
                "so it was read without an answer key."
            )

    out_dir = out_dir or os.path.dirname(os.path.abspath(results_path))
    os.makedirs(out_dir, exist_ok=True)
    labels = labels_from_manifest(results_path)
    if current_label is not None:
        labels["current"] = current_label
    if proposed_label is not None:
        labels["proposed"] = proposed_label
    generated = now_iso()[:16].replace("T", " ") + " UTC"
    summary = {"results_file": os.path.basename(results_path), "results_sha256": sha256_file(results_path),
               "generated_at": generated, "labels": labels, **summary}

    paths = {name: os.path.join(out_dir, name) for name in (SUMMARY, REVIEW_CASES, REPORT_HTML)}
    atomic_write_text(paths[SUMMARY], json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    header, rows = review_table(a, judgments)
    atomic_write_text(paths[REVIEW_CASES], to_csv(header, rows))
    data = page_data(a, summary, judgments, file_name=os.path.basename(results_path),
                     report_id=summary["results_sha256"][:12], labels=labels, lang=lang, generated=generated)
    atomic_write_text(paths[REPORT_HTML], render_html(data))
    return summary, paths, a, warnings


def text_summary(summary: dict) -> str:
    """What `report` prints. Counts and the reading rules; no verdict."""
    key = summary["mode"] == KEY
    lines = [f"{summary['cases']} case{'' if summary['cases'] == 1 else 's'}, "
             f"{'answer-key mode' if key else 'no answer key'} ({summary['equality']})"]
    for state, count in summary["states"].items():
        if not count and (state.endswith("_unconfirmed") or state == INCOMPLETE):
            continue
        ids = summary["case_ids"].get(state, [])
        shown = ""
        if ids and state != WRONG_BOTH:
            shown = "   cases: " + ", ".join(ids[:20]) + (f", and {len(ids) - 20} more" if len(ids) > 20 else "")
        lines.append(f"  {state:<26}{count:>5}{shown}")
    f = summary["first_run"]

    def show(r: dict | None) -> str:
        return "no second run" if r is None else f"{r['count']}/{r['n']} ({100 * r['rate']:.1f}%)"

    lines.append(
        f"First run: change between versions {show(f['change_between_versions'])}; re-run variation: "
        f"current {show(f['rerun_variation_current'])}, proposed {show(f['rerun_variation_proposed'])}."
    )
    if key:
        acc_b, acc_u = f["accuracy_current"], f["accuracy_proposed"]
        if acc_b and acc_u:
            lines.append(
                f"First run accuracy: {acc_b['count']}/{acc_b['n']} to {acc_u['count']}/{acc_u['n']}; "
                f"regressions {f['regressions']}, improvements {f['improvements']}."
            )
            if f["changes_cancelled_in_mean_accuracy"]:
                lines.append(
                    f"Of the {f['regressions'] + f['improvements']} answers that changed on the first run, mean "
                    f"accuracy shows {f['changes_visible_in_mean_accuracy']}; the other "
                    f"{f['changes_cancelled_in_mean_accuracy']} cancel out, regressions against improvements."
                )
        changed = summary["wrong_both_answer_changed"]
        if changed["stable"] or changed["unconfirmed"]:
            ids = changed["stable"] + [f"{i} (not re-run)" for i in changed["unconfirmed"]]
            lines.append(
                "Wrong in both versions but with a changed answer: "
                + ", ".join(ids[:20]) + (f", and {len(ids) - 20} more" if len(ids) > 20 else "")
                + ". Correctness counting does not see these."
            )
        changed = summary["correct_both_answer_changed"]
        if changed["stable"] or changed["unconfirmed"]:
            ids = changed["stable"] + [f"{i} (not re-run)" for i in changed["unconfirmed"]]
            lines.append(
                "Correct in both versions but with a changed answer: "
                + ", ".join(ids[:20]) + (f", and {len(ids) - 20} more" if len(ids) > 20 else "")
                + ". The answer key scores both answers as correct; read them if the wording matters."
            )
    else:
        j = summary["judgments"]["of_stable_changes"]
        lines.append(
            f"Stable changes judged: {j['worse']} worse, {j['better']} better, {j['same_meaning']} same meaning, "
            f"{summary['judgments']['still_to_decide']} still to decide."
        )
    passages = summary.get("passages")
    if passages:
        lines.append(
            f"Retrieved passages differ between the versions in {passages['differ']}/{passages['cases_with_passages']} "
            "cases that list passages: "
            + ", ".join(f"{state} {v['differ']}/{v['n']}" for state, v in passages["by_state"].items())
            + ". This is a count, not a cause."
        )
    lines += summary["notes"]
    return "\n".join(lines)

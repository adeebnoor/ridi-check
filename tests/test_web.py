"""The browser version (web/) must agree with the Python on every file: states, rates, review export
and which row is rejected. The JavaScript runs in Node; the parity tests are skipped without it."""

import importlib.util
import json
import os
import random
import re
import shutil
import subprocess

import pytest

from ridi_check.analysis import analyse
from ridi_check.contract import ContractError, parse_results, run_column, to_csv
from ridi_check.report import build_summary, review_table

from conftest import FIXTURE, ROOT

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="Node.js is not installed")

RUNNER = r"""
const fs = require('fs'), core = require(process.argv[2]);
const out = [];
for (const job of JSON.parse(fs.readFileSync(process.argv[3], 'utf8'))) {
  try {
    const r = core.parseResults(job.text, job.mode), a = core.analyse(r.cases, r.mode, job.sim);
    const s = core.buildSummary(a), review = core.reviewTable(a, {});
    out.push({ mode: r.mode, states: a.items.map((it) => [it.c.id, it.s]), counts: a.counts, first: s.first_run,
      any: s.any_run_disagreement, runs: s.runs_per_version, confirmable: s.confirmable_cases, compared: s.cases_compared,
      changed: s.wrong_both_answer_changed || null, review: core.toCsv(review.header, review.rows), tiles: core.pageData(a).tiles });
  } catch (e) { if (!e.code) throw e; out.push({ error: e.code, row: e.info.row || null }); }
}
fs.writeFileSync(process.argv[4], JSON.stringify(out));
"""

ERRORS = [
    (r"No rows found", "empty"), (r"needs a case_id column", "noId"), (r"^Column .* appears more than once", "dupColumn"),
    (r"name the same run", "sameRun"), (r"repeat numbers start at 1", "repeatZero"),
    (r"^The file needs baseline_correct", "needCols"), (r"Answer-key mode needs", "needKey"), (r"No-key mode needs", "needAnswers"),
    (r"case_id is missing", "rowNoId"), (r"case_id .* appears more than once", "rowDup"), (r"must be 0 or 1, got", "rowBin"),
    (r"has a value but", "rowNoCorrect"), (r" is empty\.", "rowEmptyFirst"),
]


def python_side(text, mode, sim):
    try:
        cases, resolved = parse_results(text, mode)
    except ContractError as exc:
        message = str(exc)
        code = next(code for pattern, code in ERRORS if re.search(pattern, message))
        row = re.match(r"Row (\d+)", message)
        return {"error": code, "row": int(row.group(1)) if row else None}
    a = analyse(cases, resolved, sim)
    s = build_summary(a)
    header, rows = review_table(a)

    def bare(r):
        return None if r is None else {"count": r["count"], "n": r["n"]}

    first = {k: (bare(v) if isinstance(v, dict) or v is None else v) for k, v in s["first_run"].items()
             if k != "change_exceeds_both_rerun_variations"}
    from ridi_check.report import ledger_tiles
    return {"mode": resolved, "states": [[c.case_id, st] for c, st in a.items], "counts": a.counts, "first": first,
            "any": s["any_run_disagreement"], "runs": s["runs_per_version"], "confirmable": s["confirmable_cases"],
            "compared": s["cases_compared"], "changed": s.get("wrong_both_answer_changed"),
            "review": to_csv(header, rows), "tiles": ledger_tiles(a)}


WORDS = ["yes", "Yes.", "no", "NOT_ENOUGH_INFO", "not enough info", "نعم", "نعم.", "كلا", "Paris, France", "paris france",
         'say "hi"', "a;b", "tab\there", "two\nlines", " padded ", "x-ray", "=1+1", "'quoted'", "100%", "٣ أيام"]
SENTENCES = ["the loan period is 21 days for every book in the library", "the loan period is 14 days for every book in the library",
             "the loan period is not 21 days for every book in the library", "the loan period is 21 days for each book in the library",
             "لا يُسمح بالطعام في غرف الدراسة أبداً", "يُسمح بالطعام في غرف الدراسة أبداً", "the fee is ten pounds", "the fee is ten pounds today"]


def random_job(rng):
    key = rng.random() < 0.5
    fuzzy = not key and rng.random() < 0.4
    runs_b, runs_u = rng.randint(1, 4), rng.randint(1, 4)
    with_answers = not key or rng.random() < 0.7
    header = ["case_id"] + (["question"] if rng.random() < 0.5 else []) + (["expected"] if rng.random() < 0.3 else [])
    if with_answers:
        header += [run_column("baseline", k, "answer") for k in range(1, runs_b + 1)]
        header += [run_column("updated", k, "answer") for k in range(1, runs_u + 1)]
    if key:
        header += [run_column("baseline", k, "correct") for k in range(1, runs_b + 1)]
        header += [run_column("updated", k, "correct") for k in range(1, runs_u + 1)]
    context = rng.random() < 0.3
    errors = rng.random() < 0.2
    header += (["baseline_context", "updated_context"] if context else []) + (["run_errors"] if errors else [])
    tail = header[1:]
    rng.shuffle(tail)
    header = ["case_id"] + tail
    pool = SENTENCES if fuzzy else WORDS
    noise = rng.choice([0, 0.1, 0.4])
    rows = []
    for i in range(rng.randint(1, 40)):
        row = {"case_id": f"c{i}", "question": rng.choice(["why?", "كيف؟", "", "a, b"]), "expected": rng.choice(["x", ""]),
               "baseline_context": " | ".join(rng.sample(["p1", "p2", "p3", "p4"], rng.randint(0, 3))),
               "updated_context": " | ".join(rng.sample(["p1", "p2", "p3", "p4"], rng.randint(0, 3))),
               "run_errors": "current#1: TimeoutError" if errors and rng.random() < 0.2 else ""}
        for side, n in (("baseline", runs_b), ("updated", runs_u)):
            have = n if rng.random() < 0.8 else rng.randint(1, n)
            lost_first = row["run_errors"] and rng.random() < 0.5
            answer, correct = rng.choice(pool), rng.randint(0, 1)
            for k in range(1, n + 1):
                flip = rng.random() < noise
                present = k <= have and not (k == 1 and lost_first)
                row[run_column(side, k, "answer")] = (rng.choice(pool) if flip else answer) if present else ""
                row[run_column(side, k, "correct")] = str(correct ^ flip) if present else ""
        rows.append([row[name] for name in header])

    fault = rng.random()
    if fault < 0.04:
        rows.append(list(rows[0]))                                          # duplicate case_id
    elif fault < 0.08:
        rows[rng.randrange(len(rows))][0] = ""                              # missing case_id
    elif fault < 0.12 and key:
        rows[rng.randrange(len(rows))][header.index("updated_correct")] = rng.choice(["yes", "2", "1.0"])
    elif fault < 0.15:
        header[rng.randrange(1, len(header))] = "case_id"                   # duplicate column
    elif fault < 0.18:
        header[0] = "id"                                                    # no case_id column
    elif fault < 0.21 and with_answers:
        rows[rng.randrange(len(rows))][header.index("baseline_answer")] = ""
    elif fault < 0.23 and key and with_answers and runs_b > 1:
        header[header.index("baseline_repeat_correct")] = "notes"           # answer without correctness
    text = to_csv(header, rows)
    style = rng.random()
    if style < 0.15:
        text = "﻿" + text.replace("\n", "\r\n")
    elif style < 0.25:
        text = text.replace("\n", "\n\n", 3)                                # blank lines move the row numbers
    elif style < 0.35 and not any(ch in cell for r in [header, *rows] for cell in r for ch in ',\t"\n'):
        text = text.replace(",", "\t")                                      # cells pasted from a spreadsheet
    mode = "nokey" if key and with_answers and rng.random() < 0.3 else "auto"
    return {"text": text, "mode": mode, "sim": rng.choice([0.9, 0.75]) if fuzzy else 1}


@needs_node
def test_browser_analysis_matches_python_on_random_files(tmp_path):
    rng = random.Random(20261111)
    jobs = [random_job(rng) for _ in range(400)]
    with open(FIXTURE, encoding="utf-8") as f:
        fixture = f.read()
    jobs += [{"text": fixture, "mode": "auto", "sim": 1}, {"text": fixture, "mode": "nokey", "sim": 1},
             {"text": "", "mode": "auto", "sim": 1}, {"text": "case_id,question\n1,x\n", "mode": "auto", "sim": 1},
             {"text": "case_id;baseline_correct;updated_correct\n1;1;0\n", "mode": "auto", "sim": 1},
             {"text": "case_id,baseline_answer,updated_answer,baseline_repeat0_answer\n1,a,b,c\n", "mode": "auto", "sim": 1},
             {"text": "case_id,baseline_answer,updated_answer,baseline_repeat_answer,baseline_repeat1_answer\n1,a,b,c,d\n",
              "mode": "auto", "sim": 1},
             {"text": 'case_id , baseline_answer, updated_answer\n 1 , "a ""b""" , "x\ny"\n2,plain"quote,ok\n', "mode": "auto", "sim": 1}]
    (tmp_path / "runner.js").write_text(RUNNER, encoding="utf-8")
    (tmp_path / "jobs.json").write_text(json.dumps(jobs), encoding="utf-8")
    subprocess.run([NODE, str(tmp_path / "runner.js"), os.path.join(ROOT, "web", "core.js"), str(tmp_path / "jobs.json"),
                    str(tmp_path / "out.json")], check=True)
    browser = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    kinds = {"ok": 0, "rejected": 0}
    for job, js in zip(jobs, browser):
        py = python_side(job["text"], job["mode"], job["sim"])
        assert js == py, f"browser and Python disagree on:\n{job['text'][:400]!r}\nmode={job['mode']} sim={job['sim']}"
        kinds["rejected" if "error" in py else "ok"] += 1
    assert kinds["ok"] > 250 and kinds["rejected"] > 40, kinds     # both paths are really exercised


@needs_node
def test_browser_gives_the_fixture_numbers(tmp_path):
    script = ("const core=require(process.argv[1]),fs=require('fs');const t=fs.readFileSync(process.argv[2],'utf8');"
              "const out={};for(const m of ['auto','nokey']){const r=core.parseResults(t,m),a=core.analyse(r.cases,r.mode,1);"
              "out[m]={counts:a.counts,changed:a.changed,rerun:[a.rerunB,a.rerunU],acc:[a.correctB,a.correctU],ri:[a.regressions,a.improvements],"
              "flag:a.answerChange}}console.log(JSON.stringify(out))")
    done = subprocess.run([NODE, "-e", script, os.path.join(ROOT, "web", "core.js"), FIXTURE], capture_output=True, text=True, encoding="utf-8", check=True)
    out = json.loads(done.stdout)
    key, nokey = out["auto"], out["nokey"]
    assert (key["counts"]["stable_regression"], key["counts"]["stable_improvement"], key["counts"]["unstable"],
            key["counts"]["wrong_both"], key["counts"]["correct_both"]) == (3, 2, 5, 6, 24)
    assert key["changed"] == 7 and key["rerun"] == [2, 3] and key["acc"] == [30, 29] and key["ri"] == [4, 3]
    assert key["flag"] == {"s24": "stable", "s40": "stable"}
    assert (nokey["counts"]["stable_change"], nokey["counts"]["unstable"], nokey["counts"]["same"]) == (7, 5, 28)
    assert nokey["changed"] == 9 and nokey["rerun"] == [2, 3]


def test_built_page_is_up_to_date_and_self_contained():
    spec = importlib.util.spec_from_file_location("build_web", os.path.join(ROOT, "tools", "build_web.py"))
    build_web = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build_web)
    with open(os.path.join(ROOT, "web", "ridi-update-check.html"), encoding="utf-8") as f:
        on_disk = f.read()
    assert on_disk == build_web.build(), "run: python tools/build_web.py"
    assert "__" + "STRINGS__" not in on_disk and on_disk.startswith("<!doctype html>")
    external = set(re.findall(r'(?:src|href)="(https?://[^"]+)"', on_disk))
    assert all(url.startswith("https://fonts.googleapis.com/") for url in external), external   # fonts only; no data leaves
    assert "fetch(" not in on_disk and "XMLHttpRequest" not in on_disk
    fragment = build_web.fragment(on_disk)
    assert fragment.startswith("<title>RIDI Update Check</title>") and "<html" not in fragment and "<body" not in fragment

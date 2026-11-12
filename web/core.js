/* ridi-check analysis for the browser. A line-for-line port of contract.py, analysis.py and the data
   part of report.py. tests/test_web.py runs this file in Node against the Python on random files:
   change both together. */
const RidiCore = (function () {
  "use strict";
  const KEY = "key", NOKEY = "nokey";
  const RUN_COLUMN = /^(baseline|updated)(?:_repeat([0-9]*))?_(answer|correct)$/;
  const KEY_STATES = ["stable_regression", "stable_improvement", "regression_unconfirmed", "improvement_unconfirmed",
    "unstable", "wrong_both", "correct_both", "incomplete"];
  const NOKEY_STATES = ["stable_change", "change_unconfirmed", "unstable", "same", "incomplete"];
  const UNCHANGED = new Set(["correct_both", "same"]);
  const NEGATIONS = new Set("not no never neither nor without none cannot t لا غير لم لن بدون ليس ليست".split(" "));
  const CSS_CLASS = { stable_regression: "s-reg", regression_unconfirmed: "s-reg", stable_improvement: "s-imp",
    improvement_unconfirmed: "s-imp", stable_change: "s-chg", change_unconfirmed: "s-chg", unstable: "s-uns",
    wrong_both: "s-wrong", correct_both: "s-ok", same: "s-ok", incomplete: "s-inc" };

  function RidiError(code, info) { const e = new Error(code); e.code = code; e.info = info || {}; return e; }
  const strip = (s) => String(s).replace(/^\s+|\s+$/g, "");

  /* ---------- reading ---------- */
  function sniffDelimiter(text) {
    if (!strip(text)) return ",";
    const header = text.replace(/^﻿+/, "").split(/\r\n|\n|\r/)[0] || "";
    if (!header.includes(",")) { if (header.includes("\t")) return "\t"; if (header.includes(";")) return ";"; }
    return ",";
  }
  /* Same behaviour as Python's csv.reader with skipinitialspace=True. */
  function readRecords(text) {
    text = String(text).replace(/^﻿+/, "");
    const delim = sniffDelimiter(text), all = [];
    let row = [], cur = "", state = 0; /* 0 start of field, 1 in field, 2 in quotes, 3 quote seen inside quotes */
    let started = false;
    const endField = () => { row.push(cur); cur = ""; };
    const endRecord = () => { all.push(row); row = []; started = false; state = 0; };
    for (let i = 0; i < text.length; i++) {
      const c = text[i], nl = c === "\n" || c === "\r";
      if (nl && state !== 2) {
        if (c === "\r" && text[i + 1] === "\n") i++;
        if (started) endField();
        endRecord();
        continue;
      }
      started = true;
      if (state === 0) {
        if (c === '"') state = 2;
        else if (c === " ") { /* skipped */ }
        else if (c === delim) endField();
        else { cur += c; state = 1; }
      } else if (state === 1) {
        if (c === delim) { endField(); state = 0; } else cur += c;
      } else if (state === 2) {
        if (c === '"') state = 3; else cur += c;
      } else {
        if (c === '"') { cur += '"'; state = 2; }
        else if (c === delim) { endField(); state = 0; }
        else { cur += c; state = 1; }
      }
    }
    if (started) { endField(); all.push(row); }
    const out = [];
    const unguard = (cell) => (cell.length > 1 && cell[0] === "'" && "=+-@\t\r".indexOf(cell[1]) >= 0 ? cell.slice(1) : cell);
    all.forEach((r, i) => { if (r.some((cell) => strip(cell) !== "")) out.push([i + 1, r.map(unguard)]); });
    return out;
  }
  function runColumn(side, run, kind) {
    return run === 1 ? side + "_" + kind : run === 2 ? side + "_repeat_" + kind : side + "_repeat" + (run - 1) + "_" + kind;
  }
  const splitContext = (cell) => cell.split("|").map(strip).filter(Boolean);

  const PLAIN_NUMBER = /^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$/;
  function parseResults(text, mode) {
    mode = mode || "auto";
    const records = readRecords(text);
    if (records.length < 2) throw RidiError("empty");
    const header = records[0][1].map((h) => strip(h).toLowerCase());
    const seen = new Set();
    for (const name of header) { if (name && seen.has(name)) throw RidiError("dupColumn", { name }); seen.add(name); }
    const col = {}; header.forEach((name, i) => { col[name] = i; });
    if (!("case_id" in col)) throw RidiError("noId");

    const runs = {}; /* "side|kind" -> [[index, position]] in header order */
    header.forEach((name, position) => {
      const m = RUN_COLUMN.exec(name); if (!m) return;
      let index;
      if (m[2] === undefined) index = 0;
      else if (m[2] === "") index = 1;
      else { index = parseInt(m[2], 10); if (index < 1) throw RidiError("repeatZero", { name }); }
      const slot = runs[m[1] + "|" + m[3]] = runs[m[1] + "|" + m[3]] || [];
      const clash = slot.find((x) => x[0] === index);
      if (clash) throw RidiError("sameRun", { a: header[clash[1]], b: name });
      slot.push([index, position]);
    });
    const hasKey = "baseline_correct" in col && "updated_correct" in col;
    const hasAnswers = "baseline_answer" in col && "updated_answer" in col;
    if (!hasKey && !hasAnswers) throw RidiError("needCols");
    if (mode === KEY && !hasKey) throw RidiError("needKey");
    if (mode === NOKEY && !hasAnswers) throw RidiError("needAnswers");
    const resolved = mode !== "auto" ? mode : (hasKey ? KEY : NOKEY), key = resolved === KEY;

    const cases = [], firstRow = new Map();
    for (const [row, record] of records.slice(1)) {
      const at = (i) => (i >= 0 && i < record.length ? strip(record[i]) : "");
      const get = (name) => at(name in col ? col[name] : -1);
      const id = get("case_id");
      if (!id) throw RidiError("rowNoId", { row });
      if (firstRow.has(id)) throw RidiError("rowDup", { row, id, first: firstRow.get(id) });
      firstRow.set(id, row);
      const c = { id, row, q: get("question"), expected: get("expected"), b: [], u: [],
        bc: splitContext(get("baseline_context")), uc: splitContext(get("updated_context")), err: get("run_errors"), incomplete: false };
      /* optional scores and content hashes, one for each passage, "-" for none */
      const aligned = (column, passages, numbers) => {
        const cell = get(column);
        if (strip(cell) === "") return [];
        const values = cell.split("|").map(strip);
        if (values.length !== passages.length) throw RidiError("ctxCount", { row, id, col: column, got: values.length, want: passages.length });
        return values.map((v) => {
          if (v === "" || v === "-") return null;
          if (!numbers) return v;
          if (!PLAIN_NUMBER.test(v)) throw RidiError("ctxNumber", { row, id, col: column, value: v });
          return parseFloat(v);
        });
      };
      c.bs = aligned("baseline_context_scores", c.bc, true); c.us = aligned("updated_context_scores", c.uc, true);
      c.bh = aligned("baseline_context_hashes", c.bc, false); c.uh = aligned("updated_context_hashes", c.uc, false);
      for (const side of ["baseline", "updated"]) {
        const answers = new Map(runs[side + "|answer"] || []), corrects = runs[side + "|correct"] || [];
        const scored = new Map();
        for (const [index, position] of corrects) {
          const v = at(position);
          if (v === "") scored.set(index, null);
          else if (v !== "0" && v !== "1") throw RidiError("rowBin", { row, id, col: header[position], value: v });
          else scored.set(index, +v);
        }
        const indices = Array.from(new Set([...answers.keys(), ...(key ? corrects.map((x) => x[0]) : [])])).sort((a, b) => a - b);
        const out = [];
        for (const index of indices) {
          const ans = answers.has(index) ? at(answers.get(index)) : "";
          const cor = key && scored.has(index) ? scored.get(index) : null;
          const missing = key ? cor === null : ans === "";
          if (index === 0) {
            if (missing) {
              if (!c.err) throw RidiError("rowEmptyFirst", { row, id, col: runColumn(side, 1, key ? "correct" : "answer") });
              c.incomplete = true; continue;
            }
          } else if (ans === "" && cor === null) continue;
          else if (key && cor === null) throw RidiError("rowNoCorrect", { row, id, a: runColumn(side, index + 1, "answer"), c: runColumn(side, index + 1, "correct") });
          out.push({ ans, cor });
        }
        c[side === "baseline" ? "b" : "u"] = out;
      }
      cases.push(c);
    }
    return { cases, mode: resolved };
  }

  /* ---------- analysis ---------- */
  /* Lower-case, punctuation to spaces, whitespace collapsed, except that the signs that carry meaning are kept,
     each as a word of its own: every mathematical symbol, a percent sign after a digit, "/" and "*" between two
     letters or digits, "!" before "=", and a hyphen that is a sign (-5, HIV-). Same rules as analysis.py. */
  function normalise(text) {
    const s = Array.from(String(text).toLowerCase());
    const inWord = (c) => c !== undefined && /[\p{L}\p{N}]/u.test(c), isDigit = (c) => c !== undefined && /\p{Nd}/u.test(c);
    let out = "";
    for (let i = 0; i < s.length; i++) {
      const ch = s[i];
      if (inWord(ch)) { out += ch; continue; }
      const before = s[i - 1], after = s[i + 1];
      if ((ch === "." || ch === "," || ch === "\u066b" || ch === "\u066c") && isDigit(before) && isDigit(after)) { out += ch; continue; }
      const keep = /[\p{Sm}\p{Sc}\p{So}]/u.test(ch) || ((ch === "%" || ch === "\u066a") && isDigit(before)) ||
        ((ch === "/" || ch === "*") && inWord(before) && inWord(after)) ||
        (ch === "-" && ((isDigit(after) && !inWord(before)) || (inWord(before) && !inWord(after)))) || (ch === "!" && after === "=");
      out += keep ? " " + (ch === "\u2212" ? "-" : ch) + " " : " ";
    }
    return out.replace(/\s+/g, " ").trim();
  }
  function sameAnswer(a, b, threshold) {
    const x = normalise(a), y = normalise(b);
    if (x === y) return true;
    if (!(threshold < 1)) return false;
    const xs = x.split(" "), ys = y.split(" ");
    const A = new Set(xs), B = new Set(ys);
    const neg = (S) => { for (const w of S) if (NEGATIONS.has(w)) return true; return false; };
    if (neg(A) !== neg(B)) return false;
    const nums = (s) => (s.match(/\p{Nd}+/gu) || []).join(" ");   /* the digit runs, in order: "5mg" and "50mg" differ */
    if (nums(x) !== nums(y)) return false;
    /* the signs that were kept must be the same, in the same order */
    const signs = (ws) => ws.filter((w) => w !== "" && !/[\p{L}\p{N}]/u.test(Array.from(w)[0])).join(" ");
    if (signs(xs) !== signs(ys)) return false;
    /* every word that holds a digit; a bare number is taken together with the word after it (its unit) */
    const contexts = (ws) => ws.map((w, i) => (/\p{Nd}/u.test(w) ? w + " " + (/^\p{Nd}+$/u.test(w) && i + 1 < ws.length ? ws[i + 1] : "") : null)).filter((c) => c !== null).join("|");
    if (contexts(xs) !== contexts(ys)) return false;
    /* the same number of words and not the same text: a word was replaced, or the same words stand in another order */
    if (xs.length === ys.length) return false;
    let shared = 0; A.forEach((w) => { if (B.has(w)) shared++; });
    const union = A.size + B.size - shared;
    return union > 0 && shared / union >= threshold;
  }
  const makeEq = (mode, threshold) => (mode === KEY ? (r, s) => r.cor === s.cor : (r, s) => sameAnswer(r.ans, s.ans, threshold));
  function classify(c, mode, threshold) {
    if (c.incomplete) return "incomplete";
    const eq = makeEq(mode, threshold), b = c.b, u = c.u;
    if (!b.every((r) => eq(r, b[0])) || !u.every((r) => eq(r, u[0]))) return "unstable";
    const key = mode === KEY;
    if (eq(b[0], u[0])) return !key ? "same" : (b[0].cor ? "correct_both" : "wrong_both");
    const confirmed = b.length > 1 && u.length > 1;
    if (!key) return confirmed ? "stable_change" : "change_unconfirmed";
    if (b[0].cor) return confirmed ? "stable_regression" : "regression_unconfirmed";
    return confirmed ? "stable_improvement" : "improvement_unconfirmed";
  }
  function analyse(cases, mode, threshold) {
    threshold = threshold === undefined ? 1 : threshold;
    const key = mode === KEY, eq = makeEq(mode, threshold);
    const a = { mode, threshold, items: [], counts: {}, answerChange: {}, bySimilarity: [], n: cases.length, nCompared: 0, changed: 0,
      rerunB: 0, rerunBN: 0, rerunU: 0, rerunUN: 0, anyB: 0, anyU: 0, confirmable: 0, maxRunsB: 0, maxRunsU: 0,
      correctB: 0, correctU: 0, regressions: 0, improvements: 0 };
    (key ? KEY_STATES : NOKEY_STATES).forEach((s) => { a.counts[s] = 0; });
    for (const c of cases) {
      const s = classify(c, mode, threshold);
      a.counts[s]++; a.items.push({ c, s });
      if (s === "incomplete") continue;
      const b = c.b, u = c.u;
      a.nCompared++; a.maxRunsB = Math.max(a.maxRunsB, b.length); a.maxRunsU = Math.max(a.maxRunsU, u.length);
      if (!eq(b[0], u[0])) a.changed++;
      if (b.length > 1) { a.rerunBN++; if (!eq(b[0], b[1])) a.rerunB++; if (!b.every((r) => eq(r, b[0]))) a.anyB++; }
      if (u.length > 1) { a.rerunUN++; if (!eq(u[0], u[1])) a.rerunU++; if (!u.every((r) => eq(r, u[0]))) a.anyU++; }
      if ((s === "wrong_both" || s === "correct_both") && b.concat(u).every((r) => r.ans)) {
        const byAnswer = classify(c, NOKEY, threshold);
        if (byAnswer === "stable_change") a.answerChange[c.id] = "stable";
        else if (byAnswer === "change_unconfirmed") a.answerChange[c.id] = "unconfirmed";
        else if (byAnswer === "unstable") a.answerChange[c.id] = "varied";
      }
      if (!key && threshold < 1 && classify(c, mode, 1) !== s) a.bySimilarity.push(c.id);
      if (b.length > 1 && u.length > 1) a.confirmable++;
      if (key) {
        a.correctB += b[0].cor; a.correctU += u[0].cor;
        if (b[0].cor && !u[0].cor) a.regressions++;
        if (!b[0].cor && u[0].cor) a.improvements++;
      }
    }
    a.ids = (state) => a.items.filter((it) => it.s === state).map((it) => it.c.id);
    return a;
  }

  /* ---------- report data ---------- */
  const rate = (count, n) => (n ? { count, n } : null);
  function buildSummary(a) {
    const key = a.mode === KEY;
    const first = { change_between_versions: rate(a.changed, a.nCompared) || { count: 0, n: 0 },
      rerun_variation_current: rate(a.rerunB, a.rerunBN), rerun_variation_proposed: rate(a.rerunU, a.rerunUN) };
    if (key) Object.assign(first, { accuracy_current: rate(a.correctB, a.nCompared), accuracy_proposed: rate(a.correctU, a.nCompared),
      regressions: a.regressions, improvements: a.improvements,
      changes_visible_in_mean_accuracy: Math.abs(a.improvements - a.regressions),
      changes_cancelled_in_mean_accuracy: 2 * Math.min(a.regressions, a.improvements) });
    const caseIds = {}; Object.keys(a.counts).forEach((s) => { if (!UNCHANGED.has(s)) caseIds[s] = a.ids(s); });
    const summary = { mode: a.mode, similarity_threshold: a.threshold, cases: a.n, cases_compared: a.nCompared,
      confirmable_cases: a.confirmable, runs_per_version: { current: a.maxRunsB, proposed: a.maxRunsU },
      states: Object.assign({}, a.counts), case_ids: caseIds, first_run: first,
      any_run_disagreement: { current: a.anyB, proposed: a.anyU } };
    const listed = a.items.filter((it) => it.s !== "incomplete" && (it.c.bc.length || it.c.uc.length));
    if (listed.length) {   /* a count of where the retrieved passages differ; it says nothing about cause */
      const differs = listed.map((it) => { const d = passageDifference(it.c); return [it.s, d[0].length || d[1].length ? 1 : 0]; });
      const byState = {};
      Object.keys(a.counts).forEach((s) => { const mine = differs.filter((d) => d[0] === s);
        if (mine.length) byState[s] = { differ: mine.reduce((n, d) => n + d[1], 0), n: mine.length }; });
      summary.passages = { cases_with_passages: listed.length, differ: differs.reduce((n, d) => n + d[1], 0),
        reordered: listed.filter((it) => reordered(it.c)).length,
        content_changed: listed.filter((it) => passageMoves(it.c).some((m) => m[5])).length, by_state: byState };
    }
    if (key) {
      const flagged = (state, flag) => a.items.filter((it) => it.s === state && a.answerChange[it.c.id] === flag).map((it) => it.c.id);
      for (const [name, state] of [["wrong_both_answer_changed", "wrong_both"], ["correct_both_answer_changed", "correct_both"]]) {
        summary[name] = { stable: flagged(state, "stable"), unconfirmed: flagged(state, "unconfirmed"), varied: flagged(state, "varied") };
      }
    } else if (a.threshold < 1) {
      summary.labelled_by_similarity = a.bySimilarity.slice();
    }
    return summary;
  }
  /* For each passage that both versions retrieved: [name, rank in each, score in each or null, content changed],
     when any of these differ. A rank is the place of the first time the passage appears. */
  function passageMoves(c) {
    const first = (names, values) => { const seen = new Map();
      names.forEach((name, i) => { if (!seen.has(name)) seen.set(name, [i + 1, i < values.length ? values[i] : null]); }); return seen; };
    const rankB = first(c.bc, c.bs || []), rankU = first(c.uc, c.us || []), hashB = first(c.bc, c.bh || []), hashU = first(c.uc, c.uh || []);
    const out = [];
    rankB.forEach((b, name) => {
      if (!rankU.has(name)) return;
      const u = rankU.get(name), hb = hashB.get(name)[1], hu = hashU.get(name)[1];
      const changed = !!(hb && hu && hb !== hu);
      if (b[0] !== u[0] || changed || (b[1] !== null && u[1] !== null && b[1] !== u[1])) out.push([name, b[0], u[0], b[1], u[1], changed]);
    });
    return out;
  }
  /* the same passages in both versions, in another order or another number of times */
  function reordered(c) {
    const inB = new Set(c.bc), inU = new Set(c.uc);
    return inB.size === inU.size && c.bc.every((p) => inU.has(p)) && (c.bc.length !== c.uc.length || c.bc.some((p, i) => p !== c.uc[i]));
  }
  function passageDifference(c) {
    const inB = new Set(c.bc), inU = new Set(c.uc);
    const onlyB = c.bc.filter((p) => !inU.has(p)), onlyU = c.uc.filter((p) => !inB.has(p));
    return [onlyB, onlyU, c.bc.length - onlyB.length];
  }
  function reviewTable(a, judgments) {
    judgments = judgments || {};
    const key = a.mode === KEY, cases = a.items.map((it) => it.c);
    const runsB = Math.max(0, ...cases.map((c) => c.b.length)) || 1, runsU = Math.max(0, ...cases.map((c) => c.u.length)) || 1;
    const has = (f) => cases.some(f);
    const anyAnswer = cases.some((c) => c.b.concat(c.u).some((r) => r.ans));
    const hasQ = has((c) => c.q), hasE = has((c) => c.expected), hasErr = has((c) => c.err);
    const sides = [["baseline", runsB, "b"], ["updated", runsU, "u"]];
    let header = ["case_id", "state", key ? "answer_change" : "judgment"];
    if (hasQ) header.push("question"); if (hasE) header.push("expected");
    const answerCols = anyAnswer || !key;
    if (answerCols) for (const [side, n] of sides) for (let k = 1; k <= n; k++) header.push(runColumn(side, k, "answer"));
    if (key) for (const [side, n] of sides) for (let k = 1; k <= n; k++) header.push(runColumn(side, k, "correct"));
    const withContext = has((c) => c.bc.length) || has((c) => c.uc.length);
    if (withContext) header = header.concat(["baseline_context", "updated_context", "passages_only_current", "passages_only_proposed"]);
    if (hasErr) header.push("run_errors");
    const rows = [];
    for (const { c, s } of a.items) {
      if (UNCHANGED.has(s) && !a.answerChange[c.id]) continue;
      const row = [c.id, s, key ? (a.answerChange[c.id] || "") : (judgments[c.id] || "")];
      if (hasQ) row.push(c.q); if (hasE) row.push(c.expected);
      if (answerCols) for (const [, n, f] of sides) for (let k = 0; k < n; k++) row.push(k < c[f].length ? c[f][k].ans : "");
      if (key) for (const [, n, f] of sides) for (let k = 0; k < n; k++) row.push(k < c[f].length && c[f][k].cor !== null ? String(c[f][k].cor) : "");
      if (withContext) { const [onlyB, onlyU] = passageDifference(c); row.push(c.bc.join(" | "), c.uc.join(" | "), onlyB.join(" | "), onlyU.join(" | ")); }
      if (hasErr) row.push(c.err);
      rows.push(row);
    }
    return { header, rows };
  }
  function toCsv(header, rows) {
    /* A spreadsheet reads a cell that starts with = + - @ tab or return as a formula: an apostrophe goes in front,
       and readRecords takes it off again. A null character is never read back. */
    const cell = (v) => { let s = v === null || v === undefined ? "" : String(v).replace(/\0/g, ""); if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;
      return /[,"\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
    return [header].concat(rows).map((r) => r.map(cell).join(",") + "\n").join("");
  }
  function ledgerTiles(a) {
    const n = (s) => a.counts[s] || 0;
    let stable, unconfirmed, rest;
    if (a.mode === KEY) { stable = ["stable_regression", "stable_improvement"]; unconfirmed = ["regression_unconfirmed", "improvement_unconfirmed"]; rest = ["unstable", "wrong_both", "correct_both"]; }
    else { stable = ["stable_change"]; unconfirmed = ["change_unconfirmed"]; rest = ["unstable", "same"]; }
    const anyUnconfirmed = unconfirmed.some((s) => n(s));
    return (a.confirmable || !anyUnconfirmed ? stable : []).concat(anyUnconfirmed ? unconfirmed : [], rest, n("incomplete") ? ["incomplete"] : []);
  }
  function runsForPage(runs, key, threshold) {
    return runs.map((r, i) => {
      const first = runs[0];
      const same = key ? r.cor === first.cor && (!r.ans || !first.ans || sameAnswer(r.ans, first.ans, threshold)) : sameAnswer(r.ans, first.ans, threshold);
      return { ans: r.ans, cor: r.cor, same: i ? !!same : true };
    });
  }
  function pageData(a) {
    const key = a.mode === KEY, cards = [], late = [], stripCells = [], wrong = [];
    for (const { c, s } of a.items) {
      const flag = a.answerChange[c.id] || null;
      if ((!UNCHANGED.has(s) && (s !== "wrong_both" || flag)) || (s === "correct_both" && flag)) {
        const [onlyB, onlyU, kept] = passageDifference(c);
        (s === "correct_both" ? late : cards).push({ id: c.id, state: s, flag, q: c.q, expected: c.expected, b: runsForPage(c.b, key, a.threshold), u: runsForPage(c.u, key, a.threshold),
          rem: onlyB, add: onlyU, kept, ord: reordered(c), mov: passageMoves(c), err: c.err });
      }
      stripCells.push([c.id, s, -1]);
      if (s === "wrong_both") wrong.push([c.id, c.q, flag]);
    }
    /* cases correct in both versions whose answer changed come last, so they never bury a case whose score changed */
    late.forEach((card) => cards.push(card));
    const position = new Map(cards.map((card, i) => [card.id, i]));
    stripCells.forEach((cell) => { if (position.has(cell[0])) cell[2] = position.get(cell[0]); });
    const classes = {}; Object.keys(a.counts).forEach((s) => { classes[s] = CSS_CLASS[s]; });
    return { summary: buildSummary(a), tiles: ledgerTiles(a), classes,
      acc: key && a.nCompared ? { a: a.correctB, b: a.correctU, n: a.nCompared, r: a.regressions, i: a.improvements } : null,
      strip: stripCells, cards, wrong, focus: key ? "stable_regression" : "stable_change", stable_change_ids: a.ids("stable_change") };
  }

  return { parseResults, readRecords, analyse, classify, buildSummary, reviewTable, toCsv, pageData, normalise, sameAnswer, runColumn };
})();
if (typeof module !== "undefined") module.exports = RidiCore;

/* The page: inputs, then the same report the command-line tool writes. Analysis is in core.js. */
(function () {
  "use strict";
  const UI = {
    en: {
      name: "RIDI Update Check", langBtn: "العربية",
      tagline: "Compare the current and the proposed version of an assistant on the same questions. See which answers changed, and which changes hold when each version is run again.",
      sampleKey: "Example with answer key", sampleNoKey: "Example without answer key",
      own: "Check your own results", choose: "Choose a CSV file", paste: "Or paste here: CSV text, or cells copied from a spreadsheet",
      run: "Check", privacy: "Your file is read in this browser tab only. Nothing is uploaded or stored on a server. What you paste stays until you close the tab, and your judgments are kept in this browser so that a refresh does not lose them.",
      forget: "Clear my judgments",
      tooBig: "This file is too large to show here ({n} characters). It was read and checked all the same.",
      format: "Columns", colsNote: "One row per question. The first row holds the column names.",
      cols: [
        "<code>case_id</code> required, unique.",
        "<code>baseline_answer</code>, <code>updated_answer</code>: the answer of the current and of the proposed version.",
        "<code>baseline_repeat_answer</code>, <code>updated_repeat_answer</code>: a second run of each version. Without them no change can be confirmed. Further runs: <code>baseline_repeat2_answer</code>, and so on.",
        "<code>baseline_correct</code>, <code>updated_correct</code>, <code>baseline_repeat_correct</code>, <code>updated_repeat_correct</code> (0 or 1): add these if you have an answer key.",
        "Optional: <code>question</code>, <code>expected</code>, <code>baseline_context</code>, <code>updated_context</code> (passage names separated by <code>|</code>)."
      ],
      opts: "How to compare", modeLabel: "If the file has correctness columns", modeAuto: "use them", modeNoKey: "ignore them and compare the answers",
      sameWhen: "Count two answers as the same when", simExact: "they match (ignoring case and punctuation)", sim90: "they share 90% of their words", sim75: "they share 75% of their words",
      noteKey: "Synthetic example data, not yours: 30 questions about a made-up library handbook. The proposed version splits the handbook into smaller pieces, and each version was run twice.",
      noteNoKey: "Synthetic example data, not yours: the same 30 questions with the answer key hidden, so the changes are yours to judge.",
      noteFile: "{n} cases from your file.", noteFileOne: "1 case from your file.",
      setLabel: "Example data: ", setLibrary: "Library handbook (30 questions)", setMedicines: "Invented drug names (illustration only, 12 questions)",
      noteKeyMed: "Synthetic example data, not yours: 12 questions that use invented drug names, for illustration only. The names, doses and effects are invented and are not medical guidance. The proposed version retrieves different passages, and each version was run twice.",
      noteNoKeyMed: "Synthetic example data, not yours: the same 12 questions that use invented drug names, for illustration only, with the answer key hidden, so the changes are yours to judge. Nothing here is medical guidance.",
      whyTitle: "Why each version is run more than once",
      whyList: [
        "Mean accuracy hides opposite changes. An update can fix some answers and break others. The mean moves only by the difference, so the answers it broke stay out of sight unless every case is looked at.",
        "One run cannot tell a change from re-run variation. The same version can answer the same question differently from one run to the next, so a difference seen once between two versions may have nothing to do with the update.",
        "The rule used here: a case is a stable regression when every run of the current version is correct and every run of the proposed version is wrong, with at least two runs of each. A stable improvement is the reverse. When the runs of either version disagree with each other, the case is unstable on re-run and is not counted as a change of either kind. Without an answer key the same rule is applied to the answers themselves.",
        "What this is not: no statistical test is applied, and two runs are a thin estimate of re-run variation. A stable answer is a repeated answer, not a correct one."
      ],
      copyJ: "Copy judgments.csv", copyR: "Copy the cases to review as CSV", copied: "Copied", copyFail: "Select the text below and copy it.",
      getTitle: "Where the answers come from",
      getList: [
        "Ask both versions of your assistant the same questions, twice each, and put the answers in a spreadsheet with the columns above.",
        "Or let the ridi-check command-line tool do it: it calls both versions, records every answer and writes this file as results.csv.",
        "Use questions your users really ask. 30 to 100 is a good first set."
      ],
      err: {
        empty: "No rows found. The first row must hold the column names and the next rows the cases.",
        noId: "The file needs a case_id column.", dupColumn: "Column {name} appears more than once.",
        sameRun: "Columns {a} and {b} name the same run.", repeatZero: "Column {name}: repeat numbers start at 1.",
        needCols: "The file needs baseline_answer and updated_answer, or baseline_correct and updated_correct (0 or 1).",
        needKey: "Answer-key mode needs baseline_correct and updated_correct.", needAnswers: "To compare answers the file needs baseline_answer and updated_answer.",
        rowNoId: "Row {row}: case_id is missing.", rowDup: "Row {row}: case_id {id} appears more than once (first in row {first}).",
        rowBin: "Row {row} (case {id}): {col} must be 0 or 1, got “{value}”.",
        rowEmptyFirst: "Row {row} (case {id}): {col} is empty. Every row needs a first-run value.",
        rowNoCorrect: "Row {row} (case {id}): {a} has a value but {c} is empty or absent.",
        read: "The file could not be read.",
        encoding: "The file is not UTF-8 text. Save it as UTF-8 and try again: in Excel, File > Save As > \"CSV UTF-8 (Comma delimited)\"."
      }
    },
    ar: {
      name: "RIDI Update Check", langBtn: "English",
      tagline: "قارن النسخة الحالية والنسخة المقترحة من مساعدك على الأسئلة نفسها. اعرف أي الإجابات تغيّرت، وأي تغيّر يثبت عند إعادة تشغيل كل نسخة.",
      sampleKey: "مثال مع مفتاح إجابات", sampleNoKey: "مثال بدون مفتاح إجابات",
      own: "افحص نتائجك", choose: "اختر ملف CSV", paste: "أو الصق هنا: نص CSV، أو خلايا منسوخة من جدول",
      run: "افحص", privacy: "ملفك يُقرأ داخل هذا التبويب فقط. لا يُرفع شيء ولا يُحفظ على خادم. ما تلصقه يبقى حتى تغلق التبويب، وأحكامك تُحفظ في هذا المتصفح حتى لا تضيع عند تحديث الصفحة.",
      forget: "امسح أحكامي",
      tooBig: "هذا الملف أكبر من أن يُعرض هنا ({n} حرفاً). قُرئ وفُحص على أي حال.",
      format: "الأعمدة", colsNote: "صف واحد لكل سؤال، والصف الأول فيه أسماء الأعمدة.",
      cols: [
        "<code>case_id</code> مطلوب وفريد.",
        "<code>baseline_answer</code> و<code>updated_answer</code>: إجابة النسخة الحالية وإجابة النسخة المقترحة.",
        "<code>baseline_repeat_answer</code> و<code>updated_repeat_answer</code>: تشغيل ثانٍ لكل نسخة. بدونهما لا يمكن تأكيد أي تغيّر. التشغيلات التالية: <code>baseline_repeat2_answer</code> وهكذا.",
        "<code>baseline_correct</code> و<code>updated_correct</code> و<code>baseline_repeat_correct</code> و<code>updated_repeat_correct</code> (0 أو 1): أضفها إن كان عندك مفتاح إجابات.",
        "اختياري: <code>question</code> و<code>expected</code> و<code>baseline_context</code> و<code>updated_context</code> (أسماء المقاطع مفصولة بعلامة <code>|</code>)."
      ],
      opts: "طريقة المقارنة", modeLabel: "إذا كان في الملف أعمدة صحة", modeAuto: "استخدمها", modeNoKey: "تجاهلها وقارن الإجابات",
      sameWhen: "تُعدّ الإجابتان متطابقتين عندما", simExact: "تتطابقان (مع تجاهل حالة الأحرف والترقيم)", sim90: "تشتركان في 90% من الكلمات", sim75: "تشتركان في 75% من الكلمات",
      noteKey: "بيانات مثال اصطناعية وليست بياناتك: 30 سؤالاً عن دليل مكتبة مختلَق. النسخة المقترحة تقطّع الدليل إلى قطع أصغر، وشُغّلت كل نسخة مرتين.",
      noteNoKey: "بيانات مثال اصطناعية وليست بياناتك: الأسئلة الثلاثون نفسها مع إخفاء مفتاح الإجابات، فالحكم على التغيّرات لك.",
      noteFile: "{n} حالة من ملفك.", noteFileOne: "حالة واحدة من ملفك.",
      setLabel: "بيانات المثال: ", setLibrary: "دليل مكتبة (30 سؤالاً)", setMedicines: "أسماء أدوية مختلقة (للتوضيح فقط، 12 سؤالاً)",
      noteKeyMed: "بيانات مثال اصطناعية وليست بياناتك: 12 سؤالاً بأسماء أدوية مختلقة، للتوضيح فقط. الأسماء والجرعات والتأثيرات مختلقة وليست إرشاداً طبياً. النسخة المقترحة تسترجع مقاطع مختلفة، وكل نسخة شُغّلت مرتين.",
      noteNoKeyMed: "بيانات مثال اصطناعية وليست بياناتك: الأسئلة الاثنا عشر نفسها بأسماء أدوية مختلقة، للتوضيح فقط، مع إخفاء مفتاح الإجابات، فالحكم على التغيّرات لك. لا شيء هنا إرشاد طبي.",
      whyTitle: "لماذا تُشغَّل كل نسخة أكثر من مرة",
      whyList: [
        "متوسط الدقة يخفي التغيّرات المتعاكسة. قد يصلح التحديث إجابات ويكسر أخرى، والمتوسط يتحرك بمقدار الفرق فقط، فتبقى الإجابات التي كسرها غير ظاهرة ما لم تُفحص كل حالة.",
        "تشغيل واحد لا يميّز التغيّر من تباين إعادة التشغيل. النسخة نفسها قد تجيب عن السؤال نفسه بإجابة مختلفة من تشغيل إلى آخر، فالفرق الذي يظهر مرة واحدة بين نسختين قد لا تكون له علاقة بالتحديث.",
        "القاعدة المستخدمة هنا: الحالة تراجع ثابت عندما تكون كل تشغيلات النسخة الحالية صحيحة وكل تشغيلات النسخة المقترحة خاطئة، بتشغيلين على الأقل لكل نسخة. والتحسّن الثابت عكس ذلك. وإذا اختلفت تشغيلات إحدى النسختين فيما بينها فالحالة غير مستقرة عند إعادة التشغيل ولا تُحسب تغيّراً من أي النوعين. وبلا مفتاح إجابات تُطبَّق القاعدة نفسها على الإجابات ذاتها.",
        "ما ليس هذا: لا يُطبَّق أي اختبار إحصائي، وتشغيلان تقدير ضعيف لتباين إعادة التشغيل. الإجابة الثابتة إجابة متكررة وليست بالضرورة صحيحة."
      ],
      copyJ: "انسخ judgments.csv", copyR: "انسخ حالات المراجعة بصيغة CSV", copied: "تم النسخ", copyFail: "حدّد النص أدناه وانسخه.",
      getTitle: "من أين تأتي الإجابات",
      getList: [
        "اطرح الأسئلة نفسها على نسختَي مساعدك، مرتين لكل نسخة، وضع الإجابات في جدول بالأعمدة أعلاه.",
        "أو دع أداة سطر الأوامر ridi-check تفعل ذلك: تستدعي النسختين وتسجّل كل إجابة وتكتب هذا الملف باسم results.csv.",
        "استخدم أسئلة يطرحها مستخدموك فعلاً. من 30 إلى 100 سؤال بداية جيدة."
      ],
      err: {
        empty: "لا توجد صفوف. الصف الأول لأسماء الأعمدة والصفوف التالية للحالات.",
        noId: "الملف يحتاج عمود case_id.", dupColumn: "العمود {name} مكرر.",
        sameRun: "العمودان {a} و{b} يسمّيان التشغيل نفسه.", repeatZero: "العمود {name}: أرقام الإعادة تبدأ من 1.",
        needCols: "الملف يحتاج baseline_answer وupdated_answer، أو baseline_correct وupdated_correct (0 أو 1).",
        needKey: "وضع مفتاح الإجابات يحتاج baseline_correct وupdated_correct.", needAnswers: "لمقارنة الإجابات يحتاج الملف baseline_answer وupdated_answer.",
        rowNoId: "الصف {row}: قيمة case_id ناقصة.", rowDup: "الصف {row}: المعرّف {id} مكرر (ورد أولاً في الصف {first}).",
        rowBin: "الصف {row} (الحالة {id}): العمود {col} يجب أن يكون 0 أو 1، والموجود «{value}».",
        rowEmptyFirst: "الصف {row} (الحالة {id}): العمود {col} فارغ. كل صف يحتاج قيمة للتشغيل الأول.",
        rowNoCorrect: "الصف {row} (الحالة {id}): في {a} قيمة لكن {c} فارغ أو غير موجود.",
        read: "تعذّرت قراءة الملف.",
        encoding: "الملف ليس نصاً بترميز UTF-8. احفظه بترميز UTF-8 ثم أعد المحاولة: في Excel، ملف > حفظ باسم > «CSV UTF-8»."
      }
    }
  };
  const STR = JSON.parse(document.getElementById("ridi-strings").textContent);
  const SAMPLES = { library: JSON.parse(document.getElementById("ridi-sample").textContent),
    medicines: JSON.parse(document.getElementById("ridi-sample-medicines").textContent) };
  const SAMPLE = SAMPLES.library;
  const JUDGMENTS = ["worse", "better", "same_meaning", "unsure"];
  const PAGE = 50, STRIP_MAX = 2000, LIST_MAX = 500;

  const state = { lang: "en", source: "sample-key", set: "library", text: SAMPLE, modePref: "auto", sim: 1, filter: "all", shown: 50, judge: {}, error: null, D: null, A: null, mode: "key" };
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
    del(k) { try { localStorage.removeItem(k); } catch (e) {} }
  };
  /* What was pasted or chosen is kept for this tab only, so an accidental refresh does not lose it. */
  const INPUT_KEY = "ridi-input", INPUT_LIMIT = 2000000;
  const tab = {
    get() { try { return sessionStorage.getItem(INPUT_KEY); } catch (e) { return null; } },
    set(text) { try { if (text.length <= INPUT_LIMIT) sessionStorage.setItem(INPUT_KEY, text); else sessionStorage.removeItem(INPUT_KEY); } catch (e) {} },
    clear() { try { sessionStorage.removeItem(INPUT_KEY); } catch (e) {} }
  };
  (function () {
    const saved = store.get("ridi-lang");
    if (saved === "ar" || saved === "en") state.lang = saved;
    else if ((navigator.language || "").toLowerCase().startsWith("ar")) state.lang = "ar";
  })();

  const $ = (id) => document.getElementById(id);
  const fill = (s, v) => { if (v) for (const k in v) s = s.split("{" + k + "}").join(v[k]); return s; };
  const u = (k, v) => fill(UI[state.lang][k], v);
  const L = () => STR[state.mode][state.lang];
  const t = (k, v) => fill(L()[k], v);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const pct = (k, n) => (n ? (100 * k / n) : 0);
  const fmt = (x) => (Math.round(x * 10) / 10).toFixed(1).replace(/\.0$/, "");
  const hash = (s) => { let h = 5381; for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0; return (h >>> 0).toString(36); };
  /* The key is worked out once for each text: hashing a large file again on every click would be slow. */
  let keyFor = null, keyIs = "";
  const judgeKey = () => { if (keyFor !== state.text) { keyFor = state.text; keyIs = "ridi-judge-" + hash(state.text); } return keyIs; };

  function compute() {
    state.error = null;
    try {
      const forced = state.source === "sample-nokey" ? "nokey" : state.source === "sample-key" ? "auto" : state.modePref;
      const parsed = RidiCore.parseResults(state.text, forced);
      state.mode = parsed.mode;
      state.A = RidiCore.analyse(parsed.cases, parsed.mode, parsed.mode === "nokey" ? state.sim : 1);
      state.D = RidiCore.pageData(state.A);
    } catch (e) {
      if (!e.code) throw e;
      state.error = fill(UI[state.lang].err[e.code] || UI[state.lang].err.read, e.info);
      state.errorCode = e;
    }
  }
  function load(source, text) {
    const before = { source: state.source, text: state.text };
    state.source = source; state.text = text; state.filter = "all"; state.shown = PAGE;
    compute();
    if (state.error && state.D) { /* keep showing the last good report under the message */
      state.source = before.source; state.text = before.text; const err = state.error, code = state.errorCode;
      compute(); state.error = err; state.errorCode = code;
    } else if (!state.error) {
      if (source === "file") tab.set(text); else tab.clear();
      state.judge = {};
      const saved = store.get(judgeKey()); if (saved) { try { state.judge = JSON.parse(saved) || {}; } catch (e) {} }
    }
    render();
  }

  /* ---------- report ---------- */
  const pillText = (c) => c.flag ? L().pill[c.state + (c.flag === "stable" ? "_changed" : c.flag === "varied" ? "_varied" : "_changed_unconfirmed")] : L().pill[c.state];
  const isStable = (c) => c.state.indexOf("stable_") === 0 || c.flag === "stable";
  function tile(s, sub) {
    const D = state.D;
    return '<div class="tile ' + D.classes[s] + '"><span class="n">' + (D.summary.states[s] || 0) + '</span><span class="k"><span class="dot"></span>' + esc(L().state[s]) +
      '</span><span class="small muted">' + esc(sub) + "</span></div>";
  }
  function sideHTML(label, runs) {
    const KEYM = state.mode === "key";
    let h = '<div class="side"><span class="lbl">' + esc(label) + "</span>";
    if (!runs.length) return h + "</div>";
    const r = runs[0];
    h += '<span class="ans" dir="auto">' + esc(r.ans || (r.cor === 1 ? "1" : r.cor === 0 ? "0" : "")) + "</span>";
    if (KEYM && r.ans && r.cor != null) h += '<span class="score">' + esc(t(r.cor ? "scored1" : "scored0")) + "</span>";
    runs.slice(1).forEach((x, i) => {
      h += x.same ? '<span class="rerun">' + esc(t("runSame", { k: i + 2 })) + "</span>"
        : '<span class="rerun diff">' + esc(t("runDiff", { k: i + 2 })) + '<span class="num" dir="auto">' + esc(x.ans || String(x.cor)) + "</span>" +
          (KEYM && x.ans && x.cor != null ? ' <span class="score">' + esc(t(x.cor ? "scored1" : "scored0")) + "</span>" : "") + "</span>";
    });
    return h + "</div>";
  }
  function ctxHTML(c, i) {
    if (!c.rem.length && !c.add.length) return "";
    const li = (x) => '<li><span dir="auto">' + esc(x) + "</span></li>";
    return '<details class="ctx" data-k="ctx-' + esc(c.id) + '"><summary>' + esc(t("ctx", { n: c.rem.length + c.add.length })) + '</summary><div class="ctxgrid"><div><p class="small muted">' +
      esc(t("removed")) + "</p><ul>" + c.rem.map(li).join("") + '</ul></div><div><p class="small muted">' + esc(t("added")) + "</p><ul>" + c.add.map(li).join("") +
      '</ul></div></div><p class="small muted" style="padding-top:10px">' + esc(t("kept", { n: c.kept })) + " " + esc(t("ctxNote")) + "</p></details>";
  }
  function cardHTML(c, i) {
    const D = state.D, KEYM = state.mode === "key";
    let h = '<article class="card ' + D.classes[c.state] + '" id="c-' + i + '" data-i="' + i + '"><div class="head"><span class="pill">' + esc(pillText(c)) +
      '</span><span class="small muted">' + esc(t("caseN", { id: "" })) + '<span class="num" dir="auto">' + esc(c.id) + "</span></span></div>";
    if (c.q) h += '<p class="q" dir="auto">' + esc(c.q) + "</p>";
    if (c.state === "correct_both") h += '<p class="small muted">' + esc(t("correctChangedNote")) + "</p>";
    if (KEYM && c.expected) h += '<p class="small muted">' + esc(t("expected")) + '<span class="num" dir="auto">' + esc(c.expected) + "</span></p>";
    h += '<div class="pair">' + sideHTML(t("current"), c.b) + sideHTML(t("proposed"), c.u) + "</div>";
    if (c.err) h += '<p class="errs">' + esc(t("runErrors")) + '<span class="num" dir="ltr">' + esc(c.err) + "</span></p>";
    h += ctxHTML(c, i);
    if (!KEYM && c.state === "stable_change") {
      h += '<div class="judge"><span class="small muted">' + esc(t("yourCall")) + "</span>" + JUDGMENTS.map((k) =>
        '<button type="button" data-judge="' + k + '" data-i="' + i + '" aria-pressed="' + (state.judge[c.id] === k) + '">' + esc(t(k)) + "</button>").join("") + "</div>";
    }
    return h + "</article>";
  }
  function judgedText() {
    const ids = state.D.stable_change_ids, cnt = (k) => ids.filter((id) => state.judge[id] === k).length;
    const w = cnt("worse"), b = cnt("better"), s = cnt("same_meaning");
    return t("judged", { w, b, s, u: ids.length - w - b - s });
  }
  /* Cards are drawn a page at a time, so a report with thousands of cases to review opens at once. */
  function matching() {
    const out = [];
    state.D.cards.forEach((c, i) => { if (state.filter === "all" || (state.filter === "uns" ? c.state === "unstable" || c.flag === "varied" : isStable(c))) out.push(i); });
    return out;
  }
  function applyFilter() {
    const open = Array.from(document.querySelectorAll("#cards details[open][data-k]")).map((d) => d.dataset.k);
    const all = matching(), part = all.slice(0, state.shown);
    let h = part.map((i) => cardHTML(state.D.cards[i], i)).join("");
    if (!all.length) h += '<p class="muted" id="empty">' + esc(state.D.cards.length ? t("noneView") : t("none")) + "</p>";
    if (all.length > part.length) {
      h += '<div class="row more"><span class="small muted" id="shown-of">' + esc(t("shownOf", { a: part.length, b: all.length })) + '</span><button type="button" id="more">' +
        esc(t("showMore", { n: Math.min(PAGE, all.length - part.length) })) + '</button><button type="button" id="show-all">' + esc(t("showAll", { n: all.length })) + "</button></div>";
    }
    $("cards").innerHTML = h;
    open.forEach((k) => { const d = Array.from(document.querySelectorAll("#cards details[data-k]")).find((x) => x.dataset.k === k); if (d) d.open = true; });
    document.querySelectorAll("[data-filter]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.filter === state.filter));
  }
  /* Above STRIP_MAX cases one cell per case is too many to draw or to read: one bar shows each state's share. */
  function stripHTML() {
    const D = state.D;
    if (D.strip.length > STRIP_MAX) {
      const counts = D.summary.states, n = D.strip.length;
      return '<div class="bar" role="img" aria-label="' + esc(t("stripBar", { max: STRIP_MAX, n })) + '">' + Object.keys(counts).filter((s) => counts[s]).map((s) =>
        '<span class="seg ' + state.D.classes[s] + '" style="flex-grow:' + counts[s] + '" title="' + esc(L().state[s] + ": " + counts[s]) + '"></span>').join("") +
        '</div><p class="small muted">' + esc(t("stripBar", { max: STRIP_MAX, n })) + "</p>";
    }
    return '<div class="strip" role="list">' + D.strip.map((x) => {
      const id = x[0], s = x[1], card = x[2];
      const label = esc(t("caseN", { id }) + ": " + (card >= 0 ? pillText(D.cards[card]) : L().state[s]));
      return card >= 0
        ? '<button type="button" class="cell ' + state.D.classes[s] + '" role="listitem" data-go="' + card + '" title="' + label + '" aria-label="' + label + '"></button>'
        : '<span class="cell open ' + state.D.classes[s] + '" role="listitem" title="' + label + '"></span>';
    }).join("") + '</div><p class="small muted">' + esc(t("stripNote")) + "</p>";
  }
  function reportHTML() {
    const D = state.D, S = D.summary, KEYM = state.mode === "key";
    let h = "";
    h += "<section><h2>" + esc(t("ledger")) + '</h2><div class="ledger">' + D.tiles.map((s) => tile(s, L().sub[s] || t("unconfSub"))).join("");
    h += "</div>" + stripHTML();
    h += '<p class="small muted">' + esc(t("stableNote", { b: S.runs_per_version.current, u: S.runs_per_version.proposed })) + "</p>";
    if (!KEYM && D.stable_change_ids.length) h += '<p class="small" id="judged">' + esc(judgedText()) + "</p>";
    h += "</section>";

    const F = S.first_run, ch = F.change_between_versions, rb = F.rerun_variation_current, ru = F.rerun_variation_proposed;
    const pT = pct(ch.count, ch.n), pB = rb ? pct(rb.count, rb.n) : null, pU = ru ? pct(ru.count, ru.n) : null;
    const top = Math.max(5, Math.ceil(Math.max(pT, pB || 0, pU || 0) / 5) * 5);
    const bar = (label, p, k, m, main) => '<span class="lab">' + esc(label) + '</span><span class="track"><span class="fill' + (main ? " main" : "") + '" style="width:' + (100 * p / top) +
      '%"></span></span><span class="val num">' + fmt(p) + '% <span class="muted">(' + esc(t("of", { k, n: m })) + ")</span></span>";
    h += "<section><h2>" + esc(t("rates")) + '</h2><div class="panel"><div class="bars">' + bar(t("barMain"), pT, ch.count, ch.n, true);
    if (pB !== null) h += bar(t("barB"), pB, rb.count, rb.n, false);
    if (pU !== null) h += bar(t("barU"), pU, ru.count, ru.n, false);
    h += "</div><p>";
    if (pB === null || pU === null) h += esc(t("rateNone"));
    else if (pT <= Math.max(pB, pU)) h += esc(t("rateWithin"));
    else h += esc(t("rateAbove", { t: fmt(pT), b: fmt(pB), u: fmt(pU) }));
    h += "</p>";
    if (D.acc) {
      const d = pct(D.acc.b, D.acc.n) - pct(D.acc.a, D.acc.n);
      h += '<p class="small muted">' + esc(t("acc", { a: fmt(pct(D.acc.a, D.acc.n)), b: fmt(pct(D.acc.b, D.acc.n)), d: (d > 0 ? "+" : d < 0 ? "−" : "") + fmt(Math.abs(d)), r: D.acc.r, i: D.acc.i })) + "</p>";
      if (D.acc.n >= 3 && !D.acc.a && !D.acc.b) h += '<p class="small warn">' + esc(t("noneCorrect")) + "</p>";
      const c = 2 * Math.min(D.acc.r, D.acc.i);
      if (c) h += '<p class="small muted">' + esc(t("masked", { m: D.acc.r + D.acc.i, v: Math.abs(D.acc.i - D.acc.r), c })) + "</p>";
    }
    if (D.summary.passages) { const P = D.summary.passages, F = P.by_state[D.focus];
      h += '<p class="small muted">' + esc(P.differ === P.cases_with_passages && P.cases_with_passages > 1 ? t("passagesAll", { n: P.cases_with_passages })
        : !P.differ ? t("passagesNone", { n: P.cases_with_passages })
        : t("passages", { k: P.differ, n: P.cases_with_passages }) + (F ? t("passagesFocus", { k: F.differ, n: F.n }) : "") + t("passagesNote")) + "</p>"; }
    if ((D.summary.labelled_by_similarity || []).length) { const ids = D.summary.labelled_by_similarity;
      h += '<p class="small muted">' + esc(t("bySimilarity", { n: ids.length, ids: ids.slice(0, 20).join(", ") + (ids.length > 20 ? ", …" : "") })) + "</p>"; }
    h += '<p class="small muted">' + esc(t("rateFirst")) + (Math.max(S.runs_per_version.current, S.runs_per_version.proposed) > 2
      ? " " + esc(t("anyRun", { b: S.any_run_disagreement.current, u: S.any_run_disagreement.proposed })) : "") + "</p></div></section>";

    h += "<section><h2>" + esc(t("review")) + ' <span class="num muted">' + D.cards.length + '</span></h2><div class="filters">' +
      [["all", "fAll"], ["stable", "fStable"], ["uns", "fUns"]].map((f) => '<button type="button" data-filter="' + f[0] + '">' + esc(t(f[1])) + "</button>").join("") +
      '</div><div class="cards" id="cards"></div>';
    if (KEYM && D.wrong.length) {
      const flagged = D.wrong.filter((w) => w[2]).length;
      h += '<details class="wrongs panel" data-k="wrongs"><summary>' + esc(t("wrongList", { n: D.wrong.length })) + '</summary><p class="small muted" style="padding-top:8px">' + esc(t("wrongNote")) +
        (flagged ? " " + esc(t("wrongChanged", { n: flagged })) : "") + (D.wrong.length > LIST_MAX ? " " + esc(t("wrongMore", { a: LIST_MAX, n: D.wrong.length })) : "") + "</p><ul>" + D.wrong.slice(0, LIST_MAX).map((w) => '<li><span class="num muted">' + esc(w[0]) + '</span> <span dir="auto">' + esc(w[1]) + "</span>" +
        (w[2] ? ' <span class="tag">' + esc(L().pill["wrong_both" + (w[2] === "stable" ? "_changed" : w[2] === "varied" ? "_varied" : "_changed_unconfirmed")]) + "</span>" : "") + "</li>").join("") + "</ul></details>";
    }
    h += '<div class="out"><div class="row">' + (!KEYM && D.stable_change_ids.length ? '<button type="button" id="copy-j">' + esc(u("copyJ")) + '</button><button type="button" id="forget">' + esc(u("forget")) + "</button>" : "") +
      (D.cards.length || D.wrong.length ? '<button type="button" id="copy-r">' + esc(u("copyR")) + "</button>" : "") +
      '<span class="small muted" id="copy-msg" role="status"></span></div><textarea id="csv-out" hidden readonly dir="ltr" aria-label="CSV"></textarea></div></section>';
    return h;
  }

  /* ---------- page ---------- */
  function render() {
    const open = Array.from(document.querySelectorAll("details[open][data-k]")).map((d) => d.dataset.k);
    const app = $("app");
    document.documentElement.lang = state.lang; app.dir = state.lang === "ar" ? "rtl" : "ltr";
    $("t-name").textContent = u("name"); $("lang").textContent = u("langBtn"); $("lang").lang = state.lang === "ar" ? "en" : "ar"; $("t-tagline").textContent = u("tagline");
    $("btn-sample-key").textContent = u("sampleKey"); $("btn-sample-nokey").textContent = u("sampleNoKey");
    $("t-set-label").textContent = u("setLabel"); $("opt-set-library").textContent = u("setLibrary"); $("opt-set-medicines").textContent = u("setMedicines");
    $("sample-set").value = state.set;
    $("t-why").textContent = u("whyTitle"); $("t-why-list").innerHTML = UI[state.lang].whyList.map((x) => "<li>" + esc(x) + "</li>").join("");
    $("btn-sample-key").setAttribute("aria-pressed", state.source === "sample-key");
    $("btn-sample-nokey").setAttribute("aria-pressed", state.source === "sample-nokey");
    $("t-own").textContent = u("own"); $("t-choose").textContent = u("choose"); $("t-paste").textContent = u("paste"); $("btn-run").textContent = u("run");
    $("t-privacy").textContent = u("privacy"); $("t-format").textContent = u("format"); $("t-cols-note").textContent = u("colsNote");
    $("t-cols").innerHTML = UI[state.lang].cols.map((x) => "<li>" + x + "</li>").join("");
    $("t-opts").textContent = u("opts"); $("t-mode-label").textContent = u("modeLabel"); $("t-sim-label").textContent = u("sameWhen");
    $("opt-auto").textContent = u("modeAuto"); $("opt-nokey").textContent = u("modeNoKey");
    $("opt-sim1").textContent = u("simExact"); $("opt-sim90").textContent = u("sim90"); $("opt-sim75").textContent = u("sim75");
    $("mode").value = state.modePref; $("sim").value = String(state.sim);
    $("t-get").textContent = u("getTitle"); $("t-get-list").innerHTML = UI[state.lang].getList.map((x) => "<li>" + esc(x) + "</li>").join("");
    if (state.errorCode) state.error = fill(UI[state.lang].err[state.errorCode.code] || UI[state.lang].err.read, state.errorCode.info);
    const err = $("err"); err.hidden = !state.error; err.textContent = state.error || "";
    if (!state.D) { $("report").innerHTML = ""; return; }
    let note = "<span>" + esc(state.source === "sample-key" ? u(state.set === "medicines" ? "noteKeyMed" : "noteKey") : state.source === "sample-nokey" ? u(state.set === "medicines" ? "noteNoKeyMed" : "noteNoKey") : u(state.A.n === 1 ? "noteFileOne" : "noteFile", { n: state.A.n })) + "</span>";
    note += "<span>" + esc(state.mode === "key" ? t("modeNote") : t("modeNote", { rule: state.sim >= 1 ? t("simExact") : t("simWords", { p: fmt(state.sim * 100) }) })) + "</span>";
    $("source-note").innerHTML = note;
    $("t-limits").textContent = t("limits"); $("t-limit-list").innerHTML = L().limitList.map((x) => "<li>" + esc(x) + "</li>").join("");
    $("report").innerHTML = reportHTML();
    open.forEach((k) => { const d = Array.from(document.querySelectorAll("details[data-k]")).find((x) => x.dataset.k === k); if (d) d.open = true; });
    applyFilter();
  }
  function copyOut(text, button) {
    const msg = $("copy-msg"), out = $("csv-out");
    const fail = () => { out.hidden = false; out.value = text; out.focus(); out.select(); msg.textContent = u("copyFail"); };
    const done = () => {
      msg.textContent = u("copied"); out.hidden = false; out.value = text;
      const label = button.textContent;                 /* the button itself says so for two seconds */
      button.textContent = "\u2713 " + u("copied"); button.classList.add("done");
      setTimeout(() => { if (button.isConnected) { button.textContent = label; button.classList.remove("done"); } }, 2000);
    };
    try { navigator.clipboard.writeText(text).then(done, fail); } catch (e) { fail(); }
  }

  $("lang").addEventListener("click", () => { state.lang = state.lang === "ar" ? "en" : "ar"; store.set("ridi-lang", state.lang); render(); });
  $("btn-sample-key").addEventListener("click", () => { state.errorCode = null; load("sample-key", SAMPLES[state.set]); });
  $("btn-sample-nokey").addEventListener("click", () => { state.errorCode = null; load("sample-nokey", SAMPLES[state.set]); });
  $("sample-set").addEventListener("change", (ev) => {
    state.set = ev.target.value === "medicines" ? "medicines" : "library"; state.errorCode = null;
    load(state.source === "sample-nokey" ? "sample-nokey" : "sample-key", SAMPLES[state.set]);
  });
  $("btn-run").addEventListener("click", () => { state.errorCode = null; load("file", $("paste").value); });
  $("file").addEventListener("change", (ev) => {
    const f = ev.target.files && ev.target.files[0]; if (!f) return;
    const rd = new FileReader();
    rd.onload = () => {
      const bytes = new Uint8Array(rd.result); let text = null;
      const enc = bytes[0] === 0xFF && bytes[1] === 0xFE ? "utf-16le" : bytes[0] === 0xFE && bytes[1] === 0xFF ? "utf-16be" : "utf-8";
      try { text = new TextDecoder(enc, { fatal: true }).decode(bytes); } catch (e) { text = null; }
      if (text === null || text.indexOf("\0") >= 0) { state.errorCode = { code: "encoding", info: {} }; render(); return; }
      /* A large file is checked without being copied into the text box, which would double what the page holds. */
      $("paste").value = text.length <= INPUT_LIMIT ? text : "";
      $("paste").placeholder = text.length <= INPUT_LIMIT ? "" : u("tooBig", { n: text.length.toLocaleString("en") });
      state.errorCode = null; load("file", text);
    };
    rd.onerror = () => { state.errorCode = { code: "read", info: {} }; render(); };
    rd.readAsArrayBuffer(f);
  });
  $("mode").addEventListener("change", (ev) => { state.modePref = ev.target.value; if (state.source === "file") { state.errorCode = null; load("file", state.text); } });
  $("sim").addEventListener("change", (ev) => { state.sim = parseFloat(ev.target.value); state.errorCode = null; load(state.source, state.text); });
  $("report").addEventListener("click", (ev) => {
    const b = ev.target.closest("button"); if (!b) return;
    if (b.dataset.filter) { state.filter = b.dataset.filter; state.shown = PAGE; applyFilter(); }
    else if (b.id === "more") { state.shown += PAGE; applyFilter(); }
    else if (b.id === "show-all") { state.shown = Infinity; applyFilter(); }
    else if (b.dataset.judge) {
      const id = state.D.cards[+b.dataset.i].id;
      if (state.judge[id] === b.dataset.judge) delete state.judge[id]; else state.judge[id] = b.dataset.judge;
      store.set(judgeKey(), JSON.stringify(state.judge));
      b.parentElement.querySelectorAll("[data-judge]").forEach((x) => x.setAttribute("aria-pressed", state.judge[id] === x.dataset.judge));
      const line = $("judged"); if (line) line.textContent = judgedText();
    }
    else if (b.dataset.go) {   /* the card may be on a page that is not drawn yet */
      if (state.filter !== "all" || +b.dataset.go >= state.shown) { state.filter = "all"; state.shown = Math.max(state.shown, +b.dataset.go + 1); applyFilter(); }
      const el = $("c-" + b.dataset.go); if (el) el.scrollIntoView({ block: "start" });
    }
    else if (b.id === "copy-j") {
      const ids = state.D.stable_change_ids.filter((id) => state.judge[id]);
      copyOut(RidiCore.toCsv(["case_id", "judgment"], ids.map((id) => [id, state.judge[id]])), b);
    }
    else if (b.id === "copy-r") { const r = RidiCore.reviewTable(state.A, state.judge); copyOut(RidiCore.toCsv(r.header, r.rows), b); }
    else if (b.id === "forget") { state.judge = {}; store.del(judgeKey()); render(); }
  });

  const kept = tab.get();
  if (kept) { $("paste").value = kept; load("file", kept); }
  if (!state.D) { state.errorCode = null; load("sample-key", SAMPLE); }
})();

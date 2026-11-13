"""Report text in English and Arabic. Taken from the browser prototype, with additions.

Wording rules (requirements, see README "Limits"):
- without an answer key or an owner judgment a difference is a "change", never a "regression";
- a passage without a relevance grade is "ungraded";
- nothing here says or implies that a system is safe, certified or approved.

The strings for answer-key mode are kept apart so a no-key report does not carry them at all.
"""

from __future__ import annotations

COMMON = {
    "en": {
        "passages": "The retrieved passages differ between the versions in {k} of the {n} cases that list passages.",
        "passagesNote": " This is a count, not a cause.",
        "passagesOrder": " In {r} case(s) the same passages come in another order or number.",
        "ctxOrder": "The same passages were retrieved, in another order or another number of times.",
        "passagesContent": " In {r} case(s) a passage kept its name while its content changed.",
        "ctxMoved": "In both versions, with a change", "ctxRank": "rank {a} → {b}", "ctxScore": "score {a} → {b}",
        "ctxContent": "content changed",
        "passagesAll": "The retrieved passages differ between the versions in all {n} cases that list passages, so "
                       "this count does not set any group of cases apart. An update that changes how documents are "
                       "split, or how passages are named, gives this result.",
        "passagesNone": "The retrieved passages are the same in both versions in all {n} cases that list passages.",
        "passagesNoneOne": "The retrieved passages are the same in both versions in the one case that lists passages.",
        "caseOnly": "{n} case(s) hold answers that differ only in letter case, as in mg and Mg, which is not counted "
                    "as a change: {ids}. Read them where the case of a letter carries meaning.",
        "name": "RIDI Update Check",
        "langBtn": "العربية",
        "tagline": "The current and the proposed version of an assistant, run on the same questions. "
                   "Which answers changed, and which changes hold when each version is run again.",
        "headline": "What did the update change, and which changes hold on re-run?",
        "diffNote": "Highlighting shows where the first-run answers of the two versions differ, word by word.",
        "source": "{n} cases from {file}. Report written {when} by ridi-check {version}.",
        "sourceOne": "1 case from {file}. Report written {when} by ridi-check {version}.",
        "versions": "Current version: {a}. Proposed version: {b}.",
        "ledger": "Where each case landed",
        "state": {
            "unstable": "Unstable on re-run",
            "incomplete": "Not compared",
        },
        "sub": {
            "unstable": "A version disagreed with itself",
            "incomplete": "A call failed, so a first-run answer is missing",
        },
        "pill": {
            "unstable": "Unstable on re-run",
            "incomplete": "Not compared: a call failed",
        },
        "unconfSub": "Not confirmed by a second run",
        "stableNote": "A case is stable when every repeated run of each version agreed with that version's first run. "
                      "Runs per version in this file: current {b}, proposed {u}. "
                      "Two runs is a thin estimate of the execution floor (re-run variation); more runs make the stable label firmer.",
        "stripNote": "Each cell is one case, in file order. Select a coloured cell to open it.",
        "stripBar": "With more than {max} cases the strip is one bar: each colour's share of the {n} cases.",
        "shownOf": "Showing {a} of {b}.", "showMore": "Show {n} more", "showAll": "Show all {n}",
        "rates": "Change between versions against the execution floor",
        "barMain": "Current vs proposed", "barB": "Current repeated runs", "barU": "Proposed repeated runs",
        "of": "{k} of {n}",
        "rateWithin": "The overall change is no larger than the execution floor (the re-run variation of one version). "
                      "Read the stable cases below, not the total.",
        "rateAbove": "The overall change ({t}%) is larger than the execution floor from repeated runs "
                     "({b}% and {u}%). The stable cases below are the changes that held on re-run.",
        "rateNone": "This file has no second run of both versions, so the execution floor is unknown and "
                    "no change is confirmed. Add a repeated run of each version.",
        "rateFirst": "These rates use the first run of each version. The execution floor uses run 1 against run 2.",
        "interval95": "; 95% interval {a}% to {b}%",
        "intervalNote": "The intervals are Wilson intervals. They treat the cases as a random sample of what users "
                        "ask, which a hand-picked set is not, and they say nothing about one case's own re-run "
                        "variation. The execution floor is the larger of the two re-run rates: a comparison of "
                        "point estimates, not an exact test. Nothing here is decided by these intervals.",
        "exactNone": "No matched item has two runs of both versions, so the exact conditional test is not computed.",
        "exactTest": "Exact conditional test on {n} matched items: one-sided p = {p} that the between-version change "
                     "exceeds both run-to-run disagreements. Change rate minus the larger re-run rate = {e}.",
        "exactInterval": " Conditional 95% interval for that difference: {lo} to {hi}.",
        "exactNoInterval": " The conditional interval is undefined because a version has no discordant items.",
        "exactPending": " Implementation pending confirmation against the registered protocol. This does not replace "
                        "the rounded-rate comparison, and the release gate ignores it unless --exact-test is set.",
        "anyRun": "With more than two runs a case can be unstable because of a later run. "
                  "Cases where any run differed from the first: current {b}, proposed {u}.",
        "review": "Cases to review", "fAll": "All", "fStable": "Stable", "fUns": "Unstable",
        "none": "No case changed.", "noneView": "No cases in this view.",
        "current": "Current version", "proposed": "Proposed version",
        "runSame": "Run {k}: same answer", "runDiff": "Run {k}: ",
        "runErrors": "Failed calls: ",
        "ctx": "Passages that differ ({n})", "removed": "Only in the current version",
        "added": "Only in the proposed version",
        "kept": "{n} passages are in both.",
        "ctxNote": "Passages are ungraded here. A passage with no relevance grade can still carry the evidence.",
        "caseN": "Case {id}",
        "limits": "What this check does not tell you",
        "limitList": [
            "It finds change, not correctness. A version that is wrong the same way every time looks stable.",
            "A changed answer is not always a worse one. With an answer key, the result is only as good as the key.",
            "Two runs per version is a thin estimate of re-run variation. More runs make the stable label firmer.",
            "It is not a safety certificate, and it has not been tested on agents that use tools.",
        ],
    },
    "ar": {
        "passages": "المقاطع المسترجعة تختلف بين النسختين في {k} من {n} حالة ذُكرت مقاطعها.",
        "passagesNote": " هذا عدّ وليس سبباً.",
        "passagesOrder": " وفي {r} حالة جاءت المقاطع نفسها بترتيب أو عدد مختلف.",
        "ctxOrder": "استُرجعت المقاطع نفسها، لكن بترتيب مختلف أو بعدد مرات مختلف.",
        "passagesContent": " وفي {r} حالة بقي اسم المقطع وتغيّر محتواه.",
        "ctxMoved": "في النسختين، مع تغيّر", "ctxRank": "الرتبة {a} ← {b}", "ctxScore": "الدرجة {a} ← {b}",
        "ctxContent": "تغيّر المحتوى",
        "passagesAll": "المقاطع المسترجعة تختلف بين النسختين في كل الحالات التي ذُكرت مقاطعها وعددها {n}، فهذا العدّ "
                       "لا يميّز أي مجموعة من الحالات. يحدث ذلك حين يغيّر التحديث طريقة تقسيم المستندات أو تسمية "
                       "المقاطع.",
        "passagesNone": "المقاطع المسترجعة متطابقة بين النسختين في كل الحالات التي ذُكرت مقاطعها وعددها {n}.",
        "passagesNoneOne": "المقاطع المسترجعة متطابقة بين النسختين في الحالة الوحيدة التي ذُكرت مقاطعها.",
        "caseOnly": "عدد الحالات التي تختلف إجاباتها في حالة الأحرف فقط (مثل mg و Mg) ولا تُحسب تغيّراً: {n}، وهي: "
                    "{ids}. اقرأها حيث يكون لحالة الحرف معنى.",
        "name": "RIDI Update Check",
        "langBtn": "English",
        "tagline": "النسخة الحالية والنسخة المقترحة من المساعد على الأسئلة نفسها. "
                   "أي الإجابات تغيّرت، وأي تغيّر يثبت عند إعادة تشغيل كل نسخة.",
        "headline": "ماذا غيّر التحديث، وأي تغيّر يثبت عند إعادة التشغيل؟",
        "diffNote": "التظليل يبيّن مواضع اختلاف إجابتَي التشغيل الأول للنسختين، كلمة بكلمة.",
        "source": "{n} حالة من {file}. كُتب التقرير {when} بواسطة ridi-check {version}.",
        "sourceOne": "حالة واحدة من {file}. كُتب التقرير {when} بواسطة ridi-check {version}.",
        "versions": "النسخة الحالية: {a}. النسخة المقترحة: {b}.",
        "ledger": "أين انتهت كل حالة",
        "state": {
            "unstable": "متقلبة عند الإعادة",
            "incomplete": "لم تُقارَن",
        },
        "sub": {
            "unstable": "نسخة خالفت نفسها عند إعادة التشغيل",
            "incomplete": "فشل استدعاء، فإجابة التشغيل الأول ناقصة",
        },
        "pill": {
            "unstable": "متقلبة عند الإعادة",
            "incomplete": "لم تُقارَن: فشل استدعاء",
        },
        "unconfSub": "لم يؤكدها تشغيل ثانٍ",
        "stableNote": "تُعدّ الحالة ثابتة عندما يوافق كل تشغيل متكرر لكل نسخة تشغيلها الأول. "
                      "عدد التشغيلات لكل نسخة في هذا الملف: الحالية {b}، المقترحة {u}. "
                      "تشغيلان تقدير ضعيف لأرضية التنفيذ (تقلب إعادة التشغيل)، وتشغيلات أكثر تجعل وصف «ثابت» أوثق.",
        "stripNote": "كل خانة حالة واحدة، بترتيب الملف. اختر خانة ملوّنة لفتحها.",
        "stripBar": "مع أكثر من {max} حالة يُرسم الشريط خطاً واحداً: نصيب كل لون من الحالات وعددها {n}.",
        "shownOf": "المعروض {a} من {b}.", "showMore": "اعرض {n} أخرى", "showAll": "اعرض الكل ({n})",
        "rates": "التغيّر بين النسختين مقابل أرضية التنفيذ",
        "barMain": "الحالية مقابل المقترحة", "barB": "الحالية، تشغيلات متكررة", "barU": "المقترحة، تشغيلات متكررة",
        "of": "{k} من {n}",
        "rateWithin": "التغيّر الإجمالي لا يتجاوز أرضية التنفيذ (تقلب إعادة التشغيل في إحدى النسختين). "
                      "اعتمد على الحالات الثابتة أدناه لا على المجموع.",
        "rateAbove": "التغيّر الإجمالي ({t}%) أكبر من أرضية التنفيذ من التشغيلات المتكررة "
                     "({b}% و{u}%). الحالات الثابتة أدناه هي التغيّرات التي ثبتت عند الإعادة.",
        "rateNone": "لا يوجد في هذا الملف تشغيل ثانٍ للنسختين، فأرضية التنفيذ مجهولة ولا يُؤكَّد أي تغيّر. "
                    "أضف تشغيلاً متكرراً لكل نسخة.",
        "rateFirst": "هذه النسب تعتمد على التشغيل الأول لكل نسخة. أرضية التنفيذ تقارن التشغيل الأول بالثاني.",
        "interval95": "؛ فترة 95%: من {a}% إلى {b}%",
        "intervalNote": "الفترات هي فترات Wilson. تفترض أن الحالات عينة عشوائية مما يسأله المستخدمون، والمجموعة "
                        "المنتقاة يدوياً ليست كذلك، ولا تقول شيئاً عن تقلب الحالة الواحدة عند إعادة التشغيل. "
                        "أرضية التنفيذ هي أكبر نسبتي إعادة التشغيل: مقارنة لتقديرات نقطية لا اختباراً دقيقاً. "
                        "لا يُبنى على هذه الفترات أي قرار هنا.",
        "exactNone": "لا يوجد بند متطابق له تشغيلان لكلتا النسختين، فالاختبار الشرطي الدقيق غير محسوب.",
        "exactTest": "الاختبار الشرطي الدقيق على {n} بنداً متطابقاً: قيمة p أحادية الطرف = {p} لكون تغيّر النسختين "
                     "يتجاوز اختلافي إعادة التشغيل. نسبة التغيّر ناقص أكبر نسبة إعادة تشغيل = {e}.",
        "exactInterval": " الفترة الشرطية 95% لهذا الفرق: {lo} إلى {hi}.",
        "exactNoInterval": " الفترة الشرطية غير معرّفة لأن نسخة ليس لها بنود متنافرة.",
        "exactPending": " التنفيذ بانتظار التأكيد مقابل البروتوكول المسجّل. هذا لا يستبدل مقارنة النسب المُقرَّبة، "
                        "وبوابة الإصدار تتجاهله ما لم يُمرَّر --exact-test.",
        "anyRun": "مع أكثر من تشغيلين قد تكون الحالة متقلبة بسبب تشغيل لاحق. "
                  "الحالات التي خالف فيها أي تشغيل التشغيلَ الأول: الحالية {b}، المقترحة {u}.",
        "review": "حالات للمراجعة", "fAll": "الكل", "fStable": "الثابتة", "fUns": "المتقلبة",
        "none": "لم تتغيّر أي حالة.", "noneView": "لا توجد حالات في هذا العرض.",
        "current": "النسخة الحالية", "proposed": "النسخة المقترحة",
        "runSame": "التشغيل {k}: الإجابة نفسها", "runDiff": "التشغيل {k}: ",
        "runErrors": "استدعاءات فشلت: ",
        "ctx": "المقاطع المختلفة ({n})", "removed": "في النسخة الحالية فقط",
        "added": "في النسخة المقترحة فقط",
        "kept": "{n} مقطع مشترك بين النسختين.",
        "ctxNote": "المقاطع هنا بلا درجة صلة. المقطع الذي بلا درجة صلة قد يحمل الدليل.",
        "caseN": "الحالة {id}",
        "limits": "ما لا يخبرك به هذا الفحص",
        "limitList": [
            "يكشف التغيّر لا الصحة. النسخة التي تخطئ بالطريقة نفسها كل مرة تبدو ثابتة.",
            "الإجابة المتغيّرة ليست دائمًا أسوأ. ومع مفتاح الإجابات، النتيجة بجودة المفتاح.",
            "تشغيلان لكل نسخة تقدير ضعيف لتقلب التشغيل. تشغيلات أكثر تجعل وصف «ثابت» أوثق.",
            "ليس شهادة سلامة، ولم يُختبر على إيجنتات تستخدم أدوات.",
        ],
    },
}

KEY_MODE = {
    "en": {
        "modeNote": "Answer-key mode: two results count as the same when both are correct or both are wrong.",
        "state": {
            "stable_regression": "Stable regressions", "stable_improvement": "Stable improvements",
            "regression_unconfirmed": "Regressions, not re-run", "improvement_unconfirmed": "Improvements, not re-run",
            "wrong_both": "Wrong in both versions", "correct_both": "Correct in both versions",
        },
        "sub": {
            "stable_regression": "Right before, wrong after, in every run",
            "stable_improvement": "Wrong before, right after, in every run",
            "wrong_both": "No change, still wrong", "correct_both": "No change",
        },
        "pill": {
            "stable_regression": "Stable regression", "stable_improvement": "Stable improvement",
            "regression_unconfirmed": "Regression, not re-run", "improvement_unconfirmed": "Improvement, not re-run",
            "wrong_both": "Wrong in both versions",
            "wrong_both_changed": "Wrong in both, answer changed",
            "wrong_both_changed_unconfirmed": "Wrong in both, answer changed, not re-run",
            "wrong_both_varied": "Wrong in both, answer varied on re-run",
            "correct_both_varied": "Correct in both, answer varied on re-run",
            "correct_both_changed": "Correct in both, answer changed",
            "correct_both_changed_unconfirmed": "Correct in both, answer changed, not re-run",
        },
        "wrongChanged": "{n} of them did not give the same wrong answer every time; they also appear "
                        "in the cases to review.",
        "correctChangedNote": "The answer key scores both answers as correct, so this case is not counted as a change. "
                              "The answers differ; read them if the wording matters, for example a number or a "
                              "condition.",
        "passagesFocus": " Among the stable regressions: {k} of {n}.",
        "acc": "On the first run, accuracy went from {a}% to {b}% ({d} points). Regressions: {r}. Improvements: {i}.",
        "noneCorrect": "No answer was scored correct in either version, so the scoring probably does not fit "
                       "the answers. Exact match rarely fits free text: check the expected answers, use a "
                       "scoring function, or compare the answers themselves (--mode nokey).",
        "masked": "Of the {m} answers that changed on the first run, mean accuracy shows {v}. "
                  "The other {c} cancel out: regressions against improvements.",
        "expected": "Expected: ",
        "scored1": "scored correct", "scored0": "scored wrong",
        "wrongList": "Wrong in both versions ({n})",
        "wrongNote": "This check looks for change. These answers did not change and are still wrong.",
        "wrongMore": "The first {a} are listed here; all {n} are in review_cases.csv.",
        "crossTitle": "Score and answer text, side by side",
        "crossNote": "Each row is what the score did, and each column what the answer text did, by the rule this "
                     "check uses when there is no answer key. The counts are cases. A score that changed with the "
                     "same answer, or an answer that changed with the same score, is worth reading.",
        "crossHead": "Score",
        "answerCol": {
            "stable_change": "Answer changed", "change_unconfirmed": "Answer changed, not re-run",
            "unstable": "Answer varied on re-run", "same": "Same answer", "no_answer_text": "No answer text",
        },
        "sameTextScored": "{n} case(s) hold the same answer text scored both correct and wrong: {ids}. The scoring "
                          "of these cases is not consistent: check the answer key or the scorer.",
        "scoreCheckBad": "Score check against {scorer}: {d} of {n} scored runs do not have the score it gives, in "
                         "{c} case(s): {ids}.",
        "scoreCheckOk": "Score check against {scorer}: all {n} scored runs have the score it gives. This shows that "
                        "the scores follow this scorer, not that the answer key is right.",
        "scoreCheckSkipped": " Not checked: {e} case(s) with no expected answer and {a} run(s) with no answer text.",
    },
    "ar": {
        "modeNote": "وضع مفتاح الإجابات: تُعدّ النتيجتان متطابقتين إذا كانتا صحيحتين معًا أو خاطئتين معًا.",
        "state": {
            "stable_regression": "تراجعات ثابتة", "stable_improvement": "تحسّنات ثابتة",
            "regression_unconfirmed": "تراجعات بلا إعادة تشغيل", "improvement_unconfirmed": "تحسّنات بلا إعادة تشغيل",
            "wrong_both": "خاطئة في النسختين", "correct_both": "صحيحة في النسختين",
        },
        "sub": {
            "stable_regression": "صحيحة قبل وخاطئة بعد، في كل تشغيل",
            "stable_improvement": "خاطئة قبل وصحيحة بعد، في كل تشغيل",
            "wrong_both": "لم تتغيّر وما زالت خاطئة", "correct_both": "لم تتغيّر",
        },
        "pill": {
            "stable_regression": "تراجع ثابت", "stable_improvement": "تحسّن ثابت",
            "regression_unconfirmed": "تراجع بلا إعادة تشغيل", "improvement_unconfirmed": "تحسّن بلا إعادة تشغيل",
            "wrong_both": "خاطئة في النسختين",
            "wrong_both_changed": "خاطئة في النسختين وتغيّرت الإجابة",
            "wrong_both_changed_unconfirmed": "خاطئة في النسختين وتغيّرت الإجابة، بلا إعادة تشغيل",
            "wrong_both_varied": "خاطئة في النسختين وتبدّلت الإجابة عند إعادة التشغيل",
            "correct_both_varied": "صحيحة في النسختين وتبدّلت الإجابة عند إعادة التشغيل",
            "correct_both_changed": "صحيحة في النسختين وتغيّرت الإجابة",
            "correct_both_changed_unconfirmed": "صحيحة في النسختين وتغيّرت الإجابة، بلا إعادة تشغيل",
        },
        "wrongChanged": "{n} منها لم تُعطِ الإجابة الخاطئة نفسها في كل مرة، وتظهر أيضًا ضمن حالات المراجعة.",
        "correctChangedNote": "مفتاح الإجابات يعدّ الإجابتين صحيحتين، فلا تُحسب هذه الحالة تغيّراً. "
                              "نص الإجابة اختلف؛ اقرأها إن كانت الصياغة مهمة، كرقم أو شرط.",
        "passagesFocus": " ومن التراجعات الثابتة: {k} من {n}.",
        "acc": "في التشغيل الأول انتقلت الدقة من {a}% إلى {b}% ({d} نقطة). التراجعات: {r}. التحسّنات: {i}.",
        "noneCorrect": "لم تُقيَّم أي إجابة صحيحةً في النسختين، فالأرجح أن طريقة التقييم لا تناسب الإجابات. "
                       "التطابق التام قلّما يناسب النص الحر: راجع الإجابات المتوقعة، أو استخدم دالة تقييم، "
                       "أو قارن الإجابات نفسها (‎--mode nokey).",
        "masked": "عدد الإجابات التي تغيّرت في التشغيل الأول: {m}. لا يُظهر متوسط الدقة منها إلا {v}، "
                  "والباقي ({c}) يلغي بعضه بعضًا: تراجعات مقابل تحسّنات.",
        "expected": "المتوقع: ",
        "scored1": "قُيّمت صحيحة", "scored0": "قُيّمت خاطئة",
        "wrongList": "خاطئة في النسختين ({n})",
        "wrongNote": "هذا الفحص يبحث عن التغيّر. هذه الإجابات لم تتغيّر وما زالت خاطئة.",
        "wrongMore": "تُعرض هنا أول {a} حالة؛ وكلها ({n}) في review_cases.csv.",
        "crossTitle": "الدرجة ونص الإجابة جنباً إلى جنب",
        "crossNote": "كل صف هو ما حدث للدرجة، وكل عمود هو ما حدث لنص الإجابة بالقاعدة التي يستخدمها هذا الفحص حين لا "
                     "يوجد مفتاح إجابات. الأعداد حالات. الدرجة التي تغيّرت والإجابة نفسها، أو الإجابة التي تغيّرت "
                     "والدرجة نفسها، تستحق القراءة.",
        "crossHead": "الدرجة",
        "answerCol": {
            "stable_change": "تغيّرت الإجابة", "change_unconfirmed": "تغيّرت الإجابة، بلا إعادة تشغيل",
            "unstable": "تبدّلت الإجابة عند إعادة التشغيل", "same": "الإجابة نفسها", "no_answer_text": "بلا نص إجابة",
        },
        "sameTextScored": "عدد الحالات التي فيها نص الإجابة نفسه قُيّم مرة صحيحاً ومرة خاطئاً: {n}، وهي: {ids}. "
                          "تقييم هذه الحالات غير متّسق: راجع مفتاح الإجابات أو دالة التقييم.",
        "scoreCheckBad": "فحص الدرجات مقابل {scorer}: {d} من {n} تشغيلاً مقيَّماً لا تحمل الدرجة التي يعطيها، في {c} "
                         "حالة: {ids}.",
        "scoreCheckOk": "فحص الدرجات مقابل {scorer}: كل التشغيلات المقيَّمة وعددها {n} تحمل الدرجة التي يعطيها. هذا "
                        "يبيّن أن الدرجات تتبع هذه الدالة، لا أن مفتاح الإجابات صحيح.",
        "scoreCheckSkipped": " لم يُفحص: {e} حالة بلا إجابة متوقعة و{a} تشغيلاً بلا نص إجابة.",
    },
}

NOKEY_MODE = {
    "en": {
        "passagesFocus": " Among the stable changes: {k} of {n}.",
        "bySimilarity": "{n} case(s) are labelled as they are because of the word-overlap rule; exact match would "
                        "label them differently: {ids}. Word overlap cannot tell which word matters, so read these "
                        "where one word decides.",
        "modeNote": "No answer key: two answers count as the same when {rule}. "
                    "A different answer is a change. Whether it is better or worse is your call.",
        "simExact": "they match after lower-casing and removing punctuation (signs such as < > + - % are kept)",
        "simWords": "they share at least {p}% of their words",
        "state": {
            "stable_change": "Stable changes", "change_unconfirmed": "Changes, not re-run", "same": "Same answer",
        },
        "sub": {"stable_change": "A different answer in every run", "same": "No change"},
        "pill": {"stable_change": "Stable change", "change_unconfirmed": "Change, not re-run"},
        "yourCall": "Your call:", "worse": "Worse", "better": "Better", "same_meaning": "Same meaning",
        "unsure": "Not sure",
        "judged": "Stable changes judged: {w} worse, {b} better, {s} same meaning, {u} still to decide.",
        "export": "Download judgments.csv",
        "exportHow": "Then count them: ridi-check report results.csv --judgments judgments.csv",
        "exportFail": "Copy the text below into a file named judgments.csv.",
    },
    "ar": {
        "passagesFocus": " ومن التغيّرات الثابتة: {k} من {n}.",
        "bySimilarity": "عدد الحالات التي صُنّفت كما هي بسبب قاعدة تداخل الكلمات: {n}، والمطابقة التامة كانت ستصنّفها "
                        "بغير ذلك: {ids}. تداخل الكلمات لا يعرف أي كلمة هي الحاسمة، فاقرأ هذه الحالات حيث تحسم "
                        "كلمة واحدة.",
        "modeNote": "بلا مفتاح إجابات: تُعدّ الإجابتان متطابقتين عندما {rule}. "
                    "الإجابة المختلفة تغيّر، والحكم بأنها أفضل أو أسوأ لك.",
        "simExact": "تتطابقان بعد توحيد حالة الأحرف وحذف علامات الترقيم (تبقى الرموز مثل < > + - %)",
        "simWords": "تشتركان في {p}% من الكلمات على الأقل",
        "state": {
            "stable_change": "تغيّرات ثابتة", "change_unconfirmed": "تغيّرات بلا إعادة تشغيل", "same": "الإجابة نفسها",
        },
        "sub": {"stable_change": "إجابة مختلفة في كل تشغيل", "same": "لم تتغيّر"},
        "pill": {"stable_change": "تغيّر ثابت", "change_unconfirmed": "تغيّر بلا إعادة تشغيل"},
        "yourCall": "حكمك:", "worse": "أسوأ", "better": "أفضل", "same_meaning": "المعنى نفسه",
        "unsure": "غير متأكد",
        "judged": "الحكم على التغيّرات الثابتة: {w} أسوأ، {b} أفضل، {s} بالمعنى نفسه، {u} بانتظار حكمك.",
        "export": "نزّل judgments.csv",
        "exportHow": "ثم احسبها: ridi-check report results.csv --judgments judgments.csv",
        "exportFail": "انسخ النص أدناه إلى ملف باسم judgments.csv.",
    },
}


def strings_for(mode: str) -> dict:
    """The string table for one mode, both languages."""
    extra = KEY_MODE if mode == "key" else NOKEY_MODE
    out = {}
    for lang in ("en", "ar"):
        table = {k: (dict(v) if isinstance(v, dict) else v) for k, v in COMMON[lang].items()}
        for name, value in extra[lang].items():
            if isinstance(value, dict):
                table.setdefault(name, {}).update(value)
            else:
                table[name] = value
        out[lang] = table
    return out

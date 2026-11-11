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
        "name": "RIDI Update Check",
        "langBtn": "العربية",
        "tagline": "The current and the proposed version of an assistant, run on the same questions. "
                   "Which answers changed, and which changes hold when each version is run again.",
        "source": "{n} cases from {file}. Report written {when} by ridi-check {version}.",
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
        "stableNote": "A case is stable when every run of each version agreed with that version's first run. "
                      "Runs per version in this file: current {b}, proposed {u}. "
                      "Two runs is a thin estimate of re-run variation; more runs make the stable label firmer.",
        "stripNote": "Each cell is one case, in file order. Select a coloured cell to open it.",
        "rates": "Change between versions against re-run variation",
        "barMain": "Current vs proposed", "barB": "Current, run twice", "barU": "Proposed, run twice",
        "of": "{k} of {n}",
        "rateWithin": "The overall change is no larger than the re-run variation of one version. "
                      "Read the stable cases below, not the total.",
        "rateAbove": "The overall change ({t}%) is larger than the re-run variation of both versions "
                     "({b}% and {u}%). The stable cases below are the changes that held on re-run.",
        "rateNone": "This file has no second run of both versions, so re-run variation is unknown and "
                    "no change is confirmed. Add a second run of each version.",
        "rateFirst": "These rates use the first run of each version and the first two runs for re-run variation.",
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
        "name": "RIDI Update Check",
        "langBtn": "English",
        "tagline": "النسخة الحالية والنسخة المقترحة من المساعد على الأسئلة نفسها. "
                   "أي الإجابات تغيّرت، وأي تغيّر يثبت عند إعادة تشغيل كل نسخة.",
        "source": "{n} حالة من {file}. كُتب التقرير {when} بواسطة ridi-check {version}.",
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
        "stableNote": "تُعدّ الحالة ثابتة عندما يوافق كل تشغيل لكل نسخة تشغيلها الأول. "
                      "عدد التشغيلات لكل نسخة في هذا الملف: الحالية {b}، المقترحة {u}. "
                      "تشغيلان تقدير ضعيف لتقلب إعادة التشغيل، وتشغيلات أكثر تجعل وصف «ثابت» أوثق.",
        "stripNote": "كل خانة حالة واحدة، بترتيب الملف. اختر خانة ملوّنة لفتحها.",
        "rates": "التغيّر بين النسختين مقابل تقلب إعادة التشغيل",
        "barMain": "الحالية مقابل المقترحة", "barB": "الحالية، تشغيلان", "barU": "المقترحة، تشغيلان",
        "of": "{k} من {n}",
        "rateWithin": "التغيّر الإجمالي لا يتجاوز تقلب إعادة التشغيل في إحدى النسختين. "
                      "اعتمد على الحالات الثابتة أدناه لا على المجموع.",
        "rateAbove": "التغيّر الإجمالي ({t}%) أكبر من تقلب إعادة التشغيل في النسختين "
                     "({b}% و{u}%). الحالات الثابتة أدناه هي التغيّرات التي ثبتت عند الإعادة.",
        "rateNone": "لا يوجد في هذا الملف تشغيل ثانٍ للنسختين، فتقلب التشغيل مجهول ولا يُؤكَّد أي تغيّر. "
                    "أضف تشغيلًا ثانيًا لكل نسخة.",
        "rateFirst": "هذه النسب تعتمد على التشغيل الأول لكل نسخة، وعلى أول تشغيلين لتقلب إعادة التشغيل.",
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
            "correct_both_changed": "Correct in both, answer changed",
            "correct_both_changed_unconfirmed": "Correct in both, answer changed, not re-run",
        },
        "wrongChanged": "{n} of them gave a different wrong answer after the update; they also appear "
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
            "correct_both_changed": "صحيحة في النسختين وتغيّرت الإجابة",
            "correct_both_changed_unconfirmed": "صحيحة في النسختين وتغيّرت الإجابة، بلا إعادة تشغيل",
        },
        "wrongChanged": "{n} منها أعطت إجابة خاطئة مختلفة بعد التحديث، وتظهر أيضًا ضمن حالات المراجعة.",
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
    },
}

NOKEY_MODE = {
    "en": {
        "passagesFocus": " Among the stable changes: {k} of {n}.",
        "modeNote": "No answer key: two answers count as the same when {rule}. "
                    "A different answer is a change. Whether it is better or worse is your call.",
        "simExact": "they match after lower-casing and removing punctuation",
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
        "modeNote": "بلا مفتاح إجابات: تُعدّ الإجابتان متطابقتين عندما {rule}. "
                    "الإجابة المختلفة تغيّر، والحكم بأنها أفضل أو أسوأ لك.",
        "simExact": "تتطابقان بعد توحيد حالة الأحرف وحذف علامات الترقيم",
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

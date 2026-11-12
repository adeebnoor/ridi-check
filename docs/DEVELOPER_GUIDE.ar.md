<div dir="rtl">

# دليل المطورين لـ ridi-check

للمطورين الذين يربطون مساعداً بالأداة، أو يضعونها في خط إطلاق، أو يعدّلونها. النسخة الإنجليزية:
[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md). المستخدمون يبدؤون من [دليل الاستخدام](USER_GUIDE.ar.md).

## التثبيت والاختبار

```bash
pip install -e ".[test]"
```

```bash
pytest
```

Python 3.10 أو أحدث. لا اعتماديات وقت التشغيل. الاختبارات لا تحتاج شبكة ولا مفتاح API.

## كيف تترابط الأجزاء

```
questions.csv ─┐
current  ──────┼─ run ──> raw_outputs.jsonl ──> results.csv ──┬─ report ──> summary.json
proposed ──────┘          run_manifest.json                   │             review_cases.csv
                                                              │             report.html
                                         (or made by hand) ───┴─ gate ────> exit status
```

| الوحدة | وظيفتها |
|---|---|
| `adapters.py` | تحويل تعريف النظام إلى `answer(question)`. أنواعها: python و command و http. |
| `runner.py` | أمر `run`: تخطيط الاستدعاءات، تسجيل كل محاولة، الاستئناف، كتابة `results.csv`. |
| `contract.py` | قراءة `results.csv` والتحقق منه. كل رفض يذكر رقم الصف. |
| `analysis.py` | حالات الأسئلة ونسب التشغيل الأول. المكان الوحيد للقواعد. |
| `scoring.py` | تطابق تام بعد التوحيد، أو دالة من المستخدم. لا محكّم آلي. |
| `report.py` و`strings.py` و`report_template.html` | ملفات التقرير الثلاثة. الصفحة لا تجري أي تحليل. |
| `gate.py` | مقارنة الأعداد بالحدود. |
| `cli.py` | المعاملات، و`ridi-check.json`، و`demo`، و`init`. |
| `web/` | نسخة المتصفح: `core.js` نقلٌ للتحليل و`app.js` للصفحة. يبني `python tools/build_web.py` الملف `web/ridi-update-check.html`، ويشغّل `tests/test_web.py` الملف `core.js` في Node مقابل بايثون على ملفات عشوائية. |

## ربط مساعد

الواجهة دالة واحدة:

```python
def answer(question: str) -> dict:
    return {"answer": "text", "context": ["doc-12", "doc-40"]}   # context may be None
```

إعادة نص مجرد مقبولة. أي شكل آخر يُسجَّل استدعاءً فاشلاً.

ويمكن أن يكون المقطع كائناً، ليقول التقرير أكثر من «أي المقاطع اختلفت»:

```python
    return {"answer": "text", "context": [
        {"id": "doc-12", "score": 0.91, "text": "the passage itself"},      # بترتيب الاسترجاع
        {"id": "doc-40", "score": 0.40, "text": "another passage"},
    ]}
```

الحقل `id` (أو `title` أو `name`) مطلوب، و`score` و`text` اختياريان، ويمكن إعطاء `hash` بدل `text`. النص
نفسه لا يُحفظ: يكتب `run` بصمة قصيرة له، فيُعرف المقطع الذي بقي اسمه وتغيّر محتواه. ومع محوّل http اجعل
`context_path` يشير إلى قائمة الكائنات (مثلاً `"context_path": "sources"`).

| التعريف | متى تستخدمه | ملاحظات |
|---|---|---|
| `python:module:function` | تستطيع استيراد المساعد | تُستدعى من عدة خيوط بعدد `--concurrency`. المجلد الحالي قابل للاستيراد. لا يمكن فرض مهلة على دالة Python. |
| `command:<shell command>` | المساعد برنامج بأي لغة | السؤال على stdin بترميز UTF-8. الخرج، بترميز UTF-8 كذلك، JSON فيه `answer` (و`context`) أو نص مجرد. الخروج بغير صفر استدعاء فاشل. تُضبط المتغيرات `RIDI_CHECK_CASE_ID` و`RIDI_CHECK_VERSION` و`RIDI_CHECK_RUN`. |
| `http://…` أو `https://…` | المساعد خدمة | يرسل POST فيه `{"question": …}` ويقرأ `answer` و`context` من رد JSON. |
| `path/to/system.json` | للطلب أو الرد شكل آخر | انظر أدناه. |

محوّلات جاهزة لواجهة HTTP متوافقة مع OpenAI ولواجهة Claude ولأمر shell موجودة في
[examples/adapters](../examples/adapters/README.md). تعريف JSON لنقطة محادثة على نمط OpenAI:

```json
{
  "type": "http",
  "url": "https://example.internal/v1/chat/completions",
  "headers": {"Authorization": "Bearer ${MY_API_KEY}"},
  "request": {"model": "my-model", "messages": [{"role": "user", "content": "{question}"}]},
  "answer_path": "choices.0.message.content",
  "context_path": "sources.*.title",
  "timeout": 60
}
```

يُستبدل `{question}` داخل أي نص في `request`. المسارات منقّطة؛ الرقم فهرس في قائمة و`*` تمرّ على
عناصرها. تُقرأ `${NAME}` من البيئة عند بدء التشغيل. يُنسخ التعريف إلى `run_manifest.json` كما هو،
فالمفتاح المكتوب حرفياً فيه يُنسخ أيضاً: تحذّرك الأداة إذا حمل ترويسةٌ تشبه بيانات الاعتماد قيمة
حرفية.

الدالة أو الأمر الذي يفشل يجب أن يرفع استثناءً أو يخرج برمز غير صفري: يُسجَّل الاستدعاء فاشلاً ويُعاد.
ومن دالة Python يمكنك إخبار المشغّل بأكثر من ذلك بخصائص على الاستثناء الذي ترفعه: `retry_after` (ثوانٍ
يُنتظر قبل المحاولة التالية، ولا يبدأ أي استدعاء آخر خلالها) و`retryable = False` (لا تُعِد هذا الاستدعاء)
و`service_failure = True` (الخدمة ترفض كل الاستدعاءات؛ عشرة منها متتالية توقف التشغيل). محوّل http يضبطها
من رمز الحالة وترويسة `Retry-After`؛ انظر [المرجع](REFERENCE.md#ridi-check-run).

يجب أن تختلف النسختان فقط في ما يغيّره التحديث. مثال لمحوّل Python:

```python
def ask(question, version):
    model = "model-2025" if version == "current" else "model-2026"
    reply = client.chat(model=model, system=PROMPT, user=question)
    return reply.text, [s.title for s in reply.sources]
```

## ملف الإعدادات

يقرأ `ridi-check run` الملف `ridi-check.json` من المجلد الحالي (أو `--config FILE`). المفاتيح هي
أسماء الخيارات الطويلة بشرطة سفلية: `questions` و`current` و`proposed` و`out` و`runs` و`limit`
و`concurrency` و`retries` و`retry_wait` و`timeout` و`scorer` و`current_label` و`proposed_label`
و`report` و`similarity` و`open`. خيارات سطر الأوامر تغلب. المسارات نسبية إلى مجلد الملف، والأداة
تنتقل إلى ذلك المجلد قبل التشغيل.

## التقييم

مع عمود `expected` في ملف الأسئلة تأخذ كل إجابة 0 أو 1. الافتراضي: التساوي بعد تحويل الأحرف إلى
صغيرة واستبدال علامات الترقيم بمسافات وضغط المسافات. وتبقى الرموز التي تحمل معنى مثل `<` و`>` و`+` و`%` (انظر [المرجع](REFERENCE.md#how-cases-are-labelled)). دالتك الخاصة:

```python
def scorer(answer: str, expected: str) -> bool:
    return expected.lower() in answer.lower()
```

مرّرها هكذا: `--scorer module:function`. التحكيم بنموذج لغوي خارج النطاق: المحكّم يضيف خطأه، فتقيس
الأداة عندها المحكّم مع المساعد.

## الملفات

**`raw_outputs.jsonl`**: سطر لكل محاولة، يُضاف ويُثبَّت فور اكتمالها، ولا يُعاد كتابته أبداً:

```json
{"case_id": "q07", "version": "proposed", "run": 2, "attempt": 1, "max_attempts": 3, "status": "ok",
 "answer": "…", "context": ["…"], "error": null, "started_at": "…", "ended_at": "…"}
```

قيمة `status` هي `ok` أو `failed`. يُعدّ الاستدعاء منجزاً إذا كان له سطر `ok` واحد. عند إعادة
التشغيل تُتخطى المنجزة ويُعاد الباقي. السطر المبتور بسبب إيقاف قسري يُترك مكانه ويُتجاهل.

**`run_manifest.json`**: بصمة SHA-256 لملف الأسئلة، والتعريفان كما أُعطيا (مع بصمة ملف التعريف أو
ملف مصدر Python)، وعدد التشغيلات، والتزامن، وإعادة المحاولات، ودالة التقييم، وإصدار الأداة، وقيد
لكل استدعاء للأمر بأوقاته وأعداده. يُرفض تشغيل ثانٍ في المجلد نفسه بملف أسئلة أو تعريف مختلف؛ أما
تغيّر مصدر Python فيُنبَّه عليه ولا يُرفض، لأن إصلاح محوّل معطوب ثم الاستئناف أمر معتاد.

**`results.csv`**: العقد موثّق في [المرجع](REFERENCE.md#resultscsv). يكتبه `run` فقط بعد اكتمال
الاستدعاءات. يمكنك كتابته بنفسك واستخدام `report` و`gate` وحدهما.

**`summary.json`**: `mode` و`cases` و`cases_compared` و`runs_per_version` و`states` (عدد كل حالة)
و`case_ids` و`first_run` (وفيه `change_between_versions` و`rerun_variation_current`
و`rerun_variation_proposed`، كلٌّ بصيغة `{count, n, rate, interval_95}`؛ وفي وضع مفتاح الإجابات أيضاً الدقتان
و`regressions` و`improvements` و`changes_visible_in_mean_accuracy`
و`changes_cancelled_in_mean_accuracy`) و`any_run_disagreement` و`judgments` أو
`wrong_both_answer_changed` و`correct_both_answer_changed` (معرّفات الحالات التي تساوت درجتها واختلفت
إجابتها، تحت `stable` و`unconfirmed` و`varied`) و`score_and_answer_text` (في وضع مفتاح الإجابات مع وجود نص
الإجابات: لكل حالة من حالات الدرجة، عدد حالاتها تحت كل وصف لنص الإجابة) و`same_text_scored_differently`
(معرّفات الحالات التي حمل فيها نص الإجابة نفسه درجتين) و`score_check` عند استخدام `--check-scores`
و`labelled_by_similarity` عند استخدام عتبة التشابه و`passages` إذا ذكر الملف مقاطع (`cases_with_passages` و`differ` و`by_state` وفيه
`{differ, n}` لكل حالة) و`notes`.

**`review_cases.csv`**: كل حالة ليست «الإجابة نفسها / صحيحة في النسختين»، بكل تشغيلاتها وبأسماء
أعمدة العقد، فيمكن إعادة قراءته بأمر `report`. ومع مفتاح الإجابات فيه أيضاً `answer_change`، وإذا حمل الملف نص
الإجابات ففيه `answer_state`: الوصف الذي يأخذه نص إجابة الحالة بلا مفتاح.

## القواعد بدقة

لكل حالة، وتشغيلات كل نسخة قائمة (`analysis.classify`):

1. إذا خالف أي تشغيل لنسخةٍ تشغيلَها الأول: `unstable`.
2. وإلا إذا تساوى التشغيلان الأولان للنسختين: `correct_both` أو `wrong_both` أو `same`.
3. وإلا `stable_regression` (من 1 إلى 0) أو `stable_improvement` (من 0 إلى 1) أو `stable_change`.
   وإن كان لإحدى النسختين تشغيل واحد فالوسم `*_unconfirmed`.

«التساوي» هو تساوي الصحة في وضع مفتاح الإجابات، وتساوي الإجابتين بعد التوحيد في غيره. ومع
`--similarity X` أقل من 1 تُعدّ الإجابتان متساويتين أيضاً إذا تداخلت كلماتهما بنسبة X على الأقل
(جاكارد) واحتوتا الأرقام نفسها واتفقتا في وجود أداة نفي أو غيابها.

النسب تعتمد على التشغيل الأول. التغيّر بين النسختين هو نسبة الحالات التي اختلف تشغيلاها الأولان؛
وفي وضع المفتاح يساوي التراجعات زائد التحسّنات، ويتحرك متوسط الدقة بالفرق بينهما، ويلغي
`2 × min(regressions, improvements)` من التغيّرات بعضه بعضاً في المتوسط. تقلب إعادة التشغيل هو
التشغيل 1 مقابل التشغيل 2 للنسخة نفسها، ويُعرض للنسختين. لا تطرح الأداة تقلب الإعادة من التغيّر
أبداً ولا تعطي اختباراً ولا فترة ثقة؛ الأعداد في `summary.json` إن أردت حسابها بنفسك.

إضافات على النموذج الأولي في المتصفح: الحالة `incomplete` (فشل استدعاء في التشغيل الأول؛ تُستبعد من
كل النسب)، و`any_run_disagreement`، وعلامة حالة `wrong_both` التي تغيّرت إجابتها.

## في خط CI

ملف workflow كامل جاهز للنسخ: [examples/ci/ridi-check.yml](../examples/ci/ridi-check.yml). الخطوات:

```yaml
- run: pip install ridi-check
- run: ridi-check run --config check/ridi-check.json --out "ridi-out-${{ github.sha }}"
  env:
    MY_API_KEY: ${{ secrets.MY_API_KEY }}
- run: ridi-check gate "check/ridi-out-${{ github.sha }}/results.csv" --max-stable-regressions 0
- uses: actions/upload-artifact@v4
  if: always()
  with: { name: ridi-report, path: check/ridi-out-* }
```

| رمز الخروج | `run` | `report` | `gate` |
|---|---|---|---|
| 0 | سُجّلت كل الاستدعاءات | كُتب التقرير | كل عدد ضمن حدّه |
| 1 | انتهى وبعض الاستدعاءات فشل | – | تجاوز حد |
| 2 | مدخلات غير صالحة، أو فشلت الاستدعاءات الأولى كلها | مدخلات غير صالحة | مدخلات غير صالحة |
| 130 | قوطع؛ أعد الأمر للاستئناف | – | – |

البوابة تطبع الأعداد والحالات المخالفة، ولا تطبع حكماً على النظام.

## كمكتبة

```python
from ridi_check.contract import read_results
from ridi_check.analysis import analyse
from ridi_check.report import build_summary, write_report

cases, mode = read_results("results.csv")          # mode is "key" or "nokey"
analysis = analyse(cases, mode, threshold=1.0)
print(analysis.counts, analysis.ids("stable_regression"))
summary = build_summary(analysis)
write_report("results.csv", "out")                  # the three report files
```

`ridi_check.runner.run(RunConfig(...))` ينفّذ الاستدعاءات، و`ridi_check.gate.evaluate(analysis)` يعيد
أسطر البوابة وهل تجاوز حد. قد تتغيّر الواجهة البرمجية قبل الإصدار 1.0.

## تعديل الأداة

- أي حالة أو نسبة جديدة مكانها `analysis.py` مع اختبار، وكذلك `web/core.js`؛ يفشل اختبار المطابقة حتى
  يتفقا. صفحة التقرير التي يكتبها `report` لا تحسب شيئاً.
- النص المعروض للناس مكانه `strings.py` بالإنجليزية والعربية، ويلتزم قواعد الصياغة: بلا مفتاح
  إجابات أو حكم، الاختلاف «تغيّر» لا «تراجع»؛ المقطع الذي بلا درجة صلة «ungraded»؛ لا شيء يقول أو
  يوحي بأن النظام آمن أو معتمد أو موافَق عليه؛ وحيث يُشرح «ثابت» يُذكر أن التشغيلين تقدير ضعيف.
  يتحقق `tests/test_report_gate.py` من ذلك.
- نوع محوّل جديد: دالة في `adapters.py` تعيد `answer(question, meta)`، مع فرع في `parse_definition`
  و`build_adapter`.
- الملفان `examples/toy_assistant.py` و`src/ridi_check/demo/toy_assistant.py` ملف واحد؛ يفشل اختبار
  إن اختلفا.

## كيف اختُبرت

يغطي `pytest`: عيّنة اصطناعية من أربعين حالة في الوضعين، وكل حالات رفض CSV، والاستئناف بعد الانقطاع،
والاستدعاءات الفاشلة المسجّلة، والمحوّلات الثلاثة (http على خادم محلي)، وصياغة التقرير والبوابة،
وأوامر الاستخدام الأول، وملفات عشوائية ببذرة ثابتة تُفحص على ثوابت (الحالات تقسّم الأسئلة؛ «ثابت»
يستلزم تشغيلين للنسختين؛ التغيّر = التراجعات + التحسّنات؛ `review_cases.csv` يُقرأ ثانية بالحالات
نفسها).

## حدود معروفة

- محوّل Python الذي يتعلّق لا يُقاطَع. ضع مهلة داخل دالتك.
- محوّلات `python:` تُستدعى من عدة خيوط. استخدم `--concurrency 1` إن لم تكن دالتك آمنة للخيوط.
- تُكتب الإجابات في CSV كما هي. قد يعامل برنامج الجداول الخلية التي تبدأ بـ`=` كصيغة؛ افتح النتائج
  غير الموثوقة كنص.
- يشغّل CI الاختبارات على Linux وmacOS وWindows مع Python 3.10 و3.13.
- الإيجنتات التي تستخدم أدوات أو تحتفظ بحالة، والاختبارات الإحصائية، والتحكيم بنموذج: خارج النطاق.

</div>

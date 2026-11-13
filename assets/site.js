/* RIDI landing: no analytics, cookies, third-party scripts, or uploaded data. */
(() => {
  "use strict";

  const ar = {
    skip:"تجاوز إلى المحتوى",
    navWhy:"لماذا RIDI؟",
    navHow:"كيف تعمل؟",
    navEvidence:"الأدلة الموثقة",
    navResearch:"البحث العلمي",
    navStart:"ابدأ الآن",
    launch:"افتح الأداة",
    eyebrow:"تدقيق تحديثات الذكاء الاصطناعي · مفتوح المصدر",
    heroLine1:"قد تبقى نتيجة",
    heroLine2:"التقييم كما هي.",
    heroLine3:"لكن القرار يتغير.",
    heroLead:"تحديث النموذج أو التعليمات أو الاسترجاع قد يُبقي الدرجة الإجمالية أو درجة الصلة كما تبدو، ومع ذلك يغيّر الإجابات التي يتلقاها شخص. RIDI Check تدقيق إصدار على مستوى البند: بنود متطابقة، تشغيلات متكررة، أرضية تنفيذ، واختبار شرطي دقيق إلى جانب المقارنة المُقرَّبة. بوابة الإصدار يمكنها إيقاف البناء. ليست شهادة.",
    heroCta:"بداية في 60 ثانية",
    heroSecondary:"متى لا تستخدمها",
    trustOpen:"مفتوحة المصدر",
    trustLocal:"تحليل محلي أولًا",
    trustEvidence:"سجلات قابلة للتحقق",
    monitorSigned:"تشغيل موقّع",
    monitorStudy:"QWEN2.5 · الأوزان نفسها · تحديث التعليمات",
    monitorBefore:"قبل التحديث",
    monitorAfter:"بعد التحديث",
    monitorNotEnough:"المتوسط وحده لا يُظهر الحالات",
    monitorTransitions:"بنود متطابقة",
    caseItem:"بند BoolQ متطابق",
    caseReg:"تراجع ثابت",
    flagReg:"تراجعات ثابتة",
    flagUnst:"حالات غير مستقرة",
    releaseBlocked:"بوابة الإصدار: إيقاف",
    visualCaption:"تشغيل GitHub الموقّع · تراجعات ثابتة مقابل التسميات المنشورة: p1506 وp1574 وp2179 وp2735 · غير مستقرة عند التكرار: p0358 وp0746 وp1686 · تسميات منشورة وليست تحكيماً مستقلاً",
    ribbonTitle:"تجربة قابلة لإعادة الإنتاج، لا ادعاء تسويقي",
    ribbonCases:"بندًا متطابقًا",
    ribbonCalls:"استدعاء فعليًا للنموذج",
    ribbonRepeats:"إعادات لكل نسخة",
    ribbonProof:"افحص الإثبات",
    doorKicker:"لماذا تُستخدم",
    doorTitle:"قد تثبت الدرجة وتتحرك الإجابات.",
    doorLead:"هذا هو الخطر. إن كنت تنشر تحديثاً أو تقيّمه أو تراجعه، فثبات المتوسط ليس دليلاً على أن الإجابات التي يتلقاها الناس بقيت كما هي.",
    whoPracTitle:"ممارس",
    whoPracBody:"أنت على وشك تغيير تعليمات أو نموذج أو المقاطع التي يسترجعها نظام. تحتاج الحالات التي تحركت، وبوابة يمكنها إيقاف البناء، قبل أن يرى المستخدمون الإجابات الجديدة.",
    whoEvalTitle:"مقيّم",
    whoEvalBody:"درجة المهمة تجيب عن سؤال آخر. تعرض RIDI Check انتقالات على مستوى البند لمعرّفات الحالات نفسها، إلى جانب عدد مرات مخالفة كل نسخة لنفسها.",
    whoRegTitle:"مراجع",
    whoRegBody:"تحتاج سجلاً يمكن إعادة قراءته: بنود متطابقة، وتشغيلات متكررة، وحداً معلناً. فشل البوابة تطبيق لتلك التسميات. ليس إذناً بالنشر.",
    contribKicker:"ما الذي تضيفه",
    contribTitle:"تدقيق على مستوى البند، لا درجة إجمالية أخرى.",
    contribBody:"HELM وlm-evaluation-harness وInspect مبنية لتهيئة التقييمات وتسجيلها وتسجيل مخرجاتها. وحدتها المعتادة درجة مهمة. لم تُشغَّل هذه الأدوات على البنود نفسها في هذا المستودع، ولا يُدَّعى أنها أدنى رتبة. ما يضيفه ridi-check تقرير بانتقالات على مستوى البند على بنود متطابقة، إلى جانب أرضية تنفيذ من تشغيلات متكررة، مع اختبار شرطي دقيق إلى جانب مقارنة النسب المُقرَّبة، وبوابة إصدار يمكنها إيقاف البناء. الاختبار الدقيق معلَّم: التنفيذ بانتظار التأكيد مقابل البروتوكول المسجّل. البوابة لا تعتمد النظام.",
    quickKicker:"بداية سريعة",
    quickTitle:"ثبّت، شغّل المثال بلا شبكة، واقرأ البوابة.",
    quickBody:"المثال دليل مكتبة خيالي ومساعد اصطناعي حتمي. يفحص الآلية. ليس دراسة على نموذج. الأسطر أدناه مخرج البوابة المسجّل لهذا المثال في المستودع.",
    sampleCaption:"مخرج نموذجي · مثال اصطناعي",
    quickNote:"السؤال q02 هو «كم مرة يجب تجديد العضوية؟» الدليل مبني. أربع تراجعات ثابتة تكفي لتخرج البوابة الصارمة بالحالة 1. هذا فحص للبرنامج لا لمكتبة.",
    workedKicker:"نتيجة حقيقية، ومعها النتيجة الفارغة",
    workedTitle:"التكرار التجاري المسجّل لم يحقق معياره.",
    workedBody:"RIDI-CONFIRM-C، المعرّف 10.17605/OSF.IO/ANBJD. المعيار H1c هو الدعم في نموذجين على الأقل من ثلاثة بعد Holm. لم يتحقق. الأرقام أدناه نتيجة مُبلَّغة على مقياس النسبة ولم تُعد هنا. الفروق نفسها كُتبت هنا من قبل كنقاط مئوية: +3.47 نقطة هي +0.0347. لم يُعثر على عدد تداخل البنود المتغيّرة في الملفات العامة التي أمكن قراءتها من هنا، لذلك لا يُعرض.",
    workedCaption:"فروقات H1c المُبلَّغة. لم تُعد هنا.",
    workedModel:"النموذج",
    workedEstimate:"الفرق المُبلَّغ",
    workedInterval:"الفترة",
    workedCall:"قراءة التسجيل المسبق",
    workedYes:"مدعوم",
    workedNo:"غير مدعوم",
    workedSource:"المصدر: نتيجة التكرار التجاري المُبلَّغة في هذا الموقع، التسجيل",
    workedMore:"الجدول نفسه بصياغة صفحة العلم",
    audienceKicker:"لمن هذا",
    audienceTitle:"استخدمه حين تكون وحدة الضرر إجابة واحدة.",
    audienceBody:"استخدمه لمقارنة نسختين من نظام واحد على معرّفات الحالات نفسها. لا تستخدمه لترتيب النماذج في لوحة عامة، ولا لاعتماد نظام سريري، ولا للحكم بأن إجابة صحيحة حين لا يوجد مفتاح. من دون مفتاح، الاختلاف تغيير لا تراجع.",
    faqKicker:"أسئلة",
    faqTitle:"إجابات قصيرة، والحدود باقية فيها.",
    faq1q:"هل يحكم نموذج على الإجابات؟",
    faq1a:"لا. التقييم مطابقة تامة بعد التوحيد، أو دالة توفّرها أنت. الحكم بنموذج يضيف خطأه.",
    faq2q:"هل الاختبار الدقيق هو إعادة المعاينة المسجّلة؟",
    faq2a:"لا. التحليل المسجّل إعادة معاينة مزدوجة بهامش نقطتين. تُخرج الحزمة اختباراً شرطياً ذا حدّين وتعلّمه بانتظار التأكيد. مقارنة النسب المُقرَّبة لم تتغيّر.",
    faq3q:"ماذا إن لم يوجد مفتاح إجابات؟",
    faq3a:"يسرد التقرير تغييرات لا تراجعات. أنت تحكم أي التغييرات أسوأ. يمكن للبوابة أن تعدّ تلك الأحكام. وهي لا تعتمد النظام.",
    notKicker:"متى لا تُستخدم",
    notTitle:"فشل البوابة ليس اعتماداً، ونجاحها ليس كذلك.",
    notBody:"لا تستخدم ridi-check اعتماداً سريرياً، ولا ترتيباً مقابل HELM أو Inspect أو lm-evaluation-harness، ولا دليلاً على أن إجابة ثابتة إجابة صحيحة. تشغيلان أرضية تنفيذ رقيقة. صفحة الحدود هي القائمة، لا حاشية.",
    notLink:"اقرأ الحدود",
    whyKicker:"المشكلة",
    whyTitle:"الدرجة الواحدة لا تروي القصة الكاملة لتحديث النظام.",
    whyBody:"قد تبدو نسختان متقاربتين في التقرير الإجمالي، لكنهما تقدّمان إجابات مختلفة لأسئلة ذات أثر مهم. ومن دون حالات متطابقة وإعادات تشغيل وأدلة موثّقة، يسهل أن نفوّت هذه التغيّرات.",
    p1Title:"انظر لما وراء المتوسط.",
    p1Body:"اعرف أي الإجابات تغيّرت فعليًا، حتى عندما تبدو نتيجة التقييم الإجمالية مقبولة.",
    p2Title:"افصل التغيير عن أرضية التنفيذ.",
    p2Body:"كرّر النسختين على البنود المتطابقة. أرضية التنفيذ هي ضجيج إعادة التنفيذ. التغيير الذي لا يتجاوزها ليس دليلاً على أثر التحديث.",
    p3Title:"اجعل النتائج قابلة للتدقيق.",
    p3Body:"اربط النتائج بالمدخلات المجمّدة والسجلات والبصمات وبوابة نشر يمكنها رفض التحديث.",
    howKicker:"المنهجية",
    howTitle:"من تحديث النظام إلى سجل قرارات يمكن مراجعته.",
    howBody:"لا ترتبط RIDI بمزوّد نموذج محدد. استخدم إجابات مرجعية إن توفرت، أو قارن نصوص الإجابات وراجع التغيرات بنفسك.",
    step1Title:"ثبّت الأسئلة والمدخلات",
    step1Body:"قارن النسخة الحالية والمقترحة على الأسئلة نفسها، مع إرفاق النصوص المسترجعة إن توفرت.",
    step2Title:"كرّر تشغيل النسختين",
    step2Body:"التشغيلات المتكررة تقدّر أرضية التنفيذ: كم مرة تخالف النسخة نفسها.",
    step3Title:"راجع تغيّرات كل حالة",
    step3Body:"حدّد التراجعات والتحسينات والتغيّرات الثابتة والحالات التي تتذبذب فيها الإجابات.",
    step4Title:"طبّق بوابة إصدار",
    step4Body:"بوابة الإصدار تطبيق. يمكنها إيقاف البناء عندما تتجاوز التراجعات الثابتة حداً تضعه أنت. وهي لا تعتمد النظام.",
    evidenceKicker:"أدلة قابلة للتحقق",
    evidenceTitle:"أدلة تستطيع فحصها، لا أرقامًا يُطلب منك تصديقها.",
    evidenceBody:"هذه تجارب هندسية محددة النطاق، ولها ملفات تشغيل قابلة لإعادة الإنتاج وتوقيعات GitHub/Sigstore. ليست اعتمادًا سريريًا مستقلًا ولا إثباتًا للتفوّق على أطر التقييم الأخرى.",
    signedEvidence:"أدلة موقّعة",
    syntheticControl:"اختبار اصطناعي",
    study1Type:"تحديث مضبوط لإعدادات النظام",
    study1Title:"الأوزان نفسها. تعليمات مختلفة. إجابات مختلفة.",
    study1Body:"Qwen2.5-1.5B على 48 حالة منتقاة من BoolQ، بثلاث إعادات لكل نسخة. رصد تشغيل Linux الموقّع أربع تراجعات ثابتة مقابل التسميات المنشورة وثلاث حالات غير مستقرة. ظهر اختلاف محدود عن Windows وجرى الإفصاح عنه.",
    studyCalls:"استدعاء للنموذج",
    study1Reg:"تراجعات مقابل التسميات",
    study1Var:"حالات غير مستقرة",
    seeSignedRun:"افحص التشغيل الموقّع",
    readStudy:"اقرأ التدقيق العلمي",
    study2Type:"استبدال نموذج حقيقي",
    study2Title:"قد يتحسن المتوسط مع تراجع بعض الإجابات.",
    study2Body:"مقارنة حجمين من Qwen2.5 على 48 حالة BoolQ بتسميات بشرية منشورة. أظهر التشغيل المستقل ست تراجعات ثابتة مقابل التسميات و16 تحسينًا. ما زال تحكيم التسميات مطلوبًا.",
    study2Reg:"تراجعات مقابل التسميات",
    study2Gain:"تحسينات مقابل التسميات",
    study3Type:"اختبار متكامل لبوابة النشر",
    study3Title:"التحديث غير الآمن عمدًا يجب ألا يجتاز البوابة.",
    study3Body:"دليل مكتبة خيالي ومساعد اصطناعي حتمي لاختبار مسار التشغيل. أربع حالات تراجع ثابتة ترفضها البوابة الصارمة. هذا فحص للآلية، لا لجودة نموذج.",
    study3Cases:"حالة اصطناعية",
    study3Reg:"تراجعات اصطناعية",
    study3Gate:"منع للتمرير",
    readProtocol:"بروتوكول الأدلة",
    evidenceFootnote:"في BoolQ، تشير «التراجعات» إلى الاختلاف عن مفتاح الإجابات المنشور، لا بالضرورة إلى قرار خاطئ في العالم الحقيقي. توجد تسميات تتعارض مع النصوص أو تتغير مع الزمن. راجع التدقيق العلمي.",
    researchKicker:"العلم",
    researchTitle:"مصممة للتدقيق لا للثقة العمياء.",
    researchBody:"تقارن RIDI البنود المتطابقة عبر تشغيلات متكررة وتعرض التغيير إلى جانب أرضية التنفيذ. يعرض البرنامج تلك المقارنة المُقرَّبة، وإلى جانبها اختباراً شرطياً دقيقاً معلَّماً: التنفيذ بانتظار التأكيد مقابل البروتوكول المسجّل. ولا شيء هنا اعتماد سريري.",
    priorArtLink:"الأعمال السابقة وحدود التسميات",
    benchmarkLink:"معيار التغيّرات الاصطناعي",
    referenceLink:"المرجع التقني",
    researchNot:"ما الذي لا ندّعيه؟",
    limit1Title:"ليست اعتمادًا سريريًا",
    limit1Body:"لم تكتمل بعد تجربة تحقق سريري مستقلة من السلامة.",
    limit2Title:"ليست تحكيمًا بشريًا مستقلًا",
    limit2Body:"التسميات المنشورة والحالات الاصطناعية ليست بديلًا عن تقييم الخبراء الأعمى.",
    limit3Title:"لم يثبت تفوقها على HELM أو Ragas أو Inspect AI",
    limit3Body:"لم تُجرَ بعد مقارنات مباشرة متكافئة في المهام والبيانات.",
    researchFooter:"تأتي المصداقية من إظهار النتائج وحدودها معًا.",
    startKicker:"ابدأ خلال دقائق",
    startTitle:"ابدأ بالسؤال. اختبر التحديث.",
    startBody:"استخدم أداة المتصفح التفاعلية مع أمثلة جاهزة، أو اربط RIDI بمساعدك وشغّلها محليًا أو في CI. يحلل المتصفح ملفات CSV على جهازك.",
    startBrowserTitle:"دون تثبيت. افتح التجربة.",
    startBrowserBody:"استكشف مثال المكتبة ذا الثلاثين حالة، أو المجموعة الموسومة بأسماء أدوية مخترعة للتوضيح فقط، أو ارفع نتائجك محليًا.",
    startBrowserCta:"افتح أداة المتصفح",
    privacyNote:"تحليل الملفات داخل متصفحك، دون رفعها إلى خادم RIDI.",
    startDevTitle:"جاهزة للعمل المحلي وCI.",
    startDevBody:"ثبّت حزمة Python وشغّل المثال الاصطناعي، ثم اربط مساعدك بدالة Python أو أمر أو اتصال HTTP.",
    copyLabel:"نسخ",
    copyAria:"نسخ أوامر التثبيت",
    copied:"تم النسخ",
    copyFailed:"تعذّر النسخ",
    githubLink:"الشيفرة على GitHub",
    guideLink:"دليل الاستخدام",
    closingKicker:"القرارات تستحق أدلة",
    closingTitle:"قبل نشر التحديث، اكتشف ما الذي غيّره.",
    closingBody:"أظهر اختلاف القرارات، واحتفظ بالأدلة، واترك الحكم النهائي للمسؤولين عنه.",
    closingCta:"افتح RIDI Check",
    closingSource:"استكشف المشروع المفتوح",
    footerTag:"برمجية بحثية مفتوحة المصدر · الدليل قبل الادعاء",
    footerContact:"ملاحظات واقتراحات ↗",
    navHome:"الرئيسية",
    navChangelog:"سجل التغييرات 0.10.1",
    howToCite:"كيفية الاستشهاد",
    privacyFoot:"لا متتبعات. هذه الصفحات ثابتة. لا يُرسل ما تفعله هنا إلى خادم نديره.",
    missingTitle:"الصفحة غير موجودة",
    missingBody:"هذا العنوان ليس صفحة في موقع RIDI Check. الصفحة الرئيسية وصفحة العلم وأداة المتصفح مذكورة أدناه.",
    navScience:"العلم",
    navLimits:"الحدود",
    navRepro:"إعادة الإنتاج",
    examplesKicker:"أمثلة موسومة",
    examplesTitle:"أمثلة واضحة التسمية، لا ادّعاءات.",
    examplesBody:"النصوص أدناه من ملفات هذا المستودع. المثال الطبي أسماء وآثار مخترعة للتوضيح فقط.",
    ex1Kicker:"اصطناعي · داخل المستودع",
    ex1Title:"دليل المكتبة، البند q02",
    ex1Body:"السؤال: «كم مرة يجب تجديد العضوية؟» يدرجه التشغيل التجريبي ضمن التراجعات الثابتة. الدليل والإجابات مبنية للتوضيح، وليست دراسة على نموذج.",
    ex2Kicker:"مخترع · للتوضيح فقط",
    ex2Title:"تفاعل دوائي مخترع، البند m01",
    ex2Body:"السؤال يستخدم الاسمين المخترعين Zorvalin وMerdapine. الجرعات والآثار مخترعة وليست إرشاداً طبياً. الأداة تعلّم هذه المجموعة بأنها للتوضيح فقط.",
    manuscriptLine:"مخطوطة قيد المراجعة. النسخة الأولية ستصدر لاحقاً. العنوان: Identical relevance grades cannot certify retrieval-augmented AI answers.",
    replicationLine:"تكرار تجاري مسجّل مسبقاً: المعيار H1c، أي الدعم في نموذجين على الأقل من ثلاثة بعد تصحيح Holm، لم يتحقق. Gemini 3.8 Flash +0.0347 [0.0247, 0.0452] مدعوم. GPT-5.4 mini +0.0098 [-0.0024, 0.0221] وClaude Sonnet 5.5 +0.0074 [-0.0023, 0.0174] غير مدعومين. الفروق نفسها كُتبت هنا من قبل كنقاط مئوية: +3.47 نقطة هي +0.0347. المقدار يعتمد على النموذج ويجب قياسه لكل نموذج.",
    affiliation:"كلية الحاسبات وتقنية المعلومات، جامعة الملك عبدالعزيز",
    flowTitle:"مسار المنهج",
    flowDesc:"ست خطوات: نسختان، بنود متطابقة، تشغيلات متكررة، أرضية التنفيذ، الاختبار الشرطي الدقيق، ثم قرار الإصدار على مستوى البند.",
    flowCap:"من نسختين إلى قرار إصدار على مستوى البند: بنود متطابقة، تشغيلات متكررة، أرضية التنفيذ، ثم الاختبار الشرطي الدقيق.",
    flatTitle:"الدرجة تثبت والإجابات تتغير",
    flatDesc:"رسم توضيحي بلا أعداد. عمودان بالارتفاع نفسه لدرجة إجمالية، وتحتها بنود يتغير لون بعضها.",
    gridTitle:"الخلايا المختلفة b و c",
    gridDesc:"جدول اثنان في اثنين. b تغيّر بين النسختين مع اتفاق إعادة التشغيل. c اتفاق بين النسختين مع خلاف إعادة التشغيل. الخلايا التي تتفق علامتاها لا تدخل العد.",
    chartTitle:"فروق H1c المُبلَّغة",
    chartDesc:"Gemini 3.8 Flash +0.0347 والفترة من 0.0247 إلى 0.0452 فوق الصفر ومدعوم. GPT-5.4 mini +0.0098 والفترة من -0.0024 إلى 0.0221 تقطع الصفر وغير مدعوم. Claude Sonnet 5.5 +0.0074 والفترة من -0.0023 إلى 0.0174 تقطع الصفر وغير مدعوم. المصدر 10.17605/OSF.IO/ANBJD.",
    reproTitle:"مسار إعادة الإنتاج",
    reproDesc:"سجل مجمّد، ثم أمر وبذرة مثبّتان، ثم تشغيل موقّع، ثم بصمة تُعاد حسابها. التكرار التجاري ليس على هذا المسار.",
    flatCap:"رسم توضيحي. ليس نتيجة مقاسة، والعلامات ليست أعداداً من دراسة.",
    gridCap:"b تغيّر بين النسختين دون خلاف إعادة التشغيل. c خلاف إعادة التشغيل دون تغيّر بين النسختين. الاختبار يعدّ الخلايا المختلفة فقط.",
    chartCap:"فروق H1c المُبلَّغة مع فتراتها. الخط العمودي هو الصفر. المصدر 10.17605/OSF.IO/ANBJD. لم تُعد الحسابات هنا.",
    reproCap:"مسار التشغيلات الموجودة في هذا المستودع. التكرار التجاري ليس على هذا المسار.",
    sciencePage:"اقرأ صفحة العلم",
    repCaption:"التكرار التجاري المسجّل. الأرقام كما أُبلغت، ولم تُعد حساباتها في هذا المستودع.",
    repModel:"النموذج",
    repEstimate:"الفرق المُبلَّغ",
    repInterval:"الفترة",
    repCall:"قراءة التسجيل المسبق",
    repYes:"مدعوم",
    repNo:"غير مدعوم",
    cmpCaption:"ماذا يقدّم كل أداة. هذا ليس ترتيباً ولا ادّعاء بأن RIDI أفضل.",
    cmpTool:"الأداة",
    cmpWhat:"ما هي",
    cmpUnit:"وحدة التقرير المعتادة",
    cmpRepeat:"التشغيلات المتكررة",
    cmpFloor:"انتقالات البنود مقابل أرضية إعادة التنفيذ"
  };

  const original = new Map();
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    original.set(node, node.textContent);
  });
  const originalAria = new Map();
  document.querySelectorAll("[data-i18n-aria]").forEach((node) => {
    originalAria.set(node, node.getAttribute("aria-label") || "");
  });

  const langButton = document.getElementById("langSwitch");
  const nav = document.getElementById("primaryNav");
  const menuToggle = document.getElementById("menuToggle");
  let language = "en";

  function saveLanguage(lang) {
    try { window.localStorage.setItem("ridi-site-language", lang); } catch (_err) { /* private browsing */ }
  }

  function setLanguage(lang, save = true) {
    language = lang === "ar" ? "ar" : "en";
    const inArabic = language === "ar";
    document.documentElement.lang = language;
    document.documentElement.dir = inArabic ? "rtl" : "ltr";
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      const key = node.getAttribute("data-i18n");
      node.textContent = inArabic ? (ar[key] || original.get(node)) : original.get(node);
    });
    document.querySelectorAll("[data-i18n-aria]").forEach((node) => {
      const key = node.getAttribute("data-i18n-aria");
      node.setAttribute("aria-label", inArabic ? (ar[key] || originalAria.get(node)) : originalAria.get(node));
    });
    langButton.textContent = inArabic ? "English" : "العربية";
    langButton.setAttribute("lang", inArabic ? "en" : "ar");
    langButton.setAttribute("aria-label", inArabic ? "Switch to English" : "التبديل إلى العربية");
    menuToggle.setAttribute("aria-label", inArabic ? "فتح القائمة" : "Open navigation");
    nav.setAttribute("aria-label", inArabic ? "روابط التنقل الرئيسية" : "Main navigation");
    const root = document.documentElement;
    const titleEn = root.getAttribute("data-title-en");
    const titleAr = root.getAttribute("data-title-ar");
    document.title = titleEn
      ? (inArabic ? (titleAr || titleEn) : titleEn)
      : (inArabic
        ? "RIDI Check — القرارات تستحق أكثر من درجة"
        : "RIDI Check — Decisions deserve more than a score");
    const description = document.querySelector('meta[name="description"]');
    const descEn = root.getAttribute("data-description-en");
    const descAr = root.getAttribute("data-description-ar");
    if (description) {
      if (descEn) description.setAttribute("content", inArabic ? (descAr || descEn) : descEn);
      else description.setAttribute("content", inArabic
        ? "RIDI Check تكشف اختلاف الإجابات الفردية بعد تحديث الذكاء الاصطناعي، وتوثّق الأدلة وتكرار التشغيل والتوقيع الرقمي."
        : "RIDI Check examines how AI system updates change individual answers, not just aggregate scores. Repeat runs, inspect transitions, and verify signed evaluation evidence. Open source.");
    }
    document.querySelectorAll("[data-lang-block]").forEach((node) => {
      node.hidden = node.getAttribute("data-lang-block") !== language;
    });
    if (save) saveLanguage(language);
  }

  langButton.addEventListener("click", () => setLanguage(language === "en" ? "ar" : "en"));

  function closeMenu() {
    nav.classList.remove("open");
    menuToggle.setAttribute("aria-expanded", "false");
  }
  menuToggle.addEventListener("click", () => {
    const next = !nav.classList.contains("open");
    nav.classList.toggle("open", next);
    menuToggle.setAttribute("aria-expanded", String(next));
  });
  nav.querySelectorAll('a[href^="#"]').forEach((link) => link.addEventListener("click", closeMenu));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMenu();
  });
  document.addEventListener("click", (event) => {
    if (!nav.contains(event.target) && !menuToggle.contains(event.target)) closeMenu();
  });

  document.querySelectorAll("[data-copy]").forEach((copyButton) => copyButton.addEventListener("click", async () => {
    const value = copyButton.getAttribute("data-copy") || "pip install ridi-check\nridi-check demo --open";
    let succeeded = false;
    try {
      await navigator.clipboard.writeText(value);
      succeeded = true;
    } catch (_err) {
      // Older browsers may deny the clipboard API even in an HTTPS context.
      const textarea = document.createElement("textarea");
      textarea.value = value;
      textarea.setAttribute("readonly", "");
      textarea.style.cssText = "position:fixed;left:-9999px;top:-9999px";
      document.body.appendChild(textarea);
      textarea.select();
      try { succeeded = document.execCommand("copy"); } catch (_copyError) {}
      textarea.remove();
    }
    const text = copyButton.querySelector("[data-i18n]");
    if (text) {
      text.textContent = succeeded
        ? (language === "ar" ? ar.copied : "Copied")
        : (language === "ar" ? ar.copyFailed : "Copy failed");
      window.setTimeout(() => {
        if (text.isConnected) text.textContent = language === "ar" ? ar.copyLabel : original.get(text);
      }, 2200);
    }
  }));

  const year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());

  let preferred = "en";
  try {
    const stored = window.localStorage.getItem("ridi-site-language");
    if (stored === "ar" || stored === "en") preferred = stored;
    else if ((navigator.language || "").toLowerCase().startsWith("ar")) preferred = "ar";
  } catch (_err) { /* no persistent storage required */ }
  setLanguage(preferred, false);
})();

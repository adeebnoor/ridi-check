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
    heroLead:"تغيير النموذج أو التعليمات أو طريقة الاسترجاع قد يغيّر إجابات فردية بينما تُخفي المتوسطات ما حدث. تفحص RIDI الإجابات المتغيرة، وثباتها عبر الإعادات، والأدلة التي تستند إليها.",
    heroCta:"جرّب الأداة مباشرة",
    heroSecondary:"افحص الأدلة الموقّعة",
    trustOpen:"مفتوحة المصدر",
    trustLocal:"تحليل محلي أولًا",
    trustEvidence:"سجلات قابلة للتحقق",
    monitorSigned:"تشغيل موقّع",
    monitorStudy:"QWEN2.5 · الأوزان نفسها · تحديث التعليمات",
    monitorBefore:"قبل التحديث",
    monitorAfter:"بعد التحديث",
    monitorNotEnough:"المتوسط وحده لا يُظهر الحالات",
    monitorTransitions:"تغيّرات الإجابات الفردية",
    case1:"هل فوجي أعلى جبل في العالم؟",
    case2:"أول دولة استخدمت منصب الرئيس؟",
    case3:"سن الشرب الأدنى في جميع الولايات؟",
    case4:"جائزة مسابقة تلفزيونية؟",
    case4state:"متذبذبة",
    flagReg:"تراجعات ثابتة",
    flagUnst:"حالات غير مستقرة",
    releaseBlocked:"منع تمرير التحديث",
    visualCaption:"نتائج تشغيل CPU حقيقية على GitHub · 48 سؤالًا منتقى من BoolQ · تسميات منشورة لم تُحكّم مستقلًا",
    ribbonTitle:"تجربة قابلة لإعادة الإنتاج، لا ادعاء تسويقي",
    ribbonCases:"سؤالًا متطابق المدخلات",
    ribbonCalls:"استدعاء فعليًا للنموذج",
    ribbonRepeats:"إعادات لكل نسخة",
    ribbonProof:"افحص الإثبات",
    whyKicker:"المشكلة",
    whyTitle:"الدرجة الواحدة لا تروي القصة الكاملة لتحديث النظام.",
    whyBody:"قد تبدو نسختان متقاربتين في التقرير الإجمالي، لكنهما تقدّمان إجابات مختلفة لأسئلة ذات أثر مهم. ومن دون حالات متطابقة وإعادات تشغيل وأدلة موثّقة، يسهل أن نفوّت هذه التغيّرات.",
    p1Title:"انظر لما وراء المتوسط.",
    p1Body:"اعرف أي الإجابات تغيّرت فعليًا، حتى عندما تبدو نتيجة التقييم الإجمالية مقبولة.",
    p2Title:"ميّز التغيير من التذبذب.",
    p2Body:"أعِد تشغيل النسختين، لتمييز التغيّر المتكرر عن الإجابة التي تتبدّل بين التشغيلات.",
    p3Title:"اجعل النتائج قابلة للتدقيق.",
    p3Body:"اربط النتائج بالمدخلات المجمّدة والسجلات والبصمات وبوابة نشر يمكنها رفض التحديث.",
    howKicker:"المنهجية",
    howTitle:"من تحديث النظام إلى سجل قرارات يمكن مراجعته.",
    howBody:"لا ترتبط RIDI بمزوّد نموذج محدد. استخدم إجابات مرجعية إن توفرت، أو قارن نصوص الإجابات وراجع التغيرات بنفسك.",
    step1Title:"ثبّت الأسئلة والمدخلات",
    step1Body:"قارن النسخة الحالية والمقترحة على الأسئلة نفسها، مع إرفاق النصوص المسترجعة إن توفرت.",
    step2Title:"كرّر تشغيل النسختين",
    step2Body:"سجّل الإجابات المتكررة لكشف اختلاف التشغيلات بدل افتراض أن النموذج حتمي.",
    step3Title:"راجع تغيّرات كل حالة",
    step3Body:"حدّد التراجعات والتحسينات والتغيّرات الثابتة والحالات التي تتذبذب فيها الإجابات.",
    step4Title:"تحقّق قبل النشر",
    step4Body:"راجع الدرجات المسجّلة وأدلة التشغيل، وفعّل حدودًا صارمة في خط التكامل المستمر عند الحاجة.",
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
    researchKicker:"بحث منضبط",
    researchTitle:"مصممة للتدقيق لا للثقة العمياء.",
    researchBody:"تجعل RIDI التغيّرات المرصودة أوضح للمراجعة. لكنها لا تحدّد وحدها سلامة قرار طبي أو قانوني أو عالي الخطورة، ولا تحل محل المراجعة البشرية أو تثبت ضررًا سببيًا.",
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
    startBrowserBody:"استكشف مثال الثلاثين حالة، أو أمثلة بأسماء أدوية خيالية للتوضيح، أو ارفع نتائجك محليًا.",
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
    footerContact:"ملاحظات واقتراحات ↗"
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
  const copyButton = document.getElementById("copyInstall");
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
    document.title = inArabic
      ? "RIDI Check — القرارات تستحق أكثر من درجة"
      : "RIDI Check — Decisions deserve more than a score";
    const description = document.querySelector('meta[name="description"]');
    if (description) description.setAttribute("content", inArabic
      ? "RIDI Check تكشف اختلاف الإجابات الفردية بعد تحديث الذكاء الاصطناعي، وتوثّق الأدلة وتكرار التشغيل والتوقيع الرقمي."
      : "RIDI Check examines how AI system updates change individual answers, not just aggregate scores. Repeat runs, inspect transitions, and verify signed evaluation evidence. Open source.");
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

  if (copyButton) copyButton.addEventListener("click", async () => {
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
  });

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

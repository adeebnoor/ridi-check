"""Builds transitions.csv: constructed pairs of answers, each labelled by construction.

  gold = different   the second answer says something else than the first
  gold = same        the second answer says the same thing in another surface form

Every pair is made by putting a small fragment into a sentence frame, so the label follows from the
fragment and not from anyone's reading of the pair. Nothing here comes from a real assistant, a real
dataset or a study, and the medicine names are invented. The rates measured on this set say how the
comparison rules behave on each kind of change. They are not how often such changes happen in use.

    python benchmarks/transitions/generate.py     # rewrites transitions.csv, always the same file
"""

from __future__ import annotations

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))

SHORT_EN = ["{x}.", "The answer is: {x}.", "In short, {x}.", "For this patient {x}.", "As asked: {x}."]
LONG_EN = [
    "After reading the whole record and the notes from the last three visits, the team agreed that {x}, and the plan was written down for the next shift.",
    "The handbook for this ward, in the section that covers adults who are seen every month, says that {x}, and nothing else in that section changes it.",
    "According to the summary that was sent to the family doctor at the end of the stay, {x}, and the same line appears in the letter given to the patient.",
    "When the question was put to the assistant a second time with the full history attached, it said that {x}, and it gave the same two sources as before.",
    "The note left by the night shift for whoever takes over in the morning is short and says only that {x}, with the time and the initials of the writer.",
    "In the table at the end of the leaflet, under the heading for people who take other medicines as well, the entry reads that {x}, in bold type.",
]
SHORT_AR = ["{x}.", "الجواب: {x}.", "باختصار، {x}.", "لهذا المريض {x}."]
LONG_AR = [
    "بعد قراءة الملف كاملاً وملاحظات الزيارات الثلاث الأخيرة اتفق الفريق على أن {x}، وكُتبت الخطة للمناوبة التالية.",
    "يقول دليل هذا القسم في الباب الخاص بالبالغين الذين يُراجَعون كل شهر إن {x}، ولا يغيّر ذلك شيء آخر في الباب.",
    "في الملخص الذي أُرسل إلى طبيب الأسرة عند نهاية الإقامة ورد أن {x}، والسطر نفسه موجود في الرسالة التي أُعطيت للمريض.",
]

# category -> (gold, English fragment pairs, Arabic fragment pairs)
CATEGORIES: dict[str, tuple[str, list[tuple[str, str]], list[tuple[str, str]]]] = {
    "comparison sign": ("different", [
        ("the dose must be < 5 mg", "the dose must be > 5 mg"), ("the level should stay <= 40", "the level should stay >= 40"),
        ("the level should stay ≤ 40", "the level should stay ≥ 40"), ("the two readings are = in size", "the two readings are ≠ in size"),
        ("flag A == flag B", "flag A != flag B"), ("the count is > 200", "the count is < 200"),
    ], [("الجرعة يجب أن تكون < 5 ملغ", "الجرعة يجب أن تكون > 5 ملغ"), ("المستوى يبقى ≤ 40", "المستوى يبقى ≥ 40")]),
    "plus or minus sign": ("different", [
        ("the adjustment is +5", "the adjustment is -5"), ("the result is Rh+", "the result is Rh-"),
        ("the marker is HV17+", "the marker is HV17-"), ("the change was +0.5 points", "the change was -0.5 points"),
        ("the balance is +120", "the balance is −120"),
    ], [("التعديل هو +5", "التعديل هو -5"), ("النتيجة Rh+", "النتيجة Rh-")]),
    "percent, per, times": ("different", [
        ("the risk is 10%", "the risk is 10"), ("give 5 mg/kg", "give 5 mg*kg"), ("give 5 mg/kg", "give 5 mg kg"),
        ("the rate is 3/4", "the rate is 3*4"), ("it rose by 2%", "it rose by 2"),
    ], [("الخطر 10%", "الخطر 10"), ("أعطِ 5 ملغ/كغ", "أعطِ 5 ملغ*كغ")]),
    "other symbol": ("different", [
        ("the check is marked ✓", "the check is marked ✗"), ("the fee is $5", "the fee is €5"), ("keep it at 5 °C", "keep it at 5 °F"),
        ("the trend is ↑", "the trend is ↓"), ("the fee is £20", "the fee is 20"),
    ], [("العلامة ✓", "العلامة ✗"), ("الرسم $5", "الرسم €5")]),
    "number": ("different", [
        ("the dose is 5 mg", "the dose is 50 mg"), ("return within 30 days", "return within 45 days"), ("take 2 tablets of 5 mg", "take 5 tablets of 2 mg"),
        ("the dose is 2.5 mg", "the dose is 25 mg"), ("wait 6 hours", "wait 8 hours"), ("the limit is 1000 units", "the limit is 100 units"),
    ], [("الجرعة ٥ ملغ", "الجرعة ٥٠ ملغ"), ("يُعاد خلال 30 يوماً", "يُعاد خلال 45 يوماً")]),
    "unit": ("different", [
        ("the dose is 5 mg", "the dose is 5 g"), ("return within 30 days", "return within 30 weeks"), ("the dose is 5mg", "the dose is 5g"),
        ("give it every 6 hours", "give it every 6 days"), ("the bag holds 500 ml", "the bag holds 500 l"),
    ], [("الجرعة 5 ملغ", "الجرعة 5 غرام"), ("كل 6 ساعات", "كل 6 أيام")]),
    "negation": ("different", [
        ("the two medicines can be given together", "the two medicines cannot be given together"), ("it is safe for children", "it is not safe for children"),
        ("stop the medicine", "do not stop the medicine"), ("a second test is needed", "no second test is needed"),
        ("it should be taken with food", "it should never be taken with food"),
    ], [("يمكن إعطاء الدواءين معاً", "لا يمكن إعطاء الدواءين معاً"), ("هو آمن للأطفال", "هو غير آمن للأطفال")]),
    "opposite word": ("different", [
        ("this is a major interaction", "this is a minor interaction"), ("increase the dose", "decrease the dose"), ("the combination is allowed", "the combination is forbidden"),
        ("the level will rise", "the level will fall"), ("start the medicine before the meal", "start the medicine after the meal"),
        ("the risk is high", "the risk is low"),
    ], [("الجمع بينهما مسموح", "الجمع بينهما ممنوع"), ("زِد الجرعة", "أنقِص الجرعة")]),
    "who and what swapped": ("different", [
        ("Zorvalin is allowed and Merdapine is forbidden", "Merdapine is allowed and Zorvalin is forbidden"),
        ("give Kelvaxone first and Tibrolast second", "give Tibrolast first and Kelvaxone second"),
        ("the nurse signs and the doctor checks", "the doctor signs and the nurse checks"),
        ("morning dose 5 mg and evening dose 10 mg", "morning dose 10 mg and evening dose 5 mg"),
    ], [("زورفالين مسموح وميردابين ممنوع", "ميردابين مسموح وزورفالين ممنوع")]),
    "added condition": ("different", [
        ("the combination is allowed", "the combination is allowed only under supervision"), ("the dose can be raised", "the dose can be raised if kidney function is normal"),
        ("it is safe", "it is safe for adults only"), ("stop the medicine", "stop the medicine unless the fever returns"),
        ("give 5 mg", "give 5 mg at most"),
    ], [("الجمع بينهما مسموح", "الجمع بينهما مسموح تحت الإشراف فقط"), ("هو آمن", "هو آمن للبالغين فقط")]),
    "letter case that matters": ("different", [
        ("the dose is 5 mg", "the dose is 5 Mg"), ("the level is 2 mM", "the level is 2 MM"), ("ask the US office", "ask the us office"),
        ("the unit is mL", "the unit is ML"),
    ], []),
    "decimal or thousands mark": ("different", [
        ("the total is 1.000", "the total is 1,000"), ("the dose is 2.5 mg", "the dose is 2 5 mg"), ("the count is 12.500", "the count is 12 500"),
    ], []),
    # ---- the same thing said in another surface form
    "case and punctuation": ("same", [
        ("the dose is 5 mg", "The dose is 5 mg!"), ("stop the medicine", "Stop the medicine;"), ("yes, it is allowed", "Yes it is allowed"),
        ("it is safe for children", "It is safe for children…"), ("the answer is three weeks", "the answer is: three weeks"),
    ], [("نعم، هو مسموح", "نعم هو مسموح"), ("الجرعة 5 ملغ", "الجرعة 5 ملغ!")]),
    "markup and spacing": ("same", [
        ("the dose is 5 mg", "the dose is **5 mg**"), ("stop the medicine", "- stop the medicine"), ("it is allowed", "  it   is allowed  "),
        ("return within 30 days", "return within `30 days`"), ("it is safe", "(it is safe)"),
    ], [("هو مسموح", "- هو مسموح"), ("الجرعة 5 ملغ", "الجرعة  5   ملغ")]),
    "hyphen inside a word": ("same", [
        ("take an x-ray", "take an x ray"), ("a follow-up visit is needed", "a follow up visit is needed"), ("the long-term plan stays", "the long term plan stays"),
        ("use the 5-10 mg range", "use the 5 10 mg range"),
    ], []),
    "added courtesy": ("same", [
        ("the dose is 5 mg", "the dose is 5 mg, thanks"), ("stop the medicine", "certainly, stop the medicine"), ("it is allowed", "it is allowed, I hope this helps"),
        ("return within 30 days", "sure, return within 30 days"),
    ], [("هو مسموح", "هو مسموح، شكراً"), ("الجرعة 5 ملغ", "بالتأكيد، الجرعة 5 ملغ")]),
    "list in another order": ("same", [
        ("check weight, pulse and temperature", "check temperature, pulse and weight"), ("bring the card and the letter", "bring the letter and the card"),
        ("it comes in red, green and blue", "it comes in blue, green and red"),
    ], [("افحص الوزن والنبض والحرارة", "افحص الحرارة والنبض والوزن")]),
    "another word for the same thing": ("same", [
        ("ask the doctor", "ask the physician"), ("the medicine is allowed", "the drug is allowed"), ("begin the course today", "start the course today"),
        ("it is not needed", "it is unnecessary"), ("the result is fine", "the result is normal"),
    ], [("اسأل الطبيب", "اسأل الدكتور"), ("ابدأ العلاج اليوم", "باشر العلاج اليوم")]),
}


def rows() -> list[list[str]]:
    out = []
    for category, (gold, english, arabic) in CATEGORIES.items():
        for language, pairs, short, long in (("en", english, SHORT_EN, LONG_EN), ("ar", arabic, SHORT_AR, LONG_AR)):
            for length, frames in (("short", short), ("long", long)):
                for a, b in pairs:
                    for frame in frames:
                        out.append([f"t{len(out) + 1:04d}", category, gold, language, length, frame.format(x=a), frame.format(x=b)])
    return out


def write(path: str = os.path.join(HERE, "transitions.csv")) -> int:
    data = rows()
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["pair_id", "category", "gold", "language", "length", "answer_a", "answer_b"])
        writer.writerows(data)
    return len(data)


if __name__ == "__main__":
    print(f"wrote {write()} pairs")

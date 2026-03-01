"""
📊 BALL HISOBLASH VA NATIJA FORMATLASH
7 xil test turi uchun to'g'ri hisoblash
BUG FIX: "A)" va "A) Toshkent" bir xil harf — to'g'ri hisoblanadi
"""
import re
import logging
from typing import Any, Tuple

log = logging.getLogger(__name__)

LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]


def calculate_score(questions: list, answers: dict) -> dict:
    """Test natijasini hisoblash"""
    max_score = sum(q.get("points", 1) for q in questions)
    earned = correct = wrong = skipped = 0
    details = []

    for i, q in enumerate(questions):
        u_ans = answers.get(str(i))
        pts   = float(q.get("points", 1))
        is_c  = False
        ep    = 0.0

        if u_ans is None or str(u_ans).strip() == "":
            skipped += 1
        else:
            is_c, ep = _check(q, u_ans, pts)
            if is_c:
                correct += 1
            else:
                wrong += 1
            earned += ep

        details.append({
            "question_index": i,
            "is_correct":     is_c,
            "user_answer":    u_ans,
            "correct_answer": q.get("correct"),
            "explanation":    q.get("explanation", ""),
            "earned_points":  ep,
            "max_points":     pts,
        })

    pct = round(earned / max_score * 100, 2) if max_score else 0.0
    return {
        "score":            round(earned, 2),
        "max_score":        max_score,
        "percentage":       pct,
        "correct_count":    correct,
        "wrong_count":      wrong,
        "skipped_count":    skipped,
        "total_questions":  len(questions),
        "grade":            _grade(pct),
        "emoji":            _emoji(pct),
        "detailed_results": details,
    }


def _check(q: dict, ans: Any, pts: float) -> Tuple[bool, float]:
    """Javobni to'g'riligini tekshirish"""
    t       = q.get("type", "multiple_choice")
    correct = q.get("correct")
    if correct is None:
        return False, 0.0

    try:
        if t == "multiple_choice":
            # Faqat bosh harf solishtirish: "A" == "A) Toshkent"
            a_m = re.match(r"^([A-Za-z])", str(ans).strip())
            c_m = re.match(r"^([A-Za-z])", str(correct).strip())
            if a_m and c_m:
                ok = a_m.group(1).lower() == c_m.group(1).lower()
                return ok, pts if ok else 0.0
            ok = str(ans).strip().lower() == str(correct).strip().lower()
            return ok, pts if ok else 0.0

        elif t == "true_false":
            ok = str(ans).strip().lower() == str(correct).strip().lower()
            return ok, pts if ok else 0.0

        elif t == "multi_select":
            if isinstance(ans, list) and isinstance(correct, list):
                def ls(lst):
                    s = set()
                    for x in lst:
                        m = re.match(r"^([A-Za-z])", str(x).strip())
                        if m:
                            s.add(m.group(1).lower())
                    return s
                ok = ls(ans) == ls(correct)
                return ok, pts if ok else 0.0

        elif t in ("text_input", "fill_blank"):
            u   = str(ans).strip().lower()
            c   = str(correct).strip().lower()
            acc = [str(x).strip().lower() for x in q.get("accepted_answers", [])]
            ok  = u == c or u in acc
            return ok, pts if ok else 0.0

        elif t == "matching":
            if isinstance(correct, dict):
                ok = str(ans).strip() == str(correct).strip()
                return ok, pts if ok else 0.0

        elif t == "ordering":
            if isinstance(correct, list):
                ok = list(ans) == list(correct)
                return ok, pts if ok else 0.0

    except Exception as e:
        log.error(f"Scoring error: {e}")

    return False, 0.0


def _grade(p: float) -> str:
    if p >= 90: return "A+"
    if p >= 80: return "A"
    if p >= 70: return "B"
    if p >= 60: return "C"
    if p >= 50: return "D"
    return "F"


def _emoji(p: float) -> str:
    if p >= 90: return "🌟"
    if p >= 80: return "🔥"
    if p >= 70: return "👍"
    if p >= 60: return "👌"
    if p >= 50: return "⚠️"
    return "❌"


def format_result(res: dict, test: dict) -> str:
    """Yakuniy natija xabari matni"""
    pct    = res.get("percentage", 0)
    passed = pct >= test.get("passing_score", 60)
    m, s   = divmod(res.get("time_spent", 0), 60)
    emoji  = res.get("emoji", "📝")
    grade  = res.get("grade", "F")

    if passed:
        holat = "🎉 MUVAFFAQIYATLI O'TDINGIZ!"
    else:
        holat = f"❌ YIQILDINGIZ. (O'tish: {test.get('passing_score', 60)}%)"

    return (
        f"{emoji} <b>TEST NATIJASI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>{test.get('title', 'Test')}</b>\n"
        f"📁 Fan: {test.get('category', '')}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 O'zlashtirish: <b>{pct}%</b>\n"
        f"🎯 Baho: <b>{grade}</b>\n"
        f"✅ To'g'ri: <b>{res.get('correct_count', 0)}</b>   "
        f"❌ Xato: <b>{res.get('wrong_count', 0)}</b>   "
        f"⏭ O'tkazilgan: <b>{res.get('skipped_count', 0)}</b>\n"
        f"⏱ Vaqt: <b>{m} daq {s:02d} son</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 {holat}"
    )

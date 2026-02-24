"""
📊 SCORING VA ANALYTICS (PRO VERSIYA)
Barcha 7 xil test turlari uchun aniq hisoblash va natijalarni tahlil qilish moduli.
"""
import logging
import re
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

# ==========================================================
# 1. ASOSIY HISOBLASH MANTIQI
# ==========================================================

def calculate_score(questions: List[Dict], user_answers: Dict) -> Dict:
    """
    Foydalanuvchi javoblarini tekshirish va yakuniy natijani hisoblash.
    """
    total_questions = len(questions)
    total_possible_score = sum(q.get("points", 1) for q in questions)
    
    earned_score = 0
    correct_count = 0
    wrong_count = 0
    skipped_count = 0
    detailed_results = []
    
    for i, question in enumerate(questions):
        q_id = str(i)
        user_ans = user_answers.get(q_id)
        q_points = question.get("points", 1)
        
        is_correct = False
        partial_score = 0
        
        if user_ans is None or str(user_ans).strip() == "":
            skipped_count += 1
        else:
            is_correct, partial_score = _check_answer(question, user_ans)
            if is_correct:
                correct_count += 1
                earned_score += partial_score
            else:
                wrong_count += 1
                # Ba'zi murakkab testlarda qisman to'g'ri javob uchun qisman ball berilishi mumkin
                earned_score += partial_score
                
        detailed_results.append({
            "question_index": i,
            "is_correct": is_correct,
            "earned_points": partial_score,
            "max_points": q_points,
            "user_answer": user_ans,
            "correct_answer": question.get("correct")
        })

    # O'rtacha foizni hisoblash
    if total_possible_score > 0:
        percentage = (earned_score / total_possible_score) * 100
    else:
        percentage = 0.0

    # Baho va emojini aniqlash
    grade = _get_grade(percentage)
    emoji_grade = _get_emoji(percentage)

    return {
        "score": earned_score,
        "total_possible_score": total_possible_score,
        "percentage": round(percentage, 2),
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "skipped_count": skipped_count,
        "total_questions": total_questions,
        "grade": grade,
        "emoji_grade": emoji_grade,
        "detailed_results": detailed_results
    }


# ==========================================================
# 2. TEST TURLARI BO'YICHA JAVOBLARNI TEKSHIRISH
# ==========================================================

def _check_answer(question: Dict, user_ans: Any) -> Tuple[bool, float]:
    """
    Test turiga qarab foydalanuvchi javobini to'g'ri javob bilan solishtiradi.
    Qaytaradi: (To'g'rimi(bool), Qozonilgan_ball(float))
    """
    q_type = question.get("type", "multiple_choice")
    correct = question.get("correct")
    points = float(question.get("points", 1))
    
    if correct is None:
        return False, 0.0

    try:
        # 🔘 1. BIR JAVOBLI VA HA/YO'Q
        if q_type in ["multiple_choice", "true_false"]:
            if str(user_ans).strip().lower() == str(correct).strip().lower():
                return True, points

        # ☑️ 2. KO'P JAVOBLI (Multi Select)
        elif q_type == "multi_select":
            # user_ans va correct ikkalasi ham List (ro'yxat) bo'lishi kerak
            if isinstance(user_ans, list) and isinstance(correct, list):
                # Elementlarni solishtirish uchun to'plamga (Set) aylantiramiz
                if set(user_ans) == set(correct):
                    return True, points
                else:
                    # Qisman to'g'ri topilganlar uchun ball hisoblash (Ixtiyoriy)
                    correct_hits = len(set(user_ans).intersection(set(correct)))
                    wrong_hits = len(set(user_ans) - set(correct))
                    if correct_hits > 0 and wrong_hits == 0:
                        partial = (points / len(correct)) * correct_hits
                        return False, partial

        # ✍️ 3. YOZMA VA BO'SH JOY (Text Input & Fill Blank)
        elif q_type in ["text_input", "fill_blank"]:
            ans_str = str(user_ans).strip().lower()
            correct_str = str(correct).strip().lower()
            accepted = [str(x).strip().lower() for x in question.get("accepted_answers", [])]
            
            if ans_str == correct_str or ans_str in accepted:
                return True, points

        # 🔗 4. MOSLASHTIRISH (Matching)
        elif q_type == "matching":
            # Foydalanuvchi "1-a, 2-b" kabi yozadi
            # Biz uni probellar va belgilarni olib tashlab solishtiramiz
            ans_str = re.sub(r'[^a-zA-Z0-9]', '', str(user_ans).lower())
            # To'g'ri javobni ham shunday formatga keltiramiz (Agar dict bo'lsa)
            if isinstance(correct, dict):
                correct_str = ""
                for k, v in correct.items():
                    correct_str += re.sub(r'[^a-zA-Z0-9]', '', str(k).lower() + str(v).lower())
                
                # Agar foydalanuvchi yozgan matn ichida barcha to'g'ri juftliklar qatnashgan bo'lsa
                if ans_str == correct_str: # Ideal holat
                    return True, points

        # 🔢 5. TARTIBLASH (Ordering)
        elif q_type == "ordering":
            # Foydalanuvchi "3, 1, 4, 2" deb yozadi
            ans_nums = re.findall(r'\d+', str(user_ans))
            
            # To'g'ri javoblar ro'yxati asosida to'g'ri tartibdagi raqamlarni aniqlash
            # Bu biroz murakkab, agar user ro'yxatni tartib raqamlarida yuborgan bo'lsa:
            if isinstance(correct, list):
                # Soddalashtirilgan tekshiruv: agar tartib aniq mos kelsa
                correct_nums = [str(i+1) for i in range(len(correct))]
                if ans_nums == correct_nums:
                    return True, points

    except Exception as e:
        logger.error(f"Javobni tekshirishda xato ({q_type}): {e}")
        
    return False, 0.0


# ==========================================================
# 3. FORMATLASH VA BAHOLASH (UI)
# ==========================================================

def _get_grade(percentage: float) -> str:
    """Foizga qarab harfli baho berish"""
    if percentage >= 90: return "A+"
    elif percentage >= 80: return "A"
    elif percentage >= 70: return "B"
    elif percentage >= 60: return "C"
    elif percentage >= 50: return "D"
    else: return "F"

def _get_emoji(percentage: float) -> str:
    """Foizga qarab hissiyot (emoji) qaytarish"""
    if percentage >= 90: return "🌟"
    elif percentage >= 80: return "🔥"
    elif percentage >= 70: return "👍"
    elif percentage >= 60: return "👌"
    elif percentage >= 50: return "⚠️"
    else: return "❌"

def format_result_message(result: Dict, test: Dict, user_name: str) -> str:
    """
    Test tugagach foydalanuvchiga yuboriladigan chiroyli va 
    batafsil hisobot (HTML formatda) yasaydi.
    """
    emoji = result.get("emoji_grade", "📝")
    grade = result.get("grade", "F")
    percentage = result.get("percentage", 0.0)
    correct = result.get("correct_count", 0)
    wrong = result.get("wrong_count", 0)
    skipped = result.get("skipped_count", 0)
    total = result.get("total_questions", 0)
    time_spent = result.get("time_spent", 0)
    
    passing_score = result.get("passing_score", 60)
    passed = percentage >= passing_score
    
    pass_text = "✅ <b>MUVAFFAQIYATLI O'TDINGIZ!</b>" if passed else "❌ <b>O'TA OLDINGIZ</b> (Yiqildingiz)"
    
    minutes = time_spent // 60
    seconds = time_spent % 60
    
    msg = f"""
{emoji} <b>TEST NATIJASI:</b>

👤 <b>O'quvchi:</b> {user_name}
📝 <b>Fan/Test:</b> {test.get('title', 'Nomsiz test')}

━━━━━━━━━━━━━━━━━━━━━
📊 <b>O'zlashtirish:</b> {percentage}%
🎯 <b>Sifat darajasi (Baho):</b> {grade}
{pass_text}
━━━━━━━━━━━━━━━━━━━━━
✅ <b>To'g'ri javoblar:</b> {correct} ta
❌ <b>Xatolar:</b> {wrong} ta
⏭ <b>O'tkazib yuborilgan:</b> {skipped} ta
⏱ <b>Sarflangan vaqt:</b> {minutes} daqiqa {seconds:02d} soniya
━━━━━━━━━━━━━━━━━━━━━
"""
    
    if passed:
        msg += "\n🎉 <i>Ajoyib natija! Shunday davom eting!</i>"
    else:
        msg += f"\n💡 <i>O'tish uchun kamida {passing_score}% yig'ish kerak. Qaytadan urinib ko'ring!</i>"
        
    return msg

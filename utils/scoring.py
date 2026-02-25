"""
📊 SCORING VA ANALYTICS (PRO VERSIYA)
Barcha 7 xil test turlari uchun hisoblash moduli.
BUG FIX: "B)" va "B) play" endi 100% to'g'ri hisoblanadi (faqat harf tekshiriladi).
"""
import logging
import re
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

def calculate_score(questions: List[Dict], user_answers: Dict) -> Dict:
    total_questions = len(questions)
    total_possible_score = sum(q.get("points", 1) for q in questions)
    earned_score = correct_count = wrong_count = skipped_count = 0
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
                earned_score += partial_score
                
        detailed_results.append({
            "question_index": i, "is_correct": is_correct, "earned_points": partial_score,
            "max_points": q_points, "user_answer": user_ans, "correct_answer": question.get("correct")
        })

    percentage = (earned_score / total_possible_score) * 100 if total_possible_score > 0 else 0.0
    return {
        "score": earned_score, "total_possible_score": total_possible_score,
        "percentage": round(percentage, 2), "correct_count": correct_count,
        "wrong_count": wrong_count, "skipped_count": skipped_count,
        "total_questions": total_questions, "grade": _get_grade(percentage),
        "emoji_grade": _get_emoji(percentage), "detailed_results": detailed_results
    }

def _check_answer(question: Dict, user_ans: Any) -> Tuple[bool, float]:
    q_type = question.get("type", "multiple_choice")
    correct = question.get("correct")
    points = float(question.get("points", 1))
    
    if correct is None: return False, 0.0

    try:
        # 🛡️ FIX: A, B, C, D harflarini aniq ajratib olish (B) va B) play)
        if q_type == "multiple_choice":
            ans_str = str(user_ans).strip()
            corr_str = str(correct).strip()
            
            # Matn boshidagi harfni tutib olamiz (A, B, C yoki D)
            ans_match = re.search(r'^([A-Za-z])', ans_str)
            corr_match = re.search(r'^([A-Za-z])', corr_str)
            
            if ans_match and corr_match:
                if ans_match.group(1).lower() == corr_match.group(1).lower():
                    return True, points
            
            # Agar yuqoridagi ishlamasa, oddiy tekshiruv (zaxira)
            if corr_str.lower().startswith(ans_str.lower()) or ans_str.lower() == corr_str.lower():
                return True, points

        elif q_type == "true_false":
            ans_str = str(user_ans).strip().lower()
            corr_str = str(correct).strip().lower()
            if corr_str.startswith(ans_str) or ans_str == corr_str:
                return True, points

        elif q_type == "multi_select":
            if isinstance(user_ans, list) and isinstance(correct, list):
                # Harflarni ajratib olish va solishtirish
                ans_clean = []
                for a in user_ans:
                    m = re.search(r'^([A-Za-z])', str(a).strip())
                    if m: ans_clean.append(m.group(1).lower())
                    
                corr_clean = []
                for c in correct:
                    m = re.search(r'^([A-Za-z])', str(c).strip())
                    if m: corr_clean.append(m.group(1).lower())
                
                if set(ans_clean) == set(corr_clean): return True, points

        elif q_type in ["text_input", "fill_blank"]:
            ans_str = str(user_ans).strip().lower()
            correct_str = str(correct).strip().lower()
            accepted = [str(x).strip().lower() for x in question.get("accepted_answers", [])]
            if ans_str == correct_str or ans_str in accepted:
                return True, points

        elif q_type == "matching":
            ans_str = re.sub(r'[^a-zA-Z0-9]', '', str(user_ans).lower())
            if isinstance(correct, dict):
                correct_str = ""
                for k, v in correct.items():
                    correct_str += re.sub(r'[^a-zA-Z0-9]', '', str(k).lower() + str(v).lower())
                if ans_str == correct_str: return True, points

        elif q_type == "ordering":
            ans_nums = re.findall(r'\d+', str(user_ans))
            if isinstance(correct, list):
                correct_nums = [str(i+1) for i in range(len(correct))]
                if ans_nums == correct_nums: return True, points

    except Exception as e:
        logger.error(f"Tekshirish xatosi: {e}")
        
    return False, 0.0

def _get_grade(percentage: float) -> str:
    if percentage >= 90: return "A+"
    elif percentage >= 80: return "A"
    elif percentage >= 70: return "B"
    elif percentage >= 60: return "C"
    elif percentage >= 50: return "D"
    else: return "F"

def _get_emoji(percentage: float) -> str:
    if percentage >= 90: return "🌟"
    elif percentage >= 80: return "🔥"
    elif percentage >= 70: return "👍"
    elif percentage >= 60: return "👌"
    elif percentage >= 50: return "⚠️"
    else: return "❌"

def format_result_message(result: Dict, test: Dict, user_name: str) -> str:
    emoji, grade, percentage = result.get("emoji_grade", "📝"), result.get("grade", "F"), result.get("percentage", 0.0)
    passed = percentage >= result.get("passing_score", 60)
    pass_text = "✅ <b>MUVAFFAQIYATLI O'TDINGIZ!</b>" if passed else "❌ <b>O'TA OLDINGIZ</b>"
    
    m, s = divmod(result.get("time_spent", 0), 60)
    
    msg = f"""
{emoji} <b>TEST NATIJASI:</b>\n👤 <b>O'quvchi:</b> {user_name}
📝 <b>Test:</b> {test.get('title', 'Nomsiz test')}\n━━━━━━━━━━━━━━━
📊 <b>O'zlashtirish:</b> {percentage}%
🎯 <b>Baho:</b> {grade}\n{pass_text}\n━━━━━━━━━━━━━━━
✅ <b>To'g'ri:</b> {result.get('correct_count', 0)} | ❌ <b>Xato:</b> {result.get('wrong_count', 0)}
⏭ <b>O'tkazilgan:</b> {result.get('skipped_count', 0)} | ⏱ <b>Vaqt:</b> {m} daq {s:02d} soniya
"""
    return msg
                

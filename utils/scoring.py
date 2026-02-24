"""
📊 SCORING VA ANALYTICS
Test natijalarini hisoblash va tahlil qilish
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def calculate_score(questions: List[Dict], user_answers: Dict) -> Dict:
    """
    Foydalanuvchi javoblarini tekshirish va natija hisoblash
    
    Returns:
        {
            score, percentage, correct_count, wrong_count,
            skipped_count, total_questions, detailed_results
        }
    """
    total_questions = len(questions)
    total_possible_score = sum(q.get("score", 1) for q in questions)
    
    earned_score = 0
    correct_count = 0
    wrong_count = 0
    skipped_count = 0
    detailed_results = []
    
    for i, question in enumerate(questions):
        q_id = str(i)
        q_type = question.get("type", "multiple_choice")
        user_ans = user_answers.get(q_id)
        q_score = question.get("score", 1)
        
        is_correct = False
        partial_score = 0
        
        if user_ans is None:
            skipped_count += 1
        else:
            is_correct, partial_score = _check_answer(question, user_ans)
            if is_correct:
                correct_count += 1
                earned_score += partial_score
            else:
                wrong_count += 1
                # Qisman to'g'ri (multi_select)
                if partial_score > 0:
                    earned_score += partial_score
        
        detailed_results.append({
            "question_number": i + 1,
            "question": question.get("question", ""),
            "question_type": q_type,
            "user_answer": user_ans,
            "correct_answer": _get_correct_display(question),
            "is_correct": is_correct,
            "partial_score": partial_score,
            "max_score": q_score,
            "explanation": question.get("explanation", "")
        })
    
    percentage = (earned_score / total_possible_score * 100) if total_possible_score > 0 else 0
    
    return {
        "score": round(earned_score, 2),
        "total_possible": total_possible_score,
        "percentage": round(percentage, 1),
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "skipped_count": skipped_count,
        "total_questions": total_questions,
        "detailed_results": detailed_results,
        "grade": _get_grade(percentage),
        "emoji_grade": _get_emoji_grade(percentage)
    }


def _check_answer(question: Dict, user_answer) -> Tuple[bool, float]:
    """Bitta savolni tekshirish. (is_correct, score) qaytaradi"""
    q_type = question.get("type", "multiple_choice")
    q_score = question.get("score", 1)
    
    if q_type == "multiple_choice":
        correct = question.get("correct_answer", 0)
        is_correct = int(user_answer) == correct
        return is_correct, q_score if is_correct else 0
    
    elif q_type == "true_false":
        correct = question.get("correct_answer", 0)
        is_correct = int(user_answer) == correct
        return is_correct, q_score if is_correct else 0
    
    elif q_type == "multi_select":
        correct_set = set(question.get("correct_answers", []))
        user_set = set(user_answer) if isinstance(user_answer, list) else {user_answer}
        
        if correct_set == user_set:
            return True, q_score
        elif user_set.issubset(correct_set) and user_set:
            # Qisman to'g'ri
            partial = q_score * len(user_set & correct_set) / len(correct_set)
            return False, round(partial, 1)
        return False, 0
    
    elif q_type in ["text_input", "fill_blank"]:
        acceptable = question.get("acceptable_answers", [])
        correct = question.get("correct_answer", "")
        user_text = str(user_answer).strip().lower()
        
        is_correct = (user_text in [a.lower() for a in acceptable] or 
                     user_text == correct.lower())
        return is_correct, q_score if is_correct else 0
    
    elif q_type == "matching":
        correct_pairs = question.get("correct_pairs", {})
        # user_answer = {left_idx: right_idx}
        if isinstance(user_answer, dict):
            correct_count = sum(
                1 for k, v in user_answer.items() 
                if str(k) in correct_pairs and correct_pairs[str(k)] == v
            )
            total_pairs = len(correct_pairs)
            if correct_count == total_pairs:
                return True, q_score
            partial = q_score * correct_count / total_pairs
            return False, round(partial, 1)
        return False, 0
    
    elif q_type == "ordering":
        correct_order = question.get("correct_order", [])
        is_correct = list(user_answer) == correct_order
        return is_correct, q_score if is_correct else 0
    
    return False, 0


def _get_correct_display(question: Dict) -> str:
    """To'g'ri javobni ko'rsatish uchun matn"""
    q_type = question.get("type", "multiple_choice")
    
    if q_type in ["multiple_choice", "true_false"]:
        idx = question.get("correct_answer", 0)
        options = question.get("options", [])
        if 0 <= idx < len(options):
            return options[idx]
    
    elif q_type == "multi_select":
        idxs = question.get("correct_answers", [])
        options = question.get("options", [])
        return ", ".join(options[i] for i in idxs if i < len(options))
    
    elif q_type in ["text_input", "fill_blank"]:
        return question.get("correct_answer", "")
    
    elif q_type == "matching":
        left = question.get("left_items", [])
        right = question.get("right_items", [])
        pairs = question.get("correct_pairs", {})
        return " | ".join(f"{left[int(k)]} → {right[v]}" for k, v in pairs.items() if int(k) < len(left) and v < len(right))
    
    elif q_type == "ordering":
        items = question.get("items", [])
        order = question.get("correct_order", [])
        return " → ".join(items[i] for i in order if i < len(items))
    
    return "Noma'lum"


def _get_grade(percentage: float) -> str:
    """Foizdan baho"""
    if percentage >= 90:
        return "A+ (A'lo)"
    elif percentage >= 80:
        return "A (Yaxshi)"
    elif percentage >= 70:
        return "B (O'rta)"
    elif percentage >= 60:
        return "C (Qoniqarli)"
    elif percentage >= 50:
        return "D (Yomonroq)"
    else:
        return "F (Qoniqarsiz)"


def _get_emoji_grade(percentage: float) -> str:
    if percentage >= 90:
        return "🏆"
    elif percentage >= 75:
        return "🥇"
    elif percentage >= 60:
        return "🥈"
    elif percentage >= 50:
        return "🥉"
    else:
        return "📚"


def format_result_message(result: Dict, test: Dict, user_name: str) -> str:
    """Natija xabarini formatlash"""
    emoji = result["emoji_grade"]
    grade = result["grade"]
    percentage = result["percentage"]
    correct = result["correct_count"]
    wrong = result["wrong_count"]
    skipped = result["skipped_count"]
    total = result["total_questions"]
    time_spent = result.get("time_spent", 0)
    
    passed = percentage >= test.get("passing_score", 60)
    pass_text = "✅ O'TDINGIZ!" if passed else "❌ O'TMADINGIZ"
    
    minutes = time_spent // 60
    seconds = time_spent % 60
    
    msg = f"""
{emoji} <b>TEST NATIJASI</b>

👤 <b>{user_name}</b>
📝 <b>{test.get('title', 'Test')}</b>

━━━━━━━━━━━━━━━
📊 Natija: <b>{percentage}%</b>
🎯 Baho: <b>{grade}</b>
{pass_text}
━━━━━━━━━━━━━━━
✅ To'g'ri: <b>{correct}/{total}</b>
❌ Noto'g'ri: <b>{wrong}/{total}</b>
⏭ O'tkazilgan: <b>{skipped}/{total}</b>
⏱ Sarflangan vaqt: <b>{minutes}:{seconds:02d}</b>
━━━━━━━━━━━━━━━
"""
    
    if passed:
        msg += "\n🎉 Tabriklaymiz! Zo'r natija!"
    else:
        msg += f"\n💪 Ko'proq o'qing! O'tish ball: {test.get('passing_score', 60)}%"
    
    return msg.strip()


def generate_certificate_text(user_name: str, test_title: str, percentage: float, date: str) -> str:
    """Sertifikat matni"""
    return f"""
SERTIFIKAT

Bu sertifikat tasdiqlaydiki,

{user_name}

"{test_title}" testini muvaffaqiyatli yakunladi
va {percentage}% natija ko'rsatdi.

Sana: {date}
"""

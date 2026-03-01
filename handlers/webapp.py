"""
🌐 TELEGRAM WEB APP HANDLER
Foydalanuvchi Web App (popup oyna) da test yechib tugatgach,
bot xabar qabul qiladi va natijani Firebase ga saqlaydi.

Qanday ishlaydi:
  1. Foydalanuvchi bot da "🎮 Web App" tugmasini bosadi
  2. Telegram ichida popup oyna ochiladi (test.html / history.html / create.html)
  3. Foydalanuvchi test yechib tugatadi
  4. HTML fayl window.Telegram.WebApp.sendData(JSON.stringify(result)) chaqiradi
  5. Bot shu xabarni qabul qiladi va bu handler ishlaydi
"""
import json
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import StateFilter

from firebase.db import save_result, get_test
from keyboards.keyboards import result_keyboard, webapp_review_keyboard

log = logging.getLogger(__name__)
router = Router()


# ═══════════════════════════════════════════════════════════
# WEB APP DAN KELGAN MA'LUMOTNI QABUL QILISH
# ═══════════════════════════════════════════════════════════

@router.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    """
    Telegram Web App sendData() orqali yuborilgan JSON ni qayta ishlash.
    
    test.html dan kelgan ma'lumot formati:
    {
        "type": "test_result",
        "test_id": "ABC123",
        "title": "Test nomi",
        "score": 85,
        "correct": 17,
        "total": 20,
        "elapsed": 145,
        "passed": true,
        "questions": [
            {
                "origIdx": 0,
                "text": "Savol matni",
                "status": "correct",  // correct | wrong | skip
                "userAnswer": "A",
                "correctAnswer": "A",
                "pts": 1,
                "explanation": "Izoh"
            },
            ...
        ]
    }
    
    create.html dan kelgan ma'lumot formati:
    {
        "type": "test_created",
        "test": { ...test ma'lumotlari... }
    }
    """
    uid = message.from_user.id
    raw = message.web_app_data.data

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        log.warning(f"Web App dan noto'g'ri JSON: {raw[:200]}")
        await message.answer("❌ Ma'lumot formati noto'g'ri. Qayta urinib ko'ring.")
        return

    msg_type = data.get("type", "unknown")

    # ── Test natijasi ─────────────────────────────────────
    if msg_type == "test_result":
        await _handle_test_result(message, data)

    # ── Test yaratildi ────────────────────────────────────
    elif msg_type == "test_created":
        await _handle_test_created(message, data)

    # ── Noma'lum ─────────────────────────────────────────
    else:
        log.warning(f"Noma'lum Web App data type: {msg_type}")
        await message.answer("⚠️ Noma'lum ma'lumot turi keldi.")


async def _handle_test_result(message: Message, data: dict):
    """Test natijasini qayta ishlash va Firebasega saqlash"""
    uid     = message.from_user.id
    test_id = data.get("test_id", "")
    score   = data.get("score", 0)
    correct = data.get("correct", 0)
    total   = data.get("total", 1)
    elapsed = data.get("elapsed", 0)
    passed  = data.get("passed", False)
    title   = data.get("title", "Test")
    questions = data.get("questions", [])

    # ── Firebase ga saqlash ───────────────────────────────
    scored = {
        "percentage":       score,
        "passed":           passed,
        "correct_answers":  correct,
        "total_questions":  total,
        "time_spent":       elapsed,
        "passing_score":    data.get("passScore", 60),
        "mode":             "webapp",
        "detailed_results": [
            {
                "question_index": q.get("origIdx", i),
                "is_correct":     q.get("status") == "correct",
                "user_answer":    q.get("userAnswer"),
                "correct_answer": q.get("correctAnswer"),
                "earned_points":  q.get("pts", 0),
                "max_points":     1,
            }
            for i, q in enumerate(questions)
        ]
    }

    rid = ""
    try:
        rid = save_result(uid, test_id, scored)
    except Exception as e:
        log.error(f"Natija saqlashda xato: {e}")

    # ── Natija xabari ─────────────────────────────────────
    m = elapsed // 60
    s = elapsed % 60
    status_icon = "🏆" if passed else "😔"
    status_text = "MUVAFFAQIYATLI" if passed else "MUVAFFAQIYATSIZ"

    bar_len = 10
    filled  = round(score / 100 * bar_len)
    bar     = "🟩" * filled + "🟥" * (bar_len - filled)

    text = (
        f"{status_icon} <b>TEST NATIJASI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>{title}</b>\n"
        f"{bar}  <b>{score}%</b>\n\n"
        f"✅ To'g'ri:   <b>{correct}</b> ta\n"
        f"❌ Xato:     <b>{total - correct}</b> ta\n"
        f"📋 Jami:     <b>{total}</b> ta\n"
        f"⏱ Vaqt:     <b>{m}:{s:02d}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>{status_icon} {status_text}</b>"
    )

    # Review uchun ma'lumot tayyorlash
    review_data = {
        "title":     title,
        "score":     score,
        "correct":   correct,
        "total":     total,
        "passed":    passed,
        "elapsed":   elapsed,
        "questions": questions,
    }

    keyboard = result_keyboard(test_id, rid, review_data)
    await message.answer(text, reply_markup=keyboard)


async def _handle_test_created(message: Message, data: dict):
    """Yangi test yaratilganini qayta ishlash"""
    test_data = data.get("test", {})
    title = test_data.get("title", "Yangi test")
    qcount = len(test_data.get("questions", []))

    await message.answer(
        f"✅ <b>Test muvaffaqiyatli yaratildi!</b>\n\n"
        f"📝 Nomi: <b>{title}</b>\n"
        f"📋 Savollar: <b>{qcount} ta</b>\n\n"
        f"🎓 Test bazaga qo'shildi. Endi foydalanuvchilar uni yecha oladi!",
    )

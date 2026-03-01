"""
🌐 TELEGRAM WEB APP HANDLER — Firebase yo'q versiya
Foydalanuvchi Web App da test yechib/yaratib tugatgach,
bot JSON xabar qabul qiladi.

Qanday ishlaydi:
  1. Bot test_info_keyboard da WebAppInfo(url=...) beradi
     URL da ?data=BASE64_JSON — test ma'lumoti to'liq
  2. test.html Firebase siz ishlaydi, faqat URL dan o'qiydi
  3. Foydalanuvchi testni tugatgach:
     window.Telegram.WebApp.sendData(JSON.stringify(result))
  4. Bu handler shu natijani qabul qiladi va botga yuboradi
"""
import json
import logging
from aiogram import Router, F
from aiogram.types import Message

log = logging.getLogger(__name__)
router = Router()


@router.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    """
    Telegram Web App sendData() ni qabul qilish.

    Keluvchi JSON turlari:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. test_result  — foydalanuvchi test yechib tugatdi
    2. test_created — foydalanuvchi yangi test yaratdi
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    uid = message.from_user.id
    raw = message.web_app_data.data

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as e:
        log.warning(f"[WebApp] Noto'g'ri JSON uid={uid}: {e}")
        await message.answer("❌ Ma'lumot formati noto'g'ri. Qayta urinib ko'ring.")
        return

    msg_type = data.get("type", "unknown")
    log.info(f"[WebApp] uid={uid} type={msg_type}")

    if msg_type == "test_result":
        await _handle_test_result(message, data)
    elif msg_type == "test_created":
        await _handle_test_created(message, data)
    else:
        log.warning(f"[WebApp] Noma'lum type: {msg_type}")
        await message.answer("⚠️ Noma'lum ma'lumot turi.")


# ══════════════════════════════════════════════════════════
# TEST NATIJASI
# ══════════════════════════════════════════════════════════

async def _handle_test_result(message: Message, data: dict):
    """
    test.html dan kelgan natija:
    {
      type, test_id, title, score, correct, total,
      elapsed, passed, passScore, questions:[...]
    }
    """
    uid       = message.from_user.id
    test_id   = data.get("test_id", "")
    score     = data.get("score", 0)
    correct   = data.get("correct", 0)
    total     = data.get("total", 1)
    elapsed   = data.get("elapsed", 0)
    passed    = data.get("passed", False)
    title     = data.get("title", "Test")
    questions = data.get("questions", [])

    # Firebase ga saqlash
    rid = ""
    try:
        from firebase.db import save_result
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
        rid = save_result(uid, test_id, scored)
    except Exception as e:
        log.error(f"[WebApp] Natija saqlashda xato: {e}")

    # Xabar matni
    m = elapsed // 60
    s = elapsed % 60
    bar_len = 10
    filled  = round(score / 100 * bar_len)
    bar     = "🟩" * filled + "🟥" * (bar_len - filled)
    status_icon = "🏆" if passed else "😔"

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
        f"<b>{status_icon} {'MUVAFFAQIYATLI' if passed else 'MUVAFFAQIYATSIZ'}</b>"
    )

    # Natija klaviaturasi (Web App tahlil + oddiy)
    review_data = {
        "title":     title,
        "score":     score,
        "correct":   correct,
        "total":     total,
        "passed":    passed,
        "elapsed":   elapsed,
        "questions": questions,
    }

    from keyboards.keyboards import result_keyboard
    await message.answer(text, reply_markup=result_keyboard(test_id, rid, review_data))


# ══════════════════════════════════════════════════════════
# TEST YARATISH
# ══════════════════════════════════════════════════════════

async def _handle_test_created(message: Message, data: dict):
    """
    create.html dan kelgan test:
    {
      type: "test_created",
      test: { title, category, difficulty, timeLimit, passScore,
               showResult, shuffleQuestions, questions:[...] }
    }
    """
    uid  = message.from_user.id
    test = data.get("test", {})

    if not test:
        await message.answer("❌ Test ma'lumotlari bo'sh keldi.")
        return

    title   = test.get("title", "Yangi test")
    qs      = test.get("questions", [])
    qcount  = len(qs)
    cat     = test.get("category", "Boshqa")
    diff    = test.get("difficulty", "medium")
    diff_map = {"easy": "🟢 Oson", "medium": "🟡 O'rtacha",
                "hard": "🔴 Qiyin", "expert": "⚡ Ekspert"}

    # Firebase ga saqlash
    tid = ""
    try:
        from firebase.db import create_test
        test_data_to_save = {
            "title":         title,
            "category":      cat,
            "difficulty":    diff,
            "time_limit":    test.get("timeLimit", 0),
            "passing_score": test.get("passScore", 60),
            "visibility":    "public",
            "questions":     qs,
        }
        tid = create_test(uid, test_data_to_save)
    except Exception as e:
        log.error(f"[WebApp] Test saqlashda xato: {e}")

    # Tasdiqlash xabari
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    if tid:
        builder.row(InlineKeyboardButton(
            text="▶️ Testni sinab ko'rish",
            callback_data=f"start_test_{tid}"
        ))
        builder.row(InlineKeyboardButton(
            text="🔗 Ulashish",
            callback_data=f"share_test_{tid}"
        ))
    builder.row(InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu"))

    await message.answer(
        f"✅ <b>TEST MUVAFFAQIYATLI YARATILDI!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 Nomi: <b>{title}</b>\n"
        f"📁 Fan: <b>{cat}</b>\n"
        f"⚡ Qiyinlik: <b>{diff_map.get(diff, diff)}</b>\n"
        f"📋 Savollar: <b>{qcount} ta</b>\n"
        f"{'🆔 ID: <code>' + tid + '</code>' if tid else ''}\n\n"
        f"🎉 Foydalanuvchilar endi bu testni yecha oladi!",
        reply_markup=builder.as_markup()
    )

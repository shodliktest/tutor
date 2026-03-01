"""
📊 POLL TEST HANDLER — Telegram Native Quiz Poll rejimi
Quiz Bot uslubida test ishlash, lekin natijalar bazaga saqlanadi!

Qanday ishlaydi:
1. Foydalanuvchi "📊 Poll test" ni bosadi
2. Bot har bir savol uchun native quiz poll yuboradi
3. Foydalanuvchi javob beradi (Telegram o'zi to'g'ri/noto'g'ri ko'rsatadi)
4. Barcha savollar tugagach — yakuniy natija saqlanadi va ko'rsatiladi
"""
import time
import logging
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message, Poll, PollAnswer
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from firebase.db import get_test, save_result
from utils.states import PollTest
from utils.scoring import calculate_score, format_result
from keyboards.keyboards import main_reply_keyboard, result_keyboard

log = logging.getLogger(__name__)
router = Router()

LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]


# ═══════════════════════════════════════════════════════════
# 1. POLL TEST BOSHLASH
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("start_poll_"))
async def start_poll_test(callback: CallbackQuery, state: FSMContext):
    """Poll rejimida test boshlash"""
    await callback.answer()
    tid  = callback.data[11:]
    test = get_test(tid)

    if not test:
        await callback.message.answer("❌ Test topilmadi.")
        return

    qs = test.get("questions", [])
    if not qs:
        await callback.message.answer("❌ Bu testda savollar yo'q.")
        return

    # Faqat multiple_choice va true_false savollari poll uchun mos
    poll_qs = [q for q in qs if q.get("type", "multiple_choice") in ("multiple_choice", "true_false")]
    if not poll_qs:
        await callback.message.answer(
            "⚠️ Bu testda faqat matnli savollar bor.\n"
            "Poll test faqat A/B/C/D va Ha/Yo'q savollarni qo'llab-quvvatlaydi.\n\n"
            "Iltimos <b>▶️ Inline test</b> rejimini ishlating.",
            reply_markup=InlineKeyboardBuilder().row(
                InlineKeyboardButton(text="▶️ Inline test", callback_data=f"start_test_{tid}")
            ).as_markup()
        )
        return

    await state.set_state(PollTest.active)
    await state.set_data({
        "test_id":       tid,
        "test_data":     test,
        "questions":     poll_qs,
        "current_index": 0,
        "user_answers":  {},
        "poll_msg_ids":  [],   # Yuborilgan poll message id lari
        "chat_id":       callback.message.chat.id,
        "start_time":    time.time(),
    })

    # Joriy savol xabarini o'chirish
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Boshlash xabari
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏹ Testni to'xtatish", callback_data="cancel_poll"))
    msg = await callback.bot.send_message(
        callback.message.chat.id,
        f"<b>📊 POLL TEST BOSHLANDI!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>{test.get('title')}</b>\n"
        f"📋 Savollar: <b>{len(poll_qs)} ta</b>\n\n"
        f"<i>Har bir savol native poll (ovoz berish) ko'rinishida keladi.\n"
        f"Javobingizni bosing — Telegram to'g'ri/noto'g'riligini ko'rsatadi.\n"
        f"Natijalar avtomatik saqlanadi.</i>",
        reply_markup=builder.as_markup()
    )

    await state.update_data(intro_msg_id=msg.message_id)

    # Birinchi savolni yuborish
    await _send_poll_question(callback.bot, callback.message.chat.id, state)


async def _send_poll_question(bot, chat_id: int, state: FSMContext):
    """Keyingi savol uchun native quiz poll yuborish"""
    data = await state.get_data()
    qs   = data["questions"]
    idx  = data["current_index"]

    if idx >= len(qs):
        # Barcha savollar tugadi — yakunlash
        await _finish_poll_test(bot, chat_id, state, data)
        return

    q    = qs[idx]
    title = data["test_data"].get("title", "Test")

    # Variantlarni tayyorlash
    options = []
    for i, opt in enumerate(q.get("options", [])):
        opt_text = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
        # Telegram poll variant max 100 belgi
        if len(opt_text) > 95:
            opt_text = opt_text[:95] + "..."
        options.append(opt_text)

    # To'g'ri javob indeksini topish
    correct = q.get("correct", "")
    if isinstance(correct, int):
        correct_idx = correct
    else:
        c_str = str(correct).strip()
        # "A) Toshkent" → 0, "B) ..." → 1
        import re
        m = re.match(r"^([A-Za-z])", c_str)
        if m:
            letter = m.group(1).upper()
            correct_idx = ord(letter) - ord("A")
        else:
            correct_idx = 0

    correct_idx = max(0, min(correct_idx, len(options) - 1))

    # Izoh (explanation)
    expl = q.get("explanation", "")
    if expl in ("Izoh kiritilmagan.", "Izoh yo'q", "Izoh kiritilmagan", ""):
        expl = None
    if expl and len(expl) > 195:
        expl = expl[:195] + "..."

    # Savol matni
    q_text = q.get("question", "Savol")
    # Telegram poll question max 300 belgi
    header = f"[{idx+1}/{len(qs)}] "
    if len(header + q_text) > 295:
        q_text = q_text[:295 - len(header)] + "..."
    poll_question = header + q_text

    try:
        poll_msg = await bot.send_poll(
            chat_id=chat_id,
            question=poll_question,
            options=options,
            type="quiz",
            correct_option_id=correct_idx,
            explanation=expl,
            explanation_parse_mode="HTML",
            is_anonymous=False,
            open_period=None,
        )

        # Poll message id larini saqlash
        poll_ids = data.get("poll_msg_ids", [])
        poll_ids.append(poll_msg.message_id)

        # poll_id → savol indeksi bog'lash (PollAnswer uchun)
        poll_map = data.get("poll_map", {})
        poll_map[poll_msg.poll.id] = idx

        await state.update_data(
            poll_msg_ids=poll_ids,
            poll_map=poll_map,
            current_poll_id=poll_msg.poll.id
        )

    except Exception as e:
        log.error(f"Poll yuborishda xatolik: {e}")
        await bot.send_message(
            chat_id,
            f"⚠️ {idx+1}-savolni poll ko'rinishida yuborib bo'lmadi.\n"
            f"Sabab: Variant matni juda uzun yoki boshqa xatolik.\n"
            f"Keyingi savolga o'tilmoqda..."
        )
        # Bu savolni o'tkazib yuboramiz
        await state.update_data(current_index=idx + 1)
        fresh = await state.get_data()
        await _send_poll_question(bot, chat_id, state)


# ═══════════════════════════════════════════════════════════
# 2. POLL JAVOBI QABUL QILISH
# ═══════════════════════════════════════════════════════════

@router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer, state: FSMContext):
    """Foydalanuvchi poll ga javob berganda"""
    if await state.get_state() != PollTest.active.state:
        return

    data     = await state.get_data()
    poll_map = data.get("poll_map", {})
    poll_id  = poll_answer.poll_id

    if poll_id not in poll_map:
        return

    q_idx = poll_map[poll_id]

    # Foydalanuvchi tanlagan variant indeksi
    if not poll_answer.option_ids:
        return
    chosen_idx = poll_answer.option_ids[0]
    chosen_letter = LETTERS[chosen_idx] if chosen_idx < len(LETTERS) else str(chosen_idx)

    # Javobni saqlash
    answers = data.get("user_answers", {})
    answers[str(q_idx)] = chosen_letter
    idx = data.get("current_index", 0)

    # Keyingi savolga o'tish
    new_idx = idx + 1
    await state.update_data(user_answers=answers, current_index=new_idx)

    # Keyingi savol yoki yakunlash
    fresh_data = await state.get_data()
    qs = fresh_data.get("questions", [])

    if new_idx < len(qs):
        bot = poll_answer.bot if hasattr(poll_answer, "bot") else None
        chat_id = data.get("chat_id")
        if bot and chat_id:
            await _send_poll_question(bot, chat_id, state)
    else:
        # Barcha savollarga javob berildi
        bot = poll_answer.bot if hasattr(poll_answer, "bot") else None
        chat_id = data.get("chat_id")
        if bot and chat_id:
            await _finish_poll_test(bot, chat_id, state, fresh_data)


# ═══════════════════════════════════════════════════════════
# 3. POLL TESTNI TO'XTATISH
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "cancel_poll", PollTest.active)
async def cancel_poll_test(callback: CallbackQuery, state: FSMContext):
    """Poll testni bekor qilish"""
    data = await state.get_data()
    await state.clear()
    await callback.answer("❌ Test to'xtatildi")

    # Poll xabarlarini yopishga urinish
    for msg_id in data.get("poll_msg_ids", []):
        try:
            await callback.bot.stop_poll(callback.message.chat.id, msg_id)
        except Exception:
            pass

    # Intro xabarni o'chirish
    try:
        intro_id = data.get("intro_msg_id")
        if intro_id:
            await callback.bot.delete_message(callback.message.chat.id, intro_id)
    except Exception:
        pass

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.bot.send_message(
        callback.message.chat.id,
        "<b>❌ POLL TEST TO'XTATILDI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Natijalar saqlanmadi.",
        reply_markup=main_reply_keyboard(callback.from_user.id)
    )


# ═══════════════════════════════════════════════════════════
# 4. POLL TESTNI YAKUNLASH VA NATIJA
# ═══════════════════════════════════════════════════════════

async def _finish_poll_test(bot, chat_id: int, state: FSMContext, data: dict):
    """Poll test yakunlanganda natijani hisoblash va saqlash"""
    test       = data.get("test_data", {})
    qs         = data.get("questions", [])
    u_answers  = data.get("user_answers", {})
    start_time = data.get("start_time", time.time())
    elapsed    = int(time.time() - start_time)

    # Ball hisoblash
    scored = calculate_score(qs, u_answers)
    scored["time_spent"]    = elapsed
    scored["passing_score"] = test.get("passing_score", 60)
    scored["mode"]          = "poll"

    # Firebase ga saqlash
    # chat_id = user_id (private chatda)
    result_id = save_result(chat_id, test.get("test_id"), scored)

    # Natija xabari
    pct = scored.get("percentage", 0)
    passed = pct >= test.get("passing_score", 60)

    text = format_result(scored, test)
    await state.clear()

    await bot.send_message(
        chat_id,
        text,
        reply_markup=result_keyboard(test.get("test_id"), result_id)
    )

"""
📊 POLL TEST HANDLER — Telegram Native Quiz Poll rejimi
Poll vaqti sozlamasi (poll_time field dan olinadi)
"""
import time
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, PollAnswer
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


@router.callback_query(F.data.startswith("start_poll_"))
async def start_poll_test(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    tid  = callback.data[11:]
    test = get_test(tid)

    if not test:
        return await callback.message.answer("❌ Test topilmadi.")

    qs = test.get("questions", [])
    if not qs:
        return await callback.message.answer("❌ Bu testda savollar yo'q.")

    poll_qs = [q for q in qs if q.get("type", "multiple_choice") in ("multiple_choice", "true_false")]
    if not poll_qs:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="▶️ Inline test", callback_data=f"start_test_{tid}"))
        return await callback.message.answer(
            "⚠️ Bu testda faqat matnli savollar bor.\n"
            "Poll test faqat A/B/C/D va Ha/Yo'q savollarni qo'llab-quvvatlaydi.",
            reply_markup=builder.as_markup()
        )

    poll_time = test.get("poll_time", 30)  # soniya, 0 = cheksiz

    await state.set_state(PollTest.active)
    await state.set_data({
        "test_id":       tid,
        "test_data":     test,
        "questions":     poll_qs,
        "current_index": 0,
        "user_answers":  {},
        "poll_msg_ids":  [],
        "poll_map":      {},
        "chat_id":       callback.message.chat.id,
        "start_time":    time.time(),
        "poll_time":     poll_time,
    })

    try:
        await callback.message.delete()
    except Exception:
        pass

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏹ Testni to'xtatish", callback_data="cancel_poll"))
    pt_txt = f"{poll_time} son/savol" if poll_time > 0 else "Vaqtsiz"

    await callback.bot.send_message(
        callback.message.chat.id,
        f"<b>📊 POLL TEST BOSHLANDI!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>{test.get('title')}</b>\n"
        f"📋 Savollar: <b>{len(poll_qs)} ta</b>\n"
        f"⏱ Vaqt: <b>{pt_txt}</b>\n\n"
        f"<i>Har savol native poll ko'rinishida keladi.\n"
        f"Javobingizni bosing — Telegram to'g'ri/noto'g'riligini ko'rsatadi.\n"
        f"Natijalar avtomatik saqlanadi.</i>",
        reply_markup=builder.as_markup()
    )
    await _send_poll_question(callback.bot, callback.message.chat.id, state)


async def _send_poll_question(bot, chat_id: int, state: FSMContext):
    data = await state.get_data()
    qs   = data["questions"]
    idx  = data["current_index"]

    if idx >= len(qs):
        await _finish_poll_test(bot, chat_id, state, data)
        return

    q         = qs[idx]
    poll_time = data.get("poll_time", 30)

    options = []
    for opt in q.get("options", []):
        ot = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
        options.append(ot[:95] + "..." if len(ot) > 95 else ot)

    import re as _re
    correct = q.get("correct", "")
    if isinstance(correct, int):
        correct_idx = correct
    else:
        m = _re.match(r"^([A-Za-z])", str(correct).strip())
        correct_idx = (ord(m.group(1).upper()) - ord("A")) if m else 0
    correct_idx = max(0, min(correct_idx, len(options) - 1))

    expl = q.get("explanation", "")
    if expl in ("Izoh kiritilmagan.", "Izoh yo'q", "Izoh kiritilmagan", ""):
        expl = None
    if expl and len(expl) > 195:
        expl = expl[:195] + "..."

    q_text = q.get("question", "Savol")
    # Savol matnidan boshidagi raqamni olib tashlaymiz (parser qoldirgan bo'lsa)
    q_text = re.sub(r"^\d+[\.\)]\s*", "", q_text.strip())
    header = f"[{idx+1}/{len(qs)}] "
    if len(header + q_text) > 295:
        q_text = q_text[:295 - len(header)] + "..."

    try:
        poll_msg = await bot.send_poll(
            chat_id        = chat_id,
            question       = header + q_text,
            options        = options,
            type           = "quiz",
            correct_option_id = correct_idx,
            explanation    = expl,
            is_anonymous   = False,
            open_period    = poll_time if poll_time > 0 else None,
        )
        poll_ids = data.get("poll_msg_ids", [])
        poll_ids.append(poll_msg.message_id)
        poll_map = data.get("poll_map", {})
        poll_map[poll_msg.poll.id] = idx
        await state.update_data(poll_msg_ids=poll_ids, poll_map=poll_map,
                                current_poll_id=poll_msg.poll.id)
    except Exception as e:
        log.error(f"Poll yuborishda xatolik: {e}")
        await state.update_data(current_index=idx + 1)
        await _send_poll_question(bot, chat_id, state)


@router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer, state: FSMContext):
    if await state.get_state() != PollTest.active.state:
        return

    data     = await state.get_data()
    poll_map = data.get("poll_map", {})
    poll_id  = poll_answer.poll_id

    if poll_id not in poll_map:
        return

    q_idx = poll_map[poll_id]
    if not poll_answer.option_ids:
        return

    chosen_idx    = poll_answer.option_ids[0]
    chosen_letter = LETTERS[chosen_idx] if chosen_idx < len(LETTERS) else str(chosen_idx)

    answers = data.get("user_answers", {})
    answers[str(q_idx)] = chosen_letter
    new_idx = data.get("current_index", 0) + 1
    await state.update_data(user_answers=answers, current_index=new_idx)

    fresh = await state.get_data()
    qs    = fresh.get("questions", [])
    chat_id = data.get("chat_id")
    bot   = poll_answer.bot if hasattr(poll_answer, "bot") else None

    if bot and chat_id:
        if new_idx < len(qs):
            await _send_poll_question(bot, chat_id, state)
        else:
            await _finish_poll_test(bot, chat_id, state, fresh)


@router.callback_query(F.data == "cancel_poll", PollTest.active)
async def cancel_poll_test(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await callback.answer("❌ Test to'xtatildi")
    for msg_id in data.get("poll_msg_ids", []):
        try:
            await callback.bot.stop_poll(callback.message.chat.id, msg_id)
        except Exception:
            pass
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.bot.send_message(
        callback.message.chat.id,
        "<b>❌ POLL TEST TO'XTATILDI</b>\nNatijalar saqlanmadi.",
        reply_markup=main_reply_keyboard(callback.from_user.id)
    )


async def _finish_poll_test(bot, chat_id: int, state: FSMContext, data: dict):
    test      = data.get("test_data", {})
    qs        = data.get("questions", [])
    u_answers = data.get("user_answers", {})
    elapsed   = int(time.time() - data.get("start_time", time.time()))

    scored = calculate_score(qs, u_answers)
    scored["time_spent"]    = elapsed
    scored["passing_score"] = test.get("passing_score", 60)
    scored["mode"]          = "poll"

    result_id = save_result(chat_id, test.get("test_id"), scored)
    text = format_result(scored, test)
    await state.clear()
    await bot.send_message(chat_id, text,
                           reply_markup=result_keyboard(test.get("test_id"), result_id))

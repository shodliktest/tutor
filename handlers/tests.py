"""
📚 TEST YECHISH — Inline rejim + WebApp yo'naltiruvchi
Xavfsizlik: Bloklangan foydalanuvchi tekshiriladi
"""
import time, asyncio, logging, re
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from firebase.db import get_test, get_public_tests, save_result, get_result_by_id, get_user
from utils.states import TestSolving
from utils.scoring import calculate_score, format_result
from keyboards.keyboards import (
    main_reply_keyboard, result_keyboard, answer_keyboard,
    feedback_keyboard, test_webapp_keyboard, history_keyboard
)

log = logging.getLogger(__name__)
router = Router()
LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]


# ── Xavfsizlik tekshiruvi ─────────────────────────────────

async def _check_blocked(uid: int) -> bool:
    user = get_user(uid)
    return user.get("is_blocked", False) if user else False


# ═══════════════════════════════════════════════════════════
# 1. KATALOG
# ═══════════════════════════════════════════════════════════

async def send_categories_menu(event):
    tests = get_public_tests()
    text  = (
        "<b>📚 TESTLAR BO'LIMI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Test kodini yuboring yoki fanni tanlang:</i>\n\n"
    )
    builder = InlineKeyboardBuilder()
    if not tests:
        text += "📭 Hozircha ommaviy testlar mavjud emas."
    else:
        cats = {}
        for t in tests:
            c = t.get("category", "Boshqa")
            cats[c] = cats.get(c, 0) + 1
        for cat, cnt in cats.items():
            builder.row(InlineKeyboardButton(
                text=f"📁 {cat} ({cnt})",
                callback_data=f"cat_{cat[:30]}"
            ))

    if isinstance(event, Message):
        await event.answer(text, reply_markup=builder.as_markup())
    else:
        try:
            await event.message.edit_text(text, reply_markup=builder.as_markup())
        except TelegramBadRequest:
            await event.message.answer(text, reply_markup=builder.as_markup())


@router.message(StateFilter(None), F.text == "📚 Testlar")
async def tests_menu(message: Message, state: FSMContext):
    if await _check_blocked(message.from_user.id):
        return await message.answer("🚫 Siz bloklangansiz.")
    await state.clear()
    await send_categories_menu(message)


class _IsTestCode:
    def __call__(self, msg: Message) -> bool:
        t = (msg.text or "").strip()
        return (bool(t) and "/" not in t and "\n" not in t and " " not in t
                and len(t) in range(6, 21))

_test_code_filter = _IsTestCode()


@router.message(StateFilter(None), F.text, _test_code_filter)
async def direct_code_handler(message: Message):
    tid  = (message.text or "").strip()
    test = get_test(tid)
    if not test:
        return
    from keyboards.keyboards import test_info_keyboard
    qs = test.get("questions", [])
    diff_map = {"easy": "🟢 Oson", "medium": "🟡 O'rtacha",
                "hard": "🔴 Qiyin", "expert": "⚡ Ekspert"}
    diff = diff_map.get(test.get("difficulty", ""), "")
    await message.answer(
        f"<b>🔍 TEST TOPILDI!</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>{test.get('title')}</b>\n"
        f"📁 Fan: {test.get('category', '')}\n"
        f"📋 Savollar: <b>{len(qs)} ta</b>\n"
        f"📊 Qiyinlik: <b>{diff}</b>\n"
        f"🎯 O'tish foizi: <b>{test.get('passing_score', 60)}%</b>",
        reply_markup=test_info_keyboard(tid)
    )


@router.callback_query(F.data.startswith("cat_"))
async def show_category(callback: CallbackQuery):
    await callback.answer()
    cat   = callback.data[4:]
    tests = [t for t in get_public_tests() if str(t.get("category", "")).startswith(cat)]
    if not tests:
        return await callback.message.edit_text("❌ Bu fanda testlar topilmadi.")

    builder = InlineKeyboardBuilder()
    for t in tests:
        builder.row(InlineKeyboardButton(
            text=f"📝 {t.get('title', 'Nomsiz')} ({t.get('solve_count', 0)} marta)",
            callback_data=f"view_test_{t.get('test_id')}"
        ))
    builder.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_cats"))
    try:
        await callback.message.edit_text(
            f"<b>📁 {cat.upper()}</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\nQaysi testni ishlashni xohlaysiz?",
            reply_markup=builder.as_markup()
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data == "back_to_cats")
async def back_to_cats(callback: CallbackQuery):
    await callback.answer()
    await send_categories_menu(callback)


@router.callback_query(F.data.startswith("view_test_"))
async def view_test(callback: CallbackQuery):
    await callback.answer()
    tid  = callback.data[10:]
    test = get_test(tid)
    if not test:
        return await callback.message.answer("❌ Test topilmadi.")
    qs = test.get("questions", [])
    diff_map = {"easy": "🟢 Oson", "medium": "🟡 O'rtacha",
                "hard": "🔴 Qiyin", "expert": "⚡ Ekspert"}
    diff   = diff_map.get(test.get("difficulty", ""), "")
    vis_map = {"public": "🌍 Ommaviy", "link": "🔗 Ssilka", "private": "🔒 Shaxsiy"}
    vis    = vis_map.get(test.get("visibility", ""), "")
    pt     = test.get("poll_time", 30)
    pt_txt = f"{pt} son/savol" if pt > 0 else "Vaqtsiz"

    text = (
        f"<b>📋 TEST MA'LUMOTLARI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>{test.get('title')}</b>\n"
        f"📁 Fan: {test.get('category', '')}\n"
        f"📊 Qiyinlik: {diff}\n"
        f"📋 Savollar: <b>{len(qs)} ta</b>\n"
        f"⏱ Vaqt limiti: <b>{test.get('time_limit', 0) or 'Cheksiz'} daqiqa</b>\n"
        f"🎯 O'tish foizi: <b>{test.get('passing_score', 60)}%</b>\n"
        f"🔄 Ishlangan: <b>{test.get('solve_count', 0)} marta</b>\n"
        f"🔒 Ko'rinish: {vis}\n"
        f"⏱ Poll vaqti: {pt_txt}\n\n"
        f"<i>Qaysi rejimda ishlashni tanlang:</i>\n"
        f"▶️ <b>Inline</b> — har savoldan keyin to'g'ri/noto'g'ri ko'rsatadi\n"
        f"📊 <b>Poll</b> — native quiz poll (@QuizBot uslubida)\n"
        f"🌐 <b>Web</b> — brauzer oynasida"
    )
    from keyboards.keyboards import test_info_keyboard
    try:
        await callback.message.edit_text(text, reply_markup=test_info_keyboard(tid))
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=test_info_keyboard(tid))


# ═══════════════════════════════════════════════════════════
# 2. WEB TEST BOSHLASH
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("start_web_"))
async def start_web_test(callback: CallbackQuery):
    """WebApp orqali test yechishga yo'naltirish."""
    await callback.answer()
    tid  = callback.data[10:]
    test = get_test(tid)
    if not test:
        return await callback.message.answer("❌ Test topilmadi.")

    uid  = callback.from_user.id
    text = (
        f"<b>🌐 WEB TEST</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>{test.get('title')}</b>\n"
        f"📋 {len(test.get('questions', []))} ta savol\n\n"
        f"Quyidagi tugmani bosing — test brauzer oynasida ochiladi:"
    )
    try:
        await callback.message.edit_text(text, reply_markup=test_webapp_keyboard(tid, uid))
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=test_webapp_keyboard(tid, uid))


# ═══════════════════════════════════════════════════════════
# 3. INLINE TEST BOSHLASH
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("start_test_"))
async def start_inline_test(callback: CallbackQuery, state: FSMContext):
    if await _check_blocked(callback.from_user.id):
        return await callback.answer("🚫 Siz bloklangansiz.", show_alert=True)
    await callback.answer()
    tid  = callback.data[11:]
    test = get_test(tid)
    if not test:
        return await callback.message.answer("❌ Test topilmadi.")
    qs = test.get("questions", [])
    if not qs:
        return await callback.message.answer("❌ Bu testda savollar yo'q.")

    await state.set_data({
        "test_data":     test,
        "questions":     qs,
        "current_index": 0,
        "user_answers":  {},
        "start_time":    time.time(),
    })
    await state.set_state(TestSolving.answering)
    await _send_question(callback, state, edit=True)


async def _send_question(event, state: FSMContext, edit: bool = False):
    data    = await state.get_data()
    qs      = data["questions"]
    idx     = data["current_index"]
    q       = qs[idx]
    title   = data["test_data"].get("title", "Test")
    t_limit = data["test_data"].get("time_limit", 0)
    start   = data.get("start_time", time.time())

    time_txt = ""
    if t_limit > 0:
        remain = max(0, t_limit * 60 - int(time.time() - start))
        m, s   = divmod(remain, 60)
        time_txt = f" | ⏱ {m:02d}:{s:02d}"
        if remain == 0:
            await _finish_test(event, state, data)
            return

    header = f"<b>📝 {title} | {idx+1}/{len(qs)}{time_txt}</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    q_text = re.sub(r"^\d+[\.\)]\s*", "", q.get("question", q.get("text", "Savol matni yo'q")).strip())
    body   = f"<b>{q_text}</b>\n\n"
    letters = []
    for i, opt in enumerate(q.get("options", [])):
        letter = LETTERS[i] if i < len(LETTERS) else str(i+1)
        ot     = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
        body  += f"▫️ <b>{letter})</b> <i>{ot}</i>\n"
        letters.append(letter)

    kb   = answer_keyboard(letters)
    full = header + body
    if edit and isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(full, reply_markup=kb)
            return
        except TelegramBadRequest:
            pass
    target = event.message if isinstance(event, CallbackQuery) else event
    await target.answer(full, reply_markup=kb)


# ═══════════════════════════════════════════════════════════
# 4. JAVOB QAYTA ISHLASH — 5 soniya feedback
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("ans_"), TestSolving.answering)
async def process_answer(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if await state.get_state() != TestSolving.answering.state:
        return

    letter = callback.data[4:]
    data   = await state.get_data()
    idx    = data["current_index"]
    qs     = data["questions"]
    q      = qs[idx]
    title  = data["test_data"].get("title", "Test")

    answers = data.get("user_answers", {})
    answers[str(idx)] = letter
    await state.update_data(user_answers=answers)

    correct = q.get("correct", "")
    if isinstance(correct, int):
        c_letter = LETTERS[correct] if correct < len(LETTERS) else "?"
    else:
        m = re.match(r"^([A-Za-z])", str(correct).strip())
        c_letter = m.group(1).upper() if m else "?"

    is_correct = letter.upper() == c_letter.upper()
    header = f"<b>📝 {title} | {idx+1}/{len(qs)}</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    q_text = re.sub(r"^\d+[\.\)]\s*", "", q.get("question", q.get("text", "Savol")).strip())
    body   = f"<b>{q_text}</b>\n\n"

    for i, opt in enumerate(q.get("options", [])):
        ltr = LETTERS[i] if i < len(LETTERS) else str(i+1)
        ot  = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
        if ltr.upper() == c_letter.upper():
            body += f"✅ <b>{ltr})</b> <i>{ot}</i>\n"
        elif ltr.upper() == letter.upper() and not is_correct:
            body += f"❌ <b>{ltr})</b> <i>{ot}</i>\n"
        else:
            body += f"▫️ <b>{ltr})</b> <i>{ot}</i>\n"

    body += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
    body += "🎯 <b>Natija:</b> ✅ TO'G'RI!\n" if is_correct else "🎯 <b>Natija:</b> ❌ XATO\n"
    expl  = q.get("explanation", "")
    if expl and expl not in ("Izoh kiritilmagan.", "Izoh yo'q", "Izoh kiritilmagan", ""):
        body += f"💡 <b>Izoh:</b> <i>{expl}</i>\n"

    try:
        await callback.message.edit_text(header + body, reply_markup=feedback_keyboard())
    except TelegramBadRequest:
        pass

    for _ in range(5):
        await asyncio.sleep(1)
        if await state.get_state() != TestSolving.answering.state:
            return

    fresh = await state.get_data()
    if idx < len(qs) - 1:
        await state.update_data(current_index=idx + 1)
        await _send_question(callback, state, edit=True)
    else:
        await _finish_test(callback, state, fresh)


@router.callback_query(F.data == "wait_btn")
async def wait_btn(callback: CallbackQuery):
    await callback.answer("⏳ Biroz kuting...", show_alert=False)


@router.callback_query(F.data == "cancel_test", TestSolving.answering)
async def cancel_test(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("❌ Test to'xtatildi")
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.bot.send_message(
        callback.message.chat.id,
        "<b>❌ TEST TO'XTATILDI</b>\n━━━━━━━━━━━━━━━━━━━━━━\nNatijalar saqlanmadi.",
        reply_markup=main_reply_keyboard(callback.from_user.id)
    )


# ═══════════════════════════════════════════════════════════
# 5. TEST YAKUNLASH
# ═══════════════════════════════════════════════════════════

async def _finish_test(event, state: FSMContext, data: dict):
    test      = data.get("test_data", {})
    qs        = data.get("questions", [])
    u_answers = data.get("user_answers", {})
    elapsed   = int(time.time() - data.get("start_time", time.time()))

    scored = calculate_score(qs, u_answers)
    scored["time_spent"]    = elapsed
    scored["passing_score"] = test.get("passing_score", 60)
    scored["mode"]          = "inline"

    uid     = event.from_user.id
    chat_id = (event.message if isinstance(event, CallbackQuery) else event).chat.id
    rid     = save_result(uid, test.get("test_id"), scored)
    text    = format_result(scored, test)
    await state.clear()

    try:
        if isinstance(event, CallbackQuery):
            await event.message.delete()
        else:
            await event.delete()
    except Exception:
        pass

    # user_id uzatamiz — WebApp tugmalari ko'rinadi
    await event.bot.send_message(
        chat_id, text,
        reply_markup=result_keyboard(test.get("test_id"), rid, uid)
    )


# ═══════════════════════════════════════════════════════════
# 6. NATIJALARIM (WebApp tarixi tugmasi)
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "my_results_webapp")
async def my_results_webapp(callback: CallbackQuery):
    """Foydalanuvchi 📊 Natijalarim → WebApp tarixi."""
    await callback.answer()
    uid = callback.from_user.id
    await callback.message.answer(
        "📜 <b>NATIJALARIM (Web oyna)</b>\n\nQuyidagi tugmani bosing:",
        reply_markup=history_keyboard(uid)
    )


# ═══════════════════════════════════════════════════════════
# 7. WEB TEST NATIJASI — GitHub Pages dan kelgan ma'lumot
# ═══════════════════════════════════════════════════════════

@router.message(F.web_app_data)
async def web_app_data_handler(message: Message):
    """
    GitHub Pages test.html test tugatganda WebApp.sendData() yuboradi.
    Bot shu xabarni qabul qilib foydalanuvchiga natija + tugmalar yuboradi.
    """
    import json
    try:
        data = json.loads(message.web_app_data.data)
    except Exception:
        return

    if data.get("type") != "test_result":
        return

    score     = data.get("score", 0)
    passed    = data.get("passed", False)
    result_id = data.get("result_id", "")
    test_id   = data.get("test_id", "")
    uid       = message.from_user.id

    emoji = "✅" if passed else "❌"
    text  = (
        f"<b>{emoji} WEB TEST YAKUNLANDI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 Natija: <b>{score}%</b>\n"
        f"{'🎉 Tabriklaymiz! Siz o\'tdingiz!' if passed else '💪 Yana urinib ko\'ring!'}"
    )
    await message.answer(
        text,
        reply_markup=result_keyboard(test_id, result_id, uid)
    )

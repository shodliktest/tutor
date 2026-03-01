"""
📚 TEST YECHISH HANDLER — Inline tugmalar rejimi
✅ Lambda o'rniga Filter class (Aiogram 3)
✅ asyncio.sleep race condition hal qilindi
✅ delete + bot.send_message pattern
✅ Cancel safe (har sekund state tekshirish)
"""
import time
import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from firebase.db import get_test, get_public_tests, save_result, get_result_by_id
from utils.states import TestSolving
from utils.scoring import calculate_score, format_result
from keyboards.keyboards import (
    main_reply_keyboard, result_keyboard, answer_keyboard, feedback_keyboard
)

log = logging.getLogger(__name__)
router = Router()

LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]


# ═══════════════════════════════════════════════════════════
# 1. TESTLAR KATALOGI — Fan va testlar ro'yxati
# ═══════════════════════════════════════════════════════════

async def send_categories_menu(event):
    """Ommaviy testlardan kategoriyalar menyusini yuborish"""
    tests = get_public_tests()

    text = (
        "<b>📚 TESTLAR BO'LIMI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Test kodini to'g'ridan-to'g'ri yozib yuboring\n"
        "yoki pastdagi fanlardan birini tanlang:</i>\n\n"
    )

    builder = InlineKeyboardBuilder()
    if not tests:
        text += "📭 Hozircha ommaviy testlar mavjud emas."
    else:
        cats: dict = {}
        for t in tests:
            c = t.get("category", "Boshqa")
            cats[c] = cats.get(c, 0) + 1
        for cat, cnt in cats.items():
            cb = f"cat_{cat}"[:40]
            builder.row(InlineKeyboardButton(text=f"📁 {cat} ({cnt})", callback_data=cb))

    if isinstance(event, Message):
        await event.answer(text, reply_markup=builder.as_markup())
    else:
        try:
            await event.message.edit_text(text, reply_markup=builder.as_markup())
        except Exception:
            await event.message.answer(text, reply_markup=builder.as_markup())


@router.message(StateFilter(None), F.text == "📚 Testlar")
async def tests_menu(message: Message, state: FSMContext):
    await state.clear()
    await send_categories_menu(message)


# ── Test kodi filteri (Aiogram 3 — lambda o'rniga class) ──

class _IsTestCode:
    """6 ta yoki 8 ta belgilik, bo'sh joy/slash/enter yo'q"""
    def __call__(self, msg: Message) -> bool:
        t = (msg.text or "").strip()
        return (
            bool(t)
            and "/" not in t
            and "\n" not in t
            and " " not in t
            and (len(t) == 6 or len(t) == 8 or len(t) >= 20)
        )


_test_code_filter = _IsTestCode()


@router.message(StateFilter(None), F.text, _test_code_filter)
async def direct_code_handler(message: Message):
    """Test kodi yozilsa — testni topib ko'rsatish"""
    tid  = (message.text or "").strip()
    test = get_test(tid)
    if not test:
        return  # Noto'g'ri kod — jimgina o'tkazib yuboramiz

    from keyboards.keyboards import test_info_keyboard
    qs    = test.get("questions", [])
    diff_map = {"easy": "🟢 Oson", "medium": "🟡 O'rtacha",
                "hard": "🔴 Qiyin", "expert": "⚡ Ekspert"}
    diff = diff_map.get(test.get("difficulty", ""), "")

    text = (
        f"<b>🔍 TEST TOPILDI!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>{test.get('title')}</b>\n"
        f"📁 Fan: {test.get('category', '')}\n"
        f"📋 Savollar: <b>{len(qs)} ta</b>\n"
        f"📊 Qiyinlik: <b>{diff}</b>\n"
        f"🎯 O'tish foizi: <b>{test.get('passing_score', 60)}%</b>"
    )
    await message.answer(text, reply_markup=test_info_keyboard(tid))


@router.callback_query(F.data.startswith("cat_"))
async def show_category(callback: CallbackQuery):
    await callback.answer()
    cat = callback.data[4:]

    tests = [t for t in get_public_tests() if str(t.get("category", "")).startswith(cat)]
    if not tests:
        await callback.message.edit_text("❌ Bu fanda testlar topilmadi.")
        return

    text = (
        f"<b>📁 {cat.upper()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Qaysi testni ishlashni xohlaysiz?"
    )
    builder = InlineKeyboardBuilder()
    for t in tests:
        builder.row(InlineKeyboardButton(
            text=f"📝 {t.get('title', 'Nomsiz')}  ({t.get('solve_count', 0)} marta)",
            callback_data=f"view_test_{t.get('test_id')}"
        ))
    builder.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_cats"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "back_to_cats")
async def back_to_cats(callback: CallbackQuery):
    await callback.answer()
    await send_categories_menu(callback)


@router.callback_query(F.data.startswith("view_test_"))
async def view_test(callback: CallbackQuery):
    """Test haqida to'liq ma'lumot — Inline yoki Poll tanlash"""
    await callback.answer()
    tid  = callback.data[10:]
    test = get_test(tid)
    if not test:
        await callback.message.answer("❌ Test topilmadi.")
        return

    qs = test.get("questions", [])
    diff_map = {"easy": "🟢 Oson", "medium": "🟡 O'rtacha",
                "hard": "🔴 Qiyin", "expert": "⚡ Ekspert"}
    diff = diff_map.get(test.get("difficulty", ""), "")
    vis_map = {"public": "🌍 Ommaviy", "link": "🔗 Ssilka", "private": "🔒 Shaxsiy"}
    vis = vis_map.get(test.get("visibility", ""), "")

    text = (
        f"<b>📋 TEST MA'LUMOTLARI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>{test.get('title')}</b>\n"
        f"📁 Fan: {test.get('category', '')}\n"
        f"📊 Qiyinlik: {diff}\n"
        f"📋 Savollar: <b>{len(qs)} ta</b>\n"
        f"⏱ Vaqt: <b>{test.get('time_limit', 0) or 'Cheksiz'} daqiqa</b>\n"
        f"🎯 O'tish foizi: <b>{test.get('passing_score', 60)}%</b>\n"
        f"🔄 Ishlangan: <b>{test.get('solve_count', 0)} marta</b>\n"
        f"🔒 Ko'rinish: {vis}\n\n"
        f"<i>Qaysi rejimda ishlashni tanlang:</i>\n"
        f"▶️ <b>Inline</b> — Har savoldan keyin to'g'ri/noto'g'ri ko'rsatiladi\n"
        f"📊 <b>Poll</b> — Quiz Bot uslubida native poll orqali"
    )
    from keyboards.keyboards import test_info_keyboard
    await callback.message.edit_text(text, reply_markup=test_info_keyboard(tid))


# ═══════════════════════════════════════════════════════════
# 2. INLINE TEST BOSHLASH
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("start_test_"))
async def start_inline_test(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    tid  = callback.data[11:]
    test = get_test(tid)

    if not test:
        await callback.message.answer("❌ Test topilmadi yoki o'chirilgan.")
        return

    qs = test.get("questions", [])
    if not qs:
        await callback.message.answer("❌ Bu testda savollar yo'q.")
        return

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
    """Savol xabarini yuborish yoki tahrirlash"""
    data       = await state.get_data()
    qs         = data["questions"]
    idx        = data["current_index"]
    test_title = data["test_data"].get("title", "Test")
    q          = qs[idx]
    t_limit    = data["test_data"].get("time_limit", 0)
    start_time = data.get("start_time", time.time())

    # Vaqt qoldiq
    time_txt = ""
    if t_limit > 0:
        remain = max(0, t_limit * 60 - int(time.time() - start_time))
        m, s   = divmod(remain, 60)
        time_txt = f" | ⏱ {m:02d}:{s:02d}"

        # Vaqt tugagan bo'lsa — avtomatik yakunlash
        if remain == 0:
            await _finish_test(event, state, data)
            return

    header = (
        f"<b>📝 {test_title} | {idx+1}/{len(qs)}{time_txt}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    q_text = q.get("question", q.get("text", "Savol matni yo'q"))
    body   = f"<b>{q_text}</b>\n\n"

    letters = []
    for i, opt in enumerate(q.get("options", [])):
        letter   = LETTERS[i] if i < len(LETTERS) else str(i + 1)
        opt_text = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
        body    += f"▫️ <b>{letter})</b> <i>{opt_text}</i>\n"
        letters.append(letter)

    kb        = answer_keyboard(letters)
    full_text = header + body

    if edit and isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(full_text, reply_markup=kb)
            return
        except Exception:
            pass

    target = event.message if isinstance(event, CallbackQuery) else event
    await target.answer(full_text, reply_markup=kb)


# ═══════════════════════════════════════════════════════════
# 3. JAVOB QAYTA ISHLASH — 5 sekund feedback
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

    # Javobni saqlash
    answers          = data.get("user_answers", {})
    answers[str(idx)] = letter
    await state.update_data(user_answers=answers)

    # To'g'ri javobni aniqlash
    correct = q.get("correct", "")
    if isinstance(correct, int):
        c_letter = LETTERS[correct] if correct < len(LETTERS) else "?"
    else:
        c_str    = str(correct).strip()
        c_letter = c_str[0].upper() if c_str else "?"

    is_correct = letter.upper() == c_letter.upper()

    # Feedback xabari
    header = (
        f"<b>📝 {title} | {idx+1}/{len(qs)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    q_text = q.get("question", q.get("text", "Savol"))
    body   = f"<b>{q_text}</b>\n\n"

    for i, opt in enumerate(q.get("options", [])):
        ltr  = LETTERS[i] if i < len(LETTERS) else str(i + 1)
        otxt = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
        if ltr.upper() == c_letter.upper():
            body += f"✅ <b>{ltr})</b> <i>{otxt}</i>\n"
        elif ltr.upper() == letter.upper() and not is_correct:
            body += f"❌ <b>{ltr})</b> <i>{otxt}</i>\n"
        else:
            body += f"▫️ <b>{ltr})</b> <i>{otxt}</i>\n"

    body += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
    body += "🎯 <b>Natija:</b> ✅ TO'G'RI!\n" if is_correct else "🎯 <b>Natija:</b> ❌ NOTO'G'RI\n"

    expl = q.get("explanation", "")
    if expl and expl not in ("Izoh kiritilmagan.", "Izoh yo'q", "Izoh kiritilmagan"):
        body += f"💡 <b>Izoh:</b> <i>{expl}</i>\n"

    await callback.message.edit_text(header + body, reply_markup=feedback_keyboard())

    # 5 sekund — har sekund cancel tekshirish
    for _ in range(5):
        await asyncio.sleep(1)
        if await state.get_state() != TestSolving.answering.state:
            return

    # Keyingi savol yoki yakunlash
    fresh = await state.get_data()
    if idx < len(qs) - 1:
        await state.update_data(current_index=idx + 1)
        await _send_question(callback, state, edit=True)
    else:
        await _finish_test(callback, state, fresh)


@router.callback_query(F.data == "wait_btn")
async def wait_btn(callback: CallbackQuery):
    await callback.answer("⏳ Biroz kuting...", show_alert=False)


# ═══════════════════════════════════════════════════════════
# 4. TESTNI TO'XTATISH
# ═══════════════════════════════════════════════════════════

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
        "<b>❌ TEST TO'XTATILDI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Natijalar saqlanmadi.",
        reply_markup=main_reply_keyboard(callback.from_user.id)
    )


# ═══════════════════════════════════════════════════════════
# 5. TEST YAKUNLASH VA NATIJA SAQLASH
# ═══════════════════════════════════════════════════════════

async def _finish_test(event, state: FSMContext, data: dict):
    """Testni yakunlash, natijani saqlash va ko'rsatish"""
    test       = data.get("test_data", {})
    qs         = data.get("questions", [])
    u_answers  = data.get("user_answers", {})
    start_time = data.get("start_time", time.time())
    elapsed    = int(time.time() - start_time)

    # Ball hisoblash
    scored = calculate_score(qs, u_answers)
    scored["time_spent"]     = elapsed
    scored["passing_score"]  = test.get("passing_score", 60)
    scored["mode"]           = "inline"

    uid = (event.from_user if isinstance(event, CallbackQuery) else event.from_user).id
    chat_id = (event.message if isinstance(event, CallbackQuery) else event).chat.id

    result_id = save_result(uid, test.get("test_id"), scored)

    text = format_result(scored, test)
    await state.clear()

    try:
        if isinstance(event, CallbackQuery):
            await event.message.delete()
        else:
            await event.delete()
    except Exception:
        pass

    await event.bot.send_message(
        chat_id, text,
        reply_markup=result_keyboard(test.get("test_id"), result_id)
    )


# ═══════════════════════════════════════════════════════════
# 6. BATAFSIL TAHLIL
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("analysis_"))
async def analysis(callback: CallbackQuery):
    await callback.answer("⏳ Tahlil yuklanmoqda...")
    rid = callback.data[9:]

    res = get_result_by_id(rid)
    if not res:
        await callback.message.answer("❌ Natija topilmadi.")
        return

    from firebase.db import get_test as _get_test
    test      = _get_test(res.get("test_id", ""))
    detailed  = res.get("detailed_results", [])
    questions = test.get("questions", []) if test else []

    if not detailed:
        await callback.message.answer("⚠️ Bu test uchun tahlil mavjud emas.")
        return

    title  = test.get("title", "Test").upper() if test else "TEST"
    chunks = []
    chunk  = f"<b>📝 {title} — BATAFSIL TAHLIL</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for d in detailed:
        i      = d.get("question_index", 0)
        is_c   = d.get("is_correct", False)
        u_ans  = d.get("user_answer", "Belgilanmagan")
        c_ans  = d.get("correct_answer", "Noma'lum")
        q_text = questions[i].get("question", "") if i < len(questions) else ""
        expl   = questions[i].get("explanation", "") if i < len(questions) else ""

        holat = "✅ TO'G'RI" if is_c else "❌ XATO"
        block = (
            f"<b>Savol {i+1}:</b> {q_text}\n"
            f"Holat: {holat}\n"
            f"👤 <b>Siz:</b> <i>{u_ans}</i>\n"
        )
        if not is_c:
            block += f"🎯 <b>To'g'ri:</b> <i>{c_ans}</i>\n"
        if expl and expl not in ("Izoh kiritilmagan.", "Izoh yo'q", "Izoh kiritilmagan"):
            block += f"💡 <b>Izoh:</b> <i>{expl}</i>\n"
        block += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

        if len(chunk) + len(block) > 4000:
            chunks.append(chunk)
            chunk = ""
        chunk += block

    if chunk:
        chunks.append(chunk)

    for ch in chunks:
        await callback.message.answer(ch, protect_content=True)

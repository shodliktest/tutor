"""
📚 TEST YECHISH VA TAHLIL HANDLER
✅ Lambda filter o'rniga MagicFilter
✅ asyncio.sleep race condition hal qilindi
✅ delete+answer xatosi tuzatildi
✅ cancel_test to'g'ri ishlaydi
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

from firebase.db import get_test, save_result, get_user, get_db, get_all_tests
from utils.states import TestSolving
from keyboards.keyboards import result_keyboard, main_reply_keyboard

logger = logging.getLogger(__name__)
router = Router()

LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]


# ==========================================================
# 1. TESTLAR KATALOGI
# ==========================================================
async def send_categories_menu(event):
    all_tests = get_all_tests()
    public_tests = [t for t in all_tests if t.get("visibility") == "public"]

    text = (
        "<b>📚 TESTLAR BO'LIMI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Test kodini (ID) to'g'ridan-to'g'ri yozib yuboring "
        "yoki pastdagi fanlardan birini tanlang:</i>\n\n"
    )

    builder = InlineKeyboardBuilder()
    if not public_tests:
        text += "Hozircha bazada ommaviy testlar mavjud emas."
    else:
        categories: dict[str, int] = {}
        for t in public_tests:
            cat = t.get("category", "Boshqa")
            categories[cat] = categories.get(cat, 0) + 1
        for cat, count in categories.items():
            cb_data = f"cat_{cat}"[:40]
            builder.row(InlineKeyboardButton(text=f"📁 {cat} ({count})", callback_data=cb_data))

    if isinstance(event, Message):
        await event.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await event.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.message(StateFilter(None), F.text == "📚 Testlar")
async def tests_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await send_categories_menu(message)


# ── Aiogram 3 da lambda ishlamaydi → Filter class ishlatiladi ──
class _IsTestCode(object):
    """6 xonali yoki 20+ belgilik, bo'sh joy/slash/enter yo'q"""
    def __call__(self, msg: Message) -> bool:
        t = (msg.text or "").strip()
        return (
            bool(t)
            and "/" not in t
            and "\n" not in t
            and " " not in t
            and (len(t) == 6 or len(t) >= 20)
        )

_test_code_filter = _IsTestCode()


@router.message(StateFilter(None), F.text, _test_code_filter)
async def direct_code_handler(message: Message, state: FSMContext):
    test_id = (message.text or "").strip()
    test = get_test(test_id)
    if not test:
        return  # Noto'g'ri kod — jimgina o'tkazib yuboramiz

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🚀 Testni boshlash",
        callback_data=f"start_test_{test.get('test_id')}"
    ))
    text = (
        f"<b>🔍 TEST TOPILDI!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏷 <b>Mavzu:</b> {test.get('title')}\n"
        f"📁 <b>Fan:</b> {test.get('category')}\n"
        f"📋 <b>Savollar:</b> {test.get('questionCount', len(test.get('questions', [])))} ta\n"
    )
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("cat_"))
async def show_tests_in_category(callback: CallbackQuery):
    await callback.answer()
    cat_name = callback.data[4:]

    all_tests = get_all_tests()
    cat_tests = [
        t for t in all_tests
        if t.get("visibility") == "public"
        and str(t.get("category", "")).startswith(cat_name)
    ]

    if not cat_tests:
        await callback.message.edit_text("❌ Bu fanda testlar topilmadi.")
        return

    text = (
        f"<b>📁 FAN: {cat_tests[0].get('category','Boshqa').upper()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Qaysi testni ishlashni xohlaysiz?"
    )
    builder = InlineKeyboardBuilder()
    for t in cat_tests:
        builder.row(InlineKeyboardButton(
            text=f"📝 {t.get('title','Nomsiz test')}",
            callback_data=f"start_test_{t.get('test_id')}"
        ))
    builder.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_categories"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "back_to_categories")
async def back_to_cat_handler(callback: CallbackQuery):
    await callback.answer()
    await send_categories_menu(callback)


# ==========================================================
# 2. TESTNI BOSHLASH VA SAVOL YUBORISH
# ==========================================================
@router.callback_query(F.data.startswith("start_test_"))
async def start_test_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    test_id = callback.data[11:]
    test = get_test(test_id)

    if not test:
        await callback.message.answer("❌ Test topilmadi yoki o'chirilgan.")
        return

    questions = test.get("questions", [])
    if not questions:
        await callback.message.answer("❌ Ushbu testda savollar yo'q.")
        return

    await state.set_data({
        "test_data":     test,
        "questions":     questions,
        "current_index": 0,
        "user_answers":  {},
        "start_time":    time.time(),
        "cancelled":     False,
    })
    await state.set_state(TestSolving.answering)
    await _send_question(callback, state, edit=True)


async def _send_question(event, state: FSMContext, edit: bool = False):
    data = await state.get_data()
    questions    = data["questions"]
    idx          = data["current_index"]
    test_title   = data["test_data"].get("title", "Nomsiz test")
    q            = questions[idx]
    time_limit   = data["test_data"].get("time_limit", 0)
    start_time   = data.get("start_time")

    time_text = ""
    if time_limit > 0 and start_time:
        remain = max(0, time_limit * 60 - int(time.time() - start_time))
        m, s   = divmod(remain, 60)
        time_text = f" | ⏱ {m:02d}:{s:02d}"

    header = (
        f"<b>📝 {test_title} | {idx+1}/{len(questions)}{time_text}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    q_text   = q.get("question", q.get("text", "Savol matni kiritilmagan"))
    body     = f"<b>{q_text}</b>\n\n"
    builder  = InlineKeyboardBuilder()

    for i, opt in enumerate(q.get("options", [])):
        letter   = LETTERS[i] if i < len(LETTERS) else str(i)
        opt_text = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
        body    += f"▫️ <b>{letter})</b> <i>{opt_text}</i>\n"
        builder.add(InlineKeyboardButton(text=letter, callback_data=f"ans_{letter}"))

    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ Testni to'xtatish", callback_data="cancel_test"))

    full_text = header + body
    kb = builder.as_markup()

    if edit and isinstance(event, CallbackQuery):
        await event.message.edit_text(full_text, reply_markup=kb, parse_mode="HTML")
    else:
        target = event.message if isinstance(event, CallbackQuery) else event
        await target.answer(full_text, reply_markup=kb, parse_mode="HTML")


# ==========================================================
# 3. JAVOB — 5 SEKUND KO'RSATISH → KEYINGI SAVOL
# ==========================================================
@router.callback_query(F.data.startswith("ans_"), TestSolving.answering)
async def process_button_answer(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    if await state.get_state() != TestSolving.answering.state:
        return

    answer     = callback.data[4:]
    data       = await state.get_data()
    idx        = data["current_index"]
    questions  = data["questions"]
    q          = questions[idx]
    test_title = data["test_data"].get("title", "Nomsiz test")

    # Javobni saqlash
    answers = data["user_answers"]
    answers[str(idx)] = answer
    await state.update_data(user_answers=answers)

    # To'g'ri javobni aniqlash
    c_ans   = q.get("correct", "")
    c_letter = str(c_ans).split(")")[0].strip() if isinstance(c_ans, str) and ")" in str(c_ans) else str(c_ans)
    if isinstance(c_ans, int):
        c_letter = LETTERS[c_ans] if c_ans < len(LETTERS) else "?"

    is_correct = answer.lower() == c_letter.lower()

    # Feedback ekrani
    header    = (
        f"<b>📝 {test_title} | {idx+1}/{len(questions)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    q_text    = q.get("question", q.get("text", "Savol matni kiritilmagan"))
    text_body = f"<b>{q_text}</b>\n\n"

    for i, opt in enumerate(q.get("options", [])):
        letter   = LETTERS[i] if i < len(LETTERS) else str(i)
        opt_text = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
        if letter.lower() == c_letter.lower():
            text_body += f"✅ <b>{letter})</b> <i>{opt_text}</i>\n"
        elif letter.lower() == answer.lower() and not is_correct:
            text_body += f"❌ <b>{letter})</b> <i>{opt_text}</i>\n"
        else:
            text_body += f"▫️ <b>{letter})</b> <i>{opt_text}</i>\n"

    text_body += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
    text_body += "🎯 <b>Natija:</b> ✅ TO'G'RI\n" if is_correct else "🎯 <b>Natija:</b> ❌ NOTO'G'RI\n"

    explanation = q.get("explanation", "")
    if explanation and explanation not in ("Izoh kiritilmagan", "Izoh kiritilmagan.", "Izoh yo'q"):
        text_body += f"💡 <b>Izoh:</b> <i>{explanation}</i>\n"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏳ Keyingi savolga o'tilmoqda...", callback_data="wait_btn"))
    builder.row(InlineKeyboardButton(text="❌ Testni to'xtatish", callback_data="cancel_test"))

    await callback.message.edit_text(
        header + text_body,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

    # 5 sekund — har sekund state tekshiriladi (cancel safe)
    for _ in range(5):
        await asyncio.sleep(1)
        if await state.get_state() != TestSolving.answering.state:
            return  # Cancel bosilgan — chiqib ketamiz

    # Keyingi savol yoki yakunlash
    fresh = await state.get_data()
    if idx < len(questions) - 1:
        await state.update_data(current_index=idx + 1)
        await _send_question(callback, state, edit=True)
    else:
        await _finish_test(callback.message, state, fresh)


@router.callback_query(F.data == "wait_btn")
async def wait_btn_handler(callback: CallbackQuery):
    await callback.answer("⏳ Biroz kuting...", show_alert=False)


# ==========================================================
# 4. TESTNI TO'XTATISH
# ==========================================================
@router.callback_query(F.data == "cancel_test", TestSolving.answering)
async def cancel_test_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("❌ Test to'xtatildi")
    try:
        await callback.message.delete()
    except Exception:
        pass

    # delete() dan keyin answer() ishlamaydi — bot.send_message kerak
    await callback.bot.send_message(
        callback.message.chat.id,
        "<b>❌ TEST TO'XTATILDI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Natijalar saqlanmadi.",
        reply_markup=main_reply_keyboard(callback.from_user.id),
        parse_mode="HTML"
    )


# ==========================================================
# 5. YAKUNLASH VA BAHOLASH
# ==========================================================
async def _finish_test(message: Message, state: FSMContext, data: dict):
    test       = data.get("test_data", {})
    questions  = data.get("questions", [])
    u_answers  = data.get("user_answers", {})
    start_time = data.get("start_time", time.time())

    correct_count    = 0
    detailed_results = []

    for i, q in enumerate(questions):
        u_ans  = u_answers.get(str(i), "Belgilanmagan")
        c_ans  = q.get("correct", "")

        if isinstance(c_ans, int):
            c_letter = LETTERS[c_ans] if c_ans < len(LETTERS) else "?"
            opts = q.get("options", [])
            c_full = f"{c_letter}) {opts[c_ans]}" if c_ans < len(opts) else c_letter
        else:
            c_letter = str(c_ans).split(")")[0].strip() if ")" in str(c_ans) else str(c_ans)
            c_full   = str(c_ans)

        is_correct = (str(u_ans).lower() == c_letter.lower()) and u_ans != "Belgilanmagan"
        if is_correct:
            correct_count += 1

        detailed_results.append({
            "question_index": i,
            "user_answer":    str(u_ans),
            "correct_answer": c_full,
            "is_correct":     is_correct,
        })

    total   = len(questions)
    score   = (correct_count / total * 100) if total else 0
    passed  = score >= test.get("passing_score", 60)
    elapsed = int(time.time() - start_time)
    m, s    = divmod(elapsed, 60)

    result_data = {
        "score":            score,
        "correct_count":    correct_count,
        "total_questions":  total,
        "passed":           passed,
        "time_spent":       elapsed,
        "detailed_results": detailed_results,
    }

    chat_id   = message.chat.id
    result_id = save_result(chat_id, test.get("test_id"), result_data)

    text = (
        f"<b>📊 YAKUNIY NATIJA</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>Mavzu:</b> {test.get('title','Nomsiz')}\n"
        f"📋 <b>Savollar:</b> {total} ta\n"
        f"✅ <b>To'g'ri:</b> {correct_count} ta\n"
        f"🎯 <b>Natija:</b> {round(score,1)}%\n"
        f"⏱ <b>Vaqt:</b> {m} daq {s} son\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎓 <b>Holat:</b> {'🎉 MUVAFFAQIYATLI!' if passed else '❌ YIQILDINGIZ.'}"
    )

    await state.clear()

    try:
        await message.delete()
    except Exception:
        pass

    await message.bot.send_message(
        chat_id, text,
        reply_markup=result_keyboard(test.get("test_id"), result_id, passed),
        parse_mode="HTML"
    )


# ==========================================================
# 6. BATAFSIL TAHLIL
# ==========================================================
@router.callback_query(F.data.startswith("analysis_"))
async def analysis_handler(callback: CallbackQuery):
    await callback.answer("⏳ Tahlil yuklanmoqda...")
    result_id = callback.data[9:]

    res_doc = get_db().collection("results").document(result_id).get()
    if not res_doc.exists:
        await callback.message.answer("❌ Natija bazadan topilmadi.")
        return

    res_data  = res_doc.to_dict()
    detailed  = res_data.get("detailed_results", [])
    test      = get_test(res_data.get("test_id"))
    questions = test.get("questions", []) if test else []

    if not detailed:
        await callback.message.answer(
            "<b>⚠️ ESKI TEST</b>\nBu eski test, uning tahlili yo'q.",
            parse_mode="HTML"
        )
        return

    title = test.get("title", "Test").upper() if test else "TEST"
    chunks: list[str] = []
    chunk  = f"<b>📝 {title} — TAHLIL</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for d in detailed:
        i          = d.get("question_index", 0)
        is_correct = d.get("is_correct", False)
        user_ans   = d.get("user_answer", "Belgilanmagan")
        corr_ans   = d.get("correct_answer", "Noma'lum")
        q_text     = questions[i].get("question", "") if i < len(questions) else ""
        explanation= questions[i].get("explanation", "") if i < len(questions) else ""

        holat = "✅ TO'G'RI" if is_correct else "❌ XATO"
        block = (
            f"<b>Savol {i+1}:</b> {q_text}\n"
            f"Holat: {holat}\n"
            f"👤 <b>Siz:</b> <i>{user_ans}</i>\n"
        )
        if not is_correct:
            block += f"🎯 <b>To'g'ri:</b> <i>{corr_ans}</i>\n"
        if explanation and explanation not in ("Izoh yo'q", "Izoh kiritilmagan", "Izoh kiritilmagan."):
            block += f"💡 <b>Izoh:</b> <i>{explanation}</i>\n"
        block += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

        if len(chunk) + len(block) > 4000:
            chunks.append(chunk)
            chunk = ""
        chunk += block

    if chunk:
        chunks.append(chunk)

    for ch in chunks:
        await callback.message.answer(ch, parse_mode="HTML", protect_content=True)

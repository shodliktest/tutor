"""
➕ TEST YARATISH HANDLER — Aiogram 3
Fayl yuklash (TXT/PDF/DOCX) yoki QuizBotdan poll forward qilish
Poll uslubida vaqt belgilash (har bir savol uchun soniya)
QuizBot savollarini TXT yuklab olish imkoni
Xavfsizlik: Admin/owner nazorati
"""
import os
import logging
import tempfile

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from utils.parser import parse_file
from utils.states import CreateTest
from firebase.db import create_test, get_test
from keyboards.keyboards import (
    difficulty_keyboard, test_visibility_keyboard,
    create_subject_keyboard, main_reply_keyboard
)
# _test_to_txt handlers.profile dan import qilinadi

log = logging.getLogger(__name__)
router = Router()

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "samples")

SAMPLE_TYPES = {
    "mcq":   ("multiple_choice_namuna.txt",  "🔘 Bir javobli",
              "1. O'zbekiston poytaxti qayer?\n===A) Toshkent\nB) Samarqand\nC) Buxoro\nD) Xiva\nIzoh: Toshkent 1930-yildan poytaxt."),
    "mrq":   ("multi_select_namuna.txt",     "☑️ Ko'p javobli",
              "TYPE: multi_select\n1. Qaysilar O'zbekistonda joylashgan?\n===A) Toshkent\n===B) Samarqand\nC) Ostona\n===D) Buxoro"),
    "tf":    ("true_false_namuna.txt",       "✅ Ha / Yo'q",
              "TYPE: true_false\n1. Yer Quyosh atrofida aylanadi.\nJavob: Ha\nIzoh: Yer elliptik orbita bo'ylab aylanadi."),
    "fill":  ("fill_blank_namuna.txt",       "✍️ Bo'sh joy",
              "TYPE: fill_blank\n1. Alisher Navoiy ___ yilda tug'ilgan.\nJavob: 1441\nQabul_qilinadigan: 1441-yil, 1441 yil"),
    "match": ("matching_namuna.txt",         "🔗 Moslashtirish",
              "TYPE: matching\n1. Davlat va poytaxtini moslashtiring:\nChap: O'zbekiston | Toshkent\nChap: Qozog'iston | Ostona"),
    "order": ("ordering_namuna.txt",         "🔢 Tartiblash",
              "TYPE: ordering\n1. Voqealarni tartiblang:\n1. 1-jahon urushi\n2. 2-jahon urushi\n3. Sovuq urush"),
    "all":   ("barcha_turlar_namuna.txt",    "📦 Aralash",
              "1. Poytaxt?\n===A) Toshkent\nB) Samarqand\n\nTYPE: fill_blank\n2. Pi = ___\nJavob: 3.14"),
}

POLL_TIME_OPTIONS = [15, 30, 45, 60, 90, 120]


# ═══════════════════════════════════════════════════════════
# 1. BOSHLASH
# ═══════════════════════════════════════════════════════════

@router.message(F.text == "➕ Test Yaratish")
async def create_start(message: Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📁 Fayl (TXT/PDF/DOCX)", callback_data="method_file"))
    builder.row(InlineKeyboardButton(text="📊 QuizBotdan forward",  callback_data="method_poll"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish",        callback_data="cancel_creation"))

    await message.answer(
        "<b>➕ TEST YARATISH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📁 <b>Fayl yuklash</b> — TXT, PDF yoki DOCX\n"
        "   Yaratilgan test ▶️ Inline va 📊 Poll ikki rejimda ishlaydi!\n\n"
        "📊 <b>QuizBotdan forward</b> — @QuizBot savollarini uzating\n"
        "   TXT yuklab olish + Poll uslubida ishlaydi!",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.choose_method)


# ═══════════════════════════════════════════════════════════
# 2. FAYL YUKLASH
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "method_file", CreateTest.choose_method)
async def method_file(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    for key, val in SAMPLE_TYPES.items():
        builder.add(InlineKeyboardButton(text=val[1], callback_data=f"sample_{key}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))

    await callback.message.edit_text(
        "<b>📁 TEST TURINI TANLANG</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Turni bosing → namuna olasiz → shu formatda fayl yuboring:\n\n"
        "<i>💡 Yaratilgan test ▶️ Inline va 📊 Poll rejimida ishlaydi!</i>",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.upload_file)


@router.callback_query(F.data.startswith("sample_"), CreateTest.upload_file)
async def send_sample(callback: CallbackQuery):
    await callback.answer()
    key = callback.data[7:]
    filename, type_name, mono_text = SAMPLE_TYPES.get(key, SAMPLE_TYPES["mcq"])
    file_path = os.path.join(SAMPLES_DIR, filename)

    if os.path.exists(file_path):
        await callback.message.answer_document(
            FSInputFile(file_path, filename=filename),
            caption=f"📄 <b>{type_name}</b> — namuna fayli"
        )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Boshqa tur", callback_data="method_file"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))

    await callback.message.edit_text(
        f"<b>📄 {type_name.upper()} FORMATI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Namuna:\n\n<code>{mono_text}</code>\n\n"
        f"⏳ <b>Faylingizni kutmoqdaman...</b>",
        reply_markup=builder.as_markup()
    )


@router.message(F.document, CreateTest.upload_file)
async def upload_file(message: Message, state: FSMContext):
    doc = message.document
    if not doc.file_name.lower().endswith((".txt", ".pdf", ".docx", ".doc")):
        return await message.answer("❌ Faqat TXT, PDF yoki DOCX fayllar qabul qilinadi!")

    status = await message.answer("⏳ Fayl tahlil qilinmoqda...")
    try:
        file   = await message.bot.get_file(doc.file_id)
        suffix = os.path.splitext(doc.file_name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            await message.bot.download_file(file.file_path, tmp.name)
            tmp_path = tmp.name

        questions = parse_file(tmp_path)
        os.remove(tmp_path)

        if not questions:
            return await status.edit_text(
                "❌ Fayldan savollar topilmadi.\n"
                "Namuna formatiga qarang va to'g'ri yozing."
            )

        await state.update_data(questions=questions)
        await status.edit_text(
            f"<b>✅ {len(questions)} TA SAVOL TOPILDI!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Test qaysi fanga tegishli?",
            reply_markup=create_subject_keyboard()
        )
        await state.set_state(CreateTest.set_subject)
    except Exception as e:
        log.error(f"Fayl xatosi: {e}")
        await status.edit_text("❌ Faylni o'qishda xatolik. Qaytadan urinib ko'ring.")


# ═══════════════════════════════════════════════════════════
# 3. QUIZBOT POLL FORWARD — vaqt belgilash + TXT yuklab olish
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "method_poll", CreateTest.choose_method)
async def method_poll(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(questions=[], poll_time=30)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Tayyor — davom etish", callback_data="finish_polls"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish",         callback_data="cancel_creation"))

    await callback.message.edit_text(
        "<b>📊 QUIZBOT POLL FORWARD</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ @QuizBot ga o'ting\n"
        "2️⃣ Viktorina savollarini toping\n"
        "3️⃣ Har birini bu yerga <b>Forward</b> qiling\n"
        "4️⃣ Tugagach <b>✅ Tayyor</b> bosing\n\n"
        "<i>💡 Savollarni TXT formatda yuklab olish ham mumkin bo'ladi!</i>",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.waiting_polls)


@router.message(F.poll, CreateTest.waiting_polls)
async def catch_poll(message: Message, state: FSMContext):
    poll = message.poll
    if poll.type != "quiz":
        return await message.answer(
            "❌ Faqat <b>Quiz (Viktorina)</b> turini yuboring!\n"
            "@QuizBot da savollar Quiz turida bo'lishi kerak."
        )

    data      = await state.get_data()
    questions = data.get("questions", [])
    letters   = ["A)", "B)", "C)", "D)", "E)", "F)", "G)", "H)", "I)", "J)"]
    options   = [f"{letters[i]} {opt.text}" for i, opt in enumerate(poll.options)]
    correct   = options[poll.correct_option_id]

    questions.append({
        "type":        "multiple_choice",
        "question":    poll.question,
        "options":     options,
        "correct":     correct,
        "explanation": poll.explanation or "Izoh kiritilmagan.",
        "points":      1,
        "source":      "poll",
    })
    await state.update_data(questions=questions)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Tayyor — davom etish", callback_data="finish_polls"))
    builder.row(InlineKeyboardButton(text="📄 TXT yuklab olish",     callback_data="download_polls_txt"))

    await message.answer(
        f"✅ <b>Savol qo'shildi!</b> Jami: <b>{len(questions)} ta</b>\n\n"
        f"Davom eting yoki tayyor bo'lsa bosing:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "download_polls_txt", CreateTest.waiting_polls)
async def download_polls_txt(callback: CallbackQuery, state: FSMContext):
    """QuizBotdan forward qilingan savollarni hoziroq TXT formatda yuborish"""
    await callback.answer("⏳ TXT tayyorlanmoqda...")
    data      = await state.get_data()
    questions = data.get("questions", [])
    if not questions:
        return await callback.answer("❌ Hali savol yo'q!", show_alert=True)

    # Vaqtinchalik test ob'ekti
    fake_test = {"title": "QuizBot_savollar", "questions": questions,
                 "category": "", "difficulty": "", "passing_score": 60,
                 "test_id": "DRAFT"}
    from handlers.profile import _test_to_txt as _to_txt
    txt = _to_txt(fake_test)
    doc = BufferedInputFile(txt.encode("utf-8"), filename="QuizBot_savollar.txt")
    await callback.message.answer_document(
        doc,
        caption=(
            f"📄 QuizBotdan forward qilingan savollar\n"
            f"📋 {len(questions)} ta savol\n\n"
            f"<i>Bu faylni keyinchalik '📁 Fayl yuklash' orqali ham yuklash mumkin!</i>"
        )
    )


@router.callback_query(F.data == "finish_polls", CreateTest.waiting_polls)
async def finish_polls(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("questions"):
        return await callback.answer("❌ Kamida 1 ta poll yuboring!", show_alert=True)

    # Poll uslubi uchun vaqt so'rash
    builder = InlineKeyboardBuilder()
    for sec in POLL_TIME_OPTIONS:
        builder.add(InlineKeyboardButton(text=f"⏱ {sec}s", callback_data=f"ptime_{sec}"))
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="♾ Vaqtsiz", callback_data="ptime_0"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))

    await callback.message.edit_text(
        f"<b>⏱ POLL SAVOL VAQTI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ {len(data['questions'])} ta savol tayyor!\n\n"
        f"<b>Poll uslubida</b> har savol uchun necha soniya?\n"
        f"<i>(Telegram Quiz poll da vaqt chegarasi)</i>",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.set_poll_time)


@router.callback_query(F.data.startswith("ptime_"), CreateTest.set_poll_time)
async def set_poll_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    pt = int(callback.data[6:])
    await state.update_data(poll_time=pt)

    await callback.message.edit_text(
        f"<b>📁 FANNI TANLANG</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⏱ Poll vaqti: <b>{'Cheksiz' if pt == 0 else f'{pt} soniya'}</b>\n\n"
        f"Test qaysi fanga tegishli?",
        reply_markup=create_subject_keyboard()
    )
    await state.set_state(CreateTest.set_subject)


# ═══════════════════════════════════════════════════════════
# 4. FAN, MAVZU, SOZLAMALAR
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("set_subj_"), CreateTest.set_subject)
async def set_subject_cb(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    subj = callback.data[9:]
    if subj == "other":
        await callback.message.edit_text(
            "<b>✏️ Fan nomini yozing:</b>\n"
            "<i>(Masalan: Tabiiy fanlar, Umumiy bilim)</i>"
        )
    else:
        await state.update_data(category=subj)
        await callback.message.edit_text(
            f"<b>🏷 TEST NOMI</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Fan: <b>{subj}</b>\n\n"
            f"Test mavzusini yozing:"
        )
        await state.set_state(CreateTest.set_title)


@router.message(F.text, CreateTest.set_subject)
async def set_subject_manual(message: Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await message.answer(f"<b>🏷 TEST NOMI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\nTest mavzusini yozing:")
    await state.set_state(CreateTest.set_title)


@router.message(F.text, CreateTest.set_title)
async def set_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer(
        f"<b>📊 QIYINLIK DARAJASI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Mavzu: <b>{message.text.strip()}</b>\n\n"
        f"Qiyinlik darajasini tanlang:",
        reply_markup=difficulty_keyboard()
    )
    await state.set_state(CreateTest.set_difficulty)


@router.callback_query(F.data.startswith("diff_"), CreateTest.set_difficulty)
async def set_difficulty(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(difficulty=callback.data[5:])
    await callback.message.edit_text(
        "<b>⏱ VAQT LIMITI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Vaqt limitini <b>daqiqada</b> kiriting.\n<i>Cheksiz = 0</i>"
    )
    await state.set_state(CreateTest.set_time_limit)


@router.message(F.text, CreateTest.set_time_limit)
async def set_time_limit(message: Message, state: FSMContext):
    t = message.text.strip()
    if not t.isdigit():
        return await message.answer("❌ Faqat raqam kiriting. Cheksiz = 0")
    await state.update_data(time_limit=int(t))
    await message.answer(
        "<b>🎯 O'TISH FOIZI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "O'tish foizini kiriting (0-100):\n<i>60 → 60% to'g'ri bo'lsa o'tdi</i>"
    )
    await state.set_state(CreateTest.set_passing)


@router.message(F.text, CreateTest.set_passing)
async def set_passing(message: Message, state: FSMContext):
    t = message.text.strip()
    if not t.isdigit() or not 0 <= int(t) <= 100:
        return await message.answer("❌ 0 dan 100 gacha raqam kiriting.")
    await state.update_data(passing_score=int(t))
    await message.answer(
        "<b>🔄 URINISHLAR SONI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Maksimal urinishlar sonini kiriting.\n<i>Cheksiz = 0</i>"
    )
    await state.set_state(CreateTest.set_attempts)


@router.message(F.text, CreateTest.set_attempts)
async def set_attempts(message: Message, state: FSMContext):
    t = message.text.strip()
    if not t.isdigit():
        return await message.answer("❌ Faqat raqam kiriting. Cheksiz = 0")
    await state.update_data(max_attempts=int(t))
    await message.answer(
        "<b>🔒 TEST MAXFIYLIGI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Test ko'rinishini tanlang:",
        reply_markup=test_visibility_keyboard()
    )
    await state.set_state(CreateTest.set_visibility)


# ═══════════════════════════════════════════════════════════
# 5. SAQLASH
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("vis_"), CreateTest.set_visibility)
async def save_test(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏳ Saqlanmoqda...")
    data       = await state.get_data()
    visibility = callback.data[4:]

    test_data = {
        "title":         data.get("title", "Nomsiz"),
        "category":      data.get("category", "Boshqa"),
        "difficulty":    data.get("difficulty", "medium"),
        "time_limit":    data.get("time_limit", 0),
        "poll_time":     data.get("poll_time", 30),
        "passing_score": data.get("passing_score", 60),
        "max_attempts":  data.get("max_attempts", 0),
        "visibility":    visibility,
        "questions":     data.get("questions", []),
    }
    tid      = create_test(callback.from_user.id, test_data)
    bot_user = await callback.bot.me()
    link     = f"https://t.me/{bot_user.username}?start={tid}"
    await state.clear()

    poll_time_txt = (f"{test_data['poll_time']} soniya" if test_data.get("poll_time")
                     else "Cheksiz")

    await callback.message.edit_text(
        f"<b>🎉 TEST MUVAFFAQIYATLI YARATILDI!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 Kod: <code>{tid}</code>\n"
        f"🔗 Ssilka: <code>{link}</code>\n\n"
        f"📁 Fan: {test_data['category']}\n"
        f"📝 Mavzu: {test_data['title']}\n"
        f"📋 Savollar: {len(test_data['questions'])} ta\n"
        f"⏱ Poll vaqti: {poll_time_txt} / savol\n\n"
        f"<i>✅ ▶️ Inline va 📊 Poll ikki rejimda ishlaydi!</i>"
    )

    # Kalit javoblar
    qs   = test_data["questions"]
    keys = f"🔑 <b>{test_data['title'].upper()} — JAVOBLAR KALITI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, q in enumerate(qs):
        keys += f"<b>{i+1}.</b> {q.get('correct', '?')}\n"
    if len(keys) > 4000:
        from handlers.profile import _test_to_txt as _to_txt
        txt = _to_txt(test_data)
        await callback.message.answer_document(
            BufferedInputFile(txt.encode("utf-8"), filename=f"Kalit_{tid}.txt"),
            caption="🔑 Javoblar kaliti"
        )
    else:
        await callback.message.answer(keys)


# ═══════════════════════════════════════════════════════════
# 6. BEKOR QILISH
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "cancel_creation")
async def cancel_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.bot.send_message(
        callback.from_user.id,
        "❌ Test yaratish bekor qilindi.",
        reply_markup=main_reply_keyboard(callback.from_user.id)
    )

"""
➕ TEST YARATISH HANDLER — Aiogram 3
Fayl yuklash (TXT/PDF/DOCX) yoki QuizBotdan poll forward qilish
"""
import os
import io
import uuid
import logging
import tempfile
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from utils.parser import parse_file
from utils.states import CreateTest
from firebase.db import create_test
from keyboards.keyboards import (
    difficulty_keyboard, test_visibility_keyboard,
    create_subject_keyboard, main_reply_keyboard
)

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
    "all":   ("barcha_turlar_namuna.txt",    "📦 Barcha turlar aralash",
              "1. Poytaxt?\n===A) Toshkent\nB) Samarqand\n\nTYPE: fill_blank\n2. Pi = ___\nJavob: 3.14"),
}


# ═══════════════════════════════════════════════════════════
# 1. BOSHLASH
# ═══════════════════════════════════════════════════════════

@router.message(F.text == "➕ Test Yaratish")
async def create_start(message: Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📁 Fayl yuklash (TXT/PDF)", callback_data="method_file"),
        InlineKeyboardButton(text="📊 QuizBotdan forward",     callback_data="method_poll"),
    )
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))

    await message.answer(
        "<b>➕ TEST YARATISH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Savollarni qanday yig'moqchisiz?\n\n"
        "<b>📁 Fayl yuklash:</b> TXT, PDF yoki DOCX fayldan o'qish\n"
        "<b>📊 QuizBotdan:</b> @QuizBot viktorinalarini forward qilish",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.choose_method)


# ═══════════════════════════════════════════════════════════
# 2. FAYL YUKLASH REJIMI
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
        "Birorta turni bosing — men namuna yuboraman.\n"
        "So'ng shu formatda faylingizni tayyorlab yuboring:",
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
            caption=f"📄 {type_name} uchun namuna fayli"
        )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Boshqa tur tanlash", callback_data="method_file"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))

    await callback.message.edit_text(
        f"<b>📄 {type_name.upper()} FORMATI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Namuna:\n\n"
        f"<code>{mono_text}</code>\n\n"
        f"<i>💡 Yuqoridagi matnni bosib nusxa oling, "
        f"o'zgartirib TXT/PDF/DOCX fayl sifatida yuboring.</i>\n\n"
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
                "Namunaga qarang va to'g'ri formatda yozing."
            )

        await state.update_data(questions=questions)
        await status.edit_text(
            f"<b>✅ {len(questions)} TA SAVOL TOPILDI!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Endi test qaysi fanga tegishli ekanini tanlang:",
            reply_markup=create_subject_keyboard()
        )
        await state.set_state(CreateTest.set_subject)

    except Exception as e:
        log.error(f"Fayl xatosi: {e}")
        await status.edit_text("❌ Faylni o'qishda xatolik. Qaytadan urinib ko'ring.")


# ═══════════════════════════════════════════════════════════
# 3. QUIZBOT POLL FORWARD REJIMI
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "method_poll", CreateTest.choose_method)
async def method_poll(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(questions=[])

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Tayyor, davom etish", callback_data="finish_polls"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))

    await callback.message.edit_text(
        "<b>📊 QUIZBOT POLL FORWARD</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ @QuizBot ga o'ting\n"
        "2️⃣ Tayyor viktorinani toping\n"
        "3️⃣ Har bir savolni bu yerga <b>Forward (Uzatish)</b> qiling\n"
        "4️⃣ Hammasi tugagach <b>✅ Tayyor</b> ni bosing\n\n"
        "<i>💡 Har yuborgan polldan savol qo'shiladi. "
        "Natijada bu savollar 📊 Poll test rejimida ham ishlaydi!</i>",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.waiting_polls)


@router.message(F.poll, CreateTest.waiting_polls)
async def catch_poll(message: Message, state: FSMContext):
    poll = message.poll
    if poll.type != "quiz":
        return await message.answer("❌ Faqat Quiz (Viktorina) turini yuboring!")

    data      = await state.get_data()
    questions = data.get("questions", [])

    letters  = ["A)", "B)", "C)", "D)", "E)", "F)", "G)", "H)", "I)", "J)"]
    options  = [f"{letters[i]} {opt.text}" for i, opt in enumerate(poll.options)]
    correct  = options[poll.correct_option_id]

    questions.append({
        "type":        "multiple_choice",
        "question":    poll.question,
        "options":     options,
        "correct":     correct,
        "explanation": poll.explanation or "Izoh kiritilmagan.",
        "points":      1,
        "source":      "poll",   # Poll orqali yaratilganini belgilash
    })

    await state.update_data(questions=questions)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Tayyor, davom etish", callback_data="finish_polls"))

    await message.answer(
        f"✅ Savol qo'shildi! Jami: <b>{len(questions)} ta</b>\n"
        f"Yana savollar yuboring yoki tayyor bo'lsa bosing:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "finish_polls", CreateTest.waiting_polls)
async def finish_polls(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("questions"):
        return await callback.answer("❌ Kamida 1 ta poll yuboring!", show_alert=True)

    await callback.message.edit_text(
        "<b>📁 FANNI TANLANG</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ {len(data['questions'])} ta savol tayyor!\n\n"
        "Endi test qaysi fanga tegishli ekanini tanlang:",
        reply_markup=create_subject_keyboard()
    )
    await state.set_state(CreateTest.set_subject)


# ═══════════════════════════════════════════════════════════
# 4. FAN, MAVZU, SOZLAMALAR QADAMLARI
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("set_subj_"), CreateTest.set_subject)
async def set_subject(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    subj = callback.data[9:]

    if subj == "other":
        await callback.message.edit_text("<b>✏️ Fan nomini yozing:</b>")
        # set_subject state saqlanadi — keyingi message handler ushlaydi
    else:
        await state.update_data(category=subj)
        await callback.message.edit_text(
            f"<b>🏷 TEST NOMI</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Fan: {subj}\n\n"
            f"Test mavzusini yozing:\n"
            f"<i>(Masalan: O'nlik kasrlar, Kimyoviy reaksiyalar)</i>"
        )
        await state.set_state(CreateTest.set_title)


@router.message(F.text, CreateTest.set_subject)
async def set_subject_manual(message: Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await message.answer(
        f"<b>🏷 TEST NOMI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Fan: {message.text.strip()}\n\n"
        f"Test mavzusini yozing:"
    )
    await state.set_state(CreateTest.set_title)


@router.message(F.text, CreateTest.set_title)
async def set_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer(
        f"<b>📊 QIYINLIK DARAJASI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Mavzu: {message.text.strip()}\n\n"
        f"Qiyinlik darajasini tanlang:",
        reply_markup=difficulty_keyboard()
    )
    await state.set_state(CreateTest.set_difficulty)


@router.callback_query(F.data.startswith("diff_"), CreateTest.set_difficulty)
async def set_difficulty(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(difficulty=callback.data[5:])
    await callback.message.edit_text(
        "<b>⏱ VAQT LIMITI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Vaqt limitini daqiqada kiriting.\n"
        "<i>Cheksiz bo'lsa — 0 yozing:</i>"
    )
    await state.set_state(CreateTest.set_time_limit)


@router.message(F.text, CreateTest.set_time_limit)
async def set_time_limit(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❌ Faqat raqam kiriting (daqiqada). Cheksiz = 0")
    await state.update_data(time_limit=int(message.text))
    await message.answer(
        "<b>🎯 O'TISH FOIZI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "O'tish foizini kiriting (0-100):\n"
        "<i>Masalan: 60 → 60% to'g'ri javob bo'lsa o'tdi</i>"
    )
    await state.set_state(CreateTest.set_passing)


@router.message(F.text, CreateTest.set_passing)
async def set_passing(message: Message, state: FSMContext):
    if not message.text.isdigit() or not 0 <= int(message.text) <= 100:
        return await message.answer("❌ 0 dan 100 gacha raqam kiriting.")
    await state.update_data(passing_score=int(message.text))
    await message.answer(
        "<b>🔄 URINISHLAR SONI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Maksimal urinishlar sonini kiriting.\n"
        "<i>Cheksiz bo'lsa — 0 yozing:</i>"
    )
    await state.set_state(CreateTest.set_attempts)


@router.message(F.text, CreateTest.set_attempts)
async def set_attempts(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❌ Faqat raqam kiriting. Cheksiz = 0")
    await state.update_data(max_attempts=int(message.text))
    await message.answer(
        "<b>🔒 TEST MAXFIYLIGI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
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
        "title":        data.get("title", "Nomsiz"),
        "category":     data.get("category", "Boshqa"),
        "difficulty":   data.get("difficulty", "medium"),
        "time_limit":   data.get("time_limit", 0),
        "passing_score": data.get("passing_score", 60),
        "max_attempts": data.get("max_attempts", 0),
        "visibility":   visibility,
        "questions":    data.get("questions", []),
    }
    tid = create_test(callback.from_user.id, test_data)
    await state.clear()

    bot_user = await callback.bot.me()
    link     = f"https://t.me/{bot_user.username}?start={tid}"

    await callback.message.edit_text(
        f"<b>🎉 TEST MUVAFFAQIYATLI YARATILDI!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 Kod: <code>{tid}</code>\n"
        f"🔗 Ssilka: <code>{link}</code>\n\n"
        f"📁 Fan: {test_data['category']}\n"
        f"📝 Mavzu: {test_data['title']}\n"
        f"📋 Savollar: {len(test_data['questions'])} ta\n\n"
        f"<i>Kodni ulashing — do'stlaringiz ham ishlaydi!\n"
        f"Test 2 rejimda ham ishlaydi: ▶️ Inline va 📊 Poll</i>"
    )

    # Kalit javoblarni yuborish
    qs   = test_data["questions"]
    keys = f"<b>🔑 {test_data['title'].upper()} — JAVOBLAR</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, q in enumerate(qs):
        keys += f"<b>{i+1}.</b> {q.get('correct', '?')}\n"

    if len(keys) > 4000:
        file_bytes = keys.encode("utf-8")
        await callback.message.answer_document(
            BufferedInputFile(file_bytes, filename=f"Kalit_{tid}.txt"),
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

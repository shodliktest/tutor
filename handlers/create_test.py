"""
➕ TEST YARATISH HANDLER — Aiogram 3
Oqim:
  1. Yaratish tugmasi → 3 usul taklif qilinadi
     a) Web App muharriri   → create.html ochiladi (bo'sh)
     b) Fayl yuklash (TXT/PDF/DOCX)
     c) QuizBot poll forward

  2. Fayl/poll tayyor bo'lgach →
     "🎨 Web App da ko'rish va tahrirlash" tugmasi paydo bo'ladi
     Foydalanuvchi create.html da savollarni ko'rib tahrirlaydi
     Tahrirlangach sendData() → bot saqlaydi
     YOKI
     "✅ Saqlash" → fan, nom, ko'rinish → saqlash

  3. Saqlash tugallangach → kalit javoblar + muvaffaqiyat xabari
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
from firebase.db import create_test, get_user
from keyboards.keyboards import (
    create_subject_keyboard, main_reply_keyboard,
    webapp_create_keyboard, after_parse_keyboard
)

log = logging.getLogger(__name__)
router = Router()

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "samples")

# ── Yig'ilgan xabarlar IDlari ──────────────────────────────
_upload_msgs: dict = {}   # {user_id: [msg_id, ...]}
_key_msgs: dict    = {}   # {user_id: msg_id}


def _track_msg(uid: int, msg_id: int):
    if uid not in _upload_msgs:
        _upload_msgs[uid] = []
    _upload_msgs[uid].append(msg_id)


async def _clear_upload_msgs(bot, uid: int, chat_id: int):
    for mid in _upload_msgs.pop(uid, []):
        try:
            await bot.delete_message(chat_id, mid)
        except Exception:
            pass


async def clear_key_msg(bot, uid: int, chat_id: int):
    """Kalit javoblar xabarini o'chirish"""
    mid = _key_msgs.pop(uid, None)
    if mid:
        try:
            await bot.delete_message(chat_id, mid)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════
# NAMUNA MATNLARI
# ══════════════════════════════════════════════════════════

SAMPLE_TYPES = {
    "mcq": {
        "label": "🔘 Bir javobli",
        "format": (
            "1. O'zbekiston poytaxti qayer?\n"
            "===A) Toshkent\n"
            "B) Samarqand\n"
            "C) Buxoro\n"
            "Izoh: Toshkent 1930-yildan poytaxt."
        ),
        "hint": "=== belgisi to'g'ri javob oldiga qo'yiladi. Izoh ixtiyoriy."
    },
    "tf": {
        "label": "✅ Ha / Yo'q",
        "format": (
            "TYPE: true_false\n"
            "1. Yer Quyosh atrofida aylanadi.\n"
            "Javob: Ha\n"
            "Izoh: Yer elliptik orbita bo'ylab aylanadi."
        ),
        "hint": "Javob: Ha yoki Javob: Yo'q. Izoh ixtiyoriy."
    },
    "fill": {
        "label": "✍️ Bo'sh joy",
        "format": (
            "TYPE: fill_blank\n"
            "1. Alisher Navoiy ___ yilda tug'ilgan.\n"
            "Javob: 1441\n"
            "Izoh: Buyuk shoir va mutafakkir."
        ),
        "hint": "Javob: so'zidan keyin to'g'ri javob."
    },
    "match": {
        "label": "🔗 Moslashtirish",
        "format": (
            "TYPE: matching\n"
            "1. Davlat va poytaxtini moslashtiring:\n"
            "Chap: O'zbekiston | Toshkent\n"
            "Chap: Qozog'iston | Ostona\n"
            "Chap: Rossiya | Moskva"
        ),
        "hint": "Chap: [1-ustun] | [2-ustun] formatida"
    },
    "mrq": {
        "label": "☑️ Ko'p javobli",
        "format": (
            "TYPE: multi_select\n"
            "1. OOP tamoyillari:\n"
            "===A) Inkapsulyatsiya\n"
            "B) Kompilyatsiya\n"
            "===C) Meros olish\n"
            "===D) Polimorfizm"
        ),
        "hint": "Har to'g'ri javob oldiga === qo'yiladi"
    },
    "order": {
        "label": "🔢 Tartiblash",
        "format": (
            "TYPE: ordering\n"
            "1. Voqealarni tartiblang:\n"
            "1. 1-jahon urushi\n"
            "2. 2-jahon urushi\n"
            "3. Sovuq urush"
        ),
        "hint": "Raqam bilan to'g'ri tartibda yozing"
    },
}

POLL_TIME_OPTIONS = [15, 30, 45, 60, 90, 120]


# ══════════════════════════════════════════════════════════
# 1. BOSHLASH
# ══════════════════════════════════════════════════════════

@router.message(F.text == "➕ Test Yaratish")
async def create_start(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    await clear_key_msg(message.bot, uid, message.chat.id)

    msg = await message.answer(
        "<b>➕ TEST YARATISH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✨ <b>Web App</b> — vizual muharrir:\n"
        "   Ko'p tanlovli • Ha/Yo'q • Bo'sh joy\n"
        "   Moslashtirish • Tartiblashtirish\n\n"
        "📁 <b>Fayl</b> — TXT, PDF yoki DOCX yuklab, keyin\n"
        "   Web App da ko'rib tahrirlash mumkin\n\n"
        "📊 <b>QuizBot</b> — @QuizBot pollini forward qiling,\n"
        "   keyin Web App da tahrirlash mumkin",
        reply_markup=webapp_create_keyboard()
    )
    _track_msg(uid, msg.message_id)
    _track_msg(uid, message.message_id)
    await state.set_state(CreateTest.choose_method)


# ══════════════════════════════════════════════════════════
# 2. FAYL YUKLASH
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data == "method_file", CreateTest.choose_method)
async def method_file(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    builder = InlineKeyboardBuilder()
    for key, val in SAMPLE_TYPES.items():
        builder.add(InlineKeyboardButton(text=val["label"], callback_data=f"sample_{key}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="📦 Aralash namuna", callback_data="sample_all"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))

    await callback.message.edit_text(
        "<b>📁 TEST TURINI TANLANG</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Turni bosing → namuna formatni ko'rasiz\n"
        "Shu formatda fayl tayyorlab yuboring:\n\n"
        "<i>💡 Fayl yuklangach Web App da tahrirlash imkoni bo'ladi!</i>",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.upload_file)


@router.callback_query(F.data == "sample_all", CreateTest.upload_file)
async def send_sample_all(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    file_path = os.path.join(SAMPLES_DIR, "barcha_turlar_namuna.txt")

    builder = InlineKeyboardBuilder()
    for key, val in SAMPLE_TYPES.items():
        builder.add(InlineKeyboardButton(text=val["label"], callback_data=f"sample_{key}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))

    if os.path.exists(file_path):
        await callback.message.answer_document(
            FSInputFile(file_path),
            caption="📦 <b>Barcha test turlari</b> — namuna fayli"
        )

    await callback.message.edit_text(
        "<b>📦 BARCHA TURLAR — FORMAT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Yuqorida barcha turlar namunasi yuborildi.\n\n"
        "⏳ <b>Faylingizni yuboring yoki tur tanlang:</b>",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("sample_"), CreateTest.upload_file)
async def send_sample(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    key = callback.data[7:]
    if key == "all":
        return
    info = SAMPLE_TYPES.get(key, SAMPLE_TYPES["mcq"])

    builder = InlineKeyboardBuilder()
    for k, v in SAMPLE_TYPES.items():
        builder.add(InlineKeyboardButton(
            text=v["label"] + (" ✓" if k == key else ""),
            callback_data=f"sample_{k}"
        ))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))

    await callback.message.edit_text(
        f"<b>{info['label'].upper()} — FORMAT NAMUNASI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 <i>{info['hint']}</i>\n\n"
        f"<code>{info['format']}</code>\n\n"
        f"⏳ <b>Faylingizni yuboring:</b>",
        reply_markup=builder.as_markup()
    )


@router.message(F.document, CreateTest.upload_file)
async def upload_file(message: Message, state: FSMContext):
    uid = message.from_user.id
    _track_msg(uid, message.message_id)

    doc = message.document
    if not doc.file_name.lower().endswith((".txt", ".pdf", ".docx", ".doc")):
        m = await message.answer("❌ Faqat TXT, PDF yoki DOCX fayllar qabul qilinadi!")
        _track_msg(uid, m.message_id)
        return

    status = await message.answer("⏳ Fayl tahlil qilinmoqda...")
    _track_msg(uid, status.message_id)

    try:
        file   = await message.bot.get_file(doc.file_id)
        suffix = os.path.splitext(doc.file_name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            await message.bot.download_file(file.file_path, tmp.name)
            tmp_path = tmp.name

        questions = parse_file(tmp_path)
        os.remove(tmp_path)

        if not questions:
            await status.edit_text(
                "❌ Fayldan savollar topilmadi.\n"
                "Namuna formatiga qarang va to'g'ri yozing."
            )
            return

        await state.update_data(questions=questions)

        # ── Kalit: fayldan chiqqandan keyin tahrirlash imkoni ──
        await status.edit_text(
            f"<b>✅ {len(questions)} TA SAVOL TOPILDI!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎨 <b>Web App da ko'ring va tahrirlang</b> — savollarni\n"
            f"   ko'rib chiqing, xato bo'lsa tuzating\n\n"
            f"✅ <b>Saqlash</b> — to'g'ridan fan va nom kiriting\n\n"
            f"<i>💡 Web App da tahrirlangach bot avtomatik saqlaydi</i>",
            reply_markup=after_parse_keyboard(questions)
        )
        # "✅ Saqlash" bosilsa fan tanlashga o'tiladi
        await state.set_state(CreateTest.set_subject)

    except Exception as e:
        log.error(f"Fayl xatosi: {e}")
        await status.edit_text("❌ Faylni o'qishda xatolik. Qaytadan urinib ko'ring.")


# ══════════════════════════════════════════════════════════
# 3. QUIZBOT POLL FORWARD
# ══════════════════════════════════════════════════════════

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
        "⚠️ <b>Faqat Quiz (Viktorina) turi qabul qilinadi!</b>\n"
        "<i>Saqlashdan oldin Web App da tahrirlash imkoni bo'ladi!</i>",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.waiting_polls)


@router.message(F.poll, CreateTest.waiting_polls)
async def catch_poll(message: Message, state: FSMContext):
    uid  = message.from_user.id
    _track_msg(uid, message.message_id)
    poll = message.poll

    if poll.type != "quiz":
        m = await message.answer(
            "❌ <b>Faqat Quiz (Viktorina) turini yuboring!</b>\n\n"
            "📌 @QuizBot da savollar <b>Quiz</b> turida bo'lishi kerak.\n"
            "<i>Oddiy so'rovnoma (poll) qabul qilinmaydi.</i>"
        )
        _track_msg(uid, m.message_id)
        return

    data      = await state.get_data()
    questions = data.get("questions", [])
    letters   = ["A)", "B)", "C)", "D)", "E)", "F)", "G)", "H)", "I)", "J)"]
    options   = [f"{letters[i]} {opt.text}" for i, opt in enumerate(poll.options)]
    correct   = poll.correct_option_id  # indeks saqlaymiz

    questions.append({
        "type":        "multiple_choice",
        "question":    poll.question,
        "text":        poll.question,
        "options":     options,
        "correct":     correct,
        "explanation": poll.explanation or "",
        "points":      1,
        "source":      "poll",
    })
    await state.update_data(questions=questions)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Tayyor — davom etish", callback_data="finish_polls"))
    builder.row(InlineKeyboardButton(text="📄 TXT yuklab olish",     callback_data="download_polls_txt"))

    m = await message.answer(
        f"✅ <b>Savol qo'shildi!</b> Jami: <b>{len(questions)} ta</b>\n\n"
        f"Davom eting yoki tayyor bo'lsa bosing:",
        reply_markup=builder.as_markup()
    )
    _track_msg(uid, m.message_id)


@router.callback_query(F.data == "download_polls_txt", CreateTest.waiting_polls)
async def download_polls_txt(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏳ TXT tayyorlanmoqda...")
    data      = await state.get_data()
    questions = data.get("questions", [])
    if not questions:
        return await callback.answer("❌ Hali savol yo'q!", show_alert=True)

    user     = callback.from_user
    bot_info = await callback.bot.me()
    fake_test = {
        "title": "QuizBot_savollar",
        "questions": questions,
        "category": "",
        "difficulty": "",
        "passing_score": 60,
        "test_id": "DRAFT"
    }
    from handlers.profile import _test_to_txt as _to_txt
    txt = _to_txt(fake_test, user=user, bot_info=bot_info)
    doc = BufferedInputFile(txt.encode("utf-8"), filename="QuizBot_savollar.txt")
    await callback.message.answer_document(
        doc,
        caption=(
            f"📄 QuizBotdan forward qilingan savollar\n"
            f"📋 {len(questions)} ta savol"
        )
    )


@router.callback_query(F.data == "finish_polls", CreateTest.waiting_polls)
async def finish_polls(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    questions = data.get("questions", [])
    if not questions:
        return await callback.answer("❌ Kamida 1 ta poll yuboring!", show_alert=True)

    await state.update_data(questions=questions)

    # ── Poll tugadi — tahrirlash imkoni ──
    await callback.message.edit_text(
        f"<b>✅ {len(questions)} TA SAVOL TAYYOR!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎨 <b>Web App da ko'ring va tahrirlang</b> — savollarni\n"
        f"   ko'rib chiqing, xato bo'lsa tuzating\n\n"
        f"✅ <b>Saqlash</b> — to'g'ridan fan va nom kiriting\n\n"
        f"<i>💡 Web App da tahrirlangach bot avtomatik saqlaydi</i>",
        reply_markup=after_parse_keyboard(questions)
    )
    await state.set_state(CreateTest.set_subject)


# ══════════════════════════════════════════════════════════
# "✅ Saqlash" — fan, nom, ko'rinish tanlash
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data == "proceed_to_subject")
async def proceed_to_subject(callback: CallbackQuery, state: FSMContext):
    """after_parse_keyboard dagi 'Saqlash' tugmasi"""
    await callback.answer()
    await callback.message.edit_text(
        "<b>📁 FANNI TANLANG</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Test qaysi fanga tegishli?",
        reply_markup=create_subject_keyboard()
    )


# ══════════════════════════════════════════════════════════
# FAN, MAVZU, KO'RINISH
# ══════════════════════════════════════════════════════════

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
    uid = message.from_user.id
    _track_msg(uid, message.message_id)
    await state.update_data(category=message.text.strip())
    m = await message.answer(
        "<b>🏷 TEST NOMI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\nTest mavzusini yozing:"
    )
    _track_msg(uid, m.message_id)
    await state.set_state(CreateTest.set_title)


@router.message(F.text, CreateTest.set_title)
async def set_title(message: Message, state: FSMContext):
    uid = message.from_user.id
    _track_msg(uid, message.message_id)
    await state.update_data(title=message.text.strip())

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌍 Ommaviy",        callback_data="vis_public"))
    builder.row(InlineKeyboardButton(text="🔗 Ssilka orqali",  callback_data="vis_link"))
    builder.row(InlineKeyboardButton(text="🔒 Shaxsiy",         callback_data="vis_private"))
    builder.row(InlineKeyboardButton(text="❌ Bekor",            callback_data="cancel_creation"))

    m = await message.answer(
        f"<b>🔒 TEST MAXFIYLIGI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Mavzu: <b>{message.text.strip()}</b>\n\n"
        f"Test ko'rinishini tanlang:",
        reply_markup=builder.as_markup()
    )
    _track_msg(uid, m.message_id)
    await state.set_state(CreateTest.set_visibility)


# ══════════════════════════════════════════════════════════
# SAQLASH — Firebase ga yozish + kalit
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("vis_"), CreateTest.set_visibility)
async def save_test_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏳ Saqlanmoqda...")
    data       = await state.get_data()
    visibility = callback.data[4:]
    uid        = callback.from_user.id
    chat_id    = callback.message.chat.id

    test_data = {
        "title":         data.get("title", "Nomsiz"),
        "category":      data.get("category", "Boshqa"),
        "difficulty":    "medium",
        "time_limit":    0,
        "poll_time":     data.get("poll_time", 30),
        "passing_score": 60,
        "max_attempts":  0,
        "visibility":    visibility,
        "questions":     data.get("questions", []),
    }
    tid      = create_test(uid, test_data)
    bot_user = await callback.bot.me()
    link     = f"https://t.me/{bot_user.username}?start={tid}"
    await state.clear()

    # Barcha upload xabarlarni o'chirish
    _track_msg(uid, callback.message.message_id)
    await _clear_upload_msgs(callback.bot, uid, chat_id)

    # Muvaffaqiyat xabari
    await callback.bot.send_message(
        chat_id,
        f"<b>🎉 TEST MUVAFFAQIYATLI YARATILDI!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 Kod: <code>{tid}</code>\n"
        f"🔗 Ssilka: <code>{link}</code>\n\n"
        f"📁 Fan: {test_data['category']}\n"
        f"📝 Mavzu: {test_data['title']}\n"
        f"📋 Savollar: {len(test_data['questions'])} ta\n\n"
        f"<i>✅ Web App, Inline va Poll — uch rejimda ishlaydi!</i>",
        reply_markup=main_reply_keyboard(uid)
    )

    # Kalit javoblar
    qs   = test_data["questions"]
    keys = f"🔑 <b>{test_data['title'].upper()} — JAVOBLAR KALITI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, q in enumerate(qs):
        corr = q.get("correct", "?")
        if isinstance(corr, list):
            corr = ", ".join(str(c) for c in corr)
        keys += f"<b>{i+1}.</b> {corr}\n"

    key_builder = InlineKeyboardBuilder()
    key_builder.row(InlineKeyboardButton(text="✉️ Kalit yashirish", callback_data="hide_key_msg"))

    if len(keys) > 4000:
        from handlers.profile import _test_to_txt as _to_txt
        txt = _to_txt(test_data, user=callback.from_user, bot_info=bot_user)
        m = await callback.bot.send_document(
            chat_id,
            BufferedInputFile(txt.encode("utf-8"), filename=f"Kalit_{tid}.txt"),
            caption="🔑 Javoblar kaliti"
        )
    else:
        m = await callback.bot.send_message(
            chat_id, keys, reply_markup=key_builder.as_markup()
        )
    _key_msgs[uid] = m.message_id


# ══════════════════════════════════════════════════════════
# KALIT YASHIRISH
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data == "hide_key_msg")
async def hide_key_msg(callback: CallbackQuery):
    await callback.answer("🔒 Kalit yashirildi")
    uid = callback.from_user.id
    _key_msgs.pop(uid, None)
    try:
        await callback.message.delete()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════
# BEKOR QILISH
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data == "noop")
async def noop_cb(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "cancel_creation")
async def cancel_creation(callback: CallbackQuery, state: FSMContext):
    uid     = callback.from_user.id
    chat_id = callback.message.chat.id
    await state.clear()
    await callback.answer()

    _track_msg(uid, callback.message.message_id)
    await _clear_upload_msgs(callback.bot, uid, chat_id)

    await callback.bot.send_message(
        uid,
        "❌ Test yaratish bekor qilindi.",
        reply_markup=main_reply_keyboard(uid)
    )

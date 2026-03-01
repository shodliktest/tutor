"""
➕ TEST YARATISH HANDLER — v5
Yangilik: Fayl/poll tayyor bo'lgach "Kalitni ko'rish" tugmasi
          create.html da savollar ko'rinadi — tahrirlash mumkin!
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

_upload_msgs: dict = {}
_key_msgs: dict = {}


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
    mid = _key_msgs.pop(uid, None)
    if mid:
        try:
            await bot.delete_message(chat_id, mid)
        except Exception:
            pass


SAMPLE_TYPES = {
    "mcq": {
        "label": "🔘 Bir javobli",
        "format": (
            "1. O'zbekiston poytaxti qayer?\n"
            "===A) Toshkent\nB) Samarqand\nC) Buxoro\n"
            "Izoh: Toshkent 1930-yildan poytaxt."
        ),
        "hint": "=== belgisi to'g'ri javob oldiga qo'yiladi."
    },
    "tf": {
        "label": "✅ Ha / Yo'q",
        "format": "TYPE: true_false\n1. Yer Quyosh atrofida aylanadi.\nJavob: Ha",
        "hint": "Javob: Ha yoki Javob: Yo'q"
    },
    "fill": {
        "label": "✍️ Bo'sh joy",
        "format": "TYPE: fill_blank\n1. Alisher Navoiy ___ yilda tug'ilgan.\nJavob: 1441",
        "hint": "Javob: so'zidan keyin to'g'ri javob"
    },
    "match": {
        "label": "🔗 Moslashtirish",
        "format": "TYPE: matching\n1. Davlat va poytaxtini moslashtiring:\nChap: O'zbekiston | Toshkent\nChap: Qozog'iston | Ostona",
        "hint": "Chap: [1-ustun] | [2-ustun]"
    },
    "mrq": {
        "label": "☑️ Ko'p javobli",
        "format": "TYPE: multi_select\n1. OOP tamoyillari:\n===A) Inkapsulyatsiya\nB) Kompilyatsiya\n===C) Meros olish",
        "hint": "Har to'g'ri javob oldiga === qo'yiladi"
    },
    "order": {
        "label": "🔢 Tartiblash",
        "format": "TYPE: ordering\n1. Voqealarni tartiblang:\n1. 1-jahon urushi\n2. 2-jahon urushi\n3. Sovuq urush",
        "hint": "To'g'ri tartibda raqam bilan"
    },
}


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
        "   🔑 <b>Kalit tugmasi</b> orqali savollarni ko'rish va tahrirlash mumkin!\n\n"
        "📊 <b>QuizBot</b> — @QuizBot pollini forward qiling,\n"
        "   keyin Web App da tahrirlash mumkin",
        reply_markup=webapp_create_keyboard()
    )
    _track_msg(uid, msg.message_id)
    _track_msg(uid, message.message_id)
    await state.set_state(CreateTest.choose_method)


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
        "<i>💡 Fayl yuklangach 🔑 Kalitni ko'rish tugmasi orqali\n"
        "   savollarni ko'rib tahrirlash imkoni bo'ladi!</i>",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.upload_file)


@router.callback_query(F.data.startswith("sample_"), CreateTest.upload_file)
async def send_sample(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    key = callback.data[7:]

    if key == "all":
        file_path = os.path.join(SAMPLES_DIR, "barcha_turlar_namuna.txt")
        builder = InlineKeyboardBuilder()
        for k, v in SAMPLE_TYPES.items():
            builder.add(InlineKeyboardButton(text=v["label"], callback_data=f"sample_{k}"))
        builder.adjust(2)
        builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
        if os.path.exists(file_path):
            await callback.message.answer_document(
                FSInputFile(file_path),
                caption="📦 <b>Barcha test turlari</b> — namuna fayli"
            )
        await callback.message.edit_text(
            "<b>📦 BARCHA TURLAR — FORMAT</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Yuqorida namuna yuborildi.\n\n⏳ <b>Faylingizni yuboring:</b>",
            reply_markup=builder.as_markup()
        )
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
        file = await message.bot.get_file(doc.file_id)
        suffix = os.path.splitext(doc.file_name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            await message.bot.download_file(file.file_path, tmp.name)
            tmp_path = tmp.name

        questions = parse_file(tmp_path)
        os.remove(tmp_path)

        if not questions:
            await status.edit_text(
                "❌ Fayldan savollar topilmadi.\nNamuna formatiga qarang."
            )
            return

        await state.update_data(questions=questions)

        # ── KALIT tugmasi — create.html da savollarni ko'rish ──
        await status.edit_text(
            f"<b>✅ {len(questions)} TA SAVOL TOPILDI!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔑 <b>Kalitni ko'rish va tahrirlash</b> — Web App da savollarni\n"
            f"   ko'rib chiqing, xato bo'lsa tuzating\n\n"
            f"✅ <b>Saqlash</b> — to'g'ridan fan va nom kiriting\n\n"
            f"<i>💡 Web App da tahrirlangach bot avtomatik saqlaydi</i>",
            reply_markup=after_parse_keyboard(questions)
        )
        await state.set_state(CreateTest.set_subject)

    except Exception as e:
        log.error(f"Fayl xatosi: {e}")
        await status.edit_text("❌ Faylni o'qishda xatolik.")


@router.callback_query(F.data == "method_poll", CreateTest.choose_method)
async def method_poll(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(questions=[], poll_time=30)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Tayyor — davom etish", callback_data="finish_polls"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))

    await callback.message.edit_text(
        "<b>📊 QUIZBOT POLL FORWARD</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ @QuizBot ga o'ting\n"
        "2️⃣ Quiz savollarini toping\n"
        "3️⃣ Har birini bu yerga <b>Forward</b> qiling\n"
        "4️⃣ Tugagach <b>✅ Tayyor</b> bosing\n\n"
        "⚠️ <b>Faqat Quiz turi qabul qilinadi!</b>",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.waiting_polls)


@router.message(F.poll, CreateTest.waiting_polls)
async def catch_poll(message: Message, state: FSMContext):
    uid = message.from_user.id
    _track_msg(uid, message.message_id)
    poll = message.poll

    if poll.type != "quiz":
        m = await message.answer("❌ Faqat Quiz turini yuboring!")
        _track_msg(uid, m.message_id)
        return

    data = await state.get_data()
    questions = data.get("questions", [])
    letters = ["A)", "B)", "C)", "D)", "E)", "F)", "G)", "H)", "I)", "J)"]
    options = [f"{letters[i]} {opt.text}" for i, opt in enumerate(poll.options)]

    questions.append({
        "type": "multiple_choice",
        "question": poll.question,
        "text": poll.question,
        "options": options,
        "correct": poll.correct_option_id,
        "explanation": poll.explanation or "",
        "points": 1,
        "source": "poll",
    })
    await state.update_data(questions=questions)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Tayyor — davom etish", callback_data="finish_polls"))

    m = await message.answer(
        f"✅ <b>Savol qo'shildi!</b> Jami: <b>{len(questions)} ta</b>",
        reply_markup=builder.as_markup()
    )
    _track_msg(uid, m.message_id)


@router.callback_query(F.data == "finish_polls", CreateTest.waiting_polls)
async def finish_polls(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    questions = data.get("questions", [])
    if not questions:
        return await callback.answer("❌ Kamida 1 ta poll yuboring!", show_alert=True)

    # ── KALIT tugmasi — savollarni ko'rish ──
    await callback.message.edit_text(
        f"<b>✅ {len(questions)} TA SAVOL TAYYOR!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔑 <b>Kalitni ko'rish va tahrirlash</b> — Web App da savollarni\n"
        f"   ko'rib chiqing, xato bo'lsa tuzating\n\n"
        f"✅ <b>Saqlash</b> — to'g'ridan fan va nom kiriting",
        reply_markup=after_parse_keyboard(questions)
    )
    await state.set_state(CreateTest.set_subject)


@router.callback_query(F.data == "download_draft_txt")
async def download_draft_txt(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏳ Tayyorlanmoqda...")
    data = await state.get_data()
    questions = data.get("questions", [])
    if not questions:
        return await callback.answer("❌ Savollar yo'q!", show_alert=True)

    fake_test = {"title": "Qoralama", "questions": questions, "test_id": "DRAFT"}
    from handlers.profile import _test_to_txt
    txt = _test_to_txt(fake_test)
    doc = BufferedInputFile(txt.encode("utf-8"), filename="qoralama_savollar.txt")
    await callback.message.answer_document(doc, caption=f"📄 {len(questions)} ta savol")


@router.callback_query(F.data == "proceed_to_subject")
async def proceed_to_subject(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "<b>📁 FANNI TANLANG</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Test qaysi fanga tegishli?",
        reply_markup=create_subject_keyboard()
    )


@router.callback_query(F.data.startswith("set_subj_"), CreateTest.set_subject)
async def set_subject_cb(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    subj = callback.data[9:]
    if subj == "other":
        await callback.message.edit_text(
            "<b>✏️ Fan nomini yozing:</b>\n<i>(Masalan: Tabiiy fanlar)</i>"
        )
    else:
        await state.update_data(category=subj)
        await callback.message.edit_text(
            f"<b>🏷 TEST NOMI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\nFan: <b>{subj}</b>\n\nTest mavzusini yozing:"
        )
        await state.set_state(CreateTest.set_title)


@router.message(F.text, CreateTest.set_subject)
async def set_subject_manual(message: Message, state: FSMContext):
    uid = message.from_user.id
    _track_msg(uid, message.message_id)
    await state.update_data(category=message.text.strip())
    m = await message.answer("<b>🏷 TEST NOMI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\nTest mavzusini yozing:")
    _track_msg(uid, m.message_id)
    await state.set_state(CreateTest.set_title)


@router.message(F.text, CreateTest.set_title)
async def set_title(message: Message, state: FSMContext):
    uid = message.from_user.id
    _track_msg(uid, message.message_id)
    await state.update_data(title=message.text.strip())

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌍 Ommaviy",       callback_data="vis_public"))
    builder.row(InlineKeyboardButton(text="🔗 Ssilka orqali", callback_data="vis_link"))
    builder.row(InlineKeyboardButton(text="🔒 Shaxsiy",        callback_data="vis_private"))
    builder.row(InlineKeyboardButton(text="❌ Bekor",           callback_data="cancel_creation"))

    m = await message.answer(
        f"<b>🔒 TEST MAXFIYLIGI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Mavzu: <b>{message.text.strip()}</b>\n\nKo'rinishini tanlang:",
        reply_markup=builder.as_markup()
    )
    _track_msg(uid, m.message_id)
    await state.set_state(CreateTest.set_visibility)


@router.callback_query(F.data.startswith("vis_"), CreateTest.set_visibility)
async def save_test_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏳ Saqlanmoqda...")
    data = await state.get_data()
    visibility = callback.data[4:]
    uid = callback.from_user.id
    chat_id = callback.message.chat.id

    test_data = {
        "title": data.get("title", "Nomsiz"),
        "category": data.get("category", "Boshqa"),
        "difficulty": "medium",
        "time_limit": 0,
        "poll_time": data.get("poll_time", 30),
        "passing_score": 60,
        "max_attempts": 0,
        "visibility": visibility,
        "questions": data.get("questions", []),
    }
    tid = create_test(uid, test_data)
    bot_user = await callback.bot.me()
    link = f"https://t.me/{bot_user.username}?start={tid}"
    await state.clear()

    _track_msg(uid, callback.message.message_id)
    await _clear_upload_msgs(callback.bot, uid, chat_id)

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

    # Kalit javoblar xabari
    qs = test_data["questions"]
    LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    keys = f"🔑 <b>{test_data['title'].upper()} — JAVOBLAR KALITI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, q in enumerate(qs):
        corr = q.get("correct", "?")
        if isinstance(corr, int) and corr < len(LETTERS):
            corr_str = LETTERS[corr]
        elif isinstance(corr, list):
            corr_str = ", ".join(
                LETTERS[c] if isinstance(c, int) and c < len(LETTERS) else str(c)
                for c in corr
            )
        else:
            corr_str = str(corr)
        keys += f"<b>{i + 1}.</b> {corr_str}\n"

    key_builder = InlineKeyboardBuilder()
    key_builder.row(InlineKeyboardButton(text="✉️ Kalit yashirish", callback_data="hide_key_msg"))

    if len(keys) > 4000:
        from handlers.profile import _test_to_txt
        txt = _test_to_txt(test_data)
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


@router.callback_query(F.data == "hide_key_msg")
async def hide_key_msg(callback: CallbackQuery):
    await callback.answer("🔒 Kalit yashirildi")
    uid = callback.from_user.id
    _key_msgs.pop(uid, None)
    try:
        await callback.message.delete()
    except Exception:
        pass


@router.callback_query(F.data == "noop")
async def noop_cb(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "cancel_creation")
async def cancel_creation(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    chat_id = callback.message.chat.id
    await state.clear()
    await callback.answer()
    _track_msg(uid, callback.message.message_id)
    await _clear_upload_msgs(callback.bot, uid, chat_id)
    await callback.bot.send_message(
        uid, "❌ Test yaratish bekor qilindi.",
        reply_markup=main_reply_keyboard(uid)
    )

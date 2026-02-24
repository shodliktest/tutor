"""
➕ TEST YARATISH HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Bosqichlar: Fayl -> Fan -> Qiyinlik -> Vaqt -> O'tish foizi -> Urinishlar -> Maxfiylik -> Saqlash
"""
import os
import logging
import uuid
import tempfile
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from utils.parser import parse_file
from utils.states import CreateTest
from keyboards.keyboards import difficulty_keyboard, test_visibility_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)
router = Router()

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "samples")

SAMPLE_FILES = {
    "multiple_choice": ("multiple_choice_namuna.txt", "🔘 Bir javobli test"),
    "multi_select":    ("multi_select_namuna.txt",    "☑️ Ko'p javobli test"),
    "true_false":      ("true_false_namuna.txt",      "✅ Ha/Yo'q testi"),
    "text_input":      ("text_input_namuna.txt",      "✍️ Yozma javob testi"),
    "matching":        ("matching_namuna.txt",         "🔗 Moslashtirish testi"),
    "ordering":        ("ordering_namuna.txt",         "🔢 Tartiblash testi"),
    "fill_blank":      ("fill_blank_namuna.txt",       "📝 Bo'sh joy testi"),
    "all":             ("barcha_turlar_namuna.txt",    "📦 Barcha test turlari"),
}

# ==========================================
# 1-BOSQICH: BOSHLASH VA NAMUNALAR
# ==========================================
@router.callback_query(F.data == "create_test")
async def create_test_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📂 Namuna fayllarni ko'rish", callback_data="show_samples"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    await callback.message.edit_text(
        "📝 <b>TEST YARATISH</b>\n\n"
        "Iltimos, test savollari bor TXT, DOCX yoki PDF faylni yuboring.\n"
        "Fayl formati qanday bo'lishini bilmasangiz, namunalarni ko'ring.",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.upload_file)

@router.callback_query(F.data == "show_samples", CreateTest.upload_file)
async def show_samples_handler(callback: CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    
    for key, (filename, btn_text) in SAMPLE_FILES.items():
        builder.row(InlineKeyboardButton(text=btn_text, callback_data=f"sample_{key}"))
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="create_test"))
    
    await callback.message.edit_text(
        "📂 <b>NAMUNA FAYLLAR</b>\n\nQaysi turdagi test namunasini yuklab olmoqchisiz?",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("sample_"), CreateTest.upload_file)
async def send_sample_file(callback: CallbackQuery):
    await callback.answer()
    key = callback.data.replace("sample_", "")
    filename = SAMPLE_FILES[key][0]
    file_path = os.path.join(SAMPLES_DIR, filename)
    
    if os.path.exists(file_path):
        sample_doc = FSInputFile(file_path, filename=filename)
        await callback.message.answer_document(
            document=sample_doc,
            caption="📄 Namuna fayl. Shunga o'xshatib o'z faylingizni tayyorlang va menga yuboring."
        )
    else:
        await callback.message.answer("❌ Fayl topilmadi. Tizim administratoriga murojaat qiling.")

# ==========================================
# 2-BOSQICH: FAYLNI O'QISH VA PARSING
# ==========================================
@router.message(F.document, CreateTest.upload_file)
async def upload_file_handler(message: Message, state: FSMContext):
    doc = message.document
    if not doc.file_name.lower().endswith(('.txt', '.pdf', '.docx')):
        await message.answer("❌ Faqat TXT, PDF yoki DOCX fayllar qabul qilinadi!")
        return

    status_msg = await message.answer("⏳ Fayl o'qilmoqda, kuting...")
    
    try:
        file = await message.bot.get_file(doc.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{doc.file_name}") as tmp_file:
            await message.bot.download_file(file.file_path, tmp_file.name)
            tmp_path = tmp_file.name
        
        try:
            questions = parse_file(tmp_path)
        finally:
            os.remove(tmp_path) 
            
        if not questions:
            await status_msg.edit_text("❌ Fayldan hech qanday savol topilmadi. Namuna formatini tekshiring.")
            return
            
        await state.update_data(questions=questions)
        
        await status_msg.edit_text(
            f"✅ <b>{len(questions)} ta savol topildi!</b>\n\n"
            f"📝 <b>Test nomini (Fan) kiriting:</b>\n"
            f"<i>Masalan: Tarix - Qadimiy dunyo</i>"
        )
        await state.set_state(CreateTest.set_subject)

    except Exception as e:
        logger.error(f"Faylni o'qishda xato: {e}")
        await status_msg.edit_text("❌ Faylni o'qishda xatolik yuz berdi. Iltimos, namunadagi formatdan foydalaning.")

# ==========================================
# 3-BOSQICH: FAN NOMI
# ==========================================
@router.message(F.text, CreateTest.set_subject)
async def set_subject_handler(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        "✅ Nomi saqlandi.\n\nEndi testning <b>qiyinlik darajasini</b> tanlang:",
        reply_markup=difficulty_keyboard()
    )
    await state.set_state(CreateTest.set_difficulty)

# ==========================================
# 4-BOSQICH: QIYINLIK DARAJASI
# ==========================================
@router.callback_query(F.data.startswith("diff_"), CreateTest.set_difficulty)
async def set_difficulty_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    difficulty = callback.data.replace("diff_", "")
    await state.update_data(difficulty=difficulty)
    
    await callback.message.edit_text(
        "✅ Qiyinlik darajasi tanlandi.\n\n"
        "⏱ <b>Test ishlash uchun vaqt limitini kiriting (daqiqalarda):</b>\n"
        "<i>(Masalan: 30) Agar cheklanmagan bo'lsa 0 yozing.</i>"
    )
    await state.set_state(CreateTest.set_time_limit)

# ==========================================
# 5-BOSQICH: VAQT LIMITI
# ==========================================
@router.message(F.text, CreateTest.set_time_limit)
async def set_time_limit_handler(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, faqat raqam kiriting (masalan: 30).")
        return
        
    await state.update_data(time_limit=int(message.text))
    
    await message.answer(
        "✅ Vaqt belgilandi.\n\n"
        "🎯 <b>Testdan muvaffaqiyatli o'tish foizini kiriting (0-100):</b>\n"
        "<i>(Masalan: 60) Foydalanuvchi shu foizni yig'sa Sertifikat oladi.</i>"
    )
    await state.set_state(CreateTest.set_passing_score)

# ==========================================
# 6-BOSQICH: O'TISH FOIZI
# ==========================================
@router.message(F.text, CreateTest.set_passing_score)
async def set_passing_score_handler(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (0 <= int(message.text) <= 100):
        await message.answer("❌ Iltimos, 0 dan 100 gacha bo'lgan raqam kiriting.")
        return
        
    await state.update_data(passing_score=int(message.text))
    
    await message.answer(
        "✅ O'tish foizi belgilandi.\n\n"
        "🔄 <b>Foydalanuvchi ushbu testni necha marta ishlashiga ruxsat berasiz?</b>\n"
        "<i>(Masalan: 3) Agar cheklanmagan bo'lsa 0 yozing.</i>"
    )
    await state.set_state(CreateTest.set_max_attempts)

# ==========================================
# 7-BOSQICH: URINISHLAR SONI
# ==========================================
@router.message(F.text, CreateTest.set_max_attempts)
async def set_max_attempts_handler(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, faqat raqam kiriting.")
        return
        
    await state.update_data(max_attempts=int(message.text))
    
    await message.answer(
        "✅ Urinishlar soni saqlandi.\n\n"
        "🔒 <b>Test maxfiyligini tanlang:</b>\n"
        "<i>Bu orqali test kimlarga ko'rinishini belgilaysiz.</i>",
        reply_markup=test_visibility_keyboard()
    )
    await state.set_state(CreateTest.set_visibility)

# ==========================================
# 8-BOSQICH: MAXFIYLIK VA BAZAGA SAQLASH
# ==========================================
@router.callback_query(F.data.startswith("vis_"), CreateTest.set_visibility)
async def set_visibility_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏳ Bazaga saqlanmoqda...")
    visibility = callback.data.replace("vis_", "") # public, link, private
    
    data = await state.get_data()
    questions = data.get("questions", [])
    
    from firebase.config import get_db
    db = get_db()
    test_id = str(uuid.uuid4())[:8]
    
    new_test = {
        "test_id": test_id,
        "title": data.get("title", "Nomsiz test"),
        "creator_id": callback.from_user.id,
        "difficulty": data.get("difficulty", "medium"),
        "time_limit": data.get("time_limit", 0),
        "passing_score": data.get("passing_score", 60),
        "max_attempts": data.get("max_attempts", 0),
        "visibility": visibility,
        "questions": questions,
        "created_at": datetime.now(timezone.utc),
        "solve_count": 0,
        "category": "Boshqa" 
    }
    
    # Firebase ga yozish
    db.collection("tests").document(test_id).set(new_test)
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu"))
    
    visibility_text = {
        "public": "🌍 Ommaviy (Katalogda ko'rinadi)",
        "link": "🔗 Ssilka orqali (Faqat link yuborganlaringiz ko'radi)",
        "private": "🔒 Shaxsiy (Faqat o'zingiz ko'rasiz)"
    }
    
    await callback.message.edit_text(
        f"🎉 <b>TEST MUVAFFAQIYATLI YARATILDI!</b>\n\n"
        f"<b>Test kodi:</b> <code>{test_id}</code>\n"
        f"<b>Test ssilkasi:</b> <code>https://t.me/{(await callback.bot.me()).username}?start={test_id}</code>\n\n"
        f"📊 <b>Ma'lumotlar:</b>\n"
        f"• Savollar: {len(questions)} ta\n"
        f"• Vaqt: {data.get('time_limit')} daqiqa\n"
        f"• O'tish: {data.get('passing_score')}%\n"
        f"• Urinishlar: {data.get('max_attempts')} marta\n"
        f"• Holat: {visibility_text[visibility]}\n\n"
        f"<i>Ssilkani nusxalab o'quvchilarga yuborishingiz mumkin.</i>",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "cancel_creation")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu"))
    await callback.message.edit_text("❌ Test yaratish bekor qilindi.", reply_markup=builder.as_markup())

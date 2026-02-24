"""
➕ TEST YARATISH HANDLER (AIOGRAM 3)
Fayl yuklash -> Fan nomi -> Qiyinlik -> Bazaga saqlash
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
from keyboards.keyboards import difficulty_keyboard
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

@router.callback_query(F.data == "create_test")
async def create_test_start(callback: CallbackQuery, state: FSMContext):
    """Test yaratishni boshlash"""
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
    """Namuna fayllar ro'yxatini ko'rsatish"""
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
    """Tanlangan namunani yuborish"""
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

@router.message(F.document, CreateTest.upload_file)
async def upload_file_handler(message: Message, state: FSMContext):
    """Foydalanuvchi fayl yuborganda uni o'qish va tahlil qilish"""
    doc = message.document
    if not doc.file_name.lower().endswith(('.txt', '.pdf', '.docx')):
        await message.answer("❌ Faqat TXT, PDF yoki DOCX fayllar qabul qilinadi!")
        return

    status_msg = await message.answer("⏳ Fayl o'qilmoqda...")
    
    try:
        # Faylni vaqtinchalik xotiraga yuklab olish
        file = await message.bot.get_file(doc.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{doc.file_name}") as tmp_file:
            await message.bot.download_file(file.file_path, tmp_file.name)
            tmp_path = tmp_file.name
        
        try:
            # utils.parser dagi parse_file chaqiriladi
            questions = parse_file(tmp_path)
        finally:
            os.remove(tmp_path) # Faylni darhol o'chiramiz (RAM tejamkorligi)
            
        if not questions:
            await status_msg.edit_text("❌ Fayldan hech qanday savol topilmadi. Namuna formatini tekshiring.")
            return
            
        await state.update_data(questions=questions)
        
        await status_msg.edit_text(
            f"✅ <b>{len(questions)} ta savol topildi!</b>\n\n"
            f"📝 <b>Test nomini (Fan) kiriting:</b>\n"
            f"<i>Masalan: Matematika - Algebra</i>"
        )
        await state.set_state(CreateTest.set_subject)

    except Exception as e:
        logger.error(f"Faylni o'qishda xato: {e}")
        await status_msg.edit_text("❌ Faylni o'qishda xatolik yuz berdi. Iltimos, faqat namunadagi formatdan foydalaning.")

@router.message(F.text, CreateTest.set_subject)
async def set_subject_handler(message: Message, state: FSMContext):
    """Fan nomini qabul qilish"""
    subject = message.text
    await state.update_data(title=subject)
    
    await message.answer(
        "✅ Nomi saqlandi.\n\nEndi testning <b>qiyinlik darajasini</b> tanlang:",
        reply_markup=difficulty_keyboard()
    )
    await state.set_state(CreateTest.set_difficulty)

@router.callback_query(F.data.startswith("diff_"), CreateTest.set_difficulty)
async def set_difficulty_handler(callback: CallbackQuery, state: FSMContext):
    """Qiyinlik darajasini tanlab, testni to'liq bazaga saqlash"""
    await callback.answer()
    difficulty = callback.data.replace("diff_", "")
    
    data = await state.get_data()
    questions = data.get("questions", [])
    title = data.get("title", "Nomsiz test")
    
    from firebase.config import get_db
    db = get_db()
    test_id = str(uuid.uuid4())[:8]
    
    new_test = {
        "test_id": test_id,
        "title": title,
        "creator_id": callback.from_user.id,
        "difficulty": difficulty,
        "questions": questions,
        "created_at": datetime.now(timezone.utc),
        "solve_count": 0,
        "passing_score": 60,
        "category": "Boshqa" 
    }
    
    # Bazaga yozish
    db.collection("tests").document(test_id).set(new_test)
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu"))
    
    await callback.message.edit_text(
        f"🎉 <b>TEST MUVAFFAQIYATLI YARATILDI!</b>\n\n"
        f"Test kodi: <code>{test_id}</code>\n"
        f"Savollar soni: {len(questions)} ta",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "cancel_creation")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    """Jarayonni bekor qilish"""
    await state.clear()
    await callback.answer()
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu"))
    
    await callback.message.edit_text("❌ Test yaratish bekor qilindi.", reply_markup=builder.as_markup())

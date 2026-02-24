"""
➕ TEST YARATISH HANDLER
Fayl yuklash va qo'lda test yaratish
"""
import os
import logging
import tempfile
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from firebase.db import create_test, get_user
from firebase.config import get_bucket
from utils.parser import parse_file
from utils.states import *
from keyboards.keyboards import (
    upload_method_keyboard, subjects_keyboard,
    difficulty_keyboard, visibility_keyboard
)
from config import SUBJECTS

logger = logging.getLogger(__name__)


# Namuna fayllar joylashgan papka
SAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "samples")


async def create_test_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test yaratishni boshlash"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = get_user(user_id)
    
    # Rol tekshirish
    if user and user.get("role") not in ["admin", "teacher", "user"]:
        await query.message.edit_text("🚫 Sizda test yaratish huquqi yo'q.")
        return ConversationHandler.END
    
    text = """
➕ <b>TEST YARATISH</b>

Test yaratishning 2 usuli mavjud:

📁 <b>Fayl yuklash</b> — TXT, PDF yoki DOCX fayl yuklang
✏️ <b>Qo'lda yaratish</b> — Savollarni bitta-bitta kiriting

📋 <b>Namuna fayllar</b> — Har bir test turi uchun tayyor shablon

Qaysi usulni tanlaysiz?
"""
    
    await query.message.edit_text(text, reply_markup=upload_method_keyboard(), parse_mode="HTML")
    return UPLOAD_FILE


async def upload_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Faylni qabul qilish va parse qilish"""
    document = update.message.document
    
    if not document:
        await update.message.reply_text("❌ Fayl yuklanmadi. Iltimos fayl yuboring.")
        return UPLOAD_FILE
    
    # Fayl turi tekshirish
    file_name = document.file_name.lower()
    if not any(file_name.endswith(ext) for ext in ['.txt', '.pdf', '.docx', '.doc']):
        await update.message.reply_text(
            "❌ Faqat TXT, PDF, DOCX formatlar qo'llab-quvvatlanadi.\n\n"
            "📋 Namuna fayllarni ko'rish uchun pastdagi tugmani bosing.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📋 Namunalar", callback_data="show_samples")
            ]])
        )
        return UPLOAD_FILE
    
    # Fayl hajmi tekshirish (20MB)
    if document.file_size > 20 * 1024 * 1024:
        await update.message.reply_text("❌ Fayl hajmi 20MB dan oshmasin.")
        return UPLOAD_FILE
    
    status_msg = await update.message.reply_text("⏳ Fayl yuklanmoqda va tahlil qilinmoqda...")
    
    try:
        # Faylni yuklab olish
        file = await context.bot.get_file(document.file_id)
        
        with tempfile.NamedTemporaryFile(
            suffix=os.path.splitext(file_name)[1],
            delete=False
        ) as tmp_file:
            tmp_path = tmp_file.name
        
        await file.download_to_drive(tmp_path)
        
        # Parse qilish
        questions = parse_file(tmp_path)
        os.unlink(tmp_path)  # Vaqtinchalik faylni o'chirish
        
        if not questions:
            await status_msg.edit_text(
                "❌ Savollar topilmadi!\n\n"
                "Fayl formati noto'g'ri bo'lishi mumkin.\n"
                "📋 Namuna fayllarni ko'ring va shu formatda yozing.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📋 Namunalarni ko'rish", callback_data="show_samples")
                ]])
            )
            return UPLOAD_FILE
        
        # Natijani saqlash
        context.user_data["new_test"] = {
            "questions": questions,
            "question_count": len(questions),
            "file_name": file_name
        }
        
        # Statistika
        types_count = {}
        for q in questions:
            t = q.get("type", "unknown")
            types_count[t] = types_count.get(t, 0) + 1
        
        types_text = "\n".join([f"  • {k}: {v} ta" for k, v in types_count.items()])
        
        await status_msg.edit_text(
            f"✅ <b>{len(questions)} ta savol topildi!</b>\n\n"
            f"📊 Savol turlari:\n{types_text}\n\n"
            f"Endi test ma'lumotlarini kiriting:",
            parse_mode="HTML"
        )
        
        # Fan tanlash
        await _ask_title(update.message, context)
        return SET_SUBJECT
        
    except Exception as e:
        logger.error(f"Fayl parse xatosi: {e}")
        await status_msg.edit_text(
            f"❌ Xatolik yuz berdi: {str(e)[:100]}\n\n"
            "Fayl formatini tekshiring va qayta urinib ko'ring."
        )
        return UPLOAD_FILE


async def _ask_title(message, context):
    """Test nomini so'rash"""
    await message.reply_text(
        "📝 <b>Test nomini kiriting:</b>\n\n"
        "Masalan: <i>Matematika - Algebra bo'limi</i>",
        parse_mode="HTML"
    )


async def show_samples_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Namuna fayllarni yuborish"""
    query = update.callback_query
    if query:
        await query.answer()
    
    text = """
📋 <b>NAMUNA FAYLLAR</b>

Har bir test turi uchun tayyor shablon tanlang:
"""
    
    keyboard = [
        [InlineKeyboardButton("🔘 Bir javobli (Multiple Choice)", callback_data="sample_multiple_choice")],
        [InlineKeyboardButton("☑️ Ko'p javobli (Multi-Select)", callback_data="sample_multi_select")],
        [InlineKeyboardButton("✅ Ha/Yo'q (True/False)", callback_data="sample_true_false")],
        [InlineKeyboardButton("✍️ Yozma javob (Text Input)", callback_data="sample_text_input")],
        [InlineKeyboardButton("🔗 Moslashtirish (Matching)", callback_data="sample_matching")],
        [InlineKeyboardButton("🔢 Tartiblash (Ordering)", callback_data="sample_ordering")],
        [InlineKeyboardButton("📝 Bo'sh joy (Fill in Blank)", callback_data="sample_fill_blank")],
        [InlineKeyboardButton("📦 Barcha turlar (1 fayl)", callback_data="sample_all")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="create_test")]
    ]
    
    if query:
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def send_sample_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tanlangan namuna faylni yuborish"""
    query = update.callback_query
    await query.answer()
    
    sample_type = query.data.replace("sample_", "")
    
    sample_files = {
        "multiple_choice": "multiple_choice_namuna.txt",
        "multi_select": "multi_select_namuna.txt",
        "true_false": "true_false_namuna.txt",
        "text_input": "text_input_namuna.txt",
        "matching": "matching_namuna.txt",
        "ordering": "ordering_namuna.txt",
        "fill_blank": "fill_blank_namuna.txt",
        "all": "barcha_turlar_namuna.txt"
    }
    
    file_name = sample_files.get(sample_type)
    if not file_name:
        await query.message.reply_text("❌ Namuna fayl topilmadi.")
        return
    
    file_path = os.path.join(SAMPLES_DIR, file_name)
    
    if not os.path.exists(file_path):
        await query.message.reply_text("❌ Namuna fayl mavjud emas.")
        return
    
    type_names = {
        "multiple_choice": "🔘 Bir javobli test",
        "multi_select": "☑️ Ko'p javobli test",
        "true_false": "✅ Ha/Yo'q testi",
        "text_input": "✍️ Yozma javob testi",
        "matching": "🔗 Moslashtirish testi",
        "ordering": "🔢 Tartiblash testi",
        "fill_blank": "📝 Bo'sh joy testi",
        "all": "📦 Barcha test turlari"
    }
    
    caption = f"""
📋 <b>{type_names.get(sample_type, 'Namuna')} — Shablon</b>

Bu faylni yuklab oling, to'ldiring va bot ga yuboring.

⚠️ <b>Muhim:</b>
• Fayl formatini o'zgartirmang
• [TO'G'RI] belgisini to'g'ri joyga qo'ying
• TYPE: qatorini o'chirmang
• Izoh (Izoh:) ixtiyoriy
"""
    
    with open(file_path, 'rb') as f:
        await query.message.reply_document(
            document=f,
            filename=file_name,
            caption=caption,
            parse_mode="HTML"
        )


async def manual_create_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Qo'lda test yaratish"""
    query = update.callback_query
    if query:
        await query.answer()
    
    context.user_data["new_test"] = {
        "questions": [],
        "manual_mode": True
    }
    
    text = """
✏️ <b>QO'LDA TEST YARATISH</b>

Savollarni bitta-bitta kiriting.

📝 <b>Format:</b>
<code>Savol matni
A) Variant 1
B) Variant 2 [TO'G'RI]
C) Variant 3
D) Variant 4
Izoh: Izohlash (ixtiyoriy)</code>

Birinchi savolingizni yozing:
"""
    
    if query:
        await query.message.edit_text(text, parse_mode="HTML")
    else:
        await update.message.reply_text(text, parse_mode="HTML")
    
    return MANUAL_QUESTION

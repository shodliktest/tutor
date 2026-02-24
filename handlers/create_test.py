"""
➕ TEST YARATISH HANDLER
"""
import os
import logging
import tempfile
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from firebase.db import create_test, get_user
from utils.parser import parse_file
from utils.states import *
from keyboards.keyboards import upload_method_keyboard, subjects_keyboard
from config import SUBJECTS

logger = logging.getLogger(__name__)

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


# ══════════════════════════════════════════════════════════
# TEST YARATISHNI BOSHLASH
# ══════════════════════════════════════════════════════════
async def create_test_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "➕ <b>TEST YARATISH</b>\n\n"
        "📁 <b>Fayl yuklash</b> — TXT, PDF yoki DOCX yuklang\n"
        "✏️ <b>Qo'lda yaratish</b> — Savollarni bitta-bitta kiriting\n"
        "📋 <b>Namuna fayllar</b> — Har bir test turi uchun tayyor shablon\n\n"
        "Qaysi usulni tanlaysiz?"
    )
    await query.message.edit_text(text, reply_markup=upload_method_keyboard(), parse_mode="HTML")
    return UPLOAD_FILE


# ══════════════════════════════════════════════════════════
# NAMUNA FAYLLAR — RO'YXAT
# ══════════════════════════════════════════════════════════
async def show_samples_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🔘 Bir javobli",     callback_data="sample_multiple_choice")],
        [InlineKeyboardButton("☑️ Ko'p javobli",    callback_data="sample_multi_select")],
        [InlineKeyboardButton("✅ Ha/Yo'q",          callback_data="sample_true_false")],
        [InlineKeyboardButton("✍️ Yozma javob",     callback_data="sample_text_input")],
        [InlineKeyboardButton("🔗 Moslashtirish",   callback_data="sample_matching")],
        [InlineKeyboardButton("🔢 Tartiblash",      callback_data="sample_ordering")],
        [InlineKeyboardButton("📝 Bo'sh joy",        callback_data="sample_fill_blank")],
        [InlineKeyboardButton("📦 Barcha turlar",   callback_data="sample_all")],
        [InlineKeyboardButton("◀️ Orqaga",          callback_data="create_test")],
    ]
    await query.message.edit_text(
        "📋 <b>NAMUNA FAYLLAR</b>\n\nQaysi test turi uchun shablon kerak?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# ══════════════════════════════════════════════════════════
# NAMUNA FAYL YUBORISH
# ══════════════════════════════════════════════════════════
async def send_sample_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    sample_type = query.data.replace("sample_", "")
    info = SAMPLE_FILES.get(sample_type)

    if not info:
        await query.message.reply_text("❌ Namuna topilmadi.")
        return

    file_name, type_label = info
    file_path = os.path.join(SAMPLES_DIR, file_name)

    if not os.path.exists(file_path):
        await query.message.reply_text(
            f"❌ Fayl topilmadi: {file_name}\n"
            f"Repo da samples/ papkasi borligini tekshiring."
        )
        return

    caption = (
        f"📋 <b>{type_label} — Shablon</b>\n\n"
        f"Bu faylni yuklab oling, to'ldiring va botga yuboring.\n\n"
        f"<b>Muhim qoidalar:</b>\n"
        f"• [TO'G'RI] belgisini to'g'ri javob oldiga qo'ying\n"
        f"• TYPE: qatorini o'chirmang\n"
        f"• Izoh: ixtiyoriy maydon"
    )

    with open(file_path, "rb") as f:
        await query.message.reply_document(
            document=f,
            filename=file_name,
            caption=caption,
            parse_mode="HTML"
        )


# ══════════════════════════════════════════════════════════
# FAYL YUKLASH VA PARSE
# ══════════════════════════════════════════════════════════
async def upload_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if not document:
        await update.message.reply_text("❌ Fayl yuklanmadi.")
        return UPLOAD_FILE

    file_name = document.file_name.lower()
    if not any(file_name.endswith(ext) for ext in [".txt", ".pdf", ".docx", ".doc"]):
        await update.message.reply_text(
            "❌ Faqat TXT, PDF, DOCX formatlar qo'llab-quvvatlanadi.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📋 Namunalarni ko'rish", callback_data="show_samples")
            ]])
        )
        return UPLOAD_FILE

    if document.file_size > 20 * 1024 * 1024:
        await update.message.reply_text("❌ Fayl hajmi 20MB dan oshmasin.")
        return UPLOAD_FILE

    status_msg = await update.message.reply_text("⏳ Fayl tahlil qilinmoqda...")

    try:
        file = await context.bot.get_file(document.file_id)
        suffix = os.path.splitext(file_name)[1]

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name

        await file.download_to_drive(tmp_path)
        questions = parse_file(tmp_path)
        os.unlink(tmp_path)

        if not questions:
            await status_msg.edit_text(
                "❌ Savollar topilmadi! Fayl formatini tekshiring.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📋 Namunalarni ko'rish", callback_data="show_samples")
                ]])
            )
            return UPLOAD_FILE

        context.user_data["new_test"] = {
            "questions": questions,
            "question_count": len(questions),
            "file_name": file_name
        }

        types_count = {}
        for q in questions:
            t = q.get("type", "unknown")
            types_count[t] = types_count.get(t, 0) + 1
        types_text = "\n".join(f"  • {k}: {v} ta" for k, v in types_count.items())

        await status_msg.edit_text(
            f"✅ <b>{len(questions)} ta savol topildi!</b>\n\n"
            f"📊 Turlari:\n{types_text}\n\n"
            f"Endi test nomini kiriting:",
            parse_mode="HTML"
        )

        await update.message.reply_text(
            "📝 <b>Test nomini kiriting:</b>\n"
            "<i>Masalan: Matematika - Algebra</i>",
            parse_mode="HTML"
        )
        return SET_SUBJECT

    except Exception as e:
        logger.error(f"Parse xato: {e}")
        await status_msg.edit_text(f"❌ Xatolik: {str(e)[:150]}")
        return UPLOAD_FILE


# ══════════════════════════════════════════════════════════
# QO'LDA YARATISH
# ══════════════════════════════════════════════════════════
async def manual_create_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    context.user_data["new_test"] = {"questions": [], "manual_mode": True}

    text = (
        "✏️ <b>QO'LDA TEST YARATISH</b>\n\n"
        "Savol formatini ko'rish uchun namuna fayllarni yuklab oling.\n\n"
        "Birinchi savolingizni yozing:\n\n"
        "<code>Savol matni?\n"
        "A) Variant 1\n"
        "B) Variant 2 [TO'G'RI]\n"
        "C) Variant 3\n"
        "D) Variant 4\n"
        "Izoh: Tushuntirish</code>"
    )

    if query:
        await query.message.edit_text(text, parse_mode="HTML")
    else:
        await update.message.reply_text(text, parse_mode="HTML")

    return MANUAL_QUESTION
            

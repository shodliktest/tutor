"""
🚀 START HANDLER
"""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from firebase.db import get_user, create_user
from keyboards.keyboards import main_menu_keyboard
import logging

logger = logging.getLogger(__name__)


async def _reply(update: Update, text: str, **kwargs):
    """update.message yoki callback_query ga qarab javob beradi"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, **kwargs)
    elif update.message:
        await update.message.reply_text(text, **kwargs)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user  = update.effective_user
    tg_id = user.id

    db_user = get_user(tg_id)

    if not db_user:
        create_user(telegram_id=tg_id, name=user.full_name, username=user.username)
        greeting = f"👋 Xush kelibsiz, <b>{user.first_name}</b>!\n\n🎓 Quiz Bot ga xush kelibsiz!"
        logger.info(f"Yangi foydalanuvchi: {tg_id} - {user.full_name}")
    else:
        if db_user.get("is_blocked"):
            await _reply(update, "🚫 Siz bloklangansiz. Admin bilan bog'laning.")
            return
        greeting = f"👋 Qaytib keldingiz, <b>{user.first_name}</b>!"

    # Deep link
    if context.args:
        from handlers.tests import show_test_info
        await show_test_info(update, context, context.args[0])
        return

    welcome_text = (
        f"{greeting}\n\n"
        f"🎯 <b>QUIZ BOT</b> — Professional Test Platformasi\n\n"
        f"📚 <b>Nima qila olasiz?</b>\n"
        f"• Turli fanlar bo'yicha testlar ishlash\n"
        f"• O'z testingizni yaratish va ulashish\n"
        f"• Natijalaringizni kuzatish\n"
        f"• Reytingda yuqoriga chiqish\n\n"
        f"🏆 <b>Xususiyatlar:</b>\n"
        f"✅ 7 turdagi test formati\n"
        f"✅ Batafsil tahlil va izohlar\n"
        f"✅ Leaderboard va reyting\n\n"
        f"👇 Pastdagi menyudan boshlang:"
    )

    await _reply(update, welcome_text, reply_markup=main_menu_keyboard(), parse_mode="HTML")


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "ℹ️ <b>YORDAM</b>\n\n"
        "<b>📋 Asosiy komandalar:</b>\n"
        "/start — Bosh sahifa\n"
        "/tests — Testlar\n"
        "/results — Natijalarim\n"
        "/leaderboard — Reyting\n"
        "/profile — Profilim\n"
        "/help — Yordam\n\n"
        "<b>📁 Fayl formatlari:</b>\n"
        "• TXT, PDF, DOCX\n\n"
        "<b>🎮 Test turlari:</b>\n"
        "• 🔘 Bir javobli\n"
        "• ☑️ Ko'p javobli\n"
        "• ✅ Ha/Yo'q\n"
        "• ✍️ Yozma javob\n"
        "• 🔗 Moslashtirish\n"
        "• 🔢 Tartiblash\n"
        "• 📝 Bo'sh joy to'ldirish"
    )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏠 Bosh sahifa", callback_data="main_menu")
    ]])

    await _reply(update, help_text, parse_mode="HTML", reply_markup=keyboard)
    

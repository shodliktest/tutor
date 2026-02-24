"""
🚀 START HANDLER
Bot bilan birinchi muloqot
"""
from telegram import Update
from telegram.ext import ContextTypes
from firebase.db import get_user, create_user
from keyboards.keyboards import main_menu_keyboard
import logging

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi"""
    user = update.effective_user
    tg_id = user.id
    
    # Foydalanuvchini bazada tekshirish
    db_user = get_user(tg_id)
    
    if not db_user:
        # Yangi foydalanuvchi
        create_user(
            telegram_id=tg_id,
            name=user.full_name,
            username=user.username
        )
        greeting = f"👋 Xush kelibsiz, <b>{user.first_name}</b>!\n\n🎓 Quiz Bot ga ro'yxatdan o'tdingiz!"
        logger.info(f"Yangi foydalanuvchi: {tg_id} - {user.full_name}")
    else:
        if db_user.get("is_blocked"):
            await update.message.reply_text("🚫 Siz bloklangansiz. Admin bilan bog'laning.")
            return
        greeting = f"👋 Qaytib keldingiz, <b>{user.first_name}</b>!"
    
    # Deep link tekshirish (test linki)
    args = context.args
    if args:
        test_id = args[0]
        # Test sahifasiga yo'naltirish
        from handlers.tests import show_test_info
        await show_test_info(update, context, test_id)
        return
    
    welcome_text = f"""
{greeting}

🎯 <b>QUIZ BOT</b> — Professional Test Platformasi

📚 <b>Nima qila olasiz?</b>
• Turli fanlar bo'yicha testlar ishlash
• O'z testingizni yaratish va ulashish
• Natijalaringizni kuzatish
• Reytingda yuqoriga chiqish

🏆 <b>Xususiyatlar:</b>
✅ 7 turdagi test formati
✅ Batafsil tahlil va izohlar
✅ Leaderboard va reyting
✅ Sertifikat olish

👇 Pastdagi menyudan boshlang:
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam"""
    help_text = """
ℹ️ <b>YORDAM</b>

<b>📋 Asosiy komandalar:</b>
/start — Bosh sahifa
/tests — Testlar ro'yxati
/results — Natijalarim
/leaderboard — Reyting
/profile — Mening profilim
/admin — Admin panel (faqat adminlar)
/help — Yordam

<b>📁 Test yuklash formatlari:</b>
• TXT (.txt)
• PDF (.pdf)
• Word (.docx)

<b>🎮 Test turlari:</b>
• 🔘 Bir javobli test (Multiple Choice)
• ☑️ Ko'p javobli test (Multi-Select)
• ✅ Ha / Yo'q (True/False)
• ✍️ Yozma javob (Text Input)
• 🔗 Moslashtirish (Matching)
• 🔢 Tartiblash (Ordering)
• 📝 Bo'sh joyni to'ldirish (Fill in the Blank)

<b>📋 Namuna fayllar:</b>
Test yaratishda "Namuna fayllar" tugmasini bosing
va har bir test turi uchun tayyor shablon oling.

❓ Muammo bo'lsa: @admin_username ga yozing
"""
    
    keyboard_btn = [[{"text": "🏠 Bosh sahifa", "callback_data": "main_menu"}]]
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    await update.message.reply_text(
        help_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="main_menu")]
        ])
    )

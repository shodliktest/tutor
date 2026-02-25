"""
🚀 START HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Yangi foydalanuvchi haqida adminga xabar berish, Deep-linking va Yordam menyusi bilan.
Hech narsa qisqartirilmadi!
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from config import ADMIN_IDS
from firebase.db import get_user, create_user, get_test
from keyboards.keyboards import main_reply_keyboard, test_info_keyboard

logger = logging.getLogger(__name__)
router = Router()

# ==========================================================
# 1. /START BUYRUG'I VA RO'YXATGA OLISH
# ==========================================================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear() # Har safar start bosilganda eski holatlarni tozalaymiz
    
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = message.from_user.username
    
    # Foydalanuvchini bazadan tekshirish
    user = get_user(user_id)
    
    if not user:
        # AGAR BAZADA YO'Q BO'LSA (YANGI FOYDALANUVCHI):
        create_user(user_id, user_name, username)
        welcome_text = f"👋 Salom, <b>{user_name}</b>!\nQuiz Bot platformasiga xush kelibsiz."
        
        # 🚨 ADMINGA XABAR YUBORISH QISMI
        for admin_id in ADMIN_IDS:
            try:
                uname = f"@{username}" if username else "Yo'q"
                await message.bot.send_message(
                    chat_id=admin_id, 
                    text=f"🆕 <b>Yangi foydalanuvchi botga kirdi!</b>\n👤 Ism: {user_name}\n🔗 User: {uname}\n🆔 ID: <code>{user_id}</code>"
                )
            except Exception as e:
                logger.error(f"Adminga xabar yuborishda xatolik yuz berdi: {e}")
                
    else:
        # AGAR BAZADA BOR BO'LSA (ESKI FOYDALANUVCHI):
        welcome_text = f"🏠 Xush kelibsiz, <b>{user_name}</b>!"

    # Deep-linking tekshiruvi (t.me/bot?start=test_id)
    args = message.text.split()
    if len(args) > 1:
        test_id = args[1]
        test = get_test(test_id)
        
        if test:
            await message.answer(
                f"🔍 <b>Test topildi!</b>\n\nTest: <b>{test.get('title')}</b>", 
                reply_markup=main_reply_keyboard(user_id)
            )
            
            questions = test.get("questions", [])
            diff = test.get("difficulty", "Nomalum").title()
            
            text = (
                f"📝 <b>{test.get('title')}</b>\n\n"
                f"📋 Savollar soni: <b>{len(questions)} ta</b>\n"
                f"📊 Qiyinlik darajasi: <b>{diff}</b>\n"
                f"⏱ Vaqt limiti: <b>{test.get('time_limit', 0)} daqiqa</b>\n"
            )
            await message.answer(text, reply_markup=test_info_keyboard(test_id))
            return

    # Asosiy Menyuni yuborish (Reply Keyboard)
    await message.answer(
        f"{welcome_text}\n\nPastdagi menyudan kerakli bo'limni tanlang 👇",
        reply_markup=main_reply_keyboard(user_id)
    )

# ==========================================================
# 2. INLINE TUGMALARDAN ASOSIY MENYUGA QAYTISH
# ==========================================================

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu_cb(callback: CallbackQuery, state: FSMContext):
    """Inline tugmalardagi Asosiy menyuga qaytish bosilganda"""
    await state.clear()
    await callback.answer()
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    user_id = callback.from_user.id
    await callback.message.answer(
        "🏠 <b>Asosiy menyudasiz!</b>\nIltimos, pastdagi doimiy tugmalardan foydalaning 👇",
        reply_markup=main_reply_keyboard(user_id)
    )

# ==========================================================
# 3. YORDAM VA ADMINGA YOZISH BO'LIMI
# ==========================================================

@router.message(F.text == "ℹ️ Yordam")
async def help_handler_text(message: Message):
    """Pastdagi (Reply) Yordam tugmasi bosilganda"""
    await send_help_menu(message)

@router.callback_query(F.data == "help")
async def help_handler_cb(callback: CallbackQuery):
    """Eski xabarlardagi (Inline) Yordam tugmasi bosilganda"""
    await callback.answer()
    await send_help_menu(callback.message, is_edit=True)

async def send_help_menu(message_obj: Message, is_edit: bool = False):
    """Yordam matni va Adminga yozish tugmasini chiqaruvchi umumiy funksiya"""
    help_text = (
        "❓ <b>BOTDAN FOYDALANISH BO'YICHA YORDAM</b>\n\n"
        "1️⃣ <b>Test yechish:</b> '📚 Testlar' ni bosing, fanni tanlang.\n"
        "2️⃣ <b>Test yaratish:</b> '➕ Test Yaratish' orqali o'z faylingizni yuklang.\n"
        "3️⃣ <b>Mening testlarim:</b> O'zingiz yaratgan testlar kodini olish uchun.\n\n"
        "💬 <i>Biron savol yoki muammo bo'lsa, pastdagi tugma orqali adminga murojaat qiling:</i>"
    )
    
    # 🛡️ ADMINGA YOZISH TUGMASI
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👨‍💻 Adminga yozish", callback_data="contact_admin"))
    
    if is_edit:
        try:
            await message_obj.edit_text(help_text, reply_markup=builder.as_markup())
        except Exception:
            # Agar edit qilishni imkoni bo'lmasa, yangi xabar yuboramiz
            await message_obj.answer(help_text, reply_markup=builder.as_markup())
    else:
        await message_obj.answer(help_text, reply_markup=builder.as_markup())
            

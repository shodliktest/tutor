"""
🚀 START HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Eski qolib ketgan klaviaturalarni tozalash va yuzma-yuz (Reply) menyuni ishga tushirish.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from firebase.db import get_user, create_user, get_test
from keyboards.keyboards import main_reply_keyboard, test_info_keyboard

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = message.from_user.username
    
    user = get_user(user_id)
    if not user:
        create_user(user_id, user_name, username)
        welcome_text = f"👋 Salom, <b>{user_name}</b>!\nQuiz Bot platformasiga xush kelibsiz."
    else:
        welcome_text = f"🏠 Xush kelibsiz, <b>{user_name}</b>!"

    # Deep-linking (Ssilka orqali testga kirish)
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
            text = (
                f"📝 <b>{test.get('title')}</b>\n"
                f"📋 Savollar: <b>{len(questions)} ta</b>\n"
                f"⏱ Vaqt: <b>{test.get('time_limit', 0)} daqiqa</b>\n"
            )
            await message.answer(text, reply_markup=test_info_keyboard(test_id))
            return

    # Asosiy menyuni doimiy klaviatura orqali yuborish va eski klaviaturalarni ezib tashlash
    await message.answer(
        f"{welcome_text}\n\nPastdagi menyudan kerakli bo'limni tanlang 👇", 
        reply_markup=main_reply_keyboard(user_id)
    )

# 🛡️ Inline tugmalardagi "Bosh sahifa" bosilsa, Reply menyuga o'tkazish
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    
    # Inline xabarni o'chirib tashlaymiz (Chalg'itmasligi uchun)
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    user_id = callback.from_user.id
    await callback.message.answer(
        "🏠 <b>Asosiy menyudasiz!</b>\nIltimos, pastdagi doimiy tugmalardan foydalaning 👇",
        reply_markup=main_reply_keyboard(user_id)
    )

@router.message(F.text == "ℹ️ Yordam")
async def help_handler_text(message: Message):
    help_text = (
        "❓ <b>YORDAM BO'LIMI</b>\n\n"
        "1️⃣ <b>Test yechish:</b> '📚 Testlar' ni bosing, fanni tanlang.\n"
        "2️⃣ <b>Test yaratish:</b> '➕ Test Yaratish' orqali o'z faylingizni yuklang.\n"
        "3️⃣ <b>Mening testlarim:</b> O'zingiz yaratgan testlar kodini olish uchun.\n"
        "💡 <i>Muammo yuzaga kelsa admin bilan bog'laning.</i>"
    )
    await message.answer(help_text)
    

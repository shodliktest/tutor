"""
🚀 START HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Yangi foydalanuvchilarni ro'yxatga olish va Deep-linking (Ssilka orqali test topish) bilan.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from firebase.db import get_user, create_user, get_test
from keyboards.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()

# ==========================================================
# 1. /START KOMANDASI VA DEEP-LINKING
# ==========================================================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Botga /start bosilganda yoki t.me/bot?start=test_id orqali kirilganda
    """
    await state.clear() # Har safar start bosilganda eski holatlarni tozalaymiz
    
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = message.from_user.username
    
    # 1. Foydalanuvchini bazadan tekshirish
    user = get_user(user_id)
    if not user:
        # Yangi foydalanuvchi bo'lsa, ro'yxatga qo'shamiz
        create_user(user_id, user_name, username)
        welcome_text = f"👋 Salom, <b>{user_name}</b>!\nQuiz Bot platformasiga xush kelibsiz."
    else:
        welcome_text = f"🏠 Xush kelibsiz, <b>{user_name}</b>! Sizni yana ko'rib turganimizdan xursandmiz."

    # 2. Deep-linking tekshiruvi (t.me/bot?start=test_id)
    args = message.text.split()
    if len(args) > 1:
        test_id = args[1]
        test = get_test(test_id)
        
        if test:
            # Agar ssilka orqali test topilsa, to'g'ridan-to'g'ri test haqida ma'lumotga o'tamiz
            from handlers.tests import view_test_handler
            # view_test_handler funksiyasini chaqirish uchun soxta callback yasaymiz
            class FakeCallback:
                def __init__(self, message, data, from_user):
                    self.message = message
                    self.data = data
                    self.from_user = from_user
                async def answer(self): pass
                
            fake_cb = FakeCallback(message, f"view_test_{test_id}", message.from_user)
            # Bu yerda view_test_handler'ni import qilib ishlatishimiz mumkin
            # Lekin eng to'g'ri yo'li - foydalanuvchiga testni topdik deb xabar berish
            await message.answer(f"🔍 <b>Siz qidirgan test topildi!</b>\n\nTest: <b>{test.get('title')}</b>")
            
            # Keyboards'dan foydalanib test ma'lumotini chiqaramiz
            from keyboards.keyboards import test_info_keyboard
            questions = test.get("questions", [])
            diff = test.get("difficulty", "Nomalum").title()
            
            text = (
                f"📝 <b>{test.get('title')}</b>\n\n"
                f"📋 Savollar soni: <b>{len(questions)} ta</b>\n"
                f"📊 Qiyinlik darajasi: <b>{diff}</b>\n"
                f"⏱ Vaqt limiti: <b>{test.get('time_limit', 0)} daqiqa</b>\n"
                f"<i>Pastdagi tugma orqali testni boshlashingiz mumkin:</i>"
            )
            await message.answer(text, reply_markup=test_info_keyboard(test_id))
            return

    # 3. Agar oddiy start bo'lsa, Asosiy Menyuni chiqaramiz
    await message.answer(
        f"{welcome_text}\n\nO'zingizga kerakli bo'limni tanlang:",
        reply_markup=main_menu_keyboard(user_id)
    )


# ==========================================================
# 2. ASOSIY MENYU VA YORDAM TUGMALARI
# ==========================================================

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Barcha bo'limlardan asosiy menyuga qaytish"""
    await state.clear()
    await callback.answer()
    
    user_name = callback.from_user.full_name
    text = f"🏠 <b>Asosiy Menyu</b>\n\nO'zingizga kerakli bo'limni tanlang, {user_name}:"
    
    # edit_text ishlamay qolishini (message is not modified) oldini olish uchun try-except
    try:
        await callback.message.edit_text(text, reply_markup=main_menu_keyboard(callback.from_user.id))
    except Exception:
        await callback.message.answer(text, reply_markup=main_menu_keyboard(callback.from_user.id))
        await callback.message.delete()

@router.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    """Yordam bo'limi"""
    await callback.answer()
    help_text = (
        "❓ <b>BOTDAN FOYDALANISH BO'YICHA YORDAM</b>\n\n"
        "1️⃣ <b>Test yechish:</b> '📚 Testlar' bo'limiga kiring, fanni tanlang va testni boshlang.\n"
        "2️⃣ <b>Test yaratish:</b> '➕ Test Yaratish' tugmasini bosing va namunadagi kabi fayl yuboring.\n"
        "3️⃣ <b>Natijalar:</b> '📊 Natijalarim' bo'limida barcha ishlagan testlaringiz tarixini ko'rasiz.\n"
        "4️⃣ <b>Reyting:</b> Kim eng ko'p ball to'plaganini '🏆 Reyting' bo'limida bilsangiz bo'ladi.\n\n"
        "💡 <i>Muammo yuzaga kelsa, @admin ga murojaat qiling.</i>"
    )
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="main_menu"))
    
    await callback.message.edit_text(help_text, reply_markup=builder.as_markup())

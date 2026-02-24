"""
🚀 START VA AUTHENTICATION HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Avtomatik ro'yxatdan o'tish, kutib olish va asosiy menyu
"""
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from firebase.db import get_user, create_user
from keyboards.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    """Foydalanuvchi /start bosganda ishlaydi"""
    await state.clear() # Barcha oldingi xotiralarni tozalash
    user = message.from_user
    tg_id = user.id

    # Bazadan tekshirish
    db_user = get_user(tg_id)

    if not db_user:
        # Tizimda yo'q bo'lsa, avtomatik yaratish (Auth)
        create_user(telegram_id=tg_id, name=user.full_name, username=user.username)
        greeting = f"👋 Xush kelibsiz, <b>{user.first_name}</b>!\n\n🎓 Quiz Bot ga xush kelibsiz!"
        logger.info(f"Yangi foydalanuvchi: {tg_id} - {user.full_name}")
    else:
        # Bloklanganligini tekshirish
        if db_user.get("is_blocked"):
            await message.answer("🚫 Siz bloklangansiz. Tizim administratoriga murojaat qiling.")
            return
        greeting = f"👋 Qaytib keldingiz, <b>{user.first_name}</b>!"

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

    await message.answer(welcome_text, reply_markup=main_menu_keyboard(tg_id), parse_mode="HTML")

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Istalgan joydan Bosh sahifaga qaytish"""
    await state.clear()
    await callback.answer()
    
    # Bloklanganini yana bir bor tekshiramiz
    db_user = get_user(callback.from_user.id)
    if db_user and db_user.get("is_blocked"):
        await callback.message.edit_text("🚫 Siz bloklangansiz.")
        return

    text = "🎯 <b>QUIZ BOT</b> — Asosiy menyu\n\nQuyidagi bo'limlardan birini tanlang:"
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard(callback.from_user.id), parse_mode="HTML")

@router.message(Command("help"))
async def help_handler(message: Message):
    """Yordam bo'limi"""
    help_text = (
        "ℹ️ <b>YORDAM VA QOIDALAR</b>\n\n"
        "<b>📋 Asosiy komandalar:</b>\n"
        "/start — Bosh sahifaga qaytish va botni yangilash\n"
        "/help — Ushbu yordam oynasini ko'rish\n\n"
        "<b>📁 Test yaratish bo'yicha:</b>\n"
        "Siz TXT, DOCX va PDF formatidagi fayllarni yuklashingiz mumkin. "
        "Bot test turini avtomatik taniydi (Multiple choice, Matching, Fill in blank va hokazo).\n"
        "Qo'shimcha savollaringiz bo'lsa admin bilan bog'laning."
    )
    await message.answer(help_text, parse_mode="HTML")

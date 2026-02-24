"""
👤 PROFILE HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Foydalanuvchi statistikasi, natijalar tarixi va tahlil tugmalari bilan.
Hech narsa qisqartirilmadi!
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

# Bazaviy funksiyalar va klaviaturalar
from firebase.db import get_user, get_user_results, get_test
from keyboards.keyboards import main_menu_keyboard

# Router obyektini aniqlash (bot.py import qilishi uchun shart)
logger = logging.getLogger(__name__)
router = Router()

# ==========================================================
# 1. PROFIL ASOSIY OYNASI
# ==========================================================

@router.callback_query(F.data == "profile_view")
async def profile_view_handler(callback: CallbackQuery):
    """Foydalanuvchining umumiy statistikasi (Ism, Rol, Ballar)"""
    await callback.answer()
    
    user_id = callback.from_user.id
    user = get_user(user_id)
    
    if not user:
        await callback.message.edit_text(
            "❌ Profil ma'lumotlari topilmadi. Iltimos, /start buyrug'ini qayta bosing.",
            reply_markup=main_menu_keyboard(user_id)
        )
        return

    # Ma'lumotlarni yig'ish
    name = user.get("name", "Noma'lum")
    total_tests = user.get("total_tests", 0)
    avg_score = round(user.get("avg_score", 0), 1)
    role = user.get("role", "user").replace("admin", "👨‍💼 Admin").replace("user", "🎓 O'quvchi")
    
    # Chiroyli formatda chiqarish
    text = (
        f"👤 <b>SHAXSIY PROFIL</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Ism: <b>{name}</b>\n"
        f"🎭 Rol: <b>{role}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Jami yechilgan testlar: <b>{total_tests} ta</b>\n"
        f"🎯 O'rtacha o'zlashtirish: <b>{avg_score}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 <i>O'z bilimingizni oshirishda davom eting!</i>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📊 Natijalarim tarixi", callback_data="profile_results"))
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


# ==========================================================
# 2. NATIJALAR TARIXI (OXIRGI 10 TA)
# ==========================================================

@router.callback_query(F.data == "profile_results")
async def profile_results_handler(callback: CallbackQuery):
    """Foydalanuvchi yechgan oxirgi testlar va ularning tahliliga o'tish"""
    await callback.answer()
    
    user_id = callback.from_user.id
    # Oxirgi 10 ta natijani bazadan olamiz
    results = get_user_results(user_id, limit=10)
    
    if not results:
        await callback.message.edit_text(
            "📭 Siz hali birorta ham test ishlamagansiz.\n"
            "Testlarni boshlash uchun '📚 Testlar' bo'limiga o'ting.",
            reply_markup=main_menu_keyboard(user_id)
        )
        return
        
    text = "📋 <b>OXIRGI 10 TA NATIJANGIZ:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for res in results:
        test_id = res.get("test_id")
        result_id = res.get("result_id")
        
        # Test nomini bazadan olish
        test = get_test(test_id)
        test_title = test.get("title", "O'chirilgan test") if test else "Noma'lum test"
        
        # Natija holati
        percentage = res.get("percentage", 0)
        passed = res.get("passed", False)
        status_icon = "✅" if passed else "❌"
        
        # Vaqtni formatlash (kun.oy)
        comp_at = res.get("completed_at")
        date_str = comp_at.strftime("%d.%m") if comp_at else "--"
        
        text += f"{status_icon} <b>{test_title}</b> — {percentage}% (<i>{date_str}</i>)\n"
        
        # Har bir test uchun alohida 'Tahlil' tugmasi
        builder.row(InlineKeyboardButton(
            text=f"🔍 {test_title} (Tahlil)", 
            callback_data=f"analysis_{result_id}"
        ))

    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    
    # Telegram xabar limiti uchun himoya
    if len(text) > 4000:
        text = text[:4000] + "..."
        
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

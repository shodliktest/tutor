"""
👤 PROFILE HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Foydalanuvchi natijalari, o'rtacha foizi va oxirgi ishlangan testlari.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from firebase.db import get_user, get_user_results, get_test
from keyboards.keyboards import main_menu_keyboard
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "profile_view")
async def profile_view_handler(callback: CallbackQuery):
    """Foydalanuvchining umumiy statistikasini ko'rsatish"""
    await callback.answer()
    
    user_id = callback.from_user.id
    user = get_user(user_id)
    
    if not user:
        await callback.message.edit_text("❌ Profil ma'lumotlari topilmadi.")
        return

    # Statistikani tayyorlash
    name = user.get("name", "Noma'lum")
    total_tests = user.get("total_tests", 0)
    avg_score = round(user.get("avg_score", 0), 1)
    
    # Emojilar bilan chiroyli dizayn
    text = (
        f"👤 <b>PROFIL MA'LUMOTLARI</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Ism: <b>{name}</b>\n"
        f"🎭 Rol: <b>{user.get('role', 'user').capitalize()}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 Jami yechilgan testlar: <b>{total_tests} ta</b>\n"
        f"🎯 O'rtacha o'zlashtirish: <b>{avg_score}%</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📅 Ro'yxatdan o'tgan sana: <i>{user.get('created_at').strftime('%Y-%m-%d') if user.get('created_at') else 'Noma\\'lum'}</i>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📊 Natijalarim tarixi", callback_data="profile_results"))
    builder.row(InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "profile_results")
async def profile_results_handler(callback: CallbackQuery):
    """Foydalanuvchining oxirgi 10 ta testi natijalarini ro'yxat shaklida ko'rsatish"""
    await callback.answer()
    
    user_id = callback.from_user.id
    results = get_user_results(user_id, limit=10) # db.py dagi funksiya
    
    if not results:
        await callback.message.edit_text(
            "📭 Siz hali birorta ham test ishlamagansiz.",
            reply_markup=main_menu_keyboard(user_id)
        )
        return
        
    text = "📋 <b>OXIRGI NATIJALARINGIZ:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for res in results:
        test_id = res.get("test_id")
        test = get_test(test_id)
        test_title = test.get("title", "Nomsiz test") if test else "O'chirilgan test"
        
        status = "✅" if res.get("passed", False) else "❌"
        date = res.get("completed_at").strftime("%d.%m") if res.get("completed_at") else ""
        
        # Ro'yxat matni
        text += f"{status} <b>{test_title}</b>: {res.get('percentage')}% ({date})\n"
        
        # Har bir natija uchun batafsil tahlil tugmasi (kechagi funksiya)
        builder.row(InlineKeyboardButton(
            text=f"🔍 {test_title} (Tahlil)", 
            callback_data=f"analysis_{res.get('result_id')}"
        ))

    builder.row(InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu"))
    
    # Matn juda uzun bo'lib ketsa, Telegram xato berishi mumkin, shuning uchun kesamiz
    if len(text) > 4000: text = text[:4000]
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

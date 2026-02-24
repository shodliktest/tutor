"""
👤 PROFIL VA NATIJALAR HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Foydalanuvchining shaxsiy ma'lumotlari, statistikasi va yechgan testlari tarixi
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from firebase.db import get_user, get_user_results, get_test

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "profile_view")
async def profile_handler(callback: CallbackQuery):
    """Foydalanuvchi profilini ko'rsatish"""
    await callback.answer()
    user_id = callback.from_user.id
    
    user = get_user(user_id)
    if not user:
        await callback.message.edit_text("❌ Profil topilmadi. Iltimos, /start buyrug'ini bosing.")
        return

    total_tests = user.get("total_tests", 0)
    avg_score   = user.get("avg_score", 0)
    role        = user.get("role", "user")
    name        = user.get("name", "Noma'lum")

    # Rollar uchun chiroyli nomlar
    role_map = {
        "admin":   "👑 Admin",
        "creator": "👨‍🏫 Test Yaratuvchi",
        "user":    "👤 Foydalanuvchi",
    }
    role_text = role_map.get(role, "👤 Foydalanuvchi")

    text = (
        f"👤 <b>FOYDALANUVCHI PROFILI</b>\n\n"
        f"📛 <b>Ism:</b> {name}\n"
        f"🆔 <b>ID raqam:</b> <code>{user_id}</code>\n"
        f"🎭 <b>Rolingiz:</b> {role_text}\n\n"
        f"📊 <b>UMUMIY STATISTIKA:</b>\n"
        f"📝 Ishlangan testlar: <b>{total_tests}</b> ta\n"
        f"🎯 O'rtacha natija: <b>{avg_score:.1f}%</b>\n"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📊 Natijalarimni ko'rish", callback_data="profile_results"))
    builder.row(InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "profile_results")
async def my_results_handler(callback: CallbackQuery):
    """Foydalanuvchining oxirgi yechgan testlari ro'yxati (Tarix)"""
    await callback.answer("Natijalar yuklanmoqda...")
    user_id = callback.from_user.id
    
    # Bazadan oxirgi 20 ta natijani tortamiz
    results = get_user_results(user_id, limit=20)

    builder = InlineKeyboardBuilder()
    
    if not results:
        text = (
            "📭 <b>Hali hech qanday test ishlamadingiz.</b>\n\n"
            "Testlar katalogiga o'ting va o'z bilimingizni sinab ko'ring!"
        )
        builder.row(InlineKeyboardButton(text="📚 Testlarga o'tish", callback_data="browse_all"))
        builder.row(InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu"))
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        return

    text = f"📊 <b>MENING NATIJALARIM</b> (Oxirgi {len(results)} ta)\n\n"

    # Natijalarni chiroyli ro'yxat qilib taxlash
    for r in results[:15]:
        test_id  = r.get("test_id", "")
        test     = get_test(test_id)
        
        # Agar test o'chirilib ketgan bo'lsa
        title    = test.get("title", "O'chirilgan test")[:25] if test else "O'chirilgan test"
        pct      = r.get("percentage", 0)
        passed   = r.get("passed", False)
        
        icon     = "✅" if passed else "❌"
        date     = r.get("completed_at")
        
        # Sanani formatlash (Masalan: 24.02.2026)
        date_str = date.strftime("%d.%m.%Y") if date and hasattr(date, "strftime") else "Yaqinda"
        
        text += f"{icon} <b>{title}</b>\n   Natija: {pct:.0f}% — Sana: {date_str}\n\n"

    builder.row(InlineKeyboardButton(text="👤 Profilga qaytish", callback_data="profile_view"))
    builder.row(InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

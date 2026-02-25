"""
👤 PROFILE & MY TESTS HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Doimiy (Reply) menyudagi tugmalarni ushlab, "Mening Testlarim", 
"Profil" va "Natijalarim" ni chiqaruvchi mukammal handler.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from firebase.db import get_user, get_user_results, get_test, get_db
from keyboards.keyboards import main_reply_keyboard

logger = logging.getLogger(__name__)
router = Router()

# ==========================================================
# 1. PROFIL MA'LUMOTLARI (REPLY TUGMA ORQALI)
# ==========================================================
@router.message(F.text == "👤 Profil")
async def profile_view_msg(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user: 
        return await message.answer("❌ Profil topilmadi. /start buyrug'ini yuboring.")

    name = user.get("name", "Noma'lum")
    total_tests = user.get("total_tests", 0)
    avg_score = round(user.get("avg_score", 0), 1)
    role = user.get("role", "user").replace("admin", "👨‍💼 Admin").replace("user", "🎓 O'quvchi")

    text = (
        f"👤 <b>SHAXSIY PROFIL</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Ism: <b>{name}</b>\n"
        f"🎭 Rol: <b>{role}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Jami yechilgan testlar: <b>{total_tests} ta</b>\n"
        f"🎯 O'rtacha o'zlashtirish: <b>{avg_score}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    # Profil tagida kichik inline tugmalar qo'shish mumkin
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📊 Natijalarim tarixi", callback_data="profile_results"))
    
    await message.answer(text, reply_markup=builder.as_markup())

# Eski (Inline) tugma uchun zaxira
@router.callback_query(F.data == "profile_view")
async def profile_view_cb(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    user = get_user(user_id)
    if not user: return await callback.message.edit_text("❌ Profil ma'lumotlari topilmadi.")

    name = user.get("name", "Noma'lum")
    total_tests = user.get("total_tests", 0)
    avg_score = round(user.get("avg_score", 0), 1)
    
    text = (
        f"👤 <b>SHAXSIY PROFIL</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Ism: <b>{name}</b>\n"
        f"📊 Jami yechilgan testlar: <b>{total_tests} ta</b>\n"
        f"🎯 O'rtacha o'zlashtirish: <b>{avg_score}%</b>\n"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📊 Natijalarim tarixi", callback_data="profile_results"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


# ==========================================================
# 2. NATIJALAR TARIXI (REPLY VA INLINE TUGMA ORQALI)
# ==========================================================
@router.message(F.text == "📊 Natijalarim")
async def profile_results_msg(message: Message):
    user_id = message.from_user.id
    results = get_user_results(user_id, limit=10)
    
    if not results: 
        return await message.answer("📭 Siz hali test ishlamagansiz.")
        
    text = "📋 <b>OXIRGI 10 TA NATIJANGIZ:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for res in results:
        test = get_test(res.get("test_id"))
        title = test.get("title", "O'chirilgan test") if test else "Noma'lum"
        status = "✅" if res.get("passed") else "❌"
        
        comp_at = res.get("completed_at")
        date_str = comp_at.strftime("%d.%m") if comp_at else "--"
        
        text += f"{status} <b>{title}</b> — {res.get('percentage')}% ({date_str})\n"
        builder.row(InlineKeyboardButton(text=f"🔍 {title} (Tahlil)", callback_data=f"analysis_{res.get('result_id')}"))

    await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "profile_results")
async def profile_results_cb(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    results = get_user_results(user_id, limit=10)
    
    if not results: 
        return await callback.message.edit_text("📭 Siz hali test ishlamagansiz.")
        
    text = "📋 <b>OXIRGI 10 TA NATIJANGIZ:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for res in results:
        test = get_test(res.get("test_id"))
        title = test.get("title", "O'chirilgan test") if test else "Noma'lum"
        status = "✅" if res.get("passed") else "❌"
        text += f"{status} <b>{title}</b> — {res.get('percentage')}% \n"
        builder.row(InlineKeyboardButton(text=f"🔍 {title} (Tahlil)", callback_data=f"analysis_{res.get('result_id')}"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())


# ==========================================================
# 3. MENING TESTLARIM (YANGI REPLY TUGMA ORQALI)
# ==========================================================
@router.message(F.text == "🗂 Mening testlarim")
async def my_tests_handler(message: Message):
    """Foydalanuvchi o'zi yaratgan barcha testlarni kodlari va ssilkasi bilan ko'rsatish"""
    user_id = message.from_user.id
    db = get_db()
    
    # Bazadan shu foydalanuvchi yaratgan testlarni tortish
    tests_ref = db.collection("tests").where("creator_id", "==", user_id).stream()
    tests = [t.to_dict() for t in tests_ref]
    
    if not tests:
        await message.answer("📭 Siz hali hech qanday test yaratmagansiz.\nMenyudan '➕ Test Yaratish' ni bosing.")
        return
        
    text = "🗂 <b>SIZ YARATGAN TESTLAR RO'YXATI:</b>\n\n"
    bot_username = (await message.bot.me()).username
    
    for i, t in enumerate(tests, 1):
        t_id = t.get("test_id")
        title = t.get("title", "Nomsiz")
        category = t.get("category", "Boshqa")
        vis = {"public": "🌍 Ommaviy", "link": "🔗 Ssilka", "private": "🔒 Shaxsiy"}.get(t.get("visibility"), "Noma'lum")
        
        text += f"{i}. <b>{title}</b> ({category})\n"
        text += f"   🔑 Kod: <code>{t_id}</code>\n"
        text += f"   📊 Ishlangan: {t.get('solve_count', 0)} marta | Holat: {vis}\n"
        text += f"   🔗 Ssilka: <code>https://t.me/{bot_username}?start={t_id}</code>\n\n"
        
    # Xabar uzun bo'lib ketsa, Telegram o'tkazmaydi. Matnni kesish:
    if len(text) > 4000:
        text = text[:4000] + "\n...\n(Ro'yxat juda uzun)"
        
    await message.answer(text, parse_mode="HTML")
        

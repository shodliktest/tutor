"""
🏆 LEADERBOARD HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Reyting xatoliklarini (TelegramBadRequest) oldini olish himoyasi bilan.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from firebase.db import get_global_leaderboard, get_leaderboard_by_test, get_test
from keyboards.keyboards import leaderboard_keyboard

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "🏆 Reyting")
async def global_leaderboard_handler_msg(message: Message):
    """Umumiy (Global) TOP 10 reyting (Reply tugma)"""
    leaders = get_global_leaderboard(limit=10)
    
    text = "🌍 <b>GLOBAL REYTING (TOP 10)</b>\n"
    text += "<i>O'rtacha o'zlashtirish foizi bo'yicha:</i>\n\n"
    
    if not leaders:
        text += "📭 Hozircha reyting bo'sh."
    else:
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, user in enumerate(leaders):
            medal = medals[i] if i < 10 else f"{i+1}."
            avg = round(user.get("avg_score", 0), 1)
            text += f"{medal} <b>{user.get('name')}</b> — {avg}% ({user.get('total_tests')} ta test)\n"

    await message.answer(text, reply_markup=leaderboard_keyboard("global"))

@router.callback_query(F.data == "lb_global")
async def global_leaderboard_handler_cb(callback: CallbackQuery):
    """Umumiy (Global) TOP 10 reyting (Inline tugma)"""
    await callback.answer()
    leaders = get_global_leaderboard(limit=10)
    
    text = "🌍 <b>GLOBAL REYTING (TOP 10)</b>\n"
    text += "<i>O'rtacha o'zlashtirish foizi bo'yicha:</i>\n\n"
    
    if not leaders:
        text += "📭 Hozircha reyting bo'sh."
    else:
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, user in enumerate(leaders):
            medal = medals[i] if i < 10 else f"{i+1}."
            avg = round(user.get("avg_score", 0), 1)
            text += f"{medal} <b>{user.get('name')}</b> — {avg}% ({user.get('total_tests')} ta test)\n"

    # 🛡️ Xatolikdan himoya (Agar matn o'zgarmagan bo'lsa)
    try:
        await callback.message.edit_text(text, reply_markup=leaderboard_keyboard("global"))
    except TelegramBadRequest:
        pass # Xatoni yashirish (foydalanuvchiga sezilmaydi)

@router.callback_query(F.data.startswith("lb_test_"))
async def test_leaderboard_handler(callback: CallbackQuery):
    """Ma'lum bir test bo'yicha TOP 10 natijalar"""
    await callback.answer()
    
    test_id = callback.data.replace("lb_test_", "")
    test = get_test(test_id)
    
    if not test:
        await callback.message.answer("❌ Test topilmadi.")
        return
        
    leaders = get_leaderboard_by_test(test_id, limit=10)
    
    text = f"🏆 <b>TEST REYTINGI:</b>\n📝 {test.get('title')}\n\n"
    
    if not leaders:
        text += "📭 Bu testni hali hech kim yechmagan."
    else:
        for i, res in enumerate(leaders):
            place = i + 1
            text += f"{place}. <b>{res.get('user_name')}</b> — {res.get('best_percentage')}% ({res.get('best_score')} ball)\n"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"view_test_{test_id}"))
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    
    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    except TelegramBadRequest:
        pass

@router.callback_query(F.data == "lb_subject")
async def subject_leaderboard_info(callback: CallbackQuery):
    await callback.answer("⏳ Tez kunda...")
    await callback.message.answer("📊 Fanlar bo'yicha alohida reyting tizimi keyingi yangilanishda qo'shiladi!")
    

"""
🏆 LEADERBOARD — Global va test bo'yicha reyting
TelegramBadRequest himoyasi bilan
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from firebase.db import get_global_leaderboard, get_leaderboard_by_test, get_test
from keyboards.keyboards import leaderboard_keyboard

log = logging.getLogger(__name__)
router = Router()

MEDALS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


@router.message(F.text == "🏆 Reyting")
async def global_lb_msg(message: Message):
    await message.answer(_global_text(), reply_markup=leaderboard_keyboard("global"))


@router.callback_query(F.data == "lb_global")
async def global_lb_cb(callback: CallbackQuery):
    await callback.answer()
    try:
        await callback.message.edit_text(
            _global_text(), reply_markup=leaderboard_keyboard("global")
        )
    except TelegramBadRequest:
        pass


def _global_text() -> str:
    leaders = get_global_leaderboard(limit=10)
    text    = "🌍 <b>GLOBAL REYTING (TOP 10)</b>\n"
    text   += "<i>O'rtacha o'zlashtirish bo'yicha:</i>\n\n"
    if not leaders:
        text += "📭 Reyting hali bo'sh."
    else:
        for i, u in enumerate(leaders):
            medal = MEDALS[i] if i < len(MEDALS) else f"{i+1}."
            avg   = round(u.get("avg_score", 0), 1)
            total = u.get("total_tests", 0)
            text += f"{medal} <b>{u.get('name')}</b> — {avg}% ({total} ta test)\n"
    return text


@router.callback_query(F.data.startswith("lb_test_"))
async def test_lb_cb(callback: CallbackQuery):
    await callback.answer()
    tid     = callback.data[8:]
    test    = get_test(tid)
    leaders = get_leaderboard_by_test(tid, limit=10)

    text = f"🏆 <b>TEST REYTINGI</b>\n"
    if test:
        text += f"📝 {test.get('title')}\n"
    text += "\n"

    if not leaders:
        text += "📭 Bu testni hali hech kim yechmagan."
    else:
        for i, r in enumerate(leaders):
            medal = MEDALS[i] if i < len(MEDALS) else f"{i+1}."
            text += f"{medal} <b>{r.get('user_name')}</b> — {r.get('best_percentage')}%\n"

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"view_test_{tid}"),
        InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu"),
    )
    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    except TelegramBadRequest:
        pass


@router.callback_query(F.data == "lb_subject")
async def subject_lb_cb(callback: CallbackQuery):
    await callback.answer("🔜 Tez orada...", show_alert=True)

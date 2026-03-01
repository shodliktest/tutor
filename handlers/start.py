"""
🚀 START HANDLER — Aiogram 3
Yangi foydalanuvchi, Deep-linking, Yordam, Asosiy menyu
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

log = logging.getLogger(__name__)
router = Router()


# ═══════════════════════════════════════════════════════════
# 1. /START — Ro'yxatga olish va Deep-linking
# ═══════════════════════════════════════════════════════════

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    uid   = message.from_user.id
    name  = message.from_user.full_name
    uname = message.from_user.username

    user = get_user(uid)
    if not user:
        create_user(uid, name, uname)
        welcome = f"👋 Salom, <b>{name}</b>!\n🎓 Quiz Bot platformasiga xush kelibsiz!"

        # Adminga yangi foydalanuvchi haqida xabar
        for admin_id in ADMIN_IDS:
            try:
                at = f"@{uname}" if uname else "Yo'q"
                await message.bot.send_message(
                    admin_id,
                    f"🆕 <b>Yangi foydalanuvchi!</b>\n"
                    f"👤 Ism: {name}\n🔗 User: {at}\n"
                    f"🆔 ID: <code>{uid}</code>"
                )
            except Exception:
                pass
    else:
        welcome = f"🏠 Xush kelibsiz, <b>{name}</b>!"

    # Deep-linking: /start test_id
    args = message.text.split()
    if len(args) > 1:
        tid  = args[1]
        test = get_test(tid)
        if test:
            qs = test.get("questions", [])
            diff_map = {"easy": "🟢 Oson", "medium": "🟡 O'rtacha",
                        "hard": "🔴 Qiyin", "expert": "⚡ Ekspert"}
            diff = diff_map.get(test.get("difficulty", ""), test.get("difficulty", ""))
            text = (
                f"🔍 <b>TEST TOPILDI!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📝 <b>{test.get('title')}</b>\n"
                f"📁 Fan: {test.get('category', '')}\n"
                f"📋 Savollar: <b>{len(qs)} ta</b>\n"
                f"📊 Qiyinlik: <b>{diff}</b>\n"
                f"⏱ Vaqt: <b>{test.get('time_limit', 0)} daqiqa</b>\n"
                f"🎯 O'tish foizi: <b>{test.get('passing_score', 60)}%</b>"
            )
            await message.answer(welcome, reply_markup=main_reply_keyboard(uid))
            await message.answer(text, reply_markup=test_info_keyboard(tid))
            return

    await message.answer(
        f"{welcome}\n\nPastdagi menyudan kerakli bo'limni tanlang 👇",
        reply_markup=main_reply_keyboard(uid)
    )


# ═══════════════════════════════════════════════════════════
# 2. ASOSIY MENYUGA QAYTISH
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    uid = callback.from_user.id
    await callback.bot.send_message(
        uid,
        "🏠 <b>Asosiy menyu</b>\nPastdagi tugmalardan foydalaning 👇",
        reply_markup=main_reply_keyboard(uid)
    )


# ═══════════════════════════════════════════════════════════
# 3. YORDAM
# ═══════════════════════════════════════════════════════════

@router.message(F.text == "ℹ️ Yordam")
async def help_msg(message: Message):
    await _send_help(message)


@router.callback_query(F.data == "help")
async def help_cb(callback: CallbackQuery):
    await callback.answer()
    await _send_help(callback.message, edit=True)


async def _send_help(msg: Message, edit: bool = False):
    text = (
        "❓ <b>BOTDAN FOYDALANISH BO'YICHA YORDAM</b>\n\n"
        "1️⃣ <b>Test yechish (Inline):</b>\n"
        "   '📚 Testlar' → Fan → Test → <b>▶️ Inline test</b>\n"
        "   Inline tugmalar bilan javob berish, har savoldan keyin\n"
        "   5 soniya to'g'ri/noto'g'ri ko'rsatiladi.\n\n"
        "2️⃣ <b>Test yechish (Poll):</b>\n"
        "   '📚 Testlar' → Fan → Test → <b>📊 Poll test</b>\n"
        "   Telegram native quiz poll orqali test yechish.\n"
        "   @QuizBot uslubida, lekin natijalar bazaga saqlanadi!\n\n"
        "3️⃣ <b>Test yaratish:</b>\n"
        "   '➕ Test Yaratish' → TXT/PDF fayl yuklash\n"
        "   yoki @QuizBot viktorinalarini forward qilish.\n\n"
        "4️⃣ <b>Test kodi:</b>\n"
        "   Kodini to'g'ridan-to'g'ri yozib yuboring.\n\n"
        "💬 <i>Muammo bo'lsa adminga murojaat qiling:</i>"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👨‍💻 Adminga yozish", callback_data="contact_admin"))

    if edit:
        try:
            await msg.edit_text(text, reply_markup=builder.as_markup())
            return
        except Exception:
            pass
    await msg.answer(text, reply_markup=builder.as_markup())

"""
🚀 START HANDLER — Xavfsizlik va Adminga murojaat
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_IDS
from firebase.db import get_user, create_user, get_test
from keyboards.keyboards import main_reply_keyboard, test_info_keyboard
from utils.states import ContactAdmin

log = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    uid   = message.from_user.id
    name  = message.from_user.full_name
    uname = message.from_user.username

    # Bloklangan foydalanuvchini tekshirish
    user = get_user(uid)
    if user and user.get("is_blocked"):
        return await message.answer("🚫 Siz bloklangansiz. Admin bilan bog'laning.")

    if not user:
        create_user(uid, name, uname)
        welcome = f"👋 Salom, <b>{name}</b>!\n🎓 Quiz Bot platformasiga xush kelibsiz!"
        for admin_id in ADMIN_IDS:
            try:
                at = f"@{uname}" if uname else "Yo'q"
                await message.bot.send_message(
                    admin_id,
                    f"🆕 <b>Yangi foydalanuvchi!</b>\n"
                    f"👤 {name}\n🔗 {at}\n🆔 <code>{uid}</code>"
                )
            except Exception:
                pass
    else:
        welcome = f"🏠 Xush kelibsiz, <b>{name}</b>!"

    args = message.text.split()
    if len(args) > 1:
        tid  = args[1]
        test = get_test(tid)
        if test:
            qs = test.get("questions", [])
            diff_map = {"easy": "🟢 Oson", "medium": "🟡 O'rtacha",
                        "hard": "🔴 Qiyin", "expert": "⚡ Ekspert"}
            diff = diff_map.get(test.get("difficulty", ""), "")
            text = (
                f"🔍 <b>TEST TOPILDI!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📝 <b>{test.get('title')}</b>\n"
                f"📁 Fan: {test.get('category', '')}\n"
                f"📋 Savollar: <b>{len(qs)} ta</b>\n"
                f"📊 Qiyinlik: <b>{diff}</b>\n"
                f"🎯 O'tish foizi: <b>{test.get('passing_score', 60)}%</b>"
            )
            await message.answer(welcome, reply_markup=main_reply_keyboard(uid))
            await message.answer(text, reply_markup=test_info_keyboard(tid))
            return

    await message.answer(
        f"{welcome}\n\nPastdagi menyudan kerakli bo'limni tanlang 👇",
        reply_markup=main_reply_keyboard(uid)
    )


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
        uid, "🏠 <b>Asosiy menyu</b>\n👇",
        reply_markup=main_reply_keyboard(uid)
    )


@router.message(F.text == "ℹ️ Yordam")
async def help_msg(message: Message):
    await _send_help(message)


@router.callback_query(F.data == "help")
async def help_cb(callback: CallbackQuery):
    await callback.answer()
    await _send_help(callback.message, edit=True)


async def _send_help(msg, edit: bool = False):
    text = (
        "❓ <b>BOTDAN FOYDALANISH</b>\n\n"
        "1️⃣ <b>▶️ Inline test</b> — har savoldan keyin 5 soniya to'g'ri/noto'g'ri\n\n"
        "2️⃣ <b>📊 Poll test</b> — Telegram native quiz poll (@QuizBot uslubi)\n\n"
        "3️⃣ <b>Test yaratish</b> — TXT/PDF fayl yoki @QuizBot forward\n"
        "   Yaratilgan test ikki rejimda ham ishlaydi!\n\n"
        "4️⃣ <b>Test kodi</b> — kodni to'g'ridan-to'g'ri yuboring\n\n"
        "5️⃣ <b>Natijalarim</b> — 8 tadan ko'rsatiladi, almashtirish mumkin\n\n"
        "6️⃣ <b>Mening testlarim</b> — 5 tadan, TXT yuklab olish, ulashish\n\n"
        "💬 <i>Muammo bo'lsa adminga murojaat qiling:</i>"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✉️ Adminga murojaat", callback_data="contact_admin"))
    kb = builder.as_markup()
    try:
        if edit:
            await msg.edit_text(text, reply_markup=kb)
            return
    except Exception:
        pass
    await msg.answer(text, reply_markup=kb)


# ── ADMINGA MUROJAAT ──────────────────────────────────────

@router.callback_query(F.data == "contact_admin")
async def contact_admin_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_contact"))
    try:
        await callback.message.edit_text(
            "<b>✉️ ADMINGA MUROJAAT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Xabaringizni yozing (matn, rasm yoki fayl):\n\n"
            "<i>Admin imkon topib javob beradi 🙏</i>",
            reply_markup=builder.as_markup()
        )
    except TelegramBadRequest:
        await callback.message.answer(
            "<b>✉️ ADMINGA MUROJAAT</b>\n\nXabaringizni yozing:",
            reply_markup=builder.as_markup()
        )
    await state.set_state(ContactAdmin.waiting_message)


@router.callback_query(F.data == "cancel_contact")
async def cancel_contact(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Bekor qilindi")
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.bot.send_message(
        callback.from_user.id,
        "✅ Bekor qilindi.",
        reply_markup=main_reply_keyboard(callback.from_user.id)
    )


@router.message(ContactAdmin.waiting_message)
async def contact_admin_send(message: Message, state: FSMContext):
    uid   = message.from_user.id
    name  = message.from_user.full_name
    uname = f"@{message.from_user.username}" if message.from_user.username else "Yo'q"

    sent = 0
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"📩 <b>FOYDALANUVCHIDAN MUROJAAT</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 {name}\n🔗 {uname}\n🆔 <code>{uid}</code>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\nXabar:"
            )
            await message.forward(admin_id)
            sent += 1
        except Exception as e:
            log.error(f"Admin {admin_id} ga xato: {e}")

    await state.clear()
    if sent > 0:
        await message.answer(
            "✅ <b>Xabaringiz adminga yuborildi!</b>\n\nJavobni kuting 🙏",
            reply_markup=main_reply_keyboard(uid)
        )
    else:
        await message.answer(
            "⚠️ Yuborishda muammo yuz berdi. Keyinroq urinib ko'ring.",
            reply_markup=main_reply_keyboard(uid)
        )


@router.message(F.text.startswith("/reply "))
async def admin_reply(message: Message):
    """Admin javob yuborish: /reply USER_ID Xabar matni"""
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        return await message.answer("Format: <code>/reply USER_ID Xabar</code>")
    try:
        target_id = int(parts[1])
        await message.bot.send_message(
            target_id,
            f"📬 <b>ADMINDAN JAVOB:</b>\n\n{parts[2]}"
        )
        await message.answer(f"✅ {target_id} ga yuborildi.")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")

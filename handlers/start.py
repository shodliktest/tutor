"""
🚀 START HANDLER — Aiogram 3
Yangi foydalanuvchi, Deep-linking, Yordam, Adminga murojaat
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

# Adminga murojaat uchun state
from aiogram.fsm.state import State, StatesGroup

class ContactAdmin(StatesGroup):
    waiting_message = State()


# ═══════════════════════════════════════════════════════════
# 1. /START
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
        "1️⃣ <b>Test yechish (▶️ Inline):</b>\n"
        "   Testlar → Fan → Test → <b>▶️ Inline test</b>\n"
        "   Har savoldan keyin 5 soniya to'g'ri/noto'g'ri ko'rsatadi\n\n"
        "2️⃣ <b>Test yechish (📊 Poll):</b>\n"
        "   Testlar → Fan → Test → <b>📊 Poll test</b>\n"
        "   Telegram native quiz poll — @QuizBot uslubida!\n\n"
        "3️⃣ <b>Test yaratish:</b>\n"
        "   ➕ Test Yaratish → Fayl yuklash yoki QuizBot forward\n"
        "   Yaratilgan test ikki rejimda ham ishlaydi!\n\n"
        "4️⃣ <b>Test kodi:</b>\n"
        "   Kodni to'g'ridan-to'g'ri yuboring — test ochiladi\n\n"
        "💬 <i>Muammo yoki savol bo'lsa — pastdagi tugmani bosing:</i>"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="✉️ Adminga murojaat qilish",
        callback_data="contact_admin"
    ))
    kb = builder.as_markup()

    if edit:
        try:
            await msg.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await msg.answer(text, reply_markup=kb)


# ═══════════════════════════════════════════════════════════
# 4. ADMINGA MUROJAAT
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "contact_admin")
async def contact_admin_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_contact"))

    try:
        await callback.message.edit_text(
            "<b>✉️ ADMINGA MUROJAAT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Xabaringizni yozing — admin imkon bo'lganda javob beradi:\n\n"
            "<i>(Matn, rasm yoki fayl yuborishingiz mumkin)</i>",
            reply_markup=builder.as_markup()
        )
    except Exception:
        await callback.message.answer(
            "<b>✉️ ADMINGA MUROJAAT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Xabaringizni yozing:",
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
            # Avval kimdan ekanini yubor
            await message.bot.send_message(
                admin_id,
                f"📩 <b>FOYDALANUVCHIDAN MUROJAAT</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 Ism: <b>{name}</b>\n"
                f"🔗 Username: {uname}\n"
                f"🆔 ID: <code>{uid}</code>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Xabar:"
            )
            # Keyin xabarning o'zini forward qil
            await message.forward(admin_id)
            sent += 1
        except Exception as e:
            log.error(f"Admin {admin_id} ga yuborishda xato: {e}")

    await state.clear()

    if sent > 0:
        await message.answer(
            "✅ <b>Xabaringiz adminga yuborildi!</b>\n\n"
            "Admin imkon topib javob beradi.\n"
            "Sabr qiling 🙏",
            reply_markup=main_reply_keyboard(uid)
        )
    else:
        await message.answer(
            "⚠️ Xabar yuborishda muammo yuz berdi.\n"
            "Keyinroq qayta urinib ko'ring.",
            reply_markup=main_reply_keyboard(uid)
        )


# ═══════════════════════════════════════════════════════════
# 5. ADMINING JAVOBINI FOYDALANUVCHIGA YUBORISH
# ═══════════════════════════════════════════════════════════

@router.message(F.text.startswith("/reply "))
async def admin_reply(message: Message):
    """Admin /reply 123456789 Salom xabaringizni oldim"""
    if message.from_user.id not in ADMIN_IDS:
        return

    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        return await message.answer(
            "❌ Format: <code>/reply USER_ID Xabar matni</code>"
        )

    try:
        target_id = int(parts[1])
        text      = parts[2]
        await message.bot.send_message(
            target_id,
            f"📬 <b>ADMINDAN JAVOB:</b>\n\n{text}"
        )
        await message.answer(f"✅ Foydalanuvchi {target_id} ga javob yuborildi.")
    except ValueError:
        await message.answer("❌ ID raqam bo'lishi kerak.")
    except Exception as e:
        await message.answer(f"❌ Yuborishda xato: {e}")

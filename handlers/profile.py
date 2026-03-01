"""
👤 PROFIL, NATIJALAR VA MENING TESTLARIM
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from firebase.db import get_user, get_user_results, get_test, get_my_tests
from keyboards.keyboards import main_reply_keyboard

log = logging.getLogger(__name__)
router = Router()


# ═══════════════════════════════════════════════════════════
# 1. PROFIL
# ═══════════════════════════════════════════════════════════

@router.message(F.text == "👤 Profil")
async def profile_msg(message: Message):
    await _show_profile(message, message.from_user.id)


@router.callback_query(F.data == "profile_view")
async def profile_cb(callback: CallbackQuery):
    await callback.answer()
    await _show_profile(callback.message, callback.from_user.id, edit=True)


async def _show_profile(msg, uid: int, edit: bool = False):
    user = get_user(uid)
    if not user:
        text = "❌ Profil topilmadi. /start ni bosing."
        if edit:
            await msg.edit_text(text)
        else:
            await msg.answer(text)
        return

    role_map = {
        "admin":   "👑 Admin",
        "teacher": "👨‍🏫 O'qituvchi",
        "user":    "🎓 O'quvchi",
    }
    role = role_map.get(user.get("role", "user"), "🎓 O'quvchi")

    text = (
        f"👤 <b>SHAXSIY PROFIL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"👤 Ism: <b>{user.get('name', 'Noma\'lum')}</b>\n"
        f"🎭 Rol: <b>{role}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 Yechilgan testlar: <b>{user.get('total_tests', 0)} ta</b>\n"
        f"📊 O'rtacha natija: <b>{round(user.get('avg_score', 0), 1)}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📊 Natijalar tarixim", callback_data="profile_results"))
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    kb = builder.as_markup()

    if edit:
        try:
            await msg.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await msg.answer(text, reply_markup=kb)


# ═══════════════════════════════════════════════════════════
# 2. NATIJALAR TARIXI
# ═══════════════════════════════════════════════════════════

@router.message(F.text == "📊 Natijalarim")
async def results_msg(message: Message):
    await _show_results(message, message.from_user.id)


@router.callback_query(F.data == "profile_results")
async def results_cb(callback: CallbackQuery):
    await callback.answer()
    await _show_results(callback.message, callback.from_user.id, edit=True)


async def _show_results(msg, uid: int, edit: bool = False):
    results = get_user_results(uid, limit=15)

    if not results:
        text = "📭 Siz hali hech qanday test ishlamagansiz."
        if edit:
            try:
                await msg.edit_text(text)
                return
            except Exception:
                pass
        await msg.answer(text)
        return

    text    = "📋 <b>OXIRGI NATIJALARINGIZ:</b>\n\n"
    builder = InlineKeyboardBuilder()

    for res in results:
        test = get_test(res.get("test_id", ""))
        title = test.get("title", "O'chirilgan test")[:25] if test else "Noma'lum"
        icon  = "✅" if res.get("passed") else "❌"
        pct   = res.get("percentage", 0)
        mode  = "📊" if res.get("mode") == "poll" else "▶️"
        dt    = res.get("completed_at")
        date  = dt.strftime("%d.%m") if dt and hasattr(dt, "strftime") else "--"

        text += f"{icon} {mode} <b>{title}</b> — {pct}% ({date})\n"
        builder.row(InlineKeyboardButton(
            text=f"🔍 {title[:20]} — Tahlil",
            callback_data=f"analysis_{res.get('result_id')}"
        ))

    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    kb = builder.as_markup()

    if edit:
        try:
            await msg.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await msg.answer(text, reply_markup=kb)


# ═══════════════════════════════════════════════════════════
# 3. MENING TESTLARIM
# ═══════════════════════════════════════════════════════════

@router.message(F.text == "🗂 Mening testlarim")
async def my_tests_handler(message: Message):
    uid   = message.from_user.id
    tests = get_my_tests(uid)

    if not tests:
        await message.answer(
            "📭 Siz hali test yaratmagansiz.\n"
            "Menyudan '➕ Test Yaratish' ni bosing."
        )
        return

    bot_uname = (await message.bot.me()).username
    text      = "🗂 <b>SIZ YARATGAN TESTLAR:</b>\n\n"

    for i, t in enumerate(tests, 1):
        tid   = t.get("test_id")
        title = t.get("title", "Nomsiz")
        cat   = t.get("category", "Boshqa")
        vis   = {"public": "🌍", "link": "🔗", "private": "🔒"}.get(t.get("visibility"), "")
        text += (
            f"{i}. <b>{title}</b> ({cat}) {vis}\n"
            f"   🔑 Kod: <code>{tid}</code>\n"
            f"   📊 Ishlangan: {t.get('solve_count', 0)} marta | "
            f"⭐ O'rtacha: {t.get('avg_score', 0)}%\n"
            f"   🔗 <code>https://t.me/{bot_uname}?start={tid}</code>\n\n"
        )

    if len(text) > 4000:
        text = text[:3990] + "\n...(ro'yxat qisqartirildi)"

    await message.answer(text)

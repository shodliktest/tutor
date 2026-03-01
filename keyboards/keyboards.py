"""
⌨️ BARCHA KLAVIATURALAR — Aiogram 3
✅ Telegram Web App tugmalari (popup oyna ochish uchun)
✅ Barcha mavjud tugmalar saqlab qolindi
"""
import json
import base64
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import SUBJECTS, DIFFICULTY_LEVELS, WEBAPP_BASE_URL


def main_reply_keyboard(user_id: int = None) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📚 Testlar"),         KeyboardButton(text="➕ Test Yaratish")],
        [KeyboardButton(text="📊 Natijalarim"),      KeyboardButton(text="🏆 Reyting")],
        [KeyboardButton(text="🗂 Mening testlarim"), KeyboardButton(text="👤 Profil")],
        [KeyboardButton(text="ℹ️ Yordam")],
    ]
    if user_id:
        from config import ADMIN_IDS
        if user_id in ADMIN_IDS:
            kb.append([KeyboardButton(text="👑 Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                               input_field_placeholder="Bo'limni tanlang...")


def create_subject_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in SUBJECTS:
        builder.add(InlineKeyboardButton(text=s, callback_data=f"set_subj_{s}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="✏️ Boshqa", callback_data="set_subj_other"))
    builder.row(InlineKeyboardButton(text="❌ Bekor", callback_data="cancel_creation"))
    return builder.as_markup()


def difficulty_keyboard(prefix: str = "diff_") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for k, v in DIFFICULTY_LEVELS.items():
        builder.add(InlineKeyboardButton(text=v, callback_data=f"{prefix}{k}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ Bekor", callback_data="cancel_creation"))
    return builder.as_markup()


def test_visibility_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌍 Ommaviy",       callback_data="vis_public"))
    builder.row(InlineKeyboardButton(text="🔗 Ssilka orqali", callback_data="vis_link"))
    builder.row(InlineKeyboardButton(text="🔒 Shaxsiy",        callback_data="vis_private"))
    builder.row(InlineKeyboardButton(text="❌ Bekor",           callback_data="cancel_creation"))
    return builder.as_markup()


def test_info_keyboard(test_id: str) -> InlineKeyboardMarkup:
    """
    Test haqida ekran — 3 usul:
    1. Web App orqali (popup oyna)
    2. Inline test (oddiy xabarlar)
    3. Poll test (native Telegram poll)
    """
    builder = InlineKeyboardBuilder()
    if WEBAPP_BASE_URL:
        webapp_url = f"{WEBAPP_BASE_URL}/test.html?test_id={test_id}"
        builder.row(InlineKeyboardButton(
            text="🎮 Web App (zamonaviy)",
            web_app=WebAppInfo(url=webapp_url)
        ))
    builder.row(
        InlineKeyboardButton(text="▶️ Inline test",  callback_data=f"start_test_{test_id}"),
        InlineKeyboardButton(text="📊 Poll test",     callback_data=f"start_poll_{test_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Reyting",       callback_data=f"lb_test_{test_id}"),
        InlineKeyboardButton(text="🏠 Asosiy menyu",  callback_data="main_menu"),
    )
    return builder.as_markup()


def result_keyboard(test_id: str, result_id: str, result_data: dict = None) -> InlineKeyboardMarkup:
    """Test yakunlanganda natija klaviaturasi."""
    builder = InlineKeyboardBuilder()
    if result_data and WEBAPP_BASE_URL:
        try:
            encoded = base64.b64encode(
                json.dumps(result_data, ensure_ascii=False, default=str).encode()
            ).decode()
            review_url = f"{WEBAPP_BASE_URL}/review.html?result={encoded}"
            if len(review_url) <= 2048:
                builder.row(InlineKeyboardButton(
                    text="🔍 Batafsil tahlil (Web App)",
                    web_app=WebAppInfo(url=review_url)
                ))
        except Exception:
            pass
    builder.row(InlineKeyboardButton(
        text="📊 Oddiy tahlil",
        callback_data=f"analysis_{result_id}"
    ))
    builder.row(
        InlineKeyboardButton(text="📄 TXT yuklab olish", callback_data=f"dl_result_{result_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Qaytadan",   callback_data=f"start_test_{test_id}"),
        InlineKeyboardButton(text="📊 Poll rejim",  callback_data=f"start_poll_{test_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Reyting",  callback_data=f"lb_test_{test_id}"),
        InlineKeyboardButton(text="🏠 Asosiy",   callback_data="main_menu"),
    )
    return builder.as_markup()


def answer_keyboard(letters: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for letter in letters:
        builder.add(InlineKeyboardButton(text=letter, callback_data=f"ans_{letter}"))
    builder.adjust(len(letters))
    builder.row(InlineKeyboardButton(text="❌ Testni to'xtatish", callback_data="cancel_test"))
    return builder.as_markup()


def feedback_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏳ Keyingi savolga o'tilmoqda...", callback_data="wait_btn"))
    builder.row(InlineKeyboardButton(text="❌ Testni to'xtatish", callback_data="cancel_test"))
    return builder.as_markup()


def leaderboard_keyboard(current: str = "global") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🌍 Global" + (" ✓" if current == "global" else ""),
            callback_data="lb_global"
        ),
        InlineKeyboardButton(text="📚 Fan bo'yicha", callback_data="lb_subject"),
    )
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    return builder.as_markup()


def admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users"),
        InlineKeyboardButton(text="📋 Testlar",           callback_data="admin_tests"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 Statistika",    callback_data="admin_stats"),
        InlineKeyboardButton(text="📢 Broadcast",     callback_data="admin_broadcast"),
    )
    builder.row(
        InlineKeyboardButton(text="🚫 Bloklash",      callback_data="admin_block"),
        InlineKeyboardButton(text="🗑 Test o'chirish", callback_data="admin_del_test"),
    )
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    return builder.as_markup()


# ═══════════════════════════════════════════════════════════
# WEB APP MAXSUS KLAVIATURALAR
# ═══════════════════════════════════════════════════════════

def webapp_history_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Natijalar tarixi — Web App popup"""
    builder = InlineKeyboardBuilder()
    if WEBAPP_BASE_URL:
        history_url = f"{WEBAPP_BASE_URL}/history.html?user_id={user_id}"
        builder.row(InlineKeyboardButton(
            text="📜 Natijalar tarixini ko'rish",
            web_app=WebAppInfo(url=history_url)
        ))
    builder.row(
        InlineKeyboardButton(text="⬅️ Profil",  callback_data="show_profile"),
        InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu"),
    )
    return builder.as_markup()


def webapp_create_keyboard() -> InlineKeyboardMarkup:
    """Test yaratish — Web App popup"""
    builder = InlineKeyboardBuilder()
    if WEBAPP_BASE_URL:
        create_url = f"{WEBAPP_BASE_URL}/create.html"
        builder.row(InlineKeyboardButton(
            text="✏️ Test yaratish (Web App)",
            web_app=WebAppInfo(url=create_url)
        ))
    builder.row(
        InlineKeyboardButton(text="📝 Oddiy usul (TXT)",  callback_data="create_txt_mode"),
        InlineKeyboardButton(text="🏠 Asosiy",            callback_data="main_menu"),
    )
    return builder.as_markup()

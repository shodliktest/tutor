"""
⌨️ BARCHA KLAVIATURALAR — Aiogram 3
WebApp tugmalari qo'shilgan:
  result_keyboard     → "🔍 Batafsil tahlil" WebApp oynasi
  history_keyboard    → "📜 Natijalarim" WebApp oynasi
  test_webapp_keyboard → To'liq Web rejimda test yechish
"""
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import SUBJECTS, DIFFICULTY_LEVELS


def _wa(path: str = "") -> str:
    """Streamlit WebApp URL yasash."""
    try:
        from config import STREAMLIT_URL
        base = STREAMLIT_URL.rstrip("/")
    except ImportError:
        base = "https://your-app.streamlit.app"
    return f"{base}{path}"


# ═══════════════════════════════════════════════════════════
# ASOSIY MENYU
# ═══════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════
# TEST BOSHQARUVI
# ═══════════════════════════════════════════════════════════

def test_info_keyboard(test_id: str) -> InlineKeyboardMarkup:
    """Test haqida ekran — 3 rejim: Inline, Poll, Web"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="▶️ Inline test",  callback_data=f"start_test_{test_id}"),
        InlineKeyboardButton(text="📊 Poll test",    callback_data=f"start_poll_{test_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🌐 Web test",    callback_data=f"start_web_{test_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Reyting",     callback_data=f"lb_test_{test_id}"),
        InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"),
    )
    return builder.as_markup()


def test_webapp_keyboard(test_id: str, user_id: int) -> InlineKeyboardMarkup:
    """WebApp orqali test yechish tugmasi."""
    url = _wa(f"/?mode=test&test_id={test_id}&user_id={user_id}")
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🌐 Web oynada yechish",
        web_app=WebAppInfo(url=url)
    ))
    builder.row(
        InlineKeyboardButton(text="▶️ Bot ichida", callback_data=f"start_test_{test_id}"),
        InlineKeyboardButton(text="❌ Bekor",      callback_data="main_menu"),
    )
    return builder.as_markup()


def result_keyboard(test_id: str, result_id: str, user_id: int = 0) -> InlineKeyboardMarkup:
    """
    Test yakunlanganda natija keyboard.
    user_id > 0 bo'lsa — WebApp tahlil va tarix tugmalari ko'rsatiladi.
    """
    builder = InlineKeyboardBuilder()

    if user_id:
        review_url  = _wa(f"/?mode=review&result_id={result_id}&user_id={user_id}")
        history_url = _wa(f"/?mode=history&user_id={user_id}")
        builder.row(InlineKeyboardButton(
            text="🔍 Batafsil tahlil (Web)",
            web_app=WebAppInfo(url=review_url)
        ))
        builder.row(InlineKeyboardButton(
            text="📜 Natijalar tarixi",
            web_app=WebAppInfo(url=history_url)
        ))
    else:
        # Fallback — bot ichidagi tahlil
        builder.row(InlineKeyboardButton(
            text="🔍 Batafsil tahlil",
            callback_data=f"analysis_{result_id}"
        ))

    builder.row(
        InlineKeyboardButton(text="🔄 Qaytadan",  callback_data=f"start_test_{test_id}"),
        InlineKeyboardButton(text="📊 Poll rejim", callback_data=f"start_poll_{test_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Reyting", callback_data=f"lb_test_{test_id}"),
        InlineKeyboardButton(text="🏠 Asosiy",  callback_data="main_menu"),
    )
    return builder.as_markup()


def history_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Natijalar tarixi WebApp oynasi."""
    url = _wa(f"/?mode=history&user_id={user_id}")
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📜 Natijalarim (Web oyna)",
        web_app=WebAppInfo(url=url)
    ))
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    return builder.as_markup()


# ═══════════════════════════════════════════════════════════
# JAVOB TUGMALARI (inline test)
# ═══════════════════════════════════════════════════════════

def answer_keyboard(letters: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for letter in letters:
        builder.add(InlineKeyboardButton(text=letter, callback_data=f"ans_{letter}"))
    builder.adjust(len(letters))
    builder.row(InlineKeyboardButton(text="❌ Testni to'xtatish", callback_data="cancel_test"))
    return builder.as_markup()


def feedback_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⏳ Keyingi savolga o'tilmoqda...", callback_data="wait_btn"))
    builder.row(InlineKeyboardButton(text="❌ Testni to'xtatish", callback_data="cancel_test"))
    return builder.as_markup()


# ═══════════════════════════════════════════════════════════
# TEST YARATISH
# ═══════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════
# REYTING
# ═══════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════
# ADMIN
# ═══════════════════════════════════════════════════════════

def admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users"),
        InlineKeyboardButton(text="📋 Testlar",          callback_data="admin_tests"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 Statistika",    callback_data="admin_stats"),
        InlineKeyboardButton(text="📢 Broadcast",     callback_data="admin_broadcast"),
    )
    builder.row(
        InlineKeyboardButton(text="🚫 Bloklash",       callback_data="admin_block"),
        InlineKeyboardButton(text="🗑 Test o'chirish",  callback_data="admin_del_test"),
    )
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    return builder.as_markup()

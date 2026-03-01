"""
⌨️ BARCHA KLAVIATURALAR — Aiogram 3
Reply va Inline tugmalar to'plami
"""
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import SUBJECTS, DIFFICULTY_LEVELS


# ═══════════════════════════════════════════════════════════
# 1. DOIMIY REPLY MENYU
# ═══════════════════════════════════════════════════════════

def main_reply_keyboard(user_id: int = None) -> ReplyKeyboardMarkup:
    """Asosiy pastki menyu"""
    kb = [
        [KeyboardButton(text="📚 Testlar"),      KeyboardButton(text="➕ Test Yaratish")],
        [KeyboardButton(text="📊 Natijalarim"),  KeyboardButton(text="🏆 Reyting")],
        [KeyboardButton(text="🗂 Mening testlarim"), KeyboardButton(text="👤 Profil")],
        [KeyboardButton(text="ℹ️ Yordam")],
    ]
    if user_id:
        from config import ADMIN_IDS
        if user_id in ADMIN_IDS:
            kb.append([KeyboardButton(text="👑 Admin Panel")])
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Bo'limni tanlang..."
    )


# ═══════════════════════════════════════════════════════════
# 2. TEST YARATISH KLAVIATURALARI
# ═══════════════════════════════════════════════════════════

def create_subject_keyboard() -> InlineKeyboardMarkup:
    """Fan tanlash"""
    builder = InlineKeyboardBuilder()
    for s in SUBJECTS:
        builder.add(InlineKeyboardButton(text=s, callback_data=f"set_subj_{s}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="✏️ Boshqa (Qo'lda yozish)", callback_data="set_subj_other"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    return builder.as_markup()


def difficulty_keyboard(prefix: str = "diff_") -> InlineKeyboardMarkup:
    """Qiyinlik tanlash"""
    builder = InlineKeyboardBuilder()
    for k, v in DIFFICULTY_LEVELS.items():
        builder.add(InlineKeyboardButton(text=v, callback_data=f"{prefix}{k}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    return builder.as_markup()


def test_visibility_keyboard() -> InlineKeyboardMarkup:
    """Maxfiylik tanlash"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌍 Ommaviy (Hamma ko'radi)", callback_data="vis_public"))
    builder.row(InlineKeyboardButton(text="🔗 Ssilka orqali", callback_data="vis_link"))
    builder.row(InlineKeyboardButton(text="🔒 Shaxsiy (Faqat o'zingizga)", callback_data="vis_private"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    return builder.as_markup()


# ═══════════════════════════════════════════════════════════
# 3. TEST KO'RSATISH VA BOSHLASH KLAVIATURALARI
# ═══════════════════════════════════════════════════════════

def test_info_keyboard(test_id: str) -> InlineKeyboardMarkup:
    """Test haqida ma'lumot ekranidagi tugmalar — 2 rejim tanlash"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="▶️ Inline test", callback_data=f"start_test_{test_id}"),
        InlineKeyboardButton(text="📊 Poll test",   callback_data=f"start_poll_{test_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Reyting",     callback_data=f"lb_test_{test_id}"),
        InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"),
    )
    return builder.as_markup()


def result_keyboard(test_id: str, result_id: str) -> InlineKeyboardMarkup:
    """Test yakunlanganda ko'rsatiladigan tugmalar"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📝 Batafsil tahlil", callback_data=f"analysis_{result_id}"))
    builder.row(
        InlineKeyboardButton(text="🔄 Qaytadan", callback_data=f"start_test_{test_id}"),
        InlineKeyboardButton(text="📊 Poll rejim", callback_data=f"start_poll_{test_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Reyting", callback_data=f"lb_test_{test_id}"),
        InlineKeyboardButton(text="🏠 Asosiy",  callback_data="main_menu"),
    )
    return builder.as_markup()


# ═══════════════════════════════════════════════════════════
# 4. TEST YECHISH (INLINE REJIM)
# ═══════════════════════════════════════════════════════════

def answer_keyboard(letters: list) -> InlineKeyboardMarkup:
    """Javob tugmalari (A, B, C, D ...)"""
    builder = InlineKeyboardBuilder()
    for letter in letters:
        builder.add(InlineKeyboardButton(text=letter, callback_data=f"ans_{letter}"))
    builder.adjust(len(letters))
    builder.row(InlineKeyboardButton(text="❌ Testni to'xtatish", callback_data="cancel_test"))
    return builder.as_markup()


def feedback_keyboard() -> InlineKeyboardMarkup:
    """Javob feedback ekrani tugmalari"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏳ Keyingi savolga o'tilmoqda...", callback_data="wait_btn"))
    builder.row(InlineKeyboardButton(text="❌ Testni to'xtatish", callback_data="cancel_test"))
    return builder.as_markup()


# ═══════════════════════════════════════════════════════════
# 5. LEADERBOARD VA ADMIN
# ═══════════════════════════════════════════════════════════

def leaderboard_keyboard(current: str = "global") -> InlineKeyboardMarkup:
    """Reyting ekrani tugmalari"""
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
    """Admin panel inline klaviaturasi"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users"),
        InlineKeyboardButton(text="📋 Testlar", callback_data="admin_tests"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
        InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast"),
    )
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    return builder.as_markup()

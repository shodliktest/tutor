"""
⌨️ INLINE VA REPLY KLAVIATURALAR (AIOGRAM 3)
Doimiy (Reply) menyu tizimi va Inline tugmalar jamlanmasi.
Hech narsa qisqartirilmadi.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import SUBJECTS, DIFFICULTY_LEVELS

# ==========================================
# 1. DOIMIY MENYU (REPLY KEYBOARD)
# ==========================================
def main_reply_keyboard(user_id: int = None) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📚 Testlar"), KeyboardButton(text="➕ Test Yaratish")],
        [KeyboardButton(text="📊 Natijalarim"), KeyboardButton(text="🏆 Reyting")],
        [KeyboardButton(text="🗂 Mening testlarim"), KeyboardButton(text="👤 Profil")],
        [KeyboardButton(text="ℹ️ Yordam")]
    ]
    if user_id:
        from config import ADMIN_IDS
        if user_id in ADMIN_IDS:
            kb.append([KeyboardButton(text="👨‍💼 Admin Panel")])
            
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Bo'limni tanlang...")


# ==========================================
# 2. INLINE TUGMALAR (ADMIN VA BOSHQALAR)
# ==========================================

def admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users"), InlineKeyboardButton(text="📋 Testlar", callback_data="admin_tests"))
    builder.row(InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"), InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast"))
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    return builder.as_markup()

def leaderboard_keyboard(current: str = "global") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌍 Umumiy" + (" ✓" if current == "global" else ""), callback_data="lb_global"), InlineKeyboardButton(text="📚 Fan bo'yicha", callback_data="lb_subject"))
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    return builder.as_markup()

def subjects_keyboard(callback_prefix: str = "browse_subj_") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for subject in SUBJECTS:
        builder.add(InlineKeyboardButton(text=subject, callback_data=f"{callback_prefix}{subject}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    return builder.as_markup()

def create_subject_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for subject in SUBJECTS:
        builder.add(InlineKeyboardButton(text=subject, callback_data=f"set_subj_{subject}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="✏️ Boshqa (Qo'lda yozish)", callback_data="set_subj_other"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    return builder.as_markup()

def difficulty_keyboard(callback_prefix: str = "diff_") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🟢 Oson", callback_data=f"{callback_prefix}easy"), InlineKeyboardButton(text="🟡 O'rtacha", callback_data=f"{callback_prefix}medium"), InlineKeyboardButton(text="🔴 Qiyin", callback_data=f"{callback_prefix}hard"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    return builder.as_markup()

def test_visibility_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌍 Ommaviy (Hamma ko'radi)", callback_data="vis_public"))
    builder.row(InlineKeyboardButton(text="🔗 Link orqali (Faqat ssilka)", callback_data="vis_link"))
    builder.row(InlineKeyboardButton(text="🔒 Shaxsiy (Faqat o'zingizga)", callback_data="vis_private"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    return builder.as_markup()

def tests_list_keyboard(tests: list, user_results: list, subject: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for test in tests:
        test_id = test.get("test_id")
        title = test.get("title", "Nomsiz Test")
        attempts = sum(1 for r in user_results if r.get("test_id") == test_id)
        status = f" (Yechilgan: {attempts} marta)" if attempts > 0 else " 🆕"
        builder.row(InlineKeyboardButton(text=f"{title}{status}", callback_data=f"view_test_{test_id}"))
    builder.row(InlineKeyboardButton(text="◀️ Fanlar ro'yxatiga", callback_data="browse_subjects"))
    return builder.as_markup()

def test_info_keyboard(test_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="▶️ Testni boshlash", callback_data=f"start_test_{test_id}"))
    builder.row(InlineKeyboardButton(text="🏆 Reyting", callback_data=f"lb_test_{test_id}"), InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    return builder.as_markup()

def result_keyboard(test_id: str, result_id: str, passed: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📝 Tahlil va Izohlar", callback_data=f"analysis_{result_id}"))
    builder.row(InlineKeyboardButton(text="🔄 Qaytadan ishlash", callback_data=f"view_test_{test_id}"), InlineKeyboardButton(text="🏆 Reyting", callback_data=f"lb_test_{test_id}"))
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    return builder.as_markup()

def finish_test_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏁 Testni yakunlash", callback_data="finish_test"))
    return builder.as_markup()

def multiple_choice_keyboard(options: list, question_index: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for opt in options:
        letter = opt.split(')')[0] + ')' if ')' in opt else opt[:2]
        builder.add(InlineKeyboardButton(text=letter, callback_data=f"ans_{question_index}_{letter}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🏁 Testni yakunlash", callback_data="finish_test"))
    return builder.as_markup()

def true_false_keyboard(question_index: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Ha", callback_data=f"ans_{question_index}_Ha"), InlineKeyboardButton(text="❌ Yo'q", callback_data=f"ans_{question_index}_Yo'q"))
    builder.row(InlineKeyboardButton(text="🏁 Testni yakunlash", callback_data="finish_test"))
    return builder.as_markup()

def multi_select_keyboard(options: list, question_index: int, selected: list = None) -> InlineKeyboardMarkup:
    if selected is None: selected = []
    builder = InlineKeyboardBuilder()
    for opt in options:
        letter = opt.split(')')[0] + ')' if ')' in opt else opt[:2]
        mark = " ✅" if letter in selected else ""
        builder.add(InlineKeyboardButton(text=f"{letter}{mark}", callback_data=f"msel_{question_index}_{letter}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"next_{question_index}"), InlineKeyboardButton(text="🏁 Testni yakunlash", callback_data="finish_test"))
    return builder.as_markup()

def explanation_keyboard(question_index: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💡 Tushundim (Keyingi ➡️)", callback_data=f"go_next_{question_index}"))
    builder.row(InlineKeyboardButton(text="🏁 Testni yakunlash", callback_data="finish_test"))
    return builder.as_markup()
    

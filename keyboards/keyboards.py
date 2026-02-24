"""
⌨️ INLINE KLAVIATURALAR (AIOGRAM 3)
Barcha bot klaviaturalari to'liq moslashtirildi.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import SUBJECTS, DIFFICULTY_LEVELS, TEST_TYPES

def main_menu_keyboard(user_id: int = None) -> InlineKeyboardMarkup:
    """Asosiy menyu"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📚 Testlar", callback_data="browse_all"),
        InlineKeyboardButton(text="➕ Test Yaratish", callback_data="create_test")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Natijalarim", callback_data="profile_results"),
        InlineKeyboardButton(text="🏆 Reyting", callback_data="lb_global")
    )
    builder.row(
        InlineKeyboardButton(text="👤 Profil", callback_data="profile_view"),
        InlineKeyboardButton(text="ℹ️ Yordam", callback_data="help")
    )
    
    # Admin tugmasi faqat adminlarga ko'rinadi
    if user_id:
        from config import ADMIN_IDS
        if user_id in ADMIN_IDS:
            builder.row(InlineKeyboardButton(text="👨‍💼 Admin Panel", callback_data="admin_panel"))
            
    return builder.as_markup()

def admin_keyboard() -> InlineKeyboardMarkup:
    """Admin panel klaviaturasi"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users"),
        InlineKeyboardButton(text="📋 Testlar", callback_data="admin_tests")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
        InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast")
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin_settings"),
        InlineKeyboardButton(text="🗑 Test o'chirish", callback_data="admin_delete_test")
    )
    builder.row(InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu"))
    return builder.as_markup()

def leaderboard_keyboard(current: str = "global") -> InlineKeyboardMarkup:
    """Leaderboard turi"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌍 Umumiy" + (" ✓" if current == "global" else ""), callback_data="lb_global"),
        InlineKeyboardButton(text="📚 Fan bo'yicha" + (" ✓" if current == "subject" else ""), callback_data="lb_subject")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Bu oy" + (" ✓" if current == "monthly" else ""), callback_data="lb_monthly"),
        InlineKeyboardButton(text="🏆 Test bo'yicha" + (" ✓" if current == "test" else ""), callback_data="lb_by_test")
    )
    builder.row(InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu"))
    return builder.as_markup()

def subjects_keyboard(callback_prefix: str = "browse_subj_") -> InlineKeyboardMarkup:
    """Fanlar klaviaturasi"""
    builder = InlineKeyboardBuilder()
    for subject in SUBJECTS:
        builder.add(InlineKeyboardButton(text=subject, callback_data=f"{callback_prefix}{subject}"))
    builder.adjust(2) # Tugmalarni 2 tadan qilib taxlaydi
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="main_menu"))
    return builder.as_markup()

def difficulty_keyboard(callback_prefix: str = "diff_") -> InlineKeyboardMarkup:
    """Qiyinlik darajasi"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🟢 Oson", callback_data=f"{callback_prefix}easy"),
        InlineKeyboardButton(text="🟡 O'rtacha", callback_data=f"{callback_prefix}medium"),
        InlineKeyboardButton(text="🔴 Qiyin", callback_data=f"{callback_prefix}hard")
    )
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    return builder.as_markup()

def test_visibility_keyboard() -> InlineKeyboardMarkup:
    """Test maxfiylik darajasini tanlash"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌍 Ommaviy (Hamma ko'radi)", callback_data="vis_public"))
    builder.row(InlineKeyboardButton(text="🔗 Link orqali (Faqat ssilka)", callback_data="vis_link"))
    builder.row(InlineKeyboardButton(text="🔒 Shaxsiy (Faqat o'zingizga)", callback_data="vis_private"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    return builder.as_markup()

def tests_list_keyboard(tests: list, user_results: list, subject: str, page: int = 1) -> InlineKeyboardMarkup:
    """Testlar ro'yxati va urinishlar soni"""
    builder = InlineKeyboardBuilder()
    
    for test in tests:
        test_id = test.get("test_id")
        title = test.get("title", "Nomsiz Test")
        
        # Foydalanuvchi bu testni necha marta yechganini hisoblash
        attempts = sum(1 for r in user_results if r.get("test_id") == test_id)
        status = f" (Yechilgan: {attempts} marta)" if attempts > 0 else " 🆕"
        
        builder.row(InlineKeyboardButton(text=f"{title}{status}", callback_data=f"view_test_{test_id}"))
        
    builder.row(InlineKeyboardButton(text="◀️ Fanlar ro'yxatiga", callback_data="browse_subjects"))
    return builder.as_markup()

def test_info_keyboard(test_id: str) -> InlineKeyboardMarkup:
    """Test ma'lumotlari ostidagi tugmalar"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="▶️ Testni boshlash", callback_data=f"start_test_{test_id}"))
    builder.row(
        InlineKeyboardButton(text="🏆 Reyting", callback_data=f"lb_test_{test_id}"),
        InlineKeyboardButton(text="◀️ Orqaga", callback_data="browse_all")
    )
    return builder.as_markup()

def result_keyboard(test_id: str, result_id: str, passed: bool) -> InlineKeyboardMarkup:
    """Test yakunlangandagi tugmalar"""
    builder = InlineKeyboardBuilder()
    
    # Agar foydalanuvchi o'tish foizidan o'tgan bo'lsa, sertifikat tugmasi chiqadi
    if passed:
        builder.row(InlineKeyboardButton(text="🎓 Sertifikatni yuklab olish", callback_data=f"cert_{result_id}"))
        
    builder.row(
        InlineKeyboardButton(text="🔄 Qaytadan ishlash", callback_data=f"view_test_{test_id}"),
        InlineKeyboardButton(text="🏆 Reyting", callback_data=f"lb_test_{test_id}")
    )
    builder.row(InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu"))
    return builder.as_markup()

def finish_test_keyboard() -> InlineKeyboardMarkup:
    """Test yechish jarayonida ixtiyoriy yakunlash tugmasi"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏁 Testni yakunlash", callback_data="finish_test"))
    return builder.as_markup()

def upload_method_keyboard() -> InlineKeyboardMarkup:
    """Test yaratish usulini tanlash"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📂 Fayl yuklash (TXT, DOCX, PDF)", callback_data="upload_file"),
        InlineKeyboardButton(text="✍️ Qo'lda yaratish", callback_data="manual_create")
    )
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    return builder.as_markup()

# ══════════════════════════════════════════════════════════
# 🎯 TEST YECHISH JARAYONIDAGI JAVOB TUGMALARI
# ══════════════════════════════════════════════════════════

def multiple_choice_keyboard(options: list, question_index: int) -> InlineKeyboardMarkup:
    """1 to'g'ri javobli test uchun A, B, C, D tugmalari"""
    builder = InlineKeyboardBuilder()
    for opt in options:
        # "A) Variant" dan faqat "A)" ni ajratib olamiz
        letter = opt.split(')')[0] + ')' if ')' in opt else opt[:2]
        builder.add(InlineKeyboardButton(text=letter, callback_data=f"ans_{question_index}_{letter}"))
    builder.adjust(2) # 2 tadan qilib joylash
    return builder.as_markup()

def true_false_keyboard(question_index: int) -> InlineKeyboardMarkup:
    """Ha/Yo'q testi uchun tugmalar"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Ha", callback_data=f"ans_{question_index}_Ha"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data=f"ans_{question_index}_Yo'q")
    )
    return builder.as_markup()

def multi_select_keyboard(options: list, question_index: int, selected: list = None) -> InlineKeyboardMarkup:
    """Ko'p javobli test uchun tugmalar (Belgilanganlariga ✅ qoyiladi)"""
    if selected is None:
        selected = []
        
    builder = InlineKeyboardBuilder()
    for opt in options:
        letter = opt.split(')')[0] + ')' if ')' in opt else opt[:2]
        mark = " ✅" if letter in selected else ""
        builder.add(InlineKeyboardButton(text=f"{letter}{mark}", callback_data=f"msel_{question_index}_{letter}"))
        
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"next_{question_index}"))
    return builder.as_markup()

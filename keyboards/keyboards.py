"""
⌨️ INLINE KLAVIATURALAR
Barcha bot klaviaturalari
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from config import SUBJECTS, DIFFICULTY_LEVELS, TEST_TYPES


def main_menu_keyboard():
    """Asosiy menyu"""
    keyboard = [
        [
            InlineKeyboardButton("📚 Testlar", callback_data="browse_all"),
            InlineKeyboardButton("➕ Test Yaratish", callback_data="create_test")
        ],
        [
            InlineKeyboardButton("📊 Natijalarim", callback_data="profile_results"),
            InlineKeyboardButton("🏆 Reyting", callback_data="lb_global")
        ],
        [
            InlineKeyboardButton("👤 Profil", callback_data="profile_view"),
            InlineKeyboardButton("ℹ️ Yordam", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def subjects_keyboard(callback_prefix="browse_subj_"):
    """Fanlar klaviaturasi"""
    keyboard = []
    row = []
    for i, subject in enumerate(SUBJECTS):
        row.append(InlineKeyboardButton(subject, callback_data=f"{callback_prefix}{subject}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)


def difficulty_keyboard(callback_prefix="diff_"):
    """Qiyinlik darajasi"""
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"{callback_prefix}{key}")]
        for key, label in DIFFICULTY_LEVELS.items()
    ]
    keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data="create_back")])
    return InlineKeyboardMarkup(keyboard)


def test_type_keyboard():
    """Test turi tanlash"""
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"type_{key}")]
        for key, label in TEST_TYPES.items()
    ]
    keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data="create_back")])
    return InlineKeyboardMarkup(keyboard)


def visibility_keyboard():
    """Ko'rinish darajasi"""
    keyboard = [
        [InlineKeyboardButton("🌍 Ommaviy", callback_data="vis_public")],
        [InlineKeyboardButton("🔗 Link orqali", callback_data="vis_link")],
        [InlineKeyboardButton("🔒 Faqat o'zim", callback_data="vis_private")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="create_back")]
    ]
    return InlineKeyboardMarkup(keyboard)


def upload_method_keyboard():
    """Fayl yuklash usuli"""
    keyboard = [
        [InlineKeyboardButton("📁 TXT fayl yuklash", callback_data="upload_txt")],
        [InlineKeyboardButton("📄 PDF fayl yuklash", callback_data="upload_pdf")],
        [InlineKeyboardButton("📝 DOCX fayl yuklash", callback_data="upload_docx")],
        [InlineKeyboardButton("✏️ Qo'lda kiritish", callback_data="manual_create")],
        [InlineKeyboardButton("📋 Namuna fayllarni ko'rish", callback_data="show_samples")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def tests_list_keyboard(tests: list, page: int = 0, subject: str = None):
    """Testlar ro'yxati"""
    keyboard = []
    
    # Har bir test uchun tugma
    for test in tests:
        title = test.get("title", "Nomsiz")[:35]
        count = test.get("question_count", 0)
        diff = {"easy": "🟢", "medium": "🟡", "hard": "🔴", "expert": "⚡"}.get(test.get("difficulty"), "⚪")
        
        keyboard.append([
            InlineKeyboardButton(
                f"{diff} {title} ({count} ta savol)",
                callback_data=f"test_info_{test['test_id']}"
            )
        ])
    
    # Navigatsiya
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️", callback_data=f"browse_page_{page-1}_{subject or 'all'}"))
    if len(tests) >= 10:
        nav_row.append(InlineKeyboardButton("▶️", callback_data=f"browse_page_{page+1}_{subject or 'all'}"))
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🔙 Fanlar", callback_data="browse_subjects")])
    return InlineKeyboardMarkup(keyboard)


def test_info_keyboard(test_id: str, attempts_left: int = 3, is_creator: bool = False):
    """Test ma'lumotlari sahifasi"""
    keyboard = []
    
    if attempts_left > 0:
        keyboard.append([
            InlineKeyboardButton(
                f"▶️ Testni boshlash ({attempts_left} urinish qoldi)",
                callback_data=f"take_test_{test_id}"
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("🚫 Urinishlar tugagan", callback_data="no_attempts")
        ])
    
    keyboard.append([
        InlineKeyboardButton("📊 Natijalari", callback_data=f"test_results_{test_id}"),
        InlineKeyboardButton("🏆 Top 10", callback_data=f"lb_test_{test_id}")
    ])
    
    if is_creator:
        keyboard.append([
            InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"edit_test_{test_id}"),
            InlineKeyboardButton("🗑 O'chirish", callback_data=f"delete_test_{test_id}")
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data="browse_all")])
    return InlineKeyboardMarkup(keyboard)


def multiple_choice_keyboard(options: list, question_idx: int, answered: set = None):
    """Bir javobli test klaviaturasi"""
    keyboard = []
    letters = ["A", "B", "C", "D", "E", "F"]
    
    for i, option in enumerate(options):
        letter = letters[i] if i < len(letters) else str(i+1)
        prefix = "✅" if (answered and i in answered) else "🔘"
        
        text = f"{prefix} {letter}) {option[:40]}"
        keyboard.append([
            InlineKeyboardButton(text, callback_data=f"ans_{question_idx}_{i}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data=f"ans_{question_idx}_skip"),
    ])
    return InlineKeyboardMarkup(keyboard)


def true_false_keyboard(question_idx: int):
    """Ha/Yo'q klaviaturasi"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Ha (To'g'ri)", callback_data=f"ans_{question_idx}_0"),
            InlineKeyboardButton("❌ Yo'q (Noto'g'ri)", callback_data=f"ans_{question_idx}_1")
        ],
        [InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data=f"ans_{question_idx}_skip")]
    ]
    return InlineKeyboardMarkup(keyboard)


def multi_select_keyboard(options: list, question_idx: int, selected: set = None):
    """Ko'p javobli test klaviaturasi"""
    if selected is None:
        selected = set()
    keyboard = []
    letters = ["A", "B", "C", "D", "E", "F"]
    
    for i, option in enumerate(options):
        letter = letters[i] if i < len(letters) else str(i+1)
        prefix = "✅" if i in selected else "⬜"
        text = f"{prefix} {letter}) {option[:40]}"
        keyboard.append([
            InlineKeyboardButton(text, callback_data=f"multi_{question_idx}_{i}")
        ])
    
    keyboard.extend([
        [InlineKeyboardButton("✔️ Javobni tasdiqlash", callback_data=f"ans_{question_idx}_confirm")],
        [InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data=f"ans_{question_idx}_skip")]
    ])
    return InlineKeyboardMarkup(keyboard)


def finish_test_keyboard(test_id: str):
    """Test tugash klaviaturasi"""
    keyboard = [
        [InlineKeyboardButton("✅ Testni tugatish", callback_data=f"finish_{test_id}")],
        [InlineKeyboardButton("◀️ Davom etish", callback_data=f"continue_test_{test_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def result_keyboard(test_id: str, result_id: str, passed: bool):
    """Natija sahifasi klaviaturasi"""
    keyboard = [
        [InlineKeyboardButton("📋 Batafsil tahlil", callback_data=f"detail_result_{result_id}")],
        [InlineKeyboardButton("🔄 Qayta ishlash", callback_data=f"take_test_{test_id}")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data=f"lb_test_{test_id}")],
        [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="main_menu")]
    ]
    
    if passed:
        keyboard.insert(1, [
            InlineKeyboardButton("📜 Sertifikat", callback_data=f"cert_{result_id}")
        ])
    
    return InlineKeyboardMarkup(keyboard)


def admin_keyboard():
    """Admin panel klaviaturasi"""
    keyboard = [
        [
            InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users"),
            InlineKeyboardButton("📋 Testlar", callback_data="admin_tests")
        ],
        [
            InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
            InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("⚙️ Sozlamalar", callback_data="admin_settings"),
            InlineKeyboardButton("🗑 Test o'chirish", callback_data="admin_delete_test")
        ],
        [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def leaderboard_keyboard(current: str = "global"):
    """Leaderboard turi"""
    keyboard = [
        [
            InlineKeyboardButton("🌍 Umumiy" + (" ✓" if current == "global" else ""), callback_data="lb_global"),
            InlineKeyboardButton("📚 Fan bo'yicha" + (" ✓" if current == "subject" else ""), callback_data="lb_subject")
        ],
        [
            InlineKeyboardButton("📅 Bu oy" + (" ✓" if current == "monthly" else ""), callback_data="lb_monthly"),
            InlineKeyboardButton("🏆 Test bo'yicha" + (" ✓" if current == "test" else ""), callback_data="lb_by_test")
        ],
        [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

"""
⌨️ BARCHA KLAVIATURALAR — Aiogram 3
✅ Telegram Web App tugmalari
✅ Test tanlanganda 3 usul: Inline, Poll, WebApp
✅ Fayl/poll tayyor bo'lgach Web App da tahrirlash imkoni
"""
import json
import base64
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import SUBJECTS, DIFFICULTY_LEVELS, WEBAPP_BASE_URL


def _encode(data: dict) -> str:
    """Dict → URL-safe base64 string"""
    return base64.b64encode(
        json.dumps(data, ensure_ascii=False, default=str).encode()
    ).decode()


def _webapp_url(page: str, data=None) -> str:
    """
    GitHub Pages URL yasash.
    data - dict yoki list bo'lishi mumkin.
    URL 2048 belgidan oshsa — bo'sh qaytadi.
    """
    if not WEBAPP_BASE_URL:
        return ""
    base = f"{WEBAPP_BASE_URL}/{page}"
    if data is not None:
        encoded = _encode(data) if isinstance(data, dict) else base64.b64encode(
            json.dumps(data, ensure_ascii=False, default=str).encode()
        ).decode()
        url = f"{base}?data={encoded}"
        return url if len(url) <= 2048 else ""
    return base


# ══════════════════════════════════════════════════════════
# ASOSIY KLAVIATURA
# ══════════════════════════════════════════════════════════

def main_reply_keyboard(user_id: int = None) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📚 Testlar"),          KeyboardButton(text="➕ Test Yaratish")],
        [KeyboardButton(text="📊 Natijalarim"),       KeyboardButton(text="🏆 Reyting")],
        [KeyboardButton(text="🗂 Mening testlarim"),  KeyboardButton(text="👤 Profil")],
        [KeyboardButton(text="ℹ️ Yordam")],
    ]
    if user_id:
        from config import ADMIN_IDS
        if user_id in ADMIN_IDS:
            kb.append([KeyboardButton(text="👑 Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                               input_field_placeholder="Bo'limni tanlang...")


# ══════════════════════════════════════════════════════════
# TEST YARATISH KLAVIATURAI
# ══════════════════════════════════════════════════════════

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
    builder.row(InlineKeyboardButton(text="🌍 Ommaviy",        callback_data="vis_public"))
    builder.row(InlineKeyboardButton(text="🔗 Ssilka orqali",  callback_data="vis_link"))
    builder.row(InlineKeyboardButton(text="🔒 Shaxsiy",         callback_data="vis_private"))
    builder.row(InlineKeyboardButton(text="❌ Bekor",            callback_data="cancel_creation"))
    return builder.as_markup()


# ══════════════════════════════════════════════════════════
# TEST TANLASH — 3 USUL
# ══════════════════════════════════════════════════════════

def test_info_keyboard(test_id: str, test_data: dict = None) -> InlineKeyboardMarkup:
    """
    Test tanlanganda ko'rsatiladigan klaviatura.
    Usullar:
      🎮 Web App   — Firebase siz, URL da base64
      ▶️  Inline    — savol-javob xabar orqali
      📊 Poll      — native Telegram quiz poll
    """
    builder = InlineKeyboardBuilder()

    # ── 1. WEB APP (agar URL mavjud va test kichik bo'lsa) ──
    if WEBAPP_BASE_URL and test_data:
        payload = _build_test_payload(test_data)
        url = _webapp_url("test.html", payload)
        if url:
            builder.row(InlineKeyboardButton(
                text="🎮 Web App orqali yechish",
                web_app=WebAppInfo(url=url)
            ))

    # ── 2. INLINE + POLL ──
    builder.row(
        InlineKeyboardButton(text="▶️ Inline test",   callback_data=f"start_test_{test_id}"),
        InlineKeyboardButton(text="📊 Poll test",      callback_data=f"start_poll_{test_id}"),
    )

    # ── 3. QO'SHIMCHA ──
    builder.row(
        InlineKeyboardButton(text="🏆 Reyting",        callback_data=f"lb_test_{test_id}"),
        InlineKeyboardButton(text="🏠 Asosiy menyu",   callback_data="main_menu"),
    )
    return builder.as_markup()


def _build_test_payload(test_data: dict) -> dict:
    """
    test.html uchun zarur ma'lumotlarni tayyorlash.
    Barcha savol turlarini qo'llab-quvvatlaydi.
    """
    raw_qs = test_data.get("questions", [])
    formatted_qs = []
    for q in raw_qs:
        qtype = q.get("type", "multiple_choice")
        # Turlarni normallashtirish
        if qtype in ("multiple_choice", "multi_select"):
            t = "multiple"
        elif qtype in ("true_false",):
            t = "true_false"
        elif qtype in ("text_input", "fill_blank"):
            t = "fill_blank"
        elif qtype in ("matching", "match"):
            t = "matching"
        elif qtype in ("ordering", "order"):
            t = "ordering"
        else:
            t = "multiple"

        fq = {
            "text":        q.get("text") or q.get("question", ""),
            "type":        t,
            "explanation": q.get("explanation", ""),
        }
        if t in ("multiple", "true_false"):
            fq["options"] = q.get("options", [])
            fq["correct"] = q.get("correct", 0)
            # Agar correct string bo'lsa (poll dan) — indeksga o'tkazish
            if isinstance(fq["correct"], str):
                opts = fq["options"]
                try:
                    fq["correct"] = next(
                        i for i, o in enumerate(opts)
                        if o.strip() == fq["correct"].strip()
                    )
                except StopIteration:
                    fq["correct"] = 0
        elif t == "fill_blank":
            fq["correctAnswer"] = q.get("correctAnswer") or q.get("correct_answer", "")
        elif t == "matching":
            fq["pairs"] = q.get("pairs", [])
        elif t == "ordering":
            fq["words"] = q.get("words") or q.get("items", [])

        formatted_qs.append(fq)

    return {
        "test_id":            test_data.get("test_id", test_data.get("id", "")),
        "title":              test_data.get("title", "Test"),
        "category":           test_data.get("category", ""),
        "difficulty":         test_data.get("difficulty", ""),
        "timeLimit":          test_data.get("time_limit", 0),
        "passScore":          test_data.get("passing_score", 60),
        "showResult":         test_data.get("show_result", True),
        "shuffleQuestions":   test_data.get("shuffle_questions", False),
        "questions":          formatted_qs,
    }


# ══════════════════════════════════════════════════════════
# NATIJA KLAVIATURASI
# ══════════════════════════════════════════════════════════

def result_keyboard(test_id: str, result_id: str,
                    result_data: dict = None) -> InlineKeyboardMarkup:
    """Test yakunlangandan keyin ko'rsatiladigan klaviatura."""
    builder = InlineKeyboardBuilder()

    # Web App tahlil
    if result_data and WEBAPP_BASE_URL:
        url = _webapp_url("review.html", result_data)
        if url:
            builder.row(InlineKeyboardButton(
                text="🔍 Batafsil tahlil (Web App)",
                web_app=WebAppInfo(url=url)
            ))

    builder.row(InlineKeyboardButton(
        text="📊 Oddiy tahlil",
        callback_data=f"analysis_{result_id}"
    ))
    builder.row(
        InlineKeyboardButton(text="🔄 Qaytadan",    callback_data=f"start_test_{test_id}"),
        InlineKeyboardButton(text="📊 Poll rejim",   callback_data=f"start_poll_{test_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Reyting",  callback_data=f"lb_test_{test_id}"),
        InlineKeyboardButton(text="🏠 Asosiy",   callback_data="main_menu"),
    )
    return builder.as_markup()


# ══════════════════════════════════════════════════════════
# NATIJALAR TARIXI
# ══════════════════════════════════════════════════════════

def webapp_history_keyboard(user_id: int, results: list) -> InlineKeyboardMarkup:
    """Natijalar tarixi — Web App popup (natijalar base64 URL da)"""
    builder = InlineKeyboardBuilder()
    if WEBAPP_BASE_URL and results:
        url = _webapp_url("history.html", results)
        if url:
            builder.row(InlineKeyboardButton(
                text="📜 Natijalar tarixini ko'rish",
                web_app=WebAppInfo(url=url)
            ))
    builder.row(
        InlineKeyboardButton(text="📋 Oddiy ro'yxat",  callback_data="results_p0"),
        InlineKeyboardButton(text="🏠 Asosiy",          callback_data="main_menu"),
    )
    return builder.as_markup()


# ══════════════════════════════════════════════════════════
# TEST YARATISH — WEB APP OCHISH KLAVIATURASI
# ══════════════════════════════════════════════════════════

def webapp_create_keyboard(existing_questions: list = None) -> InlineKeyboardMarkup:
    """
    Test yaratish uchun asosiy tanlov klaviaturasi.
    existing_questions — fayl/polldan chiqqan savollar bo'lsa,
    create.html ga yuborib tahrirlash imkoni beriladi.
    """
    builder = InlineKeyboardBuilder()

    if WEBAPP_BASE_URL:
        if existing_questions:
            # Mavjud savollarni create.html ga base64 orqali yuborish
            payload = {"mode": "edit", "questions": existing_questions}
            url = _webapp_url("create.html", payload)
            if url:
                builder.row(InlineKeyboardButton(
                    text="🎨 Web App da ko'rish va tahrirlash",
                    web_app=WebAppInfo(url=url)
                ))
            else:
                # URL juda uzun — savollar ko'p, bo'sh create.html ochiladi
                url0 = _webapp_url("create.html")
                if url0:
                    builder.row(InlineKeyboardButton(
                        text="✨ Web App muharriri (bo'sh)",
                        web_app=WebAppInfo(url=url0)
                    ))
        else:
            # Bo'sh yaratish
            url = _webapp_url("create.html")
            if url:
                builder.row(InlineKeyboardButton(
                    text="✨ Web App orqali yaratish",
                    web_app=WebAppInfo(url=url)
                ))

    builder.row(
        InlineKeyboardButton(text="📁 Fayl (TXT/PDF)",   callback_data="method_file"),
        InlineKeyboardButton(text="📊 QuizBot forward",  callback_data="method_poll"),
    )
    builder.row(InlineKeyboardButton(text="❌ Bekor", callback_data="cancel_creation"))
    return builder.as_markup()


def after_parse_keyboard(questions: list, test_id: str = "") -> InlineKeyboardMarkup:
    """
    Fayl/poll orqali savollar tayyor bo'lgach ko'rsatiladigan klaviatura.
    Asosiy tugma: Web App da ko'rish va tahrirlash.
    """
    builder = InlineKeyboardBuilder()

    if WEBAPP_BASE_URL:
        payload = {"mode": "edit", "questions": questions}
        url = _webapp_url("create.html", payload)
        if url:
            builder.row(InlineKeyboardButton(
                text="🎨 Web App da ko'rish va tahrirlash",
                web_app=WebAppInfo(url=url)
            ))

    builder.row(InlineKeyboardButton(
        text=f"✅ Saqlash ({len(questions)} ta savol)",
        callback_data="proceed_to_subject"
    ))
    builder.row(
        InlineKeyboardButton(text="📄 TXT yuklab olish", callback_data="download_draft_txt"),
        InlineKeyboardButton(text="❌ Bekor",             callback_data="cancel_creation"),
    )
    return builder.as_markup()


# ══════════════════════════════════════════════════════════
# TEST YECHISH KLAVIATURAI
# ══════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════
# REYTING VA ADMIN
# ══════════════════════════════════════════════════════════

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

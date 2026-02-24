"""
👤 PROFIL VA NATIJALAR HANDLER
"""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from firebase.db import get_user, get_user_results, get_test


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi profili"""
    query = update.callback_query
    user_id = (query.from_user if query else update.effective_user).id

    if query:
        await query.answer()

    user = get_user(user_id)
    if not user:
        text = "❌ Profil topilmadi. /start ni bosing."
        if query:
            await query.message.edit_text(text)
        else:
            await update.message.reply_text(text)
        return

    total_tests = user.get("total_tests", 0)
    avg_score   = user.get("avg_score", 0)
    badges      = user.get("badges", [])
    role        = user.get("role", "user")
    # f-string tashqarisida apostrofli qiymatlar
    name        = user.get("name", "Noma'lum")
    nomalum     = "Noma'lum"

    role_map = {
        "admin":   "👑 Admin",
        "teacher": "👨‍🏫 O'qituvchi",
        "user":    "👤 Foydalanuvchi",
    }
    role_text = role_map.get(role, "👤")

    # So'nggi natijalar
    recent_results = get_user_results(user_id, limit=5)
    recent_text = ""
    if recent_results:
        recent_text = "\n📋 <b>So'nggi 5 ta test:</b>\n"
        for r in recent_results:
            test  = get_test(r.get("test_id", ""))
            title = test.get("title", "Test")[:20] if test else "Test"
            pct   = r.get("percentage", 0)
            icon  = "✅" if r.get("passed") else "❌"
            recent_text += f"  {icon} {title} — {pct:.0f}%\n"

    text = (
        f"👤 <b>MENING PROFILIM</b>\n\n"
        f"{role_text}\n"
        f"📛 Ism: <b>{name}</b>\n"
        f"🆔 ID: <code>{user_id}</code>\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 Statistika:\n"
        f"📝 Ishlagan testlar: <b>{total_tests}</b>\n"
        f"📈 O'rtacha natija: <b>{avg_score:.1f}%</b>\n"
        f"🏅 Badgelar: <b>{len(badges)}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{recent_text}"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Barcha natijalar", callback_data="profile_results"),
            InlineKeyboardButton("🏆 Mening reytingim", callback_data="lb_global"),
        ],
        [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="main_menu")],
    ])

    if query:
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")


async def my_results_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mening natijalarim"""
    query   = update.callback_query
    user_id = (query.from_user if query else update.effective_user).id

    if query:
        await query.answer()

    results = get_user_results(user_id, limit=20)

    if not results:
        text = "📭 Hali hech qanday test ishlamadingiz.\n\n📚 Testlar bo'limiga o'ting va boshlang!"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📚 Testlarga o'tish", callback_data="browse_all")
        ]])
        if query:
            await query.message.edit_text(text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)
        return

    text = f"📊 <b>MENING NATIJALARIM</b> ({len(results)} ta)\n\n"

    for r in results[:15]:
        test     = get_test(r.get("test_id", ""))
        title    = test.get("title", "Test")[:25] if test else "Test"
        pct      = r.get("percentage", 0)
        icon     = "✅" if r.get("passed") else "❌"
        date     = r.get("completed_at")
        date_str = date.strftime("%d.%m") if date and hasattr(date, "strftime") else ""
        text    += f"{icon} <b>{title}</b>\n   {pct:.0f}% — {date_str}\n\n"

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏠 Bosh sahifa", callback_data="main_menu")
    ]])

    if query:
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")


async def register_handler(update, context):
    pass

async def login_handler(update, context):
    pass
        

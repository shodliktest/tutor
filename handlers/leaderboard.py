"""
🏆 LEADERBOARD HANDLER
"""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from firebase.db import get_global_leaderboard, get_leaderboard_by_test
from keyboards.keyboards import leaderboard_keyboard


async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Leaderboard"""
    query = update.callback_query
    
    if query:
        await query.answer()
        data = query.data
        
        if data == "lb_global" or data == "leaderboard":
            await _show_global(query)
        elif data == "lb_subject":
            await _show_subject_select(query)
        elif data == "lb_monthly":
            await _show_monthly(query)
        elif data.startswith("lb_test_"):
            test_id = data.replace("lb_test_", "")
            await _show_test_lb(query, test_id)
    else:
        await _show_global_message(update.message)


async def _show_global(query):
    """Umumiy reyting"""
    users = get_global_leaderboard(limit=20)
    
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 17
    text = "🏆 <b>UMUMIY REYTING</b>\n\n"
    
    if not users:
        text += "Hali hech kim test ishlamagan.\nBirinchi bo'ling! 🚀"
    else:
        for i, user in enumerate(users):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            name = user.get("name", "Noma'lum")[:20]
            avg = user.get("avg_score", 0)
            total = user.get("total_tests", 0)
            text += f"{medal} <b>{name}</b> — {avg:.0f}% o'rtacha, {total} ta test\n"
    
    await query.message.edit_text(
        text,
        reply_markup=leaderboard_keyboard("global"),
        parse_mode="HTML"
    )


async def _show_global_message(message):
    users = get_global_leaderboard(limit=10)
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    text = "🏆 <b>UMUMIY REYTING (Top 10)</b>\n\n"
    
    for i, user in enumerate(users):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        name = user.get("name", "Noma'lum")[:20]
        avg = user.get("avg_score", 0)
        text += f"{medal} <b>{name}</b> — {avg:.0f}%\n"
    
    await message.reply_text(text, reply_markup=leaderboard_keyboard("global"), parse_mode="HTML")


async def _show_subject_select(query):
    """Fan tanlash"""
    from keyboards.keyboards import subjects_keyboard
    await query.message.edit_text(
        "📚 Qaysi fan bo'yicha reytingni ko'rmoqchisiz?",
        reply_markup=subjects_keyboard(callback_prefix="lb_subj_")
    )


async def _show_monthly(query):
    """Bu oylik reyting"""
    from datetime import datetime, timezone
    from firebase.config import get_db
    
    db = get_db()
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    results = (db.collection("results")
               .where("completed_at", ">=", month_start)
               .order_by("completed_at")
               .order_by("percentage", direction="DESCENDING")
               .limit(20)
               .stream())
    
    results_list = [r.to_dict() for r in results]
    
    text = f"📅 <b>{now.strftime('%B %Y')} — OYLIK REYTING</b>\n\n"
    
    user_scores = {}
    for r in results_list:
        uid = r.get("user_id")
        if uid not in user_scores:
            user_scores[uid] = {"name": "Noma'lum", "scores": []}
        user_scores[uid]["scores"].append(r.get("percentage", 0))
    
    sorted_users = sorted(
        user_scores.items(),
        key=lambda x: sum(x[1]["scores"]) / len(x[1]["scores"]),
        reverse=True
    )
    
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 17
    
    for i, (uid, data) in enumerate(sorted_users[:15]):
        from firebase.db import get_user
        user = get_user(int(uid))
        name = user.get("name", "Noma'lum")[:20] if user else "Noma'lum"
        avg = sum(data["scores"]) / len(data["scores"])
        count = len(data["scores"])
        medal = medals[i] if i < len(medals) else f"{i+1}."
        text += f"{medal} <b>{name}</b> — {avg:.0f}% o'rtacha, {count} ta test\n"
    
    if not sorted_users:
        text += "Bu oy hali hech kim test ishlamagan."
    
    await query.message.edit_text(
        text,
        reply_markup=leaderboard_keyboard("monthly"),
        parse_mode="HTML"
    )


async def _show_test_lb(query, test_id: str):
    """Test bo'yicha reyting"""
    from firebase.db import get_test
    results = get_leaderboard_by_test(test_id, limit=10)
    test = get_test(test_id)
    
    test_title = test.get("title", "Test") if test else "Test"
    
    text = f"🏆 <b>{test_title}</b>\nTop 10 nатижalar:\n\n"
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    
    if not results:
        text += "Hali hech kim bu testni ishlamagan."
    else:
        for i, r in enumerate(results):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            name = r.get("user_name", "Noma'lum")[:20]
            pct = r.get("best_percentage", 0)
            text += f"{medal} <b>{name}</b> — {pct:.0f}%\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Orqaga", callback_data=f"test_info_{test_id}")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

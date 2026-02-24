"""
🏆 LEADERBOARD HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Umumiy, oylik va ma'lum bir test bo'yicha kuchlilar ro'yxati
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from firebase.db import get_global_leaderboard, get_leaderboard_by_test, get_user, get_db
from keyboards.keyboards import leaderboard_keyboard

router = Router()

@router.callback_query(F.data.in_(["lb_global", "leaderboard"]))
async def show_global_lb(callback: CallbackQuery):
    await callback.answer()
    
    # Bazadan TOP 20 foydalanuvchini tortish
    users = get_global_leaderboard(limit=20)
    
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 17
    text = "🏆 <b>UMUMIY REYTING (TOP 20)</b>\n\n"
    
    if not users:
        text += "Hali hech kim test ishlamagan.\nBirinchi bo'ling! 🚀"
    else:
        for i, user in enumerate(users):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            name = user.get("name", "Noma'lum")[:20]
            avg_score = user.get("avg_score", 0)
            tests_count = user.get("total_tests", 0)
            
            text += f"{medal} <b>{name}</b> — {avg_score:.1f}% ({tests_count} ta test)\n"
            
    await callback.message.edit_text(text, reply_markup=leaderboard_keyboard("global"), parse_mode="HTML")

@router.callback_query(F.data == "lb_monthly")
async def show_monthly_lb(callback: CallbackQuery):
    await callback.answer()
    
    from datetime import datetime
    current_month = datetime.now().month
    
    db = get_db()
    results = db.collection("results").stream()
    
    user_monthly_scores = {}
    for r in results:
        data = r.to_dict()
        comp_time = data.get("completed_at")
        if comp_time and comp_time.month == current_month:
            uid = data.get("user_id")
            if uid not in user_monthly_scores:
                user_monthly_scores[uid] = []
            user_monthly_scores[uid].append(data.get("percentage", 0))
            
    # O'rtacha foiz bo'yicha saralash
    sorted_users = sorted(
        user_monthly_scores.items(),
        key=lambda x: sum(x[1])/len(x[1]), 
        reverse=True
    )[:20]
    
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 17
    text = f"📅 <b>BU OYNING ENG FAOL O'QUVCHILARI</b>\n\n"
    
    if not sorted_users:
        text += "Bu oy hali hech kim test ishlamagan."
    else:
        for i, (uid, scores) in enumerate(sorted_users):
            user = get_user(int(uid))
            name = user.get("name", "Noma'lum")[:20] if user else "Noma'lum"
            avg = sum(scores) / len(scores)
            count = len(scores)
            
            medal = medals[i] if i < len(medals) else f"{i+1}."
            text += f"{medal} <b>{name}</b> — {avg:.1f}% ({count} marta ishlagan)\n"
            
    await callback.message.edit_text(text, reply_markup=leaderboard_keyboard("monthly"), parse_mode="HTML")

@router.callback_query(F.data.startswith("lb_test_"))
async def show_specific_test_lb(callback: CallbackQuery):
    await callback.answer()
    test_id = callback.data.replace("lb_test_", "")
    
    from firebase.db import get_test
    results = get_leaderboard_by_test(test_id, limit=10)
    test = get_test(test_id)
    
    test_title = test.get("title", "Test") if test else "Test"
    
    text = f"🏆 <b>{test_title}</b>\nTop 10 eng yuqori natijalar:\n\n"
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    
    if not results:
        text += "Hali hech kim bu testni ishlamagan."
    else:
        for i, r in enumerate(results):
            name = r.get("user_name", "Noma'lum")[:20]
            pct = r.get("best_percentage", 0)
            score = r.get("best_score", 0)
            medal = medals[i] if i < len(medals) else f"{i+1}."
            
            text += f"{medal} <b>{name}</b> — {pct:.1f}% ({score} ball)\n"
            
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"view_test_{test_id}"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

# Hozircha "Fan bo'yicha" reyting menyusi
@router.callback_query(F.data == "lb_subject")
async def show_subject_lb_prompt(callback: CallbackQuery):
    await callback.answer()
    
    from keyboards.keyboards import subjects_keyboard
    # Funksiya kelajakda fanlarga qarab reyting ajratish uchun tayyorlandi
    text = "📚 <b>FAN BO'YICHA REYTING</b>\n\nQaysi fan reytingini ko'rmoqchisiz?"
    await callback.message.edit_text(text, reply_markup=subjects_keyboard(callback_prefix="lb_subj_"))

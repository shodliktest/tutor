"""
👨‍💼 ADMIN PANEL HANDLER
"""
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from firebase.db import get_all_users, get_all_tests, block_user, delete_test, get_db
from keyboards.keyboards import admin_keyboard
from config import ADMIN_IDS

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        if update.callback_query:
            await update.callback_query.answer("🚫 Ruxsat yo'q!", show_alert=True)
        else:
            await update.message.reply_text("🚫 Siz admin emassiz!")
        return
    
    query = update.callback_query
    
    if query:
        await query.answer()
        data = query.data
        
        if data == "admin_users":
            await _show_users(query)
        elif data == "admin_tests":
            await _show_tests(query)
        elif data == "admin_stats":
            await _show_stats(query)
        elif data == "admin_broadcast":
            await _broadcast_prompt(query, context)
        elif data.startswith("admin_block_"):
            uid = int(data.replace("admin_block_", ""))
            block_user(uid, True)
            await query.answer("✅ Foydalanuvchi bloklandi!", show_alert=True)
        elif data.startswith("admin_unblock_"):
            uid = int(data.replace("admin_unblock_", ""))
            block_user(uid, False)
            await query.answer("✅ Blok olib tashlandi!", show_alert=True)
        elif data.startswith("admin_del_test_"):
            test_id = data.replace("admin_del_test_", "")
            delete_test(test_id)
            await query.answer("✅ Test o'chirildi!", show_alert=True)
            await _show_tests(query)
        else:
            await _show_main(query)
    else:
        await _show_main_message(update.message)


async def _show_main(query):
    """Asosiy admin sahifasi"""
    db = get_db()
    
    users_count = len(list(db.collection("users").stream()))
    tests_count = len(list(db.collection("tests").where("is_active", "==", True).stream()))
    results_count = len(list(db.collection("results").stream()))
    
    text = f"""
👨‍💼 <b>ADMIN PANEL</b>

📊 <b>Umumiy statistika:</b>
👥 Foydalanuvchilar: <b>{users_count}</b>
📋 Testlar: <b>{tests_count}</b>
📈 Natijalар: <b>{results_count}</b>

Quyidagi bo'limlarni boshqaring:
"""
    
    await query.message.edit_text(text, reply_markup=admin_keyboard(), parse_mode="HTML")


async def _show_main_message(message):
    """Admin sahifasini xabar sifatida yuborish"""
    text = "👨‍💼 <b>ADMIN PANEL</b>\n\nQuyidagi bo'limlarni boshqaring:"
    await message.reply_text(text, reply_markup=admin_keyboard(), parse_mode="HTML")


async def _show_users(query):
    """Foydalanuvchilar ro'yxati"""
    users = get_all_users(limit=20)
    
    text = f"👥 <b>FOYDALANUVCHILAR</b> ({len(users)} ta)\n\n"
    keyboard = []
    
    for user in users[:15]:
        name = user.get("name", "Noma'lum")[:20]
        tests = user.get("total_tests", 0)
        blocked = "🚫" if user.get("is_blocked") else "✅"
        uid = user.get("telegram_id")
        
        text += f"{blocked} <b>{name}</b> — {tests} ta test\n"
        
        block_label = "Blokdan chiqarish" if user.get("is_blocked") else "Bloklash"
        block_cb = f"admin_unblock_{uid}" if user.get("is_blocked") else f"admin_block_{uid}"
        
        keyboard.append([
            InlineKeyboardButton(f"{blocked} {name}", callback_data=f"user_info_{uid}"),
            InlineKeyboardButton("🚫" if not user.get("is_blocked") else "✅", callback_data=block_cb)
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data="admin_panel")])
    
    await query.message.edit_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def _show_tests(query):
    """Testlar ro'yxati"""
    tests = get_all_tests(limit=20)
    
    text = f"📋 <b>TESTLAR</b> ({len(tests)} ta)\n\n"
    keyboard = []
    
    for test in tests[:15]:
        title = test.get("title", "Nomsiz")[:25]
        attempts = test.get("total_attempts", 0)
        avg = test.get("avg_score", 0)
        test_id = test.get("test_id")
        
        text += f"📝 <b>{title}</b> — {attempts} ta urinish, {avg:.0f}% o'rtacha\n"
        
        keyboard.append([
            InlineKeyboardButton(f"📝 {title}", callback_data=f"test_info_{test_id}"),
            InlineKeyboardButton("🗑", callback_data=f"admin_del_test_{test_id}")
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data="admin_panel")])
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def _show_stats(query):
    """Statistika"""
    db = get_db()
    
    results = list(db.collection("results").stream())
    total_results = len(results)
    
    if total_results > 0:
        scores = [r.to_dict().get("percentage", 0) for r in results]
        avg_score = sum(scores) / len(scores)
        passed = sum(1 for s in scores if s >= 60)
        pass_rate = (passed / total_results * 100) if total_results else 0
    else:
        avg_score = 0
        pass_rate = 0
    
    text = f"""
📊 <b>STATISTIKA</b>

━━━━━━━━━━━━━━━
📈 Jami natijalар: <b>{total_results}</b>
📊 O'rtacha natija: <b>{avg_score:.1f}%</b>
✅ O'tish foizi: <b>{pass_rate:.1f}%</b>
━━━━━━━━━━━━━━━
"""
    
    keyboard = [[InlineKeyboardButton("◀️ Orqaga", callback_data="admin_panel")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def _broadcast_prompt(query, context):
    """Barcha foydalanuvchilarga xabar yuborish"""
    context.user_data["admin_action"] = "broadcast"
    
    await query.message.edit_text(
        "📢 <b>XABAR YUBORISH</b>\n\n"
        "Yubormoqchi bo'lgan xabaringizni yozing.\n"
        "Barcha foydalanuvchilarga yuboriladi.\n\n"
        "/cancel — bekor qilish",
        parse_mode="HTML"
    )

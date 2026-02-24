"""
👨‍💼 ADMIN PANEL HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Imkoniyatlar: Statistika, Xabar tarqatish, Bloklash, Test o'chirish
"""
import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from firebase.db import get_all_users, get_all_tests, get_db
from keyboards.keyboards import admin_keyboard
from utils.states import AdminPanel
from config import ADMIN_IDS

logger = logging.getLogger(__name__)
router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ==========================================================
# 1. ADMIN PANEL ASOSIY MENYUSI
# ==========================================================
@router.callback_query(F.data == "admin_panel")
async def admin_panel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        await callback.answer("🚫 Sizda bu bo'limga kirish huquqi yo'q!", show_alert=True)
        return
        
    await callback.answer()
    text = (
        "👨‍💼 <b>ADMINISTRATOR PANELI</b>\n\n"
        "Tizimni to'liq boshqarish uchun quyidagi bo'limlardan birini tanlang:\n"
        "• Barcha ma'lumotlar real vaqt rejimida (Firebase) olinadi."
    )
    await callback.message.edit_text(text, reply_markup=admin_keyboard(), parse_mode="HTML")


# ==========================================================
# 2. STATISTIKA VA TAHLIL
# ==========================================================
@router.callback_query(F.data == "admin_stats")
async def show_stats_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.answer("📊 Statistika hisoblanmoqda...")
    
    db = get_db()
    users_ref = list(db.collection("users").stream())
    tests_ref = list(db.collection("tests").stream())
    results_ref = list(db.collection("results").stream())
    
    total_users = len(users_ref)
    total_tests = len(tests_ref)
    total_results = len(results_ref)
    
    avg_score = 0
    pass_rate = 0
    
    if total_results > 0:
        scores = [r.to_dict().get("percentage", 0) for r in results_ref]
        avg_score = sum(scores) / len(scores)
        passed = sum(1 for s in scores if s >= 60)
        pass_rate = (passed / total_results) * 100

    text = f"""
📈 <b>TIZIMNING GLOBAL STATISTIKASI</b>

👥 <b>Foydalanuvchilar:</b>
• Jami ro'yxatdan o'tganlar: <b>{total_users}</b> ta

📋 <b>Testlar Bazasi:</b>
• Yaratilgan jami testlar: <b>{total_tests}</b> ta

📊 <b>Natijalar (Ishlangan testlar):</b>
• Jami urinishlar: <b>{total_results}</b> marta
• O'rtacha o'zlashtirish: <b>{avg_score:.1f}%</b>
• Muvaffaqiyatli o'tish (60%+): <b>{pass_rate:.1f}%</b>
"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_panel"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


# ==========================================================
# 3. XABAR TARQATISH (BROADCAST)
# ==========================================================
@router.callback_query(F.data == "admin_broadcast")
async def broadcast_prompt_handler(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.answer()
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_panel"))
    
    await callback.message.edit_text(
        "📢 <b>XABAR TARQATISH</b>\n\n"
        "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozing (rasm yoki video ham mumkin):",
        reply_markup=builder.as_markup()
    )
    await state.set_state(AdminPanel.broadcast)

@router.message(AdminPanel.broadcast)
async def send_broadcast_message(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    
    status_msg = await message.answer("⏳ Xabar tarqatish boshlandi. Iltimos kuting...")
    
    db = get_db()
    users = list(db.collection("users").stream())
    
    success_count = 0
    fail_count = 0
    
    for user_doc in users:
        uid = user_doc.id
        try:
            # Xabarni nusxalab yuborish (forward emas, copy)
            await message.send_copy(chat_id=uid)
            success_count += 1
        except TelegramForbiddenError:
            # User botni bloklagan bo'lsa, bazada is_blocked = True qilamiz
            db.collection("users").document(uid).update({"is_blocked": True})
            fail_count += 1
        except Exception:
            fail_count += 1
            
        # Telegram API limitlariga tushmaslik uchun (Max 30 ta xabar / soniya)
        await asyncio.sleep(0.05)
        
    await state.clear()
    await status_msg.edit_text(
        f"✅ <b>XABAR TARQATISH YAKUNLANDI!</b>\n\n"
        f"📩 Muvaffaqiyatli yuborildi: <b>{success_count}</b> ta\n"
        f"❌ Yuborilmadi (Bloklaganlar): <b>{fail_count}</b> ta\n",
        parse_mode="HTML"
    )


# ==========================================================
# 4. FOYDALANUVCHILARNI BOSHQRISH VA BLOKLASH
# ==========================================================
@router.callback_query(F.data == "admin_users")
async def show_users_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.answer()
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_panel"))
    
    await callback.message.edit_text(
        "👥 <b>FOYDALANUVCHINI BLOKLASH / OCHISH</b>\n\n"
        "Iltimos, bloklamoqchi yoki blokdan chiqarmoqchi bo'lgan foydalanuvchining <b>Telegram ID</b> raqamini yozib yuboring:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(AdminPanel.block_user)

@router.message(AdminPanel.block_user)
async def block_user_action(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    target_id = message.text.strip()
    
    if not target_id.isdigit():
        await message.answer("❌ Telegram ID faqat raqamlardan iborat bo'lishi kerak!")
        return
        
    db = get_db()
    user_ref = db.collection("users").document(target_id)
    doc = user_ref.get()
    
    if not doc.exists:
        await message.answer("❌ Bunday ID ga ega foydalanuvchi bazada topilmadi.")
        return
        
    current_status = doc.to_dict().get("is_blocked", False)
    new_status = not current_status
    user_ref.update({"is_blocked": new_status})
    
    action_text = "🔒 BLOKLANDI" if new_status else "🔓 BLOKDAN CHIQARILDI"
    await message.answer(f"✅ Foydalanuvchi (ID: {target_id}) holati o'zgardi:\n<b>{action_text}</b>")
    await state.clear()


# ==========================================================
# 5. TESTLARNI BOSHQRISH VA O'CHIRISH
# ==========================================================
@router.callback_query(F.data == "admin_delete_test")
async def delete_test_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.answer()
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_panel"))
    
    await callback.message.edit_text(
        "🗑 <b>TESTNI O'CHIRISH</b>\n\n"
        "O'chirmoqchi bo'lgan testning <b>Test ID</b> sini (kodi) yozib yuboring:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(AdminPanel.delete_test)

@router.message(AdminPanel.delete_test)
async def delete_test_action(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    test_id = message.text.strip()
    
    db = get_db()
    test_ref = db.collection("tests").document(test_id)
    
    if not test_ref.get().exists:
        await message.answer("❌ Bunday ID ga ega test topilmadi.")
        return
        
    test_ref.delete()
    await message.answer(f"✅ Test (ID: {test_id}) bazadan butunlay o'chirildi.")
    await state.clear()

"""
👨‍💼 ADMIN PANEL VA MULOQOT HANDLER (AIOGRAM 3)
Sundon AI uslubidagi mukammal boshqaruv tizimi.
"""
import io
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_IDS
from firebase.db import get_all_users, get_all_tests
from utils.states import AdminPanel, Support
from keyboards.keyboards import admin_keyboard, main_reply_keyboard

logger = logging.getLogger(__name__)
router = Router()

# ==========================================================
# 1. ADMIN PANEL ASOSIY MENYUSI
# ==========================================================
@router.message(F.text == "👨‍💼 Admin Panel")
async def admin_panel_handler(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    await message.answer("👨‍💼 <b>Admin Panelga xush kelibsiz!</b>\nNima qilamiz?", reply_markup=admin_keyboard())

# ==========================================================
# 2. STATISTIKA VA FOYDALANUVCHILAR RO'YXATI
# ==========================================================
@router.callback_query(F.data == "admin_stats")
async def admin_stats_handler(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return
    await callback.answer("⏳ Hisoblanmoqda...")
    users = get_all_users()
    tests = get_all_tests()
    text = (
        f"📊 <b>LOYIHA STATISTIKASI</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{len(users)} ta</b>\n"
        f"📋 Jami testlar: <b>{len(tests)} ta</b>"
    )
    await callback.message.edit_text(text, reply_markup=admin_keyboard())

@router.callback_query(F.data == "admin_users")
async def admin_users_handler(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return
    await callback.answer("⏳ Ro'yxat tayyorlanmoqda...")
    users = get_all_users()
    
    text = "ID | Ism | Username | Testlar | O'rtacha ball\n" + "-"*50 + "\n"
    for u in users:
        uname = f"@{u.get('username')}" if u.get('username') else "Yo'q"
        text += f"{u.get('telegram_id')} | {u.get('name')} | {uname} | {u.get('total_tests', 0)} | {round(u.get('avg_score', 0), 1)}%\n"
        
    doc = BufferedInputFile(text.encode('utf-8'), filename="Foydalanuvchilar.txt")
    await callback.message.answer_document(doc, caption="👥 Barcha foydalanuvchilar ro'yxati (TXT)")

# ==========================================================
# 3. OMMAVIY XABAR YUBORISH (BROADCAST)
# ==========================================================
@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS: return
    await callback.answer()
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_admin"))
    
    await callback.message.edit_text(
        "📢 <b>Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:</b>\n"
        "(Matn, rasm, video yoki fayl yuborishingiz mumkin)", 
        reply_markup=builder.as_markup()
    )
    await state.set_state(AdminPanel.broadcast)

@router.message(AdminPanel.broadcast)
async def broadcast_send(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    users = get_all_users()
    sent_count = 0
    msg = await message.answer("⏳ Xabar yuborilmoqda...")
    
    for u in users:
        try:
            await message.copy_to(chat_id=u.get('telegram_id'))
            sent_count += 1
        except Exception: 
            pass # Botni bloklaganlar xatosi yashiriladi
            
    await msg.edit_text(f"✅ Xabar <b>{sent_count}</b> ta foydalanuvchiga muvaffaqiyatli yuborildi!", reply_markup=admin_keyboard())
    await state.clear()

@router.callback_query(F.data == "cancel_admin")
async def cancel_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("👨‍💼 <b>Admin Panel</b>", reply_markup=admin_keyboard())

# ==========================================================
# 4. ADMINGA MUROJAAT (O'QUVCHIDAN ADMINGA)
# ==========================================================
@router.callback_query(F.data == "contact_admin")
async def contact_admin_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_support"))
    await callback.message.edit_text("✍️ <b>Adminga xabaringizni yozib yuboring:</b>\n<i>(Savol, taklif yoki muammolar haqida)</i>", reply_markup=builder.as_markup())
    await state.set_state(Support.waiting_for_message)

@router.message(Support.waiting_for_message)
async def send_to_admin(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    for admin_id in ADMIN_IDS:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="💬 Javob berish", callback_data=f"reply_user_{user_id}"))
        try:
            await message.bot.send_message(admin_id, f"📩 <b>Yangi murojaat!</b>\n👤 Kimdan: {user_name}\n🆔 ID: <code>{user_id}</code>\n\n👇 Xabar matni:")
            await message.copy_to(admin_id, reply_markup=builder.as_markup())
        except Exception: pass
        
    await message.answer("✅ Xabaringiz adminga yuborildi. Tez orada javob qaytaramiz!")
    await state.clear()

@router.callback_query(F.data == "cancel_support")
async def cancel_support(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("❌ Murojaat bekor qilindi.", reply_markup=main_reply_keyboard(callback.from_user.id))

# ==========================================================
# 5. ADMINDAN JAVOB (ADMINDAN O'QUVCHIGA)
# ==========================================================
@router.callback_query(F.data.startswith("reply_user_"))
async def reply_to_user_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS: return
    user_id = callback.data.replace("reply_user_", "")
    await state.update_data(reply_to=user_id)
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_admin"))
    
    await callback.message.answer(f"✍️ <code>{user_id}</code> ID egasiga javobingizni yozing:", reply_markup=builder.as_markup())
    await state.set_state(Support.waiting_for_reply)

@router.message(Support.waiting_for_reply)
async def send_reply_to_user(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_to")
    try:
        await message.bot.send_message(user_id, "👨‍💼 <b>Admindan javob keldi:</b>")
        await message.copy_to(user_id)
        await message.answer("✅ Javobingiz foydalanuvchiga muvaffaqiyatli yetkazildi!", reply_markup=admin_keyboard())
    except Exception:
        await message.answer("❌ Foydalanuvchiga xabar yuborishda xatolik (Botni bloklagan bo'lishi mumkin).", reply_markup=admin_keyboard())
    await state.clear()
      

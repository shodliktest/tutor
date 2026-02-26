"""
👑 ADMIN PANEL HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Qalin chiziqlar, TXT hisobotlar va xavfsiz boshqaruv.
Hech narsa qisqartirilmadi!
"""
import io
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from config import ADMIN_IDS
from firebase.db import get_all_users, get_all_tests, block_user, delete_test, get_test
from utils.states import AdminPanel
from keyboards.keyboards import main_reply_keyboard

logger = logging.getLogger(__name__)
router = Router()

# ==========================================================
# 1. ADMIN ASOSIY MENYUSI
# ==========================================================
@router.message(F.text == "👑 Admin Panel")
async def admin_panel_start(message: Message, state: FSMContext):
    await state.clear()
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("❌ Sizda admin huquqi yo'q!")

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users"),
        InlineKeyboardButton(text="📋 Testlar ro'yxati", callback_data="admin_tests")
    )
    builder.row(
        InlineKeyboardButton(text="📢 Xabar tarqatish", callback_data="admin_broadcast"),
        InlineKeyboardButton(text="🗑 Testni o'chirish", callback_data="admin_del_test")
    )
    builder.row(InlineKeyboardButton(text="🚫 Band/Qaytarish (Block)", callback_data="admin_block"))
    builder.row(InlineKeyboardButton(text="❌ Menyuni yopish", callback_data="admin_close"))

    text = (
        f"<b>👑 BOSH BOSHQARUV PANELI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Xush kelibsiz, Admin!\n"
        f"Quyidagi bo'limlardan birini tanlang:"
    )
    await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "admin_close")
async def close_admin_panel(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("Admin panel yopildi.")

@router.callback_query(F.data == "admin_cancel")
async def cancel_admin_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Harakat bekor qilindi.")

# ==========================================================
# 2. FOYDALANUVCHILAR RO'YXATINI OLISH
# ==========================================================
@router.callback_query(F.data == "admin_users")
async def admin_users_handler(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return
    await callback.answer("⏳ Foydalanuvchilar ro'yxati tayyorlanmoqda...")
    
    users = get_all_users()
    if not users:
        return await callback.message.answer("❌ Bazada foydalanuvchilar yo'q.")
        
    text = "ID RAQAM | ISM | USERNAME | TESTLAR SONI | O'RTACHA NATIJA | HOLATI\n"
    text += "━" * 70 + "\n"
    
    for u in users:
        uid = u.get('telegram_id', 'Noma\'lum')
        name = u.get('name', 'Ismsiz')
        user_name = f"@{u.get('username')}" if u.get('username') else "Yo'q"
        tests_count = u.get('total_tests', 0)
        avg_score = round(u.get('avg_score', 0), 1)
        blocked = "🔴 Bloklangan" if u.get('is_blocked') else "🟢 Faol"
        
        text += f"{uid} | {name} | {user_name} | {tests_count} ta | {avg_score}% | {blocked}\n"
        
    doc = BufferedInputFile(text.encode('utf-8'), filename="Barcha_Foydalanuvchilar.txt")
    
    caption_text = (
        f"<b>👥 FOYDALANUVCHILAR RO'YXATI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Jami foydalanuvchilar: <b>{len(users)} ta</b>\n"
        f"<i>Batafsil ma'lumot yuqoridagi TXT faylda.</i>"
    )
    await callback.message.answer_document(doc, caption=caption_text, parse_mode="HTML")

# ==========================================================
# 3. TESTLAR RO'YXATINI OLISH
# ==========================================================
@router.callback_query(F.data == "admin_tests")
async def admin_tests_handler(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return
    await callback.answer("⏳ Testlar ro'yxati tayyorlanmoqda...")
    
    tests = get_all_tests()
    if not tests:
        return await callback.message.answer("❌ Bazada testlar yo'q.")
        
    text = "TEST KODI | FAN | MAVZU | SAVOLLAR | YECHILGAN\n"
    text += "━" * 60 + "\n"
    
    for t in tests:
        t_id = t.get('test_id', 'Noma\'lum')
        cat = t.get('category', 'Boshqa')
        title = t.get('title', 'Nomsiz')
        q_count = len(t.get('questions', []))
        s_count = t.get('solve_count', 0)
        
        text += f"{t_id} | {cat} | {title} | {q_count} ta | {s_count} marta\n"
        
    doc = BufferedInputFile(text.encode('utf-8'), filename="Barcha_Testlar.txt")
    
    caption_text = (
        f"<b>📋 TESTLAR RO'YXATI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Jami testlar: <b>{len(tests)} ta</b>\n"
        f"<i>Test kodidan nusxa olib botdan qidirishingiz yoki o'chirishingiz mumkin.</i>"
    )
    await callback.message.answer_document(doc, caption=caption_text, parse_mode="HTML")

# ==========================================================
# 4. FOYDALANUVCHINI BLOKLASH YOKI OCHISH
# ==========================================================
@router.callback_query(F.data == "admin_block")
async def admin_block_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS: return
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_cancel"))
    
    text = (
        f"<b>🚫 FOYDALANUVCHINI BLOKLASH / OCHISH</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Amalni bajarish uchun foydalanuvchining <b>Telegram ID</b> raqamini yuboring.\n\n"
        f"<i>(ID raqamni 'Foydalanuvchilar ro'yxati'dan olishingiz mumkin)</i>"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(AdminPanel.block_user)

@router.message(AdminPanel.block_user)
async def admin_block_process(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, faqat raqamlardan iborat ID kiriting.")
        
    user_id = int(message.text)
    users = get_all_users()
    target_user = next((u for u in users if u.get("telegram_id") == user_id), None)
    
    if not target_user:
        return await message.answer("❌ Bunday ID ga ega foydalanuvchi bazadan topilmadi.")
        
    current_status = target_user.get("is_blocked", False)
    new_status = not current_status
    
    block_user(user_id, new_status)
    await state.clear()
    
    status_text = "🔴 BLOKLANDI" if new_status else "🟢 BLOKDAN CHIQARILDI"
    text = (
        f"<b>✅ AMALIYOT BAJARILDI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Foydalanuvchi: {target_user.get('name')}\n"
        f"🆔 ID raqami: {user_id}\n"
        f"🔄 Yangi holat: <b>{status_text}</b>"
    )
    await message.answer(text)

# ==========================================================
# 5. TESTNI O'CHIRISH
# ==========================================================
@router.callback_query(F.data == "admin_del_test")
async def admin_del_test_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS: return
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_cancel"))
    
    text = (
        f"<b>🗑 TESTNI O'CHIRISH</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"O'chirmoqchi bo'lgan testingizning <b>KODINI (ID)</b> yuboring.\n"
        f"<i>Diqqat: O'chirilgan testni ortga qaytarib bo'lmaydi!</i>"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(AdminPanel.delete_test)

@router.message(AdminPanel.delete_test)
async def admin_del_test_process(message: Message, state: FSMContext):
    test_id = message.text.strip()
    test = get_test(test_id)
    
    if not test:
        return await message.answer("❌ Bunday kodli test topilmadi. Kodni to'g'ri kiritganingizni tekshiring.")
        
    delete_test(test_id)
    await state.clear()
    
    text = (
        f"<b>✅ TEST O'CHIRILDI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🗑 Test kodi: <code>{test_id}</code>\n"
        f"🏷 Mavzu: {test.get('title')}\n\n"
        f"Ushbu test bazadan butunlay o'chirib tashlandi."
    )
    await message.answer(text)

# ==========================================================
# 6. XABAR TARQATISH (BROADCAST)
# ==========================================================
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS: return
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_cancel"))
    
    text = (
        f"<b>📢 XABAR TARQATISH</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozing.\n"
        f"<i>Siz matn, rasm, video yoki istalgan fayl yuborishingiz mumkin. U barchaga aynan shunday yetib boradi.</i>"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(AdminPanel.broadcast)

@router.message(AdminPanel.broadcast)
async def admin_broadcast_process(message: Message, state: FSMContext):
    await state.clear()
    status_msg = await message.answer("⏳ Xabar tarqatish boshlandi. Iltimos, kuting...")
    
    users = get_all_users()
    success = 0
    fail = 0
    
    for u in users:
        try:
            user_id = u.get("telegram_id")
            if user_id:
                # copy_message orqali istalgan turni (rasm, video, matn) yuborish mumkin
                await message.bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
                success += 1
        except Exception:
            fail += 1
            
    text = (
        f"<b>✅ XABAR TARQATISH YAKUNLANDI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📨 Jami foydalanuvchilar: {len(users)} ta\n"
        f"🟢 Muvaffaqiyatli bordi: {success} ta\n"
        f"🔴 Yetib bormadi (Bloklaganlar): {fail} ta"
    )
    await status_msg.edit_text(text)
    

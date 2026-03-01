"""
👑 ADMIN PANEL HANDLER
Xavfsizlik: faqat ADMIN_IDS, barcha amallar tekshiriladi
Test TXT yuklab olish (bot orqali)
"""
import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from config import ADMIN_IDS
from firebase.db import get_all_users, get_all_tests, block_user, delete_test, get_test, get_db
from utils.states import AdminPanel
from keyboards.keyboards import main_reply_keyboard, admin_keyboard

log = logging.getLogger(__name__)
router = Router()


def _check_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


# ═══════════════════════════════════════════════════════════
# 1. PANEL KIRISH (xavfsizlik tekshiruvi)
# ═══════════════════════════════════════════════════════════

@router.message(F.text == "👑 Admin Panel")
async def admin_panel_msg(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    if not _check_admin(uid):
        log.warning(f"Ruxsatsiz kirish urinishi: {uid}")
        return  # Xabar bermayiz — bot hech narsa qilmaydi
    await message.answer(
        "<b>👑 ADMIN PANEL</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=admin_keyboard()
    )


@router.callback_query(F.data == "admin_panel")
async def admin_panel_cb(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    if not _check_admin(uid):
        return await callback.answer("🚫 Ruxsat yo'q!", show_alert=True)
    await state.clear()
    await callback.answer()
    try:
        await callback.message.edit_text(
            "<b>👑 ADMIN PANEL</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Bo'limlardan birini tanlang:",
            reply_markup=admin_keyboard()
        )
    except TelegramBadRequest:
        pass


# ═══════════════════════════════════════════════════════════
# 2. STATISTIKA
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not _check_admin(callback.from_user.id):
        return await callback.answer("🚫", show_alert=True)
    await callback.answer("⏳")

    db           = get_db()
    users_list   = list(db.collection("users").stream())
    tests_list   = list(db.collection("tests").stream())
    results_list = list(db.collection("results").stream())

    total_u = len(users_list)
    total_t = len(tests_list)
    total_r = len(results_list)
    blocked = sum(1 for u in users_list if u.to_dict().get("is_blocked"))

    avg_pct = pass_rate = 0.0
    if total_r:
        scores    = [r.to_dict().get("percentage", 0) for r in results_list]
        avg_pct   = sum(scores) / len(scores)
        pass_rate = sum(1 for s in scores if s >= 60) / total_r * 100

    text = (
        f"📈 <b>TIZIM STATISTIKASI</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{total_u} ta</b>\n"
        f"🔴 Bloklangan: <b>{blocked} ta</b>\n"
        f"📋 Yaratilgan testlar: <b>{total_t} ta</b>\n"
        f"🎯 Jami urinishlar: <b>{total_r} marta</b>\n"
        f"📊 O'rtacha natija: <b>{avg_pct:.1f}%</b>\n"
        f"✅ Muvaffaqiyat (≥60%): <b>{pass_rate:.1f}%</b>"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_panel"))
    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    except TelegramBadRequest:
        pass


# ═══════════════════════════════════════════════════════════
# 3. FOYDALANUVCHILAR
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if not _check_admin(callback.from_user.id): return
    await callback.answer("⏳")

    users = get_all_users()
    if not users:
        return await callback.message.answer("❌ Foydalanuvchilar yo'q.")

    text  = "ID | ISM | USERNAME | TESTLAR | O'RTACHA | HOLAT\n"
    text += "─" * 60 + "\n"
    for u in users:
        uid   = u.get("telegram_id", "?")
        name  = u.get("name", "Ismsiz")[:20]
        uname = f"@{u.get('username')}" if u.get("username") else "—"
        tc    = u.get("total_tests", 0)
        avg   = round(u.get("avg_score", 0), 1)
        holat = "🔴" if u.get("is_blocked") else "🟢"
        text += f"{uid} | {name} | {uname} | {tc} ta | {avg}% | {holat}\n"

    doc = BufferedInputFile(text.encode("utf-8"), filename="Foydalanuvchilar.txt")
    await callback.message.answer_document(
        doc, caption=f"<b>👥 FOYDALANUVCHILAR</b>\nJami: <b>{len(users)} ta</b>"
    )


# ═══════════════════════════════════════════════════════════
# 4. TESTLAR + TXT YUKLAB OLISH
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_tests")
async def admin_tests(callback: CallbackQuery):
    if not _check_admin(callback.from_user.id): return
    await callback.answer("⏳")

    tests = get_all_tests()
    if not tests:
        return await callback.message.answer("❌ Testlar yo'q.")

    text  = "KOD | FAN | MAVZU | SAVOLLAR | ISHLANGAN | YARATUVCHI\n"
    text += "─" * 60 + "\n"
    for t in tests:
        tid   = t.get("test_id", "?")
        cat   = t.get("category", "Boshqa")[:15]
        title = t.get("title", "Nomsiz")[:25]
        qc    = len(t.get("questions", []))
        sc    = t.get("solve_count", 0)
        cid   = t.get("creator_id", "?")
        text += f"{tid} | {cat} | {title} | {qc} ta | {sc} marta | {cid}\n"

    doc = BufferedInputFile(text.encode("utf-8"), filename="Testlar.txt")
    await callback.message.answer_document(
        doc, caption=f"<b>📋 TESTLAR RO'YXATI</b>\nJami: <b>{len(tests)} ta</b>"
    )

    # Test TXT yuklab olish tugmalari (oxirgi 10 ta)
    builder = InlineKeyboardBuilder()
    for t in tests[:10]:
        tid   = t.get("test_id", "")
        title = t.get("title", "Nomsiz")[:20]
        builder.row(InlineKeyboardButton(
            text=f"📄 {title} ({tid})",
            callback_data=f"admin_dl_{tid}"
        ))
    builder.row(InlineKeyboardButton(text="◀️ Admin panel", callback_data="admin_panel"))
    await callback.message.answer(
        "<b>📄 Test TXT yuklab olish</b>\n<i>Qaysi testni yuklab olmoqchisiz?</i>",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("admin_dl_"))
async def admin_download_test(callback: CallbackQuery):
    """Admin istagan testni TXT yuklab oladi"""
    if not _check_admin(callback.from_user.id):
        return await callback.answer("🚫", show_alert=True)
    await callback.answer("⏳ TXT tayyorlanmoqda...")

    tid  = callback.data[9:]
    test = get_test(tid)
    if not test:
        return await callback.message.answer("❌ Test topilmadi.")

    from handlers.profile import _test_to_txt
    txt = _test_to_txt(test)
    doc = BufferedInputFile(txt.encode("utf-8"), filename=f"{test.get('title', tid)}.txt")
    await callback.message.answer_document(
        doc,
        caption=(
            f"📄 <b>{test.get('title')}</b>\n"
            f"📋 {len(test.get('questions', []))} ta savol\n"
            f"🆔 <code>{tid}</code>"
        )
    )


# ═══════════════════════════════════════════════════════════
# 5. BROADCAST
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not _check_admin(callback.from_user.id): return
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_panel"))
    try:
        await callback.message.edit_text(
            "<b>📢 BARCHA FOYDALANUVCHILARGA XABAR</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Yubormoqchi bo'lgan xabaringizni yozing\n"
            "<i>(matn, rasm, video, fayl qabul qilinadi)</i>:",
            reply_markup=builder.as_markup()
        )
    except TelegramBadRequest:
        pass
    await state.set_state(AdminPanel.broadcast)


@router.message(AdminPanel.broadcast)
async def broadcast_send(message: Message, state: FSMContext):
    if not _check_admin(message.from_user.id): return

    status = await message.answer("⏳ Tarqatish boshlandi...")
    users  = get_all_users()
    ok = fail = 0

    for u in users:
        uid = u.get("telegram_id")
        if not uid or u.get("is_blocked"):
            continue
        try:
            await message.bot.copy_message(
                chat_id     = uid,
                from_chat_id= message.chat.id,
                message_id  = message.message_id
            )
            ok += 1
        except TelegramForbiddenError:
            block_user(uid, True)
            fail += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)

    await state.clear()
    await status.edit_text(
        f"<b>✅ TARQATISH YAKUNLANDI</b>\n\n"
        f"🟢 Muvaffaqiyatli: {ok} ta\n"
        f"🔴 Bloklaganlar: {fail} ta"
    )


# ═══════════════════════════════════════════════════════════
# 6. BLOKLASH / OCHISH
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_block")
async def block_start(callback: CallbackQuery, state: FSMContext):
    if not _check_admin(callback.from_user.id): return
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_panel"))
    try:
        await callback.message.edit_text(
            "<b>🚫 BLOKLASH / OCHISH</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Foydalanuvchi <b>Telegram ID</b> raqamini yuboring:",
            reply_markup=builder.as_markup()
        )
    except TelegramBadRequest:
        pass
    await state.set_state(AdminPanel.block_user)


@router.message(AdminPanel.block_user)
async def block_process(message: Message, state: FSMContext):
    if not _check_admin(message.from_user.id): return
    t = message.text.strip().lstrip("-")
    if not t.isdigit():
        return await message.answer("❌ Faqat Telegram ID raqam kiriting.")

    uid  = int(t)
    user = None
    for u in get_all_users():
        if u.get("telegram_id") == uid:
            user = u
            break

    if not user:
        return await message.answer("❌ Foydalanuvchi topilmadi.")

    new_status = not user.get("is_blocked", False)
    block_user(uid, new_status)
    await state.clear()
    status_txt = "🔴 BLOKLANDI" if new_status else "🟢 BLOKDAN CHIQARILDI"
    await message.answer(
        f"<b>✅ BAJARILDI</b>\n\n"
        f"👤 {user.get('name')}\n"
        f"🆔 {uid}\n"
        f"Holat: <b>{status_txt}</b>"
    )


# ═══════════════════════════════════════════════════════════
# 7. TEST O'CHIRISH
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_del_test")
async def del_test_start(callback: CallbackQuery, state: FSMContext):
    if not _check_admin(callback.from_user.id): return
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_panel"))
    try:
        await callback.message.edit_text(
            "<b>🗑 TESTNI O'CHIRISH</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Test <b>KODINI</b> yuboring:\n<i>⚠️ Qaytarilmaydi!</i>",
            reply_markup=builder.as_markup()
        )
    except TelegramBadRequest:
        pass
    await state.set_state(AdminPanel.delete_test)


@router.message(AdminPanel.delete_test)
async def del_test_process(message: Message, state: FSMContext):
    if not _check_admin(message.from_user.id): return
    tid  = message.text.strip()
    test = get_test(tid)
    if not test:
        return await message.answer("❌ Bu kodli test topilmadi.")
    delete_test(tid)
    await state.clear()
    await message.answer(
        f"<b>✅ TEST O'CHIRILDI</b>\n\n"
        f"🗑 Kod: <code>{tid}</code>\n"
        f"📝 Mavzu: {test.get('title')}"
    )

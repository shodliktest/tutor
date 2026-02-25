"""
➕ TEST YARATISH HANDLER (FANLAR GURUHLANDI)
"""
import os, logging, uuid, tempfile, io
from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from utils.parser import parse_file
from utils.states import CreateTest
from keyboards.keyboards import difficulty_keyboard, test_visibility_keyboard, create_subject_keyboard
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "➕ Test Yaratish")
async def create_test_start(message: Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    await message.answer(
        "📝 <b>TEST YARATISH</b>\n\n"
        "Iltimos, test savollari bor TXT, DOCX yoki PDF faylni yuboring.\n",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.upload_file)

@router.message(F.document, CreateTest.upload_file)
async def upload_file_handler(message: Message, state: FSMContext):
    doc = message.document
    if not doc.file_name.lower().endswith(('.txt', '.pdf', '.docx')):
        await message.answer("❌ Faqat TXT, PDF yoki DOCX fayllar qabul qilinadi!")
        return

    status_msg = await message.answer("⏳ Fayl o'qilmoqda...")
    try:
        file = await message.bot.get_file(doc.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{doc.file_name}") as tmp_file:
            await message.bot.download_file(file.file_path, tmp_file.name)
            tmp_path = tmp_file.name
        try: questions = parse_file(tmp_path)
        finally: os.remove(tmp_path) 
            
        if not questions:
            await status_msg.edit_text("❌ Fayldan savol topilmadi.")
            return
            
        await state.update_data(questions=questions)
        
        # 🛡️ FANNI TANLASH TUGMALARI (GURUHLASH)
        await status_msg.edit_text(
            f"✅ <b>{len(questions)} ta savol topildi!</b>\n\n"
            f"📝 <b>Test qaysi fanga tegishli? Pastdan tanlang:</b>",
            reply_markup=create_subject_keyboard()
        )
        # Hali state ni o'zgartirmaymiz, callback ni kutamiz
    except Exception as e:
        logger.error(f"Fayl xatosi: {e}")
        await status_msg.edit_text("❌ Faylni o'qishda xatolik yuz berdi.")

# 🛡️ TUGMADAN FAN TANLANGANDA
@router.callback_query(F.data.startswith("set_subj_"), CreateTest.upload_file)
async def process_subject_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    subj = callback.data.replace("set_subj_", "")
    
    if subj == "other":
        await callback.message.edit_text("📝 <b>Fanning nomini yozib yuboring (Masalan: Ingliz tili):</b>")
        await state.set_state(CreateTest.set_subject)
    else:
        await state.update_data(title=subj)
        await callback.message.edit_text(
            f"✅ Fan: <b>{subj}</b>\n\nEndi <b>qiyinlik darajasini</b> tanlang:",
            reply_markup=difficulty_keyboard()
        )
        await state.set_state(CreateTest.set_difficulty)

# 🛡️ QO'LDA FAN YOZILGANDA
@router.message(F.text, CreateTest.set_subject)
async def set_subject_manual(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        f"✅ Fan: <b>{message.text}</b>\n\nEndi <b>qiyinlik darajasini</b> tanlang:",
        reply_markup=difficulty_keyboard()
    )
    await state.set_state(CreateTest.set_difficulty)

@router.callback_query(F.data.startswith("diff_"), CreateTest.set_difficulty)
async def set_difficulty_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(difficulty=callback.data.replace("diff_", ""))
    await callback.message.edit_text("⏱ <b>Test ishlash uchun vaqt limitini kiriting (daqiqalarda, limit yo'q bo'lsa 0):</b>")
    await state.set_state(CreateTest.set_time_limit)

@router.message(F.text, CreateTest.set_time_limit)
async def set_time_limit_handler(message: Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ Faqat raqam kiriting.")
    await state.update_data(time_limit=int(message.text))
    await message.answer("🎯 <b>Testdan o'tish foizini kiriting (0-100):</b>")
    await state.set_state(CreateTest.set_passing_score)

@router.message(F.text, CreateTest.set_passing_score)
async def set_passing_score_handler(message: Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ Faqat raqam kiriting.")
    await state.update_data(passing_score=int(message.text))
    await message.answer("🔄 <b>Necha marta ishlashga ruxsat berasiz? (Cheklanmagan bo'lsa 0):</b>")
    await state.set_state(CreateTest.set_max_attempts)

@router.message(F.text, CreateTest.set_max_attempts)
async def set_max_attempts_handler(message: Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ Faqat raqam kiriting.")
    await state.update_data(max_attempts=int(message.text))
    await message.answer("🔒 <b>Test maxfiyligini tanlang:</b>", reply_markup=test_visibility_keyboard())
    await state.set_state(CreateTest.set_visibility)

@router.callback_query(F.data.startswith("vis_"), CreateTest.set_visibility)
async def set_visibility_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏳ Saqlanmoqda...")
    visibility = callback.data.replace("vis_", "")
    data = await state.get_data()
    questions = data.get("questions", [])
    title = data.get("title", "Nomsiz test")
    
    from firebase.config import get_db
    db = get_db()
    test_id = str(uuid.uuid4())[:8]
    
    # Kategoriya (Fan nomi) sifatida 'title' ni saqlaymiz, chunki biz fanni 'title' deb oldik
    new_test = {
        "test_id": test_id, "title": title, "category": title, "creator_id": callback.from_user.id,
        "difficulty": data.get("difficulty", "medium"), "time_limit": data.get("time_limit", 0),
        "passing_score": data.get("passing_score", 60), "max_attempts": data.get("max_attempts", 0),
        "visibility": visibility, "questions": questions, "created_at": datetime.now(timezone.utc), "solve_count": 0
    }
    
    db.collection("tests").document(test_id).set(new_test)
    await state.clear()
    
    bot_username = (await callback.bot.me()).username
    await callback.message.edit_text(
        f"🎉 <b>TEST YARATILDI!</b>\n\n"
        f"<b>Test kodi:</b> <code>{test_id}</code>\n"
        f"<b>Ssilka:</b> <code>https://t.me/{bot_username}?start={test_id}</code>\n\n"
        f"<i>Klitlar pastda yuboriladi:</i>"
    )

    key_text = f"🔑 <b>{title.upper()} - JAVOBLAR KALITI</b>\n\n"
    for i, q in enumerate(questions):
        corr = q.get("correct", "Noma'lum")
        if isinstance(corr, list): corr = ", ".join(corr)
        elif isinstance(corr, dict): corr = ", ".join([f"{k}-{v}" for k, v in corr.items()])
        key_text += f"<b>{i+1}-savol:</b> {corr}\n"
        
    if len(key_text) > 4000:
        doc = BufferedInputFile(io.BytesIO(key_text.encode('utf-8')).getvalue(), filename=f"Klit_{test_id}.txt")
        await callback.message.answer_document(document=doc, caption="🔑 Test kaliti")
    else:
        await callback.message.answer(key_text, parse_mode="HTML")

@router.callback_query(F.data == "cancel_creation")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Test yaratish bekor qilindi.")
        

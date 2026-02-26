"""
➕ TEST YARATISH HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Namunalar (chatda nusxalash imkoni bilan), qalin chiziqlar va aniq format.
"""
import os
import uuid
import tempfile
import io
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from utils.parser import parse_file
from utils.states import CreateTest
from keyboards.keyboards import difficulty_keyboard, test_visibility_keyboard, create_subject_keyboard, main_reply_keyboard

router = Router()

# Chatda nusxalash uchun tayyor namunalar (Mono text)
SAMPLE_TEXTS = {
    "multiple_choice": "1. O'zbekiston poytaxti qayer?\n===A) Toshkent\nB) Samarqand\nC) Buxoro\nD) Xiva\nIzoh: Toshkent azaldan poytaxt hisoblanadi.",
    "all": "1. O'zbekiston poytaxti qayer?\n===A) Toshkent\nB) Samarqand\nC) Buxoro\n\n2. Fill in: Alisher Navoiy ___ yilda tug'ilgan.\n===A) 1441\n\n3. Match:\n===A) Olma --- Meva\n===B) Bodring --- Sabzavot"
}

# ==========================================================
# 1. TEST YARATISHNI BOSHLASH
# ==========================================================
@router.message(F.text == "➕ Test Yaratish")
async def create_test_start_msg(message: Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📁 Fayl yuklash (TXT, PDF)", callback_data="method_file"),
        InlineKeyboardButton(text="📊 QuizBotdan uzatish", callback_data="method_poll")
    )
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    text = (
        "<b>➕ TEST YARATISH BO'LIMI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Qaysi usulda savollarni yig'moqchisiz?\n\n"
        "<b>1. Fayl yuklash:</b> TXT, PDF yoki DOCX fayldan o'qish.\n"
        "<b>2. QuizBotdan uzatish:</b> Tayyor viktorinalarni shu yerga forward qilib yig'ish."
    )
    await message.answer(text, reply_markup=builder.as_markup())
    await state.set_state(CreateTest.choose_method)

# ==========================================================
# 2. FAYL YUKLASH VA NAMUNALAR
# ==========================================================
@router.callback_query(F.data == "method_file", CreateTest.choose_method)
async def method_file_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔘 Oddiy test namunasi", callback_data="sample_multiple_choice"),
        InlineKeyboardButton(text="📦 Barcha turlar", callback_data="sample_all")
    )
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    text = (
        "<b>📁 FAYL YUKLASH USULI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Test savollari bor TXT, DOCX yoki PDF faylni yuboring.\n\n"
        "<i>Agar fayl qanday yozilishini bilmasangiz, pastdagi namunalardan birini tanlang va nusxalab oling:</i>"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(CreateTest.upload_file)

@router.callback_query(F.data.startswith("sample_"), CreateTest.upload_file)
async def send_sample_text(callback: CallbackQuery):
    await callback.answer()
    key = callback.data.replace("sample_", "")
    sample_code = SAMPLE_TEXTS.get(key, SAMPLE_TEXTS["multiple_choice"])
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="method_file"))
    
    text = (
        "<b>📄 TAYYOR NAMUNA (Nusxalab oling)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Pastdagi matn ustiga bitta bossangiz nusxa olinadi. O'zgartirib menga fayl qilib yoki matn qilib yuboring:</i>\n\n"
        f"<code>{sample_code}</code>"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@router.message(F.document, CreateTest.upload_file)
async def upload_file_handler(message: Message, state: FSMContext):
    doc = message.document
    if not doc.file_name.lower().endswith(('.txt', '.pdf', '.docx')):
        return await message.answer("❌ Faqat TXT, PDF yoki DOCX fayllar qabul qilinadi!")

    status_msg = await message.answer("⏳ Fayl tahlil qilinmoqda...")
    try:
        file = await message.bot.get_file(doc.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{doc.file_name}") as tmp_file:
            await message.bot.download_file(file.file_path, tmp_file.name)
            tmp_path = tmp_file.name
        
        from utils.parser import parse_file
        questions = parse_file(tmp_path)
        os.remove(tmp_path) 
            
        if not questions:
            return await status_msg.edit_text("❌ Fayldan savollar topilmadi. Formatni tekshiring.")
            
        await state.update_data(questions=questions)
        
        text = (
            f"<b>✅ {len(questions)} TA SAVOL TOPILDI</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Test qaysi fanga tegishli? Pastdan tanlang:"
        )
        await status_msg.edit_text(text, reply_markup=create_subject_keyboard())
    except Exception as e:
        await status_msg.edit_text("❌ Xatolik yuz berdi.")

# ==========================================================
# 3. QUIZBOTDAN FORWARD QILISH
# ==========================================================
@router.callback_query(F.data == "method_poll", CreateTest.choose_method)
async def method_poll_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(questions=[])
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Tayyor", callback_data="finish_polls"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    text = (
        "<b>📊 QUIZBOTDAN UZATISH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Endi @QuizBot dagi tayyor viktorinalarni shu yerga <b>Forward</b> qiling.\n"
        "Har bir yuborgan savolingiz to'plamga qo'shiladi."
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(CreateTest.waiting_for_polls)

@router.message(F.poll, CreateTest.waiting_for_polls)
async def catch_poll_handler(message: Message, state: FSMContext):
    poll = message.poll
    if poll.type != "quiz":
        return await message.answer("❌ Faqat 'Quiz' (Viktorina) turini yuboring!")
        
    data = await state.get_data()
    questions = data.get("questions", [])
    
    letters = ["A)", "B)", "C)", "D)", "E)", "F)", "G)", "H)", "I)", "J)"]
    options = [f"{letters[i]} {opt.text}" for i, opt in enumerate(poll.options)]
    correct_answer = options[poll.correct_option_id]
    
    questions.append({
        "type": "multiple_choice",
        "question": poll.question,
        "options": options,
        "correct": correct_answer,
        "explanation": poll.explanation or "Izoh kiritilmagan.",
        "points": 1
    })
    
    await state.update_data(questions=questions)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Tayyor", callback_data="finish_polls"))
    await message.answer(f"✅ Savol qo'shildi (Jami: {len(questions)} ta).", reply_markup=builder.as_markup())

@router.callback_query(F.data == "finish_polls", CreateTest.waiting_for_polls)
async def finish_polls_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("questions"):
        return await callback.answer("❌ Hech bo'lmasa 1 ta savol yuboring!", show_alert=True)
    
    text = (
        "<b>📝 FANNI TANLANG</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Ajoyib! Endi test qaysi fanga tegishli ekanini tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=create_subject_keyboard())

# ==========================================================
# 4. FAN, MAVZU VA SOZLAMALAR
# ==========================================================
@router.callback_query(F.data.startswith("set_subj_"))
async def process_subject_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    subj = callback.data.replace("set_subj_", "")
    
    if subj == "other":
        await callback.message.edit_text("<b>📝 Fanning nomini yozib yuboring:</b>")
        await state.set_state(CreateTest.set_subject)
    else:
        await state.update_data(category=subj)
        text = f"<b>🏷 TEST MAVZUSI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\nFan: {subj}\n\nEndi test mavzusini yozing:\n<i>(Masalan: O'nlik kasrlar)</i>"
        await callback.message.edit_text(text)
        await state.set_state(CreateTest.set_test_title)

@router.message(F.text, CreateTest.set_subject)
async def set_subject_manual(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    text = f"<b>🏷 TEST MAVZUSI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\nFan: {message.text}\n\nEndi test mavzusini yozing:"
    await message.answer(text)
    await state.set_state(CreateTest.set_test_title)

@router.message(F.text, CreateTest.set_test_title)
async def set_test_title_handler(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    text = f"<b>📊 QIYINLIK DARAJASI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\nMavzu: {message.text}\n\nQiyinlik darajasini tanlang:"
    await message.answer(text, reply_markup=difficulty_keyboard())
    await state.set_state(CreateTest.set_difficulty)

@router.callback_query(F.data.startswith("diff_"), CreateTest.set_difficulty)
async def set_difficulty_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(difficulty=callback.data.replace("diff_", ""))
    text = "<b>⏱ VAQT LIMITI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\nVaqt limitini kiriting (daqiqada, cheksiz bo'lsa 0):"
    await callback.message.edit_text(text)
    await state.set_state(CreateTest.set_time_limit)

@router.message(F.text, CreateTest.set_time_limit)
async def set_time_limit_handler(message: Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ Raqam kiriting.")
    await state.update_data(time_limit=int(message.text))
    text = "<b>🎯 O'TISH FOIZI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\nO'tish foizini kiriting (0-100):"
    await message.answer(text)
    await state.set_state(CreateTest.set_passing_score)

@router.message(F.text, CreateTest.set_passing_score)
async def set_passing_score_handler(message: Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ Raqam kiriting.")
    await state.update_data(passing_score=int(message.text))
    text = "<b>🔄 URINISHLAR SONI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\nUrinishlar sonini kiriting (cheksiz bo'lsa 0):"
    await message.answer(text)
    await state.set_state(CreateTest.set_max_attempts)

@router.message(F.text, CreateTest.set_max_attempts)
async def set_max_attempts_handler(message: Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ Raqam kiriting.")
    await state.update_data(max_attempts=int(message.text))
    text = "<b>🔒 TEST MAXFIYLIGI</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\nTest maxfiyligini tanlang:"
    await message.answer(text, reply_markup=test_visibility_keyboard())
    await state.set_state(CreateTest.set_visibility)

@router.callback_query(F.data.startswith("vis_"), CreateTest.set_visibility)
async def set_visibility_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏳ Saqlanmoqda...")
    visibility = callback.data.replace("vis_", "")
    data = await state.get_data()
    
    test_id = str(uuid.uuid4())[:8]
    from firebase.config import get_db
    
    new_test = {
        "test_id": test_id,
        "title": data.get("title"),
        "category": data.get("category"),
        "creator_id": callback.from_user.id,
        "difficulty": data.get("difficulty"),
        "time_limit": data.get("time_limit"),
        "passing_score": data.get("passing_score"),
        "max_attempts": data.get("max_attempts"),
        "visibility": visibility,
        "questions": data.get("questions"),
        "created_at": datetime.now(timezone.utc),
        "solve_count": 0
    }
    
    get_db().collection("tests").document(test_id).set(new_test)
    await state.clear()
    
    bot_user = await callback.bot.me()
    text = (
        f"<b>🎉 TEST MUVAFFAQIYATLI YARATILDI!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 Kod: <code>{test_id}</code>\n"
        f"🔗 Ssilka: <code>https://t.me/{bot_user.username}?start={test_id}</code>\n\n"
        f"📌 Fan: {new_test['category']}\n"
        f"🏷 Mavzu: {new_test['title']}"
    )
    await callback.message.edit_text(text)

    # Kalitlarni yuborish
    keys = f"<b>🔑 {new_test['title'].upper()} - JAVOBLAR</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, q in enumerate(new_test['questions']):
        keys += f"<b>{i+1}.</b> {q['correct']}\n"
    
    if len(keys) > 4000:
        file_obj = io.BytesIO(keys.encode('utf-8'))
        await callback.message.answer_document(BufferedInputFile(file_obj.getvalue(), filename=f"Klit_{test_id}.txt"), caption="🔑 Kalit")
    else:
        await callback.message.answer(keys)

@router.callback_query(F.data == "cancel_creation")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer("❌ Bekor qilindi.", reply_markup=main_reply_keyboard(callback.fromuser.id))

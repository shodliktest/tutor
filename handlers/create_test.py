"""
➕ TEST YARATISH HANDLER (AIOGRAM 3)
- Fayl yuklash (PDF, TXT, DOCX)
- QuizBotdan forward qilib yig'ish (Mavjud)
- Fan va Test mavzusini alohida so'rash (Mavjud)
- Faqat Buttonli (Inline) test yaratish (Output poll olib tashlandi)
"""
import os
import logging
import uuid
import tempfile
import io
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from utils.parser import parse_file
from utils.states import CreateTest
from keyboards.keyboards import difficulty_keyboard, test_visibility_keyboard, create_subject_keyboard, main_reply_keyboard

logger = logging.getLogger(__name__)
router = Router()

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "samples")

# ==========================================================
# 1. TEST YARATISHNI BOSHLASH
# ==========================================================
@router.message(F.text == "➕ Test Yaratish")
async def create_test_start_msg(message: Message, state: FSMContext):
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📁 Fayl yuklash (TXT, PDF)", callback_data="method_file"),
        InlineKeyboardButton(text="📊 QuizBotdan uzatish (Forward)", callback_data="method_poll")
    )
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    await message.answer(
        "📝 <b>TEST YARATISH BO'LIMI</b>\n\n"
        "Qaysi usulda savollarni yig'moqchisiz?\n"
        "1. <b>Fayl yuklash:</b> TXT, PDF yoki DOCX fayldan o'qish.\n"
        "2. <b>QuizBotdan uzatish:</b> Tayyor viktorinalarni shu yerga forward qilib yig'ish.",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.choose_method)

# ==========================================================
# 2. FAYL YUKLASH USULI
# ==========================================================
@router.callback_query(F.data == "method_file", CreateTest.choose_method)
async def method_file_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    await callback.message.edit_text(
        "📁 <b>FAYL YUKLASH</b>\n\n"
        "Iltimos, test savollari bor TXT, DOCX yoki PDF faylni yuboring.",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.upload_file)

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
        
        questions = parse_file(tmp_path)
        os.remove(tmp_path) 
            
        if not questions:
            return await status_msg.edit_text("❌ Fayldan savollar topilmadi. Formatni tekshiring.")
            
        await state.update_data(questions=questions)
        await status_msg.edit_text(
            f"✅ <b>{len(questions)} ta savol topildi!</b>\n\n📝 <b>Test qaysi fanga tegishli?</b>",
            reply_markup=create_subject_keyboard()
        )
    except Exception as e:
        logger.error(f"Fayl xatosi: {e}")
        await status_msg.edit_text("❌ Xatolik yuz berdi.")

# ==========================================================
# 3. QUIZBOTDAN FORWARD QILISH USULI
# ==========================================================
@router.callback_query(F.data == "method_poll", CreateTest.choose_method)
async def method_poll_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(questions=[])
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Tayyor", callback_data="finish_polls"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    await callback.message.edit_text(
        "📊 <b>QUIZBOTDAN UZATISH (FORWARD)</b>\n\n"
        "Endi @QuizBot dagi tayyor viktorinalarni shu yerga <b>Forward</b> qiling.\n"
        "Har bir yuborgan savolingiz to'plamga qo'shiladi.",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.waiting_for_polls)

@router.message(F.poll, CreateTest.waiting_for_polls)
async def catch_poll_handler(message: Message, state: FSMContext):
    poll = message.poll
    if poll.type != "quiz":
        return await message.answer("❌ Faqat 'Quiz' (Viktorina) turidagi so'rovnomalarni yuboring!")
        
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
    
    await callback.message.edit_text("📝 <b>Ajoyib! Endi test qaysi fanga tegishli ekanini tanlang:</b>", reply_markup=create_subject_keyboard())

# ==========================================================
# 4. FAN VA MAVZUNI SO'RASH
# ==========================================================
@router.callback_query(F.data.startswith("set_subj_"))
async def process_subject_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    subj = callback.data.replace("set_subj_", "")
    
    if subj == "other":
        await callback.message.edit_text("📝 <b>Fanning nomini yozib yuboring:</b>")
        await state.set_state(CreateTest.set_subject)
    else:
        await state.update_data(category=subj)
        await callback.message.edit_text(f"✅ Fan: <b>{subj}</b>\n\n🏷 <b>Endi test mavzusini (nomini) yozing:</b>\n<i>(Masalan: O'nlik kasrlar)</i>")
        await state.set_state(CreateTest.set_test_title)

@router.message(F.text, CreateTest.set_subject)
async def set_subject_manual(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer(f"✅ Fan: <b>{message.text}</b>\n\n🏷 <b>Endi test mavzusini (nomini) yozing:</b>")
    await state.set_state(CreateTest.set_test_title)

@router.message(F.text, CreateTest.set_test_title)
async def set_test_title_handler(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(f"✅ Mavzu: <b>{message.text}</b>\n\nEndi <b>qiyinlik darajasini</b> tanlang:", reply_markup=difficulty_keyboard())
    await state.set_state(CreateTest.set_difficulty)

# ==========================================================
# 5. SOZLAMALARNI YAKUNLASH
# ==========================================================
@router.callback_query(F.data.startswith("diff_"), CreateTest.set_difficulty)
async def set_difficulty_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(difficulty=callback.data.replace("diff_", ""))
    await callback.message.edit_text("⏱ <b>Vaqt limitini kiriting (daqiqada, cheksiz bo'lsa 0):</b>")
    await state.set_state(CreateTest.set_time_limit)

@router.message(F.text, CreateTest.set_time_limit)
async def set_time_limit_handler(message: Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ Raqam kiriting.")
    await state.update_data(time_limit=int(message.text))
    await message.answer("🎯 <b>O'tish foizini kiriting (0-100):</b>")
    await state.set_state(CreateTest.set_passing_score)

@router.message(F.text, CreateTest.set_passing_score)
async def set_passing_score_handler(message: Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ Raqam kiriting.")
    await state.update_data(passing_score=int(message.text))
    await message.answer("🔄 <b>Urinishlar sonini kiriting (cheksiz bo'lsa 0):</b>")
    await state.set_state(CreateTest.set_max_attempts)

@router.message(F.text, CreateTest.set_max_attempts)
async def set_max_attempts_handler(message: Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ Raqam kiriting.")
    await state.update_data(max_attempts=int(message.text))
    await message.answer("🔒 <b>Test maxfiyligini tanlang:</b>", reply_markup=test_visibility_keyboard())
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
    await callback.message.edit_text(
        f"🎉 <b>TEST TAYYOR!</b>\n\n"
        f"🆔 Kod: <code>{test_id}</code>\n"
        f"🔗 Ssilka: <code>https://t.me/{bot_user.username}?start={test_id}</code>\n\n"
        f"📌 Fan: {new_test['category']}\n"
        f"🏷 Mavzu: {new_test['title']}"
    )

    # Kalitlarni yuborish
    keys = f"🔑 <b>{new_test['title'].upper()} - JAVOBLAR</b>\n\n"
    for i, q in enumerate(new_test['questions']):
        keys += f"{i+1}. {q['correct']}\n"
    await callback.message.answer(keys)

@router.callback_query(F.data == "cancel_creation")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer("❌ Bekor qilindi.", reply_markup=main_reply_keyboard(callback.from_user.id))
    

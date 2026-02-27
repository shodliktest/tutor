"""
➕ TEST YARATISH HANDLER
Faqat barqaror ishlaydigan test turlari (MCQ, True/False) qoldirildi.
QuizBotdan uzatilgan testlarni TXT formatda yuklab olish imkoniyati qo'shildi.
"""
import os
import logging
import uuid
import tempfile
import io
import random
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

# FAQAT ISHONCHLI VA BARQAROR TEST TURLARI QOLDIRILDI
SAMPLE_TYPES = {
    "mcq": ("1_javobli_namuna.txt", "🔘 Oddiy (A, B, C, D) test", 
            "1. O'zbekiston poytaxti qayer?\n===A) Toshkent\nB) Samarqand\nC) Buxoro\nD) Xiva\nIzoh: Toshkent azaldan poytaxt hisoblanadi."),
    
    "tf": ("rost_yolgon_namuna.txt", "⚖️ Rost / Yolg'on", 
           "1. Yer Quyosh atrofida aylanadi.\n===A) Rost\nB) Yolg'on")
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
# 2. FAYL YUKLASH: TEST TURINI TANLASH
# ==========================================================
@router.callback_query(F.data == "method_file", CreateTest.choose_method)
async def method_file_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    
    buttons = []
    for key, val in SAMPLE_TYPES.items():
        buttons.append(InlineKeyboardButton(text=val[1], callback_data=f"sample_{key}"))
    
    builder.add(*buttons)
    builder.adjust(1) 
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    text = (
        "<b>📁 TEST TURINI TANLANG</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Faqat barqaror test turlari mavjud. Turni tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(CreateTest.upload_file)

# ==========================================================
# 3. NAMUNA YUBORISH VA FAYL KUTISH
# ==========================================================
@router.callback_query(F.data.startswith("sample_"), CreateTest.upload_file)
async def send_sample_text(callback: CallbackQuery):
    await callback.answer()
    key = callback.data.replace("sample_", "")
    filename, type_name, mono_text = SAMPLE_TYPES.get(key, SAMPLE_TYPES["mcq"])
    
    file_path = os.path.join(SAMPLES_DIR, filename)
    if os.path.exists(file_path):
        await callback.message.answer_document(FSInputFile(file_path, filename=filename), caption=f"📄 {type_name} uchun namuna fayli")
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="method_file"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    text = (
        f"<b>📄 {type_name.upper()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Siz tanlagan tur uchun namuna formati:\n\n"
        f"<code>{mono_text}</code>\n\n"
        f"<i>💡 Yuqoridagi matn ustiga bitta bossangiz nusxa olinadi. O'zgartirib, savollaringizni shu ko'rinishda yozing va menga fayl (TXT, PDF, DOCX) qilib yuboring.</i>\n\n"
        f"⏳ <b>Faylingizni yuklashingizni kutmoqdaman...</b>"
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
        
        questions = parse_file(tmp_path)
        os.remove(tmp_path) 
            
        if not questions:
            return await status_msg.edit_text("❌ Fayldan savollar topilmadi. Namunadagidek yozilganiga ishonch hosil qiling.")
            
        await state.update_data(questions=questions)
        
        text = (
            f"<b>✅ {len(questions)} TA SAVOL TOPILDI</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Test qaysi fanga tegishli? Pastdan tanlang:"
        )
        await status_msg.edit_text(text, reply_markup=create_subject_keyboard())
    except Exception as e:
        logger.error(f"Fayl xatosi: {e}")
        await status_msg.edit_text("❌ Xatolik yuz berdi.")

# ==========================================================
# 4. QUIZBOTDAN FORWARD QILISH VA TXT YUKLASH IMKONIYATI
# ==========================================================
@router.callback_query(F.data == "method_poll", CreateTest.choose_method)
async def method_poll_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(questions=[])
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Yakunlash", callback_data="finish_polls"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    text = (
        "<b>📊 QUIZBOTDAN UZATISH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Endi @QuizBot dagi tayyor viktorinalarni shu yerga <b>Forward (Uzatish)</b> qiling.\n"
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
    builder.row(InlineKeyboardButton(text="✅ Yakunlash", callback_data="finish_polls"))
    await message.answer(f"✅ Savol qo'shildi (Jami: {len(questions)} ta).", reply_markup=builder.as_markup())

@router.callback_query(F.data == "finish_polls", CreateTest.waiting_for_polls)
async def finish_polls_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("questions"):
        return await callback.answer("❌ Hech bo'lmasa 1 ta savol yuboring!", show_alert=True)
    
    # YANGI MANTIQ: Foydalanuvchiga TXT yuklash yoki Bazaga saqlash tanlovi beriladi
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💾 Bazaga test qilib saqlash", callback_data="save_to_db_poll"))
    builder.row(InlineKeyboardButton(text="📥 Matn (TXT) fayl qilib yuklash", callback_data="download_txt_poll"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    text = (
        f"<b>✅ {len(data['questions'])} TA SAVOL YIG'ILDI!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Savollar bilan nima qilamiz? Ularni bazaga test qilib yuklaysizmi yoki TXT formatda o'zingizga ko'chirib olasizmi?"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

# YIG'ILGAN SAVOLLARNI TXT QILIB BERISH
@router.callback_query(F.data == "download_txt_poll", CreateTest.waiting_for_polls)
async def download_txt_poll_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    questions = data.get("questions", [])
    
    txt_content = ""
    for i, q in enumerate(questions, 1):
        txt_content += f"{i}. {q['question']}\n"
        for opt in q['options']:
            # To'g'ri javob oldiga === qo'shamiz
            if opt == q['correct'] or (isinstance(opt, str) and opt.startswith(q['correct'])):
                txt_content += f"==={opt}\n"
            else:
                txt_content += f"{opt}\n"
        txt_content += f"Izoh: {q.get('explanation', 'Izoh kiritilmagan')}\n\n"
        
    file_obj = io.BytesIO(txt_content.encode('utf-8'))
    await callback.message.answer_document(
        BufferedInputFile(file_obj.getvalue(), filename="QuizBot_Testlar.txt"), 
        caption="📄 QuizBot'dan yig'ilgan testlar va to'g'ri javoblari."
    )
    await state.clear()
    await callback.message.delete()

# BAZAGA SAQLASHNI DAVOM ETTIRISH
@router.callback_query(F.data == "save_to_db_poll", CreateTest.waiting_for_polls)
async def save_to_db_poll_handler(callback: CallbackQuery, state: FSMContext):
    text = (
        "<b>📝 FANNI TANLANG</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Test qaysi fanga tegishli ekanini tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=create_subject_keyboard())


# ==========================================================
# 5. FAN, MAVZU VA SOZLAMALAR
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

# ==========================================================
# 6. YAKUNIY SAQLASH (WEB INTEGRATSIYA B/N)
# ==========================================================
@router.callback_query(F.data.startswith("vis_"), CreateTest.set_visibility)
async def set_visibility_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏳ Saqlanmoqda...")
    visibility = callback.data.replace("vis_", "")
    data = await state.get_data()
    
    test_id = str(uuid.uuid4())
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    access_code = ''.join(random.choice(chars) for _ in range(6))
    
    from firebase.config import get_db
    db = get_db()
    bot_questions = data.get("questions", [])
    
    new_test = {
        "title": data.get("title"),
        "category": data.get("category"),
        "authorId": str(callback.from_user.id),
        "creator_id": callback.from_user.id,
        "difficulty": data.get("difficulty"),
        "time_limit": data.get("time_limit"),
        "passing_score": data.get("passing_score"),
        "max_attempts": data.get("max_attempts"),
        "visibility": visibility,
        "accessCode": access_code,
        "questionCount": len(bot_questions),
        "attempts": 0,
        "averageScore": 0,
        "solve_count": 0,
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc)
    }
    
    test_ref = db.collection("tests").document(test_id)
    test_ref.set(new_test)
    
    batch = db.batch()
    for i, q in enumerate(bot_questions):
        q_ref = test_ref.collection("questions").document()
        
        raw_options = q.get("options", [])
        clean_options = []
        correct_idx = 0
        bot_correct = q.get("correct", "")
        
        for idx, opt in enumerate(raw_options):
            clean_text = opt.split(")", 1)[1].strip() if ")" in opt else opt
            clean_options.append(clean_text)
            if opt == bot_correct or (")" in opt and bot_correct.startswith(opt.split(")")[0])):
                correct_idx = idx
                
        web_q = {
            "order": i,
            "text": q.get("question", ""),
            "type": "multiple",
            "options": clean_options,
            "correct": correct_idx,
            "bot_correct": bot_correct,
            "explanation": q.get("explanation", "Izoh kiritilmagan"),
            "points": q.get("points", 1)
        }
        batch.set(q_ref, web_q)
        
    batch.commit()
    await state.clear()
    
    bot_user = await callback.bot.me()
    text = (
        f"<b>🎉 TEST MUVAFFAQIYATLI YARATILDI!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 Kod: <code>{access_code}</code>\n"
        f"🔗 Ssilka: <code>https://t.me/{bot_user.username}?start={access_code}</code>\n\n"
        f"📌 Fan: {new_test['category']}\n"
        f"🏷 Mavzu: {new_test['title']}"
    )
    await callback.message.edit_text(text)

    keys = f"<b>🔑 {new_test['title'].upper()} - JAVOBLAR</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, q in enumerate(bot_questions):
        keys += f"<b>{i+1}.</b> {q['correct']}\n"
    
    if len(keys) > 4000:
        file_obj = io.BytesIO(keys.encode('utf-8'))
        await callback.message.answer_document(BufferedInputFile(file_obj.getvalue(), filename=f"Kalit_{access_code}.txt"), caption="🔑 Kalit")
    else:
        await callback.message.answer(keys)

@router.callback_query(F.data == "cancel_creation")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer("❌ Bekor qilindi.", reply_markup=main_reply_keyboard(callback.from_user.id))
        

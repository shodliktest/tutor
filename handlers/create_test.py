"""
➕ TEST YARATISH HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Fayl yoki Quiz orqali test tuzish, fanni va TEST MAZUSINI alohida so'rash.
Hech narsa qisqartirilmadi!
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

from utils.parser import parse_file
from utils.states import CreateTest
from keyboards.keyboards import difficulty_keyboard, test_visibility_keyboard, create_subject_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)
router = Router()

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "samples")
SAMPLE_FILES = {
    "multiple_choice": ("multiple_choice_namuna.txt", "🔘 Bir javobli test"),
    "all":             ("barcha_turlar_namuna.txt",    "📦 Barcha test turlari"),
}

# ==========================================================
# 1. YARATISH USULINI TANLASH (FAYL YOKI QUIZ)
# ==========================================================
@router.message(F.text == "➕ Test Yaratish")
async def create_test_start_msg(message: Message, state: FSMContext):
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📁 Fayl yuklash (TXT, PDF)", callback_data="method_file"),
        InlineKeyboardButton(text="📊 Telegram Quiz (So'rovnoma)", callback_data="method_poll")
    )
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    await message.answer(
        "📝 <b>TEST YARATISH BO'LIMI</b>\n\n"
        "Testni qanday usulda yaratmoqchisiz?\n"
        "1. <b>Fayl yuklash:</b> Tayyor hujjatni yuborish.\n"
        "2. <b>Telegram Quiz:</b> Botga viktorina so'rovnomalarini yasab yoki uzatib (forward) yig'ish.",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.choose_method)

# ==========================================================
# 2. FAYL USULI 
# ==========================================================
@router.callback_query(F.data == "method_file", CreateTest.choose_method)
async def method_file_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📂 Namuna fayllarni ko'rish", callback_data="show_samples"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    await callback.message.edit_text(
        "📁 <b>FAYL ORQALI YARATISH</b>\n\n"
        "Iltimos, test savollari bor TXT, DOCX yoki PDF faylni yuboring.",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CreateTest.upload_file)

@router.callback_query(F.data == "show_samples", CreateTest.upload_file)
async def show_samples_handler(callback: CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    for key, (filename, btn_text) in SAMPLE_FILES.items():
        builder.row(InlineKeyboardButton(text=btn_text, callback_data=f"sample_{key}"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    await callback.message.edit_text("📂 <b>NAMUNA FAYLLAR</b>\n\nQaysi turdagi test namunasini yuklab olmoqchisiz?", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("sample_"), CreateTest.upload_file)
async def send_sample_file(callback: CallbackQuery):
    await callback.answer()
    key = callback.data.replace("sample_", "")
    filename = SAMPLE_FILES.get(key, SAMPLE_FILES["all"])[0]
    file_path = os.path.join(SAMPLES_DIR, filename)
    if os.path.exists(file_path):
        await callback.message.answer_document(FSInputFile(file_path, filename=filename), caption="📄 Namuna fayl.")

@router.message(F.document, CreateTest.upload_file)
async def upload_file_handler(message: Message, state: FSMContext):
    doc = message.document
    if not doc.file_name.lower().endswith(('.txt', '.pdf', '.docx')):
        return await message.answer("❌ Faqat TXT, PDF yoki DOCX fayllar qabul qilinadi!")

    status_msg = await message.answer("⏳ Fayl o'qilmoqda...")
    try:
        file = await message.bot.get_file(doc.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{doc.file_name}") as tmp_file:
            await message.bot.download_file(file.file_path, tmp_file.name)
            tmp_path = tmp_file.name
        try:
            questions = parse_file(tmp_path)
        finally:
            os.remove(tmp_path) 
            
        if not questions:
            return await status_msg.edit_text("❌ Fayldan hech qanday savol topilmadi.")
            
        await state.update_data(questions=questions)
        await status_msg.edit_text(
            f"✅ <b>{len(questions)} ta savol topildi!</b>\n\n📝 <b>Test qaysi fanga tegishli? Pastdan tanlang:</b>",
            reply_markup=create_subject_keyboard()
        )
    except Exception as e:
        logger.error(f"Fayl xatosi: {e}")
        await status_msg.edit_text("❌ Faylni o'qishda xatolik yuz berdi.")

# ==========================================================
# 3. QUIZBOT USULI
# ==========================================================
@router.callback_query(F.data == "method_poll", CreateTest.choose_method)
async def method_poll_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(questions=[]) 
    
    text = (
        "📊 <b>TELEGRAM QUIZ ORQALI YARATISH</b>\n\n"
        "Telegramning o'zidan <b>Viktorina (Quiz)</b> yasab shu yerga yuboring, "
        "yoki boshqa guruh/botlardan qiziqarli testlarni bu yerga <b>Forward</b> qiling!\n\n"
        "<i>Har bir yuborgan testingiz to'plamga qoshilaveradi. Savollar yetarli bo'lganda '✅ Tayyor' tugmasini bosing.</i>"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Tayyor (Keyingi qadam)", callback_data="finish_polls"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(CreateTest.waiting_for_polls)

@router.message(F.poll, CreateTest.waiting_for_polls)
async def catch_poll_handler(message: Message, state: FSMContext):
    poll = message.poll
    
    if poll.type != "quiz":
        return await message.answer("❌ Iltimos, oddiy so'rovnoma emas, <b>Viktorina (Quiz)</b> turidagi so'rov yuboring!")
        
    data = await state.get_data()
    questions = data.get("questions", [])
    
    letters = ["A)", "B)", "C)", "D)", "E)", "F)", "G)", "H)", "I)", "J)"]
    options = []
    correct_answer = "A)"
    
    for i, opt in enumerate(poll.options):
        letter = letters[i] if i < len(letters) else f"{i+1})"
        formatted_opt = f"{letter} {opt.text}"
        options.append(formatted_opt)
        if i == poll.correct_option_id:
            correct_answer = formatted_opt
            
    explanation = poll.explanation or "Izoh kiritilmagan."
    
    new_q = {
        "type": "multiple_choice",
        "question": poll.question,
        "options": options,
        "correct": correct_answer,
        "explanation": explanation,
        "points": 1
    }
    
    questions.append(new_q)
    await state.update_data(questions=questions)
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Tayyor (Keyingi qadam)", callback_data="finish_polls"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation"))
    
    await message.answer(
        f"✅ Savol to'plamga qo'shildi! <b>(Jami: {len(questions)} ta)</b>\n"
        f"Yana test yuborishingiz yoki 'Tayyor' tugmasini bosishingiz mumkin.",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "finish_polls", CreateTest.waiting_for_polls)
async def finish_polls_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    questions = data.get("questions", [])
    
    if not questions:
        return await callback.answer("❌ Hech qanday test yubormadingiz!", show_alert=True)
        
    await callback.message.edit_text(
        f"🎉 <b>Ajoyib! Jami {len(questions)} ta savol yig'ildi.</b>\n\n"
        f"📝 <b>Test qaysi fanga tegishli? Pastdan tanlang:</b>",
        reply_markup=create_subject_keyboard()
    )

# ==========================================================
# 4. FAN VA TEST MAZUSINI BELGILASH (YANGILANGAN)
# ==========================================================
@router.callback_query(F.data.startswith("set_subj_"), CreateTest.upload_file)
@router.callback_query(F.data.startswith("set_subj_"), CreateTest.waiting_for_polls)
async def process_subject_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    subj = callback.data.replace("set_subj_", "")
    
    if subj == "other":
        await callback.message.edit_text("📝 <b>Fanning nomini yozib yuboring (Masalan: Ingliz tili):</b>")
        await state.set_state(CreateTest.set_subject)
    else:
        # 🛡️ Fanni kategoriya sifatida saqlaymiz va nomini so'raymiz
        await state.update_data(category=subj)
        await callback.message.edit_text(
            f"✅ Fan: <b>{subj}</b>\n\n"
            f"🏷 <b>Endi test uchun qisqacha nom yoki mavzu yozib yuboring:</b>\n"
            f"<i>(Masalan: 'O'nlik kasrlar', 'Fe\\'l zamonlari', '1-chorak takrorlash')</i>"
        )
        await state.set_state(CreateTest.set_test_title)

@router.message(F.text, CreateTest.set_subject)
async def set_subject_manual(message: Message, state: FSMContext):
    # 🛡️ Fanni kategoriya sifatida saqlaymiz va nomini so'raymiz
    await state.update_data(category=message.text)
    await message.answer(
        f"✅ Fan: <b>{message.text}</b>\n\n"
        f"🏷 <b>Endi test uchun qisqacha nom yoki mavzu yozib yuboring:</b>\n"
        f"<i>(Masalan: 'O'nlik kasrlar', 'Fe\\'l zamonlari', '1-chorak takrorlash')</i>"
    )
    await state.set_state(CreateTest.set_test_title)

# 🛡️ YANGI QADAM: TEST NOMINI SAQLASH
@router.message(F.text, CreateTest.set_test_title)
async def set_test_title_handler(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        f"✅ Test mavzusi: <b>{message.text}</b>\n\n"
        f"Endi <b>qiyinlik darajasini</b> tanlang:", 
        reply_markup=difficulty_keyboard()
    )
    await state.set_state(CreateTest.set_difficulty)

# ==========================================================
# 5. UMUMIY SOZLAMALAR (QIYINLIK, VAQT ...)
# ==========================================================
@router.callback_query(F.data.startswith("diff_"), CreateTest.set_difficulty)
async def set_difficulty_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(difficulty=callback.data.replace("diff_", ""))
    await callback.message.edit_text("⏱ <b>Test ishlash uchun vaqt limitini kiriting (daqiqalarda):</b>\n<i>Agar cheklanmagan bo'lsa 0 yozing.</i>")
    await state.set_state(CreateTest.set_time_limit)

@router.message(F.text, CreateTest.set_time_limit)
async def set_time_limit_handler(message: Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ Iltimos, faqat raqam kiriting.")
    await state.update_data(time_limit=int(message.text))
    await message.answer("🎯 <b>Testdan muvaffaqiyatli o'tish foizini kiriting (0-100):</b>")
    await state.set_state(CreateTest.set_passing_score)

@router.message(F.text, CreateTest.set_passing_score)
async def set_passing_score_handler(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (0 <= int(message.text) <= 100):
        return await message.answer("❌ Iltimos, 0 dan 100 gacha bo'lgan raqam kiriting.")
    await state.update_data(passing_score=int(message.text))
    await message.answer("🔄 <b>Ushbu testni necha marta ishlashga ruxsat berasiz?</b>\n<i>Agar cheklanmagan bo'lsa 0 yozing.</i>")
    await state.set_state(CreateTest.set_max_attempts)

@router.message(F.text, CreateTest.set_max_attempts)
async def set_max_attempts_handler(message: Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ Iltimos, faqat raqam kiriting.")
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
    category = data.get("category", "Boshqa") # Fanni kategoriyaga olamiz
    
    from firebase.config import get_db
    test_id = str(uuid.uuid4())[:8]
    
    new_test = {
        "test_id": test_id, 
        "title": title, 
        "category": category, 
        "creator_id": callback.from_user.id,
        "difficulty": data.get("difficulty", "medium"), 
        "time_limit": data.get("time_limit", 0),
        "passing_score": data.get("passing_score", 60), 
        "max_attempts": data.get("max_attempts", 0),
        "visibility": visibility, 
        "questions": questions, 
        "created_at": datetime.now(timezone.utc), 
        "solve_count": 0
    }
    
    get_db().collection("tests").document(test_id).set(new_test)
    await state.clear()
    
    bot_username = (await callback.bot.me()).username
    vis_text = {"public": "🌍 Ommaviy", "link": "🔗 Ssilka orqali", "private": "🔒 Shaxsiy"}[visibility]
    
    await callback.message.edit_text(
        f"🎉 <b>TEST MUVAFFAQIYATLI YARATILDI!</b>\n\n"
        f"<b>Test kodi:</b> <code>{test_id}</code>\n"
        f"<b>Ssilka:</b> <code>https://t.me/{bot_username}?start={test_id}</code>\n\n"
        f"📊 <b>Ma'lumotlar:</b>\n• Fan: {category}\n• Mavzu: {title}\n• Savollar: {len(questions)} ta\n• Holat: {vis_text}\n\n"
        f"<i>Klitlar pastda yuboriladi:</i>"
    )

    key_text = f"🔑 <b>{title.upper()} - JAVOBLAR KALITI</b>\n\n"
    for i, q in enumerate(questions):
        corr = q.get("correct", "Noma'lum")
        if isinstance(corr, list): corr = ", ".join(corr)
        elif isinstance(corr, dict): corr = ", ".join([f"{k}-{v}" for k, v in corr.items()])
        key_text += f"<b>{i+1}-savol:</b> {corr}\n"
        
    if len(key_text) > 4000:
        file_obj = io.BytesIO(key_text.encode('utf-8'))
        await callback.message.answer_document(BufferedInputFile(file_obj.getvalue(), filename=f"Klit_{test_id}.txt"), caption="🔑 Kalit")
    else:
        await callback.message.answer(key_text, parse_mode="HTML")

@router.callback_query(F.data == "cancel_creation")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    try: await callback.message.delete()
    except: pass
    from keyboards.keyboards import main_reply_keyboard
    await callback.message.answer("❌ Test yaratish bekor qilindi.", reply_markup=main_reply_keyboard(callback.from_user.id))
        

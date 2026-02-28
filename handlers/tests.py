"""
📚 TEST YECHISH VA TAHLIL HANDLER
Faqat barqaror test turlari (A, B, C va Rost/Yolg'on).
Javob berilgach 5 sekund davomida ✅/❌ belgilar va izoh ko'rsatilib,
keyin avtomatik keyingi savolga o'tadi.
Ssilka va uzun matnlar xatosi yopilgan.
"""
import time
import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from firebase.db import get_test, save_result, get_user, get_db, get_all_tests
from utils.states import TestSolving
from keyboards.keyboards import result_keyboard, main_reply_keyboard

logger = logging.getLogger(__name__)
router = Router()

# ==========================================================
# 1. TESTLAR KATALOGI
# ==========================================================
async def send_categories_menu(message_or_callback):
    all_tests = get_all_tests()
    public_tests = [t for t in all_tests if t.get("visibility") == "public"]
    
    text = (
        "<b>📚 TESTLAR BO'LIMI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Test kodini (ID) to'g'ridan-to'g'ri yozib yuboring yoki pastdagi fanlardan birini tanlang:</i>\n\n"
    )
    
    if not public_tests:
        text += "Hozircha bazada ommaviy testlar mavjud emas."
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(text)
        else:
            await message_or_callback.message.edit_text(text)
        return

    categories = {}
    for t in public_tests:
        cat = t.get("category", "Boshqa")
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1
        
    builder = InlineKeyboardBuilder()
    for cat, count in categories.items():
        cb_data = f"cat_{cat}"[:40] 
        builder.row(InlineKeyboardButton(text=f"📁 {cat} ({count})", callback_data=cb_data))
        
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(text, reply_markup=builder.as_markup())
    else:
        await message_or_callback.message.edit_text(text, reply_markup=builder.as_markup())

@router.message(StateFilter(None), F.text == "📚 Testlar")
async def tests_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await send_categories_menu(message)

# DIQQAT: Faqat 6 xonali kod yoki 20+ harfli haqiqiy ID ni qabul qiladi. 
# Ichida bo'sh joy, ssilka (/) yoki enter bo'lmasligi qat'iy tekshiriladi!
@router.message(StateFilter(None), F.text, lambda msg: msg.text and ("/" not in msg.text) and ("\n" not in msg.text) and (" " not in msg.text) and (len(msg.text.strip()) == 6 or len(msg.text.strip()) >= 20))
async def direct_code_handler(message: Message, state: FSMContext):
    test_id = message.text.strip()
    test = get_test(test_id)
    if test:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🚀 Testni boshlash", callback_data=f"start_test_{test.get('test_id')}"))
        text = (
            f"<b>🔍 TEST TOPILDI!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🏷 <b>Mavzu:</b> {test.get('title')}\n"
            f"📁 <b>Fan:</b> {test.get('category')}\n"
            f"📋 <b>Savollar:</b> {test.get('questionCount', len(test.get('questions', [])))} ta\n"
        )
        await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("cat_"))
async def show_tests_in_category(callback: CallbackQuery):
    await callback.answer()
    cat_name = callback.data.replace("cat_", "")
    
    all_tests = get_all_tests()
    cat_tests = [t for t in all_tests if t.get("visibility") == "public" and str(t.get("category", "")).startswith(cat_name)]
    
    if not cat_tests:
        return await callback.message.edit_text("❌ Bu fanda testlar topilmadi.")
        
    text = (
        f"<b>📁 FAN: {cat_tests[0].get('category', 'Boshqa').upper()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Qaysi testni ishlashni xohlaysiz?"
    )
    
    builder = InlineKeyboardBuilder()
    for t in cat_tests:
        t_title = t.get("title", "Nomsiz test")
        t_id = t.get("test_id")
        builder.row(InlineKeyboardButton(text=f"📝 {t_title}", callback_data=f"start_test_{t_id}"))
        
    builder.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_categories"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "back_to_categories")
async def back_to_cat_handler(callback: CallbackQuery):
    await callback.answer()
    await send_categories_menu(callback)

# ==========================================================
# 2. TESTNI BOSHLASH VA SAVOLNI EKRANGA CHIQARISH
# ==========================================================
@router.callback_query(F.data.startswith("start_test_"))
async def start_test_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    test_id = callback.data.replace("start_test_", "")
    test = get_test(test_id)
    
    if not test:
        return await callback.message.answer("❌ Test topilmadi yoki o'chirilgan.")
        
    questions = test.get("questions", [])
    if not questions:
        return await callback.message.answer("❌ Ushbu testda savollar yo'q.")
        
    await state.update_data(
        test_data=test,
        questions=questions,
        current_index=0,
        user_answers={},
        start_time=time.time()
    )
    await state.set_state(TestSolving.answering)
    await send_question(callback, state, edit=True)

async def send_question(message_or_callback, state: FSMContext, edit: bool = False):
    state_data = await state.get_data()
    questions = state_data.get("questions", [])
    current_index = state_data.get("current_index", 0)
    test_title = state_data.get("test_data", {}).get("title", "Nomsiz test")
    q = questions[current_index]
    
    start_time = state_data.get("start_time")
    time_limit = state_data.get("test_data", {}).get("time_limit", 0)
    time_text = ""
    if time_limit > 0 and start_time:
        elapsed = int(time.time() - start_time)
        remain = max(0, (time_limit * 60) - elapsed)
        m, s = divmod(remain, 60)
        time_text = f" | ⏱ {m:02d}:{s:02d}"

    header = (
        f"<b>📝 {test_title} | {current_index + 1}/{len(questions)}{time_text}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    q_text = q.get("question", q.get("text", "Savol matni kiritilmagan"))
    question_text = f"<b>{q_text}</b>\n\n"
    
    options_text = ""
    builder = InlineKeyboardBuilder()
    
    letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    
    if "options" in q:
        for idx, opt in enumerate(q["options"]):
            letter = letters[idx] if idx < len(letters) else str(idx)
            text = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
                
            options_text += f"▫️ <b>{letter})</b> <i>{text}</i>\n"
            builder.add(InlineKeyboardButton(text=letter, callback_data=f"ans_{letter}"))
        builder.adjust(2)

    full_text = header + question_text + options_text

    builder.row(InlineKeyboardButton(text="❌ Testni to'xtatish", callback_data="cancel_test"))

    if edit and isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(full_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        obj = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
        await obj.answer(full_text, reply_markup=builder.as_markup(), parse_mode="HTML")

# ==========================================================
# 3. JAVOB BERILGANDA 5 SEKUNDLIK KUTISH VA TAHLIL
# ==========================================================
@router.callback_query(F.data.startswith("ans_"), TestSolving.answering)
async def process_button_answer(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if not current_state: return
    
    answer = callback.data.replace("ans_", "")
    state_data = await state.get_data()
    
    current_index = state_data.get("current_index", 0)
    questions = state_data.get("questions", [])
    q = questions[current_index]
    test_title = state_data.get("test_data", {}).get("title", "Nomsiz test")
    
    user_answers = state_data.get("user_answers", {})
    user_answers[str(current_index)] = answer
    await state.update_data(user_answers=user_answers)
    
    c_ans = q.get("correct", "")
    letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    
    c_letter = str(c_ans).split(")")[0].strip() if isinstance(c_ans, str) and ")" in str(c_ans) else str(c_ans)
    if isinstance(c_ans, int):
        c_letter = letters[c_ans] if c_ans < len(letters) else "?"
        
    is_correct = (answer.lower() == c_letter.lower())
    
    # UI QISMI (5 SEKUND KO'RINIB TURADIGAN EKRAN)
    header = f"<b>📝 {test_title} | {current_index + 1}/{len(questions)}</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    q_text = q.get("question", q.get("text", "Savol matni kiritilmagan"))
    text_body = f"<b>{q_text}</b>\n\n"
    
    for idx, opt in enumerate(q.get("options", [])):
        letter = letters[idx] if idx < len(letters) else str(idx)
        opt_text = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
        
        if letter.lower() == c_letter.lower():
            text_body += f"✅ <b>{letter})</b> <i>{opt_text}</i>\n"
        elif letter.lower() == answer.lower() and not is_correct:
            text_body += f"❌ <b>{letter})</b> <i>{opt_text}</i>\n"
        else:
            text_body += f"▫️ <b>{letter})</b> <i>{opt_text}</i>\n"

    text_body += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
    
    if is_correct:
        text_body += "🎯 <b>Natija:</b> ✅ TO'G'RI\n"
    else:
        text_body += "🎯 <b>Natija:</b> ❌ NOTO'G'RI\n"
        
    explanation = q.get("explanation", "")
    if explanation and explanation not in ["Izoh kiritilmagan", "Izoh kiritilmagan.", "Izoh yo'q"]:
        text_body += f"💡 <b>Izoh:</b> <i>{explanation}</i>\n"
        
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏳ Keyingi savolga o'tilmoqda...", callback_data="wait"))
    builder.row(InlineKeyboardButton(text="❌ Testni to'xtatish", callback_data="cancel_test"))

    await callback.message.edit_text(header + text_body, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()
    
    # 5 SEKUND KUTISH
    await asyncio.sleep(5)
    
    if await state.get_state() == TestSolving.answering.state:
        if current_index < len(questions) - 1:
            await state.update_data(current_index=current_index + 1)
            await send_question(callback, state, edit=True)
        else:
            await finish_test_process(callback.message, state, await state.get_data())

@router.callback_query(F.data == "cancel_test", TestSolving.answering)
async def cancel_test_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("<b>❌ TEST TO'XTATILDI</b>\n━━━━━━━━━━━━━━━━━━━━━━\nSiz test ishlashni to'xtatdingiz. Natijalar saqlanmadi.", reply_markup=main_reply_keyboard(callback.from_user.id))
    await callback.answer()

# ==========================================================
# 4. YAKUNLASH VA BAHOLASH
# ==========================================================
async def finish_test_process(message: Message, state: FSMContext, state_data: dict):
    test = state_data.get("test_data", {})
    questions = state_data.get("questions", [])
    user_answers = state_data.get("user_answers", {})
    start_time = state_data.get("start_time", time.time())
    
    detailed_results = []
    correct_count = 0
    letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    
    for i, q in enumerate(questions):
        idx_str = str(i)
        u_ans = user_answers.get(idx_str, "Belgilanmagan") 
        c_ans = q.get("correct", "")
        
        c_letter = c_ans.split(")")[0].strip() if isinstance(c_ans, str) and ")" in c_ans else str(c_ans)
        if isinstance(c_ans, int):
            c_letter = letters[c_ans] if c_ans < len(letters) else "?"
            correct_full_text = f"{c_letter}) {q.get('options', [])[c_ans]}" if c_ans < len(q.get('options', [])) else c_letter
        else:
            correct_full_text = str(c_ans)
            
        is_correct = (str(u_ans).lower() == c_letter.lower()) and u_ans != "Belgilanmagan"
            
        if is_correct: 
            correct_count += 1
            
        detailed_results.append({
            "question_index": i,
            "user_answer": str(u_ans),
            "correct_answer": correct_full_text,
            "is_correct": is_correct
        })
    
    score_percentage = (correct_count / len(questions)) * 100 if questions else 0
    passing_score = test.get("passing_score", 60)
    passed = score_percentage >= passing_score
    time_spent_sec = int(time.time() - start_time)
    
    result_data = {
        "score": score_percentage,
        "correct_count": correct_count,
        "total_questions": len(questions),
        "passed": passed,
        "time_spent": time_spent_sec,
        "detailed_results": detailed_results 
    }
    
    chat_id = message.chat.id
    result_id = save_result(chat_id, test.get("test_id"), result_data)
    user = get_user(chat_id)
    user_name = user.get("name", "Foydalanuvchi") if user else "Foydalanuvchi"
    
    m, s = divmod(time_spent_sec, 60)
    time_str = f"{m} daq {s} son" if m > 0 else f"{s} son"
    
    text = (
        f"<b>📊 YAKUNIY NATIJA</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>Mavzu:</b> {test.get('title', 'Nomsiz')}\n"
        f"📋 <b>Savollar:</b> {len(questions)} ta\n"
        f"✅ <b>To'g'ri:</b> {correct_count} ta\n"
        f"🎯 <b>Natija:</b> {round(score_percentage, 1)}%\n"
        f"⏱ <b>Vaqt:</b> {time_str}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎓 <b>Holat:</b> {'🎉 MUVAFFAQIYATLI!' if passed else '❌ YIQILDINGIZ.'}"
    )
    
    try:
        await message.delete()
    except:
        pass
    
    await message.bot.send_message(chat_id, text, reply_markup=result_keyboard(test.get("test_id"), result_id, passed), parse_mode="HTML")
    await state.clear()

# ==========================================================
# 5. TAHLILNI KO'RSATISH (DETAILED ANALYSIS)
# ==========================================================
@router.callback_query(F.data.startswith("analysis_"))
async def analysis_handler(callback: CallbackQuery):
    await callback.answer("⏳ Tahlil yuklanmoqda...")
    result_id = callback.data.replace("analysis_", "")
    
    res_doc = get_db().collection("results").document(result_id).get()
    if not res_doc.exists: 
        return await callback.message.answer("❌ Natija bazadan topilmadi.")
        
    res_data = res_doc.to_dict()
    detailed = res_data.get("detailed_results", [])
    test = get_test(res_data.get("test_id"))
    questions = test.get("questions", []) if test else []
    
    if not detailed:
        return await callback.message.answer("<b>⚠️ ESKI TEST</b>\nBu eski test, uning tahlili yo'q.", parse_mode="HTML")

    chunks = []
    current_chunk = f"<b>📝 {test.get('title', 'Test').upper()} - TAHLIL</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for d in detailed:
        idx = d.get("question_index", 0)
        is_correct = d.get("is_correct", False)
        user_ans = d.get("user_answer", "Belgilanmagan")
        corr_ans = d.get("correct_answer", "Noma'lum")
        
        q_text = questions[idx].get("question", "Savol topilmadi") if idx < len(questions) else ""
        explanation = questions[idx].get("explanation", "Izoh yo'q") if idx < len(questions) else "Izoh yo'q"
        status = "✅ TO'G'RI" if is_correct else "❌ XATO"
        
        block = f"<b>Savol {idx+1}:</b> {q_text}\nHolat: {status}\n👤 <b>Siz:</b> <i>{user_ans}</i>\n"
        if not is_correct: block += f"🎯 <b>To'g'ri:</b> <i>{corr_ans}</i>\n"
        
        if explanation not in ["Izoh yo'q", "Izoh kiritilmagan", "Izoh kiritilmagan."]:
            block += f"💡 <b>Izoh:</b> <i>{explanation}</i>\n"
            
        block += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if len(current_chunk) + len(block) > 4000:
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk += block
        
    if current_chunk: chunks.append(current_chunk)
    for chunk in chunks:
        await callback.message.answer(chunk, parse_mode="HTML", protect_content=True)
        

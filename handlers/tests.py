"""
📚 TEST YECHISH VA TAHLIL HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Aqlli "Izoh rejimi" (Study Mode), avtomatik o'tish va to'liq tahlil.
Natijalar 100% to'liq ko'rsatiladi.
"""
import time
import logging
from aiogram import Router, F
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
# 1. TESTLAR KATALOGI (FANLAR VA SONI)
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

@router.message(F.text == "📚 Testlar")
async def tests_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await send_categories_menu(message)

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
        start_time=time.time(),
        exp_mode=False, 
        show_exp=False  
    )
    await state.set_state(TestSolving.answering)
    await send_question(callback, state, edit=True)

async def send_question(message_or_callback, state: FSMContext, edit: bool = False):
    state_data = await state.get_data()
    questions = state_data.get("questions", [])
    current_index = state_data.get("current_index", 0)
    test_title = state_data.get("test_data", {}).get("title", "Nomsiz test")
    q = questions[current_index]
    
    show_exp = state_data.get("show_exp", False)
    exp_mode = state_data.get("exp_mode", False)
    
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
    
    question_text = f"<b>{q.get('question', 'Savol matni kiritilmagan')}</b>\n\n"
    
    options_text = ""
    builder = InlineKeyboardBuilder()
    
    user_answers = state_data.get("user_answers", {})
    current_answer = user_answers.get(str(current_index), None)
    
    if q.get("type") == "multiple_choice" and "options" in q:
        for opt in q["options"]:
            if ")" in opt:
                letter, text = opt.split(")", 1)
                letter = letter.strip()
                text = text.strip()
                
                prefix = "✅ " if current_answer == f"{letter})" else ""
                options_text += f"{prefix}<b>{letter})</b> <i>{text}</i>\n"
                
                btn_text = f"✅ {letter}" if current_answer == f"{letter})" else letter
                builder.add(InlineKeyboardButton(text=btn_text, callback_data=f"ans_{letter})"))
            else:
                options_text += f"<i>{opt}</i>\n"
                letter = opt[:1]
                btn_text = f"✅ {letter}" if current_answer == opt else letter
                builder.add(InlineKeyboardButton(text=btn_text, callback_data=f"ans_{opt}"))
        
        builder.adjust(2)
    else:
        options_text += "<i>Bu savol turiga javob berish formatlanmagan.</i>\n\n"

    full_text = header + question_text + options_text

    if show_exp:
        explanation = q.get("explanation", "Ushbu savol uchun izoh kiritilmagan.")
        full_text += f"\n━━━━━━━━━━━━━━━━━━━━━━\n💡 <b>Izoh:</b> <i>{explanation}</i>\n"

    exp_btn_text = "💡 Izoh rejimi: 🟢 YONIQ" if exp_mode else "💡 Izoh rejimi: 🔴 O'CHIK"
    builder.row(InlineKeyboardButton(text=exp_btn_text, callback_data="toggle_exp_mode"))

        # 🎛 NAVIGATSIYA TUGMALARI (Oldingi/Keyingi olib tashlandi)
    nav_row = []
    # Faqat oxirgi savolga kelganda "Yakunlash" tugmasi chiqadi
    if current_index == len(questions) - 1:
        nav_row.append(InlineKeyboardButton(text="🏁 Yakunlash", callback_data="nav_finish"))

    
    builder.row(*nav_row)
    builder.row(InlineKeyboardButton(text="❌ Testni to'xtatish", callback_data="cancel_test"))

    if edit and isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(full_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        obj = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
        await obj.answer(full_text, reply_markup=builder.as_markup(), parse_mode="HTML")

# ==========================================================
# 3. AQLLI JAVOB BERISH LOGIKASI VA NAVIGATSIYA
# ==========================================================
@router.callback_query(F.data == "toggle_exp_mode", TestSolving.answering)
async def toggle_exp_mode_handler(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_mode = state_data.get("exp_mode", False)
    await state.update_data(exp_mode=not current_mode)
    await send_question(callback, state, edit=True)
    await callback.answer(f"Izoh rejimi {'yoqildi' if not current_mode else 'o\'chirildi'}!")

@router.callback_query(F.data.startswith("ans_"), TestSolving.answering)
async def process_answer(callback: CallbackQuery, state: FSMContext):
    answer = callback.data.replace("ans_", "")
    state_data = await state.get_data()
    
    user_answers = state_data.get("user_answers", {})
    current_index = state_data.get("current_index", 0)
    questions = state_data.get("questions", [])
    q = questions[current_index]
    
    user_answers[str(current_index)] = answer
    
    exp_mode = state_data.get("exp_mode", False)
    explanation = q.get("explanation", "")
    has_exp = bool(explanation and explanation != "Izoh kiritilmagan." and explanation != "Izoh yo'q.")
    
    if exp_mode and has_exp:
        await state.update_data(user_answers=user_answers, show_exp=True)
    else:
        if current_index < len(questions) - 1:
            await state.update_data(user_answers=user_answers, current_index=current_index + 1, show_exp=False)
        else:
            await state.update_data(user_answers=user_answers, show_exp=True) 
            
    await send_question(callback, state, edit=True)
    await callback.answer()

@router.callback_query(F.data == "nav_prev", TestSolving.answering)
async def nav_prev_handler(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_index = state_data.get("current_index", 0)
    if current_index > 0:
        await state.update_data(current_index=current_index - 1, show_exp=False)
        await send_question(callback, state, edit=True)
    await callback.answer()

@router.callback_query(F.data == "nav_next", TestSolving.answering)
async def nav_next_handler(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_index = state_data.get("current_index", 0)
    questions = state_data.get("questions", [])
    if current_index < len(questions) - 1:
        await state.update_data(current_index=current_index + 1, show_exp=False)
        await send_question(callback, state, edit=True)
    await callback.answer()

@router.callback_query(F.data == "cancel_test", TestSolving.answering)
async def cancel_test_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    text = (
        "<b>❌ TEST TO'XTATILDI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Siz test ishlashni to'xtatdingiz. Natijalar saqlanmadi."
    )
    await callback.message.answer(text, reply_markup=main_reply_keyboard(callback.from_user.id))
    await callback.answer()

# ==========================================================
# 4. TESTNI YAKUNLASH VA BAZAGA SAQLASH (TO'LIQ NATIJA QISMI)
# ==========================================================
@router.callback_query(F.data == "nav_finish", TestSolving.answering)
async def finish_test_handler(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await callback.message.delete()
    await finish_test_process(callback.message, state, state_data)
    await callback.answer()

async def finish_test_process(message: Message, state: FSMContext, state_data: dict):
    test = state_data.get("test_data", {})
    questions = state_data.get("questions", [])
    user_answers = state_data.get("user_answers", {})
    start_time = state_data.get("start_time", time.time())
    
    detailed_results = []
    correct_count = 0
    
    for i, q in enumerate(questions):
        idx_str = str(i)
        u_ans = user_answers.get(idx_str, "Belgilanmagan")
        c_ans = q.get("correct", "")
        
        c_ans_clean = c_ans.split(" ")[0] if " " in c_ans and ")" in c_ans else c_ans
        
        is_correct = (u_ans == c_ans_clean or u_ans in c_ans)
        if is_correct: 
            correct_count += 1
            
        detailed_results.append({
            "question_index": i,
            "user_answer": u_ans,
            "correct_answer": c_ans,
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
    
    result_id = save_result(message.chat.id, test.get("test_id"), result_data)
    user = get_user(message.chat.id)
    user_name = user.get("name", "Foydalanuvchi") if user else "Foydalanuvchi"
    
    # ⏱ Vaqtni chiroyli ko'rsatish (Daqiqa va Soniya)
    m, s = divmod(time_spent_sec, 60)
    time_str = f"{m} daqiqa {s} soniya" if m > 0 else f"{s} soniya"
    wrong_count = len(questions) - correct_count
    
    text = (
        f"<b>📊 YAKUNIY NATIJA</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>Test mavzusi:</b> {test.get('title', 'Nomsiz test')}\n"
        f"📁 <b>Fan:</b> {test.get('category', 'Boshqa')}\n"
        f"👤 <b>O'quvchi:</b> {user_name}\n\n"
        f"📋 <b>Jami savollar:</b> {len(questions)} ta\n"
        f"✅ <b>To'g'ri javoblar:</b> {correct_count} ta\n"
        f"❌ <b>Xato/Belgilanmagan:</b> {wrong_count} ta\n\n"
        f"🎯 <b>Sizning natijangiz:</b> {round(score_percentage, 1)}%\n"
        f"📈 <b>O'tish bali (Talab):</b> {passing_score}%\n"
        f"⏱ <b>Sarflangan vaqt:</b> {time_str}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎓 <b>Holat:</b> {'🎉 MUVAFFAQIYATLI O\'TDINGIZ!' if passed else '❌ YIQILDINGIZ (O\'ta olmadingiz).'}"
    )
    
    kb = result_keyboard(test.get("test_id"), result_id, passed)
    await message.answer(text, reply_markup=kb, protect_content=True)
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
        await callback.message.answer(
            "<b>⚠️ DIQQAT: ESKI TEST</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Bu eski test bo'lgani uchun, uning batafsil tahlili (qaysi savolga nima belgilaganingiz) bazada yo'q.\n"
            "<i>Yangi test ishlab ko'ring, barcha javoblar va izohlar to'liq chiqadi!</i>", 
            parse_mode="HTML"
        )
        return

    chunks = []
    current_chunk = (
        f"<b>📝 {test.get('title', 'Test').upper()} - TAHLIL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    for d in detailed:
        idx = d.get("question_index", 0)
        is_correct = d.get("is_correct", False)
        user_ans = d.get("user_answer", "Belgilanmagan")
        corr_ans = d.get("correct_answer", "Noma'lum")
        
        q_text = questions[idx].get("question", "Savol topilmadi") if idx < len(questions) else ""
        explanation = questions[idx].get("explanation", "Izoh kiritilmagan") if idx < len(questions) else "Izoh kiritilmagan"
        status = "✅ TO'G'RI" if is_correct else "❌ XATO"
        
        block = (
            f"<b>Savol {idx+1}:</b> {q_text}\n"
            f"Holat: {status}\n"
            f"👤 <b>Javobingiz:</b> <i>{user_ans}</i>\n"
        )
        if not is_correct:
            block += f"🎯 <b>To'g'ri javob:</b> <i>{corr_ans}</i>\n"
        block += f"💡 <b>Izoh:</b> <i>{explanation}</i>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if len(current_chunk) + len(block) > 4000:
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk += block
        
    if current_chunk: chunks.append(current_chunk)
    
    for chunk in chunks:
        await callback.message.answer(chunk, parse_mode="HTML", protect_content=True)
    

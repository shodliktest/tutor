"""
📚 TEST YECHISH VA TAHLIL HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Barcha 7 ta test turini (MCQ, MRQ, True/False, Fill, Match, Order, Essay) to'liq qo'llab-quvvatlaydi!
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

@router.message(F.text == "📚 Testlar")
async def tests_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await send_categories_menu(message)

@router.message(F.text, lambda msg: len(msg.text.strip()) == 6 or len(msg.text.strip()) > 10)
async def direct_code_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state: return 
    
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
    
    q_text = q.get("question", q.get("text", "Savol matni kiritilmagan"))
    question_text = f"<b>{q_text}</b>\n\n"
    
    options_text = ""
    builder = InlineKeyboardBuilder()
    
    user_answers = state_data.get("user_answers", {})
    current_answer = user_answers.get(str(current_index), "")
    
    q_type = q.get("type", "multiple_choice")
    letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    
    # 🔘 1. BIR JAVOBLI VA ROST/YOLG'ON (Oddiy tugmalar)
    if q_type in ["multiple_choice", "true_false", "multiple"] and "options" in q:
        for idx, opt in enumerate(q["options"]):
            letter = letters[idx] if idx < len(letters) else str(idx)
            text = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
                
            prefix = "✅ " if current_answer == f"{letter}" else ""
            options_text += f"{prefix}<b>{letter})</b> <i>{text}</i>\n"
            btn_text = f"✅ {letter}" if current_answer == f"{letter}" else letter
            builder.add(InlineKeyboardButton(text=btn_text, callback_data=f"ans_{letter}"))
        builder.adjust(2)

    # ☑️ 2. KO'P JAVOBLI (Belgilab, keyin tasdiqlash tugmasi bilan)
    elif q_type == "multi_select" and "options" in q:
        selected_letters = [x.strip() for x in current_answer.split(",")] if current_answer else []
        for idx, opt in enumerate(q["options"]):
            letter = letters[idx] if idx < len(letters) else str(idx)
            text = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
                
            prefix = "☑️ " if letter in selected_letters else "⬜️ "
            options_text += f"{prefix}<b>{letter})</b> <i>{text}</i>\n"
            btn_text = f"☑️ {letter}" if letter in selected_letters else letter
            builder.add(InlineKeyboardButton(text=btn_text, callback_data=f"ans_{letter}"))
            
        builder.adjust(2)
        builder.row(InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="submit_multi"))

    # 🔗 3. MOSLASHTIRISH VA TARTIBLASH (Matn orqali ketma-ketlik kiritiladi)
    elif q_type in ["matching", "ordering"]:
        if current_answer:
            options_text += f"✅ <b>Sizning ketma-ketligingiz:</b> <i>{current_answer}</i>\n\n"
        else:
            options_text += "✍️ <i>Moslashtiring yoki tartiblang va javobingizni pastdagi chatga yozib yuboring... (Masalan: 1A, 2B, 3C yoki 3, 1, 2)</i>\n\n"

    # 📝 4. OCHIQ VA BO'SH JOY (Matn kiritiladi)
    elif q_type in ["text_input", "fill_blank", "essay"]:
        if current_answer:
            options_text += f"✅ <b>Sizning javobingiz:</b> <i>{current_answer}</i>\n\n"
        else:
            options_text += "✍️ <i>Javobingizni pastdagi chatga yozib yuboring...</i>\n\n"
            
    else:
        options_text += "<i>Bu savol turiga javob berish formatlanmagan.</i>\n\n"

    full_text = header + question_text + options_text

    if show_exp:
        explanation = q.get("explanation", "Ushbu savol uchun izoh kiritilmagan.")
        full_text += f"\n━━━━━━━━━━━━━━━━━━━━━━\n💡 <b>Izoh:</b> <i>{explanation}</i>\n"

    exp_btn_text = "💡 Izoh rejimi: 🟢 YONIQ" if exp_mode else "💡 Izoh rejimi: 🔴 O'CHIK"
    builder.row(InlineKeyboardButton(text=exp_btn_text, callback_data="toggle_exp_mode"))

    nav_row = []
    if current_index > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data="nav_prev"))
    if current_index < len(questions) - 1:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data="nav_next"))
    else:
        nav_row.append(InlineKeyboardButton(text="🏁 Yakunlash", callback_data="nav_finish"))
    
    builder.row(*nav_row)
    builder.row(InlineKeyboardButton(text="❌ Testni to'xtatish", callback_data="cancel_test"))

    if edit and isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(full_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        obj = message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
        await obj.answer(full_text, reply_markup=builder.as_markup(), parse_mode="HTML")


# ==========================================================
# 3. AQLLI JAVOB BERISH LOGIKASI (TUGMA VA MATN)
# ==========================================================
@router.callback_query(F.data.startswith("ans_"), TestSolving.answering)
async def process_button_answer(callback: CallbackQuery, state: FSMContext):
    answer = callback.data.replace("ans_", "")
    state_data = await state.get_data()
    current_index = state_data.get("current_index", 0)
    questions = state_data.get("questions", [])
    q = questions[current_index]
    
    # Ko'p javobli test uchun "Tanlash va Olib tashlash" mantig'i
    if q.get("type") == "multi_select":
        user_answers = state_data.get("user_answers", {})
        current_ans = user_answers.get(str(current_index), "")
        ans_list = [x.strip() for x in current_ans.split(",") if x.strip()]
        
        if answer in ans_list:
            ans_list.remove(answer)
        else:
            ans_list.append(answer)
            
        user_answers[str(current_index)] = ",".join(sorted(ans_list))
        await state.update_data(user_answers=user_answers)
        await send_question(callback, state, edit=True)
        await callback.answer()
        return

    # Oddiy bir javobli test uchun
    await handle_user_answer(callback, answer, state)
    await callback.answer()

@router.callback_query(F.data == "submit_multi", TestSolving.answering)
async def process_multi_submit(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_index = state_data.get("current_index", 0)
    user_answers = state_data.get("user_answers", {})
    answer = user_answers.get(str(current_index), "Belgilanmagan")
    
    if not answer:
        return await callback.answer("⚠️ Iltimos, kamida bitta variantni tanlang!", show_alert=True)
        
    await handle_user_answer(callback, answer, state)
    await callback.answer()

@router.message(F.text, TestSolving.answering)
async def process_text_answer(message: Message, state: FSMContext):
    if message.text in ["📚 Testlar", "➕ Test Yaratish", "👤 Profil", "🏆 Reyting"]:
        return await message.answer("⚠️ Iltimos, avval testni yakunlang yoki '❌ Testni to'xtatish' tugmasini bosing.")
        
    state_data = await state.get_data()
    current_index = state_data.get("current_index", 0)
    q = state_data.get("questions", [])[current_index]
    
    if q.get("type") in ["multiple_choice", "multiple", "true_false", "multi_select"]:
        return await message.answer("👆 Iltimos, javob berish uchun yuqoridagi tugmalardan birini tanlang.")
        
    answer = message.text.strip()
    await handle_user_answer(message, answer, state, is_text=True)

async def handle_user_answer(event, answer, state: FSMContext, is_text=False):
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
            
    await send_question(event, state, edit=(not is_text))

@router.callback_query(F.data == "toggle_exp_mode", TestSolving.answering)
async def toggle_exp_mode_handler(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_mode = state_data.get("exp_mode", False)
    await state.update_data(exp_mode=not current_mode)
    await send_question(callback, state, edit=True)
    await callback.answer(f"Izoh rejimi {'yoqildi' if not current_mode else 'o\'chirildi'}!")

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
    await callback.message.answer("<b>❌ TEST TO'XTATILDI</b>\n━━━━━━━━━━━━━━━━━━━━━━\nSiz test ishlashni to'xtatdingiz. Natijalar saqlanmadi.", reply_markup=main_reply_keyboard(callback.from_user.id))
    await callback.answer()


# ==========================================================
# 4. YAKUNLASH VA MUKAMMAL BAHOLASH TIZIMI (BARCHA TURLAR UCHUN)
# ==========================================================
@router.callback_query(F.data == "nav_finish", TestSolving.answering)
async def finish_test_handler(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await callback.message.delete()
    await finish_test_process(callback.message, state, state_data)
    await callback.answer()

def _clean_str(text):
    """Matnlarni taqqoslash uchun ortiqcha belgilardan tozalash"""
    return str(text).lower().replace(" ", "").replace(",", "").replace("-", "").replace(".", "")

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
        q_type = q.get("type", "multiple_choice")
        c_ans = q.get("correct", "")
        
        is_correct = False
        correct_full_text = str(c_ans)
        
        if u_ans == "Belgilanmagan" and q_type != "essay":
            is_correct = False
            
        # 1. BIR JAVOBLI VA ROST/YOLG'ON
        elif q_type in ["multiple_choice", "true_false", "multiple"]:
            c_letter = c_ans.split(")")[0].strip() if isinstance(c_ans, str) and ")" in c_ans else str(c_ans)
            if isinstance(c_ans, int):
                c_letter = letters[c_ans] if c_ans < len(letters) else "?"
                correct_full_text = f"{c_letter}) {q.get('options', [])[c_ans]}" if c_ans < len(q.get('options', [])) else c_letter
                
            is_correct = (str(u_ans).lower() == c_letter.lower())
            
        # 2. KO'P JAVOBLI (A,B kabi keladi)
        elif q_type == "multi_select":
            u_set = set([x.strip().upper() for x in str(u_ans).split(",") if x.strip()])
            if isinstance(c_ans, list):
                c_set = set([x.split(")")[0].strip().upper() if ")" in x else x.strip().upper() for x in c_ans])
            else:
                c_set = set([x.strip().upper() for x in str(c_ans).split(",") if x.strip()])
                
            is_correct = (u_set == c_set)
            correct_full_text = ", ".join(c_set)
            
        # 3. OCHIQ SAVOL (Yozma)
        elif q_type in ["text_input", "fill_blank"]:
            accepted = [_clean_str(x) for x in q.get("accepted_answers", [])]
            is_correct = (_clean_str(u_ans) == _clean_str(c_ans)) or (_clean_str(u_ans) in accepted)
            
        # 4. MOSLASHTIRISH
        elif q_type == "matching":
            if isinstance(c_ans, dict):
                correct_full_text = " | ".join([f"{k} - {v}" for k,v in c_ans.items()])
                # Foydalanuvchi javobida hamma kalit so'zlar qatnashganini tekshirish
                is_correct = all([_clean_str(k) in _clean_str(u_ans) and _clean_str(v) in _clean_str(u_ans) for k,v in c_ans.items()])
            else:
                is_correct = (_clean_str(u_ans) == _clean_str(c_ans))
                
        # 5. TARTIBLASH
        elif q_type == "ordering":
            if isinstance(c_ans, list):
                correct_full_text = " ➔ ".join([str(x) for x in c_ans])
                is_correct = (_clean_str(u_ans) == "".join([_clean_str(x) for x in c_ans]))
            else:
                is_correct = (_clean_str(u_ans) == _clean_str(c_ans))
                
        # 6. ESSE (Erkin fikr)
        elif q_type == "essay":
            is_correct = True # Esse uchun ball berilaveradi, ustoz o'zi ko'rib oladi
            correct_full_text = "Erkin yozma javob (O'qituvchi baholaydi)"
            
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
    
    result_id = save_result(message.chat.id, test.get("test_id"), result_data)
    user = get_user(message.chat.id)
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
    
    await message.answer(text, reply_markup=result_keyboard(test.get("test_id"), result_id, passed), protect_content=True)
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
        block += f"💡 <b>Izoh:</b> <i>{explanation}</i>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if len(current_chunk) + len(block) > 4000:
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk += block
        
    if current_chunk: chunks.append(current_chunk)
    for chunk in chunks:
        await callback.message.answer(chunk, parse_mode="HTML", protect_content=True)

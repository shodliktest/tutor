"""
🎮 TEST ISHLASH HANDLER (AIOGRAM 3 - PRO VERSIYA)
Agar izoh bo'lmasa, avtomatik ravishda keyingi savolga o'tkazib yuboradigan
aqlli tushuntirish (explanation) mexanizmi bilan.
Hech narsa qisqartirilmadi.
"""
import time
import io
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from firebase.db import get_db, get_test, get_user_results, save_result, get_user
from utils.scoring import calculate_score, format_result_message, _check_answer
from utils.states import TestSolving
from keyboards.keyboards import (
    subjects_keyboard, tests_list_keyboard, test_info_keyboard,
    result_keyboard, multiple_choice_keyboard, true_false_keyboard,
    multi_select_keyboard, finish_test_keyboard, explanation_keyboard
)

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data.in_(["browse_all", "browse_subjects"]))
async def browse_subjects_handler(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("📚 <b>FANLAR RO'YXATI</b>\n\nQaysi fan bo'yicha test ishlashni xohlaysiz?", reply_markup=subjects_keyboard())

@router.callback_query(F.data.startswith("browse_subj_"))
async def browse_tests_handler(callback: CallbackQuery):
    await callback.answer()
    subject = callback.data.replace("browse_subj_", "")
    db = get_db()
    tests_ref = db.collection("tests").where("category", "==", subject).where("visibility", "==", "public").stream()
    tests = [t.to_dict() for t in tests_ref]
    if not tests:
        await callback.message.edit_text(f"📭 Hozircha <b>{subject}</b> fani bo'yicha ommaviy testlar yo'q.", reply_markup=subjects_keyboard())
        return
    user_results = get_user_results(callback.from_user.id)
    await callback.message.edit_text(f"📂 <b>{subject}</b> fanidan testlar:\nKerakli testni tanlang:", reply_markup=tests_list_keyboard(tests, user_results, subject))

@router.callback_query(F.data.startswith("view_test_"))
async def view_test_handler(callback: CallbackQuery):
    await callback.answer()
    test_id = callback.data.replace("view_test_", "")
    test = get_test(test_id)
    if not test:
        await callback.message.edit_text("❌ Test topilmadi yoki o'chirilgan.")
        return
    
    questions = test.get("questions", [])
    title = test.get("title", "Nomsiz")
    difficulty = test.get("difficulty", "Nomalum").title()
    time_limit = test.get("time_limit", 0)
    passing_score = test.get("passing_score", 60)
    max_attempts = test.get("max_attempts", 0)
    attempts_text = str(max_attempts) if max_attempts > 0 else "Cheklanmagan"
    
    text = (
        f"📝 <b>{title}</b>\n\n"
        f"📋 Savollar soni: <b>{len(questions)} ta</b>\n"
        f"📊 Qiyinlik darajasi: <b>{difficulty}</b>\n"
        f"⏱ Vaqt limiti: <b>{time_limit} daqiqa</b>\n"
        f"🎯 O'tish foizi: <b>{passing_score}%</b>\n"
        f"🔄 Ruxsat etilgan urinishlar: <b>{attempts_text}</b>\n\n"
        f"<i>Boshlashga tayyormisiz?</i>"
    )
    await callback.message.edit_text(text, reply_markup=test_info_keyboard(test_id))

@router.callback_query(F.data.startswith("start_test_"))
async def start_test_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    test_id = callback.data.replace("start_test_", "")
    test = get_test(test_id)
    if not test: return
    
    questions = test.get("questions", [])
    if not questions: return

    max_attempts = test.get("max_attempts", 0)
    if max_attempts > 0:
        user_results = get_user_results(callback.from_user.id)
        attempts_made = sum(1 for r in user_results if r.get("test_id") == test_id)
        if attempts_made >= max_attempts:
            await callback.message.answer("🚫 Siz bu testni ishlash limitini tugatgansiz.")
            return
        
    await state.update_data(test_id=test_id, test_data=test, questions=questions, current_index=0, user_answers={}, start_time=time.time())
    await callback.message.delete()
    await send_next_question(callback.message, state)

async def send_next_question(message: Message, state: FSMContext):
    data = await state.get_data()
    idx = data.get("current_index", 0)
    questions = data.get("questions", [])
    test_data = data.get("test_data", {})
    
    time_text = ""
    time_limit_min = test_data.get("time_limit", 0)
    if time_limit_min > 0:
        elapsed = int(time.time() - data.get("start_time", time.time()))
        rem_sec = (time_limit_min * 60) - elapsed
        if rem_sec <= 0:
            await message.answer("⏳ <b>Vaqtingiz tugadi!</b> Test avtomatik yakunlandi.")
            await finish_test_process(message, state, data)
            return
        m, s = divmod(rem_sec, 60)
        time_text = f"⏳ <b>Qolgan vaqt:</b> {m:02d}:{s:02d}\n\n"
    
    if idx >= len(questions):
        await finish_test_process(message, state, data)
        return
        
    q = questions[idx]
    q_type = q.get("type", "multiple_choice")
    
    text = f"📝 <b>{idx + 1}-savol ({len(questions)} dan):</b>\n{time_text}{q.get('question', '')}\n\n"
    keyboard = None
    
    if q_type == "multiple_choice":
        text += "\n".join(q.get("options", []))
        keyboard = multiple_choice_keyboard(q.get("options", []), idx)
        await state.set_state(TestSolving.answering)
    elif q_type == "true_false":
        keyboard = true_false_keyboard(idx)
        await state.set_state(TestSolving.answering)
    elif q_type == "multi_select":
        text += "\n".join(q.get("options", []))
        user_answers = data.get("user_answers", {})
        current_selected = user_answers.get(str(idx), [])
        keyboard = multi_select_keyboard(q.get("options", []), idx, current_selected)
        await state.set_state(TestSolving.answering)
    elif q_type == "matching":
        text += "<i>🔗 Iltimos, javoblaringizni quyidagi formatda xabar qilib yuboring:\nMasalan: 1-A, 2-C, 3-B</i>"
        keyboard = finish_test_keyboard()
        await state.set_state(TestSolving.text_answer)
    elif q_type == "ordering":
        text += "<i>🔢 Iltimos, to'g'ri tartibni vergul bilan ajratib yuboring:\nMasalan: 3, 1, 4, 2</i>"
        keyboard = finish_test_keyboard()
        await state.set_state(TestSolving.text_answer)
    elif q_type in ["text_input", "fill_blank"]:
        text += "<i>✍️ Javobingizni oddiy xabar ko'rinishida yozib yuboring.</i>"
        keyboard = finish_test_keyboard()
        await state.set_state(TestSolving.text_answer)

    msg = await message.answer(text, reply_markup=keyboard, protect_content=True)
    await state.update_data(last_msg_id=msg.message_id)


# ---------------------------------------------------------
# INTERAKTIV TUSHUNTIRISH YASOVCHI FUNKSIYA (AQLLI VERSIYA)
# ---------------------------------------------------------
async def show_explanation(message_obj, state: FSMContext, q_idx: int, user_ans, is_edit=True):
    state_data = await state.get_data()
    q = state_data["questions"][q_idx]
    
    explanation = q.get("explanation", "Izoh kiritilmagan.").strip()
    
    # 💡 AGAR IZOH BO'LMASA -> TO'G'RIDAN-TO'G'RI KEYINGI SAVOLGA O'TISH
    if explanation in ["Izoh kiritilmagan.", "", "Izoh yo'q", "Noma'lum"]:
        await state.update_data(current_index=q_idx + 1)
        if is_edit:
            try:
                await message_obj.delete()
            except: pass
        await send_next_question(message_obj, state)
        return

    # Agar izoh bo'lsa, uni ko'rsatish mantiqi:
    is_correct, _ = _check_answer(q, user_ans)
    status_emoji = "✅ <b>TO'G'RI JAVOB!</b>" if is_correct else "❌ <b>XATO JAVOB!</b>"
    
    corr_ans = q.get("correct", "Noma'lum")
    if isinstance(corr_ans, list): corr_ans = ", ".join(corr_ans)
    elif isinstance(corr_ans, dict): corr_ans = ", ".join([f"{k}-{v}" for k,v in corr_ans.items()])
    
    text = (
        f"{status_emoji}\n\n"
        f"👤 <b>Sizning javobingiz:</b> {user_ans}\n"
        f"🎯 <b>To'g'ri javob:</b> {corr_ans}\n\n"
        f"💡 <b>Tushuntirish:</b>\n{explanation}"
    )
    
    await state.update_data(current_index=q_idx + 1)
    
    if is_edit:
        await message_obj.edit_text(text, reply_markup=explanation_keyboard(q_idx))
    else:
        await message_obj.answer(text, reply_markup=explanation_keyboard(q_idx))
        
    await state.set_state(TestSolving.viewing_explanation)


@router.callback_query(TestSolving.answering)
async def handle_button_answer(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    state_data = await state.get_data()
    idx = state_data.get("current_index", 0)
    user_answers = state_data.get("user_answers", {})
    
    if data == "finish_test":
        await callback.message.delete()
        await finish_test_process(callback.message, state, state_data)
        return

    if data.startswith("msel_"):
        parts = data.split("_")
        q_idx = int(parts[1])
        ans = parts[2]
        current_ans = user_answers.get(str(q_idx), [])
        if ans in current_ans: current_ans.remove(ans)
        else: current_ans.append(ans)
        user_answers[str(q_idx)] = current_ans
        await state.update_data(user_answers=user_answers)
        
        q = state_data["questions"][q_idx]
        kb = multi_select_keyboard(q.get("options", []), q_idx, current_ans)
        await callback.message.edit_reply_markup(reply_markup=kb)
        return

    # Multi-select dagi 'Keyingi' tugmasi bosilganda ham tushuntirish ishlaydi
    if data.startswith("next_"):
        parts = data.split("_")
        q_idx = int(parts[1])
        final_ans = user_answers.get(str(q_idx), [])
        await show_explanation(callback.message, state, q_idx, final_ans, is_edit=True)
        return

    if data.startswith("ans_"):
        parts = data.split("_")
        q_idx = int(parts[1])
        ans = parts[2]
        user_answers[str(q_idx)] = ans
        await state.update_data(user_answers=user_answers)
        
        await show_explanation(callback.message, state, q_idx, ans, is_edit=True)

@router.message(F.text, TestSolving.text_answer)
async def handle_text_answer(message: Message, state: FSMContext):
    state_data = await state.get_data()
    idx = state_data.get("current_index", 0)
    user_answers = state_data.get("user_answers", {})
    
    ans = message.text.strip()
    user_answers[str(idx)] = ans
    await state.update_data(user_answers=user_answers)
    
    last_msg_id = state_data.get("last_msg_id")
    try:
        await message.delete()
        if last_msg_id: await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
    except: pass
    
    await show_explanation(message, state, idx, ans, is_edit=False)

@router.callback_query(TestSolving.text_answer, F.data == "finish_test")
async def handle_finish_from_text_state(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await callback.message.delete()
    await finish_test_process(callback.message, state, state_data)

# ---------------------------------------------------------
# 'TUSHUNDIM' TUGMASINI USHLOVCHI HANDLER
# ---------------------------------------------------------
@router.callback_query(TestSolving.viewing_explanation, F.data.startswith("go_next_"))
async def go_next_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await send_next_question(callback.message, state)

@router.callback_query(TestSolving.viewing_explanation, F.data == "finish_test")
async def finish_from_explanation(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await callback.message.delete()
    await finish_test_process(callback.message, state, state_data)


# ==========================================================
# 5. NATIJANI HISOBLASH
# ==========================================================
async def finish_test_process(message: Message, state: FSMContext, state_data: dict):
    test = state_data.get("test_data", {})
    questions = state_data.get("questions", [])
    user_answers = state_data.get("user_answers", {})
    start_time = state_data.get("start_time", time.time())
    
    time_spent = int(time.time() - start_time)
    result = calculate_score(questions, user_answers)
    result["time_spent"] = time_spent
    result["passing_score"] = test.get("passing_score", 60)
    
    user_id = message.chat.id
    result_id = save_result(user_id, test.get("test_id"), result)
    user = get_user(user_id)
    user_name = user.get("name", "Foydalanuvchi") if user else "Foydalanuvchi"
    
    result_text = format_result_message(result, test, user_name)
    kb = result_keyboard(test.get("test_id"), result_id, result.get("passed", False))
    
    await message.answer(result_text, reply_markup=kb)
    await state.clear()


# ==========================================================
# 6. TAHLIL VA IZOHLAR (TXT FAYL)
# ==========================================================
@router.callback_query(F.data.startswith("analysis_"))
async def analysis_handler(callback: CallbackQuery):
    await callback.answer("⏳ Tahlil fayli tayyorlanmoqda...")
    result_id = callback.data.replace("analysis_", "")
    
    db = get_db()
    res_doc = db.collection("results").document(result_id).get()
    if not res_doc.exists:
        await callback.message.answer("❌ Natija topilmadi.")
        return
        
    res_data = res_doc.to_dict()
    detailed = res_data.get("detailed_results", [])
    test_id = res_data.get("test_id")
    test = get_test(test_id)
    questions = test.get("questions", []) if test else []
    
    title = test.get("title", "Nomsiz Test") if test else "Test"
    text = f"📝 {title.upper()} - TAHLIL VA IZOHLAR\n" + "="*40 + "\n\n"
    
    for d in detailed:
        idx = d.get("question_index", 0)
        is_correct = d.get("is_correct", False)
        user_ans = d.get("user_answer", "Belgilanmagan")
        corr_ans = d.get("correct_answer", "Noma'lum")
        q_text = questions[idx].get("question", "Savol topilmadi") if idx < len(questions) else ""
        explanation = questions[idx].get("explanation", "Izoh kiritilmagan.") if idx < len(questions) else "Izoh yo'q"
        status = "✅ TO'G'RI" if is_correct else "❌ XATO"
        
        text += f"Savol {idx+1}: {q_text}\nHolat: {status}\nSizning javobingiz: {user_ans}\n"
        if not is_correct:
            if isinstance(corr_ans, list): corr_ans = ", ".join(corr_ans)
            elif isinstance(corr_ans, dict): corr_ans = ", ".join([f"{k}-{v}" for k,v in corr_ans.items()])
            text += f"To'g'ri javob: {corr_ans}\n"
        text += f"Izoh: {explanation}\n" + "-"*40 + "\n\n"
        
    file_obj = io.BytesIO(text.encode('utf-8'))
    doc = BufferedInputFile(file_obj.getvalue(), filename=f"Tahlil_{result_id}.txt")
    await callback.message.answer_document(document=doc, caption="📊 <b>Test bo'yicha batafsil tahlil.</b>", parse_mode="HTML")

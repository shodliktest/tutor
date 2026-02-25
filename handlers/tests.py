"""
🎮 TEST ISHLASH HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
1. protect_content=True orqali xavfsizlik (anti-cheat) qo'shildi.
2. Tahlil chatning o'zida yuboriladi.
3. Izohlarni o'chirish/yoqish tizimi ulandi.
"""
import time
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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

# ==========================================================
# 1. TESTLARNI QIDIRISH VA KO'RISH
# ==========================================================
@router.message(F.text == "📚 Testlar")
async def browse_subjects_handler_msg(message: Message):
    await message.answer("📚 <b>FANLAR RO'YXATI</b>\n\nQaysi fan bo'yicha test ishlashni xohlaysiz?", reply_markup=subjects_keyboard())

@router.callback_query(F.data == "browse_all")
async def browse_subjects_handler_cb(callback: CallbackQuery):
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
        await callback.message.edit_text("❌ Test topilmadi.")
        return
    
    questions = test.get("questions", [])
    text = (
        f"📝 <b>{test.get('title', 'Nomsiz')}</b>\n\n"
        f"📋 Savollar soni: <b>{len(questions)} ta</b>\n"
        f"📊 Qiyinlik darajasi: <b>{test.get('difficulty', 'Nomalum').title()}</b>\n"
        f"⏱ Vaqt limiti: <b>{test.get('time_limit', 0)} daqiqa</b>\n"
        f"🎯 O'tish foizi: <b>{test.get('passing_score', 60)}%</b>\n"
        f"🔄 Ruxsat etilgan urinishlar: <b>{test.get('max_attempts', 0) or 'Cheklanmagan'}</b>\n\n"
        f"<i>Boshlashga tayyormisiz?</i>"
    )
    await callback.message.edit_text(text, reply_markup=test_info_keyboard(test_id))


# ==========================================================
# 2. TESTNI BOSHLASH VA JAVOBLAR
# ==========================================================
@router.callback_query(F.data.startswith("start_test_"))
async def start_test_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    test_id = callback.data.replace("start_test_", "")
    test = get_test(test_id)
    if not test or not test.get("questions", []): return

    max_attempts = test.get("max_attempts", 0)
    if max_attempts > 0:
        user_results = get_user_results(callback.from_user.id)
        if sum(1 for r in user_results if r.get("test_id") == test_id) >= max_attempts:
            return await callback.message.answer("🚫 Siz bu testni ishlash limitini tugatgansiz.")
        
    # Xotiraga show_explanations=True (Izohlar yoniq) deb saqlaymiz
    await state.update_data(
        test_id=test_id, test_data=test, questions=test.get("questions", []), 
        current_index=0, user_answers={}, start_time=time.time(), show_explanations=True
    )
    await callback.message.delete()
    await send_next_question(callback.message, state)

async def send_next_question(message: Message, state: FSMContext):
    data = await state.get_data()
    idx = data.get("current_index", 0)
    questions = data.get("questions", [])
    test_data = data.get("test_data", {})
    show_exp = data.get("show_explanations", True) # Izohlar yoniqmi tekshirish
    
    time_text = ""
    time_limit_min = test_data.get("time_limit", 0)
    if time_limit_min > 0:
        rem_sec = (time_limit_min * 60) - int(time.time() - data.get("start_time", time.time()))
        if rem_sec <= 0:
            await message.answer("⏳ <b>Vaqtingiz tugadi!</b> Test avtomatik yakunlandi.", protect_content=True)
            return await finish_test_process(message, state, data)
        m, s = divmod(rem_sec, 60)
        time_text = f"⏳ <b>Qolgan vaqt:</b> {m:02d}:{s:02d}\n\n"
    
    if idx >= len(questions):
        return await finish_test_process(message, state, data)
        
    q = questions[idx]
    q_type = q.get("type", "multiple_choice")
    
    text = f"📝 <b>{idx + 1}-savol ({len(questions)} dan):</b>\n{time_text}{q.get('question', '')}\n\n"
    keyboard = None
    
    # Klaviaturalarni show_exp holati bilan chaqiramiz
    if q_type == "multiple_choice":
        text += "\n".join(q.get("options", []))
        keyboard = multiple_choice_keyboard(q.get("options", []), idx, show_exp)
        await state.set_state(TestSolving.answering)
    elif q_type == "true_false":
        keyboard = true_false_keyboard(idx, show_exp)
        await state.set_state(TestSolving.answering)
    elif q_type == "multi_select":
        text += "\n".join(q.get("options", []))
        user_answers = data.get("user_answers", {})
        keyboard = multi_select_keyboard(q.get("options", []), idx, user_answers.get(str(idx), []), show_exp)
        await state.set_state(TestSolving.answering)
    elif q_type in ["text_input", "fill_blank", "matching", "ordering"]:
        text += "<i>✍️ Javobingizni xabar orqali yozing.</i>"
        keyboard = finish_test_keyboard(idx, show_exp)
        await state.set_state(TestSolving.text_answer)

    # 🛡️ PROTECT_CONTENT=TRUE (Foydalanuvchi nusxa ololmaydi)
    msg = await message.answer(text, reply_markup=keyboard, protect_content=True)
    await state.update_data(last_msg_id=msg.message_id)

# 🔄 IZOHLARNI O'CHIRISH/YOQISH TUGMASI USHLAGICHI
@router.callback_query(TestSolving.answering, F.data.startswith("toggle_exp_"))
@router.callback_query(TestSolving.text_answer, F.data.startswith("toggle_exp_"))
async def toggle_explanation_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_status = data.get("show_explanations", True)
    new_status = not current_status
    await state.update_data(show_explanations=new_status)
    
    status_text = "Izohlar YOQILDI 🔊" if new_status else "Izohlar O'CHIRILDI 🔇"
    await callback.answer(status_text)
    
    # Ekranni qayta chizib yuboramizki tugma yozuvi o'zgarsin
    try:
        await callback.message.delete()
    except: pass
    await send_next_question(callback.message, state)


# ==========================================================
# 3. JAVOBLAR VA IZOHLAR
# ==========================================================
async def handle_answer_logic(message_obj, state: FSMContext, q_idx: int, ans, is_edit=True):
    data = await state.get_data()
    user_answers = data.get("user_answers", {})
    user_answers[str(q_idx)] = ans
    await state.update_data(user_answers=user_answers)
    
    q = data["questions"][q_idx]
    explanation = q.get("explanation", "Izoh kiritilmagan.").strip()
    show_exp = data.get("show_explanations", True)
    
    # Agar izoh o'chirilgan bo'lsa yoki izoh yo'q bo'lsa -> To'g'ridan to'g'ri keyingisiga
    if not show_exp or explanation in ["Izoh kiritilmagan.", "", "Izoh yo'q", "Noma'lum"]:
        await state.update_data(current_index=q_idx + 1)
        if is_edit:
            try: await message_obj.delete()
            except: pass
        return await send_next_question(message_obj, state)

    # Izoh ko'rsatish
    is_correct, _ = _check_answer(q, ans)
    status_emoji = "✅ <b>TO'G'RI JAVOB!</b>" if is_correct else "❌ <b>XATO JAVOB!</b>"
    corr_ans = q.get("correct", "Noma'lum")
    if isinstance(corr_ans, list): corr_ans = ", ".join(corr_ans)
    elif isinstance(corr_ans, dict): corr_ans = ", ".join([f"{k}-{v}" for k,v in corr_ans.items()])
    
    text = (f"{status_emoji}\n\n👤 <b>Sizning javobingiz:</b> {ans}\n🎯 <b>To'g'ri javob:</b> {corr_ans}\n\n💡 <b>Tushuntirish:</b>\n{explanation}")
    await state.update_data(current_index=q_idx + 1)
    
    # 🛡️ PROTECT_CONTENT=TRUE Izoh oynasi uchun ham
    if is_edit:
        try: await message_obj.delete()
        except: pass
        await message_obj.answer(text, reply_markup=explanation_keyboard(q_idx), protect_content=True)
    else:
        await message_obj.answer(text, reply_markup=explanation_keyboard(q_idx), protect_content=True)
    await state.set_state(TestSolving.viewing_explanation)

@router.callback_query(TestSolving.answering)
async def handle_button_answer(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    state_data = await state.get_data()
    idx = state_data.get("current_index", 0)
    
    if data == "finish_test":
        await callback.message.delete()
        return await finish_test_process(callback.message, state, state_data)

    if data.startswith("msel_"):
        parts = data.split("_")
        ans = parts[2]
        user_answers = state_data.get("user_answers", {})
        current_ans = user_answers.get(str(idx), [])
        if ans in current_ans: current_ans.remove(ans)
        else: current_ans.append(ans)
        user_answers[str(idx)] = current_ans
        await state.update_data(user_answers=user_answers)
        
        show_exp = state_data.get("show_explanations", True)
        kb = multi_select_keyboard(state_data["questions"][idx].get("options", []), idx, current_ans, show_exp)
        return await callback.message.edit_reply_markup(reply_markup=kb)

    if data.startswith("next_"):
        final_ans = state_data.get("user_answers", {}).get(str(idx), [])
        return await handle_answer_logic(callback.message, state, idx, final_ans, is_edit=True)

    if data.startswith("ans_"):
        ans = data.split("_")[2]
        return await handle_answer_logic(callback.message, state, idx, ans, is_edit=True)

@router.message(F.text, TestSolving.text_answer)
async def handle_text_answer(message: Message, state: FSMContext):
    state_data = await state.get_data()
    idx = state_data.get("current_index", 0)
    
    last_msg_id = state_data.get("last_msg_id")
    try:
        await message.delete()
        if last_msg_id: await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
    except: pass
    
    await handle_answer_logic(message, state, idx, message.text.strip(), is_edit=False)

@router.callback_query(TestSolving.text_answer, F.data == "finish_test")
@router.callback_query(TestSolving.viewing_explanation, F.data == "finish_test")
async def finish_any_state(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await callback.message.delete()
    await finish_test_process(callback.message, state, state_data)

@router.callback_query(TestSolving.viewing_explanation, F.data.startswith("go_next_"))
async def go_next_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await send_next_question(callback.message, state)


# ==========================================================
# 4. NATIJANI HISOBLASH VA CHATDA TAHLIL (YANGI)
# ==========================================================
async def finish_test_process(message: Message, state: FSMContext, state_data: dict):
    test = state_data.get("test_data", {})
    questions = state_data.get("questions", [])
    user_answers = state_data.get("user_answers", {})
    start_time = state_data.get("start_time", time.time())
    
    result = calculate_score(questions, user_answers)
    result["time_spent"] = int(time.time() - start_time)
    result["passing_score"] = test.get("passing_score", 60)
    
    result_id = save_result(message.chat.id, test.get("test_id"), result)
    user = get_user(message.chat.id)
    user_name = user.get("name", "Foydalanuvchi") if user else "Foydalanuvchi"
    
    # 🛡️ PROTECT_CONTENT=TRUE
    result_text = format_result_message(result, test, user_name)
    kb = result_keyboard(test.get("test_id"), result_id, result.get("passed", False))
    await message.answer(result_text, reply_markup=kb, protect_content=True)
    await state.clear()

@router.callback_query(F.data.startswith("analysis_"))
async def analysis_handler(callback: CallbackQuery):
    await callback.answer("⏳ Chatda tahlil tayyorlanmoqda...")
    result_id = callback.data.replace("analysis_", "")
    res_doc = get_db().collection("results").document(result_id).get()
    
    if not res_doc.exists: 
        return await callback.message.answer("❌ Natija topilmadi.")
        
    res_data = res_doc.to_dict()
    detailed = res_data.get("detailed_results", [])
    test = get_test(res_data.get("test_id"))
    questions = test.get("questions", []) if test else []
    
    # 🛡️ YANGILIK: Agar eski test bo'lsa (batafsil javoblar saqlanmagan bo'lsa)
    if not detailed:
        await callback.message.answer(
            "⚠️ <b>Kechirasiz!</b>\n\n"
            "Bu eski test natijasi bo'lgani uchun, uning batafsil tahlili (qaysi savolga nima belgilaganingiz) bazada saqlanmagan.\n\n"
            "<i>Yangi test ishlab ko'ring, barcha javoblar va izohlar to'liq chiqadi!</i>", 
            parse_mode="HTML"
        )
        return

    # TXT fayl o'rniga chatga bo'lib-bo'lib yuborish
    chunks = []
    current_chunk = f"📝 <b>{test.get('title', 'Test').upper()} - TAHLIL</b>\n{'━'*20}\n\n"
    
    for d in detailed:
        idx = d.get("question_index", 0)
        is_correct = d.get("is_correct", False)
        user_ans = d.get("user_answer", "Belgilanmagan")
        corr_ans = d.get("correct_answer", "Noma'lum")
        
        q_text = questions[idx].get("question", "Savol topilmadi") if idx < len(questions) else ""
        explanation = questions[idx].get("explanation", "Izoh yo'q") if idx < len(questions) else "Izoh yo'q"
        status = "✅ TO'G'RI" if is_correct else "❌ XATO"
        
        block = f"<b>Savol {idx+1}:</b> {q_text}\n<b>Holat:</b> {status}\n👤 <b>Javobingiz:</b> {user_ans}\n"
        if not is_correct:
            if isinstance(corr_ans, list): corr_ans = ", ".join(corr_ans)
            elif isinstance(corr_ans, dict): corr_ans = ", ".join([f"{k}-{v}" for k,v in corr_ans.items()])
            block += f"🎯 <b>To'g'ri javob:</b> {corr_ans}\n"
        block += f"💡 <b>Izoh:</b> {explanation}\n{'━'*20}\n\n"
        
        # Telegram 4096 belgidan oshsa xato beradi
        if len(current_chunk) + len(block) > 4000:
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk += block
        
    if current_chunk: chunks.append(current_chunk)
    
    # 🛡️ PROTECT_CONTENT=TRUE bilan tahlilni chatga yuborish
    for chunk in chunks:
        await callback.message.answer(chunk, parse_mode="HTML", protect_content=True)
            

"""
🎮 TEST ISHLASH HANDLER (AIOGRAM 3 - TO'LIQ VERSIYA)
Barcha 7 xil test turi, Anti-cheat, Vaqt va Urinishlar nazorati bilan.
"""
import time
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from firebase.db import get_db, get_test, get_user_results, save_result, get_user
from utils.scoring import calculate_score, format_result_message
from utils.states import TestSolving
from keyboards.keyboards import (
    subjects_keyboard, tests_list_keyboard, test_info_keyboard,
    result_keyboard, multiple_choice_keyboard, true_false_keyboard,
    multi_select_keyboard, finish_test_keyboard
)
from utils.certificate_gen import generate_pdf_certificate

logger = logging.getLogger(__name__)
router = Router()

# ==========================================================
# 1. TESTLARNI QIDIRISH VA KO'RISH
# ==========================================================

@router.callback_query(F.data.in_(["browse_all", "browse_subjects"]))
async def browse_subjects_handler(callback: CallbackQuery):
    await callback.answer()
    text = "📚 <b>FANLAR RO'YXATI</b>\n\nQaysi fan bo'yicha test ishlashni xohlaysiz?"
    await callback.message.edit_text(text, reply_markup=subjects_keyboard())

@router.callback_query(F.data.startswith("browse_subj_"))
async def browse_tests_handler(callback: CallbackQuery):
    await callback.answer()
    subject = callback.data.replace("browse_subj_", "")
    
    db = get_db()
    # Bazadan ommaviy testlarni tortish
    tests_ref = db.collection("tests").where("category", "==", subject).where("visibility", "==", "public").stream()
    tests = [t.to_dict() for t in tests_ref]
    
    if not tests:
        await callback.message.edit_text(
            f"📭 Hozircha <b>{subject}</b> fani bo'yicha ommaviy testlar yo'q.",
            reply_markup=subjects_keyboard()
        )
        return
        
    user_results = get_user_results(callback.from_user.id)
    text = f"📂 <b>{subject}</b> fanidan testlar:\nKerakli testni tanlang:"
    
    await callback.message.edit_text(text, reply_markup=tests_list_keyboard(tests, user_results, subject))

@router.callback_query(F.data.startswith("view_test_"))
async def view_test_handler(callback: CallbackQuery):
    await callback.answer()
    test_id = callback.data.replace("view_test_", "")
    test = get_test(test_id)
    
    if not test:
        await callback.message.edit_text("❌ Test topilmadi yoki o'chirilgan.")
        return
        
    questions = test.get("questions", [])
    
    # Python Syntax xato bermasligi uchun ma'lumotlarni alohida xavfsiz o'zgaruvchilarga olamiz
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


# ==========================================================
# 2. TESTNI BOSHLASH VA URINISHLARNI TEKSHIRISH
# ==========================================================

@router.callback_query(F.data.startswith("start_test_"))
async def start_test_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    test_id = callback.data.replace("start_test_", "")
    test = get_test(test_id)
    
    if not test:
        await callback.message.answer("❌ Test topilmadi.")
        return
        
    questions = test.get("questions", [])
    if not questions:
        await callback.message.answer("❌ Bu testda savollar yo'q.")
        return

    # 🛡️ Urinishlar limitini tekshirish
    max_attempts = test.get("max_attempts", 0)
    if max_attempts > 0:
        user_results = get_user_results(callback.from_user.id)
        attempts_made = sum(1 for r in user_results if r.get("test_id") == test_id)
        if attempts_made >= max_attempts:
            await callback.message.answer(
                f"🚫 Siz bu testni ishlash limitini tugatgansiz.\n"
                f"(Ruxsat etilgan: {max_attempts} marta, Siz ishladingiz: {attempts_made} marta)"
            )
            return
        
    # Xotirani tayyorlash
    await state.update_data(
        test_id=test_id,
        test_data=test,
        questions=questions,
        current_index=0,
        user_answers={},
        start_time=time.time()
    )
    
    await callback.message.delete()
    await send_next_question(callback.message, state)


# ==========================================================
# 3. SAVOLLARNI YUBORISH (BARCHA 7 XIL TUR UCHUN)
# ==========================================================

async def send_next_question(message: Message, state: FSMContext):
    data = await state.get_data()
    idx = data.get("current_index", 0)
    questions = data.get("questions", [])
    test_data = data.get("test_data", {})
    
    # ⏱ Vaqtni tekshirish
    time_limit_min = test_data.get("time_limit", 0)
    if time_limit_min > 0:
        elapsed = time.time() - data.get("start_time", time.time())
        if elapsed > (time_limit_min * 60):
            await message.answer("⏳ <b>Vaqtingiz tugadi!</b> Test avtomatik yakunlandi.")
            await finish_test_process(message, state, data)
            return
    
    # Savollar tugasa
    if idx >= len(questions):
        await finish_test_process(message, state, data)
        return
        
    q = questions[idx]
    q_type = q.get("type", "multiple_choice")
    
    # Sarlavha
    text = f"📝 <b>{idx + 1}-savol ({len(questions)} dan):</b>\n\n{q.get('question', '')}\n\n"
    
    keyboard = None
    
    # 🔘 TURLARGA QARAB MANTIQ
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

    # 🛡️ ANTI-CHEAT: protect_content=True
    msg = await message.answer(text, reply_markup=keyboard, protect_content=True)
    await state.update_data(last_msg_id=msg.message_id)


# ==========================================================
# 4. JAVOBLARNI QABUL QILISH (TUGMALAR ORQALI)
# ==========================================================

@router.callback_query(TestSolving.answering)
async def handle_button_answer(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    state_data = await state.get_data()
    idx = state_data.get("current_index", 0)
    user_answers = state_data.get("user_answers", {})
    
    # "Testni yakunlash" bosilsa
    if data == "finish_test":
        await callback.message.delete()
        await finish_test_process(callback.message, state, state_data)
        return

    # Ko'p javobli (Multi-select) belgilash
    if data.startswith("msel_"):
        parts = data.split("_")
        q_idx = int(parts[1])
        ans = parts[2]
        
        current_ans = user_answers.get(str(q_idx), [])
        if ans in current_ans:
            current_ans.remove(ans)
        else:
            current_ans.append(ans)
            
        user_answers[str(q_idx)] = current_ans
        await state.update_data(user_answers=user_answers)
        
        q = state_data["questions"][q_idx]
        kb = multi_select_keyboard(q.get("options", []), q_idx, current_ans)
        await callback.message.edit_reply_markup(reply_markup=kb)
        return

    # "Keyingi" tugmasi (Multi-select uchun)
    if data.startswith("next_"):
        await callback.message.delete()
        await state.update_data(current_index=idx + 1)
        await send_next_question(callback.message, state)
        return

    # Oddiy A, B, C, D yoki Ha/Yo'q javobi
    if data.startswith("ans_"):
        parts = data.split("_")
        q_idx = int(parts[1])
        ans = parts[2]
        
        user_answers[str(q_idx)] = ans
        await state.update_data(user_answers=user_answers, current_index=idx + 1)
        
        await callback.message.delete()
        await send_next_question(callback.message, state)


# ==========================================================
# 5. YOZMA JAVOBLARNI QABUL QILISH (TEXT INPUT)
# ==========================================================

@router.message(F.text, TestSolving.text_answer)
async def handle_text_answer(message: Message, state: FSMContext):
    """Yozma (Fill blank, Matching, Ordering, Text Input) javoblarni tekshirish"""
    state_data = await state.get_data()
    idx = state_data.get("current_index", 0)
    user_answers = state_data.get("user_answers", {})
    
    # Kiritilgan matnni saqlash
    user_answers[str(idx)] = message.text.strip()
    await state.update_data(user_answers=user_answers, current_index=idx + 1)
    
    # Oldingi savol xabarini va foydalanuvchi yozgan xabarni o'chirish (Tozalik)
    last_msg_id = state_data.get("last_msg_id")
    try:
        await message.delete()
        if last_msg_id:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
    except: pass
    
    await send_next_question(message, state)

# Shuningdek, text qabul qilayotganda tugma orqali testni yakunlasa ham ushlash uchun:
@router.callback_query(TestSolving.text_answer, F.data == "finish_test")
async def handle_finish_from_text_state(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await callback.message.delete()
    await finish_test_process(callback.message, state, state_data)


# ==========================================================
# 6. NATIJANI HISOBLASH VA SERTIFIKAT YUBORISH
# ==========================================================

async def finish_test_process(message: Message, state: FSMContext, state_data: dict):
    """Testni yakunlash, tekshirish, bazaga saqlash va sertifikat berish"""
    test = state_data.get("test_data", {})
    questions = state_data.get("questions", [])
    user_answers = state_data.get("user_answers", {})
    start_time = state_data.get("start_time", time.time())
    
    time_spent = int(time.time() - start_time)
    
    # utils/scoring.py dagi maxsus logikadan foydalanish
    result = calculate_score(questions, user_answers)
    result["time_spent"] = time_spent
    result["passing_score"] = test.get("passing_score", 60)
    
    # Bazaga saqlash
    user_id = message.chat.id
    result_id = save_result(user_id, test.get("test_id"), result)
    
    user = get_user(user_id)
    user_name = user.get("name", "Foydalanuvchi") if user else "Foydalanuvchi"
    
    # Xabarni formatlash
    result_text = format_result_message(result, test, user_name)
    kb = result_keyboard(test.get("test_id"), result_id, result.get("passed", False))
    
    await message.answer(result_text, reply_markup=kb)
    
    # 🎓 SERTIFIKAT: Agar o'tish foizidan o'tgan bo'lsa
    if result.get("passed", False):
        try:
            cert_file = generate_pdf_certificate(user_name, test.get("title"), result["percentage"])
            input_file = BufferedInputFile(cert_file.read(), filename=f"Sertifikat_{user_name}.pdf")
            await message.answer_document(
                document=input_file,
                caption="🎉 <b>Muvaffaqiyatli o'tdingiz!</b>\nBu sizning yutug'ingizni tasdiqlovchi rasmiy sertifikat.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Sertifikat yaratishda xato: {e}")
            
    await state.clear()

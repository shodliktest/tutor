"""
🎮 TEST ISHLASH HANDLER
Foydalanuvchi testni ishlashi uchun barcha logika
"""
import time
import random
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from firebase.db import (
    get_test, get_tests_by_subject, get_all_tests,
    save_result, get_attempt_count, get_user
)
from utils.scoring import calculate_score, format_result_message
from keyboards.keyboards import (
    multiple_choice_keyboard, true_false_keyboard,
    multi_select_keyboard, tests_list_keyboard,
    test_info_keyboard, subjects_keyboard, result_keyboard,
    finish_test_keyboard
)
from utils.states import ANSWERING, TEXT_ANSWER
from config import MAX_ATTEMPTS

logger = logging.getLogger(__name__)


async def browse_tests_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Testlarni ko'rish"""
    query = update.callback_query
    if query:
        await query.answer()
        data = query.data
        
        if data == "browse_all" or data == "browse_subjects":
            # Fanlar ro'yxati
            text = "📚 <b>FANLAR RO'YXATI</b>\n\nQaysi fan bo'yicha test ishlashni xohlaysiz?"
            await query.message.edit_text(text, reply_markup=subjects_keyboard(), parse_mode="HTML")
            
        elif data.startswith("browse_subj_"):
            subject = data.replace("browse_subj_", "")
            tests = get_tests_by_subject(subject)
            
            if not tests:
                await query.message.edit_text(
                    f"📭 <b>{subject}</b> bo'yicha hali test yo'q.\n\nBirinchi bo'lib test yarating! 🚀",
                    reply_markup=subjects_keyboard(),
                    parse_mode="HTML"
                )
                return
            
            text = f"📚 <b>{subject}</b> bo'yicha testlar\n\n{len(tests)} ta test topildi:"
            await query.message.edit_text(
                text,
                reply_markup=tests_list_keyboard(tests, subject=subject),
                parse_mode="HTML"
            )
        
        elif data.startswith("test_info_"):
            test_id = data.replace("test_info_", "")
            await show_test_info(update, context, test_id)


async def show_test_info(update: Update, context: ContextTypes.DEFAULT_TYPE, test_id: str):
    """Test ma'lumotlarini ko'rsatish"""
    query = update.callback_query
    
    test = get_test(test_id)
    if not test:
        msg = "❌ Test topilmadi yoki o'chirilgan."
        if query:
            await query.message.edit_text(msg)
        else:
            await update.message.reply_text(msg)
        return
    
    user_id = (query.from_user if query else update.effective_user).id
    attempts_used = get_attempt_count(user_id, test_id)
    max_attempts = test.get("max_attempts", MAX_ATTEMPTS)
    attempts_left = max(0, max_attempts - attempts_used)
    is_creator = test.get("creator_id") == user_id
    
    difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴", "expert": "⚡"}.get(test.get("difficulty"), "⚪")
    type_names = {
        "multiple_choice": "🔘 Bir javobli",
        "multi_select": "☑️ Ko'p javobli",
        "true_false": "✅ Ha/Yo'q",
        "text_input": "✍️ Yozma javob",
        "matching": "🔗 Moslashtirish",
        "ordering": "🔢 Tartiblash",
        "fill_blank": "📝 Bo'sh joyni to'ldirish"
    }
    
    text = f"""
📝 <b>{test.get('title', 'Test')}</b>

📖 {test.get('description', 'Tavsif yo\'q')}

━━━━━━━━━━━━━━━
📚 Fan: <b>{test.get('subject', 'Noma\'lum')}</b>
{difficulty_emoji} Qiyinlik: <b>{test.get('difficulty', 'medium').capitalize()}</b>
🎮 Tur: <b>{type_names.get(test.get('test_type', 'multiple_choice'), 'Test')}</b>
❓ Savollar: <b>{test.get('question_count', 0)} ta</b>
⏱ Vaqt chegarasi: <b>{test.get('time_limit', 30)} daqiqa</b>
🎯 O'tish balli: <b>{test.get('passing_score', 60)}%</b>
━━━━━━━━━━━━━━━
📊 Jami urinishlar: <b>{test.get('total_attempts', 0)}</b>
📈 O'rtacha natija: <b>{test.get('avg_score', 0):.1f}%</b>
🔄 Urinish huquqi: <b>{attempts_left}/{max_attempts}</b>
"""
    
    keyboard = test_info_keyboard(test_id, attempts_left, is_creator)
    
    if query:
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")


async def take_test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Testni boshlash"""
    query = update.callback_query
    await query.answer()
    
    test_id = query.data.replace("take_test_", "")
    user_id = query.from_user.id
    
    # Urinishlarni tekshirish
    test = get_test(test_id)
    if not test:
        await query.message.edit_text("❌ Test topilmadi!")
        return ConversationHandler.END
    
    attempts_used = get_attempt_count(user_id, test_id)
    max_attempts = test.get("max_attempts", MAX_ATTEMPTS)
    
    if attempts_used >= max_attempts:
        await query.message.edit_text(
            f"🚫 Siz bu testni {max_attempts} marta ishladingiz. Endi urinish huquqi yo'q.",
            reply_markup=test_info_keyboard(test_id, 0)
        )
        return ConversationHandler.END
    
    # Test ma'lumotlarini sessiyaga saqlash
    questions = test.get("questions", [])
    
    if test.get("shuffle_questions", True):
        random.shuffle(questions)
    
    context.user_data["current_test"] = {
        "test_id": test_id,
        "test": test,
        "questions": questions,
        "current_index": 0,
        "answers": {},
        "multi_select_temp": set(),
        "start_time": time.time(),
        "attempt_number": attempts_used + 1
    }
    
    # Birinchi savolni yuborish
    await _send_question(query.message, context, 0)
    return ANSWERING


async def _send_question(message, context: ContextTypes.DEFAULT_TYPE, idx: int):
    """Savolni yuborish"""
    test_data = context.user_data.get("current_test", {})
    questions = test_data.get("questions", [])
    
    if idx >= len(questions):
        # Test tugadi
        await _finish_test(message, context)
        return
    
    question = questions[idx]
    q_type = question.get("type", "multiple_choice")
    total = len(questions)
    
    # Progress bar
    filled = int((idx / total) * 10)
    progress = "█" * filled + "░" * (10 - filled)
    
    question_text = f"""
📊 {progress} {idx + 1}/{total}
⏱ <b>Savol {idx + 1}</b>

❓ {question.get('question', '')}
"""
    
    # Rasm bormi?
    if question.get("image_url"):
        await message.reply_photo(question["image_url"], caption=question_text, parse_mode="HTML")
    
    # Savol turiga qarab klaviatura
    if q_type == "multiple_choice":
        keyboard = multiple_choice_keyboard(question.get("options", []), idx)
        await message.reply_text(question_text, reply_markup=keyboard, parse_mode="HTML")
    
    elif q_type == "true_false":
        keyboard = true_false_keyboard(idx)
        await message.reply_text(question_text, reply_markup=keyboard, parse_mode="HTML")
    
    elif q_type == "multi_select":
        question_text += "\n💡 <i>Bir nechta javobni tanlashingiz mumkin</i>"
        keyboard = multi_select_keyboard(question.get("options", []), idx)
        await message.reply_text(question_text, reply_markup=keyboard, parse_mode="HTML")
    
    elif q_type in ["text_input", "fill_blank"]:
        question_text += "\n✍️ <i>Javobingizni matn ko'rinishida yozing</i>"
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data=f"ans_{idx}_skip")
        ]])
        await message.reply_text(question_text, reply_markup=keyboard, parse_mode="HTML")
    
    elif q_type == "matching":
        left = question.get("left_items", [])
        right = question.get("right_items", [])
        
        pairs_text = "\n🔗 <b>Quyidagilarni moslang:</b>\n"
        pairs_text += "\n".join([f"  <b>{i+1}.</b> {item}" for i, item in enumerate(left)])
        pairs_text += "\n\n"
        pairs_text += "\n".join([f"  <b>{chr(65+i)}.</b> {item}" for i, item in enumerate(right)])
        
        question_text += pairs_text
        question_text += "\n\n✍️ <i>Javobni shu formatda yozing: 1-A, 2-C, 3-B, 4-D</i>"
        
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data=f"ans_{idx}_skip")
        ]])
        await message.reply_text(question_text, reply_markup=keyboard, parse_mode="HTML")
    
    elif q_type == "ordering":
        items = question.get("items", [])
        items_shuffled = items.copy()
        random.shuffle(items_shuffled)
        
        items_text = "\n🔢 <b>Quyidagilarni to'g'ri tartibga keltiring:</b>\n"
        items_text += "\n".join([f"  • {item}" for item in items_shuffled])
        question_text += items_text
        question_text += "\n\n✍️ <i>To'g'ri tartibda yozing (vergul bilan): Birinchi, Ikkinchi, ...</i>"
        
        # Shuffled items ni saqlash
        test_data["ordering_options"] = items_shuffled
        
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data=f"ans_{idx}_skip")
        ]])
        await message.reply_text(question_text, reply_markup=keyboard, parse_mode="HTML")


async def test_answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Javobni qayta ishlash"""
    test_data = context.user_data.get("current_test")
    if not test_data:
        return ConversationHandler.END
    
    idx = test_data["current_index"]
    questions = test_data["questions"]
    question = questions[idx]
    q_type = question.get("type", "multiple_choice")
    
    # Callback query (tugmalar) orqali javob
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data
        
        if data.startswith("multi_"):
            # Ko'p javobli: variantni tanlash/bekor qilish
            _, q_idx, opt_idx = data.split("_")
            opt_idx = int(opt_idx)
            
            selected = test_data.get("multi_select_temp", set())
            if opt_idx in selected:
                selected.remove(opt_idx)
            else:
                selected.add(opt_idx)
            test_data["multi_select_temp"] = selected
            
            # Klaviaturani yangilash
            keyboard = multi_select_keyboard(question.get("options", []), idx, selected)
            await query.message.edit_reply_markup(keyboard)
            return ANSWERING
        
        elif data.startswith("ans_"):
            parts = data.split("_")
            q_idx = int(parts[1])
            answer = parts[2]
            
            if answer == "skip":
                test_data["answers"][str(idx)] = None
            elif answer == "confirm":
                # Ko'p javobli tasdiqlash
                test_data["answers"][str(idx)] = list(test_data.get("multi_select_temp", set()))
                test_data["multi_select_temp"] = set()
            else:
                test_data["answers"][str(idx)] = int(answer)
        
        message = query.message
    
    # Matn javob
    elif update.message:
        user_text = update.message.text.strip()
        
        if q_type in ["text_input", "fill_blank"]:
            test_data["answers"][str(idx)] = user_text
        
        elif q_type == "matching":
            # Format: 1-A, 2-C, 3-B
            pairs = {}
            for pair in user_text.split(","):
                pair = pair.strip()
                if "-" in pair:
                    left, right = pair.split("-")
                    try:
                        left_idx = int(left.strip()) - 1
                        right_idx = ord(right.strip().upper()) - 65
                        pairs[left_idx] = right_idx
                    except:
                        pass
            test_data["answers"][str(idx)] = pairs
        
        elif q_type == "ordering":
            items = [item.strip() for item in user_text.split(",")]
            options = test_data.get("ordering_options", question.get("items", []))
            order = []
            for item in items:
                for i, opt in enumerate(question.get("items", [])):
                    if opt.lower() in item.lower() or item.lower() in opt.lower():
                        order.append(i)
                        break
            test_data["answers"][str(idx)] = order
        
        message = update.message
    
    # Keyingi savolga o'tish
    test_data["current_index"] = idx + 1
    
    total = len(questions)
    next_idx = test_data["current_index"]
    
    if next_idx >= total:
        await _finish_test(message, context)
        return ConversationHandler.END
    
    await _send_question(message, context, next_idx)
    return ANSWERING


async def _finish_test(message, context: ContextTypes.DEFAULT_TYPE):
    """Testni tugatish va natijani hisoblash"""
    test_data = context.user_data.get("current_test", {})
    test = test_data.get("test", {})
    questions = test_data.get("questions", [])
    answers = test_data.get("answers", {})
    start_time = test_data.get("start_time", time.time())
    
    time_spent = int(time.time() - start_time)
    
    # Natijani hisoblash
    result = calculate_score(questions, answers)
    result["time_spent"] = time_spent
    result["passing_score"] = test.get("passing_score", 60)
    result["attempt_number"] = test_data.get("attempt_number", 1)
    
    # Bazaga saqlash
    user_id = None
    if hasattr(message, 'from_user') and message.from_user:
        user_id = message.from_user.id
    
    result_id = None
    if user_id:
        result_id = save_result(user_id, test.get("test_id"), result)
        user = get_user(user_id)
        user_name = user.get("name", "Foydalanuvchi") if user else "Foydalanuvchi"
    else:
        user_name = "Foydalanuvchi"
    
    # Natija xabari
    result_text = format_result_message(result, test, user_name)
    keyboard = result_keyboard(test.get("test_id"), result_id, result.get("passed", False))
    
    await message.reply_text(result_text, reply_markup=keyboard, parse_mode="HTML")
    
    # Sessiyani tozalash
    context.user_data.pop("current_test", None)


async def finish_test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Testni bekor qilish"""
    await update.message.reply_text("❌ Test bekor qilindi.")
    context.user_data.pop("current_test", None)
    return ConversationHandler.END

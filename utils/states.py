"""
📌 AIOGRAM 3 FSM (HOLATLAR / STATES)
Barcha qadamlar: Test yechish, Yaratish, Admin va Support.
Hech narsa qisqartirilmadi!
"""
from aiogram.fsm.state import State, StatesGroup

class TestSolving(StatesGroup):
    answering = State()
    text_answer = State()
    matching_answer = State()
    ordering_answer = State()
    viewing_explanation = State()

class CreateTest(StatesGroup):
    choose_method = State()     # YANGI: Fayl yoki Quiz usulini tanlash
    waiting_for_polls = State() # YANGI: Telegram Quiz'larini kutish
    upload_file = State()
    set_subject = State()
    set_difficulty = State()
    set_time_limit = State()
    set_passing_score = State()
    set_max_attempts = State()
    set_visibility = State()
    confirm_test = State()
    manual_question = State()
    manual_options = State()
    manual_correct = State()
    manual_explanation = State()

class Registration(StatesGroup):
    name = State()
    phone = State()
    role = State()

class AdminPanel(StatesGroup):
    action = State()
    block_user = State()
    delete_test = State()
    broadcast = State()

class Support(StatesGroup):
    waiting_for_message = State()
    waiting_for_reply = State()
    

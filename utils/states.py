"""
📌 AIOGRAM 3 FSM (HOLATLAR)
Foydalanuvchi qaysi qadamda turganini xotirada saqlash uchun
"""
from aiogram.fsm.state import State, StatesGroup

class TestSolving(StatesGroup):
    answering = State()
    text_answer = State()
    matching_answer = State()
    ordering_answer = State()

class CreateTest(StatesGroup):
    upload_file = State()
    set_subject = State()
    set_difficulty = State()
    set_time_limit = State()
    set_visibility = State()
    set_passing_score = State()
    confirm_test = State()

class AdminPanel(StatesGroup):
    action = State()
    block_user = State()
    delete_test = State()
    broadcast = State()

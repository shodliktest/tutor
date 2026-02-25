"""
📌 AIOGRAM 3 FSM (HOLATLAR / STATES)
Barcha qadamlar: Test yechish, Yaratish, Admin va Support.
"""
from aiogram.fsm.state import State, StatesGroup

class TestSolving(StatesGroup):
    answering = State()
    text_answer = State()
    matching_answer = State()
    ordering_answer = State()
    viewing_explanation = State()

class CreateTest(StatesGroup):
    upload_file = State()
    set_subject = State()
    set_difficulty = State()
    set_time_limit = State()
    set_passing_score = State()
    set_max_attempts = State()
    set_visibility = State()

class AdminPanel(StatesGroup):
    broadcast = State()

class Support(StatesGroup):
    waiting_for_message = State()
    waiting_for_reply = State()
    

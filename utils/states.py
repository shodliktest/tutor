"""
📌 FSM States — Aiogram 3.x
Barcha qadamlar: Test yechish, Yaratish, Poll test, Admin
"""
from aiogram.fsm.state import State, StatesGroup


class TestSolving(StatesGroup):
    """Oddiy inline button orqali test yechish"""
    answering   = State()   # Inline tugmalar bilan javob berish
    text_answer = State()   # Yozma javob kutish (text_input/fill_blank)


class PollTest(StatesGroup):
    """Telegram native quiz poll orqali test yechish"""
    active = State()        # Poll yuborilgan, javob kutilmoqda


class CreateTest(StatesGroup):
    """Test yaratish qadamlari"""
    choose_method   = State()   # Fayl yoki QuizBot tanlash
    waiting_polls   = State()   # QuizBotdan forward kutish
    upload_file     = State()   # Fayl kutish (TXT/PDF/DOCX)
    set_subject     = State()   # Qo'lda fan nomi yozish
    set_title       = State()   # Test nomi yozish
    set_difficulty  = State()   # Qiyinlik tanlash
    set_time_limit  = State()   # Vaqt limiti
    set_passing     = State()   # O'tish foizi
    set_attempts    = State()   # Urinishlar soni
    set_visibility  = State()   # Maxfiylik


class AdminPanel(StatesGroup):
    """Admin boshqaruv qadamlari"""
    broadcast   = State()   # Xabar tarqatish
    block_user  = State()   # Foydalanuvchi bloklash
    delete_test = State()   # Test o'chirish

"""
📌 AIOGRAM 3 FSM (HOLATLAR / STATES)
Foydalanuvchi qaysi qadamda turganini xotirada saqlash uchun barcha holatlar.
Hech narsa qisqartirilmadi, barcha zaxira va kelajakdagi qadamlar ham qo'shildi.
"""
from aiogram.fsm.state import State, StatesGroup

# ==========================================
# 1. TEST ISHLASH JARAYONI QADAMLARI
# ==========================================
class TestSolving(StatesGroup):
    answering = State()          # Tugmali javoblarni kutish (A, B, C, D)
    text_answer = State()        # Yozma javoblarni kutish (Text, Fill blank)
    matching_answer = State()    # Moslashtirish javobini kutish
    ordering_answer = State()    # Tartiblash javobini kutish


# ==========================================
# 2. TEST YARATISH JARAYONI QADAMLARI
# ==========================================
class CreateTest(StatesGroup):
    upload_file = State()        # Fayl yuklash qadami
    set_subject = State()        # Fan nomini kiritish
    set_difficulty = State()     # Qiyinlik darajasini tanlash
    set_time_limit = State()     # Vaqt limitini belgilash
    set_passing_score = State()  # O'tish foizini kiritish
    set_max_attempts = State()   # Urinishlar sonini belgilash (Limit)
    set_visibility = State()     # Maxfiylikni tanlash (Ommaviy/Link/Shaxsiy)
    confirm_test = State()       # Testni tasdiqlash
    
    # Qo'lda (Manual) test yaratish uchun zaxira qadamlar
    manual_question = State()    # Savol matnini yozish
    manual_options = State()     # Variantlarni kiritish
    manual_correct = State()     # To'g'ri javobni belgilash
    manual_explanation = State() # Izoh yozish


# ==========================================
# 3. RO'YXATDAN O'TISH (AUTH) QADAMLARI
# ==========================================
class Registration(StatesGroup):
    name = State()               # Ismni kutish
    phone = State()              # Telefon raqamni kutish
    role = State()               # Rolni tanlash (O'quvchi/O'qituvchi)


# ==========================================
# 4. ADMIN PANEL QADAMLARI
# ==========================================
class AdminPanel(StatesGroup):
    action = State()             # Admindan biror amal kutish
    block_user = State()         # Bloklanadigan ID ni kutish
    delete_test = State()        # O'chiriladigan Test ID ni kutish
    broadcast = State()          # Hammaga tarqatiladigan xabarni kutish

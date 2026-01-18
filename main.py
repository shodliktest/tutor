import streamlit as st
import telebot
from telebot import types
from openai import OpenAI
import os, threading, json, time

# --- 1. SOZLAMALAR VA ADMIN ---
ADMIN_ID = 1416457518 
DATA_FILE = "user_learning_data.json"

# API kalitlarni Secrets-dan olish
try:
    DEEPSEEK_KEY = st.secrets["DEEPSEEK_API_KEY"]
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
except:
    st.error("❌ Secrets-da DEEPSEEK_API_KEY yoki BOT_TOKEN topilmadi!")
    st.stop()

# Klientlarni ishga tushirish
client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")
bot = telebot.TeleBot(BOT_TOKEN)

# --- 2. MA'LUMOTLAR BAZASI MANTIQI ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Foydalanuvchi ma'lumotlarini yuklash
if 'db' not in st.session_state:
    st.session_state.db = load_data()

# --- 3. AI TUTOR PROMPT ---
SYSTEM_PROMPT = """Siz professional Repetitor (Tutor) botisiz.
1. Foydalanuvchi har qanday fandan savol bersa, aniq va ilmiy javob bering.
2. Agar foydalanuvchi "Test" deb yozsa, oxirgi suhbatdan kelib chiqib 4 variantli 1 ta test tuzing.
3. Foydalanuvchi javobini tekshiring: to'g'ri bo'lsa rag'batlantiring, xato bo'lsa 'Nega'ligini tushuntiring.
4. Javob berishda doim o'quvchini qo'llab-quvvatlovchi ohangda bo'ling."""

# --- 4. BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def welcome(m):
    uid = str(m.chat.id)
    if uid not in st.session_state.db:
        st.session_state.db[uid] = {
            "name": m.from_user.first_name,
            "score": 0,
            "tests_taken": 0,
            "level": "Boshlang'ich"
        }
        save_data(st.session_state.db)
    
    msg = (f"🎓 **Assalomu alaykum, {m.from_user.first_name}!**\n\n"
           f"Men sizning shaxsiy AI Tutor botingizman. Men bilan quyidagilarni qilishingiz mumkin:\n"
           f"🔹 Xohlagan faningizdan savol so'rash.\n"
           f"🔹 'Test' deb yozib bilimingizni sinash.\n"
           f"🔹 Xatolaringiz ustida ishlash.\n\n"
           f"🚀 Qaysi fanni o'rganishni boshlaymiz?")
    
    # Tugmalar
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add("📝 Test ishlash", "📊 Mening natijalarim")
    menu.add("ℹ️ Yordam")
    
    bot.send_message(uid, msg, parse_mode="Markdown", reply_markup=menu)

@bot.message_handler(func=lambda m: True)
def handle_text(m):
    uid = str(m.chat.id)
    user_msg = m.text
    
    if uid not in st.session_state.db:
        st.session_state.db[uid] = {"name": m.from_user.first_name, "score": 0, "tests_taken": 0, "level": "Boshlang'ich"}

    # Natijalarni ko'rish
    if user_msg == "📊 Mening natijalarim":
        stats = st.session_state.db[uid]
        bot.send_message(uid, f"📊 **Sizning ko'rsatkichlaringiz:**\n\n"
                              f"🏆 Ballar: {stats['score']}\n"
                              f"📝 Ishlangan testlar: {stats['tests_taken']}\n"
                              f"🎖 Daraja: {stats['level']}")
        return

    # AI javobini kutish
    wait_msg = bot.send_message(uid, "💡 *AI Tutor o'ylamoqda...*", parse_mode="Markdown")
    
    try:
        # DeepSeek API so'rovi
        # Test rejimi uchun mantiqni biroz kuchaytiramiz
        input_text = f"Foydalanuvchi xabari: {user_msg}. Agar bu javob bo'lsa tekshiring, agar savol bo'lsa javob bering, agar 'test' bo'lsa test tuzing."
        
        response = client.chat.completions.create(
            model="deepseek-chat", # Yoki "deepseek-reasoner" (R1)
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": input_text}
            ]
        )
        
        ai_reply = response.choices[0].message.content
        
        # Ballarni yangilash (Oddiy mantiq: Agar AI "To'g'ri" yoki "Barakalla" desa ball berish)
        if "to'g'ri" in ai_reply.lower() or "barakalla" in ai_reply.lower():
            st.session_state.db[uid]["score"] += 10
            st.session_state.db[uid]["tests_taken"] += 1
            save_data(st.session_state.db)

        bot.edit_message_text(ai_reply, uid, wait_msg.message_id, parse_mode="Markdown")
        
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi: {e}", uid, wait_msg.message_id)

# --- 5. STREAMLIT DASHBOARD (Admin Panel) ---
st.title("🎓 Smart AI Tutor Dashboard")

# Real vaqtda statistika
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Foydalanuvchilar", len(st.session_state.db))
with col2:
    st.metric("Ishlangan testlar", sum(u['tests_taken'] for u in st.session_state.db.values()))
with col3:
    st.metric("O'rtacha ball", round(sum(u['score'] for u in st.session_state.db.values()) / (len(st.session_state.db) or 1), 1))

st.divider()

st.subheader("👥 Foydalanuvchilar ro'yxati")
st.table(st.session_state.db)

# Botni alohida threadda yurgizish
if 'bot_started' not in st.session_state:
    st.session_state.bot_started = True
    threading.Thread(target=bot.infinity_polling, daemon=True).start()

st.info("ℹ️ Bot Telegramda aktiv ishlamoqda. Dashboard natijalarni real vaqtda ko'rsatadi.")

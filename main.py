import streamlit as st
import telebot
from telebot import types
from openai import OpenAI
import os, threading, json, time

# --- 1. GLOBAL BAZA VA SOZLAMALAR ---
# session_state o'rniga oddiy global o'zgaruvchi ishlatamiz
# Chunki bot oqimi session_state ni ko'ra olmaydi
ADMIN_ID = 1416457518 
DATA_FILE = "user_learning_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Ma'lumotlarni yuklab olamiz (Global o'zgaruvchiga)
if 'global_db' not in st.cache_resource:
    st.cache_resource.global_db = load_data()

db = st.cache_resource.global_db

# API kalitlar
try:
    DEEPSEEK_KEY = st.secrets["DEEPSEEK_API_KEY"]
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
except:
    st.error("❌ Secrets sozlanmagan!")
    st.stop()

client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")
bot = telebot.TeleBot(BOT_TOKEN)

# --- 2. ADMIN VA BOT HOLATI ---
# Bot statuslarini ham global qilamiz
if 'status' not in st.cache_resource:
    st.cache_resource.status = {"service": True, "quiz": True}

# --- 3. BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def welcome(m):
    uid = str(m.chat.id)
    # Endi db ni to'g'ridan-to'g'ri ishlatamiz
    if uid not in db:
        db[uid] = {"name": m.from_user.first_name, "score": 0, "tests": 0}
        save_data(db)
    
    msg = f"🎓 **Salom, {m.from_user.first_name}!**\nMen sizning AI repetitoringizman."
    
    # Menyu tugmalari
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if int(uid) == ADMIN_ID:
        menu.add("👑 Admin Panel")
    menu.add("📝 Test ishlash", "📊 Natijalarim")
    
    bot.send_message(uid, msg, parse_mode="Markdown", reply_markup=menu)

@bot.message_handler(func=lambda m: True)
def handle_text(m):
    uid = str(m.chat.id)
    
    # Xizmat holatini tekshirish
    if not st.cache_resource.status["service"] and int(uid) != ADMIN_ID:
        bot.send_message(uid, "🛑 Bot vaqtincha to'xtatilgan.")
        return

    if m.text == "📊 Natijalarim":
        stats = db.get(uid, {"score": 0, "tests": 0})
        bot.send_message(uid, f"📊 Ballaringiz: {stats['score']}")
        return

    # AI javobi
    wait = bot.send_message(uid, "💡 *AI Tutor o'ylamoqda...*", parse_mode="Markdown")
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": m.text}]
        )
        bot.edit_message_text(response.choices[0].message.content, uid, wait.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {e}", uid, wait.message_id)

# --- 4. STREAMLIT DASHBOARD ---
st.title("🎓 Smart Tutor Dashboard")

st.metric("Jami o'quvchilar", len(db))

if db:
    st.write("### 👥 Foydalanuvchilar")
    st.table(db)

# Botni ishga tushirish
if 'bot_started' not in st.cache_resource:
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    st.cache_resource.bot_started = True

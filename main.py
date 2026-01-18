import streamlit as st
import telebot
from telebot import types
from openai import OpenAI
import os, threading, json, time, datetime
import pytz

# --- 1. ADMIN VA GLOBAL SOZLAMALAR ---
ADMIN_ID = 1416457518 
DATA_FILE = "user_learning_data.json"
uz_tz = pytz.timezone('Asia/Tashkent')

def get_uz_time():
    return datetime.datetime.now(uz_tz).strftime('%H:%M:%S')

# --- 2. MULTI-THREADING UCHUN XAVFSIZ BAZA ---
@st.cache_resource
def init_shared_resources():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try: data = json.load(f)
            except: data = {}
    else:
        data = {}
    
    settings = {"service": True, "quiz": True}
    return data, settings

db, bot_settings = init_shared_resources()

def save_db():
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=4)

# --- 3. GROQ CLIENT SOZLAMASI ---
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
except:
    st.error("❌ Secrets-da GROQ_API_KEY yoki BOT_TOKEN topilmadi!")
    st.stop()

# Groq OpenAI kutubxonasi orqali ulanadi
client = OpenAI(
    api_key=GROQ_KEY,
    base_url="https://api.groq.com/openai/v1"
)
# Tavsiya etilgan model: llama-3.3-70b-versatile
MODEL_NAME = "llama-3.3-70b-versatile" 

bot = telebot.TeleBot(BOT_TOKEN)

# --- 4. MENYULAR VA ADMIN PANEL ---
def main_menu(uid):
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if int(uid) == ADMIN_ID:
        menu.add(types.KeyboardButton("👑 Admin Panel"))
    menu.add(types.KeyboardButton("📝 Test ishlash"), types.KeyboardButton("📊 Natijalarim"))
    menu.add(types.KeyboardButton("ℹ️ Yordam"))
    return menu

def admin_panel_markup():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    menu.add("📊 Statistika", "📂 Bazani yuklash")
    menu.add("📢 Hammaga xabar", "👤 UID-ga xabar")
    menu.add("🛑 Botni to'xtatish", "✅ Botni yoqish")
    menu.add("📵 Testni o'chirish", "📶 Testni yoqish")
    menu.add("♻️ Reboot", "⬅️ Orqaga")
    return menu

# --- 5. BOT MANTIQI ---

@bot.message_handler(commands=['start'])
def welcome(m):
    uid = str(m.chat.id)
    if uid not in db:
        db[uid] = {"name": m.from_user.first_name, "score": 0, "tests": 0}
        save_db()
    
    msg_text = (
        f"🎓 **Assalomu alaykum, {m.from_user.first_name}!**\n\n"
        "Men Groq LPU texnologiyasi asosida ishlovchi o‘ta tezkor AI repetitorman. "
        "Men bilan fanni 10 barobar tezroq o‘rganishingiz mumkin:\n\n"
        "⚡ **Tezkor javob:** Savol yuboring va soniyalar ichida tushuntirish oling.\n"
        "📝 **Smart Test:** Bilimingizni sinash uchun real vaqtda testlar tuzaman.\n"
        "📊 **Tahlil:** Har bir xatoingizni mantiqiy tushuntirib beraman.\n\n"
        "🚀 **Qaysi fandan darsni boshlaymiz?**"
    )
    
    if int(uid) == ADMIN_ID:
        msg_text += "\n\n😎 **Salom, Admin! Groq tizimi tayyor.**"
        
    bot.send_message(uid, msg_text, parse_mode="Markdown", reply_markup=main_menu(uid))

# ADMIN AMALLARI (Original)
@bot.message_handler(func=lambda m: m.text == "👑 Admin Panel" and m.chat.id == ADMIN_ID)
def admin_p(m):
    bot.send_message(m.chat.id, "🛠 **Boshqaruv markazi:**", reply_markup=admin_panel_markup())

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text in [
    "📊 Statistika", "🛑 Botni to'xtatish", "✅ Botni yoqish", "♻️ Reboot", "⬅️ Orqaga"
])
def admin_tools(m):
    if m.text == "📊 Statistika":
        bot.send_message(m.chat.id, f"👥 O'quvchilar: {len(db)}\n🤖 Xizmat: {bot_settings['service']}")
    elif m.text == "🛑 Botni to'xtatish":
        bot_settings['service'] = False
        bot.send_message(m.chat.id, "🛑 To'xtatildi.")
    elif m.text == "✅ Botni yoqish":
        bot_settings['service'] = True
        bot.send_message(m.chat.id, "✅ Yoqildi.")
    elif m.text == "♻️ Reboot":
        st.rerun()
    elif m.text == "⬅️ Orqaga":
        bot.send_message(m.chat.id, "Menyu:", reply_markup=main_menu(m.chat.id))

# --- 6. ASOSIY TUTOR MANTIQI ---
@bot.message_handler(func=lambda m: True)
def tutor_logic(m):
    uid = str(m.chat.id)
    
    if not bot_settings['service'] and int(uid) != ADMIN_ID:
        bot.send_message(uid, "🛑 **Bot vaqtincha to'xtatilgan.**")
        return

    if m.text == "📊 Natijalarim":
        stats = db.get(uid, {"score": 0, "tests": 0})
        bot.send_message(uid, f"🏆 Ballar: {stats['score']}\n📝 Testlar: {stats['tests']}")
        return

    wait = bot.send_message(uid, "⚡ *Groq LPU tahlil qilmoqda...*", parse_mode="Markdown")
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Siz intellektual repetitorsiz. Groq kabi tez va aniq javob bering."},
                {"role": "user", "content": m.text}
            ]
        )
        bot.edit_message_text(response.choices[0].message.content, uid, wait.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {e}", uid, wait.message_id)

# --- 7. STREAMLIT UI ---
st.title("🎓 Smart Tutor Dashboard (Groq Edition)")
st.write(f"Tizim statusi: **Online** | Model: `{MODEL_NAME}`")

c1, c2 = st.columns(2)
with c1: st.metric("O'quvchilar", len(db))
with c2: st.metric("Tezlik", "O'ta yuqori (LPU)")

if db:
    st.table(db)

@st.cache_resource
def start_bot():
    thread = threading.Thread(target=bot.infinity_polling, daemon=True)
    thread.start()
    return True

start_bot()

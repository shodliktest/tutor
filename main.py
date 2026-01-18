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
# Dekorator yordamida bazani oqimlar uchun umumiy qilamiz
@st.cache_resource
def init_shared_resources():
    # Fayldan yuklash
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except:
                data = {}
    else:
        data = {}
    
    # Bot holati va rejimlarini saqlash uchun lug'at
    settings = {"service": True, "quiz": True}
    return data, settings

# Global o'zgaruvchilarga biriktiramiz
db, bot_settings = init_shared_resources()

def save_db():
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=4)

# API kalitlar
try:
    DEEPSEEK_KEY = st.secrets["DEEPSEEK_API_KEY"]
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
except:
    st.error("❌ Secrets sozlanmagan!")
    st.stop()

client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")
bot = telebot.TeleBot(BOT_TOKEN)

# --- 3. MENYULAR (Original ko'rinishda) ---
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

# --- 4. BOT MANTIQI ---

@bot.message_handler(commands=['start'])
def welcome(m):
    uid = str(m.chat.id)
    if uid not in db:
        db[uid] = {"name": m.from_user.first_name, "score": 0, "tests": 0}
        save_db()
    
    # ORIGINAL JAVOB MATNI (To'liq holatda)
    msg_text = (
        f"👋 **Assalomu alaykum, {m.from_user.first_name}!**\n\n"
        "Men sizning intellektual repetitoringizman. Men bilan har qanday fanni o'rganishingiz mumkin. "
        "Siz uchun maxsus AI tahlil tizimi tayyorlab qo'yilgan:\n\n"
        "🔹 **O'rganish:** Savol bering, AI sizga chuqur tushuncha beradi.\n"
        "🔹 **Sinov:** 'Test' deb yozing va bilimingizni tekshiring.\n"
        "🔹 **Tahlil:** Xato qilsangiz, AI sizga sababini tushuntiradi.\n\n"
        "🚀 **Boshlash uchun xohlagan faningizdan savol yuboring!**"
    )
    
    if int(uid) == ADMIN_ID:
        msg_text += "\n\n😎 **Salom, Admin! Boshqaruv paneli aktiv.**"
        
    bot.send_message(uid, msg_text, parse_mode="Markdown", reply_markup=main_menu(uid))

# ADMIN PANEL FUNKSIYALARI
@bot.message_handler(func=lambda m: m.text == "👑 Admin Panel" and m.chat.id == ADMIN_ID)
def admin_panel(m):
    bot.send_message(m.chat.id, "🛠 **Admin boshqaruv markazi:**", reply_markup=admin_panel_markup())

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text in [
    "📊 Statistika", "📂 Bazani yuklash", "🛑 Botni to'xtatish", "✅ Botni yoqish", 
    "📵 Testni o'chirish", "📶 Testni yoqish", "♻️ Reboot", "⬅️ Orqaga"
])
def handle_admin_tools(m):
    if m.text == "📊 Statistika":
        bot.send_message(m.chat.id, f"👥 **Jami foydalanuvchilar:** {len(db)}\n"
                                   f"🤖 Bot: {'✅ Aktiv' if bot_settings['service'] else '🛑 Yopiq'}\n"
                                   f"📝 Test: {'✅ Ochiq' if bot_settings['quiz'] else '📵 Yopiq'}")
    elif m.text == "🛑 Botni to'xtatish":
        bot_settings['service'] = False
        bot.send_message(m.chat.id, "🛑 Bot xizmati to'xtatildi.")
    elif m.text == "✅ Botni yoqish":
        bot_settings['service'] = True
        bot.send_message(m.chat.id, "✅ Bot xizmati yoqildi.")
    elif m.text == "♻️ Reboot":
        bot.send_message(m.chat.id, "♻️ Server Reboot...")
        st.rerun()
    elif m.text == "⬅️ Orqaga":
        bot.send_message(m.chat.id, "Asosiy menyu:", reply_markup=main_menu(m.chat.id))

# FOYDALANUVCHI MANTIQI
@bot.message_handler(func=lambda m: True)
def tutor_logic(m):
    uid = str(m.chat.id)
    
    if not bot_settings['service'] and int(uid) != ADMIN_ID:
        bot.send_message(uid, "🛑 **Bot vaqtincha to'xtatilgan.**")
        return

    if m.text == "📊 Natijalarim":
        stats = db.get(uid, {"score": 0, "tests": 0})
        bot.send_message(uid, f"🏆 Ballaringiz: {stats['score']}\n📝 Testlar: {stats['tests']}")
        return

    wait = bot.send_message(uid, "💡 *AI Tutor o'ylamoqda...*", parse_mode="Markdown")
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Siz repetitor botisiz. Test tuzish va javobni tahlil qilish sizning vazifangiz."},
                {"role": "user", "content": m.text}
            ]
        )
        bot.edit_message_text(response.choices[0].message.content, uid, wait.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {e}", uid, wait.message_id)

# --- 5. STREAMLIT UI ---
st.title("🎓 Smart Tutor Admin Dashboard")
st.write(f"Server vaqti: {get_uz_time()}")

c1, c2 = st.columns(2)
with c1: st.metric("O'quvchilar", len(db))
with c2: st.metric("Bot Status", "Online" if bot_settings['service'] else "Offline")

if db:
    st.table(db)

# Botni ishga tushirish (Singleton pattern)
@st.cache_resource
def start_bot_thread():
    thread = threading.Thread(target=bot.infinity_polling, daemon=True)
    thread.start()
    return True

start_bot_thread()

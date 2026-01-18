import streamlit as st
import telebot
from telebot import types
from openai import OpenAI
import os, threading, json, time, datetime

# --- 1. ADMIN VA GLOBAL SOZLAMALAR ---
ADMIN_ID = 1416457518 
DATA_FILE = "user_learning_data.json"

# Bot holatini Session State orqali boshqarish
if 'service_on' not in st.session_state:
    st.session_state.service_active = True  # Umumiy bot xizmati
if 'quiz_active' not in st.session_state:
    st.session_state.quiz_active = True     # Test rejimi

# API kalitlarni Secrets-dan olish
try:
    DEEPSEEK_KEY = st.secrets["DEEPSEEK_API_KEY"]
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
except:
    st.error("❌ Secrets sozlanmagan!")
    st.stop()

client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")
bot = telebot.TeleBot(BOT_TOKEN)

# --- 2. BAZA BILAN ISHLASH ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = load_data()

# --- 3. MENYU VA TUGMALAR ---
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

# --- 4. BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def welcome(m):
    uid = str(m.chat.id)
    if uid not in st.session_state.db:
        st.session_state.db[uid] = {"name": m.from_user.first_name, "score": 0, "tests": 0}
        save_data(st.session_state.db)
    
    msg = (f"🎓 **Xush kelibsiz, {m.from_user.first_name}!**\n\n"
           "Men sizning intellektual repetitoringizman. Men bilan har qanday fanni o'rganishingiz mumkin.")
    
    if int(uid) == ADMIN_ID:
        msg += "\n\n😎 **Salom, Admin! Boshqaruv paneli aktivlashdi.**"
        
    bot.send_message(uid, msg, parse_mode="Markdown", reply_markup=main_menu(uid))

# --- ADMIN FUNKSIYALARI ---
@bot.message_handler(func=lambda m: m.text == "👑 Admin Panel" and m.chat.id == ADMIN_ID)
def open_admin(m):
    bot.send_message(m.chat.id, "🛠 **Admin boshqaruv markazi:**", reply_markup=admin_panel_markup())

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text in [
    "📊 Statistika", "📂 Bazani yuklash", "🛑 Botni to'xtatish", "✅ Botni yoqish", 
    "📵 Testni o'chirish", "📶 Testni yoqish", "♻️ Reboot", "⬅️ Orqaga"
])
def admin_actions(m):
    if m.text == "📊 Statistika":
        count = len(st.session_state.db)
        bot.send_message(m.chat.id, f"👥 **Jami foydalanuvchilar:** {count}\n"
                                   f"🤖 Bot: {'✅ Aktiv' if st.session_state.service_active else '🛑 To\'xtatilgan'}\n"
                                   f"📝 Test: {'✅ Ochiq' if st.session_state.quiz_active else '📵 Yopiq'}")
    
    elif m.text == "📂 Bazani yuklash":
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "rb") as f:
                bot.send_document(m.chat.id, f, caption="📂 Foydalanuvchilar ma'lumotlar bazasi")
    
    elif m.text == "🛑 Botni to'xtatish":
        st.session_state.service_active = False
        bot.send_message(m.chat.id, "🛑 Bot xizmati barcha uchun to'xtatildi.")
        
    elif m.text == "✅ Botni yoqish":
        st.session_state.service_active = True
        bot.send_message(m.chat.id, "✅ Bot xizmati qayta yoqildi.")

    elif m.text == "📵 Testni o'chirish":
        st.session_state.quiz_active = False
        bot.send_message(m.chat.id, "📵 Test rejimi yopildi.")

    elif m.text == "📶 Testni yoqish":
        st.session_state.quiz_active = True
        bot.send_message(m.chat.id, "📶 Test rejimi yoqildi.")

    elif m.text == "♻️ Reboot":
        bot.send_message(m.chat.id, "♻️ Server qayta yuklanmoqda...")
        st.rerun()

    elif m.text == "⬅️ Orqaga":
        bot.send_message(m.chat.id, "Asosiy menyu:", reply_markup=main_menu(m.chat.id))

# ADMIN XABARLASHISH TIZIMI
@bot.message_handler(func=lambda m: m.text == "📢 Hammaga xabar" and m.chat.id == ADMIN_ID)
def broadcast_step1(m):
    msg = bot.send_message(m.chat.id, "📢 Xabar matnini yuboring (yoki 'bekor'):")
    bot.register_next_step_handler(msg, broadcast_step2)

def broadcast_step2(m):
    if m.text.lower() == 'bekor': return
    success = 0
    for uid in st.session_state.db.keys():
        try:
            bot.send_message(uid, f"📢 **ADMIN XABARI:**\n\n{m.text}", parse_mode="Markdown")
            success += 1
            time.sleep(0.1)
        except: pass
    bot.send_message(m.chat.id, f"✅ {success} ta foydalanuvchiga yuborildi.")

@bot.message_handler(func=lambda m: m.text == "👤 UID-ga xabar" and m.chat.id == ADMIN_ID)
def private_step1(m):
    msg = bot.send_message(m.chat.id, "👤 Foydalanuvchi UID raqamini kiriting:")
    bot.register_next_step_handler(msg, private_step2)

def private_step2(m):
    try:
        target_uid = int(m.text)
        msg = bot.send_message(m.chat.id, f"UID: {target_uid} uchun xabarni yozing:")
        bot.register_next_step_handler(msg, lambda message: private_step3(message, target_uid))
    except:
        bot.send_message(m.chat.id, "❌ UID raqam bo'lishi kerak.")

def private_step3(m, target_uid):
    try:
        bot.send_message(target_uid, f"📩 **ADMIN XABARI:**\n\n{m.text}", parse_mode="Markdown")
        bot.send_message(m.chat.id, "✅ Xabar yuborildi.")
    except:
        bot.send_message(m.chat.id, "❌ Yuborishda xatolik yuz berdi.")

# --- 5. STANDART FOYDALANUVCHI MANTIQI ---
@bot.message_handler(func=lambda m: True)
def handle_all_messages(m):
    uid = str(m.chat.id)
    
    # Bot to'xtatilgan bo'lsa (Admin emas foydalanuvchilar uchun)
    if not st.session_state.service_active and int(uid) != ADMIN_ID:
        bot.send_message(uid, "🛑 **Kechirasiz!** Bot hozirda vaqtincha to'xtatilgan. Admin tomonidan tez orada qayta yoqiladi.")
        return

    # Test rejimi yopilgan bo'lsa
    if m.text == "📝 Test ishlash" and not st.session_state.quiz_active and int(uid) != ADMIN_ID:
        bot.send_message(uid, "📵 **Hozirda test rejimi yopiq.** Iltimos, keyinroq urinib ko'ring.")
        return

    # Natijalarni ko'rish
    if m.text == "📊 Natijalarim":
        stats = st.session_state.db.get(uid, {"score": 0, "tests": 0})
        bot.send_message(uid, f"📊 **Sizning ko'rsatkichlaringiz:**\n\n🏆 Ballar: {stats['score']}\n📝 Ishlangan testlar: {stats['tests']}")
        return

    # DeepSeek AI tahlili
    wait = bot.send_message(uid, "💡 *AI Tutor o'ylamoqda...*", parse_mode="Markdown")
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Siz repetitor botisiz. Test rejimi yoqilganda 1 ta savol bering."},
                {"role": "user", "content": m.text}
            ]
        )
        ai_reply = response.choices[0].message.content
        bot.edit_message_text(ai_reply, uid, wait.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {e}", uid, wait.message_id)

# --- 6. STREAMLIT UI ---
st.title("🎓 Smart Tutor Admin Panel")

# Statistik Dashboard


c1, c2 = st.columns(2)
with c1:
    st.metric("Jami o'quvchilar", len(st.session_state.db))
with c2:
    status = "Online" if st.session_state.service_active else "Offline"
    st.metric("Server holati", status)

if st.session_state.db:
    st.write("### 👥 Foydalanuvchilar Ro'yxati")
    st.table(st.session_state.db)

# Bot oqimini boshlash
if 'bot_started' not in st.session_state:
    st.session_state.bot_started = True
    threading.Thread(target=bot.infinity_polling, daemon=True).start()

import asyncio
import os
import re
import threading
import pytz
import time
from datetime import datetime

import streamlit as st
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import whisper
from groq import Groq
from deep_translator import GoogleTranslator

# --- 0. KONFIGURATSIYA ---
ADMIN_ID = 1416457518 
USERS_FILE = "bot_users_list.txt"
uz_tz = pytz.timezone('Asia/Tashkent')

def get_uz_time():
    return datetime.now(uz_tz).strftime('%Y-%m-%d %H:%M:%S')

def log_user_and_get_count(user: types.User):
    """Foydalanuvchini bazaga qo'shish va tartib raqamini olish"""
    uid = user.id
    user_list = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f: user_list = f.readlines()
    
    exists = any(str(uid) in line for line in user_list)
    if not exists:
        count = len(user_list) + 1
        row = f"{count}. ID: {uid} | Ism: {user.first_name} | @{user.username} | {get_uz_time()}\n"
        with open(USERS_FILE, "a", encoding="utf-8") as f: f.write(row)
        return count, True
    return len(user_list), False

# --- 1. BOT VA AI SOZLAMALARI ---
try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("Secrets (BOT_TOKEN / GROQ_API_KEY) topilmadi!")
    st.stop()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client_groq = Groq(api_key=GROQ_API_KEY)
async_lock = asyncio.Lock()
waiting_users = 0

@st.cache_resource
def load_local_whisper():
    return whisper.load_model("base")

model_local = load_local_whisper()
user_settings = {}
user_data = {}

# --- 2. KLAVIATURALAR ---
def get_main_menu(uid):
    kb = ReplyKeyboardBuilder()
    kb.button(text="⚡ Groq Rejimi")
    kb.button(text="🎧 Whisper Rejimi")
    kb.button(text="🌐 Saytga kirish (Login)")
    kb.button(text="ℹ️ Yordam")
    if uid == ADMIN_ID: kb.button(text="🔑 Admin Panel")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

# --- 3. FORMATLASH FUNKSIYALARI ---

def smart_format_groq(text, lang_code=None):
    """Groq uchun paragraflar va xavfsiz italyancha tarjima"""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    res = "📝 **AQLLI TAHLIL (GROQ)**\n\n"
    para = ""
    for i, s in enumerate(sentences):
        if lang_code:
            try:
                tr = GoogleTranslator(source='auto', target=lang_code).translate(s)
                # Markdown xatoligini oldini olish uchun '_' ni tozalaymiz
                tr_safe = tr.replace('_', ' ')
                s = f"{s} _({tr_safe})_"
            except: pass
        para += s + " "
        if (i + 1) % 4 == 0:
            res += "    " + para.strip() + "\n\n"
            para = ""
    if para: res += "    " + para.strip()
    return res

# --- 4. BOT HANDLERLARI ---

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    count, is_new = log_user_and_get_count(m.from_user)
    if is_new:
        try: await bot.send_message(ADMIN_ID, f"🆕 YANGI USER: {m.from_user.first_name} (№{count})")
        except: pass
    user_settings[m.chat.id] = user_settings.get(m.chat.id, "groq")
    await m.answer(f"👋 **Assalomu alaykum!**\nSiz botimizning **{count}-foydalanuvchisiz!**", 
                   reply_markup=get_main_menu(m.from_user.id), parse_mode="Markdown")

@dp.message(F.text == "⚡ Groq Rejimi")
async def set_groq(m: types.Message):
    user_settings[m.chat.id] = "groq"
    await m.answer("✅ **Groq Rejimi tanlandi!**")

@dp.message(F.text == "🎧 Whisper Rejimi")
async def set_whisper(m: types.Message):
    user_settings[m.chat.id] = "local"
    await m.answer("✅ **Whisper Rejimi tanlandi!**")

@dp.message(F.audio | F.voice)
async def handle_audio_voice(m: types.Message):
    f_size = m.audio.file_size if m.audio else m.voice.file_size
    if f_size > 25 * 1024 * 1024:
        await m.answer("❌ Fayl juda katta (Maks 25MB).")
        return
    user_data[m.chat.id] = {'fid': m.audio.file_id if m.audio else m.voice.file_id}
    kb = InlineKeyboardBuilder()
    kb.button(text="🇺🇿 O'zbek", callback_data="l_uz")
    kb.button(text="📄 Original", callback_data="l_orig")
    await m.answer("🌍 **Tilni tanlang:**", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("l_"))
async def lang_callback(call: types.CallbackQuery):
    user_data[call.message.chat.id]['lang'] = call.data.replace("l_", "")
    kb = InlineKeyboardBuilder()
    kb.button(text="⏱ Split (Vaqt bilan)", callback_data="v_split")
    kb.button(text="📖 Full (Butun matn)", callback_data="v_full")
    await call.message.edit_text("📄 **Ko'rinishni tanlang:**", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("v_"))
async def view_callback(call: types.CallbackQuery):
    user_data[call.message.chat.id]['view'] = call.data.replace("v_", "")
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Chat", callback_data="f_chat")
    kb.button(text="📁 TXT", callback_data="f_txt")
    await call.message.edit_text("💾 **Formatni tanlang:**", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("f_"))
async def start_processing(call: types.CallbackQuery):
    global waiting_users
    chat_id = call.message.chat.id
    fmt = call.data.replace("f_", "")
    data = user_data.get(chat_id)
    mode = user_settings.get(chat_id, "groq")
    
    await call.message.delete()
    waiting_users += 1
    wait_msg = await call.message.answer(f"⏳ Navbat: {waiting_users-1}\nRejim: {mode.upper()}")
    
    async with async_lock: # NAVBAT TIZIMI
        try:
            async def progress(p, status):
                bar = "▓" * (p // 10) + "░" * (10 - (p // 10))
                try: await wait_msg.edit_text(f"🛰 **REJIM: {mode.upper()}**\n\n{status}\n\n📊 {p}%\n{bar}")
                except: pass

            await progress(10, "📥 Fayl yuklanmoqda...")
            f_path = f"t_{chat_id}.mp3"
            file = await bot.get_file(data['fid'])
            await bot.download_file(file.file_path, f_path)
            
            await progress(50, "🧠 AI tahlil qilmoqda...")
            
            # MA'LUMOTLARNI OLISH (Mismatch hal qilindi)
            if mode == "groq":
                with open(f_path, "rb") as f:
                    res = client_groq.audio.transcriptions.create(
                        file=(f_path, f.read()), model="whisper-large-v3-turbo", response_format="verbose_json"
                    )
                segments = res.segments
                def get_s_data(s): return s.start, s.text
            else:
                res = model_local.transcribe(f_path)
                segments = res['segments']
                def get_s_data(s): return s['start'], s['text']

            await progress(90, "✍️ Formatlanmoqda...")
            l_code = data.get('lang') if data.get('lang') != "orig" else None
            final_text = ""

            if data['view'] == "full" and mode == "groq":
                raw = " ".join([get_s_data(s)[1].strip() for s in segments])
                final_text = smart_format_groq(raw, l_code)
            else:
                for s in segments:
                    s_start, s_text = get_s_data(s)
                    tm = f"[{int(s_start//60):02d}:{int(s_start%60):02d}]"
                    txt = s_text.strip()
                    if l_code:
                        try:
                            tr = GoogleTranslator(source='auto', target=l_code).translate(txt)
                            final_text += f"{tm} {txt}\n _({tr.replace('_', ' ')})_\n\n"
                        except: final_text += f"{tm} {txt}\n\n"
                    else:
                        final_text += f"{tm} {txt}\n\n"

            imzo = f"\n---\n👤 **Dasturchi:** @Otavaliyev_M\n🤖 **Bot:** @{(await bot.get_me()).username}\n⏰ **Vaqt:** {get_uz_time()}"
            
            if fmt == "txt":
                with open(f"r_{chat_id}.txt", "w", encoding="utf-8") as f: f.write(final_text + imzo)
                await call.message.answer_document(types.FSInputFile(f"r_{chat_id}.txt"), caption="✅ Natija tayyor!")
                os.remove(f"r_{chat_id}.txt")
            else:
                # Telegram limitiga tekshirish
                content = final_text + imzo
                if len(content) > 4096:
                    for x in range(0, len(content), 4000):
                        await call.message.answer(content[x:x+4000], parse_mode="Markdown")
                else:
                    await call.message.answer(content, parse_mode="Markdown")

            await wait_msg.delete()
            if os.path.exists(f_path): os.remove(f_path)
        except Exception as e:
            await call.message.answer(f"❌ Xato: {str(e)}")
        finally:
            waiting_users -= 1

# --- 5. STREAMLIT ASYNC ENGINE ---

def run_aiogram_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # handle_signals=False -> set_wakeup_fd xatosini tuzatadi
    loop.run_until_complete(dp.start_polling(bot, handle_signals=False, skip_updates=True))

if "bot_active" not in st.session_state:
    st.session_state.bot_active = True
    threading.Thread(target=run_aiogram_thread, daemon=True).start()

st.title("🤖 Neon Hybrid Bot Server (Aiogram Fix)")
st.success("Barcha tizimlar barqaror va xatoliklarsiz ishlamoqda!")
    

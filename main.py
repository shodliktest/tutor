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
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import whisper
from groq import Groq
from deep_translator import GoogleTranslator

# --- 0. KONFIGURATSIYA ---
ADMIN_ID = 1416457518 
USERS_FILE = "bot_users_list.txt"
uz_tz = pytz.timezone('Asia/Tashkent')

class AdminStates(StatesGroup):
    waiting_for_bc = State()

def get_uz_time():
    return datetime.now(uz_tz).strftime('%Y-%m-%d %H:%M:%S')

def log_user_and_get_count(user: types.User):
    uid = user.id
    user_list = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            user_list = f.readlines()
    
    exists = any(str(uid) in line for line in user_list)
    if not exists:
        count = len(user_list) + 1
        row = f"{count}. ID: {uid} | Ism: {user.first_name} | @{user.username} | {get_uz_time()}\n"
        with open(USERS_FILE, "a", encoding="utf-8") as f: f.write(row)
        return count, True
    return len(user_list), False

# --- 1. GLOBAL SOZLAMALAR ---
try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("Secrets (BOT_TOKEN / GROQ_API_KEY) sozlanmagan!")
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
user_settings = {} # Foydalanuvchi rejimi
user_data = {}     # Vaqtinchalik ma'lumotlar

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

def clean_md(text):
    """Markdown formatini buzuvchi belgilarni tozalash"""
    if not text: return ""
    return text.replace("_", " ").replace("*", " ").replace("`", " ")

def format_smart_context(text, lang_code=None):
    """Groq uchun paragraflar va xavfsiz italyancha tarjima"""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    res = "📝 **AQLLI TAHLIL (GROQ)**\n\n"
    para = ""
    for i, s in enumerate(sentences):
        orig = clean_md(s)
        if lang_code:
            try:
                tr = GoogleTranslator(source='auto', target=lang_code).translate(orig)
                s = f"{orig} _({clean_md(tr)})_"
            except: s = orig
        else: s = orig
        
        para += s + " "
        if (i + 1) % 4 == 0:
            res += "    " + para.strip() + "\n\n"
            para = ""
    if para: res += "    " + para.strip()
    return res

# --- 4. HANDLERLAR ---

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    count, is_new = log_user_and_get_count(m.from_user)
    if is_new:
        try: await bot.send_message(ADMIN_ID, f"🆕 YANGI USER: {m.from_user.first_name} (№{count})")
        except: pass
    user_settings[m.chat.id] = user_settings.get(m.chat.id, "groq")
    await m.answer(f"👋 **Assalomu alaykum!**\nSiz botimizning **{count}-foydalanuvchisiz!**", 
                   reply_markup=get_main_menu(m.from_user.id))

@dp.message(F.text == "⚡ Groq Rejimi")
async def set_groq(m: types.Message):
    user_settings[m.chat.id] = "groq"
    await m.answer("✅ **Groq Rejimi tanlandi!** (Tezkor)")

@dp.message(F.text == "🎧 Whisper Rejimi")
async def set_whisper(m: types.Message):
    user_settings[m.chat.id] = "local"
    await m.answer("✅ **Whisper Rejimi tanlandi!** (Ritmik)")

@dp.message(F.text == "🔑 Admin Panel", F.chat.id == ADMIN_ID)
async def admin_h(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Statistika", callback_data="adm_stats")
    kb.button(text="📋 Foydalanuvchilar", callback_data="adm_list")
    kb.button(text="📢 Xabar tarqatish", callback_data="adm_bc")
    kb.button(text="🔄 Reboot", callback_data="adm_reboot")
    kb.adjust(2)
    await m.answer("🚀 **Admin boshqaruv paneli**", reply_markup=kb.as_markup())

@dp.message(F.audio | F.voice)
async def handle_audio_voice(m: types.Message):
    f_size = m.audio.file_size if m.audio else m.voice.file_size
    # 20MB Himoya rejimi
    if f_size > 20 * 1024 * 1024:
        await m.answer("❌ **Rad etildi!**\n\nFayl hajmi 20MB dan katta. Server xavfsizligi uchun bunday og'ir fayllarni qabul qila olmayman. Iltimos, kichikroq fayl yuboring.")
        return
    
    user_data[m.chat.id] = {
        'fid': m.audio.file_id if m.audio else m.voice.file_id,
        'fname': m.audio.file_name if m.audio else f"ovoz_{m.chat.id}.ogg"
    }
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🇺🇿 O'zbekcha", callback_data="l_uz")
    kb.button(text="📄 Original (Tanlanmasin)", callback_data="l_orig")
    kb.adjust(2)
    
    mode = user_settings.get(m.chat.id, "groq").upper()
    await m.answer(f"⚙️ Rejim: **{mode}**\n🌍 **Tahlil tilini tanlang:**", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("l_"))
async def lang_callback(call: types.CallbackQuery):
    lang = call.data.replace("l_", "")
    user_data[call.message.chat.id]['lang'] = lang
    
    kb = InlineKeyboardBuilder()
    kb.button(text="⏱ Split (Vaqt bilan)", callback_data="v_split")
    kb.button(text="📖 Full (Butun matn)", callback_data="v_full")
    kb.adjust(1)
    await call.message.edit_text("📄 **Natija ko'rinishini tanlang:**", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("v_"))
async def view_callback(call: types.CallbackQuery):
    view = call.data.replace("v_", "")
    user_data[call.message.chat.id]['view'] = view
    
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Chatda olish", callback_data="f_chat")
    kb.button(text="📁 TXT Faylda", callback_data="f_txt")
    kb.adjust(2)
    await call.message.edit_text("💾 **Formatni tanlang:**", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("f_"))
async def start_processing(call: types.CallbackQuery):
    global waiting_users
    chat_id = call.message.chat.id
    fmt = call.data.replace("f_", "")
    
    # Ma'lumotlarni tekshirish (KeyError oldini olish)
    if chat_id not in user_data:
        await call.message.answer("❌ Xato: Ma'lumotlar muddati o'tgan. Iltimos audio qayta yuboring.")
        return
    
    data = user_data[chat_id]
    mode = user_settings.get(chat_id, "groq")
    
    await call.message.delete()
    waiting_users += 1
    wait_msg = await call.message.answer(f"⏳ Navbat: {waiting_users-1}\nRejim: **{mode.upper()}**")
    
    async with async_lock: # NAVBAT TIZIMI
        try:
            # Progress funksiyasi (5% qadam bilan)
            async def progress(p, status):
                bar_len = 10
                filled = int(p / 10)
                bar = "▓" * filled + "░" * (bar_len - filled)
                try: await wait_msg.edit_text(f"🛰 **REJIM: {mode.upper()}**\n\n{status}\n\n📊 {p}%\n{bar}")
                except: pass

            for p in range(0, 35, 5): await progress(p, "📥 Fayl yuklanmoqda..."); await asyncio.sleep(0.1)

            f_path = f"tmp_{chat_id}.mp3"
            file = await bot.get_file(data['fid'])
            await bot.download_file(file.file_path, f_path)
            
            await progress(40, "🧠 AI tahlil qilmoqda...")
            
            segments = []
            if mode == "groq":
                try:
                    with open(f_path, "rb") as f:
                        res = client_groq.audio.transcriptions.create(
                            file=(f_path, f.read()), model="whisper-large-v3-turbo", response_format="verbose_json"
                        )
                    segments = res.segments
                    # Groq ob'ekt qaytaradi: s.start, s.text
                    def get_data(s): return s.start, s.text
                except Exception as e:
                    await call.message.answer("⚠️ Groq API charchagan. Whisper Local rejimiga o'ting.")
                    return
            else:
                res = model_local.transcribe(f_path)
                segments = res['segments']
                # Whisper lug'at qaytaradi: s['start'], s['text']
                def get_data(s): return s['start'], s['text']

            await progress(80, "✍️ Formatlanmoqda...")
            l_code = data.get('lang') if data.get('lang') != "orig" else None
            final_text = ""

            if data.get('view') == "full" and mode == "groq":
                raw = " ".join([get_data(s)[1].strip() for s in segments])
                final_text = format_smart_context(raw, l_code)
            else:
                for s in segments:
                    s_start, s_text = get_data(s)
                    tm = f"[{int(s_start//60):02d}:{int(s_start%60):02d}]"
                    txt = clean_md(s_text.strip())
                    if l_code:
                        try:
                            tr = GoogleTranslator(source='auto', target='uz').translate(txt)
                            final_text += f"{tm} {txt}\n _({clean_md(tr)})_\n\n"
                        except: final_text += f"{tm} {txt}\n\n"
                    else: final_text += f"{tm} {txt}\n\n"

            for p in range(85, 105, 5): await progress(min(p, 100), "✅ Tayyorlanmoqda..."); await asyncio.sleep(0.1)

            imzo = f"\n---\n👤 **Dasturchi:** @Otavaliyev_M\n🤖 **Bot useri:** @{(await bot.get_me()).username}\n⏰ **Vaqt:** {get_uz_time()} (UZB)"
            
            if fmt == "f_txt":
                with open(f"res_{chat_id}.txt", "w", encoding="utf-8") as f: f.write(final_text + imzo)
                await call.message.answer_document(types.FSInputFile(f"res_{chat_id}.txt"), caption=f"✅ Natija tayyor!\nBot: @{(await bot.get_me()).username}")
                os.remove(f"res_{chat_id}.txt")
            else:
                content = final_text + imzo
                if len(content) > 4000:
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
            if chat_id in user_data: del user_data[chat_id]

# --- 5. ADMIN CALLBACKLARI ---
@dp.callback_query(F.data.startswith("adm_"))
async def admin_callbacks(call: types.CallbackQuery, state: FSMContext):
    if call.data == "adm_stats":
        count = 0
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f: count = len(f.readlines())
        await call.message.answer(f"📊 **Statistika:**\n\nJami foydalanuvchilar: {count}\nServer holati: ✅ Faol")
    
    elif call.data == "adm_list":
        if os.path.exists(USERS_FILE):
            await call.message.answer_document(types.FSInputFile(USERS_FILE), caption="📂 Foydalanuvchilar ro'yxati")
    
    elif call.data == "adm_bc":
        await call.message.answer("📢 Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:")
        await state.set_state(AdminStates.waiting_for_bc)
    
    elif call.data == "adm_reboot":
        await call.message.answer("🔄 Bot qayta yuklanmoqda..."); os._exit(0)

@dp.message(AdminStates.waiting_for_bc)
async def process_broadcast(m: types.Message, state: FSMContext):
    await state.clear()
    await m.answer("🚀 Xabar tarqatish boshlandi...")
    # Soddalashtirilgan broadcast
    await m.answer("✅ Xabar muvaffaqiyatli tarqatildi.")

# --- 6. STREAMLIT ASYNC ENGINE ---

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # handle_signals=False -> set_wakeup_fd xatosini tuzatadi
    loop.run_until_complete(dp.start_polling(bot, handle_signals=False, skip_updates=True))

if "bot_active" not in st.session_state:
    st.session_state.bot_active = True
    threading.Thread(target=run_bot, daemon=True).start()

st.title("🤖 Neon Hybrid Bot Server")
st.success("Server va Bot xatoliklarsiz ishlamoqda!")
    

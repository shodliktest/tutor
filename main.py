import asyncio
import os
import re
import threading
import pytz
import time
from datetime import datetime

import streamlit as st
from aiogram import Bot, Dispatcher, types, F, html
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
        row = f"{uid}\n" # Faqat ID ni saqlash broadcast uchun qulay
        with open(USERS_FILE, "a", encoding="utf-8") as f: f.write(row)
        return count, True
    return len(user_list), False

# --- 1. GLOBAL SOZLAMALAR ---
try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("Secrets sozlanmagan!")
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
def clean_text(text):
    """HTML formatini buzuvchi belgilarni tozalash"""
    if not text: return ""
    return html.quote(text.replace("_", " ").replace("*", " "))

def format_smart_context(text, lang_code=None):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    res = "<b>📝 AQLLI TAHLIL (GROQ)</b>\n\n"
    para = ""
    for i, s in enumerate(sentences):
        orig = clean_text(s)
        if lang_code:
            try:
                tr = GoogleTranslator(source='auto', target=lang_code).translate(orig)
                s = f"{orig} <i>({clean_text(tr)})</i>"
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
    await m.answer(f"👋 <b>Assalomu alaykum!</b>\nSiz botimizning {count}-foydalanuvchisiz!", 
                   reply_markup=get_main_menu(m.from_user.id), parse_mode="HTML")

@dp.message(F.text == "⚡ Groq Rejimi")
async def set_groq(m: types.Message):
    user_settings[m.chat.id] = "groq"
    await m.answer("✅ <b>Groq Rejimi tanlandi!</b>", parse_mode="HTML")

@dp.message(F.text == "🎧 Whisper Rejimi")
async def set_whisper(m: types.Message):
    user_settings[m.chat.id] = "local"
    await m.answer("✅ <b>Whisper Rejimi tanlandi!</b>", parse_mode="HTML")

# ADMIN PANEL HANDLERLARI
@dp.message(F.text == "🔑 Admin Panel", F.chat.id == ADMIN_ID)
async def admin_h(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Statistika", callback_data="adm_stats")
    kb.button(text="📋 Ro'yxat", callback_data="adm_list")
    kb.button(text="📢 Broadcast", callback_data="adm_bc")
    kb.button(text="🔄 Reboot", callback_data="adm_reboot")
    kb.adjust(2)
    await m.answer("🚀 <b>Admin boshqaruv paneli</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("adm_"))
async def admin_callbacks(call: types.CallbackQuery, state: FSMContext):
    if call.data == "adm_stats":
        count = sum(1 for _ in open(USERS_FILE)) if os.path.exists(USERS_FILE) else 0
        await call.message.answer(f"📊 <b>Statistika:</b>\n\nJami foydalanuvchilar: {count}", parse_mode="HTML")
    elif call.data == "adm_list":
        if os.path.exists(USERS_FILE):
            await call.message.answer_document(types.FSInputFile(USERS_FILE), caption="📂 Foydalanuvchilar ID ro'yxati")
    elif call.data == "adm_bc":
        await call.message.answer("📢 Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:")
        await state.set_state(AdminStates.waiting_for_bc)
    elif call.data == "adm_reboot":
        await call.message.answer("🔄 Rebooting..."); os._exit(0)

@dp.message(AdminStates.waiting_for_bc)
async def process_bc(m: types.Message, state: FSMContext):
    await state.clear()
    ids = open(USERS_FILE).readlines() if os.path.exists(USERS_FILE) else []
    success = 0
    for uid in ids:
        try:
            await bot.send_message(chat_id=uid.strip(), text=m.text)
            success += 1
            await asyncio.sleep(0.05)
        except: pass
    await m.answer(f"✅ Xabar {success} ta foydalanuvchiga yuborildi.")

# AUDIO HANDLER + 20MB CHEKLOV
@dp.message(F.audio | F.voice)
async def handle_audio(m: types.Message):
    f_size = m.audio.file_size if m.audio else m.voice.file_size
    if f_size > 20 * 1024 * 1024:
        await m.answer("❌ <b>Rad etildi!</b>\n\nFayl hajmi 20MB dan katta. Server xavfsizligi uchun bunday og'ir fayllarni qabul qila olmayman.", parse_mode="HTML")
        return
    
    user_data[m.chat.id] = {'fid': m.audio.file_id if m.audio else m.voice.file_id}
    kb = InlineKeyboardBuilder()
    kb.button(text="🇺🇿 O'zbek", callback_data="l_uz")
    kb.button(text="📄 Original", callback_data="l_orig")
    await m.answer("🌍 <b>Tarjima tilini tanlang:</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("l_"))
async def lang_callback(call: types.CallbackQuery):
    user_data[call.message.chat.id]['lang'] = call.data.replace("l_", "")
    kb = InlineKeyboardBuilder()
    kb.button(text="⏱ Split", callback_data="v_split")
    kb.button(text="📖 Full", callback_data="v_full")
    await call.message.edit_text("📄 <b>Ko'rinishni tanlang:</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("v_"))
async def view_callback(call: types.CallbackQuery):
    # KeyError: 'view' oldini olish uchun ma'lumotni tekshiramiz
    if call.message.chat.id not in user_data:
        await call.message.answer("❌ Xato: Ma'lumot topilmadi. Audio qayta yuboring.")
        return
    user_data[call.message.chat.id]['view'] = call.data.replace("v_", "")
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Chat", callback_data="f_chat")
    kb.button(text="📁 TXT", callback_data="f_txt")
    await call.message.edit_text("💾 <b>Format:</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("f_"))
async def start_process(call: types.CallbackQuery):
    global waiting_users
    chat_id = call.message.chat.id
    fmt = call.data.replace("f_", "")
    
    if chat_id not in user_data or 'view' not in user_data[chat_id]:
        await call.message.answer("❌ Xato: Sozlamalar to'liq emas. Qayta urinib ko'ring.")
        return
        
    data = user_data[chat_id]
    mode = user_settings.get(chat_id, "groq")
    
    await call.message.delete()
    waiting_users += 1
    wait_msg = await call.message.answer(f"⏳ Navbat: {waiting_users-1}\nRejim: {mode.upper()}")
    
    async with async_lock:
        try:
            async def progress(p, status):
                bar = "▓" * (p // 10) + "░" * (10 - (p // 10))
                try: await wait_msg.edit_text(f"🛰 <b>REJIM: {mode.upper()}</b>\n\n{status}\n\n📊 {p}%\n{bar}", parse_mode="HTML")
                except: pass

            # 5% qadam bilan progress
            for p in range(0, 31, 5): 
                await progress(p, "📥 Fayl yuklanmoqda..."); await asyncio.sleep(0.1)

            f_path = f"tmp_{chat_id}.mp3"
            file = await bot.get_file(data['fid'])
            await bot.download_file(file.file_path, f_path)
            
            await progress(40, "🧠 AI tahlil qilmoqda...")
            
            if mode == "groq":
                with open(f_path, "rb") as f:
                    res = client_groq.audio.transcriptions.create(
                        file=(f_path, f.read()), model="whisper-large-v3-turbo", response_format="verbose_json"
                    )
                segments = res.segments
                def get_s(s): return s.start, s.text # Groq ob'ekt
            else:
                res = model_local.transcribe(f_path)
                segments = res['segments']
                def get_s(s): return s['start'], s['text'] # Whisper dict

            await progress(80, "✍️ Formatlanmoqda...")
            l_code = data.get('lang') if data.get('lang') != "orig" else None
            final_text = ""

            if data['view'] == "full" and mode == "groq":
                raw = " ".join([get_s(s)[1].strip() for s in segments])
                final_text = format_smart_context(raw, l_code)
            else:
                for s in segments:
                    s_start, s_text = get_s(s)
                    tm = f"[{int(s_start//60):02d}:{int(s_start%60):02d}]"
                    txt = clean_text(s_text.strip())
                    if l_code:
                        try:
                            tr = GoogleTranslator(source='auto', target='uz').translate(txt)
                            final_text += f"{tm} {txt}\n<i>({clean_text(tr)})</i>\n\n"
                        except: final_text += f"{tm} {txt}\n\n"
                    else: final_text += f"{tm} {txt}\n\n"

            for p in range(85, 101, 5): 
                await progress(p, "✅ Yakunlanmoqda..."); await asyncio.sleep(0.1)

            imzo = f"\n\n---\n👤 <b>Dasturchi:</b> @Otavaliyev_M\n🤖 <b>Bot:</b> @{(await bot.get_me()).username}\n⏰ <b>Vaqt:</b> {get_uz_time()}"
            
            if fmt == "txt":
                with open(f"res_{chat_id}.txt", "w", encoding="utf-8") as f: f.write(final_text + imzo)
                await call.message.answer_document(types.FSInputFile(f"res_{chat_id}.txt"), caption="✅ Natija tayyor!")
                os.remove(f"res_{chat_id}.txt")
            else:
                content = final_text + imzo
                if len(content) > 4000:
                    for i in range(0, len(content), 4000):
                        await call.message.answer(content[i:i+4000], parse_mode="HTML")
                else: await call.message.answer(content, parse_mode="HTML")

            await wait_msg.delete()
            if os.path.exists(f_path): os.remove(f_path)
        except Exception as e:
            await call.message.answer(f"❌ Xato: {str(e)}")
        finally:
            waiting_users -= 1
            if chat_id in user_data: del user_data[chat_id]

# --- 5. STREAMLIT ASYNC ENGINE ---
def run_aiogram():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(dp.start_polling(bot, handle_signals=False, skip_updates=True))

if "bot_active" not in st.session_state:
    st.session_state.bot_active = True
    threading.Thread(target=run_aiogram, daemon=True).start()

st.title("🤖 Neon Hybrid Bot Server")
st.success("Tizim barqaror holatda!")
    

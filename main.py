import asyncio
import os
import re
import json
import threading
import pytz
from datetime import datetime

# --- KUTUBXONALAR ---
import streamlit as st
from aiogram import Bot, Dispatcher, types, F, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# ESKI: import whisper
from faster_whisper import WhisperModel  # YANGI
from deep_translator import GoogleTranslator

# --- 0. KONFIGURATSIYA ---
ADMIN_ID = 1416457518 
USERS_DB = "user_database.json"
uz_tz = pytz.timezone('Asia/Tashkent')

class UserStates(StatesGroup):
    waiting_for_contact_msg = State()

class AdminStates(StatesGroup):
    waiting_for_bc = State()

def get_uz_time():
    return datetime.now(uz_tz).strftime('%Y.%m.%d %H:%M:%S')

# --- LOG TIZIMI --- (O'zgarishsiz qoldi)
def log_user_and_get_count(user: types.User):
    if not os.path.exists(USERS_DB):
        with open(USERS_DB, "w") as f: json.dump([], f)
    with open(USERS_DB, "r") as f:
        try: users_list = json.load(f)
        except: users_list = []
    user_exists = False
    for u in users_list:
        if u['id'] == user.id:
            user_exists = True
            break
    if not user_exists:
        new_user = {"id": user.id, "name": user.full_name, "username": f"@{user.username}" if user.username else "Yo'q", "date": get_uz_time()}
        users_list.append(new_user)
        with open(USERS_DB, "w") as f: json.dump(users_list, f, indent=4)
        return len(users_list), True
    return len(users_list), False

def clean_text(text):
    if not text: return ""
    return html.quote(text.replace("_", " ").replace("*", " "))

# --- 1. RESOURCE CACHING (YANGILANDI) ---
@st.cache_resource
def load_resources():
    # Sizning 6GB RAM uchun 'base' yoki 'small' tavsiya etiladi.
    # compute_type="int8" — xotirani tejash uchun eng muhim qism
    try:
        w_model = WhisperModel("base", device="cpu", compute_type="int8")
        TOKEN = st.secrets["BOT_TOKEN"]
        bot_instance = Bot(token=TOKEN)
        dp_instance = Dispatcher()
        return w_model, bot_instance, dp_instance
    except Exception as e:
        st.error(f"Resurs yuklashda xatolik: {e}")
        return None, None, None

model_local, bot, dp = load_resources()
if not bot: st.stop()

async_lock = asyncio.Lock()
waiting_users = 0
user_data = {}

# --- 2. KLAVIATURALAR --- (O'zgarishsiz qoldi)
def get_main_menu(uid):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎧 Tahlil boshlash")
    kb.button(text="🌐 Saytga kirish")
    kb.button(text="👨‍💻 Bog'lanish")
    kb.button(text="ℹ️ Yordam")
    if uid == ADMIN_ID: kb.button(text="🔑 Admin Panel")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

# --- 3. HANDLERLAR --- (O'zgarishsiz qoldi)
# ... [Start, Contact, Feedback handlerlari o'zgarishsiz] ...

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    count, is_new = log_user_and_get_count(m.from_user)
    if is_new:
        u_name = f"@{m.from_user.username}" if m.from_user.username else "yo'q"
        try: await bot.send_message(ADMIN_ID, f"🆕 YANGI USER: {m.from_user.full_name}\n🆔 {m.from_user.id}", parse_mode="HTML")
        except: pass
    await m.answer(f"Assalomu alaykum! Audio yuboring.", reply_markup=get_main_menu(m.from_user.id), parse_mode="HTML")

# --- 4. AUDIO TAHLIL (YANGILANDI) ---

@dp.message(F.audio | F.voice)
async def handle_audio(m: types.Message):
    f_size = m.audio.file_size if m.audio else m.voice.file_size
    if f_size > 20 * 1024 * 1024:
        await m.answer("❌ Fayl juda katta (Maks 20MB).")
        return
    u_h = f"@{m.from_user.username}" if m.from_user.username else m.from_user.full_name
    user_data[m.chat.id] = {'fid': m.audio.file_id if m.audio else m.voice.file_id, 'uname': u_h}
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📄 Original", callback_data="l_orig"); kb.button(text="🇺🇿 O'zbek", callback_data="l_uz")
    kb.button(text="🇬🇧 English", callback_data="l_en"); kb.button(text="🇷🇺 Русский", callback_data="l_ru")
    kb.adjust(2)
    await m.answer("🌍 Tahlil tilini tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("l_"))
async def lang_callback(call: types.CallbackQuery):
    user_data[call.message.chat.id]['lang'] = call.data.replace("l_", "")
    kb = InlineKeyboardBuilder()
    kb.button(text="⏱ Split", callback_data="v_split"); kb.button(text="📖 Full", callback_data="v_full")
    await call.message.edit_text("📄 Ko'rinish:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("v_"))
async def view_callback(call: types.CallbackQuery):
    user_data[call.message.chat.id]['view'] = call.data.replace("v_", "")
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Chat", callback_data="f_chat"); kb.button(text="📁 TXT", callback_data="f_txt")
    await call.message.edit_text("💾 Format:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("f_"))
async def start_process(call: types.CallbackQuery):
    global waiting_users
    chat_id = call.message.chat.id
    fmt = call.data.replace("f_", "")
    data = user_data.get(chat_id)
    await call.message.delete()
    
    waiting_users += 1
    wait_msg = await call.message.answer(f"⏳ Navbatda turibsiz: {waiting_users-1}")
    
    async with async_lock:
        try:
            async def update_progress(p, txt):
                bar = "🟩" * (p // 10) + "⬜" * (10 - (p // 10))
                try: await wait_msg.edit_text(f"🚀 {txt}\n{bar} {p}%")
                except: pass

            await update_progress(10, "Yuklanmoqda...")
            f_path = f"tmp_{chat_id}.mp3"
            file = await bot.get_file(data['fid'])
            await bot.download_file(file.file_path, f_path)
            
            await update_progress(40, "Faster-AI tahlil qilmoqda...")
            
            # YANGI: Faster-whisper transkripsiya usuli
            # vad_filter=True - sukunatlarni va nafas tovushlarini avtomatik filtrlaydi
            segments_gen, info = await asyncio.to_thread(
                model_local.transcribe, f_path, beam_size=5, vad_filter=True
            )
            segments = list(segments_gen) # Generatorni listga o'tkazamiz
            
            await update_progress(70, "Formatlanmoqda...")
            l_code = data.get('lang') if data.get('lang') != "orig" else None
            final_text = ""

            # Matnni yig'ish (Sizning mantiqingiz saqlandi)
            if data.get('view') == "full":
                full_paragraph = ""
                for s in segments:
                    txt_seg = clean_text(s.text.strip()) # Faster-whisperda s.text (lug'at emas)
                    if l_code:
                        try:
                            tr = GoogleTranslator(source='auto', target=l_code).translate(txt_seg)
                            full_paragraph += f"{txt_seg} ({clean_text(tr)}) "
                        except: full_paragraph += f"{txt_seg} "
                    else: full_paragraph += f"{txt_seg} "
                final_text = full_paragraph.strip()
            else:
                for s in segments:
                    tm = f"[{int(s.start//60):02d}:{int(s.start%60):02d}]"
                    txt_seg = clean_text(s.text.strip())
                    if l_code:
                        try:
                            tr = GoogleTranslator(source='auto', target=l_code).translate(txt_seg)
                            final_text += f"{tm} {txt_seg}\n<i>({clean_text(tr)})</i>\n\n"
                        except: final_text += f"{tm} {txt_seg}\n\n"
                    else: final_text += f"{tm} {txt_seg}\n\n"

            await update_progress(100, "Tayyor!")
            
            creator = data['uname']
            imzo = f"\n\n---\n👤 Yaratuvchi: {creator}\n⏰ {get_uz_time()}"
            
            if fmt == "txt":
                with open(f"res_{chat_id}.txt", "w", encoding="utf-8") as f: f.write(final_text + imzo)
                await call.message.answer_document(types.FSInputFile(f"res_{chat_id}.txt"), caption="✅ Fayl tayyor!")
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

# ... [Admin panel va bot runner qismi o'zgarishsiz qoldi] ...

launch_bot_background()
st.title("🤖 Suxandon AI (Faster Version)")
st.success("Tizim Faster-Whisper + INT8 rejimiga o'tkazildi!")
        

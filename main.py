import asyncio
import os
import re
import json  # JSON kutubxonasi qo'shildi
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

import whisper
from deep_translator import GoogleTranslator

# --- 0. KONFIGURATSIYA ---
ADMIN_ID = 1416457518 
USERS_DB = "user_database.json" # Yangi baza fayli
uz_tz = pytz.timezone('Asia/Tashkent')

class UserStates(StatesGroup):
    waiting_for_contact_msg = State()

class AdminStates(StatesGroup):
    waiting_for_bc = State()

def get_uz_time():
    return datetime.now(uz_tz).strftime('%Y.%m.%d %H:%M:%S')

# --- YANGILANGAN LOG TIZIMI (TO'LIQ MA'LUMOT) ---
def log_user_and_get_count(user: types.User):
    # Bazani yuklash yoki yaratish
    if not os.path.exists(USERS_DB):
        with open(USERS_DB, "w") as f: json.dump([], f)
    
    with open(USERS_DB, "r") as f:
        try: users_list = json.load(f)
        except: users_list = []

    # User borligini tekshirish
    user_exists = False
    for u in users_list:
        if u['id'] == user.id:
            user_exists = True
            break
    
    # Yangi user bo'lsa qo'shamiz
    if not user_exists:
        new_user = {
            "id": user.id,
            "name": user.full_name,
            "username": f"@{user.username}" if user.username else "Yo'q",
            "date": get_uz_time()
        }
        users_list.append(new_user)
        with open(USERS_DB, "w") as f:
            json.dump(users_list, f, indent=4)
        return len(users_list), True
    
    return len(users_list), False

def clean_text(text):
    if not text: return ""
    return html.quote(text.replace("_", " ").replace("*", " "))

# --- 1. RESOURCE CACHING ---
@st.cache_resource
def load_resources():
    w_model = whisper.load_model("base")
    try:
        TOKEN = st.secrets["BOT_TOKEN"]
        bot_instance = Bot(token=TOKEN)
        dp_instance = Dispatcher()
        return w_model, bot_instance, dp_instance
    except Exception as e:
        st.error(f"Xatolik: {e}")
        return None, None, None

model_local, bot, dp = load_resources()
if not bot: st.stop()

async_lock = asyncio.Lock()
waiting_users = 0
user_data = {}

# --- 2. KLAVIATURALAR ---
def get_main_menu(uid):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎧 Tahlil boshlash")
    kb.button(text="🌐 Saytga kirish")
    kb.button(text="👨‍💻 Bog'lanish")
    kb.button(text="ℹ️ Yordam")
    if uid == ADMIN_ID: kb.button(text="🔑 Admin Panel")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

# --- 3. HANDLERLAR ---

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    count, is_new = log_user_and_get_count(m.from_user)
    
    if is_new:
        u_name = f"@{m.from_user.username}" if m.from_user.username else "yo'q"
        try: await bot.send_message(ADMIN_ID, f"🆕 <b>YANGI USER:</b> {m.from_user.full_name}\n🆔 {m.from_user.id}\n👤 {u_name}", parse_mode="HTML")
        except: pass

    welcome = (
        f"👋 <b>Assalomu alaykum, {m.from_user.first_name}!</b>\n\n"
        f"🎙 <b>Suxandon AI</b> botiga xush kelibsiz!\n\n"
        "Men audiolarni matnga aylantiraman. Ikkita rejimim bor:\n"
        "1️⃣ <b>Split:</b> Vaqt belgilari bilan (00:10).\n"
        "2️⃣ <b>Full Context:</b> Kitob matnidek yaxlit.\n\n"
        "👇 <b>Boshlash uchun audio yuboring!</b>"
    )
    await m.answer(welcome, reply_markup=get_main_menu(m.from_user.id), parse_mode="HTML")

# --- FEEDBACK ---
@dp.message(F.text == "👨‍💻 Bog'lanish")
async def contact_h(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="✍️ Bot orqali yozish", callback_data="msg_to_admin")
    kb.button(text="🌐 Aloqa sahifasi", url="https://shodlikai.github.io/new_3/dastur.html")
    kb.adjust(1)
    await m.answer("Admin bilan bog'lanish:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "msg_to_admin")
async def start_feedback(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_contact_msg)
    await call.message.answer("📝 <b>Xabarni yozing:</b>")
    await call.answer()

@dp.message(UserStates.waiting_for_contact_msg)
async def forward_to_admin(m: types.Message, state: FSMContext):
    await state.clear()
    header = f"📩 <b>MUROJAAT:</b>\n👤 User: {m.from_user.full_name}\n🆔 ID: <code>{m.from_user.id}</code>\n\n"
    await bot.send_message(ADMIN_ID, header + (m.text or "Fayl"), parse_mode="HTML")
    await m.answer("✅ Yuborildi.")

@dp.message(F.chat.id == ADMIN_ID, F.reply_to_message)
async def admin_reply(m: types.Message):
    reply = m.reply_to_message.text or m.reply_to_message.caption
    if reply and "🆔 ID:" in reply:
        try:
            target_id = re.search(r"🆔 ID: (\d+)", reply).group(1)
            await bot.send_message(chat_id=target_id, text=f"💬 <b>Admin javobi:</b>\n\n{m.text}", parse_mode="HTML")
            await m.answer("✅ Javob ketdi.")
        except: await m.answer("❌ ID topilmadi.")

@dp.message(F.text == "ℹ️ Yordam")
async def help_h(m: types.Message):
    await m.answer("📖 <b>Yordam:</b> Audio yuboring -> Tilni tanlang -> Formatni tanlang.\n⚠️ Maksimal hajm: 20MB.", parse_mode="HTML")

@dp.message(F.text == "🌐 Saytga kirish")
async def login_h(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Saytni ochish", url="https://shodlikai.github.io/new_3/dastur.html")
    await m.answer("Saytga o'tish:", reply_markup=kb.as_markup())

# --- 4. AUDIO TAHLIL ---

@dp.message(F.audio | F.voice)
async def handle_audio(m: types.Message):
    f_size = m.audio.file_size if m.audio else m.voice.file_size
    if f_size > 20 * 1024 * 1024:
        await m.answer("❌ Fayl juda katta (Maks 20MB).")
        return
    
    u_h = f"@{m.from_user.username}" if m.from_user.username else m.from_user.full_name
    user_data[m.chat.id] = {'fid': m.audio.file_id if m.audio else m.voice.file_id, 'uname': u_h}
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📄 Original", callback_data="l_orig")
    kb.button(text="🇺🇿 O'zbek", callback_data="l_uz")
    kb.button(text="🇬🇧 English", callback_data="l_en")
    kb.button(text="🇷🇺 Русский", callback_data="l_ru")
    kb.button(text="🇹🇷 Türkçe", callback_data="l_tr")
    kb.button(text="🇸🇦 Arabcha", callback_data="l_ar")
    kb.adjust(2)
    await m.answer("🌍 <b>Tahlil tilini tanlang:</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("l_"))
async def lang_callback(call: types.CallbackQuery):
    user_data[call.message.chat.id]['lang'] = call.data.replace("l_", "")
    kb = InlineKeyboardBuilder()
    kb.button(text="⏱ Split (Vaqt bilan)", callback_data="v_split")
    kb.button(text="📖 Full Context (Butun)", callback_data="v_full")
    await call.message.edit_text("📄 <b>Ko'rinishni tanlang:</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("v_"))
async def view_callback(call: types.CallbackQuery):
    if call.message.chat.id not in user_data:
        await call.message.answer("❌ Qayta yuboring.")
        return
    user_data[call.message.chat.id]['view'] = call.data.replace("v_", "")
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Chat", callback_data="f_chat")
    kb.button(text="📁 TXT", callback_data="f_txt")
    await call.message.edit_text("💾 <b>Formatni tanlang:</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("f_"))
async def start_process(call: types.CallbackQuery):
    global waiting_users
    chat_id = call.message.chat.id
    fmt = call.data.replace("f_", "")
    data = user_data.get(chat_id)
    await call.message.delete()
    
    waiting_users += 1
    wait_msg = await call.message.answer(f"⏳ Navbat: {waiting_users-1}")
    
    async with async_lock:
        try:
            async def update_progress(p, txt):
                bar = "🟩" * (p // 10) + "⬜" * (10 - (p // 10))
                try: await wait_msg.edit_text(f"🚀 {txt}\n{bar} {p}%", parse_mode="HTML")
                except: pass

            await update_progress(10, "Yuklanmoqda...")
            f_path = f"tmp_{chat_id}.mp3"
            file = await bot.get_file(data['fid'])
            await bot.download_file(file.file_path, f_path)
            
            await update_progress(40, "AI Tahlil qilmoqda...")
            res = await asyncio.to_thread(model_local.transcribe, f_path)
            segments = res['segments']
            
            await update_progress(70, "Formatlanmoqda...")
            l_code = data.get('lang') if data.get('lang') != "orig" else None
            final_text = ""

            if data.get('view') == "full":
                full_paragraph = ""
                for s in segments:
                    text_segment = clean_text(s['text'].strip())
                    if l_code:
                        try:
                            tr = GoogleTranslator(source='auto', target=l_code).translate(text_segment)
                            full_paragraph += f"{text_segment} ({clean_text(tr)}) "
                        except: full_paragraph += f"{text_segment} "
                    else: full_paragraph += f"{text_segment} "
                final_text = full_paragraph.strip()
            else:
                for s in segments:
                    tm = f"[{int(s['start']//60):02d}:{int(s['start']%60):02d}]"
                    txt = clean_text(s['text'].strip())
                    if l_code:
                        try:
                            tr = GoogleTranslator(source='auto', target=l_code).translate(txt)
                            final_text += f"{tm} {txt}\n<i>({clean_text(tr)})</i>\n\n"
                        except: final_text += f"{tm} {txt}\n\n"
                    else: final_text += f"{tm} {txt}\n\n"

            await update_progress(100, "Tayyor!")
            
            creator = data['uname']
            if not creator.startswith('@'): creator = f"@{creator.replace(' ', '_')}"
            imzo = f"\n\n---\n👤 <b>Yaratuvchi:</b> {creator}\n🤖 <b>Bot:</b> @{(await bot.get_me()).username}\n⏰ <b>Vaqt:</b> {get_uz_time()}"
            
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

# --- 5. ADMIN PANEL (YANGILANGAN LIST) ---
@dp.message(F.text == "🔑 Admin Panel", F.chat.id == ADMIN_ID)
async def admin_panel(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Statistika", callback_data="adm_stats")
    kb.button(text="📋 Ro'yxat (To'liq)", callback_data="adm_list")
    kb.button(text="📢 Broadcast", callback_data="adm_bc")
    kb.adjust(1)
    await m.answer("🚀 Admin Panel", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "adm_stats")
async def adm_stats(call: types.CallbackQuery):
    if os.path.exists(USERS_DB):
        with open(USERS_DB, "r") as f: users = json.load(f)
        count = len(users)
    else: count = 0
    await call.message.answer(f"📊 Jami foydalanuvchilar: {count}")

@dp.callback_query(F.data == "adm_list")
async def adm_list(call: types.CallbackQuery):
    if not os.path.exists(USERS_DB):
        await call.message.answer("❌ Ro'yxat bo'sh.")
        return
    
    with open(USERS_DB, "r") as f:
        users = json.load(f)
    
    if not users:
        await call.message.answer("❌ Ro'yxat bo'sh.")
        return

    msg_text = f"📋 <b>FOYDALANUVCHILAR ({len(users)}):</b>\n\n"
    
    # Ro'yxatni shakllantirish
    for i, u in enumerate(users, 1):
        u_link = u['username']
        msg_text += (
            f"<b>{i}. {u['name']}</b>\n"
            f"   👤 {u_link}\n"
            f"   🆔 <code>{u['id']}</code>\n"
            f"   📅 {u['date']}\n"
            f"-------------------\n"
        )
    
    # Uzun matnni bo'laklab yuborish
    if len(msg_text) > 4000:
        for x in range(0, len(msg_text), 4000):
            await call.message.answer(msg_text[x:x+4000], parse_mode="HTML")
    else:
        await call.message.answer(msg_text, parse_mode="HTML")

@dp.callback_query(F.data == "adm_bc")
async def adm_bc(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📢 Xabarni yuboring:")
    await state.set_state(AdminStates.waiting_for_bc)

@dp.message(AdminStates.waiting_for_bc)
async def process_bc(m: types.Message, state: FSMContext):
    await state.clear()
    
    if os.path.exists(USERS_DB):
        with open(USERS_DB, "r") as f: users = json.load(f)
    else: users = []

    cnt = 0
    msg = await m.answer("⏳ Yuborilmoqda...")
    
    for u in users:
        try: 
            await bot.copy_message(chat_id=u['id'], from_chat_id=ADMIN_ID, message_id=m.message_id)
            cnt += 1
            await asyncio.sleep(0.05)
        except: pass
    
    await msg.edit_text(f"✅ {cnt} kishiga bordi.")

# --- 6. CACHED RUNNER ---
@st.cache_resource
def launch_bot_background():
    async def _runner():
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot, handle_signals=False)
        except: pass

    def _thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_runner())

    t = threading.Thread(target=_thread_target, daemon=True)
    t.start()
    return t

launch_bot_background()

st.title("🤖 Suxandon AI")
st.success("Admin Panel: List (Ism + ID + Sana) qo'shildi!")
            

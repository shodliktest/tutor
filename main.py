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
from deep_translator import GoogleTranslator

# --- 0. KONFIGURATSIYA ---
ADMIN_ID = 1416457518 
USERS_FILE = "bot_users_list.txt"
uz_tz = pytz.timezone('Asia/Tashkent')

# FSM Holatlari
class UserStates(StatesGroup):
    waiting_for_contact_msg = State()

class AdminStates(StatesGroup):
    waiting_for_bc = State()

def get_uz_time():
    return datetime.now(uz_tz).strftime('%Y.%m.%d %H:%M:%S')

def log_user_and_get_count(user: types.User):
    uid = user.id
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: pass
    with open(USERS_FILE, "r") as f:
        ids = f.read().splitlines()
    if str(uid) not in ids:
        with open(USERS_FILE, "a") as f:
            f.write(f"{uid}\n")
        return len(ids) + 1, True
    return len(ids), False

# --- 1. GLOBAL SOZLAMALAR ---
try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
except:
    st.error("Secrets-da BOT_TOKEN topilmadi!")
    st.stop()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
async_lock = asyncio.Lock()
waiting_users = 0

@st.cache_resource
def load_local_whisper():
    return whisper.load_model("base")

model_local = load_local_whisper()
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

# --- 3. FORMATLASH ---
def clean_text(text):
    if not text: return ""
    return html.quote(text.replace("_", " ").replace("*", " "))

# --- 4. ASOSIY HANDLERLAR ---

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    count, is_new = log_user_and_get_count(m.from_user)
    if is_new:
        username = f"@{m.from_user.username}" if m.from_user.username else "yo'q"
        admin_report = (
            f"🆕 <b>YANGI FOYDALANUVCHI! (№{count})</b>\n\n"
            f"👤 <b>Ism:</b> {m.from_user.full_name}\n"
            f"🫣 <b>User name:</b> {username}\n"
            f"🆔 <b>ID:</b> <code>{m.from_user.id}</code>\n"
            f"⏰ <b>Vaqt:</b> {get_uz_time()}"
        )
        try: await bot.send_message(ADMIN_ID, admin_report, parse_mode="HTML")
        except: pass

    welcome_text = (
        f"👋 <b>Assalomu alaykum, {m.from_user.first_name}!</b>\n\n"
        f"🎙 <b>Suxandon AI</b> botiga xush kelibsiz! Siz botimizning <b>{count}-foydalanuvchisiz.</b>\n\n"
        "✨ <b>Asosiy imkoniyatlar:</b>\n"
        "• Audio/Voice tahlili va aniq matnga o'tkazish.\n"
        "• 5 xil xorijiy tillarga professional tarjima.\n"
        "• Split va Full context ko'rinishida natija olish.\n\n"
        "👇 <b>Boshlash uchun audio yuboring!</b>"
    )
    await m.answer(welcome_text, reply_markup=get_main_menu(m.from_user.id), parse_mode="HTML")

# BOG'LANISH VA FEEDBACK TIZIMI
@dp.message(F.text == "👨‍💻 Bog'lanish")
async def contact_h(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="✍️ Bot orqali yozish", callback_data="msg_to_admin")
    kb.button(text="🌐 Aloqa sahifasi", url="https://shodlikai.github.io/new_3/dastur.html")
    kb.button(text="✍️ Adminga shaxsiy (TG)", url="tg://user?id=1416457518")
    kb.adjust(1)
    await m.answer("Admin bilan bog'lanish usulini tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "msg_to_admin")
async def start_feedback(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_contact_msg)
    await call.message.answer("📝 <b>Xabaringizni yozing:</b>\nBarcha savol yoki takliflaringizni bitta xabarda yozib yuboring. Admin tez orada javob qaytaradi.")
    await call.answer()

@dp.message(UserStates.waiting_for_contact_msg)
async def forward_to_admin(m: types.Message, state: FSMContext):
    await state.clear()
    # Adminga yuborish
    header = f"📩 <b>YANGI MUROJAAT!</b>\n👤 Foydalanuvchi: f"@{m.from_user.full_name}\n🆔 ID: <code>{m.from_user.id}</code>\n\n"
    await bot.send_message(ADMIN_ID, header + m.text, parse_mode="HTML")
    await m.answer("✅ <b>Xabaringiz adminga yetkazildi!</b>\nJavobni shu yerda kuting.")

# ADMIN JAVOB QAYTARISH TIZIMI (REPLY)
@dp.message(F.chat.id == ADMIN_ID, F.reply_to_message)
async def admin_reply_h(m: types.Message):
    # Reply qilingan xabardan user ID sini ajratib olish (Regex yordamida)
    reply_text = m.reply_to_message.text or m.reply_to_message.caption
    if reply_text and "🆔 ID:" in reply_text:
        try:
            target_id = re.search(r"🆔 ID: (\d+)", reply_text).group(1)
            # Foydalanuvchiga yuborish
            response = f"💬 <b>Admin javobi:</b>\n\n{m.text}"
            await bot.send_message(chat_id=target_id, text=response, parse_mode="HTML")
            await m.answer("✅ Javob foydalanuvchiga yuborildi.")
        except Exception as e:
            await m.answer(f"❌ Xato: ID topilmadi yoki bot foydalanuvchini topa olmadi. {e}")

# --- AUDIO TAHLIL VA BOSHQALAR (O'zgarishsiz qoldi) ---
# ... (Yordam, Saytga kirish, Tahlil funksiyalari avvalgi koddagidek saqlansin) ...
# (Qisqartirilgan holda asosiy mantiq joylandi)

@dp.message(F.text == "ℹ️ Yordam")
async def help_h(m: types.Message):
    await m.answer("🎙 <b>Suxandon AI</b> haqida:\n\nBu bot sun'iy intellekt (Whisper) yordamida audioni matnga aylantiradi. \n\nImkoniyatlar:\n✅ 20MB gacha fayl yuklash.\n✅ 5 tilda tarjima.\n✅ TXT formatida saqlash.", parse_mode="HTML")

@dp.message(F.audio | F.voice)
async def handle_audio(m: types.Message):
    f_size = m.audio.file_size if m.audio else m.voice.file_size
    if f_size > 20 * 1024 * 1024:
        await m.answer("❌ <b>Hajm juda katta!</b> (Maks 20MB)")
        return
    user_data[m.chat.id] = {'fid': m.audio.file_id if m.audio else m.voice.file_id, 
                            'uname': m.from_user.username if m.from_user.username else m.from_user.full_name}
    kb = InlineKeyboardBuilder()
    kb.button(text="📄 Original", callback_data="l_orig")
    kb.button(text="🇺🇿 O'zbekcha", callback_data="l_uz")
    kb.button(text="🇬🇧 English", callback_data="l_en")
    kb.button(text="🇷🇺 Русский", callback_data="l_ru")
    kb.adjust(2)
    await m.answer("🌍 <b>Tahlil tilini tanlang:</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("l_"))
async def lang_callback(call: types.CallbackQuery):
    user_data[call.message.chat.id]['lang'] = call.data.replace("l_", "")
    kb = InlineKeyboardBuilder()
    kb.button(text="⏱ Split", callback_data="v_split")
    kb.button(text="📖 Full Context", callback_data="v_full")
    await call.message.edit_text("📄 <b>Natija ko'rinishini tanlang:</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("v_"))
async def view_callback(call: types.CallbackQuery):
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
    wait_msg = await call.message.answer(f"⏳ Navbat: {waiting_users-1}\nTizim: <b>Suxandon AI</b>", parse_mode="HTML")
    
    async with async_lock:
        try:
            async def progress(p, status):
                bar = "▓" * (p // 10) + "░" * (10 - (p // 10))
                try: await wait_msg.edit_text(f"🎧 <b>TAHLIL JARAYONI</b>\n\n{status}\n\n📊 {p}%\n{bar}", parse_mode="HTML")
                except: pass

            for p in range(0, 31, 5): 
                await progress(p, "📥 Fayl serverga yuklanmoqda..."); await asyncio.sleep(0.1)

            f_path = f"tmp_{chat_id}.mp3"
            file = await bot.get_file(data['fid'])
            await bot.download_file(file.file_path, f_path)
            
            await progress(40, "🧠 AI tahlil qilmoqda...")
            res = await asyncio.to_thread(model_local.transcribe, f_path)
            segments = res['segments']

            await progress(85, "✍️ Matn shakllantirilmoqda...")
            l_code = data.get('lang') if data.get('lang') != "orig" else None
            final_text = ""

            if data.get('view') == "full":
                raw = " ".join([s['text'].strip() for s in segments])
                final_text = "🎙 <b>TO'LIQ KONTEKST NATIJASI</b>\n\n"
                sentences = re.split(r'(?<=[.!?])\s+', raw)
                for i, sent in enumerate(sentences):
                    if l_code:
                        try:
                            tr = GoogleTranslator(source='auto', target=l_code).translate(sent)
                            final_text += f"{sent} <i>({clean_text(tr)})</i> "
                        except: final_text += f"{sent} "
                    else: final_text += f"{sent} "
                    if (i + 1) % 4 == 0: final_text += "\n\n"
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

            await progress(100, "✅ Tahlil yakunlandi!")
            imzo = f"\n\n---\n👤 <b>Yaratuvchi:</b> {data['uname']}\n🤖 <b>Bot:</b> @{(await bot.get_me()).username}\n⏰ <b>Vaqt:</b> {get_uz_time()} (UZB)"
            
            if fmt == "txt":
                with open(f"res_{chat_id}.txt", "w", encoding="utf-8") as f: f.write(final_text + imzo)
                await call.message.answer_document(types.FSInputFile(f"res_{chat_id}.txt"), caption="✅ Natija tayyor!")
                os.remove(f"res_{chat_id}.txt")
            else:
                if len(final_text + imzo) > 4000:
                    for i in range(0, len(final_text + imzo), 4000):
                        await call.message.answer((final_text+imzo)[i:i+4000], parse_mode="HTML")
                else: await call.message.answer(final_text + imzo, parse_mode="HTML")

            await wait_msg.delete()
            if os.path.exists(f_path): os.remove(f_path)
        except Exception as e:
            await call.message.answer(f"❌ Xato: {str(e)}")
        finally:
            waiting_users -= 1
            if chat_id in user_data: del user_data[chat_id]

# --- 5. ADMIN PANEL ---
@dp.message(F.text == "🔑 Admin Panel", F.chat.id == ADMIN_ID)
async def admin_p_h(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Statistika", callback_data="adm_stats")
    kb.button(text="📋 Ro'yxat", callback_data="adm_list")
    kb.button(text="📢 Broadcast", callback_data="adm_bc")
    kb.adjust(1)
    await m.answer("🚀 <b>Admin boshqaruv paneli</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("adm_"))
async def admin_calls(call: types.CallbackQuery, state: FSMContext):
    if call.data == "adm_stats":
        count = sum(1 for _ in open(USERS_FILE)) if os.path.exists(USERS_FILE) else 0
        await call.message.answer(f"📊 <b>Statistika:</b>\n\nJami foydalanuvchilar: {count}")
    elif call.data == "adm_list":
        if os.path.exists(USERS_FILE):
            await call.message.answer_document(types.FSInputFile(USERS_FILE), caption="📂 User ID ro'yxati")
    elif call.data == "adm_bc":
        await call.message.answer("📢 Xabarni yuboring:")
        await state.set_state(AdminStates.waiting_for_bc)

@dp.message(AdminStates.waiting_for_bc)
async def process_bc(m: types.Message, state: FSMContext):
    await state.clear()
    ids = open(USERS_FILE).read().splitlines() if os.path.exists(USERS_FILE) else []
    for uid in ids:
        try: await bot.copy_message(chat_id=uid.strip(), from_chat_id=ADMIN_ID, message_id=m.message_id)
        except: pass
    await m.answer("✅ Broadcast yakunlandi.")

# --- 6. STREAMLIT ENGINE ---
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(dp.start_polling(bot, handle_signals=False, skip_updates=True))

if "bot_active" not in st.session_state:
    st.session_state.bot_active = True
    threading.Thread(target=run_bot, daemon=True).start()

st.title("🤖 Suxandon AI Bot Server")
st.success("Tizim barcha funksiyalar (Feedback, Reply, Admin Panel) bilan faol!")
    

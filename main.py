import asyncio
import os
import re
import threading
import pytz
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

class UserStates(StatesGroup):
    waiting_for_contact_msg = State()

class AdminStates(StatesGroup):
    waiting_for_bc = State()

def get_uz_time():
    return datetime.now(uz_tz).strftime('%Y.%m.%d %H:%M:%S')

def log_user_and_get_count(user: types.User):
    uid = str(user.id)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: pass
    with open(USERS_FILE, "r") as f:
        ids = f.read().splitlines()
    if uid not in ids:
        with open(USERS_FILE, "a") as f:
            f.write(f"{uid}\n")
        return len(ids) + 1, True
    return len(ids), False

def clean_text(text):
    """HTML formatini buzadigan belgilarni tozalash"""
    if not text: return ""
    return html.quote(text.replace("_", " ").replace("*", " "))

# --- 1. RESURSLARNI KESHLASH (CONFLICT KILLER) ---
# Bu funksiya serverda faqat 1 marta ishlaydi.
@st.cache_resource
def load_resources():
    # 1. Modelni yuklash
    w_model = whisper.load_model("base")
    
    # 2. Botni yuklash
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

# Navbat tizimi uchun qulf
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

# --- 3. HANDLERLAR (MANTIQ) ---

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    count, is_new = log_user_and_get_count(m.from_user)
    if is_new:
        u_name = f"@{m.from_user.username}" if m.from_user.username else "yo'q"
        try: await bot.send_message(ADMIN_ID, f"🆕 <b>YANGI USER:</b> {m.from_user.full_name} (ID: {m.from_user.id})", parse_mode="HTML")
        except: pass

    welcome = (
        f"👋 <b>Assalomu alaykum, {m.from_user.first_name}!</b>\n\n"
        f"🎙 <b>Suxandon AI</b> - Sun'iy intellekt yordamida ishlaydigan professional bot.\n\n"
        "Men quyidagi ishlarni bajaraman:\n"
        "✅ <b>Audio Tahlil:</b> Ovozli xabarlarni matnga aylantirish.\n"
        "✅ <b>Tarjima:</b> 5 xil xalqaro tillarga tarjima qilish.\n"
        "✅ <b>Formatlash:</b> Matnni vaqt belgilari bilan yoki to'liq holda taqdim etish.\n\n"
        "👇 <b>Ishni boshlash uchun audio yuboring yoki menyudan tanlang!</b>"
    )
    await m.answer(welcome, reply_markup=get_main_menu(m.from_user.id), parse_mode="HTML")

# --- YORDAM VA SAYT ---
@dp.message(F.text == "🌐 Saytga kirish")
async def login_h(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Saytni ochish", url="https://shodlikai.github.io/new_3/dastur.html")
    await m.answer("Bizning rasmiy veb-saytimizga o'tish uchun tugmani bosing:", reply_markup=kb.as_markup())

@dp.message(F.text == "ℹ️ Yordam")
async def help_h(m: types.Message):
    help_text = (
        "📖 <b>QO'LLANMA:</b>\n\n"
        "1️⃣ <b>Audio yuboring:</b> Ovozli xabar yoki MP3 fayl (maks 20MB).\n"
        "2️⃣ <b>Tilni tanlang:</b> Tarjima kerak bo'lsa tilni, bo'lmasa 'Original'ni tanlang.\n"
        "3️⃣ <b>Format:</b>\n"
        "   - <i>Split:</i> [00:12] Matn...\n"
        "   - <i>Full Context:</i> Oddiy matn ko'rinishida.\n"
        "4️⃣ <b>Natija:</b> Chatda o'qish yoki TXT fayl sifatida yuklab olish.\n\n"
        "💡 <i>Muammo bo'lsa 'Bog'lanish' bo'limidan yozing.</i>"
    )
    await m.answer(help_text, parse_mode="HTML")

# --- FEEDBACK VA REPLY TIZIMI ---
@dp.message(F.text == "👨‍💻 Bog'lanish")
async def contact_h(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="✍️ Bot orqali yozish", callback_data="msg_to_admin")
    kb.button(text="🌐 Aloqa sahifasi", url="https://shodlikai.github.io/new_3/dastur.html")
    kb.adjust(1)
    await m.answer("📞 <b>Admin bilan aloqa:</b>\n\nTaklif yoki shikoyatlaringizni to'g'ridan-to'g'ri yuborishingiz mumkin.", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "msg_to_admin")
async def start_feedback(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_contact_msg)
    await call.message.answer("📝 <b>Xabaringizni yozib qoldiring:</b>\n(Matn, rasm yoki audio bo'lishi mumkin)")
    await call.answer()

@dp.message(UserStates.waiting_for_contact_msg)
async def forward_to_admin(m: types.Message, state: FSMContext):
    await state.clear()
    header = f"📩 <b>MUROJAAT:</b>\n👤 User: {m.from_user.full_name}\n🆔 ID: <code>{m.from_user.id}</code>\n\n"
    await bot.send_message(ADMIN_ID, header + (m.text or "Fayl yuborildi"), parse_mode="HTML")
    await m.answer("✅ <b>Xabaringiz yetkazildi!</b>\nAdmin javobini shu bot orqali olasiz.")

@dp.message(F.chat.id == ADMIN_ID, F.reply_to_message)
async def admin_reply(m: types.Message):
    reply = m.reply_to_message.text or m.reply_to_message.caption
    if reply and "🆔 ID:" in reply:
        try:
            target_id = re.search(r"🆔 ID: (\d+)", reply).group(1)
            await bot.send_message(chat_id=target_id, text=f"💬 <b>Admin javobi:</b>\n\n{m.text}", parse_mode="HTML")
            await m.answer("✅ Javob yuborildi.")
        except: await m.answer("❌ ID topilmadi.")

# --- 4. AUDIO TAHLIL VA PROGRESS ---

@dp.message(F.audio | F.voice)
async def handle_audio(m: types.Message):
    # 20MB check
    f_size = m.audio.file_size if m.audio else m.voice.file_size
    if f_size > 20 * 1024 * 1024:
        await m.answer("❌ <b>Fayl juda katta!</b>\nIltimos, 20MB dan kichik fayl yuboring.", parse_mode="HTML")
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
    kb.button(text="⏱ Split", callback_data="v_split")
    kb.button(text="📖 Full Context", callback_data="v_full")
    await call.message.edit_text("📄 <b>Natija ko'rinishini tanlang:</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("v_"))
async def view_callback(call: types.CallbackQuery):
    if call.message.chat.id not in user_data:
        await call.message.answer("❌ Ma'lumot eskirgan. Qayta yuboring.")
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
    # Boshlang'ich xabar
    wait_msg = await call.message.answer(f"⏳ <b>Navbatda turing:</b> Sizdan oldin {waiting_users-1} kishi bor...", parse_mode="HTML")
    
    async with async_lock:
        try:
            # PROGRESS BAR FUNKSIYASI
            async def update_progress(percent, text):
                bar_len = 10
                filled = int(percent / 10)
                bar = "🟩" * filled + "⬜" * (bar_len - filled)
                try: await wait_msg.edit_text(f"🚀 <b>JARAYON KETMOQDA...</b>\n\n{text}\n\n{bar} {percent}%", parse_mode="HTML")
                except: pass

            # 1. Yuklash
            await update_progress(10, "📥 Audio serverga yuklanmoqda...")
            f_path = f"tmp_{chat_id}.mp3"
            file = await bot.get_file(data['fid'])
            await bot.download_file(file.file_path, f_path)
            
            # 2. Tahlil (Whisper)
            await update_progress(40, "🧠 Sun'iy intellekt tahlil qilmoqda...")
            res = await asyncio.to_thread(model_local.transcribe, f_path)
            segments = res['segments']
            
            # 3. Formatlash va Tarjima
            await update_progress(70, "📝 Matn formatlanmoqda va tarjima qilinmoqda...")
            l_code = data.get('lang') if data.get('lang') != "orig" else None
            final_text = ""

            for s in segments:
                tm = f"[{int(s['start']//60):02d}:{int(s['start']%60):02d}]"
                txt = clean_text(s['text'].strip())
                if l_code:
                    try:
                        tr = GoogleTranslator(source='auto', target=l_code).translate(txt)
                        final_text += f"{tm} {txt}\n<i>({clean_text(tr)})</i>\n\n"
                    except: final_text += f"{tm} {txt}\n\n"
                else: final_text += f"{tm} {txt}\n\n"

            # 4. Yuborish
            await update_progress(100, "✅ Tayyor! Yuborilmoqda...")
            
            # Pechat (Imzo)
            creator = data['uname']
            if not creator.startswith('@'): creator = f"@{creator.replace(' ', '_')}"
            imzo = f"\n\n---\n👤 <b>Yaratuvchi:</b> {creator}\n🤖 <b>Bot:</b> @{(await bot.get_me()).username}\n⏰ <b>Vaqt:</b> {get_uz_time()}"
            
            if fmt == "txt":
                with open(f"res_{chat_id}.txt", "w", encoding="utf-8") as f: f.write(final_text + imzo)
                await call.message.answer_document(types.FSInputFile(f"res_{chat_id}.txt"), caption="✅ Natija faylda!")
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
            await call.message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
        finally:
            waiting_users -= 1
            if chat_id in user_data: del user_data[chat_id]

# --- 5. ADMIN PANEL ---
@dp.message(F.text == "🔑 Admin Panel", F.chat.id == ADMIN_ID)
async def admin_panel(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Statistika", callback_data="adm_stats")
    kb.button(text="📢 Broadcast", callback_data="adm_bc")
    kb.adjust(1)
    await m.answer("🚀 <b>Admin Panel</b>", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "adm_stats")
async def adm_stats(call: types.CallbackQuery):
    count = sum(1 for _ in open(USERS_FILE)) if os.path.exists(USERS_FILE) else 0
    await call.message.answer(f"📊 Jami foydalanuvchilar: {count}")

@dp.callback_query(F.data == "adm_bc")
async def adm_bc(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📢 Xabarni yuboring (Rasm, Video, Matn):")
    await state.set_state(AdminStates.waiting_for_bc)

@dp.message(AdminStates.waiting_for_bc)
async def process_bc(m: types.Message, state: FSMContext):
    await state.clear()
    ids = open(USERS_FILE).read().splitlines() if os.path.exists(USERS_FILE) else []
    success = 0
    status_msg = await m.answer("⏳ Tarqatish boshlandi...")
    
    for uid in ids:
        try: 
            await bot.copy_message(chat_id=uid.strip(), from_chat_id=ADMIN_ID, message_id=m.message_id)
            success += 1
            await asyncio.sleep(0.05) # Spamdan himoya
        except: pass
    
    await status_msg.edit_text(f"✅ Xabar {success} kishiga yetib bordi.")

# --- 6. SINGLETON BACKGROUND RUNNER (ENG MUHIM QISM) ---
# Bu funksiya @st.cache_resource sababli faqat 1 marta ishlaydi
# Sahifa yangilansa ham qayta ishga tushmaydi!

@st.cache_resource
def launch_bot_background():
    async def _runner():
        try:
            # 1. Eski webhooklarni o'chirish (KONFLIKTNI TUZATISH)
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ Webhooklar tozalandi.")
            
            # 2. Pollingni boshlash
            await dp.start_polling(bot, handle_signals=False)
        except Exception as e:
            print(f"Polling error: {e}")

    def _thread_target():
        # Yangi event loop ochib, botni o'sha yerda aylantiramiz
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_runner())

    # Daemon thread (Asosiy dastur o'chsa, bu ham o'chadi)
    t = threading.Thread(target=_thread_target, daemon=True)
    t.start()
    return t

# Botni ishga tushirish (Faqat 1 marta)
launch_bot_background()

# --- STREAMLIT UI ---
st.set_page_config(page_title="Suxandon AI Server", page_icon="🤖")
st.title("🤖 Suxandon AI")
st.success("Server barqaror ishlamoqda. Telegramdan botni ishlatavering!")
st.info("Eslatma: Bu sahifani yopib yuborsangiz ham bot ishlashda davom etadi.")
    

"""
🎓 QUIZ BOT (AIOGRAM 3 - TO'LIQ VERSIYA)
✅ Conflict-free polling (Streamlit uchun Singleton Threading)
✅ 100% Jim rejim (Terminal getUpdates xabarlaridan tozalandi)
✅ Barcha modullar (Routers) to'liq ulangan
✅ Global Error Handler (Tizim qulab tushmasligi uchun himoya)
"""
import logging
import asyncio
import sys
import threading
import traceback
from handlers.bot_admin import router as bot_admin_router

# ══════════════════════════════════════════════════════════
# 1. LOGGING (TERMINALNI TOZALASH VA XATOLARNI YOZISH)
# ══════════════════════════════════════════════════════════
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Aiogram va HTTP so'rovlarining keraksiz loglarini (INFO) yashirish
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ══════════════════════════════════════════════════════════
# 2. KUTUBXONALAR VA IMPORTLAR
# ══════════════════════════════════════════════════════════
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent

from config import BOT_TOKEN
from firebase.config import initialize_firebase

# 📦 Barcha Aiogram Routerlarni import qilish
from handlers.start import router as start_router
from handlers.profile import router as profile_router
from handlers.create_test import router as create_test_router
from handlers.tests import router as tests_router
from handlers.admin import router as admin_router
from handlers.leaderboard import router as leaderboard_router


# ══════════════════════════════════════════════════════════
# 3. BOT VA DISPATCHER SOZLAMALARI
# ══════════════════════════════════════════════════════════
# Botni HTML formatida xabar yuborishga moslash
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# FSM (Holatlar) uchun xotira
dp = Dispatcher(storage=MemoryStorage())

# 🔗 Barcha routerlarni (modullarni) Dispatcher ga ulash
dp.include_router(start_router)
dp.include_router(profile_router)
dp.include_router(create_test_router)
dp.include_router(tests_router)
dp.include_router(admin_router)
dp.include_router(leaderboard_router)
dp.include_router(bot_admin_router)


# 🛡️ GLOBAL ERROR HANDLER (Qulab tushishdan himoya)
@dp.errors()
async def global_error_handler(event: ErrorEvent):
    """Bot ishlayotganda kutilmagan xatolik chiqsa, bot o'chib qolmaydi."""
    logger.error("Kutilmagan xatolik yuz berdi:")
    logger.error(f"Xato turi: {type(event.exception).__name__}")
    logger.error(f"Xato matni: {event.exception}")
    # Xatoning qayerdan chiqqanini aniq ko'rsatish
    traceback.print_exc()
    return True # Xato ushlandi, bot ishlashda davom etadi


# ══════════════════════════════════════════════════════════
# 4. STREAMLIT UCHUN ORQA FONDA ISHLASH MANTIQI (THREADING)
# ══════════════════════════════════════════════════════════
_lock = threading.Lock()
_bot_thread = None
_bot_started = False

def run_bot_in_background():
    """
    Streamlit sayti yangilanganda bot qayta-qayta ishga tushib (Conflict)
    bermasligi uchun yagona oqim (Singleton) mexanizmi.
    """
    global _bot_started, _bot_thread
    with _lock:
        if _bot_started:
            return _bot_thread
        _bot_started = True

    # Firebase'ni ishga tushirish
    initialize_firebase()

    async def _run():
        try:
            # Eski qolib ketgan webhook yoki update'larni tozalash
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("🚀 Aiogram Bot ishga tushdi (Streamlit Thread orqali)!")
            # Botni poling rejimida ishga tushirish (handle_signals=False juda muhim!)
            await dp.start_polling(bot, handle_signals=False)
        except Exception as e:
            logger.error(f"Polling xatosi: {e}")

    def _thread_target():
        # Yangi Asyncio Event Loop yaratish va yurgizish
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run())
        finally:
            loop.close()

    # Orqa fonda ishlaydigan Daemon Thread yaratish
    _bot_thread = threading.Thread(target=_thread_target, daemon=True, name="AiogramBotThread")
    _bot_thread.start()
    return _bot_thread


# ══════════════════════════════════════════════════════════
# 5. LOKAL TEST QILISH UCHUN (python bot.py)
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Lokal ishga tushirganda Firebase ulanishini ta'minlash
    initialize_firebase()
    
    async def main():
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🚀 Aiogram Bot ishga tushdi (Lokal rejim)!")
        await dp.start_polling(bot)
        
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot to'xtatildi.")

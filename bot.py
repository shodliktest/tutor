"""
🎓 QUIZ BOT — Aiogram 3 (To'liq versiya)
✅ Conflict-free polling (Singleton Threading)
✅ Global Error Handler
✅ Poll test rejimi (Native Telegram Quiz Poll)
✅ Inline test rejimi (Tugmalar bilan)
"""
import logging
import asyncio
import sys
import threading
import traceback

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

# Keraksiz loglarni yashirish
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent

from config import BOT_TOKEN
from firebase.config import initialize_firebase

# Barcha handlerlarni import qilish
from handlers.start        import router as start_router
from handlers.tests        import router as tests_router
from handlers.poll_test    import router as poll_router
from handlers.create_test  import router as create_router
from handlers.profile      import router as profile_router
from handlers.leaderboard  import router as lb_router
from handlers.admin        import router as admin_router

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp  = Dispatcher(storage=MemoryStorage())

# Routerlarni ulash (tartib muhim!)
dp.include_router(start_router)
dp.include_router(poll_router)      # Poll handler — tests dan oldin!
dp.include_router(tests_router)
dp.include_router(create_router)
dp.include_router(profile_router)
dp.include_router(lb_router)
dp.include_router(admin_router)


# ── Global Error Handler ──────────────────────────────────

@dp.errors()
async def global_error(event: ErrorEvent):
    log.error(f"Kutilmagan xatolik: {type(event.exception).__name__}: {event.exception}")
    traceback.print_exc()
    return True


# ═══════════════════════════════════════════════════════════
# STREAMLIT UCHUN SINGLETON THREADING
# ═══════════════════════════════════════════════════════════

_lock       = threading.Lock()
_bot_thread = None
_started    = False


def run_bot_in_background():
    """
    Streamlit har yangilanganda bot qayta ishga tushib
    TelegramConflictError bermasligi uchun Singleton pattern.
    """
    global _bot_thread, _started

    with _lock:
        if _started:
            return _bot_thread
        _started = True

    initialize_firebase()

    async def _run():
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            log.info("🚀 Bot ishga tushdi (Streamlit thread)!")
            await dp.start_polling(bot, handle_signals=False)
        except Exception as e:
            log.error(f"Polling xatosi: {e}")

    def _thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run())
        finally:
            loop.close()

    _bot_thread = threading.Thread(target=_thread, daemon=True, name="BotThread")
    _bot_thread.start()
    return _bot_thread


# ═══════════════════════════════════════════════════════════
# LOKAL ISHGA TUSHIRISH: python bot.py
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    initialize_firebase()

    async def main():
        await bot.delete_webhook(drop_pending_updates=True)
        log.info("🚀 Bot lokal rejimda ishga tushdi!")
        await dp.start_polling(bot)

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("🛑 Bot to'xtatildi.")

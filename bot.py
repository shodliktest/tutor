"""
🎓 QUIZ BOT — Aiogram 3.x
✅ Deploy boshlanganda AVVAL webhook/eski polling o'chiriladi
✅ Singleton — ikki instance HECH QACHON ochilmaydi
✅ Streamlit bilan thread-safe
"""
import asyncio
import logging
import sys
import threading

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from firebase.config import init_firebase

# ── Singleton ─────────────────────────────────────────────
_lock    = threading.Lock()
_started = False
_thread: threading.Thread | None = None


def _build_dp() -> Dispatcher:
    from handlers import start, tests, create_test, profile, leaderboard, admin
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    dp.include_router(tests.router)
    dp.include_router(create_test.router)
    dp.include_router(profile.router)
    dp.include_router(leaderboard.router)
    dp.include_router(admin.router)
    return dp


async def _kill_all_sessions(bot: Bot):
    """
    Eski webhook VA getUpdates sessiyalarini to'liq o'chiradi.
    drop_pending_updates=True — eski xabarlar ham o'chiriladi.
    """
    try:
        # 1. Webhookni o'chirish
        await bot.delete_webhook(drop_pending_updates=True)
        log.info("🪓 Webhook o'chirildi + pending updates tozalandi")
    except Exception as e:
        log.warning(f"Webhook o'chirishda xato (muammo emas): {e}")

    # 2. Biroz kutish — Telegram serverida eski session yopilsin
    await asyncio.sleep(2)
    log.info("✅ Telegram session tozalandi, polling boshlanadi")


async def _run_polling():
    if not BOT_TOKEN:
        log.error("❌ BOT_TOKEN topilmadi! Secrets ni tekshiring.")
        return

    init_firebase()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Har safar botni ishga tushirishdan OLDIN eski sessionni o'chiramiz
    await _kill_all_sessions(bot)

    dp = _build_dp()

    log.info("🚀 Polling boshlandi!")
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,
            polling_timeout=30,
            handle_signals=False,    # Streamlit signal bilan to'qnashuv yo'q
        )
    finally:
        await bot.session.close()
        log.info("🛑 Bot to'xtatildi")


def run_bot() -> threading.Thread | None:
    """
    Botni bitta background thread da ishga tushiradi.
    Ikkinchi marta chaqirilsa — mavjud threadni qaytaradi.
    """
    global _started, _thread

    with _lock:
        # Thread tirik bo'lsa — yangi ochmayiz
        if _thread and _thread.is_alive():
            log.info("⚠️  Bot allaqachon ishlayapti — yangi instance ochilmadi")
            return _thread

        # Birinchi marta yoki thread o'lgan bo'lsa — yangisini ochamiz
        _started = True

    def _target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run_polling())
        except Exception as e:
            log.error(f"Bot thread xato: {e}")
        finally:
            loop.close()
            log.info("🧵 BotThread yopildi")

    _thread = threading.Thread(
        target=_target,
        daemon=True,
        name="BotThread"
    )
    _thread.start()
    log.info(f"🧵 BotThread ishga tushdi (id={_thread.ident})")
    return _thread


# ── Lokal ishlatish: python bot.py ────────────────────────
if __name__ == "__main__":
    try:
        asyncio.run(_run_polling())
    except KeyboardInterrupt:
        log.info("🛑 To'xtatildi")

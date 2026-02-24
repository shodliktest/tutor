"""
🎓 QUIZ BOT - Professional Test Platformasi
Author: Otavaliyev.M (SHodlik)

✅ SingletonConfig  — faqat bitta bot instance
✅ WebhookKiller    — eski webhook o'chiriladi
✅ Thread-safe      — asyncio loop muammosi yo'q
"""

import logging
import asyncio
import sys
import os

# ── Logging (faqat StreamHandler — Streamlit Cloud da fayl yozib bo'lmaydi) ──
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ── Import ────────────────────────────────────────────────────────────────────
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters
)
from firebase.config import initialize_firebase
from handlers.start import start_handler, help_handler
from handlers.auth import register_handler, login_handler
from handlers.tests import (
    browse_tests_handler, take_test_handler,
    test_answer_handler, finish_test_handler
)
from handlers.create_test import (
    create_test_start, upload_file_handler,
    manual_create_handler
)
from handlers.admin import admin_panel_handler
from handlers.results import my_results_handler
from handlers.leaderboard import leaderboard_handler
from handlers.profile import profile_handler
from utils.states import *
from config import BOT_TOKEN


# ══════════════════════════════════════════════════════════════════════════════
# 1️⃣  SINGLETON — faqat bitta Application instance bo'ladi
# ══════════════════════════════════════════════════════════════════════════════
_app_instance: Application | None = None


def get_application() -> Application:
    """
    Application ni bir marta yaratadi va qayta ishlatadi.
    Streamlit har sahifa yangilanishida bu funksiyani chaqirsa ham
    bot qayta-qayta ishga tushmaydi.
    """
    global _app_instance
    if _app_instance is None:
        _app_instance = _build_application()
    return _app_instance


def _build_application() -> Application:
    """Application va barcha handlerlarni bir marta qurish"""
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)   # Thread-safe concurrent updates
        .build()
    )

    # ── Asosiy komandalar ─────────────────────────────────
    app.add_handler(CommandHandler("start",       start_handler))
    app.add_handler(CommandHandler("help",        help_handler))
    app.add_handler(CommandHandler("admin",       admin_panel_handler))
    app.add_handler(CommandHandler("profile",     profile_handler))
    app.add_handler(CommandHandler("results",     my_results_handler))
    app.add_handler(CommandHandler("leaderboard", leaderboard_handler))
    app.add_handler(CommandHandler("tests",       browse_tests_handler))

    # ── Test ishlash conversation ─────────────────────────
    test_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(take_test_handler, pattern="^take_test_")
        ],
        states={
            ANSWERING: [
                CallbackQueryHandler(test_answer_handler, pattern="^ans_"),
                CallbackQueryHandler(test_answer_handler, pattern="^multi_"),
            ],
            TEXT_ANSWER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, test_answer_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", finish_test_handler)],
        per_user=True,
        per_chat=False,
        allow_reentry=True,
    )
    app.add_handler(test_conv)

    # ── Test yaratish conversation ────────────────────────
    create_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(create_test_start, pattern="^create_test$")
        ],
        states={
            UPLOAD_FILE: [
                MessageHandler(filters.Document.ALL, upload_file_handler),
                CallbackQueryHandler(manual_create_handler, pattern="^manual_create$"),
                CallbackQueryHandler(
                    lambda u, c: u.callback_query.answer(),
                    pattern="^show_samples$"
                ),
            ],
            SET_SUBJECT: [
                CallbackQueryHandler(lambda u, c: None, pattern="^subj_")
            ],
            SET_DIFFICULTY: [
                CallbackQueryHandler(lambda u, c: None, pattern="^diff_")
            ],
            CONFIRM_TEST: [
                CallbackQueryHandler(lambda u, c: None, pattern="^confirm_")
            ],
        },
        fallbacks=[
            CommandHandler("cancel", lambda u, c: ConversationHandler.END)
        ],
        allow_reentry=True,
    )
    app.add_handler(create_conv)

    # ── Global callback query handlerlar ─────────────────
    app.add_handler(CallbackQueryHandler(browse_tests_handler,  pattern="^browse_"))
    app.add_handler(CallbackQueryHandler(browse_tests_handler,  pattern="^test_info_"))
    app.add_handler(CallbackQueryHandler(leaderboard_handler,   pattern="^lb_"))
    app.add_handler(CallbackQueryHandler(admin_panel_handler,   pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(profile_handler,       pattern="^profile_"))
    app.add_handler(CallbackQueryHandler(my_results_handler,    pattern="^profile_results$"))

    # ── Main menu fallback ────────────────────────────────
    from handlers.start import start_handler as _start
    app.add_handler(CallbackQueryHandler(
        lambda u, c: _start(u, c),
        pattern="^main_menu$"
    ))

    logger.info("✅ Application qurildi — barcha handlerlar ulandi")
    return app


# ══════════════════════════════════════════════════════════════════════════════
# 2️⃣  WEBHOOK KILLER — eski webhook bo'lsa o'chiradi
# ══════════════════════════════════════════════════════════════════════════════
async def kill_webhook(app: Application) -> None:
    """
    Polling ishlatishdan oldin eski webhookni o'chiradi.
    Aks holda: 'Conflict: terminated by other getUpdates request'
    """
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("🪓 Webhook o'chirildi (agar mavjud bo'lsa)")
    except Exception as e:
        logger.warning(f"Webhook o'chirishda xato (muammo emas): {e}")


# ══════════════════════════════════════════════════════════════════════════════
# 3️⃣  THREAD-SAFE RUNNER — event loop muammosini hal qiladi
# ══════════════════════════════════════════════════════════════════════════════
def run_bot() -> None:
    """
    Bot ni to'g'ri ishga tushirish.

    Muammo: Streamlit o'zining event loop ini ishlatadi.
    Yechim: Alohida thread da yangi event loop ochib botni ishlatamiz.
    """
    import threading

    def _run_in_thread():
        """Yangi thread da yangi event loop bilan bot ishga tushadi"""
        # Yangi event loop — Streamlit ning loop iga tegmaydi
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _start_bot():
            initialize_firebase()
            app = get_application()
            await kill_webhook(app)
            logger.info("🚀 Bot polling ishga tushdi!")
            # run_polling o'rniga qo'lda initialize + start + idle
            async with app:
                await app.start()
                await app.updater.start_polling(
                    drop_pending_updates=True,
                    allowed_updates=Update.ALL_TYPES,
                )
                # To bot tugaguncha kutadi
                await asyncio.Event().wait()

        try:
            loop.run_until_complete(_start_bot())
        except (KeyboardInterrupt, SystemExit):
            logger.info("🛑 Bot to'xtatildi")
        finally:
            loop.close()

    # Daemon thread — asosiy process tugasa u ham tugaydi
    thread = threading.Thread(target=_run_in_thread, daemon=True, name="BotThread")
    thread.start()
    logger.info(f"🧵 Bot thread ishga tushdi: {thread.name}")
    return thread


# ══════════════════════════════════════════════════════════════════════════════
# 4️⃣  TO'G'RIDAN-TO'G'RI ISHGA TUSHIRISH (python bot.py)
# ══════════════════════════════════════════════════════════════════════════════
def main():
    """Lokal serverda to'g'ridan-to'g'ri ishga tushirish uchun"""
    initialize_firebase()
    app = get_application()

    async def _run():
        await kill_webhook(app)
        logger.info("🚀 Bot ishga tushdi (polling rejimi)!")
        async with app:
            await app.start()
            await app.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES,
            )
            await asyncio.Event().wait()

    try:
        asyncio.run(_run())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot to'xtatildi")


if __name__ == "__main__":
    main()
    

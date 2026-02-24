"""
🎓 QUIZ BOT
✅ Conflict-free polling
✅ Webhook killer
✅ Thread-safe singleton
"""
import logging
import asyncio
import sys
import threading

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

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
    manual_create_handler, show_samples_handler, send_sample_file
)
from handlers.admin import admin_panel_handler
from handlers.results import my_results_handler
from handlers.leaderboard import leaderboard_handler
from handlers.profile import profile_handler
from utils.states import *
from config import BOT_TOKEN

# ── Singleton ─────────────────────────────────────────────
_lock = threading.Lock()
_bot_thread: threading.Thread | None = None
_bot_started = False


def _build_app() -> Application:
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    # Komandalar
    app.add_handler(CommandHandler("start",       start_handler))
    app.add_handler(CommandHandler("help",        help_handler))
    app.add_handler(CommandHandler("admin",       admin_panel_handler))
    app.add_handler(CommandHandler("profile",     profile_handler))
    app.add_handler(CommandHandler("results",     my_results_handler))
    app.add_handler(CommandHandler("leaderboard", leaderboard_handler))
    app.add_handler(CommandHandler("tests",       browse_tests_handler))

    # Test ishlash
    test_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(take_test_handler, pattern="^take_test_")],
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

    # Test yaratish
    create_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_test_start, pattern="^create_test$")],
        states={
            UPLOAD_FILE: [
                MessageHandler(filters.Document.ALL, upload_file_handler),
                CallbackQueryHandler(manual_create_handler, pattern="^manual_create$"),
            ],
            SET_SUBJECT:   [CallbackQueryHandler(lambda u,c: None, pattern="^subj_")],
            SET_DIFFICULTY:[CallbackQueryHandler(lambda u,c: None, pattern="^diff_")],
            CONFIRM_TEST:  [CallbackQueryHandler(lambda u,c: None, pattern="^confirm_")],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)],
        allow_reentry=True,
    )
    app.add_handler(create_conv)

    # Namuna fayllar
    app.add_handler(CallbackQueryHandler(show_samples_handler, pattern="^show_samples$"))
    app.add_handler(CallbackQueryHandler(send_sample_file,     pattern="^sample_"))

    # Callback querylar
    app.add_handler(CallbackQueryHandler(browse_tests_handler, pattern="^browse_"))
    app.add_handler(CallbackQueryHandler(browse_tests_handler, pattern="^test_info_"))
    app.add_handler(CallbackQueryHandler(leaderboard_handler,  pattern="^lb_"))
    app.add_handler(CallbackQueryHandler(admin_panel_handler,  pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(profile_handler,      pattern="^profile_"))
    app.add_handler(CallbackQueryHandler(my_results_handler,   pattern="^profile_results$"))
    app.add_handler(CallbackQueryHandler(
        lambda u,c: start_handler(u,c), pattern="^main_menu$"
    ))

    return app


def run_bot() -> threading.Thread | None:
    """
    Botni bitta daemon thread da ishga tushiradi.
    Ikkinchi marta chaqirilsa — hech narsa qilmaydi (singleton).
    """
    global _bot_thread, _bot_started

    with _lock:
        # Agar allaqachon ishga tushirilgan bo'lsa — qaytib ketadi
        if _bot_started and _bot_thread and _bot_thread.is_alive():
            logger.info("⚠️ Bot allaqachon ishlayapti — yangi instance ochilmadi")
            return _bot_thread

        _bot_started = True

    def _thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _run():
            initialize_firebase()
            app = _build_app()

            # Webhook o'chirish
            try:
                await app.bot.delete_webhook(drop_pending_updates=True)
                logger.info("🪓 Webhook o'chirildi")
            except Exception as e:
                logger.warning(f"Webhook o'chirishda xato: {e}")

            logger.info("🚀 Bot polling boshlandi!")
            async with app:
                await app.start()
                await app.updater.start_polling(
                    drop_pending_updates=True,
                    allowed_updates=Update.ALL_TYPES,
                    poll_interval=1.0,
                    timeout=30,
                )
                # Cheksiz kutish
                await asyncio.Event().wait()

        try:
            loop.run_until_complete(_run())
        except Exception as e:
            logger.error(f"Bot thread xato: {e}")
        finally:
            loop.close()

    _bot_thread = threading.Thread(
        target=_thread_target,
        daemon=True,
        name="TelegramBotThread"
    )
    _bot_thread.start()
    logger.info(f"🧵 Bot thread ishga tushdi")
    return _bot_thread


def main():
    """python bot.py — lokal ishga tushirish"""
    initialize_firebase()

    async def _run():
        app = _build_app()
        try:
            await app.bot.delete_webhook(drop_pending_updates=True)
        except Exception:
            pass
        logger.info("🚀 Bot ishga tushdi (lokal)!")
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
    

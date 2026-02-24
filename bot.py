"""
🎓 QUIZ BOT - Professional Test Platformasi
Author: Otavaliyev.M (SHodlik)
Stack: Python-Telegram-Bot + Firebase
"""

import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler,
    filters
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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    # Firebase ishga tushirish
    initialize_firebase()
    
    # Bot yaratish
    app = Application.builder().token(BOT_TOKEN).build()

    # ===== ASOSIY HANDLERLAR =====
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("admin", admin_panel_handler))
    app.add_handler(CommandHandler("profile", profile_handler))
    app.add_handler(CommandHandler("results", my_results_handler))
    app.add_handler(CommandHandler("leaderboard", leaderboard_handler))
    app.add_handler(CommandHandler("tests", browse_tests_handler))

    # ===== TEST ISHLASH CONVERSATION =====
    test_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(take_test_handler, pattern="^take_test_")],
        states={
            ANSWERING: [CallbackQueryHandler(test_answer_handler, pattern="^ans_")],
            TEXT_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, test_answer_handler)],
        },
        fallbacks=[CommandHandler("cancel", finish_test_handler)],
        per_user=True
    )
    app.add_handler(test_conv)

    # ===== TEST YARATISH CONVERSATION =====
    create_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_test_start, pattern="^create_test$")],
        states={
            UPLOAD_FILE: [
                MessageHandler(filters.Document.ALL, upload_file_handler),
                CallbackQueryHandler(manual_create_handler, pattern="^manual_create$")
            ],
            SET_SUBJECT: [CallbackQueryHandler(lambda u,c: None, pattern="^subj_")],
            SET_DIFFICULTY: [CallbackQueryHandler(lambda u,c: None, pattern="^diff_")],
            CONFIRM_TEST: [CallbackQueryHandler(lambda u,c: None, pattern="^confirm_")],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)],
    )
    app.add_handler(create_conv)

    # ===== CALLBACK QUERY HANDLER =====
    app.add_handler(CallbackQueryHandler(browse_tests_handler, pattern="^browse_"))
    app.add_handler(CallbackQueryHandler(leaderboard_handler, pattern="^lb_"))
    app.add_handler(CallbackQueryHandler(admin_panel_handler, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(profile_handler, pattern="^profile_"))

    logger.info("🚀 Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

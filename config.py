"""
⚙️ KONFIGURATSIYA
.env faylidan o'qiydi
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Firebase
FIREBASE_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL", "")
}

# Admin user IDlar (Telegram ID)
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",")]

# Bot sozlamalari
MAX_ATTEMPTS = 3           # Bir testga nechta urinish
DEFAULT_TIME_LIMIT = 30    # Daqiqa
PASSING_SCORE = 60         # O'tish foizi (default)
MAX_FILE_SIZE = 20         # MB

# Fanlar ro'yxati
SUBJECTS = [
    "Matematika",
    "Fizika", 
    "Kimyo",
    "Biologiya",
    "Tarix",
    "Geografiya",
    "Ingliz tili",
    "Rus tili",
    "Ona tili",
    "Informatika",
    "Adabiyot",
    "Huquq",
    "Iqtisodiyot",
    "Boshqa"
]

# Qiyinlik darajalari
DIFFICULTY_LEVELS = {
    "easy": "🟢 Oson",
    "medium": "🟡 O'rtacha",
    "hard": "🔴 Qiyin",
    "expert": "⚡ Ekspert"
}

# Test turlari
TEST_TYPES = {
    "multiple_choice": "🔘 Bir javobli test",
    "multi_select": "☑️ Ko'p javobli test",
    "true_false": "✅ Ha / Yo'q",
    "text_input": "✍️ Yozma javob",
    "matching": "🔗 Moslashtirish",
    "ordering": "🔢 Tartiblash",
    "fill_blank": "📝 Bo'sh joyni to'ldirish"
}

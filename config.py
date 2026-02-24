"""
⚙️ KONFIGURATSIYA
Streamlit Cloud secrets dan o'qiydi (st.secrets)
Lokal ishlatganda: .streamlit/secrets.toml faylidan
"""
import os


def _get_secret(key: str, default=None):
    """
    Avval st.secrets dan o'qiydi (Streamlit Cloud),
    keyin os.environ dan (Railway, Heroku, lokal .env).
    """
    try:
        import streamlit as st
        if "." in key:
            section, subkey = key.split(".", 1)
            return st.secrets[section][subkey]
        return st.secrets[key]
    except Exception:
        env_key = key.replace(".", "_").upper()
        return os.environ.get(env_key, default)


# ── Telegram ──────────────────────────────────────────────
BOT_TOKEN = _get_secret("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ── Firebase ──────────────────────────────────────────────
FIREBASE_CONFIG = {
    "apiKey":            _get_secret("firebase.api_key"),
    "authDomain":        _get_secret("firebase.auth_domain"),
    "projectId":         _get_secret("firebase.project_id"),
    "storageBucket":     _get_secret("firebase.storage_bucket"),
    "messagingSenderId": _get_secret("firebase.messaging_sender_id"),
    "appId":             _get_secret("firebase.app_id"),
    "databaseURL":       _get_secret("firebase.database_url", ""),
}

# ── Admin IDlar ───────────────────────────────────────────
_admin_raw = _get_secret("ADMIN_IDS", "123456789")
ADMIN_IDS = [int(x.strip()) for x in str(_admin_raw).split(",") if x.strip()]

# ── Bot sozlamalari ───────────────────────────────────────
MAX_ATTEMPTS = 3
DEFAULT_TIME_LIMIT = 30
PASSING_SCORE = 60
MAX_FILE_SIZE = 20

# ── Fanlar ro'yxati ───────────────────────────────────────
SUBJECTS = [
    "Matematika", "Fizika", "Kimyo", "Biologiya",
    "Tarix", "Geografiya", "Ingliz tili", "Rus tili",
    "Ona tili", "Informatika", "Adabiyot", "Huquq",
    "Iqtisodiyot", "Boshqa"
]

# ── Qiyinlik darajalari ───────────────────────────────────
DIFFICULTY_LEVELS = {
    "easy":   "🟢 Oson",
    "medium": "🟡 O'rtacha",
    "hard":   "🔴 Qiyin",
    "expert": "⚡ Ekspert",
}

# ── Test turlari ──────────────────────────────────────────
TEST_TYPES = {
    "multiple_choice": "🔘 Bir javobli test",
    "multi_select":    "☑️ Ko'p javobli test",
    "true_false":      "✅ Ha / Yo'q",
    "text_input":      "✍️ Yozma javob",
    "matching":        "🔗 Moslashtirish",
    "ordering":        "🔢 Tartiblash",
    "fill_blank":      "📝 Bo'sh joyni to'ldirish",
}

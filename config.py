"""
⚙️ KONFIGURATSIYA
Streamlit Cloud secrets yoki os.environ dan o'qiydi
"""
import os


def _s(key: str, default=None):
    """st.secrets yoki os.environ dan qiymat olish"""
    try:
        import streamlit as st
        if "." in key:
            sec, sub = key.split(".", 1)
            return st.secrets[sec][sub]
        return st.secrets[key]
    except Exception:
        return os.environ.get(key.replace(".", "_").upper(), default)


# ── Telegram ──────────────────────────────────────────────
BOT_TOKEN: str = _s("BOT_TOKEN", "")

# ── Admin IDlar (vergul bilan ajratilgan) ─────────────────
_raw = str(_s("ADMIN_IDS", "123456789"))
ADMIN_IDS: list = [int(x.strip()) for x in _raw.split(",") if x.strip().isdigit()]

# ── Admin panel paroli ────────────────────────────────────
ADMIN_PASSWORD: str = _s("ADMIN_PASSWORD", "admin123")

# ── Firebase ──────────────────────────────────────────────
FIREBASE_CFG = {
    "apiKey":            _s("firebase.api_key", ""),
    "authDomain":        _s("firebase.auth_domain", ""),
    "projectId":         _s("firebase.project_id", ""),
    "storageBucket":     _s("firebase.storage_bucket", ""),
    "messagingSenderId": _s("firebase.messaging_sender_id", ""),
    "appId":             _s("firebase.app_id", ""),
    "databaseURL":       _s("firebase.database_url", ""),
}

# ── Bot sozlamalari ───────────────────────────────────────
PASSING_SCORE   = 60      # O'tish foizi (%)
MAX_FILE_MB     = 20      # Maksimal fayl hajmi
ANSWER_DELAY    = 5       # Javobdan keyin ko'rsatish (sekund)

# ── Fanlar ro'yxati ───────────────────────────────────────
SUBJECTS = [
    "Matematika", "Fizika", "Kimyo", "Biologiya",
    "Tarix", "Geografiya", "Ingliz tili", "Rus tili",
    "Ona tili", "Informatika", "Adabiyot", "Huquq",
    "Iqtisodiyot", "Boshqa",
]

# ── Qiyinlik darajalari ───────────────────────────────────
DIFFICULTY_LEVELS = {
    "easy":   "🟢 Oson",
    "medium": "🟡 O'rtacha",
    "hard":   "🔴 Qiyin",
    "expert": "⚡ Ekspert",
}

# ── Telegram Web App URL ──────────────────────────────────
# GitHub Pages URL: https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/webapp_pages
# Yoki boshqa hosting URL (HTTPS bo'lishi SHART)
WEBAPP_BASE_URL: str = _s("WEBAPP_BASE_URL", "").rstrip("/")

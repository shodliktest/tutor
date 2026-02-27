"""
🔥 FIREBASE KONFIGURATSIYA
st.secrets dan service account o'qiydi
"""
import json
import logging
import firebase_admin
from firebase_admin import credentials, firestore, storage

logger = logging.getLogger(__name__)

_db = None
_bucket = None
_initialized = False


def _get_service_account() -> dict:
    """
    Firebase Service Account JSON ni st.secrets dan olish.
    secrets.toml da [firebase_sa] bo'limi bo'lishi kerak.
    """
    try:
        import streamlit as st
        # Variant 1: [firebase_sa] bo'limi (tavsiya etiladi)
        if "firebase_sa" in st.secrets:
            sa = dict(st.secrets["firebase_sa"])
            # private_key ichidagi \\n ni \n ga almashtirish
            if "private_key" in sa:
                sa["private_key"] = sa["private_key"].replace("\\n", "\n")
            return sa

        # Variant 2: firebase_sa_json — butun JSON string
        if "firebase_sa_json" in st.secrets:
            return json.loads(st.secrets["firebase_sa_json"])

    except Exception:
        pass

    # Fallback: os.environ dan
    import os
    sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "{}")
    try:
        return json.loads(sa_json)
    except Exception:
        return {}


def initialize_firebase():
    """Firebase ni ishga tushirish (bir martaiki)"""
    global _db, _bucket, _initialized

    if _initialized:
        return True

    # Agar allaqachon boshqa app ishga tushirilgan bo'lsa
    if firebase_admin._apps:
        _db = firestore.client()
        from config import FIREBASE_CONFIG
        _bucket = storage.bucket("karoke-pro.firebasestorage.app")
        _initialized = True
        return True

    try:
        import os
        # Lokal: serviceAccountKey.json fayli bo'lsa
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
        else:
            sa = _get_service_account()
            if not sa:
                raise ValueError("Service Account ma'lumotlari topilmadi!")
            cred = credentials.Certificate(sa)

        from config import FIREBASE_CONFIG
        firebase_admin.initialize_app(cred, {
            "storageBucket": FIREBASE_CONFIG.get("storageBucket", "")
        })

        _db = firestore.client()
        _bucket = storage.bucket()
        _initialized = True
        logger.info("✅ Firebase muvaffaqiyatli ulandi!")
        return True

    except Exception as e:
        logger.error(f"❌ Firebase xatolik: {e}")
        return False


def get_db():
    global _db
    if not _initialized:
        initialize_firebase()
    return _db


def get_bucket():
    global _bucket
    return _bucket

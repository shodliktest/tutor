"""
🔥 FIREBASE KONFIGURATSIYA (YAKUNIY INTEGRATSIYA)
Web sayt (karoke-pro) bilan 100% bog'langan versiya.
"""
import json
import logging
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage

logger = logging.getLogger(__name__)

# Global o'zgaruvchilar
_db = None
_bucket = None
_initialized = False

def initialize_firebase():
    """Firebase Admin SDK ni ishga tushirish"""
    global _db, _bucket, _initialized

    if _initialized:
        return True

    try:
        # 1. Agar allaqachon boshqa joyda (masalan botda) ishga tushgan bo'lsa, shuni olamiz
        if firebase_admin._apps:
            _db = firestore.client()
            _bucket = storage.bucket("karoke-pro.firebasestorage.app")
            _initialized = True
            return True

        # 2. Secrets dan Service Account ma'lumotlarini olish
        if "firebase_sa" not in st.secrets:
            logger.error("❌ Streamlit Secrets ichida [firebase_sa] bo'limi topilmadi!")
            return False

        sa_info = dict(st.secrets["firebase_sa"])
        
        # Private key dagi xatoliklarni to'g'rilash (eng muhim joyi)
        if "private_key" in sa_info:
            sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")

        # 3. SDK ni konfiguratsiya bilan ishga tushirish
        cred = credentials.Certificate(sa_info)
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'karoke-pro.firebasestorage.app'
        })

        _db = firestore.client()
        _bucket = storage.bucket()
        _initialized = True
        
        logger.info("✅ Firebase Admin (karoke-pro) muvaffaqiyatli ishga tushdi!")
        return True

    except Exception as e:
        logger.error(f"❌ Firebase ulanishda jiddiy xatolik: {e}")
        return False

def get_db():
    """Baza ulanishini olish"""
    global _db
    if not _initialized:
        initialize_firebase()
    return _db

def get_bucket():
    """Fayl omborini olish"""
    global _bucket
    if not _initialized:
        initialize_firebase()
    return _bucket

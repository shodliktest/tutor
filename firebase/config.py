"""
🔥 FIREBASE KONFIGURATSIYA
"""
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
import logging
from config import FIREBASE_CONFIG
import os

logger = logging.getLogger(__name__)

_db = None
_bucket = None


def initialize_firebase():
    """Firebase ni ishga tushirish"""
    global _db, _bucket
    
    try:
        # Service account key fayli bilan ishga tushirish
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
        else:
            # Environment variable dan
            import json
            service_account = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT", "{}"))
            cred = credentials.Certificate(service_account)
        
        firebase_admin.initialize_app(cred, {
            'storageBucket': FIREBASE_CONFIG.get('storageBucket', '')
        })
        
        _db = firestore.client()
        _bucket = storage.bucket()
        
        logger.info("✅ Firebase muvaffaqiyatli ulandi!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Firebase xatolik: {e}")
        return False


def get_db():
    """Firestore client qaytarish"""
    global _db
    if _db is None:
        initialize_firebase()
    return _db


def get_bucket():
    """Storage bucket qaytarish"""
    global _bucket
    return _bucket

"""
🔥 FIREBASE KONFIGURATSIYA — Storage qo'shildi
"""
import json
import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore, storage

log = logging.getLogger(__name__)

_db = None
_bucket = None
_initialized = False


def _get_service_account() -> dict:
    try:
        import streamlit as st
        if "firebase_sa" in st.secrets:
            sa = dict(st.secrets["firebase_sa"])
            sa["private_key"] = sa.get("private_key", "").replace("\\n", "\n")
            return sa
        if "firebase_sa_json" in st.secrets:
            return json.loads(st.secrets["firebase_sa_json"])
    except Exception:
        pass
    try:
        return json.loads(os.environ.get("FIREBASE_SERVICE_ACCOUNT", "{}"))
    except Exception:
        return {}


def initialize_firebase() -> bool:
    global _db, _bucket, _initialized
    if _initialized:
        return True
    try:
        if firebase_admin._apps:
            _db = firestore.client()
            try:
                _bucket = storage.bucket()
            except Exception:
                pass
            _initialized = True
            return True

        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
        else:
            sa = _get_service_account()
            if not sa.get("project_id"):
                raise ValueError("Firebase credentials topilmadi!")
            cred = credentials.Certificate(sa)

        from config import FIREBASE_CFG
        storage_bucket = FIREBASE_CFG.get("storageBucket", "")
        firebase_admin.initialize_app(cred, {"storageBucket": storage_bucket})

        _db = firestore.client()
        try:
            _bucket = storage.bucket()
            log.info("✅ Firebase Storage ulandi")
        except Exception as e:
            log.warning(f"Storage ulanmadi: {e}")

        _initialized = True
        log.info("✅ Firebase ulandi")
        return True

    except Exception as e:
        log.error(f"❌ Firebase xatolik: {e}")
        return False


def get_db():
    global _db
    if not _initialized:
        initialize_firebase()
    return _db


def get_bucket():
    global _bucket
    if not _initialized:
        initialize_firebase()
    return _bucket

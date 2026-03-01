"""
📦 FIREBASE STORAGE — TXT format bilan samarali arxiv
Barcha testlar:          storage: db/tests_all.txt
Foydalanuvchi natijalari: storage: db/results_{user_id}.txt
Foydalanuvchilar:         storage: db/users_all.txt

Limit tejash strategiyasi:
  - O'qish: Streamlit session_state da 1 kun cache
  - Yozish: Faqat kuning oxirida (23:55) scheduler orqali
  - Bir test = bitta natija: oxirgisi saqlanadi
"""
import json
import logging

log = logging.getLogger(__name__)


def _bucket():
    """Firebase Storage bucket obyektini qaytarish."""
    import firebase_admin.storage as st
    return st.bucket()


# ═══════════════════════════════════════════════════════════
# TESTS — db/tests_all.txt
# ═══════════════════════════════════════════════════════════

TESTS_FILE = "db/tests_all.txt"


def upload_tests_txt(tests: list) -> bool:
    """
    Barcha testlarni bitta TXT faylga yoz.
    JSON format (ensure_ascii=False — o'zbek harflar to'g'ri ko'rinadi).
    """
    try:
        blob    = _bucket().blob(TESTS_FILE)
        content = json.dumps(tests, ensure_ascii=False, default=str)
        blob.upload_from_string(
            content.encode("utf-8"),
            content_type="text/plain; charset=utf-8"
        )
        log.info(f"✅ Tests Storage ga yuklandi: {len(tests)} ta → {TESTS_FILE}")
        return True
    except Exception as e:
        log.error(f"❌ Tests upload xato: {e}")
        return False


def download_tests_txt() -> list:
    """Firebase Storage dan barcha testlarni yuklab ol."""
    try:
        blob = _bucket().blob(TESTS_FILE)
        if not blob.exists():
            log.info(f"📭 {TESTS_FILE} mavjud emas, bo'sh ro'yxat")
            return []
        content = blob.download_as_bytes()
        tests   = json.loads(content.decode("utf-8"))
        log.info(f"✅ Tests Storage dan yuklandi: {len(tests)} ta")
        return tests
    except Exception as e:
        log.error(f"❌ Tests download xato: {e}")
        return []


# ═══════════════════════════════════════════════════════════
# USER RESULTS — db/results_{user_id}.txt
# Bir test uchun faqat bitta natija (oxirgisi)
# ═══════════════════════════════════════════════════════════

def _results_path(user_id: int) -> str:
    return f"db/results_{user_id}.txt"


def upload_user_results(user_id: int, results: list) -> bool:
    """
    Foydalanuvchi natijalarini Storage ga yoz.
    results: list of dict
    Bir test_id uchun faqat bitta natija — caller tomonidan filtrlanadi.
    """
    try:
        blob    = _bucket().blob(_results_path(user_id))
        content = json.dumps(results, ensure_ascii=False, default=str)
        blob.upload_from_string(
            content.encode("utf-8"),
            content_type="text/plain; charset=utf-8"
        )
        log.info(f"✅ User {user_id} natijalari yuklandi: {len(results)} ta")
        return True
    except Exception as e:
        log.error(f"❌ User {user_id} natijalar upload xato: {e}")
        return False


def download_user_results(user_id: int) -> list:
    """Firebase Storage dan foydalanuvchi natijalarini yuklab ol."""
    try:
        blob = _bucket().blob(_results_path(user_id))
        if not blob.exists():
            return []
        content = blob.download_as_bytes()
        results = json.loads(content.decode("utf-8"))
        log.info(f"✅ User {user_id} natijalari Storage dan yuklandi: {len(results)} ta")
        return results
    except Exception as e:
        log.error(f"❌ User {user_id} natijalar download xato: {e}")
        return []


# ═══════════════════════════════════════════════════════════
# USERS — db/users_all.txt
# ═══════════════════════════════════════════════════════════

USERS_FILE = "db/users_all.txt"


def upload_users_txt(users: list) -> bool:
    """Barcha foydalanuvchilarni bitta TXT faylga yoz."""
    try:
        blob    = _bucket().blob(USERS_FILE)
        content = json.dumps(users, ensure_ascii=False, default=str)
        blob.upload_from_string(
            content.encode("utf-8"),
            content_type="text/plain; charset=utf-8"
        )
        log.info(f"✅ Users Storage ga yuklandi: {len(users)} ta")
        return True
    except Exception as e:
        log.error(f"❌ Users upload xato: {e}")
        return False


def download_users_txt() -> list:
    """Firebase Storage dan foydalanuvchilarni yuklab ol."""
    try:
        blob = _bucket().blob(USERS_FILE)
        if not blob.exists():
            return []
        content = blob.download_as_bytes()
        users   = json.loads(content.decode("utf-8"))
        log.info(f"✅ Users Storage dan yuklandi: {len(users)} ta")
        return users
    except Exception as e:
        log.error(f"❌ Users download xato: {e}")
        return []

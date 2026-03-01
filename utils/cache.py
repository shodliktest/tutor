"""
🗄️ LOCAL CACHE — Streamlit session_state + kunlik Firebase sync
══════════════════════════════════════════════════════════════
MAQSAD: Firebase limit tejash

QOIDALAR:
  ✅ Testlar  → 1 marta/kun Storage dan yuklanadi, session_state da saqlanadi
  ✅ Natijalar → session_state da to'planadi, 23:55 da Storage ga sync
  ✅ 1 test   → 1 natija (oxirgisi)
  ✅ Yangi test/natija → Firestore ga ham yoziladi (kichik doc)
══════════════════════════════════════════════════════════════
"""
import streamlit as st
import logging
from datetime import datetime, timezone, date
from typing import Optional

log = logging.getLogger(__name__)
UTC = timezone.utc

# ── Cache kalitlari ───────────────────────────────────────
_TESTS_KEY   = "_c_tests"
_TESTS_DATE  = "_c_tests_date"
_RES_KEY     = "_c_results"       # {uid_str: [result,...]}
_RES_DATE    = "_c_results_date"  # {uid_str: date_str}
_PENDING_KEY = "_c_pending"       # {uid_str: {test_id: result}}
_USERS_KEY   = "_c_users"
_USERS_DATE  = "_c_users_date"


def _today() -> str:
    return date.today().isoformat()


# ═══════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════

def get_tests_cached() -> list:
    """
    Testlarni olish (3 qatlam):
      1. Bugun yuklangan → session_state
      2. Firebase Storage TXT → yuklab ol, cache
      3. Firestore fallback
    """
    if (st.session_state.get(_TESTS_KEY) is not None
            and st.session_state.get(_TESTS_DATE) == _today()):
        return st.session_state[_TESTS_KEY]

    # Firebase Storage
    try:
        from firebase.storage import download_tests_txt
        tests = download_tests_txt()
        if tests:
            st.session_state[_TESTS_KEY]  = tests
            st.session_state[_TESTS_DATE] = _today()
            return tests
    except Exception as e:
        log.warning(f"Storage yuklanmadi, Firestore fallback: {e}")

    # Firestore fallback
    try:
        from firebase.db import get_all_tests
        tests = get_all_tests()
        st.session_state[_TESTS_KEY]  = tests
        st.session_state[_TESTS_DATE] = _today()
        return tests
    except Exception as e:
        log.error(f"Testlar yuklanmadi: {e}")
        return []


def get_test_cached(test_id: str) -> Optional[dict]:
    """Bitta testni cache dan qidir, topilmasa Firestore."""
    for t in get_tests_cached():
        if t.get("test_id") == test_id:
            return t

    try:
        from firebase.db import get_test
        t = get_test(test_id)
        if t:
            cur = [x for x in st.session_state.get(_TESTS_KEY, [])
                   if x.get("test_id") != test_id]
            cur.append(t)
            st.session_state[_TESTS_KEY] = cur
        return t
    except Exception as e:
        log.error(f"get_test_cached xato: {e}")
        return None


def invalidate_tests_cache():
    """Test qo'shilganda / o'chirilganda cacheni tozala."""
    st.session_state.pop(_TESTS_KEY, None)
    st.session_state.pop(_TESTS_DATE, None)


def schedule_tests_upload():
    """Kunlik: barcha testlarni Storage ga sync. Scheduler chaqiradi."""
    try:
        from firebase.db import get_all_tests
        from firebase.storage import upload_tests_txt
        tests = get_all_tests()
        if tests:
            upload_tests_txt(tests)
            log.info(f"🌙 Kunlik tests sync: {len(tests)} ta")
    except Exception as e:
        log.error(f"Tests sync xato: {e}")


# ═══════════════════════════════════════════════════════════
# USER RESULTS
# ═══════════════════════════════════════════════════════════

def get_user_results_cached(user_id: int) -> list:
    """
    Foydalanuvchi natijalarini olish (3 qatlam):
      1. Bugun yuklangan → session_state
      2. Firebase Storage TXT
      3. Firestore fallback
    """
    uid_s    = str(user_id)
    res_map  = st.session_state.get(_RES_KEY, {})
    date_map = st.session_state.get(_RES_DATE, {})

    if uid_s in res_map and date_map.get(uid_s) == _today():
        return res_map[uid_s]

    # Firebase Storage
    try:
        from firebase.storage import download_user_results
        results = download_user_results(user_id)
        if results:
            _set_results_cache(uid_s, results)
            return results
    except Exception as e:
        log.warning(f"Storage results yuklanmadi: {e}")

    # Firestore fallback
    try:
        from firebase.db import get_user_results
        results = get_user_results(user_id, limit=200)
        _set_results_cache(uid_s, results)
        return results
    except Exception as e:
        log.error(f"Natijalar yuklanmadi: {e}")
        return []


def _set_results_cache(uid_s: str, results: list):
    if _RES_KEY not in st.session_state:
        st.session_state[_RES_KEY]  = {}
        st.session_state[_RES_DATE] = {}
    st.session_state[_RES_KEY][uid_s]  = results
    st.session_state[_RES_DATE][uid_s] = _today()


def add_pending_result(user_id: int, test_id: str, result: dict):
    """
    Yangi natijani pending ro'yxatga qo'sh.
    Bir test uchun faqat bitta natija — yangi kelsa eskisi o'chadi.
    """
    if _PENDING_KEY not in st.session_state:
        st.session_state[_PENDING_KEY] = {}

    uid_s = str(user_id)
    if uid_s not in st.session_state[_PENDING_KEY]:
        st.session_state[_PENDING_KEY][uid_s] = {}

    result["synced"]   = False
    result["added_at"] = datetime.now(UTC).isoformat()
    st.session_state[_PENDING_KEY][uid_s][test_id] = result

    # Session cache ni ham yangilaymiz
    if _RES_KEY not in st.session_state:
        st.session_state[_RES_KEY] = {}
    existing = [r for r in st.session_state[_RES_KEY].get(uid_s, [])
                if r.get("test_id") != test_id]
    existing.insert(0, result)
    st.session_state[_RES_KEY][uid_s] = existing


def get_last_result_for_test(user_id: int, test_id: str) -> Optional[dict]:
    """Berilgan test uchun foydalanuvchining so'nggi natijasini qaytarish."""
    uid_s   = str(user_id)
    pending = st.session_state.get(_PENDING_KEY, {})
    if uid_s in pending and test_id in pending[uid_s]:
        return pending[uid_s][test_id]

    for r in get_user_results_cached(user_id):
        if r.get("test_id") == test_id:
            return r
    return None


def sync_pending_results():
    """
    Kunlik: pending natijalarni Firebase Storage ga yuk.
    Bir test = bitta natija: oxirgisi qoladi.
    """
    pending = st.session_state.get(_PENDING_KEY, {})
    if not pending:
        log.info("Sync: pending natijalar yo'q")
        return

    from firebase.storage import download_user_results, upload_user_results

    for uid_s, test_results in list(pending.items()):
        try:
            user_id  = int(uid_s)
            existing = download_user_results(user_id)
            # Mavjud natijalarni map ga o'tkazamiz
            ex_map = {r.get("test_id"): r for r in existing}
            # Pending yangiroq — ustiga yozamiz
            ex_map.update(test_results)
            merged = list(ex_map.values())
            upload_user_results(user_id, merged)
            log.info(f"🌙 User {uid_s} natijalari sync: {len(merged)} ta")
        except Exception as e:
            log.error(f"User {uid_s} sync xato: {e}")


# ═══════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════

def get_users_cached() -> list:
    """Foydalanuvchilarni 1 marta/kun yuklab olish."""
    if (st.session_state.get(_USERS_KEY) is not None
            and st.session_state.get(_USERS_DATE) == _today()):
        return st.session_state[_USERS_KEY]

    try:
        from firebase.storage import download_users_txt
        users = download_users_txt()
        if users:
            st.session_state[_USERS_KEY]  = users
            st.session_state[_USERS_DATE] = _today()
            return users
    except Exception:
        pass

    try:
        from firebase.db import get_all_users
        users = get_all_users()
        st.session_state[_USERS_KEY]  = users
        st.session_state[_USERS_DATE] = _today()
        return users
    except Exception as e:
        log.error(f"Users yuklanmadi: {e}")
        return []

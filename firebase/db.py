"""
🗄️ FIREBASE DATABASE — TXT fayl asosida saqlash + kesh
Arxitektura:
  - Testlar: Firebase Storage da "tests.txt" (JSON lines)
  - Foydalanuvchilar: Storage da "users.txt"
  - Natijalar: Firestore results_latest koleksiyasi (uid_testid doc)
  
  Kesh qoidalari:
  - Testlar: kun davomida 1 marta yuklanadi
  - Har test uchun faqat 1 natija (oxirgi) saqlanadi
  - Kuning oxirida batch flush
"""
import json
import uuid
import logging
from datetime import datetime, timezone, date
from firebase.config import get_db, get_bucket

log = logging.getLogger(__name__)
UTC = timezone.utc

# ── In-memory kesh ────────────────────────────────────────
_tests_cache: dict = {}
_tests_loaded_date: str = ""
_users_cache: dict = {}
_users_loaded_date: str = ""
_results_cache: dict = {}    # {uid_s: {test_id: result}}
_pending_results: dict = {}
_pending_users: dict = {}
_new_tests: dict = {}        # yangi yaratilgan testlar
_leaderboard_cache: dict = {}


def _today() -> str:
    return date.today().isoformat()


# ══════════════════════════════════════════════════════════
# STORAGE HELPERS
# ══════════════════════════════════════════════════════════

def _load_txt(filename: str) -> list:
    try:
        bucket = get_bucket()
        if not bucket:
            return []
        blob = bucket.blob(filename)
        if not blob.exists():
            return []
        content = blob.download_as_text(encoding="utf-8")
        result = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if line:
                try:
                    result.append(json.loads(line))
                except Exception:
                    pass
        return result
    except Exception as e:
        log.error(f"Storage yuklash ({filename}): {e}")
        return []


def _save_txt(filename: str, records: list) -> bool:
    try:
        bucket = get_bucket()
        if not bucket:
            return False
        lines = "\n".join(json.dumps(r, ensure_ascii=False, default=str) for r in records)
        blob = bucket.blob(filename)
        blob.upload_from_string(lines.encode("utf-8"), content_type="text/plain; charset=utf-8")
        log.info(f"Storage: {filename} ← {len(records)} ta yozuv")
        return True
    except Exception as e:
        log.error(f"Storage yozish ({filename}): {e}")
        return False


# ══════════════════════════════════════════════════════════
# TESTLAR
# ══════════════════════════════════════════════════════════

def _ensure_tests():
    global _tests_cache, _tests_loaded_date
    today = _today()
    if _tests_loaded_date == today and _tests_cache:
        return
    records = _load_txt("tests.txt")
    _tests_cache = {t["test_id"]: t for t in records if t.get("test_id") and t.get("is_active", True)}
    _tests_cache.update(_new_tests)
    _tests_loaded_date = today


def get_test(tid: str):
    _ensure_tests()
    t = _tests_cache.get(tid) or _new_tests.get(tid)
    return t if t and t.get("is_active", True) else None


def get_public_tests(limit: int = 100) -> list:
    _ensure_tests()
    all_t = list(_tests_cache.values())
    res = [t for t in all_t if t.get("visibility") == "public" and t.get("is_active", True)]
    res.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return res[:limit]


def get_all_tests(limit: int = 300) -> list:
    _ensure_tests()
    all_t = sorted(_tests_cache.values(), key=lambda x: x.get("created_at", ""), reverse=True)
    return list(all_t)[:limit]


def get_my_tests(creator_id: int) -> list:
    _ensure_tests()
    res = [t for t in _tests_cache.values()
           if t.get("creator_id") == creator_id and t.get("is_active", True)]
    res.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return res


def create_test(creator_id: int, data: dict) -> str:
    global _new_tests
    tid = str(uuid.uuid4())[:8].upper()
    doc = {
        "test_id": tid, "creator_id": creator_id,
        "title": data.get("title", "Nomsiz"),
        "category": data.get("category", "Boshqa"),
        "difficulty": data.get("difficulty", "medium"),
        "visibility": data.get("visibility", "public"),
        "time_limit": data.get("time_limit", 0),
        "poll_time": data.get("poll_time", 30),
        "passing_score": data.get("passing_score", 60),
        "max_attempts": data.get("max_attempts", 0),
        "questions": data.get("questions", []),
        "question_count": len(data.get("questions", [])),
        "solve_count": 0, "avg_score": 0.0, "is_active": True,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    _new_tests[tid] = doc
    _tests_cache[tid] = doc
    return tid


def delete_test(tid: str):
    if tid in _tests_cache:
        _tests_cache[tid]["is_active"] = False
    if tid in _new_tests:
        _new_tests[tid]["is_active"] = False


def _update_test_stats(tid: str, pct: float):
    t = _tests_cache.get(tid)
    if t:
        total = t.get("solve_count", 0) + 1
        avg = ((t.get("avg_score", 0) * (total - 1)) + pct) / total
        t["solve_count"] = total
        t["avg_score"] = round(avg, 1)


def flush_tests_to_storage():
    global _new_tests
    if not _new_tests:
        return
    existing = _load_txt("tests.txt")
    ex_ids = {t.get("test_id") for t in existing}
    for tid, t in _new_tests.items():
        if tid not in ex_ids:
            existing.append(t)
    if _save_txt("tests.txt", existing):
        _new_tests.clear()


# ══════════════════════════════════════════════════════════
# FOYDALANUVCHILAR
# ══════════════════════════════════════════════════════════

def _ensure_users():
    global _users_cache, _users_loaded_date
    today = _today()
    if _users_loaded_date == today and _users_cache:
        return
    records = _load_txt("users.txt")
    _users_cache = {str(r["telegram_id"]): r for r in records if r.get("telegram_id")}
    _users_loaded_date = today


def get_user(tg_id: int):
    _ensure_users()
    return _users_cache.get(str(tg_id))


def create_user(tg_id: int, name: str, username: str = None, role: str = "user") -> dict:
    _ensure_users()
    data = {
        "telegram_id": tg_id, "name": name, "username": username,
        "role": role, "is_blocked": False,
        "total_tests": 0, "total_score": 0.0, "avg_score": 0.0,
        "badges": [], "streak_days": 0,
        "created_at": datetime.now(UTC).isoformat(),
        "last_active": datetime.now(UTC).isoformat(),
    }
    _users_cache[str(tg_id)] = data
    _pending_users[tg_id] = data
    return data


def update_user(tg_id: int, data: dict):
    _ensure_users()
    uid_s = str(tg_id)
    existing = _users_cache.get(uid_s, {})
    existing.update(data)
    existing["last_active"] = datetime.now(UTC).isoformat()
    _users_cache[uid_s] = existing
    _pending_users[tg_id] = existing


def get_all_users(limit: int = 500) -> list:
    _ensure_users()
    return list(_users_cache.values())[:limit]


def block_user(tg_id: int, blocked: bool = True):
    update_user(tg_id, {"is_blocked": blocked})


def _update_user_stats(uid: int, pct: float):
    uid_s = str(uid)
    u = _users_cache.get(uid_s, {})
    total = u.get("total_tests", 0) + 1
    score = u.get("total_score", 0.0) + pct
    u["total_tests"] = total
    u["total_score"] = score
    u["avg_score"] = round(score / total, 1)
    u["last_active"] = datetime.now(UTC).isoformat()
    _users_cache[uid_s] = u
    _pending_users[uid] = u


def flush_users_to_storage():
    global _pending_users
    if not _pending_users:
        return
    existing = _load_txt("users.txt")
    ex_map = {str(u.get("telegram_id")): i for i, u in enumerate(existing)}
    for uid, udata in _pending_users.items():
        uid_s = str(uid)
        if uid_s in ex_map:
            existing[ex_map[uid_s]] = udata
        else:
            existing.append(udata)
    if _save_txt("users.txt", existing):
        _pending_users.clear()


# ══════════════════════════════════════════════════════════
# NATIJALAR — Firestore (results_latest)
# Har test uchun 1 ta: document ID = "uid_testid"
# ══════════════════════════════════════════════════════════

def save_result(user_id: int, test_id: str, res: dict) -> str:
    uid_s = str(user_id)
    rid = str(uuid.uuid4())
    pct = res.get("percentage", 0)
    passing = res.get("passing_score", 60)

    doc = {
        "result_id": rid, "user_id": user_id, "test_id": test_id,
        "percentage": pct,
        "correct_count": res.get("correct_answers", res.get("correct_count", 0)),
        "total_questions": res.get("total_questions", 0),
        "time_spent": res.get("time_spent", 0),
        "passed": pct >= passing, "passing_score": passing,
        "detailed_results": res.get("detailed_results", []),
        "mode": res.get("mode", "inline"),
        "completed_at": datetime.now(UTC).isoformat(),
    }

    # Keshga saqlash
    if uid_s not in _results_cache:
        _results_cache[uid_s] = {}
    _results_cache[uid_s][test_id] = doc

    if uid_s not in _pending_results:
        _pending_results[uid_s] = {}
    _pending_results[uid_s][test_id] = doc

    # Statistika
    _update_test_stats(test_id, pct)
    _update_user_stats(user_id, pct)
    _update_leaderboard(user_id, test_id, pct)

    # Firestore ga yozish
    try:
        save_doc = {k: v for k, v in doc.items() if k != "detailed_results"}
        get_db().collection("results_latest").document(f"{user_id}_{test_id}").set(save_doc)
    except Exception as e:
        log.warning(f"Firestore result: {e}")

    return rid


def get_user_results(user_id: int, limit: int = 50) -> list:
    uid_s = str(user_id)
    # Avval keshdan
    if uid_s in _results_cache and _results_cache[uid_s]:
        res = sorted(_results_cache[uid_s].values(),
                     key=lambda x: x.get("completed_at", ""), reverse=True)
        return res[:limit]
    # Firestore dan
    try:
        docs = list(
            get_db().collection("results_latest")
            .where("user_id", "==", user_id).limit(200).stream()
        )
        res = [d.to_dict() for d in docs]
        res.sort(key=lambda x: x.get("completed_at", ""), reverse=True)
        _results_cache[uid_s] = {r["test_id"]: r for r in res}
        return res[:limit]
    except Exception as e:
        log.error(f"get_user_results: {e}")
        return []


def get_result_by_id(result_id: str):
    for uid_res in _results_cache.values():
        for r in uid_res.values():
            if r.get("result_id") == result_id:
                return r
    try:
        docs = list(
            get_db().collection("results_latest")
            .where("result_id", "==", result_id).limit(1).stream()
        )
        return docs[0].to_dict() if docs else None
    except Exception:
        return None


def get_attempt_count(user_id: int, test_id: str) -> int:
    uid_s = str(user_id)
    if uid_s in _results_cache and test_id in _results_cache[uid_s]:
        return 1
    return 0


def flush_results_to_storage():
    global _pending_results
    if not _pending_results:
        return
    db = get_db()
    batch = db.batch()
    count = 0
    for uid_s, test_results in _pending_results.items():
        for test_id, result in test_results.items():
            ref = db.collection("results_latest").document(f"{uid_s}_{test_id}")
            batch.set(ref, {k: v for k, v in result.items() if k != "detailed_results"})
            count += 1
    try:
        batch.commit()
        _pending_results.clear()
        log.info(f"✅ {count} ta natija Firestore ga yozildi")
    except Exception as e:
        log.error(f"Batch commit: {e}")


# ══════════════════════════════════════════════════════════
# LEADERBOARD
# ══════════════════════════════════════════════════════════

def _update_leaderboard(uid: int, test_id: str, pct: float):
    key = f"{uid}_{test_id}"
    existing = _leaderboard_cache.get(key, {})
    if pct > existing.get("best_percentage", 0):
        u = _users_cache.get(str(uid), {})
        entry = {
            "user_id": uid, "user_name": u.get("name", "Noma'lum"),
            "test_id": test_id, "best_percentage": pct,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        _leaderboard_cache[key] = entry
        try:
            get_db().collection("leaderboard").document(key).set(entry)
        except Exception:
            pass


def get_leaderboard_by_test(tid: str, limit: int = 10) -> list:
    # Avval keshdan
    cache_entries = [v for k, v in _leaderboard_cache.items() if v.get("test_id") == tid]
    if cache_entries:
        cache_entries.sort(key=lambda x: x.get("best_percentage", 0), reverse=True)
        return cache_entries[:limit]
    try:
        docs = list(
            get_db().collection("leaderboard")
            .where("test_id", "==", tid).limit(50).stream()
        )
        res = [d.to_dict() for d in docs]
        res.sort(key=lambda x: x.get("best_percentage", 0), reverse=True)
        return res[:limit]
    except Exception:
        return []


def get_global_leaderboard(limit: int = 20) -> list:
    _ensure_users()
    docs = [u for u in _users_cache.values() if u.get("total_tests", 0) > 0]
    docs.sort(key=lambda x: x.get("avg_score", 0), reverse=True)
    return docs[:limit]


# ══════════════════════════════════════════════════════════
# KUNLIK FLUSH
# ══════════════════════════════════════════════════════════

def flush_all_to_storage():
    """Barcha pending ma'lumotlarni yozish"""
    log.info("🔄 Kunlik flush...")
    flush_tests_to_storage()
    flush_users_to_storage()
    flush_results_to_storage()
    log.info("✅ Kunlik flush tugadi")

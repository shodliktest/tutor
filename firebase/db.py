"""
🗄️ FIREBASE DATABASE — barcha CRUD operatsiyalar
Composite index kerak emas: faqat bitta where() ishlatiladi
"""
from firebase.config import get_db
from datetime import datetime, timezone
import uuid
import logging

log = logging.getLogger(__name__)
UTC = timezone.utc

def _safe_dt(val):
    """Offset-naive va offset-aware datetime ni bir xil ko'rinishga keltirish"""
    if val is None:
        return datetime.min.replace(tzinfo=UTC)
    if hasattr(val, "tzinfo"):
        return val if val.tzinfo else val.replace(tzinfo=UTC)
    return datetime.min.replace(tzinfo=UTC)


# ═══════════════════════════════════════════════════════════
# USERS (FOYDALANUVCHILAR)
# ═══════════════════════════════════════════════════════════

def create_user(tg_id: int, name: str, username: str = None, role: str = "user") -> dict:
    data = {
        "telegram_id": tg_id,
        "name": name,
        "username": username,
        "role": role,
        "is_blocked": False,
        "total_tests": 0,
        "total_score": 0.0,
        "avg_score": 0.0,
        "badges": [],
        "streak_days": 0,
        "created_at": datetime.now(UTC),
        "last_active": datetime.now(UTC),
    }
    get_db().collection("users").document(str(tg_id)).set(data)
    return data


def get_user(tg_id: int) -> dict | None:
    doc = get_db().collection("users").document(str(tg_id)).get()
    return doc.to_dict() if doc.exists else None


def update_user(tg_id: int, data: dict):
    data["last_active"] = datetime.now(UTC)
    get_db().collection("users").document(str(tg_id)).update(data)


def get_all_users(limit: int = 500) -> list:
    return [d.to_dict() for d in get_db().collection("users").limit(limit).stream()]


def block_user(tg_id: int, blocked: bool = True):
    get_db().collection("users").document(str(tg_id)).update({
        "is_blocked": blocked,
        "last_active": datetime.now(UTC),
    })


# ═══════════════════════════════════════════════════════════
# TESTS (TESTLAR)
# ═══════════════════════════════════════════════════════════

def create_test(creator_id: int, data: dict) -> str:
    db = get_db()
    tid = str(uuid.uuid4())[:8].upper()
    doc = {
        "test_id":        tid,
        "creator_id":     creator_id,
        "title":          data.get("title", "Nomsiz"),
        "category":       data.get("category", "Boshqa"),
        "difficulty":     data.get("difficulty", "medium"),
        "visibility":     data.get("visibility", "public"),
        "time_limit":     data.get("time_limit", 0),
        "passing_score":  data.get("passing_score", 60),
        "max_attempts":   data.get("max_attempts", 0),
        "questions":      data.get("questions", []),
        "question_count": len(data.get("questions", [])),
        "solve_count":    0,
        "avg_score":      0.0,
        "is_active":      True,
        "created_at":     datetime.now(UTC),
        "updated_at":     datetime.now(UTC),
    }
    db.collection("tests").document(tid).set(doc)
    return tid


def get_test(tid: str) -> dict | None:
    doc = get_db().collection("tests").document(tid).get()
    if not doc.exists:
        return None
    d = doc.to_dict()
    # Soft-deleted testlarni qaytarmaymiz
    if not d.get("is_active", True):
        return None
    return d


def get_all_tests(limit: int = 300) -> list:
    docs = [d.to_dict() for d in get_db().collection("tests").limit(limit).stream()]
    docs = [d for d in docs if d.get("is_active", True)]
    docs.sort(key=lambda x: _safe_dt(x.get("created_at")), reverse=True)
    return docs


def get_public_tests(limit: int = 100) -> list:
    docs = [d.to_dict() for d in
            get_db().collection("tests").where("visibility", "==", "public").limit(150).stream()]
    docs = [d for d in docs if d.get("is_active", True)]
    docs.sort(key=lambda x: _safe_dt(x.get("created_at")), reverse=True)
    return docs[:limit]


def get_tests_by_category(category: str, limit: int = 50) -> list:
    docs = [d.to_dict() for d in
            get_db().collection("tests").where("category", "==", category).limit(100).stream()]
    docs = [d for d in docs if d.get("is_active", True) and d.get("visibility") == "public"]
    docs.sort(key=lambda x: _safe_dt(x.get("created_at")), reverse=True)
    return docs[:limit]


def get_my_tests(creator_id: int) -> list:
    docs = [d.to_dict() for d in
            get_db().collection("tests").where("creator_id", "==", creator_id).stream()]
    docs = [d for d in docs if d.get("is_active", True)]
    docs.sort(key=lambda x: _safe_dt(x.get("created_at")), reverse=True)
    return docs


def delete_test(tid: str):
    """Soft delete — test bazadan o'chirilmaydi, faqat is_active=False"""
    get_db().collection("tests").document(tid).update({
        "is_active": False,
        "updated_at": datetime.now(UTC),
    })


# ═══════════════════════════════════════════════════════════
# RESULTS (NATIJALAR)
# ═══════════════════════════════════════════════════════════

def save_result(user_id: int, test_id: str, res: dict) -> str:
    db = get_db()
    rid = str(uuid.uuid4())
    passing = res.get("passing_score", 60)
    passed  = res.get("percentage", 0) >= passing

    doc = {
        "result_id":        rid,
        "user_id":          user_id,
        "test_id":          test_id,
        "score":            res.get("score", 0),
        "percentage":       res.get("percentage", 0),
        "correct_count":    res.get("correct_count", 0),
        "wrong_count":      res.get("wrong_count", 0),
        "skipped_count":    res.get("skipped_count", 0),
        "total_questions":  res.get("total_questions", 0),
        "time_spent":       res.get("time_spent", 0),
        "passed":           passed,
        "passing_score":    passing,
        "detailed_results": res.get("detailed_results", []),
        "mode":             res.get("mode", "inline"),   # "inline" yoki "poll"
        "completed_at":     datetime.now(UTC),
    }
    db.collection("results").document(rid).set(doc)

    # Test statistikasini yangilash
    _update_test_stats(test_id, doc["percentage"])
    # User statistikasini yangilash
    _update_user_stats(user_id, doc["percentage"])
    # Leaderboard yangilash
    user = get_user(user_id)
    name = user.get("name", "Noma'lum") if user else "Noma'lum"
    _update_leaderboard(user_id, name, test_id, doc["percentage"])
    return rid


def get_user_results(user_id: int, limit: int = 20) -> list:
    docs = [d.to_dict() for d in
            get_db().collection("results").where("user_id", "==", user_id).limit(100).stream()]
    docs.sort(key=lambda x: _safe_dt(x.get("completed_at")), reverse=True)
    return docs[:limit]


def get_result_by_id(result_id: str) -> dict | None:
    doc = get_db().collection("results").document(result_id).get()
    return doc.to_dict() if doc.exists else None


def get_attempt_count(user_id: int, test_id: str) -> int:
    docs = list(get_db().collection("results")
                .where("user_id", "==", user_id)
                .where("test_id", "==", test_id).stream())
    return len(docs)


def _update_test_stats(tid: str, pct: float):
    ref = get_db().collection("tests").document(tid)
    d = ref.get().to_dict() or {}
    total = d.get("solve_count", 0) + 1
    avg   = ((d.get("avg_score", 0) * (total - 1)) + pct) / total
    ref.update({"solve_count": total, "avg_score": round(avg, 1)})


def _update_user_stats(uid: int, pct: float):
    ref  = get_db().collection("users").document(str(uid))
    d    = ref.get().to_dict() or {}
    total = d.get("total_tests", 0) + 1
    score = d.get("total_score", 0.0) + pct
    ref.update({
        "total_tests":  total,
        "total_score":  score,
        "avg_score":    round(score / total, 1),
        "last_active":  datetime.now(UTC),
    })


def _update_leaderboard(uid: int, name: str, tid: str, pct: float):
    db  = get_db()
    lid = f"{uid}_{tid}"
    doc = db.collection("leaderboard").document(lid).get()
    if doc.exists:
        if pct > doc.to_dict().get("best_percentage", 0):
            db.collection("leaderboard").document(lid).update({
                "best_percentage": pct,
                "updated_at": datetime.now(UTC),
            })
    else:
        db.collection("leaderboard").document(lid).set({
            "user_id":         uid,
            "user_name":       name,
            "test_id":         tid,
            "best_percentage": pct,
            "created_at":      datetime.now(UTC),
            "updated_at":      datetime.now(UTC),
        })


# ═══════════════════════════════════════════════════════════
# LEADERBOARD (REYTING)
# ═══════════════════════════════════════════════════════════

def get_leaderboard_by_test(tid: str, limit: int = 10) -> list:
    docs = [d.to_dict() for d in
            get_db().collection("leaderboard").where("test_id", "==", tid).limit(50).stream()]
    docs.sort(key=lambda x: x.get("best_percentage", 0), reverse=True)
    return docs[:limit]


def get_global_leaderboard(limit: int = 20) -> list:
    docs = [d.to_dict() for d in get_db().collection("users").limit(300).stream()]
    docs = [d for d in docs if d.get("total_tests", 0) > 0]
    docs.sort(key=lambda x: x.get("avg_score", 0), reverse=True)
    return docs[:limit]

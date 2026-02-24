"""
🗄️ FIREBASE DATABASE OPERATSIYALARI
Barcha CRUD operatsiyalar shu yerda
"""
from firebase_admin import firestore
from firebase.config import get_db
from datetime import datetime, timezone
import logging
import uuid

logger = logging.getLogger(__name__)


# ==================== FOYDALANUVCHILAR ====================

def create_user(telegram_id: int, name: str, username: str = None, role: str = "user"):
    """Yangi foydalanuvchi yaratish"""
    db = get_db()
    user_data = {
        "telegram_id": telegram_id,
        "name": name,
        "username": username,
        "role": role,  # user / teacher / admin
        "created_at": datetime.now(timezone.utc),
        "total_tests": 0,
        "total_score": 0,
        "badges": [],
        "is_blocked": False,
        "streak_days": 0,
        "last_active": datetime.now(timezone.utc)
    }
    db.collection("users").document(str(telegram_id)).set(user_data)
    return user_data


def get_user(telegram_id: int):
    """Foydalanuvchi ma'lumotini olish"""
    db = get_db()
    doc = db.collection("users").document(str(telegram_id)).get()
    if doc.exists:
        return doc.to_dict()
    return None


def update_user(telegram_id: int, data: dict):
    """Foydalanuvchi ma'lumotini yangilash"""
    db = get_db()
    data["last_active"] = datetime.now(timezone.utc)
    db.collection("users").document(str(telegram_id)).update(data)


def get_all_users(limit: int = 100):
    """Barcha foydalanuvchilar"""
    db = get_db()
    users = db.collection("users").limit(limit).stream()
    return [u.to_dict() for u in users]


def block_user(telegram_id: int, blocked: bool = True):
    """Foydalanuvchini bloklash/blokdan chiqarish"""
    update_user(telegram_id, {"is_blocked": blocked})


# ==================== TESTLAR ====================

def create_test(creator_id: int, test_data: dict) -> str:
    """Yangi test yaratish"""
    db = get_db()
    test_id = str(uuid.uuid4())[:8].upper()
    
    test = {
        "test_id": test_id,
        "creator_id": creator_id,
        "title": test_data.get("title", "Nomsiz test"),
        "description": test_data.get("description", ""),
        "subject": test_data.get("subject", "Boshqa"),
        "section": test_data.get("section", ""),
        "difficulty": test_data.get("difficulty", "medium"),
        "test_type": test_data.get("test_type", "multiple_choice"),
        "visibility": test_data.get("visibility", "public"),  # public/link/private
        "time_limit": test_data.get("time_limit", 30),  # daqiqa
        "passing_score": test_data.get("passing_score", 60),  # foiz
        "max_attempts": test_data.get("max_attempts", 3),
        "shuffle_questions": test_data.get("shuffle_questions", True),
        "shuffle_options": test_data.get("shuffle_options", True),
        "show_answers": test_data.get("show_answers", True),
        "questions": test_data.get("questions", []),
        "question_count": len(test_data.get("questions", [])),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True,
        "total_attempts": 0,
        "avg_score": 0,
        "pass_rate": 0,
    }
    
    db.collection("tests").document(test_id).set(test)
    logger.info(f"✅ Test yaratildi: {test_id}")
    return test_id


def get_test(test_id: str) -> dict:
    """Test ma'lumotini olish"""
    db = get_db()
    doc = db.collection("tests").document(test_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


def get_tests_by_subject(subject: str, limit: int = 20) -> list:
    """Fan bo'yicha testlar"""
    db = get_db()
    tests = (db.collection("tests")
             .where("subject", "==", subject)
             .where("visibility", "==", "public")
             .where("is_active", "==", True)
             .limit(limit)
             .stream())
    return [t.to_dict() for t in tests]


def get_all_tests(limit: int = 50) -> list:
    """Barcha ommaviy testlar"""
    db = get_db()
    tests = (db.collection("tests")
             .where("visibility", "==", "public")
             .where("is_active", "==", True)
             .order_by("created_at", direction=firestore.Query.DESCENDING)
             .limit(limit)
             .stream())
    return [t.to_dict() for t in tests]


def get_my_tests(creator_id: int) -> list:
    """Mening testlarim"""
    db = get_db()
    tests = (db.collection("tests")
             .where("creator_id", "==", creator_id)
             .order_by("created_at", direction=firestore.Query.DESCENDING)
             .stream())
    return [t.to_dict() for t in tests]


def update_test(test_id: str, data: dict):
    """Test ma'lumotini yangilash"""
    db = get_db()
    data["updated_at"] = datetime.now(timezone.utc)
    db.collection("tests").document(test_id).update(data)


def delete_test(test_id: str):
    """Testni o'chirish (soft delete)"""
    update_test(test_id, {"is_active": False})


# ==================== NATIJALAR ====================

def save_result(user_id: int, test_id: str, result_data: dict) -> str:
    """Natijani saqlash"""
    db = get_db()
    result_id = f"{user_id}_{test_id}_{int(datetime.now().timestamp())}"
    
    result = {
        "result_id": result_id,
        "user_id": user_id,
        "test_id": test_id,
        "score": result_data.get("score", 0),
        "percentage": result_data.get("percentage", 0),
        "correct_count": result_data.get("correct_count", 0),
        "wrong_count": result_data.get("wrong_count", 0),
        "skipped_count": result_data.get("skipped_count", 0),
        "total_questions": result_data.get("total_questions", 0),
        "time_spent": result_data.get("time_spent", 0),  # sekund
        "answers": result_data.get("answers", {}),
        "passed": result_data.get("percentage", 0) >= result_data.get("passing_score", 60),
        "attempt_number": result_data.get("attempt_number", 1),
        "completed_at": datetime.now(timezone.utc),
    }
    
    db.collection("results").document(result_id).set(result)
    
    # Test statistikasini yangilash
    _update_test_stats(test_id, result["percentage"])
    # Foydalanuvchi statistikasini yangilash
    _update_user_stats(user_id, result["percentage"], result["passed"])
    # Leaderboard yangilash
    _update_leaderboard(user_id, test_id, result["percentage"], result["score"])
    
    return result_id


def get_user_results(user_id: int, limit: int = 20) -> list:
    """Foydalanuvchi natijalari"""
    db = get_db()
    results = (db.collection("results")
               .where("user_id", "==", user_id)
               .order_by("completed_at", direction=firestore.Query.DESCENDING)
               .limit(limit)
               .stream())
    return [r.to_dict() for r in results]


def get_test_results(test_id: str, limit: int = 50) -> list:
    """Test natijalari"""
    db = get_db()
    results = (db.collection("results")
               .where("test_id", "==", test_id)
               .order_by("percentage", direction=firestore.Query.DESCENDING)
               .limit(limit)
               .stream())
    return [r.to_dict() for r in results]


def get_attempt_count(user_id: int, test_id: str) -> int:
    """Foydalanuvchining testga urinishlar soni"""
    db = get_db()
    results = (db.collection("results")
               .where("user_id", "==", user_id)
               .where("test_id", "==", test_id)
               .stream())
    return len(list(results))


def _update_test_stats(test_id: str, new_percentage: float):
    """Test statistikasini yangilash"""
    db = get_db()
    test_ref = db.collection("tests").document(test_id)
    
    @firestore.transactional
    def update_in_transaction(transaction, test_ref):
        snapshot = test_ref.get(transaction=transaction)
        if snapshot.exists:
            data = snapshot.to_dict()
            total = data.get("total_attempts", 0) + 1
            old_avg = data.get("avg_score", 0)
            new_avg = ((old_avg * (total - 1)) + new_percentage) / total
            pass_rate = data.get("pass_rate", 0)
            
            transaction.update(test_ref, {
                "total_attempts": total,
                "avg_score": round(new_avg, 1),
            })
    
    transaction = db.transaction()
    update_in_transaction(transaction, test_ref)


def _update_user_stats(user_id: int, percentage: float, passed: bool):
    """Foydalanuvchi statistikasini yangilash"""
    db = get_db()
    user_ref = db.collection("users").document(str(user_id))
    
    doc = user_ref.get()
    if doc.exists:
        data = doc.to_dict()
        total_tests = data.get("total_tests", 0) + 1
        total_score = data.get("total_score", 0) + percentage
        
        user_ref.update({
            "total_tests": total_tests,
            "total_score": total_score,
            "avg_score": round(total_score / total_tests, 1),
            "last_active": datetime.now(timezone.utc)
        })


def _update_leaderboard(user_id: int, test_id: str, percentage: float, score: float):
    """Leaderboard yangilash"""
    db = get_db()
    lb_id = f"{user_id}_{test_id}"
    
    existing = db.collection("leaderboard").document(lb_id).get()
    
    if existing.exists:
        current_best = existing.to_dict().get("best_percentage", 0)
        if percentage > current_best:
            db.collection("leaderboard").document(lb_id).update({
                "best_percentage": percentage,
                "best_score": score,
                "updated_at": datetime.now(timezone.utc)
            })
    else:
        user = get_user(user_id)
        db.collection("leaderboard").document(lb_id).set({
            "user_id": user_id,
            "user_name": user.get("name", "Noma'lum") if user else "Noma'lum",
            "test_id": test_id,
            "best_percentage": percentage,
            "best_score": score,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })


# ==================== LEADERBOARD ====================

def get_leaderboard_by_test(test_id: str, limit: int = 10) -> list:
    """Test bo'yicha leaderboard"""
    db = get_db()
    results = (db.collection("leaderboard")
               .where("test_id", "==", test_id)
               .order_by("best_percentage", direction=firestore.Query.DESCENDING)
               .limit(limit)
               .stream())
    return [r.to_dict() for r in results]


def get_global_leaderboard(limit: int = 20) -> list:
    """Umumiy leaderboard - avg_score bo'yicha"""
    db = get_db()
    users = (db.collection("users")
             .where("total_tests", ">", 0)
             .order_by("total_tests")
             .order_by("avg_score", direction=firestore.Query.DESCENDING)
             .limit(limit)
             .stream())
    return [u.to_dict() for u in users]

"""
🗄️ FIREBASE DATABASE OPERATSIYALARI (TO'LIQ VERSIYA)
Barcha filtrlash, ma'lumotlarni saqlash va reyting hisoblash funksiyalari
"""
from firebase.config import get_db
from datetime import datetime, timezone
from google.cloud import firestore
import logging
import uuid

logger = logging.getLogger(__name__)

# ==========================================================
# 1. FOYDALANUVCHILAR (USERS) OPERATSIYALARI
# ==========================================================

def create_user(telegram_id: int, name: str, username: str = None, role: str = "user"):
    db = get_db()
    user_data = {
        "telegram_id": telegram_id,
        "name": name,
        "username": username,
        "role": role,
        "created_at": datetime.now(timezone.utc),
        "total_tests": 0,
        "total_score": 0,
        "avg_score": 0,
        "badges": [],
        "is_blocked": False,
        "streak_days": 0,
        "last_active": datetime.now(timezone.utc)
    }
    db.collection("users").document(str(telegram_id)).set(user_data)
    return user_data

def get_user(telegram_id: int):
    db = get_db()
    doc = db.collection("users").document(str(telegram_id)).get()
    return doc.to_dict() if doc.exists else None

def update_user(telegram_id: int, data: dict):
    db = get_db()
    data["last_active"] = datetime.now(timezone.utc)
    db.collection("users").document(str(telegram_id)).update(data)

def get_all_users():
    """Admin panel uchun barcha foydalanuvchilarni olish"""
    db = get_db()
    users = db.collection("users").stream()
    return [u.to_dict() for u in users]

def block_user(telegram_id: int, status: bool = True):
    """Admin orqali foydalanuvchini bloklash yoki ochish"""
    db = get_db()
    db.collection("users").document(str(telegram_id)).update({
        "is_blocked": status,
        "updated_at": datetime.now(timezone.utc)
    })


# ==========================================================
# 2. TESTLAR (TESTS) OPERATSIYALARI
# ==========================================================

def get_test(test_id: str):
    db = get_db()
    doc = db.collection("tests").document(test_id).get()
    return doc.to_dict() if doc.exists else None

def get_all_tests():
    """Admin panel uchun barcha testlarni olish"""
    db = get_db()
    tests = db.collection("tests").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    return [t.to_dict() for t in tests]

def delete_test(test_id: str):
    """Admin yoki Yaratuvchi orqali testni butunlay o'chirish"""
    db = get_db()
    db.collection("tests").document(test_id).delete()


# ==========================================================
# 3. NATIJALAR (RESULTS) OPERATSIYALARI
# ==========================================================

def save_result(user_id: int, test_id: str, result_data: dict) -> str:
    """Test yakunlanganda natijani saqlash va barcha statistikalarni yangilash"""
    db = get_db()
    result_id = str(uuid.uuid4())
    
    # O'tish foizidan o'tganligini tekshirish
    passed = result_data.get("percentage", 0) >= result_data.get("passing_score", 60)
    
    final_result = {
        "result_id": result_id,
        "user_id": user_id,
        "test_id": test_id,
        "score": result_data.get("score", 0),
        "percentage": result_data.get("percentage", 0),
        "correct_count": result_data.get("correct_count", 0),
        "wrong_count": result_data.get("wrong_count", 0),
        "skipped_count": result_data.get("skipped_count", 0),
        "time_spent": result_data.get("time_spent", 0),
        "passed": passed,
        "completed_at": datetime.now(timezone.utc)
    }
    
    # 1. Natijani Firebase'ga yozish
    db.collection("results").document(result_id).set(final_result)
    
    # 2. Testning ishlanganlik sonini (solve_count) +1 ga oshirish
    test_ref = db.collection("tests").document(test_id)
    if test_ref.get().exists:
        test_ref.update({"solve_count": firestore.Increment(1)})
        
    # 3. Foydalanuvchining shaxsiy statistikasini yangilash
    user_ref = db.collection("users").document(str(user_id))
    user_doc = user_ref.get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        total_tests = user_data.get("total_tests", 0) + 1
        old_avg = user_data.get("avg_score", 0)
        new_pct = final_result["percentage"]
        
        # Yangi o'rtacha foizni hisoblash: ((Eski * (Soni-1)) + Yangi) / Soni
        new_avg = ((old_avg * (total_tests - 1)) + new_pct) / total_tests
        
        user_ref.update({
            "total_tests": total_tests,
            "avg_score": new_avg,
            "last_active": datetime.now(timezone.utc)
        })
        
        # 4. Leaderboard'ni avtomatik yangilash
        _update_leaderboard(
            user_id=user_id, 
            user_name=user_data.get("name", "Noma'lum"), 
            test_id=test_id, 
            percentage=final_result["percentage"], 
            score=final_result["score"]
        )
        
    return result_id

def get_user_results(user_id: int, limit: int = 50):
    """Foydalanuvchining oxirgi yechgan testlarini olish (Profil uchun)"""
    db = get_db()
    results = db.collection("results").where("user_id", "==", user_id).stream()
    
    # Python yordamida sanasiga ko'ra teskari (eng yangilari birinchi) tartiblash
    res_list = [r.to_dict() for r in results]
    res_list.sort(key=lambda x: x.get("completed_at", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    
    return res_list[:limit]


# ==========================================================
# 4. LEADERBOARD (REYTING) OPERATSIYALARI
# ==========================================================

def _update_leaderboard(user_id: int, user_name: str, test_id: str, percentage: float, score: float):
    """Yashirin funksiya: Har safar test ishlanganida eng yuqori natijani reytingga yozadi"""
    db = get_db()
    lb_id = f"{user_id}_{test_id}"
    lb_ref = db.collection("leaderboard").document(lb_id)
    lb_doc = lb_ref.get()
    
    if lb_doc.exists:
        # Faqat o'zining avvalgi rekordini yangilasa yozamiz
        if percentage > lb_doc.to_dict().get("best_percentage", 0):
            lb_ref.update({
                "best_percentage": percentage,
                "best_score": score,
                "updated_at": datetime.now(timezone.utc)
            })
    else:
        lb_ref.set({
            "user_id": user_id,
            "user_name": user_name,
            "test_id": test_id,
            "best_percentage": percentage,
            "best_score": score,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

def get_leaderboard_by_test(test_id: str, limit: int = 10):
    """Bitta aniq test bo'yicha kuchlilar o'nligini olish"""
    db = get_db()
    results = db.collection("leaderboard").where("test_id", "==", test_id).stream()
    
    res_list = [r.to_dict() for r in results]
    res_list.sort(key=lambda x: x.get("best_percentage", 0), reverse=True)
    return res_list[:limit]

def get_global_leaderboard(limit: int = 20):
    """Global umumiy reytingni olish (O'rtacha foizi eng balandlar)"""
    db = get_db()
    users = db.collection("users").stream()
    
    # Faqat kamida bitta test ishlagan foydalanuvchilarni ajratib olamiz
    user_list = [u.to_dict() for u in users if u.to_dict().get("total_tests", 0) > 0]
    
    # O'rtacha foiz bo'yicha kamayish tartibida saralaymiz
    user_list.sort(key=lambda x: x.get("avg_score", 0), reverse=True)
    return user_list[:limit]

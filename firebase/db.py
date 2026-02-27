"""
🗄️ FIREBASE DATABASE OPERATSIYALARI (TO'LIQ VERSIYA)
Web sayt (TestPro 2.0) bilan 100% integratsiya qilingan.
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
        "createdAt": datetime.now(timezone.utc), # Veb-saytga moslik uchun
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
    data["updatedAt"] = datetime.now(timezone.utc) # Veb-saytga moslik uchun
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
# 2. TESTLAR (TESTS) OPERATSIYALARI (WEB BILAN INTEGRATSIYA)
# ==========================================================

def get_test(test_id_or_code: str):
    """
    Testni hujjat ID si yoki 6 xonali accessCode bo'yicha bazadan qidirib topadi
    va savollarini subcollectiondan (papkadan) yig'ib beradi.
    """
    db = get_db()
    test_data = None
    test_id = None
    
    # 1. ID ni turini aniqlaymiz (AccessCode doim 6 xonali bo'ladi)
    if len(test_id_or_code) == 6:
        # 6 harfli Kod bo'yicha qidirish (Sayt tizimi)
        docs = db.collection("tests").where("accessCode", "==", test_id_or_code.upper().strip()).limit(1).get()
        if docs:
            test_data = docs[0].to_dict()
            test_id = docs[0].id
    else:
        # Haqiqiy uzun ID bo'yicha qidirish
        doc = db.collection("tests").document(test_id_or_code).get()
        if doc.exists:
            test_data = doc.to_dict()
            test_id = doc.id
            
    if not test_data or not test_id:
        return None
        
    test_data["test_id"] = test_id # Bot ishlashi uchun ID ni saqlaymiz
    
    # 2. Savollarni (questions) subcollection'dan olish
    questions_ref = db.collection("tests").document(test_id).collection("questions").order_by("order").get()
    questions = []
    
    for q in questions_ref:
        q_dict = q.to_dict()
        q_dict["id"] = q.id
        questions.append(q_dict)
        
    # Agar botning eski formatidagi test bo'lsa (questions asosiy hujjatda ro'yxat bo'lsa), o'zgartirmaymiz
    if not questions and "questions" in test_data:
        pass
    else:
        # Veb sayt testlarini bot tiliga o'giramiz
        test_data["questions"] = questions 
        
    return test_data

def get_all_tests():
    """Admin panel va Katalog uchun barcha testlarni olish"""
    db = get_db()
    tests = db.collection("tests").stream()
    result = []
    
    for t in tests:
        data = t.to_dict()
        data["test_id"] = t.id
        
        # Botning admin paneli "len(questions)" qilib hisoblaydi.
        # Saytda esa savollar papkada, shuning uchun "questionCount" orqali soxta uzunlik beramiz
        q_count = data.get("questionCount", 0)
        if "questions" not in data and q_count > 0:
            data["questions"] = [None] * q_count 
            
        result.append(data)
        
    # Yaratilgan sana bo'yicha yangilari birinchi turadigan qilib saralash
    result.sort(key=lambda x: x.get("createdAt") or x.get("created_at", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    return result

def delete_test(test_id: str):
    """Admin orqali testni va uning ichidagi papkasidagi (subcollection) savollarni o'chirish"""
    db = get_db()
    
    # Avval subcollection'dagi barcha savollarni o'chiramiz
    qs = db.collection("tests").document(test_id).collection("questions").stream()
    batch = db.batch()
    count = 0
    for q in qs:
        batch.delete(q.reference)
        count += 1
        
    if count > 0:
        batch.commit()
    
    # Keyin asosiy testni o'chiramiz
    db.collection("tests").document(test_id).delete()

def get_user_tests(user_id: int):
    """Profil uchun foydalanuvchi yaratgan testlarni olish"""
    db = get_db()
    tests = db.collection("tests").where("creator_id", "==", user_id).stream()
    res_list = []
    for t in tests:
        data = t.to_dict()
        data["test_id"] = t.id
        res_list.append(data)
    res_list.sort(key=lambda x: x.get("createdAt") or x.get("created_at", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    return res_list


# ==========================================================
# 3. NATIJALAR (RESULTS) OPERATSIYALARI (WEB BILAN INTEGRATSIYA)
# ==========================================================

def save_result(user_id: int, test_id: str, result_data: dict) -> str:
    """Test yakunlanganda natijani saqlash va statistikalarni (attempts, averageScore) yangilash"""
    db = get_db()
    result_id = str(uuid.uuid4())
    
    # 1. Natijani Firebase'ga yozish (Veb-saytga 100% moslab)
    final_result = {
        "result_id": result_id,
        "user_id": user_id,
        "userId": str(user_id), # Veb-sayt uchun
        "test_id": test_id,
        "testId": test_id,      # Veb-sayt uchun
        "score": result_data.get("score", 0),
        "percentage": result_data.get("score", 0), # Bot score ni foizda beradi
        "correct_count": result_data.get("correct_count", 0),
        "total_questions": result_data.get("total_questions", 0),
        "time_spent": result_data.get("time_spent", 0),
        "passed": result_data.get("passed", False),
        "detailed_results": result_data.get("detailed_results", []),
        "completed_at": datetime.now(timezone.utc),
        "completedAt": datetime.now(timezone.utc) # Veb-sayt uchun
    }
    
    db.collection("results").document(result_id).set(final_result)
    
    # 2. Testning statistikasini yangilash (attempts, averageScore va solve_count)
    test_ref = db.collection("tests").document(test_id)
    doc = test_ref.get()
    
    if doc.exists:
        prev = doc.to_dict()
        attempts = prev.get("attempts", 0) + 1
        avg_score = prev.get("averageScore", 0)
        current_score = result_data.get("score", 0)
        
        # O'rtacha natijani hisoblash formula (saytdagi kabi)
        new_avg = round(((avg_score * (attempts - 1)) + current_score) / attempts)
        
        test_ref.update({
            "attempts": attempts,
            "averageScore": new_avg,
            "solve_count": firestore.Increment(1) # Bot uchun
        })
        
    return result_id

def get_user_results(user_id: int, limit: int = 10):
    """Profil uchun foydalanuvchining oxirgi ishlagan testlari natijalarini olish"""
    db = get_db()
    results = db.collection("results").where("user_id", "==", user_id).stream()
    
    res_list = []
    for r in results:
        data = r.to_dict()
        res_list.append(data)
        
    res_list.sort(key=lambda x: x.get("completed_at") or x.get("completedAt", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    return res_list[:limit]


# ==========================================================
# 4. REYTING (LEADERBOARD) OPERATSIYALARI
# ==========================================================

def update_leaderboard(user_id: int, user_name: str, test_id: str, score: float, percentage: float):
    db = get_db()
    lb_ref = db.collection("leaderboard").document(f"{user_id}_{test_id}")
    lb_doc = lb_ref.get()
    
    if lb_doc.exists:
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
    db = get_db()
    results = db.collection("leaderboard").where("test_id", "==", test_id).stream()
    
    res_list = [r.to_dict() for r in results]
    res_list.sort(key=lambda x: x.get("best_percentage", 0), reverse=True)
    return res_list[:limit]

def get_global_leaderboard(limit: int = 20):
    db = get_db()
    users = db.collection("users").stream()
    
    res_list = []
    for u in users:
        d = u.to_dict()
        if d.get("total_tests", 0) > 0:
            res_list.append(d)
            
    res_list.sort(key=lambda x: x.get("avg_score", 0), reverse=True)
    return res_list[:limit]
    

/**
 * 🔥 FIREBASE JS CONFIG — HTML sahifalar uchun
 * Bu faylni o'zingizning Firebase loyiha ma'lumotlari bilan to'ldiring.
 * Firebase Console → Project Settings → Your apps → Web app → Config
 * 
 * Qo'llanilishi: test.html, history.html, review.html sahifalarida
 * <script src="firebase-config.js"></script> orqali ulanadi
 */

// ═══════════════════════════════════════════════════════════
// 1. SHU QATORLARNI O'ZGARTIRING
// ═══════════════════════════════════════════════════════════
const FIREBASE_CONFIG = {
  apiKey: "AIzaSyCPdGiX2gnPCvfP7KFSixP09PbVkVZ_eEo",
  authDomain: "testbot-7c514.firebaseapp.com",
  projectId: "testbot-7c514",
  storageBucket: "testbot-7c514.appspot.com",
  messagingSenderId: "223522501634",
  appId: "1:223522501634:web:ca9865cc95e0bc5db9a31b"
};

// ═══════════════════════════════════════════════════════════
// 2. FIREBASE ISHGA TUSHIRISH
// ═══════════════════════════════════════════════════════════
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getFirestore, doc, getDoc, collection, query, where, getDocs, orderBy, limit }
  from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

const app = initializeApp(FIREBASE_CONFIG);
const db = getFirestore(app);


// ═══════════════════════════════════════════════════════════
// 3. TESTNI ID BO'YICHA OLISH
// ═══════════════════════════════════════════════════════════
/**
 * Testni Firestore dan yuklab olish.
 * @param {string} testId — test_id (masalan: "ABC12345")
 * @returns {Promise<Object|null>}
 */
async function getTestById(testId) {
  try {
    const docRef = doc(db, "tests", testId);
    const docSnap = await getDoc(docRef);
    if (docSnap.exists()) {
      const data = docSnap.data();
      if (data.is_active === false) return null;
      return data;
    }
    return null;
  } catch (e) {
    console.error("getTestById xatosi:", e);
    return null;
  }
}


// ═══════════════════════════════════════════════════════════
// 4. FOYDALANUVCHI NATIJALARINI OLISH
// ═══════════════════════════════════════════════════════════
/**
 * Foydalanuvchi natijalarini Firestore dan olish.
 * results_latest koleksiyasidan: doc ID = "uid_testid"
 * @param {number|string} userId — Telegram user_id
 * @param {number} limitCount — nechta natija (max)
 * @returns {Promise<Array>}
 */
async function getUserResults(userId, limitCount = 50) {
  try {
    const q = query(
      collection(db, "results_latest"),
      where("user_id", "==", Number(userId)),
      limit(limitCount)
    );
    const snap = await getDocs(q);
    const results = [];
    snap.forEach(d => results.push(d.data()));
    // Vaqt bo'yicha tartiblash (yangirogʻi birinchi)
    results.sort((a, b) => {
      const ta = a.completed_at || "";
      const tb = b.completed_at || "";
      return tb.localeCompare(ta);
    });
    return results;
  } catch (e) {
    console.error("getUserResults xatosi:", e);
    return [];
  }
}


// ═══════════════════════════════════════════════════════════
// 5. OMMAVIY TESTLARNI OLISH
// ═══════════════════════════════════════════════════════════
/**
 * Barcha ommaviy testlarni Firestore dan olish.
 * @returns {Promise<Array>}
 */
async function getPublicTests() {
  try {
    const q = query(
      collection(db, "tests"),
      where("visibility", "==", "public"),
      where("is_active", "==", true),
      limit(100)
    );
    const snap = await getDocs(q);
    const tests = [];
    snap.forEach(d => tests.push(d.data()));
    return tests;
  } catch (e) {
    console.error("getPublicTests xatosi:", e);
    return [];
  }
}


// Global eksport
window.FirebaseDB = {
  getTestById,
  getUserResults,
  getPublicTests,
};

console.log("✅ Firebase JS ulandi");

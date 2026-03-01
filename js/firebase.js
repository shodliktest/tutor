/**
 * firebase.js — GitHub Pages versiyasi
 * Firebase config va DB yordamchi funksiyalar
 * Auth: Telegram user_id (integer) asosida — Firebase Auth ISHLATILMAYDI
 *
 * ⚠️  SOZLASH: quyidagi firebaseConfig ni o'zingizniki bilan almashtiring.
 *     Bu ma'lumotlar Firebase Console → Project Settings → Your apps dan olinadi.
 */

const firebaseConfig = {
  apiKey:            "AIzaSyCPdGiX2gnPCvfP7KFSixP09PbVkVZ_eEo",
  authDomain:        "testbot-7c514.firebaseapp.com",
  projectId:         "testbot-7c514",
  storageBucket:     "testbot-7c514.appspot.com",
  messagingSenderId: "223522501634",
  appId:             "1:223522501634:web:ca9865cc95e0bc5db9a31b"
};

/* ── Firebase init ────────────────────────────────────────── */
if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();

/* ── URL parametr yordamchisi ─────────────────────────────── */
const UP = {
  get(key) { return new URLSearchParams(location.search).get(key); }
};

/**
 * getTelegramUserId()
 * Prioritet: 1) window.Telegram.WebApp.initDataUnsafe.user.id
 *            2) URL ?user_id= parametri
 *            3) null
 */
function getTelegramUserId() {
  try {
    const tg = window.Telegram?.WebApp;
    if (tg) {
      const uid = tg.initDataUnsafe?.user?.id;
      if (uid) return Number(uid);
    }
  } catch (_) {}
  const p = UP.get('user_id');
  return p ? Number(p) : null;
}

/* ── Subject ma'lumotnomasi ───────────────────────────────── */
const SUBJECTS = {
  english:  { label: 'Ingliz tili',   icon: '🇬🇧' },
  arabic:   { label: 'Arab tili',     icon: '🕌'  },
  russian:  { label: 'Rus tili',      icon: '🇷🇺' },
  turkish:  { label: 'Turk tili',     icon: '🇹🇷' },
  math:     { label: 'Matematika',    icon: '🧮'  },
  it:       { label: 'Informatika',   icon: '💻'  },
  science:  { label: 'Fan',           icon: '🔬'  },
  religion: { label: 'Din',           icon: '📖'  },
  other:    { label: 'Boshqa',        icon: '📚'  },
};

function getSubject(key) {
  return SUBJECTS[key] || SUBJECTS.other;
}

/* ── Yordamchi funksiyalar ────────────────────────────────── */
function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function goTo(page) {
  // uid ni barcha sahifalarga uzatib yuramiz
  const uid = getTelegramUserId();
  const sep = page.includes('?') ? '&' : '?';
  location.href = uid ? `${page}${sep}user_id=${uid}` : page;
}

/* ── DB ─────────────────────────────────────────────────────
 *  Firestore da ma'lumotlar tuzilmasi:
 *    tests/{testId}          — test meta-ma'lumotlari
 *    tests/{testId}/questions — savol kolleksiyasi
 *    results/{resultId}      — natijalar (bot tomonidan yoziladi, HTML o'qiydi)
 *
 *  ⚠️ Natija yozish (saveResult) — faqat HTML test.html dan chaqiriladi.
 *     Bot ham o'zining firebase/db.py orqali yozadi (inline/poll rejimlar uchun).
 */
const DB = {

  /* ── Test ma'lumotlari ── */
  async getTest(id) {
    const doc = await db.collection('tests').doc(id).get();
    if (!doc.exists) return null;
    return { id: doc.id, ...doc.data() };
  },

  async getTestByCode(code) {
    const snap = await db.collection('tests')
      .where('code', '==', code).limit(1).get();
    if (snap.empty) return null;
    const doc = snap.docs[0];
    return { id: doc.id, ...doc.data() };
  },

  async getQuestions(testId) {
    // Savollar tests/{id}/questions subcollection da saqlangan
    // Yoki tests/{id}.questions array bo'lishi mumkin
    try {
      const snap = await db.collection('tests').doc(testId)
        .collection('questions').orderBy('order').get();
      if (!snap.empty)
        return snap.docs.map(d => ({ id: d.id, ...d.data() }));
    } catch (_) {}
    // Fallback: array ichida
    const t = await this.getTest(testId);
    return t?.questions || [];
  },

  /* ── Natijalar ── */
  /**
   * saveResult — faqat Web (HTML) rejimi uchun.
   * Bot inline/poll natijalari firebase/db.py orqali saqlanadi.
   *
   * @param {object} data  { userId (Telegram int), testId, testTitle, subject,
   *                         score, correct, total, elapsed, userAnswers, passed }
   */
  async saveResult(data) {
    const rid = Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
    await db.collection('results').doc(rid).set({
      result_id:       rid,
      user_id:         Number(data.userId),
      test_id:         data.testId,
      test_title:      data.testTitle || '',
      subject:         data.subject   || 'other',
      score:           data.score     || 0,
      percentage:      data.score     || 0,
      correct_count:   data.correct   || 0,
      wrong_count:     (data.total || 0) - (data.correct || 0),
      total_questions: data.total     || 0,
      time_spent:      data.elapsed   || 0,
      passed:          !!data.passed,
      passing_score:   data.passScore || 60,
      user_answers:    data.userAnswers || [],
      mode:            'web',
      completed_at:    firebase.firestore.FieldValue.serverTimestamp(),
    });
    return rid;
  },

  /**
   * getResultById — review.html ishlatadi.
   * Firestore da natijalar result_id field va document ID ikkalasi bir xil.
   */
  async getResultById(rid) {
    const doc = await db.collection('results').doc(rid).get();
    if (!doc.exists) return null;
    return { id: doc.id, ...doc.data() };
  },

  /**
   * getMyResults — history.html ishlatadi.
   * Telegram user_id bo'yicha so'raydi.
   */
  async getMyResults(userId, _limit = 50) {
    const snap = await db.collection('results')
      .where('user_id', '==', Number(userId))
      .orderBy('completed_at', 'desc')
      .limit(100)
      .get();
    return snap.docs.map(d => ({ id: d.id, ...d.data() }));
  },

  /* ── Foydalanuvchi ── (ixtiyoriy) */
  async getUser(userId) {
    const doc = await db.collection('users').doc(String(userId)).get();
    return doc.exists ? { id: doc.id, ...doc.data() } : null;
  }
};

/* ── AuthHelpers shim ─────────────────────────────────────
 * Eski kod `AuthHelpers.getCurrentUser()` deb chaqiradi.
 * Biz uni Telegram user_id qaytaradigan stub bilan almashtiramiz.
 * uid = "tg_" + telegramId  shaklida qaytariladi (string).
 */
const AuthHelpers = {
  getCurrentUser() {
    const uid = getTelegramUserId();
    if (!uid) return Promise.resolve(null);
    return Promise.resolve({ uid: String(uid), telegramId: uid });
  },
  requireAuth(redirectPage) {
    const uid = getTelegramUserId();
    if (!uid) {
      // Telegram WebApp da login.html yo'q — xato ko'rsatamiz
      document.body.innerHTML =
        `<div style="padding:2rem;text-align:center;font-family:sans-serif">
          <h2>❌ Foydalanuvchi aniqlanmadi</h2>
          <p>Iltimos, botdan kirish havolasini bosing.</p>
        </div>`;
      return Promise.resolve(null);
    }
    return Promise.resolve({ uid: String(uid), telegramId: uid });
  }
};

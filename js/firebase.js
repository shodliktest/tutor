/* ================================================================
   firebase.js — Telegram Bot (testbot-7c514) bilan ishlash uchun
   Bot formatini HTML formatiga normalize qiladi
   ================================================================ */

const firebaseConfig = {
  apiKey:            "AIzaSyCPdGiX2gnPCvfP7KFSixP09PbVkVZ_eEo",
  authDomain:        "testbot-7c514.firebaseapp.com",
  projectId:         "testbot-7c514",
  storageBucket:     "testbot-7c514.appspot.com",
  messagingSenderId: "223522501634",
  appId:             "1:223522501634:web:ca9865cc95e0bc5db9a31b"
};

if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();

/* ── URL parametr ── */
const UP = { get(k) { return new URLSearchParams(location.search).get(k); } };

/* ── Telegram user_id olish ── */
function getTelegramUserId() {
  try {
    const uid = window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
    if (uid) return Number(uid);
  } catch(_) {}
  const p = UP.get('user_id');
  return p ? Number(p) : null;
}

/* ================================================================
   normalizeQuestion — Bot Python formati → HTML formati
   
   Bot saqlaydi:
     { question: "...", options: ["A) Ha", "B) Yo'q"], correct: "A) Ha",
       type: "multiple_choice" }
   
   HTML kutadi:
     { text: "...", options: ["Ha", "Yo'q"], correct: 0 (index),
       type: "multiple" }
   ================================================================ */
function normalizeQuestion(q) {
  const LETTERS = ['A','B','C','D','E','F','G','H','I','J'];

  // text field
  const text = q.question || q.text || '';

  // type normalize
  let type = (q.type || 'multiple').toLowerCase();
  if (type === 'multiple_choice') type = 'multiple';
  if (type === 'true_false')      type = 'truefalse';
  if (type === 'text_input' || type === 'fill_blank') type = 'text';

  // options — "A) Toshkent" → "Toshkent"
  const rawOpts = q.options || [];
  const options = rawOpts.map(o => {
    const s = String(o);
    return s.replace(/^[A-Za-z][\.\)]\s*/, '').trim();
  });

  // correct — string "A) ..." yoki "A" → index raqamiga
  let correct = q.correct;
  if (typeof correct === 'string') {
    const m = correct.trim().match(/^([A-Za-z])/);
    if (m) {
      correct = LETTERS.indexOf(m[1].toUpperCase());
      if (correct < 0) correct = 0;
    } else {
      // To'g'ridan-to'g'ri option matni bo'lsa
      const idx = options.findIndex(o =>
        o.toLowerCase() === correct.toLowerCase()
      );
      correct = idx >= 0 ? idx : 0;
    }
  }
  if (typeof correct !== 'number') correct = 0;

  // correctAnswer (text type uchun)
  const correctAnswer = q.correctAnswer || q.correct_answer ||
    (type === 'text' && typeof q.correct === 'string' ? q.correct : '');

  return {
    ...q,
    text,
    type,
    options,
    correct,
    correctAnswer,
    explanation: q.explanation || '',
    points: q.points || 1,
  };
}

/* ── Subject ── */
const SUBJECTS = {
  english:  { label: 'Ingliz tili', icon: '🇬🇧' },
  arabic:   { label: 'Arab tili',   icon: '🕌'  },
  russian:  { label: 'Rus tili',    icon: '🇷🇺' },
  turkish:  { label: 'Turk tili',   icon: '🇹🇷' },
  math:     { label: 'Matematika',  icon: '🧮'  },
  it:       { label: 'Informatika', icon: '💻'  },
  science:  { label: 'Fan',         icon: '🔬'  },
  religion: { label: 'Din',         icon: '📖'  },
  other:    { label: 'Boshqa',      icon: '📚'  },
};
function getSubject(k) { return SUBJECTS[k] || SUBJECTS.other; }

/* ── Helpers ── */
function esc(s) {
  return String(s ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function fmtTime(secs) {
  secs = secs || 0;
  return String(Math.floor(secs/60)).padStart(2,'0') + ':' +
         String(secs % 60).padStart(2,'0');
}
function goTo(page) {
  const uid = getTelegramUserId();
  const sep = page.includes('?') ? '&' : '?';
  location.href = uid ? `${page}${sep}user_id=${uid}` : page;
}

/* ── DB ── */
const DB = {

  async getTest(id) {
    const doc = await db.collection('tests').doc(id).get();
    if (!doc.exists) return null;
    const d = doc.data();
    // is_active = false bo'lsa ko'rsatmaymiz
    if (d.is_active === false) return null;
    return { id: doc.id, ...d };
  },

  async getTestByCode(code) {
    // Bot 'code' field ishlatmaydi — 'accessCode' ham yo'q
    // test_id = document ID, uni to'g'ridan-to'g'ri olish kerak
    const upper = code.toUpperCase().trim();
    // Avval document ID sifatida sinab ko'ramiz
    try {
      const doc = await db.collection('tests').doc(upper).get();
      if (doc.exists) return { id: doc.id, ...doc.data() };
    } catch(_) {}
    // Keyin code field bo'yicha qidiramiz
    try {
      const snap = await db.collection('tests')
        .where('code', '==', upper).limit(1).get();
      if (!snap.empty) return { id: snap.docs[0].id, ...snap.docs[0].data() };
    } catch(_) {}
    return null;
  },

  async getQuestions(testId) {
    let qs = [];
    // 1) subcollection
    try {
      const snap = await db.collection('tests').doc(testId)
        .collection('questions').orderBy('order').get();
      if (!snap.empty)
        qs = snap.docs.map(d => ({ id: d.id, ...d.data() }));
    } catch(_) {}
    // 2) questions array ichida (bot bu usulni ishlatadi)
    if (!qs.length) {
      const t = await this.getTest(testId);
      qs = t?.questions || [];
    }
    // 3) Bot formatini HTML formatiga o'giramiz
    return qs.map(q => normalizeQuestion(q));
  },

  async saveResult(data) {
    const rid = Date.now().toString(36) + Math.random().toString(36).slice(2,7);
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

  async getResultById(rid) {
    const doc = await db.collection('results').doc(rid).get();
    if (!doc.exists) return null;
    return { id: doc.id, ...doc.data() };
  },

  async getMyResults(userId) {
    try {
      const snap = await db.collection('results')
        .where('user_id', '==', Number(userId))
        .orderBy('completed_at', 'desc')
        .limit(100).get();
      return snap.docs.map(d => ({ id: d.id, ...d.data() }));
    } catch(_) {
      // Index yo'q bo'lsa orderBy olmagan holda olamiz
      const snap = await db.collection('results')
        .where('user_id', '==', Number(userId))
        .limit(100).get();
      const list = snap.docs.map(d => ({ id: d.id, ...d.data() }));
      return list.sort((a,b) =>
        (b.completed_at?.seconds||0) - (a.completed_at?.seconds||0));
    }
  },

  async getUser(userId) {
    const doc = await db.collection('users').doc(String(userId)).get();
    return doc.exists ? { id: doc.id, ...doc.data() } : null;
  }
};

/* ── AuthHelpers shim ── */
const AuthHelpers = {
  getCurrentUser() {
    const uid = getTelegramUserId();
    if (!uid) return Promise.resolve(null);
    return Promise.resolve({ uid: String(uid), telegramId: uid });
  },
  requireAuth() {
    const uid = getTelegramUserId();
    if (!uid) {
      document.body.innerHTML =
        `<div style="padding:2rem;text-align:center;font-family:sans-serif;color:#1a1a2e">
          <div style="font-size:3rem">❌</div>
          <h2>Foydalanuvchi aniqlanmadi</h2>
          <p>Iltimos, bot havolasidan kiring.</p>
        </div>`;
      return Promise.resolve(null);
    }
    return Promise.resolve({ uid: String(uid), telegramId: uid });
  }
};

/* ── Global eksport ── */
window.DB          = DB;
window.AuthHelpers = AuthHelpers;
window.getSubject  = getSubject;
window.getTelegramUserId = getTelegramUserId;
window.normalizeQuestion = normalizeQuestion;
window.esc         = esc;
window.fmtTime     = fmtTime;
window.goTo        = goTo;

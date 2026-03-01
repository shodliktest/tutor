/* ================================================================
   firebase.js — Universal format
   Bot (Python) va HTML bir xil formatda o'qiydi/yozadi:
     options       : ["Toshkent", "Moskva"]   — toza, harfsiz
     correct       : 0  (index)
     correct_letter: "A"
     text/question : savol matni (ikkalasi bir xil)
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

/* ── Telegram user_id ── */
function getTelegramUserId() {
  try {
    const uid = window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
    if (uid) return Number(uid);
  } catch(_) {}
  const p = UP.get('user_id');
  return p ? Number(p) : null;
}

/* ================================================================
   normalizeQuestion — eski formatda saqlangan testlar uchun fallback
   Yangi testlar allaqachon to'g'ri formatda keladi.
   ================================================================ */
function normalizeQuestion(q) {
  const LETTERS = ['A','B','C','D','E','F','G','H','I','J'];

  // text = question yoki text
  const text = (q.text || q.question || '').replace(/^\d+[\.\)]\s*/, '').trim();

  // type normalize
  let type = (q.type || 'multiple_choice').toLowerCase();
  if (type === 'multiple_choice') type = 'multiple';
  if (type === 'true_false')      type = 'truefalse';
  if (type === 'text_input' || type === 'fill_blank') type = 'text';

  // options — agar "A) Matn" formatda bo'lsa tozalaymiz
  const rawOpts = q.options || [];
  const options = rawOpts.map(o =>
    String(o).replace(/^[A-Za-z][\.\)]\s*/, '').replace(/\[TO'G'RI\]/gi,'')
             .replace(/\*/g,'').replace(/={3}/g,'').trim()
  );

  // correct — index bo'lmasa o'giramiz
  let correct = q.correct;
  if (typeof correct === 'string' && correct.trim() !== '') {
    // "A" yoki "A) Matn" → index
    const m = correct.trim().match(/^([A-Za-z])/);
    if (m) {
      const idx = LETTERS.indexOf(m[1].toUpperCase());
      correct = idx >= 0 ? idx : 0;
    } else {
      // Option matniga mos indeksini topamiz
      const cleaned = correct.replace(/^[A-Za-z][\.\)]\s*/,'').trim().toLowerCase();
      const idx = options.findIndex(o => o.toLowerCase() === cleaned);
      correct = idx >= 0 ? idx : 0;
    }
  }
  if (typeof correct !== 'number') correct = 0;

  const correctAnswer = q.correctAnswer || q.correct_answer ||
    (type === 'text' && typeof q.correct === 'string' ? q.correct : '');

  return { ...q, text, type, options, correct, correctAnswer,
           explanation: q.explanation || '', points: q.points || 1 };
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
    if (d.is_active === false) return null;
    return { id: doc.id, ...d };
  },

  async getTestByCode(code) {
    const upper = code.toUpperCase().trim();
    // 1) Document ID sifatida
    try {
      const doc = await db.collection('tests').doc(upper).get();
      if (doc.exists && doc.data().is_active !== false)
        return { id: doc.id, ...doc.data() };
    } catch(_) {}
    // 2) code field
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
    // 2) questions array (bot bu usulni ishlatadi)
    if (!qs.length) {
      const t = await this.getTest(testId);
      qs = t?.questions || [];
    }
    // 3) Normalize (yangi formatda bo'lsa ham xavfsiz)
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
      wrong_count:     (data.total||0) - (data.correct||0),
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
      // Composite index yo'q bo'lsa
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
        `<div style="padding:2rem;text-align:center;font-family:'Plus Jakarta Sans',sans-serif">
          <div style="font-size:3rem;margin-bottom:1rem">❌</div>
          <h2 style="color:#1a1a2e">Foydalanuvchi aniqlanmadi</h2>
          <p style="color:#6b7280">Bot havolasidan kiring.</p>
        </div>`;
      return Promise.resolve(null);
    }
    return Promise.resolve({ uid: String(uid), telegramId: uid });
  }
};

/* ── Global ── */
window.DB = DB;
window.AuthHelpers = AuthHelpers;
window.getSubject = getSubject;
window.getTelegramUserId = getTelegramUserId;
window.normalizeQuestion = normalizeQuestion;
window.esc = esc;
window.fmtTime = fmtTime;
window.goTo = goTo;

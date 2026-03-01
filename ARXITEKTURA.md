# 🎓 QUIZ BOT PRO — To'liq arxitektura

## 📁 Loyiha tuzilmasi

```
tutor_pro/
├── bot.py                    ← Aiogram 3 bot, Singleton threading
├── config.py                 ← Barcha sozlamalar (secrets.toml dan)
├── streamlit_app.py          ← Admin panel + WebApp routing
├── requirements.txt
│
├── firebase/
│   ├── config.py             ← Firebase init (Singleton)
│   ├── db.py                 ← Barcha Firestore CRUD
│   └── storage.py            ← Firebase Storage TXT arxiv (YANGI)
│
├── utils/
│   ├── parser.py             ← TXT/PDF/DOCX parser
│   ├── scoring.py            ← Ball hisoblash, 7 test turi
│   ├── states.py             ← FSM States
│   └── cache.py              ← Streamlit session_state cache (YANGI)
│
├── handlers/
│   ├── start.py              ← /start, Adminga murojaat
│   ├── tests.py              ← Inline test + Web yo'naltiruvchi
│   ├── poll_test.py          ← Native Telegram Quiz Poll
│   ├── create_test.py        ← Test yaratish (fayl/QuizBot)
│   ├── profile.py            ← Profil, natijalar, mening testlarim
│   ├── leaderboard.py        ← Reyting
│   └── admin.py              ← Admin panel (bot ichida)
│
├── keyboards/
│   └── keyboards.py          ← Barcha klaviaturalar + WebApp tugmalari
│
├── pages/
│   └── web_app.py            ← Telegram WebApp sahifasi (YANGI)
│
├── samples/                  ← Test namunalari (TXT)
│   ├── multiple_choice_namuna.txt
│   ├── multi_select_namuna.txt
│   ├── true_false_namuna.txt
│   ├── fill_blank_namuna.txt
│   ├── matching_namuna.txt
│   ├── ordering_namuna.txt
│   └── barcha_turlar_namuna.txt
│
└── .streamlit/
    └── secrets.toml          ← MAXFIY — GitHub ga yuklamang!
```

---

## 🚀 Muhim yangiliklar

### 1. Telegram WebApp (pages/web_app.py)
Bot tugmalaridan Streamlit oynasiga o'tish:

| Tugma | Mode | Ma'lumot |
|-------|------|----------|
| 🌐 Web test | `?mode=test&test_id=X&user_id=Y` | Test yechish |
| 🔍 Batafsil tahlil | `?mode=review&result_id=X&user_id=Y` | Tahlil |
| 📜 Natijalarim | `?mode=history&user_id=Y` | Tarix |

### 2. Firebase limit tejash (utils/cache.py + firebase/storage.py)
- Testlar: kuniga 1 marta Storage dan yuklanadi
- Natijalar: session_state da to'planadi, 23:55 da sync
- 1 test = 1 natija (oxirgisi saqlanadi)

**Taxminiy tejash: 70-90% kam read/write**

### 3. Scheduler (streamlit_app.py)
```python
schedule.every().day.at("23:55").do(_daily_job)
```

---

## ⚙️ O'rnatish

### 1. Secrets konfiguratsiya
`.streamlit/secrets.toml` faylini to'ldiring:

```toml
BOT_TOKEN = "7123456789:AAH..."
ADMIN_IDS = "123456789"
ADMIN_PASSWORD = "siz_xohlagan_parol"
STREAMLIT_URL = "https://your-app.streamlit.app"

[firebase_sa]
type = "service_account"
project_id = "sizning-project-id"
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n"
client_email = "firebase-adminsdk-xxx@..."

[firebase]
storage_bucket = "sizning-project-id.appspot.com"
```

### 2. Requirements o'rnatish
```bash
pip install -r requirements.txt
```

### 3. Lokal ishga tushirish
```bash
# Bot alohida:
python bot.py

# Streamlit alohida (bot + admin panel):
streamlit run streamlit_app.py
```

### 4. Streamlit Cloud deploy
1. GitHub ga yuklang (secrets.toml SIZ)
2. [share.streamlit.io](https://share.streamlit.io) ga o'ting
3. Repository ni ulang
4. Main file: `streamlit_app.py`
5. Secrets ni kiriting

---

## 🔧 Firebase Storage Rules
```
service firebase.storage {
  match /b/{bucket}/o {
    match /db/{allPaths=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```
**Eslatma**: Admin SDK autentifikatsiya talab qilmaydi — bu qoidalar faqat client uchun.

---

## 📋 Test turlari (7 ta)

| Tur | Misol format |
|-----|--------------|
| multiple_choice | `===A) Toshkent` |
| multi_select | `TYPE: multi_select` + `===A)...` |
| true_false | `TYPE: true_false` + `Javob: Ha` |
| fill_blank | `TYPE: fill_blank` + `Javob: ...` |
| text_input | `TYPE: text_input` + `Javob: ...` |
| matching | `TYPE: matching` + `Chap: X \| Y` |
| ordering | `TYPE: ordering` + `1. ...` |

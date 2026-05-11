# 🎓 Quiz Bot Pro — Aiogram 3 + Firebase + Streamlit

Telegram quiz bot — 2 rejimda test yechish, Firebase baza, Streamlit admin panel.

## ✨ Asosiy imkoniyatlar
f
| Imkoniyat | Tavsif |
|-----------|--------|
| ▶️ **Inline test** | Har savoldan keyin 5 soniya to'g'ri/noto'g'ri ko'rsatadi |
| 📊 **Poll test** | Telegram native quiz poll — @QuizBot uslubida |
| 📁 **Fayl yuklash** | TXT / PDF / DOCX fayldan savollar import |
| 📊 **QuizBot forward** | @QuizBot viktorinalarini forward qilish |
| 🏆 **Reyting** | Global va test bo'yicha alohida reyting |
| 👑 **Admin panel** | Broadcast, bloklash, statistika (Streamlit web) |

## 🚀 Ishga tushirish

### 1. Talablar
```
pip install -r requirements.txt
```

### 2. Konfiguratsiya
`.streamlit/secrets.toml` faylini to'ldiring:
```toml
BOT_TOKEN = "TOKEN"
ADMIN_IDS = "123456789"
ADMIN_PASSWORD = "parol"

[firebase_sa]
type = "service_account"
project_id = "loyiha-id"
# ... qolgan Firebase kalitlari
```

### 3. Lokal ishga tushirish
```bash
# Faqat bot
python bot.py

# Bot + Admin panel birga
streamlit run streamlit_app.py
```

### 4. Streamlit Cloud deploy
1. GitHub ga push qiling
2. share.streamlit.io da yangi app yarating
3. Secrets bo'limiga `secrets.toml` mazmunini kiriting

## 📄 Fayl formati

### Bir javobli test (TXT):
```
1. O'zbekiston poytaxti qayer?
===A) Toshkent
B) Samarqand
C) Buxoro
D) Xiva
Izoh: Toshkent 1930-yildan poytaxt.
```

### Ko'p javobli test:
```
TYPE: multi_select
1. Qaysilar O'zbekistonda joylashgan?
===A) Toshkent
===B) Samarqand
C) Ostona
===D) Buxoro
```

### Bo'sh joy to'ldirish:
```
TYPE: fill_blank
1. Alisher Navoiy ___ yilda tug'ilgan.
Javob: 1441
Qabul_qilinadigan: 1441-yil, 1441 yil
```

**To'g'ri javob belgilash:** `===`, `*` yoki `[TO'G'RI]`

## 📊 Poll test nima?

Poll test Telegram native quiz poll ishlatadi:
- Telegram o'zi to'g'ri/noto'g'riligini ko'rsatadi
- Izoh va to'g'ri javob avtomatik chiqadi
- Natijalar bazaga saqlanadi

**Faqat MCQ va Ha/Yo'q** savollar poll rejimida ishlaydi.

## 🗂 Fayl tuzilishi

```
tutor-pro/
├── bot.py                # Asosiy bot (singleton threading)
├── config.py             # Konfiguratsiya
├── streamlit_app.py      # Admin web panel
├── requirements.txt
├── firebase/
│   ├── config.py         # Firebase ulanish
│   └── db.py             # CRUD operatsiyalar
├── handlers/
│   ├── start.py          # /start, deep-link, yordam
│   ├── tests.py          # Inline test rejimi
│   ├── poll_test.py      # Poll test rejimi (YANGI!)
│   ├── create_test.py    # Test yaratish
│   ├── profile.py        # Profil, natijalar
│   ├── leaderboard.py    # Reyting
│   └── admin.py          # Admin panel
├── utils/
│   ├── states.py         # FSM holatlari
│   ├── parser.py         # TXT/PDF/DOCX parser
│   └── scoring.py        # Ball hisoblash
├── keyboards/
│   └── keyboards.py      # Barcha klaviaturalar
└── samples/              # Namuna fayllar
```

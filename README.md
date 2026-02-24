# 🎓 QUIZ BOT — Professional Test Platformasi

> Telegram orqali ishlatiladigan to'liq funksional quiz/test platformasi
> Python-Telegram-Bot + Firebase + GitHub

---

## 🚀 Xususiyatlar

### 📝 Test Turlari
| Tur | Tavsif |
|-----|--------|
| 🔘 Multiple Choice | Bir to'g'ri javobli test |
| ☑️ Multi-Select | Ko'p to'g'ri javobli test |
| ✅ True/False | Ha yoki Yo'q |
| ✍️ Text Input | Yozma javob |
| 🔗 Matching | Moslashtirish |
| 🔢 Ordering | Tartiblash |
| 📝 Fill in Blank | Bo'sh joyni to'ldirish |

### ⚡ Asosiy Funksiyalar
- 📁 TXT, PDF, DOCX fayllardan test yuklash
- 📋 Har bir tur uchun namuna fayllar
- 🏆 Leaderboard (Umumiy / Fan / Oylik / Test bo'yicha)
- 📊 Batafsil natija tahlili
- 👨‍💼 Admin panel (statistika, bloklash, o'chirish)
- 👤 Foydalanuvchi profili
- 🔗 Link orqali test ulashish
- 🎯 O'tish foizi va urinish cheklovi

---

## 📦 O'rnatish

### 1. Loyihani klonlash
```bash
git clone https://github.com/username/quiz-bot.git
cd quiz-bot
```

### 2. Virtual muhit yaratish
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. .env faylni sozlash
```bash
cp .env.example .env
# .env faylini tahrirlang va ma'lumotlarni kiriting
```

### 5. Firebase sozlash
1. https://console.firebase.google.com/ ga kiring
2. Yangi loyiha yarating
3. Firestore Database yarating
4. `serviceAccountKey.json` ni yuklab oling
5. Fayli loyiha papkasiga qo'ying

### 6. Botni ishga tushirish
```bash
python bot.py
```

---

## 📁 Loyiha Strukturasi

```
quiz_bot/
├── bot.py              # Asosiy fayl
├── config.py           # Konfiguratsiya
├── requirements.txt    # Kutubxonalar
├── .env.example        # .env namunasi
├── .gitignore
│
├── handlers/           # Telegram handlerlar
│   ├── start.py        # /start va /help
│   ├── tests.py        # Test ishlash
│   ├── create_test.py  # Test yaratish
│   ├── admin.py        # Admin panel
│   ├── leaderboard.py  # Reyting
│   └── results.py      # Natijalar va profil
│
├── firebase/           # Firebase bilan ishlash
│   ├── config.py       # Ulanish
│   └── db.py           # CRUD operatsiyalar
│
├── utils/              # Yordamchi funksiyalar
│   ├── parser.py       # Fayl parser
│   ├── scoring.py      # Natija hisoblash
│   └── states.py       # Conversation states
│
├── keyboards/          # Inline klaviaturalar
│   └── keyboards.py
│
└── samples/            # Namuna fayllar
    ├── multiple_choice_namuna.txt
    ├── multi_select_namuna.txt
    ├── true_false_namuna.txt
    ├── text_input_namuna.txt
    ├── matching_namuna.txt
    ├── ordering_namuna.txt
    ├── fill_blank_namuna.txt
    └── barcha_turlar_namuna.txt
```

---

## 📋 Test Fayl Formati

### 1. Bir javobli test
```
1. Savol matni?
A) Variant 1
B) Variant 2 [TO'G'RI]
C) Variant 3
D) Variant 4
Izoh: Tushuntirish (ixtiyoriy)
```

### 2. Ko'p javobli
```
2. Savollar?
TYPE: MULTI_SELECT
A) Variant [TO'G'RI]
B) Variant
C) Variant [TO'G'RI]
```

### 3. Ha/Yo'q
```
3. Savol matni.
TYPE: TRUE_FALSE
Javob: Ha
```

### 4. Yozma javob
```
4. Savol matni?
TYPE: TEXT_INPUT
Javob: To'g'ri javob
Qabul_qilinadigan: variant1, variant2
```

### 5. Moslashtirish
```
5. Savollar va javoblarni moslang:
TYPE: MATCHING
CHAP: Element 1 | Javob 1
CHAP: Element 2 | Javob 2
```

### 6. Tartiblash
```
6. To'g'ri tartibda joylashtiring:
TYPE: ORDERING
1. Birinchi
2. Ikkinchi
3. Uchinchi
```

### 7. Bo'sh joy
```
7. ___ O'zbekistonning poytaxti.
TYPE: FILL_BLANK
Javob: Toshkent
```

---

## 🔐 Xavfsizlik
- `.env` va `serviceAccountKey.json` ni **hech qachon** GitHub ga yuklamang
- `.gitignore` faylida ular allaqachon ko'rsatilgan

---

## 🛠 Texnologiyalar
- **Python 3.10+**
- **python-telegram-bot 20.x**
- **Firebase Admin SDK**
- **pdfplumber** (PDF o'qish)
- **python-docx** (DOCX o'qish)

---

## 👤 Muallif
**Otavaliyev.M (SHodlik)**

---

*Quiz Bot — O'qituvchilar va o'quvchilar uchun professional test platformasi* 🎓

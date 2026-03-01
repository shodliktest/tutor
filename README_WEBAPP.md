# 🎓 TestPro Bot — Telegram Web App Integratsiyasi

## 🌟 Qanday ishlaydi?

```
Foydalanuvchi botda tugma bosadi
        ↓
Telegram ichida POPUP oyna ochiladi (alohida browser emas!)
        ↓
Foydalanuvchi test yechadi yoki test yaratadi
        ↓
HTML fayl sendData() orqali botga natija yuboradi
        ↓
Bot natijani qabul qilib, xush ko'rinishli xabar yuboradi
```

## 📁 Loyiha strukturasi

```
tutor_pro/
├── bot.py                     # Asosiy bot (webapp_router qo'shildi)
├── config.py                  # WEBAPP_BASE_URL qo'shildi
├── handlers/
│   ├── webapp.py              # 🆕 Web App natijalarini qabul qilish
│   ├── create_test.py         # ✏️ Web App yaratish tugmasi qo'shildi
│   ├── profile.py             # 📊 Web App history tugmasi qo'shildi
│   └── ...
├── keyboards/
│   └── keyboards.py           # 🆕 WebAppInfo tugmalari qo'shildi
├── webapp_pages/              # 🆕 GitHub Pages da host qilinadigan fayllar
│   ├── index.html             # Asosiy sahifa
│   ├── test.html              # Test yechish (sendData qo'shildi)
│   ├── history.html           # Natijalar tarixi (Telegram SDK qo'shildi)
│   ├── create.html            # Test yaratish (sendData qo'shildi)
│   └── review.html            # 🆕 Batafsil tahlil sahifasi
└── .github/
    └── workflows/
        └── deploy-pages.yml   # 🆕 Avtomatik GitHub Pages deploy
```

---

## 🚀 O'rnatish qo'llanmasi (Qadam-ba-qadam)

### 1️⃣ GitHub Repository yarating

1. GitHub.com ga kiring
2. **New repository** tugmasini bosing
3. Nom bering: `tutor-pro` (yoki xohlagan nom)
4. **Public** tanlang (GitHub Pages bepul faqat public uchun)
5. **Create repository**

### 2️⃣ Fayllarni GitHub ga yuklang

```bash
# Terminal da:
git init
git add .
git commit -m "TestPro Bot + Web App integration"
git remote add origin https://github.com/YOUR_USERNAME/tutor-pro.git
git push -u origin main
```

### 3️⃣ GitHub Pages ni yoqing

1. GitHub repository sahifasiga o'ting
2. **Settings** → **Pages** bo'limiga kiring
3. **Source**: `GitHub Actions` tanlang
4. Biroz kuting — `Actions` tab da deploy ishlaydi
5. URL ko'rinadi: `https://YOUR_USERNAME.github.io/tutor-pro/`

**Sizning Web App URL:**
```
https://YOUR_USERNAME.github.io/tutor-pro/webapp_pages
```

### 4️⃣ BotFather da Web App ro'yxatdan o'tkazing

Telegram da `@BotFather` ga boring:
```
/setmenubutton  ← botingizni tanlang
```
Keyin:
```
/setdomain
```
→ Botingizni tanlang → GitHub Pages URL ni kiriting:
```
YOUR_USERNAME.github.io
```

### 5️⃣ secrets.toml ni to'ldiring

`.streamlit/secrets.toml` faylida:
```toml
WEBAPP_BASE_URL = "https://YOUR_USERNAME.github.io/tutor-pro/webapp_pages"
```

### 6️⃣ Botni qayta ishga tushiring

Streamlit Cloud da:
- **Reboot app** bosing

Lokal da:
```bash
streamlit run streamlit_app.py
```

---

## 🎮 Funksiyalar

### Test Yechish — 3 usul

| Usul | Ko'rinish | Qayerda |
|------|-----------|---------|
| 🎮 **Web App** | Chiroyli popup oyna | Bot chatida |
| ▶️ **Inline** | Xabarlar orqali | Bot chatida |
| 📊 **Poll** | Native Telegram quiz | Bot chatida |

**Web App test yechish jarayoni:**
1. Test kodini yuboring yoki katalogdan tanlang
2. `🎮 Web App (zamonaviy)` tugmasini bosing
3. Popup oyna ochiladi — test yechib bo'ling
4. Natija avtomatik botga yuboriladi
5. Bot natijani chiroyli xabar sifatida ko'rsatadi
6. `🔍 Batafsil tahlil (Web App)` → `review.html` ochiladi

### Natijalar Tarixi

`📊 Natijalarim` bosilganda:
- `📜 Natijalar tarixi (Web App)` → `history.html` popup oynada ochiladi
- `📋 Oddiy ro'yxat` → chat ichida matn ko'rinishida

### Test Yaratish

`➕ Test Yaratish` bosilganda:
- `✨ Web App orqali yaratish` → `create.html` popup oynada ochiladi
- Barcha savollarni vizual muharrir orqali yaratish va tahrirlash
- `doSave()` botga xabar yuboradi: `test_created`

### Batafsil Tahlil

Test yakunlanganda:
- `🔍 Batafsil tahlil (Web App)` → `review.html` popup oynada ochiladi
- Har bir savol bo'yicha to'g'ri/noto'g'ri ko'rinadi
- Izohlar ko'rsatiladi
- Filtrlar: barchasi / to'g'ri / xato / o'tkazilgan

---

## 🔧 Texnik tushuntirma

### sendData() qanday ishlaydi?

```javascript
// test.html ichida (finish() funksiyasida):
window.Telegram.WebApp.sendData(JSON.stringify({
  type: "test_result",
  test_id: "ABC123",
  score: 85,
  correct: 17,
  total: 20,
  elapsed: 145,
  passed: true,
  questions: [...]  // har bir savol natijasi
}));
```

```python
# handlers/webapp.py da:
@router.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    data = json.loads(message.web_app_data.data)
    if data["type"] == "test_result":
        # Firebase ga saqlash + chiroyli xabar
```

### review.html ma'lumot olish usuli

Bot `result_keyboard()` da URL ga base64 encoded JSON qo'shadi:
```
https://...github.io/webapp_pages/review.html?result=BASE64_DATA
```

`review.html` URL dan o'qiydi:
```javascript
const raw = new URLSearchParams(location.search).get('result');
const data = JSON.parse(atob(decodeURIComponent(raw)));
```

---

## ⚠️ Muhim eslatmalar

1. **HTTPS shart!** — Telegram Web App faqat HTTPS URLlarni qabul qiladi. GitHub Pages avtomatik HTTPS beradi.

2. **Domain ro'yxatdan o'tkazish** — BotFather da `/setdomain` orqali GitHub Pages domenini qo'shing.

3. **URL uzunligi** — `review.html?result=...` da base64 ma'lumot 2048 belgidan oshmasligi kerak. Juda uzun bo'lsa, bot oddiy tahlilga o'tadi.

4. **Firebase + Telegram ikki tomonlama** — `test.html` Firebase Auth ishlatadi. Agar auth ishlamasa ham, test yechish davom etadi va natija `sendData()` orqali botga yuboriladi.

5. **`webapp_pages` papkasini** — GitHub Pages faqat shu papkani serve qiladi (Actions workflow sozlangan).

---

## 🐛 Muammolar va Yechimlar

| Muammo | Yechim |
|--------|--------|
| Web App tugmasi ko'rinmayapti | `WEBAPP_BASE_URL` ni secrets.toml ga qo'shing |
| Natija botga kelmayapti | BotFather da domain ro'yxatdan o'tkazing |
| "HTTPS required" xatosi | GitHub Pages HTTPS shart — HTTP ishlamaydi |
| review.html ochilmayapti | URL 2048 belgidan oshgan — bot oddiy tahlil yuboradi |
| history.html bo'sh | Firebase Auth yoki user_id URL da yo'q |

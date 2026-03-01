# 🎓 Quiz Bot Pro — v5

## Yangiliklar (v5)

### 🗄️ Kesh Arxitekturasi
- **Testlar**: Firebase Storage da `tests.txt` (JSON lines) — kun davomida 1 marta yuklanadi
- **Foydalanuvchilar**: `users.txt` — kun davomida 1 marta yuklanadi
- **Natijalar**: Firestore `results_latest` — har test uchun 1 ta (oxirgi) saqlanadi
- **Kunlik flush**: tun yarimi kesh → Storage/Firestore ga yoziladi

### 🤖 Bot Yangiliklari
1. **Test tanlash → 3 usul**: 🎮 Web App | ▶️ Inline | 📊 Poll
2. **Bot linki**: `t.me/botusername?start=TEST_ID` → WebApp ochiladi
3. **Kalit tugmasi**: Fayl/poll yuklangach `create.html` da savollar ko'rinadi
4. **Tahlil link**: Natijadan `review.html` ga WebApp link
5. **Tarix**: `Natijalarim` → `history.html` WebApp

### 📁 Firebase JS (HTML sahifalar uchun)
- `webapp_pages/firebase-config.js` faylini o'z loyiha ma'lumotlari bilan to'ldiring
- `test.html?test_id=ABCD1234` — Firebase dan test yuklab olish
- `history.html?user_id=123456789` — Firebase dan natijalar

### ⚙️ Sozlash

**.streamlit/secrets.toml**:
```toml
BOT_TOKEN = "..."
ADMIN_IDS = "123456789"
ADMIN_PASSWORD = "parol"
WEBAPP_BASE_URL = "https://username.github.io/repo/webapp_pages"

[firebase]
api_key = "..."
project_id = "loyiha-id"
storage_bucket = "loyiha-id.appspot.com"

[firebase_sa]
type = "service_account"
project_id = "loyiha-id"
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "firebase-adminsdk@loyiha-id.iam.gserviceaccount.com"
```

**firebase-config.js** — `FIREBASE_CONFIG` o'zgaruvchini to'ldiring.

### 🔄 Ishlash Prinsipi
```
Kun boshida:
  Firebase Storage (tests.txt, users.txt) → Streamlit kesh

Kun davomida:
  Bot yangi testlar → faqat keshda
  Natijalar → Firestore results_latest (tezkor)
  
Tun yarimi:
  Kesh → Storage (tests.txt, users.txt)
  Natijalar allaqachon Firestore da
```

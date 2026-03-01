# 🎓 TestPro — Telegram Web App Integratsiyasi

## Arxitektura

```
BOT (Python/Firebase)          URL ?data=BASE64       HTML (GitHub Pages)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Firebase → test/savollar  ──→  base64 encode    ──→  URL dan o'qiydi
                                                      Firebase yo'q ✅
User javoblari ←────────────────── sendData() ──────────────────
```

## Test tanlashda 3 USUL

| Tugma | Qanday ishlaydi |
|-------|----------------|
| 🎮 Web App | Firebase siz, URL da base64, chiroyli interfeys |
| ▶️ Inline | Savol-javob xabar orqali, darhol feedback |
| 📊 Poll | Native Telegram quiz poll, anonymous |

## Test yaratishda oqim

```
➕ Test Yaratish
├── ✨ Web App muharriri → create.html (bo'sh)
│     Foydalanuvchi qo'lda savol kiritadi
│     💾 Saqlash → sendData() → bot saqlaydi
│
├── 📁 Fayl (TXT/PDF/DOCX)
│     Parser savollarni chiqaradi
│     ✅ {N} ta savol topildi
│     ├── 🎨 Web App da ko'rish va tahrirlash
│     │     → create.html ?data=BASE64 (savollar yuklangan)
│     │     Tahrirlash, o'chirish, qo'shish
│     │     💾 Saqlash → sendData() → bot saqlaydi
│     └── ✅ Saqlash → fan → nom → ko'rinish → Firebase
│
└── 📊 QuizBot Poll Forward
      Har poll forward qilinadi
      ✅ Tayyor
      ├── 🎨 Web App da ko'rish va tahrirlash (yuqoridek)
      └── ✅ Saqlash → fan → nom → ko'rinish → Firebase
```

## GitHub Pages sozlash

1. Repository yaratish (public)
2. `git push` qilish
3. Settings → Pages → Source: GitHub Actions
4. URL olish: `https://USERNAME.github.io/REPO/`
5. BotFather: `/setdomain` → `USERNAME.github.io`
6. `.streamlit/secrets.toml`:
   ```toml
   WEBAPP_BASE_URL = "https://USERNAME.github.io/REPO/webapp_pages"
   ```

## HTML fayllar

| Fayl | Maqsad | Ma'lumot qayerdan |
|------|--------|------------------|
| `test.html` | Test yechish | `?data=BASE64` (test+savollar) |
| `create.html` | Test yaratish/tahrirlash | `?data=BASE64` (savollar) yoki bo'sh |
| `history.html` | Natijalar tarixi | `?data=BASE64` (natijalar ro'yxati) |
| `review.html` | Tahlil | `?data=BASE64` (tahlil ma'lumoti) |

## Bot handlers

| Fayl | Maqsad |
|------|--------|
| `handlers/webapp.py` | `sendData()` natijalarini qabul qilish |
| `handlers/tests.py` | Test tanlash, 3 usul klaviaturasi |
| `handlers/create_test.py` | Test yaratish oqimi |
| `keyboards/keyboards.py` | Barcha klaviaturalar, URL builder |

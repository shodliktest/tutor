"""
🌐 ADMIN WEB PANEL — Streamlit v5
Kesh arxitekturasi:
- Testlar, foydalanuvchilar: session_state da saqlanadi
- Kunlik flush: kuning oxirida Storage/Firestore ga yoziladi
- Natijalar: Firestore (kichik hajm)
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import time
import threading
import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)

st.set_page_config(page_title="Quiz Bot | Admin", page_icon="🎓",
                   layout="wide", initial_sidebar_state="expanded")


# ══════════════════════════════════════════════════════════
# TIZIMNI ISHGA TUSHIRISH
# ══════════════════════════════════════════════════════════

@st.cache_resource
def init_system():
    from firebase.config import initialize_firebase
    from bot import run_bot_in_background
    initialize_firebase()
    bot_thread = run_bot_in_background()
    # Kunlik flush schedulerini ishga tushirish
    _start_daily_flush()
    return bot_thread


def _start_daily_flush():
    """Har 24 soatda bir marta keshni Storage ga yozish"""
    def _flush_loop():
        while True:
            # Tun yarimi kutamiz
            now = datetime.now(timezone.utc)
            seconds_to_midnight = (24 * 3600) - (now.hour * 3600 + now.minute * 60 + now.second)
            time.sleep(max(seconds_to_midnight, 3600))  # kamida 1 soat
            try:
                from firebase.db import flush_all_to_storage
                flush_all_to_storage()
                log.info("✅ Kunlik flush bajarildi")
            except Exception as e:
                log.error(f"Flush xatosi: {e}")

    t = threading.Thread(target=_flush_loop, daemon=True, name="DailyFlush")
    t.start()


bot_thread = init_system()


# ══════════════════════════════════════════════════════════
# MA'LUMOTLARNI YUKLASH (session_state kesh)
# ══════════════════════════════════════════════════════════

def load_data(force_refresh: bool = False):
    """
    Ma'lumotlarni session_state keshdan olish.
    force_refresh=True bo'lsa Firebase dan yangilaydi.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    cache_valid = (
        "data_date" in st.session_state and
        st.session_state["data_date"] == today and
        not force_refresh
    )

    if not cache_valid:
        from firebase.db import get_all_users, get_all_tests, get_global_leaderboard
        st.session_state["users_data"] = get_all_users()
        st.session_state["tests_data"] = get_all_tests()
        st.session_state["leaders_data"] = get_global_leaderboard(limit=50)
        st.session_state["data_date"] = today

    return (
        st.session_state.get("users_data", []),
        st.session_state.get("tests_data", []),
        st.session_state.get("leaders_data", []),
    )


# ── Login ─────────────────────────────────────────────────
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Admin Panel — Kirish")
    pwd = st.text_input("Parol:", type="password")
    if st.button("Kirish"):
        correct = st.secrets.get("ADMIN_PASSWORD", "admin123")
        if pwd == correct:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("❌ Noto'g'ri parol!")
    st.stop()

# Ma'lumotlarni yuklash
users_data, tests_data, leaders_data = load_data()

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.title("🎓 Quiz Bot Pro")
    if bot_thread and bot_thread.is_alive():
        st.success("🟢 Bot Online")
    else:
        st.error("🔴 Bot to'xtagan")

    st.markdown("---")
    menu = st.radio("📋 Menyu", [
        "📊 Dashboard", "👥 Foydalanuvchilar",
        "📋 Testlar", "🎮 Test Yechish (Modal)",
        "📜 Natijalar Tarixi", "📄 Test TXT yuklab olish",
        "🏆 Reyting", "💾 Storage Boshqaruvi", "⚙️ Sozlamalar"
    ])
    st.markdown("---")

    # Kesh holati
    today = datetime.now().strftime("%Y-%m-%d")
    cache_ok = st.session_state.get("data_date") == today
    st.info(f"📦 Kesh: {'✅ Bugungi' if cache_ok else '❌ Yangilanmagan'}")

    if st.button("🔄 Yangilash (Firebase)"):
        load_data(force_refresh=True)
        st.rerun()

    if st.button("🚪 Chiqish"):
        st.session_state.auth = False
        st.rerun()


# ─────────────────────────────────────────────────────────
# 📊 DASHBOARD
# ─────────────────────────────────────────────────────────
if menu == "📊 Dashboard":
    st.header("📊 Tizim holati")

    c1, c2, c3, c4 = st.columns(4)
    active = [u for u in users_data if u.get("total_tests", 0) > 0]
    avg_s = round(sum(u.get("avg_score", 0) for u in active) / len(active), 1) if active else 0

    c1.metric("👥 Foydalanuvchilar", f"{len(users_data)} ta")
    c2.metric("📋 Testlar",          f"{len(tests_data)} ta")
    c3.metric("🎯 Ishlangan",        f"{sum(t.get('solve_count', 0) for t in tests_data)} marta")
    c4.metric("📈 O'rtacha",         f"{avg_s}%")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📁 Fanlar bo'yicha")
        if tests_data:
            df = pd.DataFrame(tests_data)
            df["category"] = df.get("category", pd.Series(dtype=str)).fillna("Boshqa")
            fig = px.pie(df, names="category", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("🏆 Top 5 faol")
        if users_data:
            df_u = pd.DataFrame(users_data)
            df_u["total_tests"] = df_u.get("total_tests", pd.Series(dtype=int)).fillna(0)
            top5 = df_u[df_u["total_tests"] > 0].sort_values("total_tests", ascending=False).head(5)
            if not top5.empty:
                fig2 = px.bar(top5, x="name", y="total_tests", text="total_tests", color="name")
                fig2.update_traces(textposition="outside")
                st.plotly_chart(fig2, use_container_width=True)


# ─────────────────────────────────────────────────────────
# 👥 FOYDALANUVCHILAR
# ─────────────────────────────────────────────────────────
elif menu == "👥 Foydalanuvchilar":
    st.header("👥 Foydalanuvchilar")
    if not users_data:
        st.warning("Bo'sh.")
    else:
        df = pd.DataFrame(users_data)
        for col in ["telegram_id", "name", "username", "role", "total_tests", "avg_score", "is_blocked"]:
            if col not in df.columns: df[col] = None
        df_s = df[["telegram_id", "name", "username", "role", "total_tests", "avg_score", "is_blocked"]].copy()
        df_s["avg_score"] = df_s["avg_score"].fillna(0).round(1).astype(str) + "%"
        df_s.columns = ["ID", "Ism", "Username", "Rol", "Testlar", "O'rtacha", "Bloklangan"]
        q = st.text_input("🔍 Qidirish:")
        if q:
            mask = (df_s["Ism"].astype(str).str.contains(q, case=False, na=False) |
                    df_s["ID"].astype(str).str.contains(q, na=False))
            df_s = df_s[mask]
        st.dataframe(df_s, use_container_width=True)
        st.caption(f"Jami: {len(users_data)} ta")

        st.markdown("### 🚫 Bloklash / Ochish")
        opts = [f"{r.get('telegram_id', '?')} — {r.get('name', '?')}" for r in users_data]
        sel = st.selectbox("Tanlang:", opts)
        if st.button("⚡ Holatini o'zgartirish"):
            from firebase.db import block_user, get_user
            uid_s = int(sel.split(" — ")[0])
            u = get_user(uid_s)
            if u:
                block_user(uid_s, not u.get("is_blocked", False))
                load_data(force_refresh=True)
                st.success("✅ O'zgartirildi!")
                st.rerun()


# ─────────────────────────────────────────────────────────
# 📋 TESTLAR
# ─────────────────────────────────────────────────────────
elif menu == "📋 Testlar":
    st.header("📋 Testlar bazasi")
    if not tests_data:
        st.warning("Bo'sh.")
    else:
        df = pd.DataFrame(tests_data)
        df["savollar"] = df["questions"].apply(lambda x: len(x) if isinstance(x, list) else 0)
        disp = ["test_id", "title", "category", "difficulty", "savollar", "solve_count", "visibility", "avg_score"]
        st.dataframe(df[[c for c in disp if c in df.columns]], use_container_width=True)
        st.caption(f"Jami: {len(tests_data)} ta")

        st.markdown("### 🗑 O'chirish")
        opts = [f"{r.get('test_id', '?')} — {r.get('title', '?')}" for r in tests_data]
        sel = st.selectbox("Test:", opts)
        if st.button("🗑 O'chirish", type="primary"):
            from firebase.db import delete_test
            delete_test(sel.split(" — ")[0])
            load_data(force_refresh=True)
            st.success("✅ O'chirildi!")
            st.rerun()


# ─────────────────────────────────────────────────────────
# 📄 TEST TXT YUKLAB OLISH
# ─────────────────────────────────────────────────────────
elif menu == "📄 Test TXT yuklab olish":
    st.header("📄 Testni TXT formatda yuklab olish")
    if not tests_data:
        st.warning("Testlar yo'q.")
    else:
        opts = [f"{t.get('test_id')} — {t.get('title', '?')} ({len(t.get('questions', []))} savol)"
                for t in tests_data]
        sel = st.selectbox("Testni tanlang:", opts)
        sel_id = sel.split(" — ")[0].strip()
        sel_test = next((t for t in tests_data if t.get("test_id") == sel_id), None)

        if sel_test and st.button("📥 TXT yuklab olish"):
            from handlers.profile import _test_to_txt
            txt = _test_to_txt(sel_test)
            fname = f"{sel_test.get('title', sel_id)}.txt"
            st.download_button(
                label=f"⬇️ {fname} ni yuklash",
                data=txt.encode("utf-8"),
                file_name=fname,
                mime="text/plain"
            )
            st.success(f"✅ {len(sel_test.get('questions', []))} ta savol tayyor!")
            with st.expander("📄 Fayl mazmunini ko'rish"):
                st.text(txt[:3000] + ("..." if len(txt) > 3000 else ""))


# ─────────────────────────────────────────────────────────
# 🏆 REYTING
# ─────────────────────────────────────────────────────────
elif menu == "🏆 Reyting":
    st.header("🏆 Global Reyting (TOP 50)")
    if leaders_data:
        df = pd.DataFrame(leaders_data)
        for col in ["name", "username", "avg_score", "total_tests"]:
            if col not in df.columns: df[col] = None
        df["avg_score"] = df["avg_score"].fillna(0).round(1).astype(str) + "%"
        disp = df[["name", "username", "avg_score", "total_tests"]].copy()
        disp.index = range(1, len(disp) + 1)
        disp.columns = ["Ism", "Username", "O'rtacha", "Testlar"]
        st.table(disp)
    else:
        st.info("Reyting bo'sh.")


# ─────────────────────────────────────────────────────────
# 💾 STORAGE BOSHQARUVI
# ─────────────────────────────────────────────────────────
elif menu == "💾 Storage Boshqaruvi":
    st.header("💾 Firebase Storage Boshqaruvi")

    st.info("""
    **Kesh arxitekturasi:**
    - Testlar: `tests.txt` — Firebase Storage (JSON lines)
    - Foydalanuvchilar: `users.txt` — Firebase Storage
    - Natijalar: Firestore `results_latest` (uid_testid)
    
    **Qoidalar:**
    - Testlar kun davomida bir marta yuklanadi
    - Har test uchun faqat 1 ta natija saqlanadi (oxirgi)
    - Yangi testlar + natijalar kuning oxirida yoziladi
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Testlarni hozir yozish"):
            from firebase.db import flush_tests_to_storage
            flush_tests_to_storage()
            st.success("✅ Testlar Storage ga yozildi!")

    with col2:
        if st.button("🔄 Foydalanuvchilarni yozish"):
            from firebase.db import flush_users_to_storage
            flush_users_to_storage()
            st.success("✅ Foydalanuvchilar yozildi!")

    with col3:
        if st.button("🔄 Barcha ma'lumotlarni yozish"):
            from firebase.db import flush_all_to_storage
            flush_all_to_storage()
            st.success("✅ Barcha ma'lumotlar yozildi!")

    st.markdown("---")
    st.subheader("📊 Kesh holati")
    from firebase.db import _tests_cache, _users_cache, _results_cache, _new_tests, _pending_users
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📋 Testlar (kesh)", len(_tests_cache))
    col2.metric("👥 Foydalanuvchilar (kesh)", len(_users_cache))
    col3.metric("📊 Natijalar (kesh)", sum(len(v) for v in _results_cache.values()))
    col4.metric("🆕 Yangi testlar (pending)", len(_new_tests))

    if _new_tests:
        st.warning(f"⚠️ {len(_new_tests)} ta yangi test hali Storage ga yozilmagan!")


# ─────────────────────────────────────────────────────────
# 🎮 TEST YECHISH MODAL
# ─────────────────────────────────────────────────────────
elif menu == "🎮 Test Yechish (Modal)":
    st.header("🎮 Test Yechish — Modal Oyna")

    col1, col2 = st.columns([3, 1])
    with col1:
        test_id_input = st.text_input("🔑 Test kodi:", placeholder="Masalan: ABC123")
    with col2:
        st.write(""); st.write("")
        start_btn = st.button("🚀 Boshlash", type="primary")

    if not test_id_input and tests_data:
        st.subheader("📋 Mavjud testlar")
        for t in tests_data[:10]:
            tid = t.get("test_id", "")
            title = t.get("title", "Nomsiz")
            cat = t.get("category", "")
            qc = len(t.get("questions", []))
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"**{title}** · 📁 {cat} · 📋 {qc} savol · `{tid}`")
            with col_b:
                if st.button("▶️ Yech", key=f"play_{tid}"):
                    st.session_state["active_test"] = tid

    active_tid = test_id_input.strip() if start_btn and test_id_input else st.session_state.get("active_test")
    if active_tid:
        try:
            import pathlib, json
            import streamlit.components.v1 as components
            from firebase.db import get_test as _get_test

            test = _get_test(active_tid)
            if not test:
                st.error(f"❌ Test topilmadi: `{active_tid}`")
            else:
                st.success(f"✅ **{test.get('title')}** — {len(test.get('questions', []))} ta savol")
                html_path = pathlib.Path(__file__).parent / "static" / "quiz_modal.html"
                if html_path.exists():
                    html = html_path.read_text(encoding="utf-8")
                    test_json = json.dumps(test, ensure_ascii=False, default=str)
                    inject = f"<script>window.addEventListener('load',()=>setTimeout(()=>initTest({test_json}),150));</script>"
                    html = html.replace("</body>", inject + "</body>")
                    components.html(html, height=720, scrolling=False)
                else:
                    st.error("❌ static/quiz_modal.html topilmadi")
        except Exception as e:
            st.error(f"Xatolik: {e}")


# ─────────────────────────────────────────────────────────
# 📜 NATIJALAR TARIXI
# ─────────────────────────────────────────────────────────
elif menu == "📜 Natijalar Tarixi":
    st.header("📜 Foydalanuvchi Natijalari Tarixi")

    col1, col2 = st.columns([3, 1])
    with col1:
        uid_input = st.text_input("👤 Foydalanuvchi Telegram ID:", placeholder="123456789")
    with col2:
        st.write(""); st.write("")
        load_btn = st.button("📥 Yuklash", type="primary")

    if load_btn and uid_input:
        try:
            import pathlib, json
            import streamlit.components.v1 as components
            from firebase.db import get_user_results as _get_results

            uid = int(uid_input.strip())
            results = _get_results(uid, limit=200)
            if not results:
                st.warning("📭 Bu foydalanuvchida natijalar yo'q.")
            else:
                st.success(f"✅ {len(results)} ta natija topildi")
                html_path = pathlib.Path(__file__).parent / "static" / "history_modal.html"
                if html_path.exists():
                    html = html_path.read_text(encoding="utf-8")
                    res_json = json.dumps(results, ensure_ascii=False, default=str)
                    inject = f"<script>window.addEventListener('load',()=>setTimeout(()=>initHistory({res_json}),150));</script>"
                    html = html.replace("</body>", inject + "</body>")
                    components.html(html, height=680, scrolling=False)
                else:
                    st.error("❌ static/history_modal.html topilmadi")
        except ValueError:
            st.error("❌ To'g'ri Telegram ID kiriting")
        except Exception as e:
            st.error(f"Xatolik: {e}")


# ─────────────────────────────────────────────────────────
# ⚙️ SOZLAMALAR
# ─────────────────────────────────────────────────────────
elif menu == "⚙️ Sozlamalar":
    st.header("⚙️ Konfiguratsiya")
    st.code("""
BOT_TOKEN = "7123456789:AAH..."
ADMIN_IDS = "123456789, 987654321"
ADMIN_PASSWORD = "maxfiy_parol"
WEBAPP_BASE_URL = "https://username.github.io/repo/webapp_pages"

[firebase]
api_key = "..."
project_id = "loyiha-id"
storage_bucket = "loyiha-id.appspot.com"

[firebase_sa]
type = "service_account"
project_id = "loyiha-id"
private_key = "-----BEGIN RSA PRIVATE KEY-----\\n...\\n-----END RSA PRIVATE KEY-----\\n"
client_email = "firebase-adminsdk@loyiha-id.iam.gserviceaccount.com"
""", language="toml")
    st.json({"Foydalanuvchilar": len(users_data), "Testlar": len(tests_data),
             "Bot": bot_thread.is_alive() if bot_thread else False})

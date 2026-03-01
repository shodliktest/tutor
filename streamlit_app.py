"""
🌐 ADMIN WEB PANEL + TELEGRAM WEBAPP — Streamlit
Admin panel: /              → login + dashboard
Telegram WebApp: ?mode=test|review|history → WebApp sahifasi
Scheduler: 23:55 da Firebase Storage ga sync
"""
import streamlit as st
import threading
import logging

st.set_page_config(
    page_title="Quiz Bot | Admin",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# 1. WEBAPP ROUTING — admin panel dan oldin tekshiriladi
# ═══════════════════════════════════════════════════════════

_mode = st.query_params.get("mode", "")
if _mode in ("test", "review", "history"):
    # Firebase init (bot ishga tushirilmaydi)
    try:
        from firebase.config import initialize_firebase
        initialize_firebase()
    except Exception as e:
        st.error(f"Firebase bağlantı xatosi: {e}")

    from pages.web_app import render_webapp
    render_webapp()
    st.stop()


# ═══════════════════════════════════════════════════════════
# 2. SCHEDULER — 23:55 da Firebase Storage ga sync
# ═══════════════════════════════════════════════════════════

@st.cache_resource
def _start_scheduler():
    """
    Kunlik scheduler: testlar va natijalarni Firebase Storage ga yuklaydi.
    Bu Firestore read/write limitini 70-80% kamaytiradi.
    """
    try:
        import schedule
        import time as _t

        def _daily_job():
            try:
                from utils.cache import sync_pending_results, schedule_tests_upload
                log.info("🌙 23:55 sync boshlandi...")
                sync_pending_results()
                schedule_tests_upload()
                log.info("✅ Kunlik sync yakunlandi")
            except Exception as e:
                log.error(f"Kunlik sync xato: {e}")

        schedule.every().day.at("23:55").do(_daily_job)

        def _run():
            while True:
                schedule.run_pending()
                _t.sleep(60)

        t = threading.Thread(target=_run, daemon=True, name="SchedulerThread")
        t.start()
        log.info("✅ Scheduler ishga tushdi (23:55 da sync)")
        return t
    except Exception as e:
        log.error(f"Scheduler xato: {e}")
        return None


_scheduler_thread = _start_scheduler()


# ═══════════════════════════════════════════════════════════
# 3. TIZIM INIT — Firebase + Bot
# ═══════════════════════════════════════════════════════════

@st.cache_resource
def init_system():
    from firebase.config import initialize_firebase
    from bot import run_bot_in_background
    initialize_firebase()
    return run_bot_in_background()


bot_thread = init_system()


@st.cache_data(ttl=300)
def load_data():
    from firebase.db import get_all_users, get_all_tests, get_global_leaderboard
    return get_all_users(), get_all_tests(), get_global_leaderboard(limit=50)


users_data, tests_data, leaders_data = load_data()


# ═══════════════════════════════════════════════════════════
# 4. LOGIN
# ═══════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════
# 5. SIDEBAR
# ═══════════════════════════════════════════════════════════

with st.sidebar:
    st.title("🎓 Quiz Bot Pro")
    if bot_thread and bot_thread.is_alive():
        st.success("🟢 Bot Online")
    else:
        st.error("🔴 Bot to'xtagan")

    if _scheduler_thread and _scheduler_thread.is_alive():
        st.info("⏰ Scheduler: Ishlaydi")

    st.markdown("---")
    menu = st.radio("📋 Menyu", [
        "📊 Dashboard",
        "👥 Foydalanuvchilar",
        "📋 Testlar",
        "📄 Test TXT yuklab olish",
        "🏆 Reyting",
        "🔗 WebApp Havolalar",
        "⚙️ Sozlamalar",
    ])
    st.markdown("---")
    if st.button("🚪 Chiqish"):
        st.session_state.auth = False
        st.rerun()


# ═══════════════════════════════════════════════════════════
# 6. DASHBOARD
# ═══════════════════════════════════════════════════════════

if menu == "📊 Dashboard":
    import pandas as pd
    import plotly.express as px

    st.header("📊 Tizim holati")
    if st.button("🔄 Yangilash"):
        load_data.clear()
        st.rerun()

    c1, c2, c3, c4 = st.columns(4)
    active = [u for u in users_data if u.get("total_tests", 0) > 0]
    avg_s  = round(sum(u.get("avg_score", 0) for u in active)/len(active), 1) if active else 0

    c1.metric("👥 Foydalanuvchilar", f"{len(users_data)} ta")
    c2.metric("📋 Testlar",          f"{len(tests_data)} ta")
    c3.metric("🎯 Ishlangan",        f"{sum(t.get('solve_count',0) for t in tests_data)} marta")
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


# ═══════════════════════════════════════════════════════════
# 7. FOYDALANUVCHILAR
# ═══════════════════════════════════════════════════════════

elif menu == "👥 Foydalanuvchilar":
    import pandas as pd
    st.header("👥 Foydalanuvchilar")
    if st.button("🔄 Yangilash"):
        load_data.clear()
        st.rerun()

    if not users_data:
        st.warning("Bo'sh.")
    else:
        df = pd.DataFrame(users_data)
        for col in ["telegram_id","name","username","role","total_tests","avg_score","is_blocked"]:
            if col not in df.columns:
                df[col] = None
        df_s = df[["telegram_id","name","username","role","total_tests","avg_score","is_blocked"]].copy()
        df_s["avg_score"] = df_s["avg_score"].fillna(0).round(1).astype(str) + "%"
        df_s.columns = ["ID","Ism","Username","Rol","Testlar","O'rtacha","Bloklangan"]

        q = st.text_input("🔍 Qidirish:")
        if q:
            mask = (df_s["Ism"].astype(str).str.contains(q, case=False, na=False) |
                    df_s["ID"].astype(str).str.contains(q, na=False))
            df_s = df_s[mask]

        st.dataframe(df_s, use_container_width=True)
        st.caption(f"Jami: {len(users_data)} ta")

        st.markdown("### 🚫 Bloklash / Ochish")
        opts = [f"{r.get('telegram_id','?')} — {r.get('name','?')}" for r in users_data]
        sel  = st.selectbox("Tanlang:", opts)
        if st.button("⚡ Holatini o'zgartirish"):
            from firebase.db import block_user, get_user
            uid_s = int(sel.split(" — ")[0])
            u     = get_user(uid_s)
            if u:
                block_user(uid_s, not u.get("is_blocked", False))
                load_data.clear()
                st.success("✅ O'zgartirildi!")
                st.rerun()


# ═══════════════════════════════════════════════════════════
# 8. TESTLAR
# ═══════════════════════════════════════════════════════════

elif menu == "📋 Testlar":
    import pandas as pd
    st.header("📋 Testlar bazasi")
    if st.button("🔄 Yangilash"):
        load_data.clear()
        st.rerun()

    if not tests_data:
        st.warning("Bo'sh.")
    else:
        df = pd.DataFrame(tests_data)
        df["savollar"] = df["questions"].apply(lambda x: len(x) if isinstance(x, list) else 0)
        disp = ["test_id","title","category","difficulty","savollar","solve_count","visibility","avg_score"]
        st.dataframe(df[[c for c in disp if c in df.columns]], use_container_width=True)
        st.caption(f"Jami: {len(tests_data)} ta")

        st.markdown("### 🗑 O'chirish")
        opts = [f"{r.get('test_id','?')} — {r.get('title','?')}" for r in tests_data]
        sel  = st.selectbox("Test:", opts)
        if st.button("🗑 O'chirish", type="primary"):
            from firebase.db import delete_test
            delete_test(sel.split(" — ")[0])
            load_data.clear()
            st.success("✅ O'chirildi!")
            st.rerun()


# ═══════════════════════════════════════════════════════════
# 9. TXT YUKLAB OLISH
# ═══════════════════════════════════════════════════════════

elif menu == "📄 Test TXT yuklab olish":
    st.header("📄 Testni TXT formatda yuklab olish")
    st.info("Bu bo'lim faqat admin uchun.")

    if not tests_data:
        st.warning("Testlar yo'q.")
    else:
        opts = [f"{t.get('test_id')} — {t.get('title','?')} ({len(t.get('questions',[]))} savol)"
                for t in tests_data]
        sel     = st.selectbox("Testni tanlang:", opts)
        sel_id  = sel.split(" — ")[0].strip()
        sel_test = next((t for t in tests_data if t.get("test_id") == sel_id), None)

        if sel_test and st.button("📥 TXT yuklab olish"):
            from handlers.profile import _test_to_txt
            txt   = _test_to_txt(sel_test)
            fname = f"{sel_test.get('title', sel_id)}.txt"
            st.download_button(
                label    = f"⬇️ {fname} ni yuklash",
                data     = txt.encode("utf-8"),
                file_name= fname,
                mime     = "text/plain"
            )
            st.success(f"✅ {len(sel_test.get('questions',[]))} ta savol tayyor!")
            with st.expander("📄 Fayl mazmunini ko'rish"):
                st.text(txt[:3000] + ("..." if len(txt) > 3000 else ""))


# ═══════════════════════════════════════════════════════════
# 10. REYTING
# ═══════════════════════════════════════════════════════════

elif menu == "🏆 Reyting":
    import pandas as pd
    st.header("🏆 Global Reyting (TOP 50)")
    if st.button("🔄 Yangilash"):
        load_data.clear()
        st.rerun()

    if leaders_data:
        df = pd.DataFrame(leaders_data)
        for col in ["name","username","avg_score","total_tests"]:
            if col not in df.columns:
                df[col] = None
        df["avg_score"] = df["avg_score"].fillna(0).round(1).astype(str) + "%"
        disp = df[["name","username","avg_score","total_tests"]].copy()
        disp.index = range(1, len(disp)+1)
        disp.columns = ["Ism","Username","O'rtacha","Testlar"]
        st.table(disp)
    else:
        st.info("Reyting bo'sh.")


# ═══════════════════════════════════════════════════════════
# 11. WEBAPP HAVOLALAR
# ═══════════════════════════════════════════════════════════

elif menu == "🔗 WebApp Havolalar":
    st.header("🔗 Telegram WebApp Havolalar")

    try:
        from config import STREAMLIT_URL
    except ImportError:
        STREAMLIT_URL = "https://your-app.streamlit.app"

    st.info(f"🌐 Streamlit URL: `{STREAMLIT_URL}`")

    st.markdown("### 📋 URL formatlar")
    st.code(f"""
# Test yechish:
{STREAMLIT_URL}/?mode=test&test_id=TEST_ID&user_id=USER_ID

# Batafsil tahlil:
{STREAMLIT_URL}/?mode=review&result_id=RESULT_ID&user_id=USER_ID

# Natijalar tarixi:
{STREAMLIT_URL}/?mode=history&user_id=USER_ID
    """, language="text")

    st.markdown("### 🤖 Bot keyboards.py misoli")
    st.code(f"""
from aiogram.types import InlineKeyboardButton, WebAppInfo

# Test WebApp
InlineKeyboardButton(
    text="🌐 Web test",
    web_app=WebAppInfo(url="{STREAMLIT_URL}/?mode=test&test_id=TEST_ID&user_id=USER_ID")
)

# Natijalar tarixi
InlineKeyboardButton(
    text="📜 Natijalarim",
    web_app=WebAppInfo(url="{STREAMLIT_URL}/?mode=history&user_id=USER_ID")
)
    """, language="python")

    st.markdown("### 🔄 Qo'lda sync")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Testlarni Storage ga yuklash"):
            try:
                from firebase.db import get_all_tests
                from firebase.storage import upload_tests_txt
                tests = get_all_tests()
                if upload_tests_txt(tests):
                    st.success(f"✅ {len(tests)} ta test yuklandi!")
                else:
                    st.error("❌ Yuklashda xato")
            except Exception as e:
                st.error(f"❌ Xato: {e}")

    with col2:
        if st.button("🔄 Natijalarni sync qilish"):
            try:
                from utils.cache import sync_pending_results
                sync_pending_results()
                st.success("✅ Natijalar sync qilindi!")
            except Exception as e:
                st.error(f"❌ Xato: {e}")


# ═══════════════════════════════════════════════════════════
# 12. SOZLAMALAR
# ═══════════════════════════════════════════════════════════

elif menu == "⚙️ Sozlamalar":
    st.header("⚙️ Konfiguratsiya")
    st.code("""
BOT_TOKEN = "7123456789:AAH..."
ADMIN_IDS = "123456789, 987654321"
ADMIN_PASSWORD = "maxfiy_parol"
STREAMLIT_URL = "https://your-app.streamlit.app"

[firebase_sa]
type = "service_account"
project_id = "loyiha-id"
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\\n...\\n-----END RSA PRIVATE KEY-----\\n"
client_email = "firebase-adminsdk-...@loyiha-id.iam.gserviceaccount.com"
client_id = "..."

[firebase]
storage_bucket = "loyiha-id.appspot.com"
    """, language="toml")

    st.markdown("### ✉️ Admin javob berish")
    st.code("/reply 123456789 Xabaringizni oldim, hal qilindi!", language="text")

    st.markdown("### 📊 Tizim ma'lumotlari")
    st.json({
        "Foydalanuvchilar": len(users_data),
        "Testlar": len(tests_data),
        "Bot": bot_thread.is_alive() if bot_thread else False,
        "Scheduler": _scheduler_thread.is_alive() if _scheduler_thread else False,
    })

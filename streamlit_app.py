"""
🌐 ADMIN WEB PANEL — Streamlit
Admin Streamlit orqali test TXT yuklab olish
use_container_width → width='stretch'
"""
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Quiz Bot | Admin", page_icon="🎓",
                   layout="wide", initial_sidebar_state="expanded")


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
        "📋 Testlar", "📄 Test TXT yuklab olish",
        "🏆 Reyting", "⚙️ Sozlamalar"
    ])
    st.markdown("---")
    if st.button("🚪 Chiqish"):
        st.session_state.auth = False
        st.rerun()

# ─────────────────────────────────────────────────────────
# 📊 DASHBOARD
# ─────────────────────────────────────────────────────────
if menu == "📊 Dashboard":
    st.header("📊 Tizim holati")
    if st.button("🔄 Yangilash"):
        load_data.clear(); st.rerun()

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
            st.plotly_chart(fig, width="stretch")
    with col2:
        st.subheader("🏆 Top 5 faol")
        if users_data:
            df_u = pd.DataFrame(users_data)
            df_u["total_tests"] = df_u.get("total_tests", pd.Series(dtype=int)).fillna(0)
            top5 = df_u[df_u["total_tests"] > 0].sort_values("total_tests", ascending=False).head(5)
            if not top5.empty:
                fig2 = px.bar(top5, x="name", y="total_tests", text="total_tests", color="name")
                fig2.update_traces(textposition="outside")
                st.plotly_chart(fig2, width="stretch")

# ─────────────────────────────────────────────────────────
# 👥 FOYDALANUVCHILAR
# ─────────────────────────────────────────────────────────
elif menu == "👥 Foydalanuvchilar":
    st.header("👥 Foydalanuvchilar")
    if st.button("🔄 Yangilash"):
        load_data.clear(); st.rerun()

    if not users_data:
        st.warning("Bo'sh.")
    else:
        df = pd.DataFrame(users_data)
        for col in ["telegram_id","name","username","role","total_tests","avg_score","is_blocked"]:
            if col not in df.columns: df[col] = None
        df_s = df[["telegram_id","name","username","role","total_tests","avg_score","is_blocked"]].copy()
        df_s["avg_score"] = df_s["avg_score"].fillna(0).round(1).astype(str) + "%"
        df_s.columns = ["ID","Ism","Username","Rol","Testlar","O'rtacha","Bloklangan"]

        q = st.text_input("🔍 Qidirish:")
        if q:
            mask = (df_s["Ism"].astype(str).str.contains(q, case=False, na=False) |
                    df_s["ID"].astype(str).str.contains(q, na=False))
            df_s = df_s[mask]

        st.dataframe(df_s, width="stretch")
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

# ─────────────────────────────────────────────────────────
# 📋 TESTLAR
# ─────────────────────────────────────────────────────────
elif menu == "📋 Testlar":
    st.header("📋 Testlar bazasi")
    if st.button("🔄 Yangilash"):
        load_data.clear(); st.rerun()

    if not tests_data:
        st.warning("Bo'sh.")
    else:
        df = pd.DataFrame(tests_data)
        df["savollar"] = df["questions"].apply(lambda x: len(x) if isinstance(x, list) else 0)
        disp = ["test_id","title","category","difficulty","savollar","solve_count","visibility","avg_score"]
        st.dataframe(df[[c for c in disp if c in df.columns]], width="stretch")
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

# ─────────────────────────────────────────────────────────
# 📄 TEST TXT YUKLAB OLISH (ADMIN)
# ─────────────────────────────────────────────────────────
elif menu == "📄 Test TXT yuklab olish":
    st.header("📄 Testni TXT formatda yuklab olish")
    st.info("Bu bo'lim faqat admin uchun. Bot orqali ham /download_test buyrug'i ishlaydi.")

    if not tests_data:
        st.warning("Testlar yo'q.")
    else:
        opts = [f"{t.get('test_id')} — {t.get('title','?')} ({len(t.get('questions',[]))} savol)"
                for t in tests_data]
        sel  = st.selectbox("Testni tanlang:", opts)
        sel_id = sel.split(" — ")[0].strip()

        sel_test = next((t for t in tests_data if t.get("test_id") == sel_id), None)

        if sel_test and st.button("📥 TXT yuklab olish"):
            import sys, os
            sys.path.insert(0, os.path.dirname(__file__))
            from handlers.profile import _test_to_txt
            txt  = _test_to_txt(sel_test)
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

# ─────────────────────────────────────────────────────────
# 🏆 REYTING
# ─────────────────────────────────────────────────────────
elif menu == "🏆 Reyting":
    st.header("🏆 Global Reyting (TOP 50)")
    if st.button("🔄 Yangilash"):
        load_data.clear(); st.rerun()

    if leaders_data:
        df = pd.DataFrame(leaders_data)
        for col in ["name","username","avg_score","total_tests"]:
            if col not in df.columns: df[col] = None
        df["avg_score"] = df["avg_score"].fillna(0).round(1).astype(str) + "%"
        disp = df[["name","username","avg_score","total_tests"]].copy()
        disp.index = range(1, len(disp)+1)
        disp.columns = ["Ism","Username","O'rtacha","Testlar"]
        st.table(disp)
    else:
        st.info("Reyting bo'sh.")

# ─────────────────────────────────────────────────────────
# ⚙️ SOZLAMALAR
# ─────────────────────────────────────────────────────────
elif menu == "⚙️ Sozlamalar":
    st.header("⚙️ Konfiguratsiya")
    st.code("""
BOT_TOKEN = "7123456789:AAH..."
ADMIN_IDS = "123456789, 987654321"
ADMIN_PASSWORD = "maxfiy_parol"

[firebase_sa]
type = "service_account"
project_id = "loyiha-id"
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\\n...\\n-----END RSA PRIVATE KEY-----\\n"
client_email = "firebase-adminsdk-...@loyiha-id.iam.gserviceaccount.com"
client_id = "..."
""", language="toml")
    st.markdown("### ✉️ Admin javob berish")
    st.code("/reply 123456789 Xabaringizni oldim, hal qilindi!", language="text")
    st.json({"Foydalanuvchilar": len(users_data), "Testlar": len(tests_data),
             "Bot": bot_thread.is_alive() if bot_thread else False})

"""
🌐 ADMIN WEB PANEL — Streamlit
Parol bilan himoyalangan, Firebase keshlangan, Bot singleton threading
"""
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Quiz Bot | Admin Panel",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Bot va Firebase ishga tushirish (login dan OLDIN) ──────

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


# ── Login tizimi ───────────────────────────────────────────

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


# ── Sidebar ────────────────────────────────────────────────

with st.sidebar:
    st.title("🎓 Quiz Bot Pro")
    st.markdown("### 🤖 Bot holati")
    if bot_thread and bot_thread.is_alive():
        st.success("🟢 Bot faol (Online)")
    else:
        st.error("🔴 Bot to'xtagan")

    st.markdown("---")
    menu = st.radio("📋 Menyu", [
        "📊 Dashboard",
        "👥 Foydalanuvchilar",
        "📋 Testlar bazasi",
        "🏆 Reyting",
        "⚙️ Sozlamalar",
    ])
    st.markdown("---")
    if st.button("🚪 Chiqish"):
        st.session_state.auth = False
        st.rerun()
    st.caption("© 2026 Quiz Bot LMS")


# ═══════════════════════════════════════════════════════════
# 📊 DASHBOARD
# ═══════════════════════════════════════════════════════════

if menu == "📊 Dashboard":
    st.header("📊 Tizim holati")

    if st.button("🔄 Yangilash"):
        load_data.clear()
        st.rerun()

    c1, c2, c3, c4 = st.columns(4)
    total_u = len(users_data)
    total_t = len(tests_data)
    total_s = sum(t.get("solve_count", 0) for t in tests_data)
    active  = [u for u in users_data if u.get("total_tests", 0) > 0]
    avg_sys = round(sum(u.get("avg_score", 0) for u in active) / len(active), 1) if active else 0

    c1.metric("👥 Foydalanuvchilar", f"{total_u} ta")
    c2.metric("📋 Testlar",          f"{total_t} ta")
    c3.metric("🎯 Ishlangan",        f"{total_s} marta")
    c4.metric("📈 O'rtacha",         f"{avg_sys}%")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🗂 Fanlar bo'yicha testlar")
        if tests_data:
            df = pd.DataFrame(tests_data)
            df["category"] = df.get("category", "Boshqa").fillna("Boshqa") if "category" in df else "Boshqa"
            fig = px.pie(df, names="category", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Testlar yo'q.")

    with col2:
        st.subheader("🏆 Top 5 faol foydalanuvchi")
        if users_data:
            df_u = pd.DataFrame(users_data)
            df_a = df_u[df_u["total_tests"] > 0].sort_values("total_tests", ascending=False).head(5)
            if not df_a.empty:
                fig2 = px.bar(df_a, x="name", y="total_tests",
                              text="total_tests", color="name")
                fig2.update_traces(textposition="outside")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Hali test ishlaganlar yo'q.")


# ═══════════════════════════════════════════════════════════
# 👥 FOYDALANUVCHILAR
# ═══════════════════════════════════════════════════════════

elif menu == "👥 Foydalanuvchilar":
    st.header("👥 Foydalanuvchilar")

    if not users_data:
        st.warning("Bazada foydalanuvchilar yo'q.")
    else:
        df = pd.DataFrame(users_data)
        cols = ["telegram_id", "name", "username", "role", "total_tests", "avg_score", "is_blocked"]
        df_show = df[[c for c in cols if c in df.columns]].copy()
        if "avg_score" in df_show:
            df_show["avg_score"] = df_show["avg_score"].round(1).astype(str) + "%"
        df_show.columns = [
            "ID", "Ism", "Username", "Rol",
            "Yechgan testlar", "O'rtacha", "Bloklangan"
        ][:len(df_show.columns)]

        q = st.text_input("🔍 Qidirish (Ism yoki ID):")
        if q:
            df_show = df_show[
                df_show["Ism"].str.contains(q, case=False, na=False) |
                df_show["ID"].astype(str).str.contains(q)
            ]
        st.dataframe(df_show, use_container_width=True)

        st.markdown("### 🚫 Bloklash / Ochish")
        options = df.apply(lambda r: f"{r['telegram_id']} — {r['name']}", axis=1).tolist()
        sel     = st.selectbox("Foydalanuvchi:", options)
        if st.button("Holatini o'zgartirish"):
            from firebase.db import block_user as _bu, get_user as _gu
            uid_sel = int(sel.split(" — ")[0])
            u_data  = _gu(uid_sel)
            if u_data:
                _bu(uid_sel, not u_data.get("is_blocked", False))
                load_data.clear()
                st.success("✅ Holat o'zgartirildi!")
                st.rerun()


# ═══════════════════════════════════════════════════════════
# 📋 TESTLAR BAZASI
# ═══════════════════════════════════════════════════════════

elif menu == "📋 Testlar bazasi":
    st.header("📋 Testlar bazasi")

    if not tests_data:
        st.warning("Bazada testlar yo'q.")
    else:
        df = pd.DataFrame(tests_data)
        df["savollar"] = df["questions"].apply(lambda x: len(x) if isinstance(x, list) else 0)
        if "created_at" in df.columns:
            df["yaratilgan"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d")

        disp_cols = ["test_id", "title", "category", "difficulty", "savollar", "solve_count", "visibility"]
        avail = [c for c in disp_cols if c in df.columns]
        st.dataframe(df[avail], use_container_width=True)

        st.markdown("### 🗑 Testni o'chirish")
        opts = df.apply(lambda r: f"{r['test_id']} — {r.get('title', '?')}", axis=1).tolist()
        sel  = st.selectbox("Test:", opts)
        if st.button("🗑 O'chirish", type="primary"):
            from firebase.db import delete_test as _dt
            tid_sel = sel.split(" — ")[0]
            _dt(tid_sel)
            load_data.clear()
            st.success("✅ Test o'chirildi!")
            st.rerun()


# ═══════════════════════════════════════════════════════════
# 🏆 REYTING
# ═══════════════════════════════════════════════════════════

elif menu == "🏆 Reyting":
    st.header("🏆 Global Reyting (TOP 50)")
    if leaders_data:
        df = pd.DataFrame(leaders_data)
        df["avg_score"] = df["avg_score"].round(1).astype(str) + "%"
        disp = df[["name", "username", "avg_score", "total_tests"]].copy()
        disp.index += 1
        disp.columns = ["Ism", "Username", "O'rtacha", "Ishlagan testlar"]
        st.table(disp)
    else:
        st.info("Reyting uchun kamida 1 ta test ishlagan foydalanuvchi kerak.")


# ═══════════════════════════════════════════════════════════
# ⚙️ SOZLAMALAR
# ═══════════════════════════════════════════════════════════

elif menu == "⚙️ Sozlamalar":
    st.header("⚙️ Secrets konfiguratsiyasi")
    st.info("Streamlit Cloud → App settings → Secrets bo'limiga quyidagilarni kiriting:")
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
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
""", language="toml")
    st.markdown("### 📋 Tizim holati")
    st.json({
        "Foydalanuvchilar": len(users_data),
        "Testlar": len(tests_data),
        "Bot ishlayapti": bot_thread.is_alive() if bot_thread else False,
    })

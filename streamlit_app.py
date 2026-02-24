"""
🌐 STREAMLIT WEB INTERFEYSI
Quiz Bot uchun admin va foydalanuvchi paneli
"""
import streamlit as st
from firebase.config import initialize_firebase
from firebase.db import (
    get_all_tests, get_all_users, get_user_results,
    get_global_leaderboard, get_test_results, get_test
)
from config import SUBJECTS, DIFFICULTY_LEVELS, TEST_TYPES, ADMIN_IDS

st.set_page_config(
    page_title="Quiz Bot Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════
# 🔥 FIREBASE — bir marta ishga tushirish (cache_resource)
# ══════════════════════════════════════════════════════════
@st.cache_resource
def init_firebase():
    return initialize_firebase()

# ══════════════════════════════════════════════════════════
# 🤖 BOT — alohida thread da ishga tushirish
#   cache_resource: Streamlit qayta render qilsa ham
#   bot qayta-qayta ishga tushmaydi (Singleton)
# ══════════════════════════════════════════════════════════
@st.cache_resource
def start_bot_thread():
    """
    cache_resource — Streamlit qayta render qilsa ham
    bu funksiya FAQAT BIR MARTA chaqiriladi.
    bot.py dagi _lock ham qo'shimcha himoya beradi.
    """
    try:
        from bot import run_bot
        thread = run_bot()
        return thread
    except Exception as e:
        st.error(f"Bot ishga tushmadi: {e}")
        return None

ok = init_firebase()
_bot_thread = start_bot_thread()

if not ok:
    st.error("❌ Firebase ulanmadi! Secrets ni tekshiring.")
    st.code("""
# .streamlit/secrets.toml da bo'lishi kerak:
BOT_TOKEN = "..."
ADMIN_IDS = "123456789"

[firebase]
project_id = "..."
...

[firebase_sa]
type = "service_account"
...
    """, language="toml")
    st.stop()

# ── CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem; border-radius: 12px; color: white;
    text-align: center; margin: 0.5rem 0;
}
.metric-card h2 { font-size: 2rem; margin: 0; }
.metric-card p  { margin: 0; opacity: 0.85; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/quiz.png", width=80)
    st.title("🎓 Quiz Bot")

    # Bot holati
    if _bot_thread and _bot_thread.is_alive():
        st.success("🤖 Bot: Ishlayapti ✅")
    else:
        st.error("🤖 Bot: Ishlamayapti ❌")

    st.divider()
    page = st.radio(
        "Bo'lim:",
        ["🏠 Bosh sahifa", "📚 Testlar", "👥 Foydalanuvchilar",
         "🏆 Leaderboard", "📊 Statistika", "⚙️ Sozlamalar"],
        label_visibility="collapsed"
    )

# ══════════════════════════════════════════════════════════
# 🏠 BOSH SAHIFA
# ══════════════════════════════════════════════════════════
if page == "🏠 Bosh sahifa":
    st.title("🎓 Quiz Bot — Admin Panel")

    tests  = get_all_tests(limit=200)
    users  = get_all_users(limit=500)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📋 Jami testlar",       len(tests))
    col2.metric("👥 Foydalanuvchilar",   len(users))
    col3.metric("📈 O'rtacha natija",
                f"{sum(u.get('avg_score',0) for u in users)/len(users):.1f}%" if users else "—")
    col4.metric("✅ Faol testlar",
                sum(1 for t in tests if t.get("is_active")))

    st.divider()
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("📚 So'nggi testlar")
        for t in tests[:8]:
            diff_emoji = {"easy":"🟢","medium":"🟡","hard":"🔴","expert":"⚡"}.get(t.get("difficulty",""),"⚪")
            st.write(f"{diff_emoji} **{t.get('title','—')}** — {t.get('total_attempts',0)} ta urinish")

    with col_r:
        st.subheader("👥 So'nggi foydalanuvchilar")
        for u in users[:8]:
            st.write(f"👤 **{u.get('name','—')}** — {u.get('total_tests',0)} ta test, {u.get('avg_score',0):.0f}%")

# ══════════════════════════════════════════════════════════
# 📚 TESTLAR
# ══════════════════════════════════════════════════════════
elif page == "📚 Testlar":
    st.title("📚 Testlar")

    col1, col2, col3 = st.columns(3)
    subject_filter = col1.selectbox("Fan:", ["Barchasi"] + SUBJECTS)
    diff_filter    = col2.selectbox("Qiyinlik:", ["Barchasi"] + list(DIFFICULTY_LEVELS.values()))
    search         = col3.text_input("🔍 Qidirish:")

    tests = get_all_tests(limit=200)

    if subject_filter != "Barchasi":
        tests = [t for t in tests if t.get("subject") == subject_filter]
    if diff_filter != "Barchasi":
        diff_key = {v: k for k, v in DIFFICULTY_LEVELS.items()}.get(diff_filter)
        tests = [t for t in tests if t.get("difficulty") == diff_key]
    if search:
        tests = [t for t in tests if search.lower() in t.get("title","").lower()]

    st.write(f"**{len(tests)} ta test topildi**")

    for t in tests:
        diff_emoji = {"easy":"🟢","medium":"🟡","hard":"🔴","expert":"⚡"}.get(t.get("difficulty",""),"⚪")
        with st.expander(f"{diff_emoji} {t.get('title','—')} — {t.get('subject','')}", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Savollar", t.get("question_count", 0))
            c2.metric("Urinishlar", t.get("total_attempts", 0))
            c3.metric("O'rtacha", f"{t.get('avg_score',0):.1f}%")
            c4.metric("O'tish balli", f"{t.get('passing_score',60)}%")

            st.write(f"🎮 Tur: **{TEST_TYPES.get(t.get('test_type',''), t.get('test_type',''))}**")
            st.write(f"⏱ Vaqt: **{t.get('time_limit', 30)} daqiqa**")
            st.write(f"🔗 Test ID: `{t.get('test_id','')}`")
            if t.get("description"):
                st.write(f"📝 {t.get('description')}")

            # Test natijalari
            if st.button(f"📊 Natijalarni ko'rish", key=f"res_{t.get('test_id')}"):
                results = get_test_results(t.get("test_id",""), limit=20)
                if results:
                    import pandas as pd
                    df = pd.DataFrame([{
                        "Foydalanuvchi": r.get("user_id"),
                        "Natija %": r.get("percentage", 0),
                        "To'g'ri": r.get("correct_count", 0),
                        "Noto'g'ri": r.get("wrong_count", 0),
                        "O'tdi": "✅" if r.get("passed") else "❌",
                    } for r in results])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Hali natija yo'q.")

# ══════════════════════════════════════════════════════════
# 👥 FOYDALANUVCHILAR
# ══════════════════════════════════════════════════════════
elif page == "👥 Foydalanuvchilar":
    st.title("👥 Foydalanuvchilar")

    users = get_all_users(limit=500)
    search = st.text_input("🔍 Ism bo'yicha qidirish:")
    if search:
        users = [u for u in users if search.lower() in u.get("name","").lower()]

    st.write(f"**{len(users)} ta foydalanuvchi**")

    import pandas as pd
    df = pd.DataFrame([{
        "ID":           u.get("telegram_id", ""),
        "Ism":          u.get("name", "—"),
        "Username":     f"@{u.get('username','')}" if u.get("username") else "—",
        "Rol":          u.get("role", "user"),
        "Testlar":      u.get("total_tests", 0),
        "O'rtacha %":   round(u.get("avg_score", 0), 1),
        "Holat":        "🚫 Bloklangan" if u.get("is_blocked") else "✅ Faol",
    } for u in users])
    st.dataframe(df, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════
# 🏆 LEADERBOARD
# ══════════════════════════════════════════════════════════
elif page == "🏆 Leaderboard":
    st.title("🏆 Leaderboard")

    tab1, tab2 = st.tabs(["🌍 Umumiy reyting", "📚 Fan bo'yicha"])

    with tab1:
        users = get_global_leaderboard(limit=50)
        medals = ["🥇","🥈","🥉"] + ["🏅"]*47
        for i, u in enumerate(users):
            col1, col2, col3 = st.columns([1, 4, 2])
            col1.write(medals[i] if i < len(medals) else f"{i+1}.")
            col2.write(f"**{u.get('name','—')}**")
            col3.write(f"{u.get('avg_score',0):.1f}% / {u.get('total_tests',0)} ta test")

    with tab2:
        sel_subj = st.selectbox("Fan tanlang:", SUBJECTS)
        st.info(f"📚 {sel_subj} bo'yicha test leaderboard Telegram botda ko'rinadi.")

# ══════════════════════════════════════════════════════════
# 📊 STATISTIKA
# ══════════════════════════════════════════════════════════
elif page == "📊 Statistika":
    st.title("📊 Umumiy Statistika")

    tests = get_all_tests(limit=500)
    users = get_all_users(limit=500)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📚 Fanlar bo'yicha testlar")
        subj_count = {}
        for t in tests:
            s = t.get("subject", "Boshqa")
            subj_count[s] = subj_count.get(s, 0) + 1
        if subj_count:
            import pandas as pd
            df = pd.DataFrame({"Fan": list(subj_count.keys()), "Testlar": list(subj_count.values())})
            st.bar_chart(df.set_index("Fan"))

    with col2:
        st.subheader("🎮 Test turlari bo'yicha taqsimot")
        type_count = {}
        for t in tests:
            tp = TEST_TYPES.get(t.get("test_type",""), t.get("test_type",""))
            type_count[tp] = type_count.get(tp, 0) + 1
        if type_count:
            import pandas as pd
            df2 = pd.DataFrame({"Tur": list(type_count.keys()), "Soni": list(type_count.values())})
            st.bar_chart(df2.set_index("Tur"))

    st.subheader("📈 Foydalanuvchilar faolligi")
    active = sum(1 for u in users if u.get("total_tests", 0) > 0)
    st.progress(active / len(users) if users else 0,
                text=f"Faol foydalanuvchilar: {active}/{len(users)}")

# ══════════════════════════════════════════════════════════
# ⚙️ SOZLAMALAR — SECRETS KO'RSATMASI
# ══════════════════════════════════════════════════════════
elif page == "⚙️ Sozlamalar":
    st.title("⚙️ Sozlamalar va Secrets")

    st.success("✅ Firebase ulangan va ishlayapti!")

    st.subheader("🔑 Streamlit Cloud — Secrets qo'shish yo'riqnomasi")

    st.markdown("""
    **1-qadam:** [share.streamlit.io](https://share.streamlit.io) ga kiring

    **2-qadam:** Ilovangizni toping -> **⋮ (3 nuqta)** -> **Settings**

    **3-qadam:** **Secrets** bo'limiga o'ting

    **4-qadam:** Quyidagi formatda barcha secretlarni kiriting:
    """)

    st.code("""
# ── Telegram ─────────────────────────────
BOT_TOKEN = "1234567890:ABCdefGHI..."
ADMIN_IDS  = "123456789,987654321"

# ── Firebase asosiy config ───────────────
[firebase]
api_key             = "AIzaSy..."
auth_domain         = "your-app.firebaseapp.com"
project_id          = "your-project-id"
storage_bucket      = "your-app.appspot.com"
messaging_sender_id = "123456789012"
app_id              = "1:123456789012:web:abc..."
database_url        = ""

# ── Firebase Service Account ─────────────
# Firebase Console -> Project Settings ->
# Service accounts -> Generate new private key
[firebase_sa]
type                        = "service_account"
project_id                  = "your-project-id"
private_key_id              = "abc123def456..."
private_key                 = "-----BEGIN RSA PRIVATE KEY-----\\nMIIE...\\n-----END RSA PRIVATE KEY-----\\n"
client_email                = "firebase-adminsdk-xxx@your-app.iam.gserviceaccount.com"
client_id                   = "123456789012345678901"
auth_uri                    = "https://accounts.google.com/o/oauth2/auth"
token_uri                   = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url        = "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxx%40your-app.iam.gserviceaccount.com"
universe_domain             = "googleapis.com"
    """, language="toml")

    st.warning("""
    ⚠️ **Muhim eslatmalar:**
    - `private_key` dagi yangi qatorlar `\\n` sifatida yozilishi kerak
    - Barcha qiymatlar qo'shtirnoq ichida bo'lishi kerak
    - Faylni hech qachon GitHub ga yuklamang!
    """)

    st.divider()
    st.subheader("🔍 Joriy secrets holati")
    checks = {
        "BOT_TOKEN":     bool(st.secrets.get("BOT_TOKEN")),
        "ADMIN_IDS":     bool(st.secrets.get("ADMIN_IDS")),
        "[firebase]":    "firebase" in st.secrets,
        "[firebase_sa]": "firebase_sa" in st.secrets,
    }
    for k, v in checks.items():
        st.write(f"{'✅' if v else '❌'} `{k}`")
    

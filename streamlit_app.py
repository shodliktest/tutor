"""🌐 Streamlit Admin Panel"""
import streamlit as st
import time

st.set_page_config(page_title="Quiz Bot", page_icon="🎓", layout="wide")


# ══════════════════════════════════════════════════════════
# Firebase — bir marta
# ══════════════════════════════════════════════════════════
@st.cache_resource
def _start_firebase():
    from firebase.config import init_firebase
    return init_firebase()


# ══════════════════════════════════════════════════════════
# Bot — bitta thread, hech qachon ikki marta emas
#
# st.cache_resource Streamlit Cloud da PROCESS miqyosida
# ishlaydi — sahifa har yangilansa ham bu funksiya
# faqat BIR MARTA chaqiriladi.
# ══════════════════════════════════════════════════════════
@st.cache_resource
def _start_bot():
    # Kichik kutish — Firebase tayyor bo'lsin
    time.sleep(1)
    try:
        from bot import run_bot
        thread = run_bot()
        return thread
    except Exception as e:
        return None


firebase_ok = _start_firebase()
bot_thread  = _start_bot()


# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.title("🎓 Quiz Bot")

    if bot_thread and bot_thread.is_alive():
        st.success("🤖 Bot: Ishlayapti ✅")
    else:
        st.error("🤖 Bot: Ishlamayapti ❌")
        if st.button("🔄 Botni qayta ishga tushirish"):
            # cache ni tozalash — keyingi refresh da qayta ishga tushadi
            st.cache_resource.clear()
            st.rerun()

    st.divider()
    page = st.radio("Bo'lim:", [
        "🏠 Asosiy", "📋 Testlar", "👥 Foydalanuvchilar",
        "🏆 Reyting", "📊 Statistika", "⚙️ Secrets"
    ], label_visibility="collapsed")


if not firebase_ok:
    st.error("❌ Firebase ulanmadi! Secrets ni tekshiring.")
    st.code("""
BOT_TOKEN = "..."
ADMIN_IDS = "123456789"

[firebase]
api_key = "..."
project_id = "..."
storage_bucket = "....appspot.com"
auth_domain = "....firebaseapp.com"
messaging_sender_id = "..."
app_id = "..."
database_url = ""

[firebase_sa]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
""", language="toml")
    st.stop()


from firebase.db import get_all_tests, get_all_users, get_global_leaderboard
from config import SUBJECTS, DIFFICULTY


# ═══════════════ ASOSIY ═══════════════
if page == "🏠 Asosiy":
    st.title("🎓 Quiz Bot — Admin Panel")
    tests = get_all_tests(200)
    users = get_all_users(500)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 Testlar",          len(tests))
    c2.metric("👥 Foydalanuvchilar", len(users))
    c3.metric("📈 O'rtacha ball",
              f"{sum(u.get('avg_score',0) for u in users)/len(users):.1f}%" if users else "—")
    c4.metric("🔄 Jami urinishlar",  sum(t.get("total_attempts",0) for t in tests))
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 So'nggi testlar")
        for t in tests[:8]:
            de = {"easy":"🟢","medium":"🟡","hard":"🔴","expert":"⚡"}.get(t.get("difficulty",""),"⚪")
            st.write(f"{de} **{t.get('title','')}** — {t.get('total_attempts',0)} urinish")
    with col2:
        st.subheader("👥 So'nggi foydalanuvchilar")
        for u in users[:8]:
            st.write(f"👤 **{u.get('name','')}** — {u.get('avg_score',0):.0f}% ({u.get('total_tests',0)} test)")


# ═══════════════ TESTLAR ═══════════════
elif page == "📋 Testlar":
    st.title("📋 Testlar")
    tests = get_all_tests(200)
    c1, c2, c3 = st.columns(3)
    sf = c1.selectbox("Fan:", ["Barchasi"] + SUBJECTS)
    df = c2.selectbox("Qiyinlik:", ["Barchasi"] + list(DIFFICULTY.values()))
    sr = c3.text_input("🔍 Qidirish:")
    if sf != "Barchasi":
        tests = [t for t in tests if t.get("subject") == sf]
    if df != "Barchasi":
        dk = {v: k for k, v in DIFFICULTY.items()}.get(df)
        tests = [t for t in tests if t.get("difficulty") == dk]
    if sr:
        tests = [t for t in tests if sr.lower() in t.get("title","").lower()]
    st.write(f"**{len(tests)} ta test**")
    for t in tests:
        de = {"easy":"🟢","medium":"🟡","hard":"🔴","expert":"⚡"}.get(t.get("difficulty",""),"⚪")
        with st.expander(f"{de} {t.get('title','')} — {t.get('subject','')}"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Savollar",    t.get("question_count", 0))
            c2.metric("Urinishlar",  t.get("total_attempts", 0))
            c3.metric("O'rtacha",    f"{t.get('avg_score',0):.1f}%")
            c4.metric("O'tish balli",f"{t.get('passing_score',60)}%")
            st.code(t.get("test_id",""), language=None)


# ═══════════════ FOYDALANUVCHILAR ═══════════════
elif page == "👥 Foydalanuvchilar":
    st.title("👥 Foydalanuvchilar")
    users = get_all_users(500)
    sr = st.text_input("🔍 Qidirish:")
    if sr:
        users = [u for u in users if sr.lower() in u.get("name","").lower()]
    st.write(f"**{len(users)} ta foydalanuvchi**")
    import pandas as pd
    df = pd.DataFrame([{
        "ID":       u.get("telegram_id",""),
        "Ism":      u.get("name",""),
        "Testlar":  u.get("total_tests", 0),
        "O'rtacha": f"{u.get('avg_score',0):.1f}%",
        "Holat":    "🚫" if u.get("is_blocked") else "✅",
    } for u in users])
    st.dataframe(df, use_container_width=True, hide_index=True)


# ═══════════════ REYTING ═══════════════
elif page == "🏆 Reyting":
    st.title("🏆 Reyting")
    users  = get_global_leaderboard(50)
    medals = ["🥇","🥈","🥉"] + ["🏅"] * 47
    for i, u in enumerate(users):
        c1, c2, c3 = st.columns([1, 4, 2])
        c1.write(medals[i] if i < 50 else f"{i+1}.")
        c2.write(f"**{u.get('name','')}**")
        c3.write(f"{u.get('avg_score',0):.1f}% / {u.get('total_tests',0)} test")


# ═══════════════ STATISTIKA ═══════════════
elif page == "📊 Statistika":
    st.title("📊 Statistika")
    tests = get_all_tests(500)
    users = get_all_users(500)
    c1, c2 = st.columns(2)
    import pandas as pd
    with c1:
        st.subheader("Fan bo'yicha testlar")
        sc = {}
        for t in tests:
            k = t.get("subject","?")
            sc[k] = sc.get(k, 0) + 1
        if sc:
            st.bar_chart(pd.DataFrame({"Son": sc}))
    with c2:
        st.subheader("Qiyinlik bo'yicha")
        dc = {}
        for t in tests:
            k = t.get("difficulty","?")
            dc[k] = dc.get(k, 0) + 1
        if dc:
            st.bar_chart(pd.DataFrame({"Son": dc}))


# ═══════════════ SECRETS ═══════════════
elif page == "⚙️ Secrets":
    st.title("⚙️ Secrets ko'rsatmasi")
    st.markdown("**Streamlit Cloud → App settings → Secrets** bo'limiga kiriting:")
    st.code("""
BOT_TOKEN = "bot_token_shu_yerga"
ADMIN_IDS = "123456789,987654321"

[firebase]
api_key = "AIzaSy..."
project_id = "project-id"
storage_bucket = "project-id.appspot.com"
auth_domain = "project-id.firebaseapp.com"
messaging_sender_id = "123456789"
app_id = "1:123:web:abc"
database_url = ""

[firebase_sa]
type = "service_account"
project_id = "project-id"
private_key_id = "abc123"
private_key = "-----BEGIN PRIVATE KEY-----\\nMIIE...\\n-----END PRIVATE KEY-----\\n"
client_email = "firebase-adminsdk-xxx@project-id.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
universe_domain = "googleapis.com"
    """, language="toml")

    st.divider()
    st.subheader("Joriy holat")
    checks = {
        "BOT_TOKEN":     bool(st.secrets.get("BOT_TOKEN")),
        "ADMIN_IDS":     bool(st.secrets.get("ADMIN_IDS")),
        "[firebase]":    "firebase" in st.secrets,
        "[firebase_sa]": "firebase_sa" in st.secrets,
    }
    for k, v in checks.items():
        st.write(f"{'✅' if v else '❌'} `{k}`")

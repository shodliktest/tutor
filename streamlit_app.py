"""
🌐 STREAMLIT WEB INTERFEYSI (PRO VERSIYA)
Quiz Bot uchun ilg'or admin paneli, analitika va botni orqa fonda yurgizish mexanizmi.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Bazaviy funksiyalarni import qilish
from firebase.config import initialize_firebase
from firebase.db import (
    get_all_tests, get_all_users, get_global_leaderboard, 
    block_user, delete_test
)
from bot import run_bot_in_background
from config import SUBJECTS

# ══════════════════════════════════════════════════════════
# 1. SAHIFA SOZLAMALARI
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Quiz Bot | Admin Panel",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════
# 2. CACHE QILINGAN ASOSIY FUNKSIYALAR (SINGLETON)
# ══════════════════════════════════════════════════════════
@st.cache_resource
def init_system():
    """Firebase va Botni faqat 1 marta ishga tushirish"""
    # 1. Firebase ulanishi
    initialize_firebase()
    
    # 2. Aiogram 3 botni orqa fonda yurgizish
    bot_thread = run_bot_in_background()
    return bot_thread

# Tizimni ishga tushirish
bot_thread = init_system()


# ══════════════════════════════════════════════════════════
# 3. YORDAMCHI FUNKSIYALAR (MA'LUMOTLARNI TAYYORLASH)
# ══════════════════════════════════════════════════════════
def load_data():
    """Barcha ma'lumotlarni Firebase'dan tortib olish"""
    users = get_all_users()
    tests = get_all_tests()
    leaders = get_global_leaderboard(limit=50)
    return users, tests, leaders


# ══════════════════════════════════════════════════════════
# 4. YON PANEL (SIDEBAR) VA NAVIGATSIYA
# ══════════════════════════════════════════════════════════
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=100)
    st.title("🎓 Quiz Bot Pro")
    
    st.markdown("### 🤖 Bot Holati")
    if bot_thread and bot_thread.is_alive():
        st.success("🟢 Bot faol (Online)")
    else:
        st.error("🔴 Bot to'xtagan")
        
    st.markdown("---")
    menu = st.radio(
        "📋 Menyu",
        ["📊 Bosh Panel (Dashboard)", "👥 Foydalanuvchilar", "📋 Testlar Bazasi", "🏆 Reyting", "⚙️ Sozlamalar (Secrets)"]
    )
    st.markdown("---")
    st.caption("© 2026 Abduvali Quiz LMS")


# ══════════════════════════════════════════════════════════
# 5. ASOSIY SAHIFA MANTIQI
# ══════════════════════════════════════════════════════════
users_data, tests_data, leaders_data = load_data()

# ----------------------------------------------------------
# 📊 BOSH PANEL (DASHBOARD)
# ----------------------------------------------------------
if menu == "📊 Bosh Panel (Dashboard)":
    st.header("📊 Tizimning Umumiy Holati")
    
    # Metrikalar
    col1, col2, col3, col4 = st.columns(4)
    total_users = len(users_data)
    total_tests = len(tests_data)
    
    # Barcha ishlangan testlar sonini hisoblash
    total_solves = sum([t.get("solve_count", 0) for t in tests_data])
    
    # O'rtacha tizim foizini topish
    avg_sys_score = sum([u.get("avg_score", 0) for u in users_data if u.get("total_tests", 0) > 0])
    active_users = len([u for u in users_data if u.get("total_tests", 0) > 0])
    avg_sys_score = (avg_sys_score / active_users) if active_users > 0 else 0

    col1.metric("👥 Jami Foydalanuvchilar", f"{total_users} ta")
    col2.metric("📋 Jami Testlar", f"{total_tests} ta")
    col3.metric("🎯 Ishlangan testlar", f"{total_solves} marta")
    col4.metric("📈 O'rtacha o'zlashtirish", f"{avg_sys_score:.1f}%")

    st.markdown("---")
    
    # Grafiklar
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🗂 Fanlar bo'yicha testlar ulushi")
        if tests_data:
            df_tests = pd.DataFrame(tests_data)
            # Agar 'category' bo'lmasa, default 'Boshqa' ni qo'yamiz
            if 'category' not in df_tests.columns:
                df_tests['category'] = "Boshqa"
                
            fig_pie = px.pie(df_tests, names='category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Hozircha testlar yaratilmagan.")

    with c2:
        st.subheader("🏆 Eng faol 5 ta foydalanuvchi")
        if users_data:
            df_users = pd.DataFrame(users_data)
            df_active = df_users[df_users['total_tests'] > 0].sort_values(by='total_tests', ascending=False).head(5)
            if not df_active.empty:
                fig_bar = px.bar(df_active, x='name', y='total_tests', text='total_tests', color='name')
                fig_bar.update_traces(textposition='outside')
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Hali hech kim test ishlamagan.")
        else:
            st.info("Foydalanuvchilar yo'q.")


# ----------------------------------------------------------
# 👥 FOYDALANUVCHILAR
# ----------------------------------------------------------
elif menu == "👥 Foydalanuvchilar":
    st.header("👥 Tizim Foydalanuvchilari")
    
    if users_data:
        df_users = pd.DataFrame(users_data)
        
        # Kerakli ustunlarni chiroyli nomlash
        display_df = df_users[['telegram_id', 'name', 'username', 'role', 'total_tests', 'avg_score', 'is_blocked']].copy()
        display_df['avg_score'] = display_df['avg_score'].round(1).astype(str) + "%"
        display_df.columns = ['ID', 'Ism', 'Username', 'Rol', 'Yechgan testlari', 'O\'rtacha natija', 'Bloklanganmi?']
        
        # Qidiruv
        search = st.text_input("🔍 ID yoki Ism bo'yicha qidirish:")
        if search:
            display_df = display_df[
                display_df['Ism'].str.contains(search, case=False, na=False) | 
                display_df['ID'].astype(str).str.contains(search)
            ]
            
        st.dataframe(display_df, use_container_width=True)
        
        st.markdown("### 🚫 Foydalanuvchini bloklash / ochish")
        col_b1, col_b2 = st.columns([3, 1])
        with col_b1:
            target_id = st.selectbox("Foydalanuvchini tanlang (ID - Ism):", df_users.apply(lambda row: f"{row['telegram_id']} - {row['name']}", axis=1))
        
        with col_b2:
            st.write("")
            st.write("")
            if st.button("Holatini o'zgartirish (Bloklash/Ochish)", use_container_width=True):
                uid = int(target_id.split(" - ")[0])
                current_status = df_users[df_users['telegram_id'] == uid]['is_blocked'].values[0]
                block_user(uid, not current_status)
                st.success("✅ Holat muvaffaqiyatli o'zgartirildi! Sahifani yangilang.")
                st.rerun()
    else:
        st.warning("Hozircha bazada foydalanuvchilar yo'q.")


# ----------------------------------------------------------
# 📋 TESTLAR BAZASI
# ----------------------------------------------------------
elif menu == "📋 Testlar Bazasi":
    st.header("📋 Yaratilgan Testlar")
    
    if tests_data:
        df_tests = pd.DataFrame(tests_data)
        
        # Vaqtni formatlash va savollar sonini hisoblash
        df_tests['questions_count'] = df_tests['questions'].apply(lambda x: len(x) if isinstance(x, list) else 0)
        df_tests['created_at'] = pd.to_datetime(df_tests['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        display_tests = df_tests[['test_id', 'title', 'category', 'difficulty', 'questions_count', 'solve_count', 'visibility', 'created_at']]
        display_tests.columns = ['Test ID', 'Nomi', 'Fan', 'Qiyinlik', 'Savollar soni', 'Ishlangan', 'Maxfiylik', 'Yaratilgan sana']
        
        st.dataframe(display_tests, use_container_width=True)
        
        st.markdown("### 🗑 Testni butunlay o'chirish")
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            target_test = st.selectbox("O'chirmoqchi bo'lgan testni tanlang:", df_tests.apply(lambda row: f"{row['test_id']} - {row['title']}", axis=1))
            
        with col_t2:
            st.write("")
            st.write("")
            if st.button("🗑 O'chirish (Qaytarib bo'lmaydi)", type="primary", use_container_width=True):
                t_id = target_test.split(" - ")[0]
                delete_test(t_id)
                st.success(f"✅ Test ({t_id}) butunlay o'chirildi! Sahifani yangilang.")
                st.rerun()
    else:
        st.warning("Hozircha bazada testlar yo'q.")


# ----------------------------------------------------------
# 🏆 REYTING
# ----------------------------------------------------------
elif menu == "🏆 Reyting":
    st.header("🏆 Global Reyting (TOP 50)")
    
    if leaders_data:
        df_leaders = pd.DataFrame(leaders_data)
        df_leaders['avg_score'] = df_leaders['avg_score'].round(1).astype(str) + "%"
        
        display_leaders = df_leaders[['name', 'username', 'avg_score', 'total_tests']]
        display_leaders.index += 1 # 1 dan boshlash
        display_leaders.columns = ['Ism', 'Username', 'O\'rtacha Foiz', 'Ishlagan testlari']
        
        st.table(display_leaders)
    else:
        st.info("Reyting shakllanishi uchun foydalanuvchilar kamida 1 ta test ishlagan bo'lishi kerak.")


# ----------------------------------------------------------
# ⚙️ SOZLAMALAR (SECRETS QO'LLANMASI)
# ----------------------------------------------------------
elif menu == "⚙️ Sozlamalar (Secrets)":
    st.header("⚙️ Tizim Sozlamalari va Secrets")
    
    st.info("""
    Streamlit Cloud da loyihani deploy qilayotganda, **Advanced Settings -> Secrets** bo'limiga quyidagi 
    ma'lumotlarni kiritishingiz shart. Bu bot va Firebase ishlashi uchun asosiy qon tomirdir.
    """)
    
    st.code("""
BOT_TOKEN = "SIZNING_TELEGRAM_BOT_TOKENINGIZ"
ADMIN_IDS = "123456789, 987654321"

# Firebase Service Account JSON
# Firebase Console -> Project Settings -> Service accounts -> Generate new private key
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
    - `private_key` dagi yangi qatorlar albatta `\\n` bilan yozilishi kerak (Firebase xato bermasligi uchun).
    - Hech qachon ushbu kodlarni ochiq holda GitHub ga yuklamang! Faqat Streamlit Cloud Secrets ichiga yozing.
    """)

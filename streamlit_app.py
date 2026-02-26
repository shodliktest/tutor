"""
🌐 STREAMLIT WEB INTERFEYSI (PRO SECURE VERSIYA)
Parol bilan himoyalangan va Firebase limitlarini tejovchi Kesh (Cache) tizimiga ega.
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
# 1. SAHIFA SOZLAMALARI (ENG TEPADA BO'LISHI SHART)
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Quiz Bot | Admin Panel",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════
# 2. BOTNI VA BAZANI ISHGA TUSHIRISH (PAROLDAN OLDIN!)
# ══════════════════════════════════════════════════════════
@st.cache_resource
def init_system():
    """Bot va Firebase faqat 1 marta ishga tushadi"""
    initialize_firebase()
    bot_thread = run_bot_in_background()
    return bot_thread

# Dastur ishlashi bilan bot uyg'onadi, parol kiritishni kutib o'tirmaydi
bot_thread = init_system()

@st.cache_data(ttl=300) 
def load_data():
    """Barcha ma'lumotlarni tortish (Keshlangan)"""
    users = get_all_users()
    tests = get_all_tests()
    leaders = get_global_leaderboard(limit=50)
    return users, tests, leaders

# Ma'lumotlarni yuklash (tezkor ishlaydi)
users_data, tests_data, leaders_data = load_data()


# ══════════════════════════════════════════════════════════
# 3. XAVFSIZLIK: LOGIN TIZIMI (ENDI BOTGA XALAL BERMAYDI)
# ══════════════════════════════════════════════════════════
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Tizimga kirish")
    st.write("Bu sahifa faqat administratorlar uchun mo'ljallangan.")
    
    pwd = st.text_input("Parolni kiriting:", type="password")
    
    if st.button("Kirish"):
        correct_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
        
        if pwd == correct_password:
            st.session_state.authenticated = True
            st.rerun() 
        else:
            st.error("❌ Noto'g'ri parol!")
            
    st.stop() # Sayt shu yerda to'xtaydi, lekin tepadagi bot_thread ishlab yotaveradi!

# ======================= BUNDAN UYOG'I FAQAT ADMIN UCHUN =======================

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
    
    if st.button("🚪 Tizimdan chiqish"):
        st.session_state.authenticated = False
        st.rerun()
        
    st.caption("© 2026 Abduvali Quiz LMS")


# ══════════════════════════════════════════════════════════
# 5. ASOSIY SAHIFA MANTIQI
# ══════════════════════════════════════════════════════════

# ----------------------------------------------------------
# 📊 BOSH PANEL (DASHBOARD)
# ----------------------------------------------------------
if menu == "📊 Bosh Panel (Dashboard)":
    st.header("📊 Tizimning Umumiy Holati")
    
    if st.button("🔄 Ma'lumotlarni yangilash"):
        load_data.clear() 
        st.rerun()
        
    col1, col2, col3, col4 = st.columns(4)
    total_users = len(users_data)
    total_tests = len(tests_data)
    total_solves = sum([t.get("solve_count", 0) for t in tests_data])
    
    avg_sys_score = sum([u.get("avg_score", 0) for u in users_data if u.get("total_tests", 0) > 0])
    active_users = len([u for u in users_data if u.get("total_tests", 0) > 0])
    avg_sys_score = (avg_sys_score / active_users) if active_users > 0 else 0

    col1.metric("👥 Foydalanuvchilar", f"{total_users} ta")
    col2.metric("📋 Jami Testlar", f"{total_tests} ta")
    col3.metric("🎯 Ishlangan testlar", f"{total_solves} marta")
    col4.metric("📈 O'rtacha reyting", f"{avg_sys_score:.1f}%")

    st.markdown("---")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🗂 Fanlar bo'yicha testlar")
        if tests_data:
            df_tests = pd.DataFrame(tests_data)
            if 'category' not in df_tests.columns: df_tests['category'] = "Boshqa"
            fig_pie = px.pie(df_tests, names='category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Testlar yo'q.")

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
                st.info("Hali test ishlaganlar yo'q.")
        else:
            st.info("Foydalanuvchilar yo'q.")

# ----------------------------------------------------------
# 👥 FOYDALANUVCHILAR
# ----------------------------------------------------------
elif menu == "👥 Foydalanuvchilar":
    st.header("👥 Tizim Foydalanuvchilari")
    
    if users_data:
        df_users = pd.DataFrame(users_data)
        display_df = df_users[['telegram_id', 'name', 'username', 'role', 'total_tests', 'avg_score', 'is_blocked']].copy()
        display_df['avg_score'] = display_df['avg_score'].round(1).astype(str) + "%"
        display_df.columns = ['ID', 'Ism', 'Username', 'Rol', 'Yechgan testlari', 'O\'rtacha natija', 'Bloklanganmi?']
        
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
            target_id = st.selectbox("Tanlang (ID - Ism):", df_users.apply(lambda row: f"{row['telegram_id']} - {row['name']}", axis=1))
        
        with col_b2:
            st.write(""); st.write("")
            if st.button("Holatini o'zgartirish", use_container_width=True):
                uid = int(target_id.split(" - ")[0])
                current_status = df_users[df_users['telegram_id'] == uid]['is_blocked'].values[0]
                block_user(uid, not current_status)
                load_data.clear() 
                st.success("✅ Muvaffaqiyatli! Sahifa yangilanmoqda...")
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
            st.write(""); st.write("")
            if st.button("🗑 O'chirish", type="primary", use_container_width=True):
                t_id = target_test.split(" - ")[0]
                delete_test(t_id)
                load_data.clear() 
                st.success("✅ Test o'chirildi!")
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
        display_leaders.index += 1
        display_leaders.columns = ['Ism', 'Username', 'O\'rtacha Foiz', 'Ishlagan testlari']
        st.table(display_leaders)
    else:
        st.info("Reyting shakllanishi uchun foydalanuvchilar kamida 1 ta test ishlagan bo'lishi kerak.")

# ----------------------------------------------------------
# ⚙️ SOZLAMALAR (SECRETS QO'LLANMASI)
# ----------------------------------------------------------
elif menu == "⚙️ Sozlamalar (Secrets)":
    st.header("⚙️ Tizim Sozlamalari")
    st.info("Streamlit Cloud dagi Secrets bo'limiga quyidagilarni kiritish esdan chiqmasin.")
    
    st.code("""
BOT_TOKEN = "SIZNING_TELEGRAM_BOT_TOKENINGIZ"
ADMIN_IDS = "123456789, 987654321"

# Saytga kirish uchun parolingiz (o'zingiz xohlagan parolni yozing)
ADMIN_PASSWORD = "meni_maxfiy_parolim"

[firebase_sa]
type = "service_account"
# ... qolgan firebase kalitlari ...
    """, language="toml")
             

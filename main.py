import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# -----------------------------
# Supabase Connection
# -----------------------------
SUPABASE_URL = "https://harcxehngjirskbwvzkz.supabase.co"
SUPABASE_KEY = "sb_publishable_lbq4hT1Fnksa0lhEaeIvbA_eKtjCJwn"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# Page Setup
# -----------------------------
st.set_page_config(page_title="نظام حضور الأنشطة", layout="centered")

# -----------------------------
# CSS Design
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');

* {font-family:'Cairo',sans-serif!important;direction:rtl!important;text-align:right!important;}

.stApp{background-color:#0f172a;color:#f8fafc;}

.header-box{
background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);
padding:2rem;border-radius:20px;border:1px solid #334155;margin-bottom:2rem;text-align:center!important;}

.main-title{
background:linear-gradient(90deg,#38bdf8,#818cf8);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;
font-size:2.6rem;font-weight:900;margin:0;text-align:center!important;}

.stButton>button{
border-radius:12px;background:linear-gradient(90deg,#3b82f6,#2563eb);
color:white;font-weight:bold;width:100%;height:3rem;border:none;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1 class="main-title">نظام حضور الأنشطة</h1></div>', unsafe_allow_html=True)

# -----------------------------
# Fetch Data
# -----------------------------
@st.cache_data(ttl=5)
def fetch_students():
    data = supabase.table("students").select("*").execute()
    return pd.DataFrame(data.data)

@st.cache_data(ttl=5)
def fetch_logs():
    data = supabase.table("attendance").select("*").execute()
    return pd.DataFrame(data.data)

df_students = fetch_students()
df_logs = fetch_logs()

# -----------------------------
# Passwords
# -----------------------------
PASSWORDS = {
"فئة أشبال السالمية":"Salmiya2026",
"فئة أشبال حولي":"Hawally2026",
"فئة الفتية":"Fetya2026",
"فئة الشباب":"Shabab2026",
"فئة الجامعيين":"Uni2026"
}

target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))

tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام","🔐 بوابة المشرف"])

m_list = df_students[df_students['category']==target_cat] if not df_students.empty else pd.DataFrame()
l_list = df_logs[df_logs['category']==target_cat] if not df_logs.empty else pd.DataFrame()

# =============================
# كشف الالتزام
# =============================
with tab_stats:

    if m_list.empty:
        st.info("لا يوجد طلاب")

    else:

        if not l_list.empty:
            l_list['date'] = pd.to_datetime(l_list['date'])

        total_days = l_list['date'].dt.date.nunique() if not l_list.empty else 0

        m_list['أيام الحضور'] = m_list['name'].apply(
            lambda n: l_list[l_list['name']==n]['date'].dt.date.nunique()
            if not l_list.empty else 0
        )

        m_list['النسبة'] = (m_list['أيام الحضور']/total_days*100).round(1).astype(str)+'%' if total_days>0 else "0%"

        st.table(m_list[['name','mosque','grade','أيام الحضور','النسبة']])

# =============================
# Admin Panel
# =============================
with tab_admin:

    pwd = st.text_input("أدخل كلمة المرور", type="password")

    if pwd == PASSWORDS.get(target_cat):

        st.success("تم تسجيل الدخول")

        sub1,sub2,sub3 = st.tabs(["📝 تسجيل الحضور","➕ إدارة الطلاب","📥 التقارير"])

        # -----------------------------
        # تسجيل الحضور
        # -----------------------------
        with sub1:

            attendance_date = st.date_input("تاريخ الحضور", datetime.now())

            selected_students = []

            if not m_list.empty:
                for n in sorted(m_list['name'].unique()):
                    if st.checkbox(n):
                        selected_students.append(n)

            if st.button("اعتماد الحضور"):

                for n in selected_students:

                    supabase.table("attendance").insert({
                        "name": n,
                        "category": target_cat,
                        "date": str(attendance_date)
                    }).execute()

                st.success("تم تسجيل الحضور")

        # -----------------------------
        # إضافة / حذف طالب
        # -----------------------------
        with sub2:

            with st.form("add_student"):

                name_in = st.text_input("الاسم الثلاثي")

                msq_in = st.selectbox("المسجد",[
                "شاهه العبيد","اليوسفين","العسعوسي",
                "السهو","فاطمه الغلوم","الصقعبي",
                "الرشيد","الرومي"
                ])

                lvl_in = st.selectbox("المرحلة الدراسية",[
                "الرابع","الخامس","السادس","السابع",
                "الثامن","التاسع","العاشر",
                "الحادي عشر","الثاني عشر","جامعي"
                ])

                if st.form_submit_button("إضافة الطالب"):

                    supabase.table("students").insert({
                        "name": name_in,
                        "mosque": msq_in,
                        "grade": lvl_in,
                        "category": target_cat
                    }).execute()

                    st.success("تمت إضافة الطالب")

            if not m_list.empty:

                del_n = st.selectbox("اختر الطالب للحذف", m_list['name'])

                if st.button("حذف الطالب"):

                    supabase.table("students").delete().eq("name", del_n).execute()

                    st.success("تم الحذف")

        # -----------------------------
        # التقارير التفصيلية
        # -----------------------------
        with sub3:

            col1,col2 = st.columns(2)

            date_from = col1.date_input("من تاريخ", datetime.now())
            date_to = col2.date_input("إلى تاريخ", datetime.now())

            if st.button("📊 تجهيز التقرير"):

                logs = l_list.copy()

                if not logs.empty:
                    logs['date'] = pd.to_datetime(logs['date'])

                mask = (
                    (logs['date']>=pd.to_datetime(date_from)) &
                    (logs['date']<=pd.to_datetime(date_to))
                ) if not logs.empty else []

                filtered = logs[mask] if not logs.empty else pd.DataFrame()

                days = filtered['date'].dt.date.nunique() if not filtered.empty else 0

                report = []

                for _, s in m_list.iterrows():

                    count = len(filtered[filtered['name']==s['name']])

                    pct = f"{(count/days*100):.1f}%" if days>0 else "0%"

                    report.append({
                        "الاسم": s['name'],
                        "المسجد": s['mosque'],
                        "المرحلة": s['grade'],
                        "أيام الحضور": count,
                        "النسبة": pct
                    })

                res_df = pd.DataFrame(report)

                st.table(res_df)

                csv = res_df.to_csv(index=False).encode('utf-8-sig')

                st.download_button(
                    "📥 تحميل CSV",
                    csv,
                    f"report_{datetime.now().strftime('%Y-%m-%d')}.csv",
                    "text/csv"
                )

import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# -----------------------------
# إعداد الصفحة
# -----------------------------
st.set_page_config(page_title="نظام حضور الأنشطة", layout="centered")

# -----------------------------
# الاتصال بقاعدة البيانات
# -----------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# RTL وتصميم
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; direction: rtl !important; text-align: right !important; }
.stApp { background-color: #0f172a; color: #f8fafc; }
.header-box { background: linear-gradient(135deg,#1e293b 0%,#0f172a 100%); padding:2rem; border-radius:20px; border:1px solid #334155; margin-bottom:2rem; text-align:center !important;}
.main-title { background: linear-gradient(90deg,#38bdf8,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:2.8rem; font-weight:900; margin:0;}
.stButton>button{border-radius:12px;background:linear-gradient(90deg,#3b82f6,#2563eb);color:white;font-weight:bold;width:100%;height:3.5rem;border:none;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1 class="main-title">نظام حضور الأنشطة</h1></div>', unsafe_allow_html=True)

# -----------------------------
# جلب البيانات
# -----------------------------
def fetch_students():

    res = supabase.table("students").select("*").execute()

    if res.data:
        return pd.DataFrame(res.data)

    return pd.DataFrame(columns=["name","mosque","grade","category"])


def fetch_attendance():

    res = supabase.table("attendance").select("*").execute()

    if res.data:
        return pd.DataFrame(res.data)

    return pd.DataFrame(columns=["name","category","date"])


df_students = fetch_students()
df_logs = fetch_attendance()

# -----------------------------
# كلمات المرور
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

# -----------------------------
# تصفية الطلاب
# -----------------------------
m_list = df_students[df_students['category']==target_cat] if not df_students.empty else pd.DataFrame()
l_list = df_logs[df_logs['category']==target_cat] if not df_logs.empty else pd.DataFrame()

# =============================
# كشف الالتزام
# =============================
with tab_stats:

    if m_list.empty:

        st.info("لا توجد طلاب في هذه الفئة.")

    else:

        m_list['name'] = m_list['name'].astype(str).str.strip()

        if not l_list.empty:

            l_list['name'] = l_list['name'].astype(str).str.strip()
            l_list['date'] = pd.to_datetime(l_list['date'],errors='coerce')

        total_days = l_list['date'].dt.date.nunique() if not l_list.empty else 0

        m_list['أيام الحضور'] = m_list['name'].apply(
            lambda n: l_list[l_list['name']==n]['date'].dt.date.nunique() if not l_list.empty else 0
        )

        m_list['النسبة المئوية'] = (
            (m_list['أيام الحضور']/total_days*100).round(1).astype(str)+'%'
            if total_days>0 else '0%'
        )

        st.table(m_list[['name','mosque','grade','أيام الحضور','النسبة المئوية']])

# =============================
# بوابة المشرف
# =============================
with tab_admin:

    pwd = st.text_input("أدخل كلمة المرور:", type="password")

    if pwd == PASSWORDS.get(target_cat):

        st.success("تم تسجيل الدخول ✅")

        sub1, sub2, sub3 = st.tabs([
            "📝 تسجيل الحضور",
            "➕ إدارة الطلاب",
            "📥 التقارير التفصيلية"
        ])

        # -----------------------------
        # تسجيل الحضور
        # -----------------------------
        with sub1:

            if not m_list.empty:

                attendance_date = st.date_input("اختر التاريخ:", datetime.now())

                selected_students = []

                for n in sorted(m_list['name'].unique()):

                    if st.checkbox(n):

                        selected_students.append(n)

                if st.button("✅ اعتماد كشف الحضور"):

                    for n in selected_students:

                        supabase.table("attendance").insert({
                            "name":n,
                            "category":target_cat,
                            "date":str(attendance_date)
                        }).execute()

                    st.success("تم تسجيل الحضور")

        # -----------------------------
        # إدارة الطلاب
        # -----------------------------
        with sub2:

            with st.form(key="add_student"):

                name = st.text_input("الاسم الثلاثي")

                mosque = st.selectbox(
                    "المسجد",
                    ["شاهه العبيد","اليوسفين","العسعوسي","السهو","فاطمه الغلوم","الصقعبي","الرشيد","الرومي"]
                )

                grade = st.selectbox(
                    "المرحلة الدراسية",
                    ["الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر","الحادي عشر","الثاني عشر","جامعي"]
                )

                if st.form_submit_button("إضافة الطالب"):

                    supabase.table("students").insert({
                        "name":name,
                        "mosque":mosque,
                        "grade":grade,
                        "category":target_cat
                    }).execute()

                    st.success("تمت إضافة الطالب")

            if not m_list.empty:

                del_n = st.selectbox("اختر الاسم للحذف:", [""] + sorted(m_list['name'].tolist()))

                if st.button("حذف الطالب") and del_n:

                    supabase.table("students").delete().eq("name",del_n).execute()

                    st.success("تم الحذف")

        # -----------------------------
        # التقارير التفصيلية
        # -----------------------------
        with sub3:

            d1,d2 = st.columns(2)

            date_from = d1.date_input("من تاريخ",datetime.now())
            date_to = d2.date_input("إلى تاريخ",datetime.now())

            if st.button("📊 تجهيز التقرير"):

                all_logs = df_logs.copy()

                all_logs['date'] = pd.to_datetime(all_logs['date'],errors='coerce')

                mask = (
                    (all_logs['date']>=pd.to_datetime(date_from)) &
                    (all_logs['date']<=pd.to_datetime(date_to))
                )

                filtered = all_logs[mask]

                days_in_period = len(filtered['date'].dt.date.unique()) if not filtered.empty else 0

                rep = []

                for _,s in m_list.iterrows():

                    count = len(filtered[filtered['name']==s['name']])

                    pct = f"{(count/days_in_period*100):.1f}%" if days_in_period>0 else "0%"

                    rep.append({
                        "الاسم":s['name'],
                        "المسجد":s['mosque'],
                        "المرحلة":s['grade'],
                        "الحضور":count,
                        "النسبة":pct
                    })

                res_df = pd.DataFrame(rep)

                st.table(res_df)

                csv = res_df.to_csv(index=False).encode('utf-8-sig')

                st.download_button(
                    "📥 تحميل CSV",
                    csv,
                    "attendance_report.csv",
                    "text/csv"
                )

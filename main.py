import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# -------------------------
# إعداد الصفحة
# -------------------------
st.set_page_config(page_title="نظام حضور الأنشطة", layout="centered")

# -------------------------
# الاتصال ب Supabase
# -------------------------
import streamlit as st
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# -------------------------
# تصميم RTL
# -------------------------
st.markdown("""
<style>
* {direction: rtl; text-align: right;}
.stApp {background-color:#0f172a;color:white;}
</style>
""", unsafe_allow_html=True)

st.title("نظام حضور الأنشطة")

# -------------------------
# جلب الطلاب
# -------------------------
def fetch_students():

    res = supabase.table("students").select("*").execute()

    if res.data:
        df = pd.DataFrame(res.data)

        df["name"] = df["name"].astype(str).str.strip()
        df["category"] = df["category"].astype(str).str.strip()

        return df

    return pd.DataFrame(columns=["name","mosque","grade","category"])


# -------------------------
# جلب الحضور
# -------------------------
def fetch_attendance():

    res = supabase.table("attendance").select("*").execute()

    if res.data:
        df = pd.DataFrame(res.data)
        df["name"] = df["name"].astype(str).str.strip()
        return df

    return pd.DataFrame(columns=["name","category","date"])


df_students = fetch_students()
df_logs = fetch_attendance()

# -------------------------
# الفئات وكلمات المرور
# -------------------------
PASSWORDS = {
"فئة أشبال السالمية":"Salmiya2026",
"فئة أشبال حولي":"Hawally2026",
"فئة الفتية":"Fetya2026",
"فئة الشباب":"Shabab2026",
"فئة الجامعيين":"Uni2026"
}

target_cat = st.selectbox("اختر الفئة", list(PASSWORDS.keys()))

# فلترة
m_list = df_students[df_students["category"] == target_cat]
l_list = df_logs[df_logs["category"] == target_cat]

# -------------------------
# التبويبات
# -------------------------
tab_stats, tab_admin, tab_reports = st.tabs([
"كشف الالتزام",
"بوابة المشرف",
"التقارير التفصيلية"
])

# =========================
# كشف الالتزام
# =========================
with tab_stats:

    if m_list.empty:
        st.warning("لا يوجد طلاب في هذه الفئة")

    else:

        l_list["date"] = pd.to_datetime(l_list["date"], errors="coerce")

        total_days = l_list["date"].dt.date.nunique()

        m_list["أيام الحضور"] = m_list["name"].apply(
            lambda n: l_list[l_list["name"]==n]["date"].dt.date.nunique()
        )

        m_list["النسبة"] = (
            (m_list["أيام الحضور"]/total_days*100).round(1).astype(str)+"%"
            if total_days>0 else "0%"
        )

        st.table(m_list[["name","mosque","grade","أيام الحضور","النسبة"]])

# =========================
# بوابة المشرف
# =========================
with tab_admin:

    pwd = st.text_input("كلمة المرور", type="password")

    if pwd == PASSWORDS.get(target_cat):

        st.success("تم تسجيل الدخول")

        sub1, sub2 = st.tabs([
        "تسجيل الحضور",
        "إدارة الطلاب"
        ])

        # -----------------
        # تسجيل الحضور
        # -----------------
        with sub1:

            if not m_list.empty:

                attendance_date = st.date_input("التاريخ", datetime.now())

                selected = []

                for n in sorted(m_list["name"].unique()):

                    if st.checkbox(n):
                        selected.append(n)

                if st.button("اعتماد الحضور"):

                    for n in selected:

                        supabase.table("attendance").insert({
                        "name":n,
                        "category":target_cat,
                        "date":str(attendance_date)
                        }).execute()

                    st.success("تم تسجيل الحضور")

                    st.rerun()

        # -----------------
        # إضافة طالب
        # -----------------
        with sub2:

            name = st.text_input("اسم الطالب")

            mosque = st.selectbox("المسجد",[
            "شاهه العبيد","اليوسفين","العسعوسي","السهو",
            "فاطمه الغلوم","الصقعبي","الرشيد","الرومي"
            ])

            grade = st.selectbox("المرحلة",[
            "الرابع","الخامس","السادس","السابع",
            "الثامن","التاسع","العاشر","الحادي عشر",
            "الثاني عشر","جامعي"
            ])

            if st.button("إضافة الطالب"):

                supabase.table("students").insert({
                "name":name.strip(),
                "mosque":mosque,
                "grade":grade,
                "category":target_cat
                }).execute()

                st.success("تمت إضافة الطالب")

                st.rerun()

# =========================
# التقارير التفصيلية
# =========================
with tab_reports:

    st.subheader("تقرير الحضور")

    d1, d2 = st.columns(2)

    date_from = d1.date_input("من تاريخ", datetime.now())
    date_to = d2.date_input("إلى تاريخ", datetime.now())

    if st.button("تجهيز التقرير"):

        all_logs = df_logs.copy()

        all_logs["date"] = pd.to_datetime(all_logs["date"], errors="coerce")

        mask = (
        (all_logs["date"] >= pd.to_datetime(date_from)) &
        (all_logs["date"] <= pd.to_datetime(date_to))
        )

        filtered = all_logs[mask]

        report = []

        for _, s in m_list.iterrows():

            count = len(filtered[filtered["name"] == s["name"]])

            report.append({
            "الاسم": s["name"],
            "المسجد": s["mosque"],
            "المرحلة": s["grade"],
            "الحضور": count
            })

        res_df = pd.DataFrame(report)

        st.table(res_df)

        csv = res_df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
        "تحميل التقرير CSV",
        csv,
        "attendance_report.csv",
        "text/csv"
        )

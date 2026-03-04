import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# -----------------------------
# إعدادات الصفحة
# -----------------------------
st.set_page_config(page_title="نظام حضور الأنشطة", layout="centered")

# روابط جوجل شيت
API_URL = "https://script.google.com/macros/s/AKfycbyK2LU11Y8PZAEJL3tvzj0XnJVVSnmjvptAXlRcxE4Z57zTLgfRJyi87uPG25Ap8-8DHA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"

READ_M_BASE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_L_BASE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

# -----------------------------
# جلب البيانات
# -----------------------------
@st.cache_data(ttl=3)
def fetch_data():
    try:
        m = pd.read_csv(READ_M_BASE)
        l = pd.read_csv(READ_L_BASE)
        m.columns = m.columns.str.strip()
        l.columns = l.columns.str.strip()
        return m, l
    except:
        return (
            pd.DataFrame(columns=["الاسم","المسجد","المرحلة الدراسية","الفئة"]),
            pd.DataFrame(columns=["الاسم","الفئة","التاريخ"])
        )

df_m, df_l = fetch_data()

PASSWORDS = {
    "فئة أشبال السالمية":"Salmiya2026",
    "فئة أشبال حولي":"Hawally2026",
    "فئة الفتية":"Fetya2026",
    "فئة الشباب":"Shabab2026",
    "فئة الجامعيين":"Uni2026"
}

target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))
tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام والنسب", "🔐 بوابة المشرف"])

m_list = df_m[df_m["الفئة"]==target_cat].copy()
l_list = df_l[df_l["الفئة"]==target_cat].copy()

# تنظيف
if not m_list.empty:
    m_list["الاسم"] = m_list["الاسم"].astype(str).str.strip()
    m_list = m_list.sort_values(by="الاسم", ignore_index=True)

if not l_list.empty:
    l_list["الاسم"] = l_list["الاسم"].astype(str).str.strip()
    l_list["التاريخ"] = pd.to_datetime(l_list["التاريخ"], errors="coerce")

# =============================
# كشف الالتزام
# =============================
with tab_stats:

    if m_list.empty:
        st.info("لا يوجد طلاب في هذه الفئة.")
    else:
        total_days = l_list["التاريخ"].dt.date.nunique() if not l_list.empty else 0

        def count_attendance(name):
            return l_list[l_list["الاسم"]==name]["التاريخ"].dt.date.nunique()

        m_list["أيام الحضور"] = m_list["الاسم"].apply(count_attendance)

        if total_days > 0:
            m_list["النسبة المئوية"] = (
                (m_list["أيام الحضور"]/total_days*100)
                .round(1)
                .astype(str)+"%"
            )
        else:
            m_list["النسبة المئوية"] = "0%"

        st.table(
            m_list[[
                "الاسم",
                "المسجد",
                "المرحلة الدراسية",
                "أيام الحضور",
                "النسبة المئوية"
            ]]
        )

# =============================
# بوابة المشرف
# =============================
with tab_admin:

    pwd = st.text_input("أدخل كلمة المرور:", type="password")

    if pwd == PASSWORDS.get(target_cat):

        st.success("تم تسجيل الدخول بنجاح ✅")

        sub1, sub2, sub3 = st.tabs(
            ["📝 تسجيل الحضور", "➕ إدارة الطلاب", "📥 التقارير التفصيلية"]
        )

        # -------------------------
        # تسجيل الحضور
        # -------------------------
        with sub1:

            if not m_list.empty:

                with st.form("attendance_form", clear_on_submit=True):

                    today = st.date_input("تاريخ اليوم:", datetime.now())

                    selected = []
                    for n in m_list["الاسم"]:
                        if st.checkbox(n, key=f"att_{n}"):
                            selected.append(n)

                    submitted = st.form_submit_button("✅ اعتماد كشف الحضور")

                    if submitted and selected:

                        recs = [
                            {"name":n,"category":target_cat,"date":str(today)}
                            for n in selected
                        ]

                        requests.post(
                            API_URL,
                            json={"action":"add_attendance","records":recs}
                        )

                        st.cache_data.clear()
                        time.sleep(0.2)
                        st.rerun()

                    elif submitted:
                        st.warning("اختر طالب واحد على الأقل.")

            else:
                st.info("لا يوجد طلاب لتسجيل حضورهم.")

        # -------------------------
        # إضافة طالب
        # -------------------------
        with sub2:

            with st.form("add_student_form"):

                name_in = st.text_input("الاسم الثلاثي")

                msq_in = st.selectbox(
                    "المسجد",
                    ["شاهه العبيد","اليوسفين","العسعوسي",
                     "السهو","فاطمه الغلوم","الصقعبي",
                     "الرشيد","الرومي"]
                )

                lvl_in = st.selectbox(
                    "المرحلة الدراسية",
                    ["الرابع","الخامس","السادس","السابع",
                     "الثامن","التاسع","العاشر",
                     "الحادي عشر","الثاني عشر","جامعي"]
                )

                submitted = st.form_submit_button("إضافة الطالب الآن")

                if submitted and name_in:

                    requests.post(
                        API_URL,
                        json={
                            "action":"add_student",
                            "name":name_in,
                            "mosque":msq_in,
                            "grade":lvl_in,
                            "category":target_cat
                        }
                    )

                    st.cache_data.clear()
                    time.sleep(0.2)
                    st.rerun()

            st.divider()

            if not m_list.empty:

                del_name = st.selectbox(
                    "اختر الاسم المراد حذفه:",
                    [""]+m_list["الاسم"].tolist()
                )

                if st.button("تأكيد الحذف النهائي") and del_name:

                    requests.post(
                        API_URL,
                        json={
                            "action":"delete_student",
                            "name":del_name,
                            "category":target_cat
                        }
                    )

                    st.cache_data.clear()
                    time.sleep(0.2)
                    st.rerun()

        # -------------------------
        # التقارير التفصيلية
        # -------------------------
        with sub3:

            d1, d2 = st.columns(2)

            date_from = d1.date_input("من تاريخ", datetime.now())
            date_to = d2.date_input("إلى تاريخ", datetime.now())

            if st.button("📊 تجهيز التقرير التفصيلي"):

                mask = (
                    (l_list["التاريخ"] >= pd.to_datetime(date_from)) &
                    (l_list["التاريخ"] <= pd.to_datetime(date_to))
                )

                filtered = l_list[mask]

                days_in_period = filtered["التاريخ"].dt.date.nunique()

                report = []

                for _, s in m_list.iterrows():

                    count = filtered[
                        filtered["الاسم"]==s["الاسم"]
                    ]["التاريخ"].dt.date.nunique()

                    pct = (
                        f"{(count/days_in_period*100):.1f}%"
                        if days_in_period>0 else "0%"
                    )

                    report.append({
                        "الاسم":s["الاسم"],
                        "المسجد":s["المسجد"],
                        "المرحلة الدراسية":s["المرحلة الدراسية"],
                        "أيام الحضور للفترة":count,
                        "النسبة المئوية":pct
                    })

                res_df = pd.DataFrame(report)

                st.table(res_df)

                csv = res_df.to_csv(index=False).encode("utf-8-sig")

                st.download_button(
                    "📥 تحميل التقرير الشامل",
                    csv,
                    f"تقرير_{datetime.now().strftime('%Y-%m-%d')}.csv",
                    "text/csv"
                )

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام حضور الأنشطة", layout="centered")

# --- ذاكرة فورية ---
if 'local_students' not in st.session_state:
    st.session_state['local_students'] = pd.DataFrame(
        columns=["الاسم", "المسجد", "المرحلة الدراسية", "الفئة"]
    )

# الروابط
API_URL = "https://script.google.com/macros/s/AKfycbxwpiAyguMMZugESiw_QPiNA5t_MWr5YKqYOtwSoS_RfubNovE7QvRkhjmzr03dnIBtIA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
READ_M_BASE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_L_BASE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

# 2. تنسيق RTL
st.markdown("""
<style>
* { direction: rtl; text-align: right; }
.stApp { background-color: #0f172a; color: white; }
.stButton>button { width:100%; height:3rem; border-radius:10px; }
</style>
""", unsafe_allow_html=True)

# 3. جلب البيانات
@st.cache_data(ttl=0)
def fetch_data():
    try:
        nocache = int(time.time())
        m = pd.read_csv(f"{READ_M_BASE}&_={nocache}")
        l = pd.read_csv(f"{READ_L_BASE}&_={nocache}")
        m.columns = [str(c).strip() for c in m.columns]
        l.columns = [str(c).strip() for c in l.columns]
        return m, l
    except:
        return pd.DataFrame(columns=["الاسم","المسجد","المرحلة الدراسية","الفئة"]), \
               pd.DataFrame(columns=["الاسم","الفئة","التاريخ"])

st.title("📊 نظام حضور الأنشطة")

df_m_fetched, df_l = fetch_data()

df_m = pd.concat(
    [df_m_fetched, st.session_state['local_students']]
).drop_duplicates(subset=['الاسم','الفئة'], keep='first')

PASSWORDS = {
    "فئة أشبال السالمية": "Salmiya2026",
    "فئة أشبال حولي": "Hawally2026",
    "فئة الفتية": "Fetya2026",
    "فئة الشباب": "Shabab2026",
    "فئة الجامعيين": "Uni2026"
}

target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))
tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام", "🔐 بوابة المشرف"])

m_list = df_m[df_m['الفئة'] == target_cat] if not df_m.empty else pd.DataFrame()
l_list = df_l[df_l['الفئة'] == target_cat] if not df_l.empty else pd.DataFrame()

# ------------------------
# 📊 كشف الالتزام
# ------------------------
with tab_stats:
    if not m_list.empty:
        total_days = len(l_list["التاريخ"].unique()) if not l_list.empty else 0
        
        st.metric("👥 عدد الطلاب", len(m_list))
        st.metric("📅 أيام النشاط", total_days)

        display_df = m_list.copy()
        display_df['أيام الحضور'] = display_df['الاسم'].apply(
            lambda x: len(l_list[l_list['الاسم'] == x]) if not l_list.empty else 0
        )
        display_df['النسبة'] = display_df['أيام الحضور'].apply(
            lambda x: f"{(x/total_days*100):.1f}%" if total_days>0 else "0%"
        )

        st.dataframe(
            display_df[["الاسم","المسجد","أيام الحضور","النسبة"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("لا توجد بيانات.")

# ------------------------
# 🔐 بوابة المشرف
# ------------------------
with tab_admin:
    pwd = st.text_input("كلمة المرور:", type="password")
    if pwd == PASSWORDS.get(target_cat):

        sub1, sub2 = st.tabs(["📝 تسجيل الحضور", "➕ إدارة الطلاب"])

        # --------------------------------
        # 📝 تسجيل الحضور (نسخة سريعة)
        # --------------------------------
        with sub1:
            if not m_list.empty:
                names = sorted(m_list['الاسم'].unique().tolist())

                with st.form("attendance_form", clear_on_submit=True):

                    today = st.date_input("تاريخ اليوم", datetime.now())

                    # زر تحديد الكل
                    select_all = st.checkbox("تحديد الكل")

                    if select_all:
                        selected = names
                    else:
                        selected = st.multiselect(
                            "اختر الطلاب الحاضرين",
                            options=names,
                            placeholder="ابحث بالاسم..."
                        )

                    submitted = st.form_submit_button("✅ اعتماد الحضور")

                    if submitted:
                        if selected:
                            records = [
                                {"name": n, "category": target_cat, "date": str(today)}
                                for n in selected
                            ]

                            requests.post(
                                API_URL,
                                json={"action": "add_attendance", "records": records}
                            )

                            st.success("تم تسجيل الحضور بنجاح ✅")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("اختر طالب واحد على الأقل")

            else:
                st.warning("لا يوجد طلاب")

        # --------------------------------
        # ➕ إدارة الطلاب
        # --------------------------------
        with sub2:
            with st.form("add_student", clear_on_submit=True):
                name = st.text_input("اسم الطالب")
                mosque = st.text_input("المسجد")
                grade = st.text_input("المرحلة")

                if st.form_submit_button("إضافة"):
                    if name:
                        requests.post(API_URL, json={
                            "action":"add_student",
                            "name":name,
                            "mosque":mosque,
                            "grade":grade,
                            "category":target_cat
                        })

                        new_student = pd.DataFrame([{
                            "الاسم":name,
                            "المسجد":mosque,
                            "المرحلة الدراسية":grade,
                            "الفئة":target_cat
                        }])

                        st.session_state['local_students'] = pd.concat(
                            [st.session_state['local_students'], new_student],
                            ignore_index=True
                        )

                        st.success("تمت الإضافة ✅")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("اكتب الاسم أولاً")

    else:
        if pwd:
            st.error("كلمة المرور غير صحيحة")

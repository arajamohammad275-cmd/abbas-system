import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- 1. إعداد الاتصال السريع بقاعدة البيانات ---
@st.cache_resource
def get_engine():
    db_url = st.secrets["DB_URL"]
    # استخدام نظام الـ Pool لزيادة سرعة الاستجابة
    return create_engine(db_url, pool_pre_ping=True, pool_size=10, max_overflow=20)

engine = get_engine()

def run_query(query, params=None, commit=False):
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        if commit:
            conn.commit()
            return None
        return pd.DataFrame(result.fetchall(), columns=result.keys())

# --- 2. التصميم (Cairo Font & Green Alerts) ---
st.set_page_config(page_title="نظام الحضور السحابي", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; direction: rtl !important; text-align: right !important; }
.stApp { background-color: #0f172a; color: white; }
.header-box { background: linear-gradient(135deg,#1e293b 0%,#0f172a 100%); padding:1.5rem; border-radius:15px; border:1px solid #334155; margin-bottom:1.5rem; text-align:center; }
.main-title { background: linear-gradient(90deg,#38bdf8,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:2.5rem; font-weight:900; }
/* تحسين شكل التنبيه الأخضر */
.stSuccess { background-color: #065f46 !important; color: #ecfdf5 !important; border: 1px solid #10b981; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1 class="main-title">نظام الحضور والالتزام 📊</h1></div>', unsafe_allow_html=True)

# --- 3. الإعدادات ---
PASSWORDS = {
    "فئة أشبال السالمية":"Salmiya2026", "فئة أشبال حولي":"Hawally2026",
    "فئة الفتية":"Fetya2026", "فئة الشباب":"Shabab2026", "فئة الجامعيين":"Uni2026"
}

target_cat = st.selectbox("📂 اختر الفئة لعرض البيانات:", list(PASSWORDS.keys()))
tab_stats, tab_admin = st.tabs(["📊 التقرير المفصل", "🔐 لوحة التحكم"])

# --- 4. التقرير المفصل (الذي طلبته) ---
with tab_stats:
    # جلب بيانات الطلاب والحضور للفئة المختارة
    df_students = run_query("SELECT name, mosque, grade FROM students WHERE category = :cat", {"cat": target_cat})
    df_attendance = run_query("SELECT student_name, date FROM attendance WHERE category = :cat", {"cat": target_cat})
    
    if df_students is None or df_students.empty:
        st.info("لا يوجد طلاب مسجلين في هذه الفئة حالياً.")
    else:
        # حساب إجمالي أيام النشاط (التواريخ الفريدة)
        total_active_days = df_attendance['date'].nunique() if not df_attendance.empty else 0
        
        # بناء التقرير لكل طالب
        report_data = []
        for _, s in df_students.iterrows():
            # حساب أيام حضور هذا الطالب بالتحديد
            s_att_count = len(df_attendance[df_attendance['student_name'] == s['name']]) if not df_attendance.empty else 0
            # حساب النسبة المئوية
            attendance_perc = (s_att_count / total_active_days * 100) if total_active_days > 0 else 0
            
            report_data.append({
                "اسم الطالب": s['name'],
                "المسجد": s['mosque'],
                "المرحلة": s['grade'],
                "أيام الحضور": s_att_count,
                "نسبة الالتزام": f"{attendance_perc:.1f}%"
            })
        
        # عرض الجدول بشكل احترافي
        final_df = pd.DataFrame(report_data)
        st.dataframe(final_df, use_container_width=True, hide_index=True)
        st.caption(f"إجمالي عدد أيام النشاط المسجلة لهذه الفئة: {total_active_days}")

# --- 5. لوحة التحكم ---
with tab_admin:
    pwd = st.text_input("كلمة مرور المشرف:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        t1, t2 = st.tabs(["📝 تسجيل حضور اليوم", "➕ إضافة/حذف طلاب"])
        
        with t1:
            st.subheader("تسجيل الحضور")
            att_date = st.date_input("تاريخ اليوم:", datetime.now())
            with st.form("attendance_form"):
                all_names = sorted(df_students['name'].tolist()) if not df_students.empty else []
                selected_names = []
                for name in all_names:
                    if st.checkbox(name):
                        selected_names.append(name)
                
                if st.form_submit_button("اعتماد الحضور"):
                    for n in selected_names:
                        run_query("INSERT INTO attendance (student_name, category, date) SELECT :n, :c, :d WHERE NOT EXISTS (SELECT 1 FROM attendance WHERE student_name=:n AND date=:d AND category=:c)", 
                                  {"n": n, "c": target_cat, "d": str(att_date)}, commit=True)
                    st.success("✨ تم حفظ الكشف بنجاح!")
                    st.rerun()

        with t2:
            st.subheader("إضافة طالب جديد")
            with st.form("new_student_form", clear_on_submit=True):
                n_name = st.text_input("الاسم الكامل")
                n_mosque = st.selectbox("المسجد", ["شاهه العبيد","اليوسفين","العسعوسي","السهو","فاطمه الغلوم","الصقعبي","الرشيد","الرومي"])
                n_grade = st.selectbox("المرحلة", ["الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر","الحادي عشر","الثاني عشر","جامعي"])
                if st.form_submit_button("إضافة الطالب"):
                    if n_name:
                        run_query("INSERT INTO students (name, mosque, grade, category) VALUES (:n, :m, :g, :c)", 
                                  {"n": n_name, "m": n_mosque, "g": n_grade, "c": target_cat}, commit=True)
                        st.success(f"✅ تم إضافة الطالب ({n_name}) بنجاح!")
                        st.rerun()

            st.divider()
            st.subheader("حذف طالب")
            del_name = st.selectbox("اختر الاسم للحذف:", [""] + (df_students['name'].tolist() if not df_students.empty else []))
            if st.button("🗑️ تأكيد الحذف النهائي"):
                if del_name:
                    run_query("DELETE FROM students WHERE name = :n AND category = :c", {"n": del_name, "c": target_cat}, commit=True)
                    st.warning(f"تم حذف {del_name}")
                    st.rerun()

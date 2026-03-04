import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import io

# --- 1. إعداد محرك الاتصال السريع (فقط لضمان السرعة) ---
@st.cache_resource
def get_engine():
    return create_engine(
        st.secrets["DB_URL"], 
        pool_pre_ping=True, 
        pool_size=20, 
        max_overflow=30
    )

engine = get_engine()

def run_query(query, params=None, fetch=False):
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        if fetch:
            return pd.DataFrame(result.fetchall(), columns=result.keys())
        conn.commit()

# --- 2. واجهة التطبيق (كودك الأصلي الفخم) ---
st.set_page_config(page_title="نظام حضور الأنشطة", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; direction: rtl !important; text-align: right !important; }
.stApp { background-color: #0f172a; color: #f8fafc; }
.header-box { background: linear-gradient(135deg,#1e293b 0%,#0f172a 100%); padding:2rem; border-radius:20px; border:1px solid #334155; margin-bottom:2rem; text-align:center !important;}
.main-title { background: linear-gradient(90deg,#38bdf8,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:2.8rem; font-weight:900; margin:0; text-align:center !important;}
/* الرسالة الخضراء التي طلبتها */
.stSuccess { background-color: #064e3b !important; color: #ecfdf5 !important; border: 1px solid #059669; border-radius:12px; padding: 15px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1 class="main-title">نظام حضور الأنشطة والتقارير ☁️</h1></div>', unsafe_allow_html=True)

# --- 3. الثوابت وقاعدة البيانات ---
PASSWORDS = {
    "فئة أشبال السالمية":"Salmiya2026", "فئة أشبال حولي":"Hawally2026",
    "فئة الفتية":"Fetya2026", "فئة الشباب":"Shabab2026", "فئة الجامعيين":"Uni2026"
}

target_cat = st.sidebar.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))
tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام العام", "🔐 بوابة المشرف"])

# --- 4. التبويب الأول: كشف الالتزام (التقرير الأصلي الكامل) ---
with tab_stats:
    df_m = run_query("SELECT * FROM students WHERE category = :cat", {"cat": target_cat}, fetch=True)
    df_l = run_query("SELECT * FROM attendance WHERE category = :cat", {"cat": target_cat}, fetch=True)
    
    if df_m is not None and not df_m.empty:
        total_days = df_l['date'].nunique() if not df_l.empty else 0
        report = []
        for _, s in df_m.iterrows():
            s_att = len(df_l[df_l['student_name'] == s['name']]) if not df_l.empty else 0
            perc = (s_att / total_days * 100) if total_days > 0 else 0
            report.append({
                "الاسم الكامل": s['name'], "المسجد": s['mosque'], "المرحلة": s['grade'],
                "الحضور": s_att, "نسبة الالتزام": f"{perc:.1f}%"
            })
        st.table(pd.DataFrame(report))
    else:
        st.info("لا يوجد طلاب مسجلين.")

# --- 5. التبويب الثاني: بوابة المشرف (تحتوي على الأقسام الثلاثة بالداخل) ---
with tab_admin:
    pwd = st.text_input("كلمة مرور المشرف:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("🔓 تم الدخول بنجاح، متاح لك كامل الصلاحيات.")
        
        # الأقسام الثلاثة التي طلبتها داخل بوابة المشرف
        s1, s2, s3 = st.tabs(["📝 كشف حضور جديد", "➕ إضافة وحذف الطلاب", "📥 استخراج تقرير Excel"])
        
        with s1:
            st.subheader("تسجيل الحضور اليومي")
            att_date = st.date_input("اختر التاريخ:", datetime.now())
            names = sorted(df_m['name'].tolist()) if not df_m.empty else []
            with st.form("attendance_form"):
                selected = [n for n in names if st.checkbox(n, key=f"att_{n}")]
                if st.form_submit_button("✅ اعتماد كشف الحضور"):
                    for n in selected:
                        run_query("INSERT INTO attendance (student_name, category, date) SELECT :n, :c, :d WHERE NOT EXISTS (SELECT 1 FROM attendance WHERE student_name=:n AND date=:d AND category=:c)", {"n": n, "c": target_cat, "d": str(att_date)})
                    st.success("✨ تم تسجيل الحضور في السحابة بنجاح!")
                    st.rerun()

        with s2:
            st.subheader("إدارة سجلات الطلاب")
            with st.form("add_student_form", clear_on_submit=True):
                n_in = st.text_input("اسم الطالب الجديد:")
                m_in = st.selectbox("المسجد:", ["شاهه العبيد","اليوسفين","العسعوسي","السهو","فاطمه الغلوم","الصقعبي","الرشيد","الرومي"])
                g_in = st.selectbox("المرحلة الدراسية:", ["الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر","الحادي عشر","الثاني عشر","جامعي"])
                if st.form_submit_button("➕ إضافة الطالب"):
                    if n_in:
                        run_query("INSERT INTO students (name, mosque, grade, category) VALUES (:n, :m, :g, :c)", {"n": n_in, "m": m_in, "g": g_in, "c": target_cat})
                        st.success(f"✅ تم إضافة الطالب ({n_in}) بنجاح للمنظومة!")
                        st.rerun()
            
            st.divider()
            df_m_del = run_query("SELECT name FROM students WHERE category = :cat", {"cat": target_cat}, fetch=True)
            del_n = st.selectbox("حذف طالب من السجلات:", [""] + (df_m_del['name'].tolist() if df_m_del is not None else []))
            if st.button("🗑️ حذف نهائي"):
                if del_n:
                    run_query("DELETE FROM students WHERE name = :n AND category = :c", {"n": del_n, "c": target_cat})
                    st.warning(f"تم مسح بيانات {del_n}")
                    st.rerun()

        with s3:
            st.subheader("استخراج تقرير Excel للمشرفين")
            col1, col2 = st.columns(2)
            with col1:
                start_d = st.date_input("من تاريخ:", datetime.now() - timedelta(days=30))
            with col2:
                end_d = st.date_input("إلى تاريخ:", datetime.now())

            if st.button("📊 توليد ملف Excel"):
                df_period = run_query("""
                    SELECT student_name, date FROM attendance 
                    WHERE category = :cat AND date BETWEEN :s AND :e
                """, {"cat": target_cat, "s": str(start_d), "e": str(end_d)}, fetch=True)
                
                if not df_period.empty:
                    # تحويل البيانات لجدول عرضي (Matrix) كما في الصورة التي أرفقتها
                    report_xl = df_period.pivot_table(index='student_name', columns='date', aggfunc=lambda x: '✅', fill_value='❌')
                    
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        report_xl.to_excel(writer, sheet_name='الحضور')
                    
                    st.success("✅ تم تجهيز الملف! يمكنك تحميله الآن.")
                    st.download_button(
                        label="📥 تحميل تقرير Excel الآن",
                        data=output.getvalue(),
                        file_name=f"Report_{target_cat}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.dataframe(report_xl) # عرض معاينة للجدول
                else:
                    st.warning("لا توجد بيانات حضور في الفترة المختارة.")
    elif pwd != "":
        st.error("❌ كلمة المرور غير صحيحة.")

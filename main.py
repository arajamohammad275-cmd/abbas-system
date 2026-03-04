import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import io

# --- 1. محرك السرعة السحابي (Engine) ---
@st.cache_resource
def get_engine():
    return create_engine(
        st.secrets["DB_URL"], 
        pool_pre_ping=True, 
        pool_size=10, 
        max_overflow=20
    )

engine = get_engine()

def run_query(query, params=None, fetch=False):
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        if fetch:
            return pd.DataFrame(result.fetchall(), columns=result.keys())
        conn.commit()

# --- 2. التنسيق الجمالي (الأصلي) ---
st.set_page_config(page_title="نظام حضور الأنشطة المتكامل", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; direction: rtl !important; text-align: right !important; }
.stApp { background-color: #0f172a; color: #f8fafc; }
.header-box { background: linear-gradient(135deg,#1e293b 0%,#0f172a 100%); padding:2rem; border-radius:20px; border:1px solid #334155; margin-bottom:2rem; text-align:center !important;}
.main-title { background: linear-gradient(90deg,#38bdf8,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:2.8rem; font-weight:900; margin:0; text-align:center !important;}
.stSuccess { background-color: #064e3b !important; color: #ecfdf5 !important; border: 1px solid #059669; border-radius:12px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1 class="main-title">نظام الحضور والتقارير الذكي ☁️</h1></div>', unsafe_allow_html=True)

# --- 3. البيانات الأساسية ---
PASSWORDS = {
    "فئة أشبال السالمية":"Salmiya2026", "فئة أشبال حولي":"Hawally2026",
    "فئة الفتية":"Fetya2026", "فئة الشباب":"Shabab2026", "فئة الجامعيين":"Uni2026"
}

target_cat = st.sidebar.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))
tab_stats, tab_export, tab_admin = st.tabs(["📊 كشف الالتزام", "📥 استخراج التقارير (Excel)", "🔐 بوابة المشرف"])

# --- 4. التبويب الأول: كشف الالتزام الحالي ---
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
                "الاسم": s['name'], "المسجد": s['mosque'], "المرحلة": s['grade'],
                "أيام الحضور": s_att, "النسبة": f"{perc:.1f}%"
            })
        st.table(pd.DataFrame(report))
    else:
        st.info("لا يوجد طلاب مسجلين.")

# --- 5. التبويب الثاني: استخراج التقارير (القسم الثالث الذي سألت عنه) ---
with tab_export:
    st.subheader("تحديد فترة التقرير")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("من تاريخ:", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("إلى تاريخ:", datetime.now())

    if st.button("توليد تقرير الفترة"):
        # جلب الحضور في هذه الفترة فقط
        df_period = run_query("""
            SELECT student_name, date FROM attendance 
            WHERE category = :cat AND date BETWEEN :s AND :e
        """, {"cat": target_cat, "s": str(start_date), "e": str(end_date)}, fetch=True)
        
        if not df_period.empty:
            # تحويل البيانات لشكل جدول Excel (Matrix)
            report_xl = df_period.pivot_table(index='student_name', columns='date', aggfunc=lambda x: '✅', fill_value='❌')
            
            # تحويله لملف Excel في الذاكرة
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                report_xl.to_excel(writer, sheet_name='تقرير الحضور')
            
            st.success("✅ تم تجهيز التقرير بنجاح!")
            st.download_button(
                label="📥 تحميل التقرير بصيغة Excel",
                data=output.getvalue(),
                file_name=f"تقرير_حضور_{target_cat}_{start_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.dataframe(report_xl)
        else:
            st.warning("لا توجد سجلات حضور في هذه الفترة.")

# --- 6. التبويب الثالث: بوابة المشرف ---
with tab_admin:
    pwd = st.text_input("كلمة المرور:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        s1, s2 = st.tabs(["📝 تسجيل حضور", "➕ إدارة الطلاب"])
        with s1:
            # كود تسجيل الحضور (كما كان عندك)
            att_date = st.date_input("التاريخ:", datetime.now())
            names = sorted(df_m['name'].tolist()) if not df_m.empty else []
            with st.form("att_f"):
                selected = [n for n in names if st.checkbox(n)]
                if st.form_submit_button("اعتماد"):
                    for n in selected:
                        run_query("INSERT INTO attendance (student_name, category, date) SELECT :n, :c, :d WHERE NOT EXISTS (SELECT 1 FROM attendance WHERE student_name=:n AND date=:d AND category=:c)", {"n": n, "c": target_cat, "d": str(att_date)})
                    st.success("✨ تم الحفظ بنجاح!")
                    st.rerun()
        with s2:
            # كود إضافة الطلاب مع الرسالة الخضراء
            with st.form("add_f", clear_on_submit=True):
                n_in = st.text_input("اسم الطالب:")
                m_in = st.selectbox("المسجد:", ["شاهه العبيد","اليوسفين","العسعوسي","السهو","فاطمه الغلوم","الصقعبي","الرشيد","الرومي"])
                g_in = st.selectbox("المرحلة:", ["الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر","الحادي عشر","الثاني عشر","جامعي"])
                if st.form_submit_button("إضافة الطالب"):
                    if n_in:
                        run_query("INSERT INTO students (name, mosque, grade, category) VALUES (:n, :m, :g, :c)", {"n": n_in, "m": m_in, "g": g_in, "c": target_cat})
                        st.success(f"✅ تم إضافة الطالب ({n_in}) بنجاح!")
                        st.rerun()

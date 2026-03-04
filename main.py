import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import io

# --- 1. إعداد الاتصال ---
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DB_URL"], pool_pre_ping=True)

engine = get_engine()

def run_query(query, params=None, fetch=False):
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        if fetch:
            return pd.DataFrame(result.fetchall(), columns=result.keys())
        conn.commit()

# --- 2. إصلاح التصميم (حذف الشرطة وتحسين الواجهة) ---
st.set_page_config(page_title="نظام الحضور", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; direction: rtl !important; text-align: right !important; }
.stApp { background-color: #0f172a; color: white; }
.header-box { background: linear-gradient(135deg,#1e293b 0%,#0f172a 100%); padding:2rem; border-radius:20px; border:1px solid #334155; margin-bottom:2rem; text-align:center; }
.main-title { background: linear-gradient(90deg,#38bdf8,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:2.8rem; font-weight:900; }

/* إصلاح مشكلة الشرطة والخطوط المتداخلة في الـ Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: none !important; }
.stTabs [data-baseweb="tab"] { 
    background-color: #1e293b !important; 
    border-radius: 10px 10px 0 0 !important; 
    padding: 10px 20px !important;
    border: none !important;
}
.stTabs [data-baseweb="tab-panel"] { border: none !important; padding-top: 20px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1 class="main-title">نظام الحضور والتقارير 📊</h1></div>', unsafe_allow_html=True)

# --- 3. المنطق الأساسي ---
PASSWORDS = {
    "فئة أشبال السالمية":"Salmiya2026", "فئة أشبال حولي":"Hawally2026",
    "فئة الفتية":"Fetya2026", "فئة الشباب":"Shabab2026", "فئة الجامعيين":"Uni2026"
}

target_cat = st.sidebar.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))
tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام العام", "🔐 بوابة المشرف"])

# جلب البيانات الأساسية
df_m = run_query("SELECT * FROM students WHERE category = :cat", {"cat": target_cat}, fetch=True)
df_l = run_query("SELECT * FROM attendance WHERE category = :cat", {"cat": target_cat}, fetch=True)

with tab_stats:
    if df_m is not None and not df_m.empty:
        total_days = df_l['date'].nunique() if not df_l.empty else 0
        report = []
        for _, s in df_m.iterrows():
            s_att = len(df_l[df_l['student_name'] == s['name']]) if not df_l.empty else 0
            perc = (s_att / total_days * 100) if total_days > 0 else 0
            report.append({
                "الاسم الكامل": s['name'], "المسجد": s['mosque'], "المرحلة": s['grade'],
                "الحضور": s_att, "النسبة": f"{perc:.1f}%"
            })
        st.table(pd.DataFrame(report))
    else:
        st.info("لا يوجد طلاب مسجلين.")

with tab_admin:
    pwd = st.text_input("كلمة المرور:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("🔓 تم الدخول")
        s1, s2, s3 = st.tabs(["📝 تسجيل حضور", "➕ إدارة الطلاب", "📥 تقارير Excel"])
        
        with s1:
            att_date = st.date_input("التاريخ:", datetime.now())
            names = sorted(df_m['name'].tolist()) if not df_m.empty else []
            with st.form("att_f"):
                selected = [n for n in names if st.checkbox(n)]
                if st.form_submit_button("اعتماد"):
                    for n in selected:
                        run_query("INSERT INTO attendance (student_name, category, date) SELECT :n, :c, :d WHERE NOT EXISTS (SELECT 1 FROM attendance WHERE student_name=:n AND date=:d AND category=:c)", {"n": n, "c": target_cat, "d": str(att_date)})
                    st.success("✨ تم التسجيل!")
                    st.rerun()

        with s2:
            with st.form("add_f", clear_on_submit=True):
                n_in = st.text_input("الاسم:")
                m_in = st.selectbox("المسجد:", ["شاهه العبيد","اليوسفين","العسعوسي","السهو","فاطمة الغلوم","الصقعبي","الرشيد","الرومي"])
                g_in = st.selectbox("المرحلة:", ["الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر","الحادي عشر","الثاني عشر","جامعي"])
                if st.form_submit_button("إضافة"):
                    if n_in:
                        run_query("INSERT INTO students (name, mosque, grade, category) VALUES (:n, :m, :g, :c)", {"n": n_in, "m": m_in, "g": g_in, "c": target_cat})
                        st.success("✅ تمت الإضافة")
                        st.rerun()

        with s3:
            st.subheader("تحميل تقرير إكسل")
            col1, col2 = st.columns(2)
            with col1: start_d = st.date_input("من:", datetime.now() - timedelta(days=30))
            with col2: end_d = st.date_input("إلى:", datetime.now())

            if st.button("توليد ملف Excel"):
                df_p = run_query("SELECT student_name, date FROM attendance WHERE category = :cat AND date BETWEEN :s AND :e", {"cat": target_cat, "s": str(start_d), "e": str(end_d)}, fetch=True)
                if not df_p.empty:
                    report_xl = df_p.pivot_table(index='student_name', columns='date', aggfunc=lambda x: '✅', fill_value='❌')
                    
                    # --- إصلاح ملف الإكسل (توسيع الأعمدة تلقائياً) ---
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        report_xl.to_excel(writer, sheet_name='التقرير')
                        workbook = writer.book
                        worksheet = writer.sheets['التقرير']
                        
                        # كود برمجي لتوسيع الأعمدة بناءً على طول الأسماء
                        for i, col in enumerate(report_xl.columns):
                            column_len = max(report_xl[col].astype(str).map(len).max(), len(str(col))) + 5
                            worksheet.set_column(i + 1, i + 1, column_len)
                        # توسيع عمود الأسماء (العمود الأول)
                        worksheet.set_column(0, 0, 30)
                        
                    st.success("✅ تم تجهيز الملف!")
                    st.download_button(label="📥 تحميل الآن", data=output.getvalue(), file_name=f"Report_{target_cat}.xlsx")
                else:
                    st.warning("لا توجد بيانات.")

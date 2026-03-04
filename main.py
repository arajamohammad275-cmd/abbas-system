import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import io

# --- 1. الاتصال بقاعدة البيانات ---
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

# --- 2. التصميم وإخفاء الخطوط المزعجة ---
st.set_page_config(page_title="نظام الحضور", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; direction: rtl !important; text-align: right !important; }
.stApp { background-color: #0f172a; color: white; }
.header-box { background: linear-gradient(135deg,#1e293b 0%,#0f172a 100%); padding:1.5rem; border-radius:20px; border:1px solid #334155; margin-bottom:2rem; text-align:center; }
.main-title { background: linear-gradient(90deg,#38bdf8,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:2.5rem; font-weight:900; }

/* إزالة الخطوط والشرطات بين التبويبات */
.stTabs [data-baseweb="tab-list"] { border-bottom: none !important; gap: 10px; }
.stTabs [data-baseweb="tab"] { background-color: #1e293b !important; border-radius: 8px 8px 0 0 !important; border: none !important; color: white !important; }
.stTabs [data-baseweb="tab-panel"] { border: none !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1 class="main-title">نظام الحضور والتقارير الذكي 📊</h1></div>', unsafe_allow_html=True)

# --- 3. المنطق الأساسي ---
PASSWORDS = {
    "فئة أشبال السالمية":"Salmiya2026", "فئة أشبال حولي":"Hawally2026",
    "فئة الفتية":"Fetya2026", "فئة الشباب":"Shabab2026", "فئة الجامعيين":"Uni2026"
}

target_cat = st.sidebar.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))
tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام العام", "🔐 بوابة المشرف"])

# جلب البيانات
df_m = run_query("SELECT * FROM students WHERE category = :cat", {"cat": target_cat}, fetch=True)
df_l = run_query("SELECT * FROM attendance WHERE category = :cat", {"cat": target_cat}, fetch=True)

# بناء تقرير الالتزام (الذي تريده في الإكسل)
def build_detailed_report(students, logs):
    if students is None or students.empty: return pd.DataFrame()
    total_days = logs['date'].nunique() if logs is not None and not logs.empty else 0
    report_list = []
    for _, s in students.iterrows():
        s_att = len(logs[logs['student_name'] == s['name']]) if logs is not None and not logs.empty else 0
        perc = (s_att / total_days * 100) if total_days > 0 else 0
        report_list.append({
            "الاسم الكامل": s['name'],
            "المسجد": s['mosque'],
            "المرحلة": s['grade'],
            "أيام الحضور": s_att,
            "النسبة": f"{perc:.1f}%"
        })
    return pd.DataFrame(report_list)

detailed_df = build_detailed_report(df_m, df_l)

with tab_stats:
    if not detailed_df.empty:
        st.table(detailed_df)
    else:
        st.info("لا يوجد طلاب مسجلين.")

with tab_admin:
    pwd = st.text_input("كلمة مرور المشرف:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("🔓 تم الدخول بنجاح")
        s1, s2, s3 = st.tabs(["📝 تسجيل حضور", "➕ إدارة الطلاب", "📥 تقارير Excel"])
        
        with s1:
            att_date = st.date_input("تاريخ اليوم:", datetime.now())
            names = sorted(df_m['name'].tolist()) if not df_m.empty else []
            with st.form("att_form"):
                selected = [n for n in names if st.checkbox(n)]
                if st.form_submit_button("اعتماد"):
                    for n in selected:
                        run_query("INSERT INTO attendance (student_name, category, date) SELECT :n, :c, :d WHERE NOT EXISTS (SELECT 1 FROM attendance WHERE student_name=:n AND date=:d AND category=:c)", {"n": n, "c": target_cat, "d": str(att_date)})
                    st.success("✨ تم التسجيل!")
                    st.rerun()

        with s2:
            with st.form("add_form", clear_on_submit=True):
                n_in = st.text_input("اسم الطالب:")
                m_in = st.selectbox("المسجد:", ["شاهه العبيد","اليوسفين","العسعوسي","السهو","فاطمة الغلوم","الصقعبي","الرومي"])
                g_in = st.selectbox("المرحلة:", ["الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر","الحادي عشر","الثاني عشر","جامعي"])
                if st.form_submit_button("إضافة الطالب"):
                    if n_in:
                        run_query("INSERT INTO students (name, mosque, grade, category) VALUES (:n, :m, :g, :c)", {"n": n_in, "m": m_in, "g": g_in, "c": target_cat})
                        st.success("✅ تمت الإضافة")
                        st.rerun()

        with s3:
            st.subheader("تحميل التقرير التفصيلي (Excel)")
            if not detailed_df.empty:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # تصدير الجدول بنفس الأعمدة التي طلبتها
                    detailed_df.to_excel(writer, sheet_name='تقرير الالتزام', index=False)
                    
                    workbook = writer.book
                    worksheet = writer.sheets['تقرير الالتزام']
                    
                    # تنسيق العناوين والأعمدة (Auto-fit)
                    header_format = workbook.add_format({'bold': True, 'bg_color': '#38bdf8', 'border': 1, 'align': 'center'})
                    for col_num, value in enumerate(detailed_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                        # توسيع تلقائي
                        column_len = max(detailed_df[value].astype(str).map(len).max(), len(value)) + 5
                        worksheet.set_column(col_num, col_num, column_len)
                
                st.write("اضغط على الزر أدناه لتحميل الجدول الكامل بصيغة إكسل:")
                st.download_button(
                    label="📥 تحميل تقرير Excel الآن",
                    data=output.getvalue(),
                    file_name=f"Detailed_Report_{target_cat}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.dataframe(detailed_df) # عرض معاينة لما سيتم تحميله
            else:
                st.warning("لا توجد بيانات لتصديرها.")

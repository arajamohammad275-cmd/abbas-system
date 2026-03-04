import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# 1. الاتصال بقاعدة البيانات السحابية
# يقوم بجلب الرابط من الـ Secrets التي وضعتها تواً
db_url = st.secrets["DB_URL"]
engine = create_engine(db_url)

def run_query(query, params=None, fetch=False):
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        conn.commit()
        if fetch:
            return pd.DataFrame(result.fetchall(), columns=result.keys())

# إنشاء الجداول تلقائياً في Supabase عند أول تشغيل
run_query('''
    CREATE TABLE IF NOT EXISTS students (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        mosque TEXT,
        grade TEXT,
        category TEXT
    )
''')
run_query('''
    CREATE TABLE IF NOT EXISTS attendance (
        id SERIAL PRIMARY KEY,
        student_name TEXT,
        category TEXT,
        date TEXT
    )
''')

# -----------------------------
# التصميم والواجهة (نفس كودك السابق مع تعديلات الربط)
# -----------------------------
st.set_page_config(page_title="نظام حضور الأنشطة السحابي", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; direction: rtl !important; text-align: right !important; }
.stApp { background-color: #0f172a; color: #f8fafc; }
.header-box { background: linear-gradient(135deg,#1e293b 0%,#0f172a 100%); padding:2rem; border-radius:20px; border:1px solid #334155; margin-bottom:2rem; text-align:center !important;}
.main-title { background: linear-gradient(90deg,#38bdf8,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:2.8rem; font-weight:900; margin:0; text-align:center !important;}
.stButton>button{border-radius:12px;background:linear-gradient(90deg,#3b82f6,#2563eb);color:white;font-weight:bold;width:100%;height:3.5rem;border:none;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1 class="main-title">نظام حضور الأنشطة ☁️</h1></div>', unsafe_allow_html=True)

PASSWORDS = {
    "فئة أشبال السالمية":"Salmiya2026",
    "فئة أشبال حولي":"Hawally2026",
    "فئة الفتية":"Fetya2026",
    "فئة الشباب":"Shabab2026",
    "فئة الجامعيين":"Uni2026"
}

target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))
tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام", "🔐 بوابة المشرف"])

# --- تبويب الإحصائيات ---
with tab_stats:
    df_m = run_query("SELECT * FROM students WHERE category = :cat", {"cat": target_cat}, fetch=True)
    df_l = run_query("SELECT * FROM attendance WHERE category = :cat", {"cat": target_cat}, fetch=True)
    
    if df_m is None or df_m.empty:
        st.info("لا يوجد طلاب مسجلين حالياً.")
    else:
        total_days = df_l['date'].nunique() if not df_l.empty else 0
        report = []
        for _, student in df_m.iterrows():
            days_attended = len(df_l[df_l['student_name'] == student['name']]['date'].unique()) if not df_l.empty else 0
            perc = f"{(days_attended/total_days*100):.1f}%" if total_days > 0 else "0%"
            report.append({
                "الاسم": student['name'], "المسجد": student['mosque'], 
                "المرحلة": student['grade'], "الحضور": days_attended, "النسبة": perc
            })
        st.table(pd.DataFrame(report))

# --- تبويب المشرف ---
with tab_admin:
    pwd = st.text_input("كلمة المرور:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        sub1, sub2 = st.tabs(["📝 تسجيل الحضور", "➕ إدارة الطلاب"])

        with sub1:
            df_m = run_query("SELECT name FROM students WHERE category = :cat", {"cat": target_cat}, fetch=True)
            if df_m is not None and not df_m.empty:
                att_date = st.date_input("التاريخ:", datetime.now())
                with st.form("att_form"):
                    selected = []
                    names = sorted(df_m['name'].tolist())
                    for n in names:
                        if st.checkbox(n, key=f"att_{n}"):
                            selected.append(n)
                    
                    if st.form_submit_button("اعتماد"):
                        for name in selected:
                            run_query("INSERT INTO attendance (student_name, category, date) SELECT :n, :c, :d WHERE NOT EXISTS (SELECT 1 FROM attendance WHERE student_name=:n AND date=:d AND category=:c)", 
                                      {"n": name, "c": target_cat, "d": str(att_date)})
                        st.success("تم الحفظ بنجاح!")
                        st.rerun()

        with sub2:
            with st.form("add_student", clear_on_submit=True):
                n_in = st.text_input("الاسم")
                m_in = st.selectbox("المسجد", ["شاهه العبيد","اليوسفين","العسعوسي","السهو","فاطمه الغلوم","الصقعبي","الرشيد","الرومي"])
                g_in = st.selectbox("المرحلة", ["الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر","الحادي عشر","الثاني عشر","جامعي"])
                if st.form_submit_button("إضافة"):
                    if n_in:
                        run_query("INSERT INTO students (name, mosque, grade, category) VALUES (:n, :m, :g, :c)", 
                                  {"n": n_in, "m": m_in, "g": g_in, "c": target_cat})
                        st.success(f"تمت إضافة {n_in}")
                        st.rerun()
            
            st.divider()
            df_m_del = run_query("SELECT name FROM students WHERE category = :cat", {"cat": target_cat}, fetch=True)
            del_n = st.selectbox("حذف طالب:", [""] + (df_m_del['name'].tolist() if df_m_del is not None else []))
            if st.button("حذف نهائي"):
                if del_n:
                    run_query("DELETE FROM students WHERE name = :n AND category = :c", {"n": del_n, "c": target_cat})
                    run_query("DELETE FROM attendance WHERE student_name = :n AND category = :c", {"n": del_n, "c": target_cat})
                    st.warning(f"تم حذف {del_n}")
                    st.rerun()

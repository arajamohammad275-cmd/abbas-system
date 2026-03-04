import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- 1. إعداد الاتصال بقاعدة البيانات السحابية ---
# تأكد أنك وضعت الرابط في Secrets باسم DB_URL
try:
    db_url = st.secrets["DB_URL"]
    # استخدام pool_pre_ping للتأكد من أن الاتصال حي دائماً
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=3600)
except Exception as e:
    st.error("خطأ في الاتصال بقاعدة البيانات. تأكد من إعداد Secrets بشكل صحيح.")
    st.stop()

def run_query(query, params=None, fetch=False):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            conn.commit()
            if fetch:
                return pd.DataFrame(result.fetchall(), columns=result.keys())
    except Exception as e:
        st.error(f"حدث خطأ أثناء تنفيذ العملية: {e}")
        return None

# --- 2. إنشاء الجداول تلقائياً إذا كانت غير موجودة ---
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

# --- 3. إعدادات الواجهة والتصميم ---
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

# --- 4. الثوابت ---
PASSWORDS = {
    "فئة أشبال السالمية":"Salmiya2026",
    "فئة أشبال حولي":"Hawally2026",
    "فئة الفتية":"Fetya2026",
    "فئة الشباب":"Shabab2026",
    "فئة الجامعيين":"Uni2026"
}

target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))
tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام", "🔐 بوابة المشرف"])

# --- 5. تبويب كشف الالتزام (العام) ---
with tab_stats:
    df_m = run_query("SELECT * FROM students WHERE category = :cat", {"cat": target_cat}, fetch=True)
    df_l = run_query("SELECT * FROM attendance WHERE category = :cat", {"cat": target_cat}, fetch=True)
    
    if df_m is None or df_m.empty:
        st.info("لا يوجد طلاب مسجلين حالياً في هذه الفئة.")
    else:
        total_days = df_l['date'].nunique() if (df_l is not None and not df_l.empty) else 0
        report = []
        for _, student in df_m.iterrows():
            days_attended = len(df_l[df_l['student_name'] == student['name']]['date'].unique()) if (df_l is not None and not df_l.empty) else 0
            perc = f"{(days_attended/total_days*100):.1f}%" if total_days > 0 else "0%"
            report.append({
                "الاسم": student['name'], "المسجد": student['mosque'], 
                "المرحلة": student['grade'], "الحضور": days_attended, "النسبة": perc
            })
        st.table(pd.DataFrame(report))

# --- 6. بوابة المشرف ---
with tab_admin:
    pwd = st.text_input("أدخل كلمة المرور الخاصة بالفئة:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("تم الدخول بنجاح")
        sub1, sub2 = st.tabs(["📝 تسجيل الحضور", "➕ إدارة الطلاب"])

        with sub1:
            df_m_att = run_query("SELECT name FROM students WHERE category = :cat", {"cat": target_cat}, fetch=True)
            if df_m_att is not None and not df_m_att.empty:
                att_date = st.date_input("اختر التاريخ:", datetime.now())
                with st.form("att_form"):
                    st.write("حدد الطلاب الحاضرين:")
                    selected = []
                    names = sorted(df_m_att['name'].tolist())
                    for n in names:
                        if st.checkbox(n, key=f"att_{n}"):
                            selected.append(n)
                    
                    if st.form_submit_button("✅ اعتماد كشف الحضور"):
                        if selected:
                            for name in selected:
                                # منع التكرار في نفس اليوم
                                run_query("""
                                    INSERT INTO attendance (student_name, category, date) 
                                    SELECT :n, :c, :d 
                                    WHERE NOT EXISTS (
                                        SELECT 1 FROM attendance WHERE student_name=:n AND date=:d AND category=:c
                                    )""", {"n": name, "c": target_cat, "d": str(att_date)})
                            st.success(f"تم تسجيل حضور {len(selected)} طالب بنجاح!")
                            st.rerun()
                        else:
                            st.warning("يرجى اختيار طالب واحد على الأقل.")
            else:
                st.warning("قائمة الطلاب فارغة، أضف طلاباً أولاً.")

        with sub2:
            with st.form("add_student", clear_on_submit=True):
                st.subheader("إضافة طالب جديد")
                n_in = st.text_input("الاسم الثلاثي")
                m_in = st.selectbox("المسجد", ["شاهه العبيد","اليوسفين","العسعوسي","السهو","فاطمه الغلوم","الصقعبي","الرشيد","الرومي"])
                g_in = st.selectbox("المرحلة", ["الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر","الحادي عشر","الثاني عشر","جامعي"])
                if st.form_submit_button("إضافة الطالب"):
                    if n_in:
                        run_query("INSERT INTO students (name, mosque, grade, category) VALUES (:n, :m, :g, :c)", 
                                  {"n": n_in, "m": m_in, "g": g_in, "c": target_cat})
                        st.success(f"تمت إضافة {n_in} بنجاح")
                        st.rerun()
            
            st.divider()
            st.subheader("حذف طالب")
            df_m_del = run_query("SELECT name FROM students WHERE category = :cat", {"cat": target_cat}, fetch=True)
            del_n = st.selectbox("اختر الطالب المراد حذفه نهائياً:", [""] + (df_m_del['name'].tolist() if df_m_del is not None else []))
            if st.button("🗑️ حذف نهائي"):
                if del_n:
                    run_query("DELETE FROM students WHERE name = :n AND category = :c", {"n": del_n, "c": target_cat})
                    run_query("DELETE FROM attendance WHERE student_name = :n AND category = :c", {"n": del_n, "c": target_cat})
                    st.warning(f"تم حذف {del_n} وكافة بياناته.")
                    st.rerun()

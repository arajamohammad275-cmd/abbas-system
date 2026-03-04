import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- 1. إعداد الاتصال السريع (Engine) ---
@st.cache_resource
def get_engine():
    # الرابط الذي وضعته في Secrets
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

# --- 2. التصميم الفخم (الأصلي) ---
st.set_page_config(page_title="نظام حضور الأنشطة", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; direction: rtl !important; text-align: right !important; }
.stApp { background-color: #0f172a; color: #f8fafc; }
.header-box { background: linear-gradient(135deg,#1e293b 0%,#0f172a 100%); padding:2rem; border-radius:20px; border:1px solid #334155; margin-bottom:2rem; text-align:center !important;}
.main-title { background: linear-gradient(90deg,#38bdf8,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:2.8rem; font-weight:900; margin:0; text-align:center !important;}
.stButton>button{border-radius:12px;background:linear-gradient(90deg,#3b82f6,#2563eb);color:white;font-weight:bold;width:100%;height:3.5rem;border:none;}
/* الرسالة الخضراء الاحترافية */
.stSuccess { background-color: #064e3b !important; color: #ecfdf5 !important; border: 1px solid #059669; border-radius:12px; padding: 15px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1 class="main-title">نظام حضور الأنشطة ☁️</h1></div>', unsafe_allow_html=True)

# --- 3. الثوابت وإعداد الجداول ---
PASSWORDS = {
    "فئة أشبال السالمية":"Salmiya2026",
    "فئة أشبال حولي":"Hawally2026",
    "فئة الفتية":"Fetya2026",
    "فئة الشباب":"Shabab2026",
    "فئة الجامعيين":"Uni2026"
}

# إنشاء الجداول عند أول تشغيل
run_query('''
    CREATE TABLE IF NOT EXISTS students (id SERIAL PRIMARY KEY, name TEXT, mosque TEXT, grade TEXT, category TEXT);
    CREATE TABLE IF NOT EXISTS attendance (id SERIAL PRIMARY KEY, student_name TEXT, category TEXT, date TEXT);
''')

target_cat = st.selectbox("📂 اختر الفئة المطلوبة:", list(PASSWORDS.keys()))
tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام والتقارير", "🔐 بوابة المشرفين"])

# --- 4. تبويب التقارير (الكود الطويل والمفصل) ---
with tab_stats:
    df_m = run_query("SELECT * FROM students WHERE category = :cat", {"cat": target_cat}, fetch=True)
    df_l = run_query("SELECT * FROM attendance WHERE category = :cat", {"cat": target_cat}, fetch=True)
    
    if df_m is None or df_m.empty:
        st.info("لم يتم العثور على طلاب مسجلين في هذه الفئة.")
    else:
        # حساب التواريخ الفريدة (أيام النشاط)
        unique_dates = df_l['date'].unique() if (df_l is not None and not df_l.empty) else []
        total_days = len(unique_dates)
        
        report = []
        for _, student in df_m.iterrows():
            # حساب حضور الطالب بدقة
            student_att = df_l[df_l['student_name'] == student['name']] if (df_l is not None and not df_l.empty) else pd.DataFrame()
            days_attended = len(student_att['date'].unique())
            
            # حساب النسبة المئوية
            perc = (days_attended / total_days * 100) if total_days > 0 else 0
            
            report.append({
                "الاسم الكامل": student['name'],
                "المسجد التابع له": student['mosque'],
                "المرحلة الدراسية": student['grade'],
                "عدد أيام الحضور": days_attended,
                "نسبة الالتزام": f"{perc:.1f}%"
            })
        
        # عرض الجدول الطويل المفصل
        final_report_df = pd.DataFrame(report)
        st.table(final_report_df)
        st.write(f"📝 إجمالي أيام النشاط المسجلة: **{total_days}** يوم")

# --- 5. بوابة المشرف (إضافة وحذف وتسجيل) ---
with tab_admin:
    pwd = st.text_input("كلمة المرور للدخول:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("✅ تم التحقق من الهوية، مرحباً بك.")
        sub1, sub2 = st.tabs(["📝 كشف حضور جديد", "➕ إضافة وحذف الطلاب"])

        with sub1:
            st.subheader("تسجيل حضور الطلاب")
            df_m_att = run_query("SELECT name FROM students WHERE category = :cat", {"cat": target_cat}, fetch=True)
            if df_m_att is not None and not df_m_att.empty:
                att_date = st.date_input("تاريخ اليوم:", datetime.now())
                with st.form("att_form"):
                    st.write("اختر الطلاب الحاضرين:")
                    selected = []
                    # ترتيب الأسماء أبجدياً
                    names_list = sorted(df_m_att['name'].tolist())
                    for n in names_list:
                        if st.checkbox(n, key=f"ch_{n}"):
                            selected.append(n)
                    
                    if st.form_submit_button("إرسال كشف الحضور"):
                        if selected:
                            for name in selected:
                                run_query("""
                                    INSERT INTO attendance (student_name, category, date) 
                                    SELECT :n, :c, :d 
                                    WHERE NOT EXISTS (SELECT 1 FROM attendance WHERE student_name=:n AND date=:d AND category=:c)
                                """, {"n": name, "c": target_cat, "d": str(att_date)})
                            st.success(f"✨ تم بنجاح تسجيل حضور {len(selected)} طالب لهذا اليوم!")
                            st.rerun()
                        else:
                            st.warning("يرجى اختيار طالب واحد على الأقل.")
            else:
                st.info("لا يوجد طلاب للإحضار، يرجى إضافة طلاب أولاً.")

        with sub2:
            st.subheader("إدارة قاعدة بيانات الطلاب")
            with st.form("add_student", clear_on_submit=True):
                n_in = st.text_input("اسم الطالب الجديد:")
                m_in = st.selectbox("المسجد:", ["شاهه العبيد","اليوسفين","العسعوسي","السهو","فاطمه الغلوم","الصقعبي","الرشيد","الرومي"])
                g_in = st.selectbox("المرحلة:", ["الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر","الحادي عشر","الثاني عشر","جامعي"])
                
                if st.form_submit_button("إضافة الطالب للسجلات"):
                    if n_in:
                        run_query("INSERT INTO students (name, mosque, grade, category) VALUES (:n, :m, :g, :c)", 
                                  {"n": n_in, "m": m_in, "g": g_in, "c": target_cat})
                        # التنبيه الأخضر الذي طلبته
                        st.success(f"🎊 مبروك! تم إضافة الطالب ({n_in}) بنجاح إلى قاعدة البيانات السحابية.")
                        st.rerun()
                    else:
                        st.error("خطأ: يرجى إدخال اسم الطالب.")
            
            st.divider()
            st.subheader("حذف طالب من النظام")
            df_m_del = run_query("SELECT name FROM students WHERE category = :cat", {"cat": target_cat}, fetch=True)
            names_to_del = [""] + (df_m_del['name'].tolist() if df_m_del is not None else [])
            del_n = st.selectbox("اختر الطالب المراد حذفه نهائياً:", names_to_del)
            
            if st.button("🗑️ تنفيذ الحذف"):
                if del_n:
                    run_query("DELETE FROM students WHERE name = :n AND category = :c", {"n": del_n, "c": target_cat})
                    run_query("DELETE FROM attendance WHERE student_name = :n AND category = :c", {"n": del_n, "c": target_cat})
                    st.warning(f"تم حذف الطالب {del_n} وجميع سجلاته بنجاح.")
                    st.rerun()

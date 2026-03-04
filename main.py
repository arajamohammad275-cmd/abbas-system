import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# -----------------------------
# 1. إعداد قاعدة البيانات (SQL)
# -----------------------------
def init_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    # جدول الطلاب
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mosque TEXT,
            grade TEXT,
            category TEXT
        )
    ''')
    # جدول الحضور
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            category TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# -----------------------------
# 2. إعدادات الصفحة والتصميم
# -----------------------------
st.set_page_config(page_title="نظام حضور الأنشطة Pro", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; direction: rtl !important; text-align: right !important; }
.stApp { background-color: #0f172a; color: #f8fafc; }
.header-box { background: linear-gradient(135deg,#1e293b 0%,#0f172a 100%); padding:2rem; border-radius:20px; border:1px solid #334155; margin-bottom:2rem; text-align:center !important; box-shadow:0 10px 15px -3px rgba(0,0,0,0.3);}
.main-title { background: linear-gradient(90deg,#38bdf8,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:2.8rem; font-weight:900; margin:0; text-align:center !important;}
.stButton>button{border-radius:12px;background:linear-gradient(90deg,#3b82f6,#2563eb);color:white;font-weight:bold;width:100%;height:3.5rem;border:none;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1 class="main-title">نظام حضور الأنشطة</h1></div>', unsafe_allow_html=True)

# -----------------------------
# 3. الثوابت والإعدادات
# -----------------------------
PASSWORDS = {
    "فئة أشبال السالمية":"Salmiya2026",
    "فئة أشبال حولي":"Hawally2026",
    "فئة الفتية":"Fetya2026",
    "فئة الشباب":"Shabab2026",
    "فئة الجامعيين":"Uni2026"
}

target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))

# -----------------------------
# 4. جلب البيانات من SQL
# -----------------------------
def get_students(cat):
    return pd.read_sql(f"SELECT * FROM students WHERE category='{cat}'", conn)

def get_attendance(cat):
    return pd.read_sql(f"SELECT * FROM attendance WHERE category='{cat}'", conn)

# -----------------------------
# 5. التبويبات الرئيسية
# -----------------------------
tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام", "🔐 بوابة المشرف"])

# --- كشف الالتزام ---
with tab_stats:
    df_m = get_students(target_cat)
    df_l = get_attendance(target_cat)
    
    if df_m.empty:
        st.info("لا يوجد طلاب مسجلين في هذه الفئة حالياً.")
    else:
        # حساب الإحصائيات
        total_days = df_l['date'].nunique()
        
        report = []
        for _, student in df_m.iterrows():
            st_name = student['name']
            # عدد أيام حضور الطالب
            days_attended = len(df_l[df_l['student_name'] == st_name]['date'].unique())
            perc = f"{(days_attended/total_days*100):.1f}%" if total_days > 0 else "0%"
            
            report.append({
                "الاسم": st_name,
                "المسجد": student['mosque'],
                "المرحلة": student['grade'],
                "أيام الحضور": days_attended,
                "النسبة": perc
            })
        
        st.table(pd.DataFrame(report))

# --- بوابة المشرف ---
with tab_admin:
    pwd = st.text_input("أدخل كلمة المرور:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("تم تسجيل الدخول بنجاح")
        sub1, sub2, sub3 = st.tabs(["📝 تسجيل الحضور", "➕ إدارة الطلاب", "📥 التقارير"])

        # 1. تسجيل الحضور
        with sub1:
            df_m = get_students(target_cat)
            if not df_m.empty:
                att_date = st.date_input("تاريخ اليوم:", datetime.now())
                st.write("اختر الحاضرين:")
                
                selected_students = []
                # عرض الأسماء بشكل مرتب
                names = sorted(df_m['name'].tolist())
                for n in names:
                    if st.checkbox(n, key=f"att_{n}"):
                        selected_students.append(n)
                
                if st.button("✅ اعتماد الحضور"):
                    cursor = conn.cursor()
                    for name in selected_students:
                        # التأكد من عدم تكرار الحضور لنفس الطالب في نفس اليوم
                        check = cursor.execute("SELECT * FROM attendance WHERE student_name=? AND date=? AND category=?", (name, str(att_date), target_cat)).fetchone()
                        if not check:
                            cursor.execute("INSERT INTO attendance (student_name, category, date) VALUES (?, ?, ?)", (name, target_cat, str(att_date)))
                    conn.commit()
                    st.success(f"تم تسجيل حضور {len(selected_students)} طالب بتاريخ {att_date}")
            else:
                st.warning("أضف طلاباً أولاً لتتمكن من رصد الحضور.")

        # 2. إدارة الطلاب
        with sub2:
            st.subheader("إضافة طالب جديد")
            with st.form("add_form", clear_on_submit=True):
                name_in = st.text_input("الاسم الثلاثي")
                msq_in = st.selectbox("المسجد", ["شاهه العبيد","اليوسفين","العسعوسي","السهو","فاطمه الغلوم","الصقعبي","الرشيد","الرومي"])
                lvl_in = st.selectbox("المرحلة الدراسية", ["الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر","الحادي عشر","الثاني عشر","جامعي"])
                if st.form_submit_button("إضافة الطالب"):
                    if name_in:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO students (name, mosque, grade, category) VALUES (?, ?, ?, ?)", (name_in, msq_in, lvl_in, target_cat))
                        conn.commit()
                        st.success(f"تمت إضافة {name_in} بنجاح!")
                        st.rerun()

            st.divider()
            st.subheader("حذف طالب")
            df_m = get_students(target_cat)
            del_n = st.selectbox("اختر الطالب المراد حذفه:", [""] + df_m['name'].tolist())
            if st.button("🗑️ حذف نهائي"):
                if del_n:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM students WHERE name=? AND category=?", (del_n, target_cat))
                    cursor.execute("DELETE FROM attendance WHERE student_name=? AND category=?", (del_n, target_cat))
                    conn.commit()
                    st.warning(f"تم حذف {del_n} وكافة بيانات حضوره.")
                    st.rerun()

        # 3. التقارير
        with sub3:
            st.subheader("استخراج تقرير مفصل")
            d1 = st.date_input("من تاريخ", datetime.now())
            d2 = st.date_input("إلى تاريخ", datetime.now())
            
            if st.button("📊 توليد تقرير للفترة"):
                df_l = get_attendance(target_cat)
                df_l['date_dt'] = pd.to_datetime(df_l['date'])
                mask = (df_l['date_dt'] >= pd.to_datetime(d1)) & (df_l['date_dt'] <= pd.to_datetime(d2))
                filtered_l = df_l[mask]
                
                period_days = filtered_l['date'].nunique()
                df_m = get_students(target_cat)
                
                rep_data = []
                for _, s in df_m.iterrows():
                    count = len(filtered_l[filtered_l['student_name'] == s['name']])
                    rep_data.append({
                        "الاسم": s['name'],
                        "أيام الحضور": count,
                        "نسبة الفترة": f"{(count/period_days*100):.1f}%" if period_days > 0 else "0%"
                    })
                
                res_df = pd.DataFrame(rep_data)
                st.dataframe(res_df, use_container_width=True)
                csv = res_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 تحميل التقرير CSV", csv, "report.csv", "text/csv")

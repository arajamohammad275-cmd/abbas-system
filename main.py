import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام حضور الأنشطة", layout="centered")

# --- الحل السحري: ذاكرة الموقع الفورية ---
if 'local_students' not in st.session_state:
    st.session_state['local_students'] = pd.DataFrame(columns=["الاسم", "المسجد", "المرحلة الدراسية", "الفئة"])

# الروابط
API_URL = "https://script.google.com/macros/s/AKfycbxwpiAyguMMZugESiw_QPiNA5t_MWr5YKqYOtwSoS_RfubNovE7QvRkhjmzr03dnIBtIA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
READ_M_BASE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_L_BASE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

# 2. الواجهة والمحاذاة الإجبارية لليمين (RTL)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    
    * {
        font-family: 'Cairo', sans-serif !important; 
        direction: rtl !important; 
        text-align: right !important;
    }
    
    .stApp { background-color: #0f172a; color: #f8fafc; }
    
    .header-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 2rem; border-radius: 20px; border: 1px solid #334155;
        margin-bottom: 2rem; text-align: center !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    .main-title { 
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 2.8rem; font-weight: 900; margin: 0; text-align: center !important;
    }
    
    .metric-card {
        background: #1e293b; border-radius: 15px; padding: 1.5rem;
        border-right: 5px solid #38bdf8; text-align: center !important; margin-bottom: 1rem;
    }
    .metric-card h3 { color: #94a3b8; font-size: 1.2rem; margin-bottom: 10px; text-align: center !important;}
    .metric-card h2 { color: #f8fafc; font-size: 2.2rem; margin: 0; font-weight: bold; text-align: center !important;}

    div[data-baseweb="select"] > div { direction: rtl !important; text-align: right !important; }
    .stDataFrame div { direction: rtl !important; text-align: right !important; }
    .stTextInput input, .stSelectbox div, .stDateInput input { text-align: right !important; direction: rtl !important; }
    label { text-align: right !important; width: 100%; display: block !important; font-weight:bold; color: #e2e8f0; }

    .stButton>button, .stFormSubmitButton>button { 
        border-radius: 12px !important; background: linear-gradient(90deg, #3b82f6, #2563eb) !important;
        color: white !important; font-weight: bold !important; width: 100% !important; height: 3.5rem !important; border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. جلب البيانات 
@st.cache_data(ttl=0)
def fetch_data_secure():
    try:
        nocache = int(time.time())
        m = pd.read_csv(f"{READ_M_BASE}&_={nocache}")
        l = pd.read_csv(f"{READ_L_BASE}&_={nocache}")
        m.columns = [str(c).strip() for c in m.columns]
        l.columns = [str(c).strip() for c in l.columns]
        return m, l
    except:
        return pd.DataFrame(columns=["الاسم", "المسجد", "المرحلة الدراسية", "الفئة"]), pd.DataFrame(columns=["الاسم", "الفئة", "التاريخ"])

st.markdown('<div class="header-box"><h1 class="main-title">نظام حضور الأنشطة</h1></div>', unsafe_allow_html=True)

df_m_fetched, df_l = fetch_data_secure()

# --- دمج الأسماء من جوجل شيت + الأسماء المضافة فوراً في الذاكرة ---
df_m = pd.concat([df_m_fetched, st.session_state['local_students']]).drop_duplicates(subset=['الاسم', 'الفئة'], keep='first')

PASSWORDS = {"فئة أشبال السالمية": "Salmiya2026", "فئة أشبال حولي": "Hawally2026", "فئة الفتية": "Fetya2026", "فئة الشباب": "Shabab2026", "فئة الجامعيين": "Uni2026"}

target_cat = st.selectbox("📂 اختر الفئة للإدارة:", list(PASSWORDS.keys()))
tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام والنسب", "🔐 بوابة المشرف"])

m_list = df_m[df_m['الفئة'] == target_cat] if not df_m.empty else pd.DataFrame()
l_list = df_l[df_l['الفئة'] == target_cat] if not df_l.empty else pd.DataFrame()

# --- التبويب الأول: الكشف العام ---
with tab_stats:
    if not m_list.empty:

        # التأكد من وجود بيانات وسجلات
        if not l_list.empty and "التاريخ" in l_list.columns:
            l_list["التاريخ"] = pd.to_datetime(l_list["التاريخ"], errors="coerce")
            total_activity_days = l_list["التاريخ"].nunique()
        else:
            total_activity_days = 0

        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="metric-card"><h3>👥 طلاب الفئة</h3><h2>{len(m_list)}</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><h3>📅 أيام النشاط</h3><h2>{total_activity_days}</h2></div>', unsafe_allow_html=True)

        display_df = m_list.copy()

        # حساب أيام الحضور الفعلية (أيام فريدة لكل طالب)
        def calculate_attendance(student_name):
            if not l_list.empty and "الاسم" in l_list.columns:
                student_logs = l_list[l_list["الاسم"] == student_name]
                return student_logs["التاريخ"].nunique()
            return 0

        display_df["أيام الحضور"] = display_df["الاسم"].apply(calculate_attendance)

                # حساب عدد أيام النشاط الفعلية
        if not l_list.empty and "التاريخ" in l_list.columns:
            l_list["التاريخ"] = pd.to_datetime(l_list["التاريخ"], errors="coerce")
            total_activity_days = l_list["التاريخ"].nunique()
        else:
            total_activity_days = 0

        display_df = m_list.copy()

        # حساب أيام الحضور الفعلية لكل طالب
        display_df["أيام الحضور"] = display_df["الاسم"].apply(
            lambda name: l_list[l_list["الاسم"] == name]["التاريخ"].nunique()
            if not l_list.empty else 0
        )

        # حساب النسبة المئوية
        if total_activity_days > 0:
            display_df["النسبة المئوية"] = (
                (display_df["أيام الحضور"] / total_activity_days) * 100
            ).round(1).astype(str) + "%"
        else:
            display_df["النسبة المئوية"] = "0%"

        st.table(display_df)
# --- التبويب الثاني: بوابة المشرف ---
with tab_admin:
    pwd = st.text_input("أدخل كلمة المرور لدخول المشرف:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("تم تسجيل الدخول بنجاح ✅")
        
        sub1, sub2, sub3 = st.tabs(["📝 تسجيل الحضور", "➕ إدارة الطلاب", "📥 التقارير التفصيلية"])
        
        # 1. تسجيل الحضور
        with sub1:
            if not m_list.empty:
                with st.form(key="attendance_form_secure", clear_on_submit=True):
                    today = st.date_input("تاريخ اليوم:", datetime.now())
                    st.write("اختر الحاضرين:")
                    selected = []
                    names = sorted(m_list['الاسم'].unique())
                    for n in names:
                        if st.checkbox(n, key=f"att_{n}"): selected.append(n)
                    
                    if st.form_submit_button("✅ اعتماد كشف الحضور", use_container_width=True):
                        if selected:
                            recs = [{"name": n, "category": target_cat, "date": str(today)} for n in selected]
                            requests.post(API_URL, json={"action": "add_attendance", "records": recs})
                            st.cache_data.clear() 
                            st.success("تم تسجيل الحضور بنجاح!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("الرجاء تحديد طالب واحد على الأقل.")
            else:
                st.warning("يرجى إضافة طلاب أولاً.")
        
        # 2. إضافة وحذف الطلاب
        with sub2:
            with st.form(key="add_student_form_secure", clear_on_submit=True):
                st.write("### ➕ إضافة طالب جديد")
                name_in = st.text_input("الاسم الثلاثي")
                msq_in = st.selectbox("المسجد", ["شاهه العبيد", "اليوسفين", "العسعوسي", "السهو", "فاطمه الغلوم", "الصقعبي", "الرشيد", "الرومي"])
                lvl_in = st.selectbox("المرحلة الدراسية", ["الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر", "جامعي"])
                
                if st.form_submit_button("إضافة الطالب الآن", use_container_width=True):
                    if name_in:
                        # 1. إرسال البيانات لجوجل
                        requests.post(API_URL, json={"action": "add_student", "name": name_in, "mosque": msq_in, "grade": lvl_in, "category": target_cat})
                        
                        # 2. إضافة الاسم فوراً لذاكرة الموقع (هنا حل المشكلة)
                        new_student = pd.DataFrame([{"الاسم": name_in, "المسجد": msq_in, "المرحلة الدراسية": lvl_in, "الفئة": target_cat}])
                        st.session_state['local_students'] = pd.concat([st.session_state['local_students'], new_student], ignore_index=True)
                        
                        st.cache_data.clear()
                        st.success(f"تمت إضافة {name_in} بنجاح!")
                        time.sleep(0.5)
                        st.rerun()
                    else: 
                        st.error("يرجى كتابة اسم الطالب أولاً")

            st.divider()
            st.write("###  حذف طالب")
            del_n = st.selectbox("اختر الاسم المراد حذفه:", [""] + sorted(m_list['الاسم'].tolist()) if not m_list.empty else [""])
            if st.button("تأكيد الحذف النهائي", use_container_width=True):
                if del_n:
                    requests.post(API_URL, json={"action": "delete_student", "name": del_n, "category": target_cat})
                    
                    # حذفه من الذاكرة أيضاً
                    st.session_state['local_students'] = st.session_state['local_students'][st.session_state['local_students']['الاسم'] != del_n]
                    
                    st.cache_data.clear()
                    st.error(f"تم حذف {del_n} نهائياً.")
                    time.sleep(0.5)
                    st.rerun()
        
        # 3. التقارير التفصيلية
        with sub3:
            st.write("### 📊 استخراج التقرير المفصل")
            d1, d2 = st.columns(2)
            date_from = d1.date_input("من تاريخ", datetime.now())
            date_to = d2.date_input("إلى تاريخ", datetime.now())
            
             

if st.button("🔍 تجهيز التقرير التفصيلي", use_container_width=True):
    if not l_list.empty:
        # تأكد أن التاريخ بصيغة datetime    


mask = (l_list['التاريخ'] >= str(date_from)) & (l_list['التاريخ'] <= str(date_to))

                    filtered_logs = l_list[mask]
                    days_in_period = len(filtered_logs['التاريخ'].unique()) if not filtered_logs.empty else 0
                    
                    rep_data = []
                    for _, student in m_list.iterrows():
                        count = len(filtered_logs[filtered_logs['الاسم'] == student['الاسم']])
                        pct = f"{(count / days_in_period * 100):.1f}%" if days_in_period > 0 else "0%"
                        
                        rep_data.append({
                            "الاسم": student['الاسم'],
                            "المسجد": student['المسجد'],
                            "المرحلة الدراسية": student['المرحلة الدراسية'],
                            "أيام الحضور للفترة": count,
                            "النسبة المئوية": pct
                        })
                    
                    res_df = pd.DataFrame(rep_data)
                    res_df = res_df.sort_values(by="الاسم")
                    res_df = res_df[[
    "الاسم",
    "المسجد",
    "المرحلة الدراسية",
    "أيام الحضور للفترة",
    "النسبة المئوية",
]]
                    st.table(res_df)
                    csv = res_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 تحميل التقرير الشامل (Excel / CSV)", csv, f"تقرير_مفصل_{target_cat}.csv", "text/csv", use_container_width=True)
                else:
                    st.info("لا توجد سجلات حضور بعد.")

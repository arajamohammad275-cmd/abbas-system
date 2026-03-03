import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# -----------------------------
# إعادة التشغيل الآمن
# -----------------------------
if 'rerun_flag' not in st.session_state:
    st.session_state['rerun_flag'] = False
if st.session_state['rerun_flag']:
    st.session_state['rerun_flag'] = False
    st.experimental_rerun()

# -----------------------------
# 1. إعدادات الصفحة
# -----------------------------
st.set_page_config(page_title="نظام حضور الأنشطة", layout="centered")

# ذاكرة الموقع الفورية
if 'local_students' not in st.session_state:
    st.session_state['local_students'] = pd.DataFrame(columns=["الاسم","المسجد","المرحلة الدراسية","الفئة"])
if 'local_logs' not in st.session_state:
    st.session_state['local_logs'] = pd.DataFrame(columns=["الاسم","الفئة","التاريخ"])

# روابط جوجل شيت
API_URL = "https://script.google.com/macros/s/AKfycbyK2LU11Y8PZAEJL3tvzj0XnJVVSnmjvptAXlRcxE4Z57zTLgfRJyi87uPG25Ap8-8DHA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
READ_M_BASE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_L_BASE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

# -----------------------------
# 2. تصميم RTL
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; direction: rtl !important; text-align: right !important; }
.stApp { background-color: #0f172a; color: #f8fafc; }
.header-box { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 2rem; border-radius: 20px; border: 1px solid #334155; margin-bottom: 2rem; text-align: center !important; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); }
.main-title { background: linear-gradient(90deg,#38bdf8,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:2.8rem; font-weight:900; margin:0; text-align:center !important; }
.metric-card { background:#1e293b; border-radius:15px; padding:1.5rem; border-right:5px solid #38bdf8; text-align:center !important; margin-bottom:1rem; }
.metric-card h3 { color:#94a3b8; font-size:1.2rem; margin-bottom:10px; text-align:center !important;}
.metric-card h2 { color:#f8fafc; font-size:2.2rem; margin:0; font-weight:bold; text-align:center !important;}
div[data-baseweb="select"]>div { direction:rtl !important; text-align:right !important; }
.stDataFrame div { direction:rtl !important; text-align:right !important; }
.stTextInput input, .stSelectbox div, .stDateInput input { text-align:right !important; direction:rtl !important; }
label { text-align:right !important; width:100%; display:block !important; font-weight:bold; color:#e2e8f0; }
.stButton>button, .stFormSubmitButton>button { border-radius:12px !important; background:linear-gradient(90deg,#3b82f6,#2563eb) !important; color:white !important; font-weight:bold !important; width:100% !important; height:3.5rem !important; border:none !important; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 3. جلب البيانات
# -----------------------------
@st.cache_data(ttl=5)
def fetch_data_secure():
    try:
        m = pd.read_csv(READ_M_BASE)
        l = pd.read_csv(READ_L_BASE)
        m.columns = [str(c).strip() for c in m.columns]
        l.columns = [str(c).strip() for c in l.columns]
        return m,l
    except:
        return pd.DataFrame(columns=["الاسم","المسجد","المرحلة الدراسية","الفئة"]), pd.DataFrame(columns=["الاسم","الفئة","التاريخ"])

st.markdown('<div class="header-box"><h1 class="main-title">نظام حضور الأنشطة</h1></div>', unsafe_allow_html=True)
df_m_fetched, df_l = fetch_data_secure()
df_m = pd.concat([df_m_fetched, st.session_state['local_students']]).drop_duplicates(subset=['الاسم','الفئة'], keep='first')

PASSWORDS = {
    "فئة أشبال السالمية":"Salmiya2026",
    "فئة أشبال حولي":"Hawally2026",
    "فئة الفتية":"Fetya2026",
    "فئة الشباب":"Shabab2026",
    "فئة الجامعيين":"Uni2026"
}

target_cat = st.selectbox("📂 اختر الفئة للإدارة:", list(PASSWORDS.keys()))
tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام والنسب","🔐 بوابة المشرف"])

m_list = df_m[df_m['الفئة']==target_cat].sort_values(by="الاسم",ignore_index=True) if not df_m.empty else pd.DataFrame()
l_list = df_l[df_l['الفئة']==target_cat] if not df_l.empty else pd.DataFrame()

# =============================
# كشف الالتزام والنسب
# =============================
with tab_stats:
    if m_list.empty:
        st.info("لا توجد طلاب في هذه الفئة حتى الآن.")
    else:
        m_list['الاسم']=m_list['الاسم'].astype(str).str.strip()
        if not l_list.empty:
            l_list['الاسم']=l_list['الاسم'].astype(str).str.strip()
            l_list['التاريخ']=pd.to_datetime(l_list['التاريخ'],errors='coerce')
        else:
            l_list=pd.DataFrame(columns=['الاسم','التاريخ'])

        total_days = l_list['التاريخ'].dt.date.nunique() if not l_list.empty else 0
        m_list['أيام الحضور']=m_list['الاسم'].apply(lambda n:l_list[l_list['الاسم']==n]['التاريخ'].dt.date.nunique() if not l_list.empty else 0)
        m_list['النسبة المئوية']=(m_list['أيام الحضور']/total_days*100).round(1).astype(str)+'%' if total_days>0 else '0%'
        st.table(m_list[['الاسم','المسجد','المرحلة الدراسية','أيام الحضور','النسبة المئوية']])

# =============================
# بوابة المشرف
# =============================
with tab_admin:
    pwd = st.text_input("أدخل كلمة المرور:", type="password")
    if pwd==PASSWORDS.get(target_cat):
        st.success("تم تسجيل الدخول بنجاح ✅")
        sub1, sub2, sub3 = st.tabs(["📝 تسجيل الحضور","➕ إدارة الطلاب","📥 التقارير التفصيلية"])

        # تسجيل الحضور
        with sub1:
            if not m_list.empty:
                with st.form(key="att_form", clear_on_submit=True):
                    today = st.date_input("تاريخ اليوم:",datetime.now())
                    selected=[n for n in sorted(m_list['الاسم'].unique()) if st.checkbox(n,key=f"att_{n}")]
                    if st.form_submit_button("✅ اعتماد كشف الحضور", use_container_width=True):
                        if selected:
                            recs=[{"name":n,"category":target_cat,"date":str(today)} for n in selected]
                            requests.post(API_URL,json={"action":"add_attendance","records":recs})
                            for n in selected:
                                st.session_state['local_logs']=pd.concat([st.session_state['local_logs'],pd.DataFrame([{'الاسم':n,'الفئة':target_cat,'التاريخ':today}])],ignore_index=True)
                            st.session_state['rerun_flag']=True

        # إضافة وحذف الطلاب
        with sub2:
            with st.form(key="add_student_form", clear_on_submit=True):
                name_in=st.text_input("الاسم الثلاثي")
                msq_in=st.selectbox("المسجد",["شاهه العبيد","اليوسفين","العسعوسي","السهو","فاطمه الغلوم","الصقعبي","الرشيد","الرومي"])
                lvl_in=st.selectbox("المرحلة الدراسية",["الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر","الحادي عشر","الثاني عشر","جامعي"])
                if st.form_submit_button("إضافة الطالب الآن", use_container_width=True):
                    if name_in:
                        requests.post(API_URL,json={"action":"add_student","name":name_in,"mosque":msq_in,"grade":lvl_in,"category":target_cat})
                        new_student=pd.DataFrame([{"الاسم":name_in,"المسجد":msq_in,"المرحلة الدراسية":lvl_in,"الفئة":target_cat}])
                        st.session_state['local_students']=pd.concat([st.session_state['local_students'],new_student],ignore_index=True)
                        st.session_state['rerun_flag']=True

            del_n=st.selectbox("اختر الاسم المراد حذفه:",[""]+sorted(m_list['الاسم'].tolist()) if not m_list.empty else [""])
            if st.button("تأكيد الحذف النهائي", use_container_width=True):
                if del_n:
                    requests.post(API_URL,json={"action":"delete_student","name":del_n,"category":target_cat})
                    st.session_state['local_students']=st.session_state['local_students'][st.session_state['local_students']['الاسم']!=del_n]
                    st.session_state['rerun_flag']=True

        # التقارير التفصيلية
        with sub3:
            d1,d2=st.columns(2)
            date_from=d1.date_input("من تاريخ",datetime.now())
            date_to=d2.date_input("إلى تاريخ",datetime.now())
            if st.button("🔍 تجهيز التقرير التفصيلي", use_container_width=True):
                all_logs=pd.concat([l_list,st.session_state['local_logs']],ignore_index=True)
                all_logs['الاسم']=all_logs['الاسم'].astype(str).str.strip()
                all_logs['التاريخ']=pd.to_datetime(all_logs['التاريخ'],errors='coerce')
                mask=(all_logs['التاريخ']>=pd.to_datetime(date_from)) & (all_logs['التاريخ']<=pd.to_datetime(date_to))
                filtered=all_logs[mask] if not all_logs.empty else pd.DataFrame(columns=all_logs.columns)
                days_in_period=len(filtered['التاريخ'].dt.date.unique()) if not filtered.empty else 0
                rep=[]
                for _,student in m_list.iterrows():
                    count=len(filtered[filtered['الاسم']==student['الاسم']])
                    pct=f"{(count/days_in_period*100):.1f}%" if days_in_period>0 else "0%"
                    rep.append({"الاسم":student['الاسم'],"المسجد":student['المسجد'],"المرحلة الدراسية":student['المرحلة الدراسية'],"أيام الحضور للفترة":count,"النسبة المئوية":pct})
                res_df=pd.DataFrame(rep).sort_values(by='الاسم',ignore_index=True)
                st.table(res_df)
                csv=res_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 تحميل التقرير الشامل (Excel / CSV)",csv,f"تقرير_مفصل_{datetime.now().strftime('%Y-%m-%d')}.csv","text/csv",use_container_width=True)

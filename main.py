import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# -----------------------------
# إعدادات الصفحة
# -----------------------------
st.set_page_config(page_title="نظام حضور الأنشطة", layout="centered")

# ذاكرة الموقع
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
# RTL وتصميم
# -----------------------------
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
# جلب البيانات
# -----------------------------
@st.cache_data(ttl=5)
def fetch_data():
    try:
        m = pd.read_csv(READ_M_BASE)
        l = pd.read_csv(READ_L_BASE)
        m.columns = [str(c).strip() for c in m.columns]
        l.columns = [str(c).strip() for c in l.columns]
        return m,l
    except:
        return pd.DataFrame(columns=["الاسم","المسجد","المرحلة الدراسية","الفئة"]), pd.DataFrame(columns=["الاسم","الفئة","التاريخ"])

df_m_fetched, df_l = fetch_data()
df_m = pd.concat([df_m_fetched, st.session_state['local_students']]).drop_duplicates(subset=['الاسم','الفئة'], keep='first')

PASSWORDS = {
    "فئة أشبال السالمية":"Salmiya2026",
    "فئة أشبال حولي":"Hawally2026",
    "فئة الفتية":"Fetya2026",
    "فئة الشباب":"Shabab2026",
    "فئة الجامعيين":"Uni2026"
}

target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))
tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام","🔐 بوابة المشرف"])

# =============================
# تصفية الفئة
# =============================
m_list = df_m[df_m['الفئة']==target_cat].sort_values(by="الاسم",ignore_index=True) if not df_m.empty else pd.DataFrame()
l_list = df_l[df_l['الفئة']==target_cat] if not df_l.empty else pd.DataFrame()

# =============================
# كشف الالتزام والنسب
# =============================
with tab_stats:
    if m_list.empty:
        st.info("لا توجد طلاب في هذه الفئة.")
    else:
        m_list['الاسم']=m_list['الاسم'].astype(str).str.strip()
        if not l_list.empty:
            l_list['الاسم']=l_list['الاسم'].astype(str).str.strip()
            l_list['التاريخ']=pd.to_datetime(l_list['التاريخ'],errors='coerce')
        total_days = l_list['التاريخ'].dt.date.nunique() if not l_list.empty else 0
        m_list['أيام الحضور'] = m_list['الاسم'].apply(lambda n: l_list[l_list['الاسم']==n]['التاريخ'].dt.date.nunique() if not l_list.empty else 0)
        m_list['النسبة المئوية'] = (m_list['أيام الحضور']/total_days*100).round(1).astype(str)+'%' if total_days>0 else '0%'
        st.table(m_list[['الاسم','المسجد','المرحلة الدراسية','أيام الحضور','النسبة المئوية']])

# =============================
# بوابة المشرف
# =============================
with tab_admin:
    pwd = st.text_input("أدخل كلمة المرور:", type="password")
    if pwd==PASSWORDS.get(target_cat):
        st.success("تم تسجيل الدخول ✅")
        sub1, sub2, sub3 = st.tabs(["📝 تسجيل الحضور","➕ إدارة الطلاب","📥 التقارير التفصيلية"])

        # تسجيل الحضور (checkbox)
        with sub1:
            if not m_list.empty:
                st.write("اختر الحاضرين:")
                today = datetime.now().date()
                for n in sorted(m_list['الاسم'].unique()):
                    checked = n in st.session_state['local_logs']['الاسم'].tolist() if not st.session_state['local_logs'].empty else False
                    cb = st.checkbox(n,value=checked,key=f"att_{n}")
                    if cb and not checked:
                        # إضافة حضور جديد
                        requests.post(API_URL,json={"action":"add_attendance","records":[{"name":n,"category":target_cat,"date":str(today)}]})
                        st.session_state['local_logs'] = pd.concat([st.session_state['local_logs'], pd.DataFrame([{'الاسم':n,'الفئة':target_cat,'التاريخ':today}])],ignore_index=True)

        # إدارة الطلاب
        with sub2:
            with st.form(key="add_student",clear_on_submit=True):
                name_in=st.text_input("الاسم الثلاثي")
                msq_in=st.selectbox("المسجد",["شاهه العبيد","اليوسفين","العسعوسي","السهو","فاطمه الغلوم","الصقعبي","الرشيد","الرومي"])
                lvl_in=st.selectbox("المرحلة الدراسية",["الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر","الحادي عشر","الثاني عشر","جامعي"])
                if st.form_submit_button("إضافة الطالب",use_container_width=True):
                    if name_in:
                        requests.post(API_URL,json={"action":"add_student","name":name_in,"mosque":msq_in,"grade":lvl_in,"category":target_cat})
                        new_student=pd.DataFrame([{"الاسم":name_in,"المسجد":msq_in,"المرحلة الدراسية":lvl_in,"الفئة":target_cat}])
                        st.session_state['local_students']=pd.concat([st.session_state['local_students'],new_student],ignore_index=True)
                        st.success(f"تمت إضافة {name_in} ✅")
            del_n=st.selectbox("اختر الاسم لحذفه:",[""]+sorted(m_list['الاسم'].tolist()) if not m_list.empty else [""])
            if st.button("حذف الطالب",use_container_width=True):
                if del_n:
                    requests.post(API_URL,json={"action":"delete_student","name":del_n,"category":target_cat})
                    st.session_state['local_students']=st.session_state['local_students'][st.session_state['local_students']['الاسم']!=del_n]
                    st.success(f"تم حذف {del_n} ✅")

        # التقارير التفصيلية
        with sub3:
            d1,d2=st.columns(2)
            date_from=d1.date_input("من تاريخ",datetime.now())
            date_to=d2.date_input("إلى تاريخ",datetime.now())
            if st.button("📊 تجهيز التقرير",use_container_width=True):
                all_logs=pd.concat([l_list,st.session_state['local_logs']],ignore_index=True)
                all_logs['الاسم']=all_logs['الاسم'].astype(str).str.strip()
                all_logs['التاريخ']=pd.to_datetime(all_logs['التاريخ'],errors='coerce')
                mask=(all_logs['التاريخ']>=pd.to_datetime(date_from)) & (all_logs['التاريخ']<=pd.to_datetime(date_to))
                filtered=all_logs[mask] if not all_logs.empty else pd.DataFrame(columns=all_logs.columns)
                days_in_period=len(filtered['التاريخ'].dt.date.unique()) if not filtered.empty else 0
                rep=[]
                for _,s in m_list.iterrows():
                    count=len(filtered[filtered['الاسم']==s['الاسم']])
                    pct=f"{(count/days_in_period*100):.1f}%" if days_in_period>0 else "0%"
                    rep.append({"الاسم":s['الاسم'],"المسجد":s['المسجد'],"المرحلة الدراسية":s['المرحلة الدراسية'],"أيام الحضور للفترة":count,"النسبة المئوية":pct})
                res_df=pd.DataFrame(rep).sort_values(by='الاسم',ignore_index=True)
                st.table(res_df)
                csv=res_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 تحميل CSV",csv,f"تقرير_مفصل_{datetime.now().strftime('%Y-%m-%d')}.csv","text/csv",use_container_width=True)

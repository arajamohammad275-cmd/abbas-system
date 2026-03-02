import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# إعدادات المظهر (نفس كودك بالضبط)
st.set_page_config(page_title="نظام حضور الأنشطة", layout="centered")

# *** ضع الرابط الذي حصلت عليه من جوجل هنا ***
API_URL = "https://script.google.com/macros/s/AKfycbxwpiAyguMMZugESiw_QPiNA5t_MWr5YKQyOtwSoS_RfubNovE7QvRkhjmzr03dnlBtIA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
READ_URL_M = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_URL_L = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

# التنسيق الجمالي (نفس كودك)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"], .stApp { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; color: #FFFFFF !important; }
    .stApp { background-color: #0f172a; }
    .main-header { background: linear-gradient(90deg, #00dbde, #fc00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center !important; font-size: 32px; font-weight: 800; padding: 20px 0; }
    .stButton>button { border-radius: 10px; background-color: #3b82f6 !important; color: white !important; font-weight: bold; width: 100%; height: 3.5em; border: none; }
    .card { background-color: #1e293b; border-radius: 12px; padding: 15px; border: 1px solid #475569; text-align: center; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# البيانات الثابتة
PASSWORDS = {"فئة أشبال السالمية": "Salmiya2026", "فئة أشبال حولي": "Hawally2026", "فئة الفتية": "Fetya2026", "فئة الشباب": "Shabab2026", "فئة الجامعيين": "Uni2026"}
MOSQUES = ["شاهه العبيد", "اليوسفين", "العسعوسي", "السهو", "فاطمه الغلوم", "الصقعبي", "الرشيد", "الرومي"]
LEVELS = ["الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر", "جامعي"]

def load_data():
    try:
        df_m = pd.read_csv(READ_URL_M)
        df_l = pd.read_csv(READ_URL_L)
        return df_m, df_l
    except:
        return pd.DataFrame(columns=["الاسم", "المسجد", "المرحلة الدراسية", "الفئة"]), pd.DataFrame(columns=["الاسم", "الفئة", "التاريخ"])

st.markdown('<div class="main-header">📊 نظام حضور الأنشطة</div>', unsafe_allow_html=True)
target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))
df_m, df_l = load_data()

tab1, tab2 = st.tabs(["👥 كشف الطلاب والالتزام", "🔐 بوابة المشرف"])

with tab1:
    m_list = df_m[df_m['الفئة'] == target_cat]
    l_list = df_l[df_l['الفئة'] == target_cat]
    total_days = len(l_list["التاريخ"].unique()) if not l_list.empty else 0
    
    col1, col2 = st.columns(2)
    col1.markdown(f'<div class="card"><h3>📅 أيام النشاط</h3><h2>{total_days}</h2></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="card"><h3>👥 طلاب الفئة</h3><h2>{len(m_list)}</h2></div>', unsafe_allow_html=True)
    
    if not m_list.empty:
        stats = []
        for _, row in m_list.iterrows():
            count = len(l_list[l_list['الاسم'] == row['الاسم']])
            pct = (count / total_days * 100) if total_days > 0 else 0
            stats.append({"الاسم": row['الاسم'], "المسجد": row['المسجد'], "نسبة الحضور": f"{pct:.1f}%"})
        st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)

with tab2:
    pwd = st.text_input("ادخل كلمة المرور", type="password")
    if pwd == PASSWORDS[target_cat]:
        st.success("أهلاً بك ✅")
        m_tab1, m_tab2 = st.tabs(["📝 تسجيل حضور", "⚙️ إدارة الطلاب"])
        
        with m_tab1:
            with st.form("att_form"):
                today = st.date_input("اختر تاريخ اليوم")
                selected = []
                for n in sorted(m_list["الاسم"].tolist()):
                    if st.checkbox(n): selected.append(n)
                if st.form_submit_button("اعتماد وحفظ"):
                    recs = [{"name": n, "category": target_cat, "date": str(today)} for n in selected]
                    requests.post(API_URL, json={"action": "add_attendance", "records": recs})
                    st.success("تم الحفظ في جوجل شيت!"); st.rerun()

        with m_tab2:
            with st.form("add_st"):
                new_n = st.text_input("اسم الطالب")
                new_m = st.selectbox("المسجد", MOSQUES)
                new_l = st.selectbox("المرحلة", LEVELS)
                if st.form_submit_button("إضافة الطالب"):
                    requests.post(API_URL, json={"action": "add_student", "name": new_n, "mosque": new_m, "grade": new_l, "category": target_cat})
                    st.success("تمت الإضافة!"); st.rerun()

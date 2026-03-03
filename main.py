import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. إعدادات الصفحة والمحاذاة
st.set_page_config(page_title="نظام مركز ابن عباس", layout="centered")

# --- الروابط ---
API_URL = "https://script.google.com/macros/s/AKfycbxwpiAyguMMZugESiw_QPiNA5t_MWr5YKqYOtwSoS_RfubNovE7QvRkhjmzr03dnIBtIA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
READ_M = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_L = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

# تنسيق الواجهة والمحاذاة يمين
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"], .stApp { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right !important; }
    .stApp { background-color: #0f172a; color: white; }
    .main-header { background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center !important; font-size: 30px; font-weight: 800; padding: 10px; }
    div[data-testid="stMarkdownContainer"] > p { text-align: right; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #3b82f6 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. جلب البيانات بأمان
@st.cache_data(ttl=0)
def load_data():
    try:
        m = pd.read_csv(READ_M)
        l = pd.read_csv(READ_L)
        m.columns = [c.strip() for c in m.columns]
        l.columns = [c.strip() for c in l.columns]
        return m, l
    except:
        # صنع جداول وهمية بالعناوين الصحيحة لو فشل التحميل أو كان الشيت فاضي
        return pd.DataFrame(columns=["الاسم", "المسجد", "المرحلة الدراسية", "الفئة"]), \
               pd.DataFrame(columns=["الاسم", "الفئة", "التاريخ"])

# القوائم والكلمات
PASSWORDS = {"فئة أشبال السالمية": "Salmiya2026", "فئة أشبال حولي": "Hawally2026", "فئة الفتية": "Fetya2026", "فئة الشباب": "Shabab2026", "فئة الجامعيين": "Uni2026"}
LEVELS = ["الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر", "جامعي"]
MOSQUES = ["شاهه العبيد", "اليوسفين", "العسعوسي", "السهو", "فاطمه الغلوم", "الصقعبي", "الرشيد", "الرومي"]

st.markdown('<div class="main-header">📊 نظام مركز ابن عباس</div>', unsafe_allow_html=True)
df_m, df_l = load_data()
target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))

tab1, tab2 = st.tabs(["👥 كشف الالتزام والنسب", "🔐 بوابة المشرف"])

with tab1:
    # تصفية آمنة للبيانات
    m_list = df_m[df_m['الفئة'] == target_cat] if not df_m.empty and 'الفئة' in df_m.columns else pd.DataFrame()
    l_list = df_l[df_l['الفئة'] == target_cat] if not df_l.empty and 'الفئة' in df_l.columns else pd.DataFrame()
    
    total_days = len(l_list["التاريخ"].unique()) if not l_list.empty else 0
    st.write(f"### عدد أيام النشاط الكلي: {total_days}")
    
    if not m_list.empty:
        # حساب النسبة المئوية
        m_list = m_list.copy()
        m_list['الحضور'] = m_list['الاسم'].apply(lambda x: len(l_list[l_list['الاسم'] == x]) if not l_list.empty else 0)
        m_list['النسبة'] = m_list['الحضور'].apply(lambda x: f"{(x/total_days*100):.1f}%" if total_days > 0 else "0%")
        st.dataframe(m_list[["الاسم", "المسجد", "الحضور", "الالنسبة"]], use_container_width=True, hide_index=True)
    else:
        st.info("لا يوجد طلاب مسجلين لهذه الفئة.")

with tab2:
    pwd = st.text_input("كلمة المرور:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("تم الدخول ✅")
        sub1, sub2 = st.tabs(["📝 تسجيل حضور", "⚙️ إدارة الطلاب"])
        
        with sub1:
            if not m_list.empty:
                with st.form(key="att_form_fixed"):
                    day = st.date_input("تاريخ اليوم")
                    st.write("اختر الحاضرين:")
                    selected = []
                    # ترتيب الأسماء أبجدياً
                    names = sorted(m_list['الاسم'].unique())
                    for n in names:
                        if st.checkbox(n, key=f"check_{n}"):
                            selected.append(n)
                    
                    # زر الحفظ داخل الفورم عشان ما يطلع خطأ
                    submit = st.form_submit_button("حفظ الحضور")
                    if submit:
                        if selected:
                            recs = [{"name": n, "category": target_cat, "date": str(day)} for n in selected]
                            requests.post(API_URL, json={"action": "add_attendance", "records": recs})
                            st.success("تم الحفظ بنجاح!"); st.rerun()
            else: st.info("أضف طلاباً من تبويب الإدارة.")

        with sub2:
            st.subheader("إضافة طالب")
            with st.form("add_student_form"):
                n = st.text_input("الاسم")
                m = st.selectbox("المسجد", MOSQUES)
                l = st.selectbox("المرحلة", LEVELS)
                if st.form_submit_button("إضافة الطالب"):
                    if n:
                        requests.post(API_URL, json={"action": "add_student", "name": n, "mosque": m, "grade": l, "category": target_cat})
                        st.success("تمت الإضافة!"); st.rerun()
            
            st.divider()
            st.subheader("حذف طالب")
            d_n = st.selectbox("اختر الاسم للتحذف:", [""] + (sorted(m_list['الاسم'].tolist()) if not m_list.empty else []))
            if st.button("حذف نهائي"):
                if d_n:
                    requests.post(API_URL, json={"action": "delete_student", "name": d_n, "category": target_cat})
                    st.error("تم الحذف"); st.rerun()

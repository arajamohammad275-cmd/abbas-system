import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# إعداد الصفحة وسرعة الاستجابة
st.set_page_config(page_title="نظام مركز ابن عباس", layout="centered")

# --- الرابط اللي نسخته من صورتك (image_ee05f5.png) ---
API_URL = "https://script.google.com/macros/s/AKfycbxwpiAyguMMZugESiw_QPiNA5t_MWr5YKqYOtwSoS_RfubNovE7QvRkhjmzr03dnIBtIA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
READ_M = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_L = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

# تنسيق المحاذاة لليمين والخط العربي
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"], .stApp { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right !important; }
    .stApp { background-color: #0f172a; color: white; }
    .main-header { background: linear-gradient(90deg, #00dbde, #fc00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center !important; font-size: 30px; font-weight: 800; padding: 10px; }
    .stButton>button { border-radius: 10px; background-color: #3b82f6 !important; width: 100%; height: 3em; }
    div[data-testid="stMarkdownContainer"] > p { text-align: right; }
    .stSelectbox, .stTextInput, .stCheckbox { direction: rtl !important; text-align: right !important; }
    </style>
    """, unsafe_allow_html=True)

# جلب البيانات بأعلى سرعة (بدون ذاكرة مؤقتة TTL=0)
@st.cache_data(ttl=0)
def load_data():
    try:
        m = pd.read_csv(READ_M); l = pd.read_csv(READ_L)
        m.columns = [c.strip() for c in m.columns]; l.columns = [c.strip() for c in l.columns]
        return m, l
    except:
        return pd.DataFrame(columns=["الاسم", "المسجد", "المرحلة الدراسية", "الفئة"]), pd.DataFrame(columns=["الاسم", "الفئة", "التاريخ"])

LEVELS = ["الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر", "جامعي"]
MOSQUES = ["شاهه العبيد", "اليوسفين", "العسعوسي", "السهو", "فاطمه الغلوم", "الصقعبي", "الرشيد", "الرومي"]
PASSWORDS = {"فئة أشبال السالمية": "Salmiya2026", "فئة أشبال حولي": "Hawally2026", "فئة الفتية": "Fetya2026", "فئة الشباب": "Shabab2026", "فئة الجامعيين": "Uni2026"}

st.markdown('<div class="main-header">📊 نظام مركز ابن عباس</div>', unsafe_allow_html=True)
df_m, df_l = load_data()
target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))

t1, t2 = st.tabs(["👥 كشف الالتزام", "🔐 بوابة المشرف"])

with t1:
    m_list = df_m[df_m['الفئة'] == target_cat] if not df_m.empty and 'الفئة' in df_m.columns else pd.DataFrame()
    if not m_list.empty:
        st.dataframe(m_list[["الاسم", "المسجد", "المرحلة الدراسية"]], use_container_width=True, hide_index=True)
    else: st.info("لا يوجد طلاب حالياً.")

with t2:
    pwd = st.text_input("كلمة المرور:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("مرحباً بك ✅")
        sub1, sub2, sub3 = st.tabs(["📝 تسجيل حضور", "⚙️ إدارة الطلاب", "📊 التقارير"])
        with sub1:
            if not m_list.empty:
                with st.form("att_form"):
                    day = st.date_input("التاريخ")
                    sel = []
                    for n in sorted(m_list['الاسم'].unique()):
                        if st.checkbox(n, key=f"c_{n}"): sel.append(n)
                    if st.form_submit_button("حفظ الحضور"):
                        recs = [{"name": n, "category": target_cat, "date": str(day)} for n in sel]
                        requests.post(API_URL, json={"action": "add_attendance", "records": recs})
                        st.success("تم الحفظ!"); st.rerun()
            else: st.info("يرجى إضافة طلاب أولاً.")
        with sub2:
            st.subheader("إضافة طالب")
            with st.form("add"):
                n = st.text_input("الاسم"); m = st.selectbox("المسجد", MOSQUES); l = st.selectbox("المرحلة", LEVELS)
                if st.form_submit_button("إضافة"):
                    requests.post(API_URL, json={"action": "add_student", "name": n, "mosque": m, "grade": l, "category": target_cat})
                    st.success("تم!"); st.rerun()
            st.divider()
            st.subheader("حذف طالب")
            d_n = st.selectbox("اختر الاسم:", [""] + sorted(m_list['الاسم'].tolist()) if not m_list.empty else [""])
            if st.button("حذف نهائي"):
                if d_n:
                    requests.post(API_URL, json={"action": "delete_student", "name": d_n, "category": target_cat})
                    st.error("تم الحذف"); st.rerun()
        with sub3:
            st.subheader("التقارير")
            d1 = st.date_input("من", datetime.now()); d2 = st.date_input("إلى", datetime.now())
            if st.button("عرض"):
                mask = (df_l['الفئة'] == target_cat) & (df_l['التاريخ'] >= str(d1)) & (df_l['التاريخ'] <= str(d2))
                f_l = df_l[mask]
                res_df = pd.DataFrame([{"الاسم": r['الاسم'], "الحضور": len(f_l[f_l['الاسم'] == r['الاسم']])} for _, r in m_list.iterrows()])
                st.table(res_df)
                st.download_button("تحميل", res_df.to_csv(index=False).encode('utf-8-sig'), "report.csv")

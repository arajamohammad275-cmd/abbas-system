import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. إعدادات الصفحة والستايل الاحترافي
st.set_page_config(page_title="نظام ابن عباس الذكي", layout="centered")

# الروابط
API_URL = "https://script.google.com/macros/s/AKfycbxwpiAyguMMZugESiw_QPiNA5t_MWr5YKqYOtwSoS_RfubNovE7QvRkhjmzr03dnIBtIA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
READ_M = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_L = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

# تنسيق CSS لضمان اليمين والجمالية
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"], .stApp { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right !important; }
    .stApp { background-color: #0f172a; color: white; }
    .header { background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center !important; font-size: 32px; font-weight: 800; padding: 20px; }
    .stButton>button { width: 100%; border-radius: 12px; background-color: #3b82f6 !important; color: white !important; font-weight: bold; }
    div[data-testid="stExpander"] { direction: rtl; }
    .metric-box { background: #1e293b; padding: 15px; border-radius: 15px; text-align: center; border-right: 5px solid #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

# 2. جلب البيانات ومعالجة أسماء الأعمدة (حل مشكلة KeyError)
@st.cache_data(ttl=0)
def load_data_safe():
    try:
        m = pd.read_csv(READ_M)
        l = pd.read_csv(READ_L)
        # تنظيف أسماء الأعمدة من المسافات المخفية
        m.columns = [str(c).strip() for c in m.columns]
        l.columns = [str(c).strip() for c in l.columns]
        return m, l
    except:
        return pd.DataFrame(), pd.DataFrame()

st.markdown('<div class="header">نظام مركز ابن عباس الذكي</div>', unsafe_allow_html=True)

df_m, df_l = load_data_safe()
PASSWORDS = {"فئة أشبال السالمية": "Salmiya2026", "فئة أشبال حولي": "Hawally2026", "فئة الفتية": "Fetya2026", "فئة الشباب": "Shabab2026", "فئة الجامعيين": "Uni2026"}

target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))

tab1, tab2 = st.tabs(["👥 كشف الطلاب والنسب", "🔐 بوابة المشرف"])

# تصفية البيانات بأمان
m_list = df_m[df_m['الفئة'] == target_cat] if not df_m.empty and 'الفئة' in df_m.columns else pd.DataFrame()
l_list = df_l[df_l['الفئة'] == target_cat] if not df_l.empty and 'الفئة' in df_l.columns else pd.DataFrame()

# --- التبويب الأول: النسب والكشف ---
with tab1:
    days_count = len(l_list["التاريخ"].unique()) if not l_list.empty and "التاريخ" in l_list.columns else 0
    c1, c2 = st.columns(2)
    with c1: st.markdown(f'<div class="metric-box">طلاب الفئة<br><h2>{len(m_list)}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-box">أيام النشاط<br><h2>{days_count}</h2></div>', unsafe_allow_html=True)
    
    st.write("### قائمة الطلاب ونسب الالتزام:")
    if not m_list.empty:
        # حساب الحضور والنسبة
        display_df = m_list.copy()
        def get_att(name): return len(l_list[l_list['الاسم'] == name]) if not l_list.empty else 0
        display_df['الحضور'] = display_df['الاسم'].apply(get_att)
        display_df['النسبة'] = display_df['الحضور'].apply(lambda x: f"{(x/days_count*100):.1f}%" if days_count > 0 else "0%")
        
        # عرض الأعمدة الأساسية فقط
        st.dataframe(display_df[["الاسم", "المسجد", "الحضور", "النسبة"]], use_container_width=True, hide_index=True)
    else:
        st.info("لا يوجد طلاب حالياً في هذه الفئة.")

# --- التبويب الثاني: الإدارة (حل مشكلة الزر) ---
with tab2:
    pwd = st.text_input("كلمة المرور:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("تم الدخول بنجاح ✅")
        sub1, sub2 = st.tabs(["📝 تسجيل حضور", "⚙️ إدارة الإسماء"])
        
        with sub1:
            if not m_list.empty:
                with st.form("att_form_new"):
                    date_now = st.date_input("تاريخ اليوم")
                    st.write("اختر الطلاب الحاضرين:")
                    selected_names = []
                    all_names = sorted(m_list['الاسم'].unique())
                    for n in all_names:
                        if st.checkbox(n, key=f"chk_{n}"):
                            selected_names.append(n)
                    
                    # الزر هنا داخل الـ Form حصراً
                    if st.form_submit_button("✅ حفظ كشف الحضور"):
                        if selected_names:
                            recs = [{"name": n, "category": target_cat, "date": str(date_now)} for n in selected_names]
                            requests.post(API_URL, json={"action": "add_attendance", "records": recs})
                            st.success("تم تسجيل الحضور!"); st.rerun()
                        else: st.warning("لم يتم اختيار أي طالب")
            else: st.error("لا يوجد طلاب لتحضيرهم")

        with sub2:
            with st.form("add_st"):
                st.write("➕ إضافة طالب جديد")
                new_n = st.text_input("اسم الطالب")
                new_m = st.selectbox("المسجد", ["شاهه العبيد", "اليوسفين", "العسعوسي", "السهو", "فاطمه الغلوم", "الصقعبي", "الرشيد", "الرومي"])
                new_g = st.selectbox("المرحلة", ["الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر", "جامعي"])
                if st.form_submit_button("إضافة"):
                    if new_n:
                        requests.post(API_URL, json={"action": "add_student", "name": new_n, "mosque": new_m, "grade": new_g, "category": target_cat})
                        st.success("تمت الإضافة"); st.rerun()

            st.divider()
            st.write("🗑️ حذف اسم")
            del_n = st.selectbox("اختر الاسم:", [""] + (sorted(m_list['الاسم'].tolist()) if not m_list.empty else []))
            if st.button("حذف نهائي"):
                if del_n:
                    requests.post(API_URL, json={"action": "delete_student", "name": del_n, "category": target_cat})
                    st.error("تم الحذف"); st.rerun()

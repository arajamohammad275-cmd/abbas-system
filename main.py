import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. إعدادات الصفحة والمحاذاة (السرعة والمظهر)
st.set_page_config(page_title="نظام مركز ابن عباس", layout="centered")

# --- الرابط الخاص بك (تأكد من تحديثه دائماً) ---
API_URL = "https://script.google.com/macros/s/AKfycbxwpiAyguMMZugESiw_QPiNA5t_MWr5YKqYOtwSoS_RfubNovE7QvRkhjmzr03dnIBtIA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
READ_M = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_L = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

# كود التنسيق لضمان المحاذاة لليمين والسرعة في العرض
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"], .stApp { 
        font-family: 'Cairo', sans-serif; 
        direction: rtl; 
        text-align: right !important; 
        color: #FFFFFF !important; 
    }
    .stApp { background-color: #0f172a; }
    .main-header { 
        background: linear-gradient(90deg, #00dbde, #fc00ff); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        text-align: center !important; 
        font-size: 32px; 
        font-weight: 800; 
        padding: 10px 0; 
    }
    /* جعل كل الحقول والأزرار لليمين */
    .stSelectbox, .stTextInput, .stDateInput, .stForm { text-align: right !important; direction: rtl !important; }
    div[data-baseweb="select"] { direction: rtl !important; }
    .stCheckbox { direction: rtl !important; text-align: right !important; }
    
    .stButton>button { border-radius: 10px; background-color: #3b82f6 !important; color: white !important; font-weight: bold; width: 100%; height: 3.5em; }
    .card { background-color: #1e293b; border-radius: 12px; padding: 15px; border: 1px solid #475569; text-align: center; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. جلب البيانات بأسرع طريقة ممكنة
@st.cache_data(ttl=0) # القيمة 0 تعني تحديث فوري وسرعة أكبر عند العودة
def load_quick_data():
    try:
        m = pd.read_csv(READ_M)
        l = pd.read_csv(READ_L)
        m.columns = [c.strip() for c in m.columns]
        l.columns = [c.strip() for c in l.columns]
        return m, l
    except:
        return pd.DataFrame(columns=["الاسم", "المسجد", "المرحلة الدراسية", "الفئة"]), pd.DataFrame(columns=["الاسم", "الفئة", "التاريخ"])

# القوائم
LEVELS = ["الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر", "جامعي"]
MOSQUES = ["شاهه العبيد", "اليوسفين", "العسعوسي", "السهو", "فاطمه الغلوم", "الصقعبي", "الرشيد", "الرومي"]
PASSWORDS = {"فئة أشبال السالمية": "Salmiya2026", "فئة أشبال حولي": "Hawally2026", "فئة الفتية": "Fetya2026", "فئة الشباب": "Shabab2026", "فئة الجامعيين": "Uni2026"}

st.markdown('<div class="main-header">📊 نظام مركز ابن عباس</div>', unsafe_allow_html=True)
df_m, df_l = load_quick_data()

target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))

tab1, tab2 = st.tabs(["👥 كشف الالتزام", "🔐 بوابة المشرف"])

with tab1:
    m_list = df_m[df_m['الفئة'] == target_cat] if not df_m.empty and 'الفئة' in df_m.columns else pd.DataFrame()
    l_list = df_l[df_l['الفئة'] == target_cat] if not df_l.empty and 'الفئة' in df_l.columns else pd.DataFrame()
    
    c1, c2 = st.columns(2)
    c1.markdown(f'<div class="card"><h3>📅 أيام النشاط</h3><h2>{len(l_list["التاريخ"].unique()) if not l_list.empty else 0}</h2></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card"><h3>👥 طلاب الفئة</h3><h2>{len(m_list)}</h2></div>', unsafe_allow_html=True)
    
    if not m_list.empty:
        st.write("### قائمة الطلاب:")
        st.dataframe(m_list[["الاسم", "المسجد", "المرحلة الدراسية"]], use_container_width=True, hide_index=True)

with tab2:
    pwd = st.text_input("كلمة المرور:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("مرحباً بك ✅")
        m_t1, m_t2, m_t3 = st.tabs(["📝 تسجيل حضور", "⚙️ إدارة الطلاب", "📊 التقارير"])
        
        with m_t1:
            if not m_list.empty:
                with st.form("quick_att"):
                    day = st.date_input("تاريخ اليوم")
                    st.write("ضع علامة صح بجانب أسماء الحاضرين:")
                    sel = []
                    # تحسين سرعة العرض هنا
                    student_names = sorted(m_list['الاسم'].unique())
                    for n in student_names:
                        if st.checkbox(n, key=f"chk_{n}"): sel.append(n)
                    
                    if st.form_submit_button("حفظ كشف الحضور"):
                        if sel:
                            recs = [{"name": n, "category": target_cat, "date": str(day)} for n in sel]
                            requests.post(API_URL, json={"action": "add_attendance", "records": recs})
                            st.success("تم تسجيل الحضور في جوجل شيت!")
                            st.rerun()
            else:
                st.info("لا يوجد طلاب مسجلين لعرضهم.")

        with m_t2:
            # قسم الإضافة والحذف بنفس المحاذاة لليمين
            st.subheader("إضافة طالب جديد")
            with st.form("add_student_fast"):
                n = st.text_input("اسم الطالب")
                m = st.selectbox("المسجد", MOSQUES)
                l = st.selectbox("المرحلة الدراسية", LEVELS)
                if st.form_submit_button("إضافة"):
                    requests.post(API_URL, json={"action": "add_student", "name": n, "mosque": m, "grade": l, "category": target_cat})
                    st.success("تمت الإضافة!"); st.rerun()
            
            st.divider()
            st.subheader("حذف طالب")
            names_to_del = sorted(m_list['الاسم'].unique().tolist()) if not m_list.empty else []
            d_n = st.selectbox("اختر الاسم المراد حذفه:", [""] + names_to_del)
            if st.button("تأكيد الحذف"):
                if d_n:
                    requests.post(API_URL, json={"action": "delete_student", "name": d_n, "category": target_cat})
                    st.error(f"تم حذف {d_n}"); st.rerun()

        with m_t3:
            # التقارير
            st.subheader("تحميل التقارير")
            d1 = st.date_input("من تاريخ", datetime.now())
            d2 = st.date_input("إلى تاريخ", datetime.now())
            if st.button("عرض ملخص الفترة"):
                mask = (df_l['الفئة'] == target_cat) & (df_l['التاريخ'] >= str(d1)) & (df_l['التاريخ'] <= str(d2))
                f_l = df_l[mask]
                res = []
                for _, r in m_list.iterrows():
                    c = len(f_l[f_l['الاسم'] == r['الاسم']])
                    res.append({"الاسم": r['الاسم'], "عدد أيام الحضور": c})
                st.table(pd.DataFrame(res))

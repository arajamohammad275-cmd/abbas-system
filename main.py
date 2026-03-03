import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. إعداد الصفحة وتنسيق المحاذاة لليمين
st.set_page_config(page_title="نظام ابن عباس الذكي", layout="centered")

# --- الروابط (تأكد من صحتها) ---
API_URL = "https://script.google.com/macros/s/AKfycbxwpiAyguMMZugESiw_QPiNA5t_MWr5YKqYOtwSoS_RfubNovE7QvRkhjmzr03dnIBtIA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
READ_M = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_L = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

# تنسيق الواجهة الاحترافية والمحاذاة لليمين
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .header-container { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 1.5rem; border-radius: 20px; border: 1px solid #334155; margin-bottom: 2rem; text-align: center !important; }
    .main-title { background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.2rem; font-weight: 800; text-align: center !important; }
    .metric-card { background: #1e293b; border-radius: 15px; padding: 1rem; border-right: 5px solid #3b82f6; text-align: center !important; margin-bottom: 1rem; }
    .stButton>button { border-radius: 12px; font-weight: 600; height: 3rem; width: 100%; background-color: #3b82f6 !important; color: white !important; }
    div[data-testid="stMarkdownContainer"] > p { text-align: right; }
    .stSelectbox, .stTextInput, .stCheckbox { direction: rtl !important; text-align: right !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظيفة جلب البيانات مع معالجة الأخطاء
@st.cache_data(ttl=0)
def fetch_secure_data():
    try:
        m = pd.read_csv(READ_M)
        l = pd.read_csv(READ_L)
        m.columns = [c.strip() for c in m.columns]
        l.columns = [c.strip() for c in l.columns]
        return m, l
    except Exception:
        # إذا فشل التحميل، ننشئ جداول فارغة بنفس العناوين المطلوبة
        return pd.DataFrame(columns=["الاسم", "المسجد", "المرحلة الدراسية", "الفئة"]), \
               pd.DataFrame(columns=["الاسم", "الفئة", "التاريخ"])

# القوائم
LEVELS = ["الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر", "جامعي"]
MOSQUES = ["شاهه العبيد", "اليوسفين", "العسعوسي", "السهو", "فاطمه الغلوم", "الصقعبي", "الرشيد", "الرومي"]
PASSWORDS = {"فئة أشبال السالمية": "Salmiya2026", "فئة أشبال حولي": "Hawally2026", "فئة الفتية": "Fetya2026", "فئة الشباب": "Shabab2026", "فئة الجامعيين": "Uni2026"}

st.markdown('<div class="header-container"><h1 class="main-title">مركز ابن عباس الذكي</h1></div>', unsafe_allow_html=True)

df_m, df_l = fetch_secure_data()
target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))

tab1, tab2 = st.tabs(["👥 كشف الالتزام والنسب", "🔐 بوابة المشرفين"])

# تصفية البيانات حسب الفئة المختارة بشكل آمن
if not df_m.empty and 'الفئة' in df_m.columns:
    m_list = df_m[df_m['الفئة'] == target_cat]
else:
    m_list = pd.DataFrame()

if not df_l.empty and 'الفئة' in df_l.columns:
    l_list = df_l[df_l['الفئة'] == target_cat]
else:
    l_list = pd.DataFrame()

# --- التبويب الأول: كشف الالتزام والنسبة المئوية ---
with tab1:
    total_days = len(l_list["التاريخ"].unique()) if not l_list.empty and "التاريخ" in l_list.columns else 0
    
    col1, col2 = st.columns(2)
    col1.markdown(f'<div class="metric-card"><p style="color:#38bdf8;">👥 طلاب الفئة</p><h2>{len(m_list)}</h2></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="metric-card"><p style="color:#fbbf24;">📅 أيام النشاط</p><h2>{total_days}</h2></div>', unsafe_allow_html=True)
    
    if not m_list.empty:
        stats = []
        for _, row in m_list.iterrows():
            attendance_count = len(l_list[l_list['الاسم'] == row['الاسم']]) if not l_list.empty else 0
            percentage = (attendance_count / total_days * 100) if total_days > 0 else 0
            stats.append({
                "الاسم": row['الاسم'],
                "المسجد": row['المسجد'],
                "المرحلة": row['المرحلة الدراسية'],
                "أيام الحضور": attendance_count,
                "نسبة الالتزام": f"{percentage:.1f}%"
            })
        st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد بيانات طلاب لهذه الفئة حالياً.")

# --- التبويب الثاني: بوابة المشرف ---
with tab2:
    pwd = st.text_input("🔑 كلمة المرور:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("تم الدخول بنجاح ✅")
        sub1, sub2, sub3 = st.tabs(["📝 تسجيل حضور", "⚙️ إدارة الطلاب", "📊 التقارير"])
        
        with sub1:
            if not m_list.empty:
                with st.form("attendance_final"):
                    today = st.date_input("🗓️ تاريخ اليوم")
                    st.write("اختر الحاضرين:")
                    selected = []
                    names = sorted(m_list['الاسم'].unique())
                    # حل مشكلة النموذج: وضع زر الإرسال قبل عرض الـ checkboxes
                    for n in names:
                        if st.checkbox(n, key=f"att_{n}"):
                            selected.append(n)
                    if st.form_submit_button("✅ حفظ كشف الحضور"):
                        if selected:
                            recs = [{"name": n, "category": target_cat, "date": str(today)} for n in selected]
                            requests.post(API_URL, json={"action": "add_attendance", "records": recs})
                            st.success("تم الحفظ بنجاح!"); st.rerun()
            else: st.warning("أضف طلاباً أولاً.")

        with sub2:
            st.subheader("➕ إضافة طالب")
            with st.form("add_form"):
                n = st.text_input("الاسم")
                m = st.selectbox("المسجد", MOSQUES)
                l = st.selectbox("المرحلة", LEVELS)
                if st.form_submit_button("إضافة"):
                    requests.post(API_URL, json={"action": "add_student", "name": n, "mosque": m, "grade": l, "category": target_cat})
                    st.success("تم!"); st.rerun()
            
            st.divider()
            st.subheader("🗑️ حذف طالب")
            names_del = sorted(m_list['الاسم'].tolist()) if not m_list.empty else []
            d_n = st.selectbox("اختر الاسم:", [""] + names_del)
            if st.button("حذف نهائي"):
                if d_n:
                    requests.post(API_URL, json={"action": "delete_student", "name": d_n, "category": target_cat})
                    st.error("تم الحذف"); st.rerun()

        with sub3:
            st.subheader("📊 التقارير")
            d1 = st.date_input("من", datetime.now())
            d2 = st.date_input("إلى", datetime.now())
            if st.button("عرض التقرير"):
                mask = (df_l['الفئة'] == target_cat) & (df_l['التاريخ'] >= str(d1)) & (df_l['التاريخ'] <= str(d2))
                f_l = df_l[mask]
                rep = [{"الاسم": r['الاسم'], "الحضور": len(f_l[f_l['الاسم'] == r['الاسم']])} for _, r in m_list.iterrows()]
                res_df = pd.DataFrame(rep)
                st.table(res_df)
                st.download_button("تحميل CSV", res_df.to_csv(index=False).encode('utf-8-sig'), "report.csv")

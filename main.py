import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام حضور الأنشطة", layout="centered")

# الروابط
API_URL = "https://script.google.com/macros/s/AKfycbxwpiAyguMMZugESiw_QPiNA5t_MWr5YKqYOtwSoS_RfubNovE7QvRkhjmzr03dnIBtIA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
READ_M = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_L = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

# 2. الواجهة الحديثة (Dark Mode & Gradient & Arabic Font)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    
    html, body, [class*="css"], .stApp { 
        font-family: 'Cairo', sans-serif !important; 
        direction: rtl !important; 
        text-align: right !important; 
    }
    .stApp { background-color: #0f172a; color: #f8fafc; }
    
    /* تصميم الهيدر الحديث */
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
    
    /* تصميم البطاقات الإحصائية */
    .metric-card {
        background: #1e293b; border-radius: 15px; padding: 1.5rem;
        border-right: 5px solid #38bdf8; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        text-align: center !important; margin-bottom: 1rem;
    }
    .metric-card h3 { color: #94a3b8; font-size: 1.2rem; margin-bottom: 10px; }
    .metric-card h2 { color: #f8fafc; font-size: 2.2rem; margin: 0; font-weight: bold; }

    /* محاذاة كافة المدخلات */
    div[data-testid="stMarkdownContainer"] > p { text-align: right !important; }
    .stTextInput input, .stSelectbox div, .stDateInput input { 
        text-align: right !important; direction: rtl !important; 
    }
    label { text-align: right !important; width: 100%; display: block !important; font-weight:bold; color: #e2e8f0; }

    /* الأزرار الحديثة */
    .stButton>button { 
        border-radius: 12px; background: linear-gradient(90deg, #3b82f6, #2563eb) !important;
        color: white !important; font-weight: bold; width: 100%; height: 3.5rem; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. جلب البيانات بأمان
@st.cache_data(ttl=0)
def fetch_data_secure():
    try:
        m = pd.read_csv(READ_M)
        l = pd.read_csv(READ_L)
        m.columns = [str(c).strip() for c in m.columns]
        l.columns = [str(c).strip() for c in l.columns]
        return m, l
    except:
        return pd.DataFrame(), pd.DataFrame()

# العنوان الرئيسي الجديد
st.markdown('<div class="header-box"><h1 class="main-title">نظام حضور الأنشطة</h1></div>', unsafe_allow_html=True)

df_m, df_l = fetch_data_secure()
PASSWORDS = {"فئة أشبال السالمية": "Salmiya2026", "فئة أشبال حولي": "Hawally2026", "فئة الفتية": "Fetya2026", "فئة الشباب": "Shabab2026", "فئة الجامعيين": "Uni2026"}

target_cat = st.selectbox("📂 اختر الفئة للإدارة:", list(PASSWORDS.keys()))
tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام والنسب", "🔐 بوابة المشرف"])

# تصفية البيانات
m_list = df_m[df_m['الفئة'] == target_cat] if not df_m.empty and 'الفئة' in df_m.columns else pd.DataFrame()
l_list = df_l[df_l['الفئة'] == target_cat] if not df_l.empty and 'الفئة' in df_l.columns else pd.DataFrame()

# --- التبويب الأول: الكشف مع النسبة المئوية ---
with tab_stats:
    if not m_list.empty:
        total_activity_days = len(l_list["التاريخ"].unique()) if not l_list.empty and "التاريخ" in l_list.columns else 0
        
        # البطاقات الإحصائية الحديثة
        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="metric-card"><h3>👥 إجمالي طلاب الفئة</h3><h2>{len(m_list)}</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><h3>📅 أيام النشاط</h3><h2>{total_activity_days}</h2></div>', unsafe_allow_html=True)
        
        st.write(f"### 📋 سجل الحضور التفصيلي")
        
        # حساب الحضور والنسبة المئوية
        display_df = m_list.copy()
        display_df['أيام الحضور'] = display_df['الاسم'].apply(lambda x: len(l_list[l_list['الاسم'] == x]) if not l_list.empty and 'الاسم' in l_list.columns else 0)
        display_df['النسبة المئوية'] = display_df['أيام الحضور'].apply(lambda x: f"{(x / total_activity_days * 100):.1f}%" if total_activity_days > 0 else "0%")
        
        # عرض الجدول
        st.dataframe(display_df[["الاسم", "المسجد", "أيام الحضور", "النسبة المئوية"]], use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد بيانات لهذه الفئة حالياً.")

# --- التبويب الثاني: بوابة المشرف (آمنة من الأخطاء) ---
with tab_admin:
    pwd = st.text_input("أدخل كلمة المرور لدخول المشرف:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("تم تسجيل الدخول بنجاح ✅")
        sub1, sub2 = st.tabs(["📝 تسجيل الحضور", "➕ إدارة الطلاب (إضافة/حذف)"])
        
        with sub1:
            if not m_list.empty:
                # زر الإرسال داخل الـ Form لمنع الخطأ الأحمر
                with st.form(key="attendance_form_secure", clear_on_submit=False):
                    st.write("### 📅 تاريخ اليوم:")
                    today = st.date_input("", datetime.now(), label_visibility="collapsed")
                    st.write("### 👥 اختر الحاضرين:")
                    selected = []
                    names = sorted(m_list['الاسم'].unique())
                    for n in names:
                        if st.checkbox(n, key=f"att_{n}"): selected.append(n)
                    
                    if st.form_submit_button("✅ اعتماد كشف الحضور"):
                        if selected:
                            recs = [{"name": n, "category": target_cat, "date": str(today)} for n in selected]
                            requests.post(API_URL, json={"action": "add_attendance", "records": recs})
                            st.success("تم تسجيل الحضور في جوجل شيت بنجاح!")
                            st.rerun()
                        else:
                            st.warning("الرجاء تحديد طالب واحد على الأقل.")
            else:
                st.warning("يرجى إضافة طلاب أولاً من تبويب إدارة الطلاب.")
        
        with sub2:
            # نموذج الإضافة (يمسح الخانات تلقائياً بعد الإضافة)
            with st.form(key="add_student_form_secure", clear_on_submit=True):
                st.write("### ➕ إضافة طالب جديد")
                name_in = st.text_input("الاسم الثلاثي")
                msq_in = st.selectbox("المسجد التابع له", ["شاهه العبيد", "اليوسفين", "العسعوسي", "السهو", "فاطمه الغلوم", "الصقعبي", "الرشيد", "الرومي"])
                lvl_in = st.selectbox("المرحلة الدراسية", ["الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر", "جامعي"])
                
                if st.form_submit_button("إضافة الطالب الآن"):
                    if name_in:
                        requests.post(API_URL, json={"action": "add_student", "name": name_in, "mosque": msq_in, "grade": lvl_in, "category": target_cat})
                        st.success(f"تمت إضافة {name_in} بنجاح!")
                    else: 
                        st.error("يرجى كتابة اسم الطالب أولاً")

            st.divider()
            st.write("### 🗑️ حذف طالب")
            del_n = st.selectbox("اختر الاسم المراد حذفه:", [""] + sorted(m_list['الاسم'].tolist()) if not m_list.empty else [""])
            if st.button("تأكيد الحذف النهائي"):
                if del_n:
                    requests.post(API_URL, json={"action": "delete_student", "name": del_n, "category": target_cat})
                    st.error(f"تم حذف {del_n} نهائياً.")
                    st.rerun()

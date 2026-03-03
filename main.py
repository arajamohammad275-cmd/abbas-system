import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. إعداد الصفحة والخطوط (بدون مكتبات إضافية لضمان التشغيل)
st.set_page_config(page_title="نظام مركز ابن عباس", layout="centered")

# الروابط الخاصة بك
API_URL = "https://script.google.com/macros/s/AKfycbxwpiAyguMMZugESiw_QPiNA5t_MWr5YKqYOtwSoS_RfubNovE7QvRkhjmzr03dnIBtIA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
READ_M = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_L = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

# 2. تنسيق CSS شامل للمحاذاة والخط
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    
    html, body, [class*="css"], .stApp { 
        font-family: 'Cairo', sans-serif !important; 
        direction: rtl !important; 
        text-align: right !important; 
    }
    .stApp { background-color: #0f172a; color: #ffffff; }
    
    /* تنسيق الهيدر */
    .header-text { 
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center !important; font-size: 32px; font-weight: 900; padding: 20px;
    }

    /* محاذاة كافة الحقول لليمين */
    div[data-testid="stMarkdownContainer"] > p { text-align: right !important; }
    .stTextInput input, .stSelectbox div, .stDateInput input { 
        text-align: right !important; direction: rtl !important; 
    }
    label { text-align: right !important; width: 100%; display: block !important; font-weight: bold !important; }

    /* تنسيق الأزرار */
    .stButton>button { 
        border-radius: 12px; background-color: #3b82f6 !important; 
        color: white !important; font-weight: bold; width: 100%; height: 3.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. وظيفة جلب البيانات
@st.cache_data(ttl=0)
def load_data_v3():
    try:
        m = pd.read_csv(READ_M)
        l = pd.read_csv(READ_L)
        m.columns = [str(c).strip() for c in m.columns]
        l.columns = [str(c).strip() for c in l.columns]
        return m, l
    except:
        return pd.DataFrame(), pd.DataFrame()

st.markdown('<div class="header-text">نظام مركز ابن عباس الذكي</div>', unsafe_allow_html=True)

df_m, df_l = load_data_v3()
PASSWORDS = {"فئة أشبال السالمية": "Salmiya2026", "فئة أشبال حولي": "Hawally2026", "فئة الفتية": "Fetya2026", "فئة الشباب": "Shabab2026", "فئة الجامعيين": "Uni2026"}

target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))

tab1, tab2 = st.tabs(["👥 كشف الطلاب", "🔐 الإدارة"])

m_list = df_m[df_m['الفئة'] == target_cat] if not df_m.empty and 'الفئة' in df_m.columns else pd.DataFrame()
l_list = df_l[df_l['الفئة'] == target_cat] if not df_l.empty and 'الفئة' in df_l.columns else pd.DataFrame()

# --- التبويب الأول: الكشف ---
with tab1:
    if not m_list.empty:
        st.write(f"### سجل حضور {target_cat}")
        display_df = m_list.copy()
        display_df['أيام الحضور'] = display_df['الاسم'].apply(lambda x: len(l_list[l_list['الاسم'] == x]) if not l_list.empty else 0)
        st.dataframe(display_df[["الاسم", "المسجد", "أيام الحضور"]], use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد أسماء مسجلة حالياً.")

# --- التبويب الثاني: الإدارة ---
with tab2:
    pwd = st.text_input("أدخل كلمة المرور لدخول المشرف:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("تم الدخول بنجاح ✅")
        sub1, sub2 = st.tabs(["📝 تسجيل الحضور", "➕ إضافة وحذف"])
        
        with sub1:
            if not m_list.empty:
                # الفورم هنا يحتوي على زر الإرسال بالداخل إجبارياً
                with st.form(key="attendance_fixed_form"):
                    st.write("تاريخ اليوم:")
                    today = st.date_input("", datetime.now(), label_visibility="collapsed")
                    st.write("اختر الحاضرين:")
                    selected = []
                    names = sorted(m_list['الاسم'].unique())
                    for n in names:
                        if st.checkbox(n, key=f"p_{n}"): selected.append(n)
                    
                    if st.form_submit_button("✅ حفظ الكشف"):
                        if selected:
                            recs = [{"name": n, "category": target_cat, "date": str(today)} for n in selected]
                            requests.post(API_URL, json={"action": "add_attendance", "records": recs})
                            st.success("تم تسجيل الحضور بنجاح")
                            st.rerun()
            else: st.warning("أضف طلاباً أولاً")

        with sub2:
            # استخدام clear_on_submit لمسح الخانات بعد الإضافة
            with st.form(key="add_student_fixed", clear_on_submit=True):
                st.write("### إضافة اسم جديد")
                name_in = st.text_input("اسم الطالب")
                msq_in = st.selectbox("المسجد", ["شاهه العبيد", "اليوسفين", "العسعوسي", "السهو", "فاطمه الغلوم", "الصقعبي", "الرشيد", "الرومي"])
                lvl_in = st.selectbox("المرحلة", ["الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر", "جامعي"])
                
                if st.form_submit_button("إضافة الآن"):
                    if name_in:
                        requests.post(API_URL, json={"action": "add_student", "name": name_in, "mosque": msq_in, "grade": lvl_in, "category": target_cat})
                        st.success(f"تمت إضافة {name_in}")
                        # لا حاجة لـ rerun هنا لأن clear_on_submit سيمسح النص تلقائياً
                    else: st.error("يرجى كتابة الاسم")

            st.divider()
            st.write("### حذف اسم")
            del_n = st.selectbox("اختر الاسم:", [""] + sorted(m_list['الاسم'].tolist()) if not m_list.empty else [""])
            if st.button("حذف نهائي"):
                if del_n:
                    requests.post(API_URL, json={"action": "delete_student", "name": del_n, "category": target_cat})
                    st.error("تم الحذف")
                    st.rerun()

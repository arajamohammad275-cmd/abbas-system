import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="نظام ابن عباس", layout="centered", initial_sidebar_state="collapsed")

# --- الروابط (تأكد من صحتها) ---
API_URL = "https://script.google.com/macros/s/AKfycbxwpiAyguMMZugESiw_QPiNA5t_MWr5YKqYOtwSoS_RfubNovE7QvRkhjmzr03dnIBtIA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
READ_M = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_L = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

# 2. تصميم الواجهة الاحترافي (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #0f172a; color: #f8fafc; }
    
    /* الهيدر */
    .header-container {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 2rem; border-radius: 20px; border: 1px solid #334155;
        margin-bottom: 2rem; text-align: center !important;
    }
    .main-title { 
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 2.5rem; font-weight: 800; margin: 0; text-align: center !important;
    }
    
    /* البطاقات الإحصائية */
    .metric-card {
        background: #1e293b; border-radius: 15px; padding: 1.5rem;
        border-right: 5px solid #3b82f6; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        text-align: center !important; margin: 10px 0;
    }
    
    /* الأزرار */
    .stButton>button {
        border-radius: 12px; font-weight: 600; transition: all 0.3s;
        border: none; height: 3.5rem; width: 100%;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.5); }
    
    /* التبويبات */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b; border-radius: 10px; padding: 10px 20px; color: white;
    }
    .stTabs [aria-selected="true"] { background-color: #3b82f6 !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. وظائف جلب البيانات
@st.cache_data(ttl=0)
def fetch_data():
    try:
        m = pd.read_csv(READ_M); l = pd.read_csv(READ_L)
        m.columns = [c.strip() for c in m.columns]
        l.columns = [c.strip() for c in l.columns]
        return m, l
    except:
        return pd.DataFrame(columns=["الاسم", "المسجد", "المرحلة الدراسية", "الفئة"]), pd.DataFrame(columns=["الاسم", "الفئة", "التاريخ"])

# القوائم
LEVELS = ["الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر", "جامعي"]
MOSQUES = ["شاهه العبيد", "اليوسفين", "العسعوسي", "السهو", "فاطمه الغلوم", "الصقعبي", "الرشيد", "الرومي"]
PASSWORDS = {"فئة أشبال السالمية": "Salmiya2026", "فئة أشبال حولي": "Hawally2026", "فئة الفتية": "Fetya2026", "فئة الشباب": "Shabab2026", "فئة الجامعيين": "Uni2026"}

# --- بداية محتوى الصفحة ---
st.markdown('<div class="header-container"><h1 class="main-title">مركز ابن عباس الذكي</h1><p style="color:#94a3b8;">نظام إدارة الحضور والأنشطة</p></div>', unsafe_allow_html=True)

df_m, df_l = fetch_data()
target_cat = st.selectbox("📂 اختر الفئة للإدارة أو العرض:", list(PASSWORDS.keys()))

tab_main, tab_admin = st.tabs(["📊 كشف الالتزام العام", "🔐 بوابة المشرفين"])

# --- التبويب الأول: عرض البيانات ---
with tab_main:
    m_list = df_m[df_m['الفئة'] == target_cat] if not df_m.empty and 'الفئة' in df_m.columns else pd.DataFrame()
    l_list = df_l[df_l['الفئة'] == target_cat] if not df_l.empty and 'الفئة' in df_l.columns else pd.DataFrame()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="metric-card"><p style="margin:0;color:#38bdf8;">👥 عدد الطلاب</p><h2>{len(m_list)}</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><p style="margin:0;color:#fbbf24;">📅 أيام النشاط</p><h2>{len(l_list["التاريخ"].unique()) if not l_list.empty else 0}</h2></div>', unsafe_allow_html=True)
    
    st.markdown("### 📋 قائمة الطلاب والالتزام")
    if not m_list.empty:
        st.dataframe(m_list[["الاسم", "المسجد", "المرحلة الدراسية"]], use_container_width=True, hide_index=True)
    else:
        st.info("لا يوجد طلاب مسجلين في هذه الفئة حالياً.")

# --- التبويب الثاني: بوابة المشرف ---
with tab_admin:
    pwd = st.text_input("🔑 أدخل كلمة مرور الفئة للدخول:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success(f"أهلاً بك مشرف {target_cat} ✅")
        
        m_tabs = st.tabs(["📝 تسجيل الحضور", "⚙️ إدارة الطلاب", "📥 التقارير"])
        
        # 1. تسجيل الحضور
        with m_tabs[0]:
            if not m_list.empty:
                with st.form("attendance_form"):
                    today = st.date_input("🗓️ تاريخ اليوم")
                    st.write("اختر الطلاب الحاضرين:")
                    selected = []
                    names = sorted(m_list['الاسم'].unique())
                    # عرض الأسماء في أعمدة لتوفير المساحة
                    cols = st.columns(2)
                    for i, name in enumerate(names):
                        with cols[i % 2]:
                            if st.checkbox(name, key=f"att_{name}"): selected.append(name)
                    
                    if st.form_submit_button("✅ اعتماد الحفظ"):
                        if selected:
                            recs = [{"name": n, "category": target_cat, "date": str(today)} for n in selected]
                            requests.post(API_URL, json={"action": "add_attendance", "records": recs})
                            st.balloons()
                            st.success("تم الحفظ بنجاح!"); st.rerun()
            else: st.warning("يجب إضافة طلاب أولاً من تبويب الإدارة.")

        # 2. إدارة الطلاب
        with m_tabs[1]:
            col_add, col_del = st.columns(2)
            with col_add:
                st.subheader("➕ إضافة طالب")
                with st.form("add_student"):
                    n = st.text_input("الاسم الثلاثي")
                    m = st.selectbox("المسجد", MOSQUES)
                    l = st.selectbox("المرحلة", LEVELS)
                    if st.form_submit_button("إضافة"):
                        requests.post(API_URL, json={"action": "add_student", "name": n, "mosque": m, "grade": l, "category": target_cat})
                        st.success("تمت الإضافة!"); st.rerun()
            
            with col_del:
                st.subheader("🗑️ حذف طالب")
                names_del = sorted(m_list['الاسم'].tolist()) if not m_list.empty else []
                d_n = st.selectbox("اختر الاسم المراد حذفه:", [""] + names_del)
                if st.button("تأكيد الحذف النهائي", type="secondary"):
                    if d_n:
                        requests.post(API_URL, json={"action": "delete_student", "name": d_n, "category": target_cat})
                        st.error(f"تم حذف {d_n}"); st.rerun()

        # 3. التقارير
        with m_tabs[2]:
            st.subheader("📊 استخراج تقارير إكسل")
            d1, d2 = st.columns(2)
            date_from = d1.date_input("من تاريخ", datetime.now())
            date_to = d2.date_input("إلى تاريخ", datetime.now())
            
            if st.button("🔍 عرض ملخص الفترة"):
                mask = (df_l['الفئة'] == target_cat) & (df_l['التاريخ'] >= str(date_from)) & (df_l['التاريخ'] <= str(date_to))
                filtered_logs = df_l[mask]
                
                report_data = []
                for _, student in m_list.iterrows():
                    count = len(filtered_logs[filtered_logs['الاسم'] == student['الاسم']])
                    report_data.append({"الاسم": student['الاسم'], "الحضور": count})
                
                res_df = pd.DataFrame(report_data)
                st.table(res_df)
                csv = res_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 تحميل ملف التقرير", csv, f"تقرير_{target_cat}.csv", "text/csv")

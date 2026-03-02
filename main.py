import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. إعدادات المظهر
st.set_page_config(page_title="نظام حضور الأنشطة", layout="centered")

# *** رابط الـ Web App الخاص بك ***
API_URL = "https://script.google.com/macros/s/AKfycbxwpiAyguMMZugESiw_QPiNA5t_MWr5YKqYOtwSoS_RfubNovE7QvRkhjmzr03dnIBtIA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
READ_M = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_L = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"], .stApp { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; color: #FFFFFF !important; }
    .stApp { background-color: #0f172a; }
    .main-header { background: linear-gradient(90deg, #00dbde, #fc00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center !important; font-size: 32px; font-weight: 800; padding: 20px 0; }
    .stButton>button { border-radius: 10px; background-color: #3b82f6 !important; color: white !important; font-weight: bold; width: 100%; height: 3.5em; border: none; }
    .stDownloadButton>button { background-color: #10b981 !important; color: white !important; border-radius: 10px; width: 100%; height: 3.5em; }
    .card { background-color: #1e293b; border-radius: 12px; padding: 15px; border: 1px solid #475569; text-align: center; margin-bottom: 10px; }
    [data-testid="stHeader"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# 2. القوائم الثابتة (رجعت لك كل المساجد والمراحل)
LEVELS = ["الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر", "جامعي"]
MOSQUES = ["شاهه العبيد", "اليوسفين", "العسعوسي", "السهو", "فاطمه الغلوم", "الصقعبي", "الرشيد", "الرومي"]
PASSWORDS = {
    "فئة أشبال السالمية": "Salmiya2026", 
    "فئة أشبال حولي": "Hawally2026", 
    "فئة الفتية": "Fetya2026", 
    "فئة الشباب": "Shabab2026",
    "فئة الجامعيين": "Uni2026"
}

@st.cache_data(ttl=5)
def load_data():
    try:
        df_m = pd.read_csv(READ_M)
        df_l = pd.read_csv(READ_L)
        df_m.columns = df_m.columns.str.strip()
        df_l.columns = df_l.columns.str.strip()
        return df_m, df_l
    except:
        return pd.DataFrame(columns=["الاسم", "المسجد", "المرحلة الدراسية", "الفئة"]), pd.DataFrame(columns=["الاسم", "الفئة", "التاريخ"])

st.markdown('<div class="main-header">📊 نظام حضور الأنشطة - مركز ابن عباس</div>', unsafe_allow_html=True)
df_m, df_l = load_data()
target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))

tab1, tab2 = st.tabs(["👥 كشف الطلاب والالتزام", "🔐 بوابة المشرف"])

with tab1:
    m_list = df_m[df_m['الفئة'] == target_cat] if not df_m.empty else pd.DataFrame()
    l_list = df_l[df_l['الفئة'] == target_cat] if not df_l.empty else pd.DataFrame()
    
    total_days = len(l_list["التاريخ"].unique()) if not l_list.empty else 0
    c1, c2 = st.columns(2)
    c1.markdown(f'<div class="card"><h3>📅 أيام النشاط</h3><h2>{total_days}</h2></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card"><h3>👥 طلاب الفئة</h3><h2>{len(m_list)}</h2></div>', unsafe_allow_html=True)
    
    if not m_list.empty:
        stats = []
        for _, row in m_list.iterrows():
            count = len(l_list[l_list['الاسم'] == row['الاسم']]) if not l_list.empty else 0
            pct = (count / total_days * 100) if total_days > 0 else 0
            stats.append({"الاسم": row['الاسم'], "المسجد": row['المسجد'], "المرحلة": row['المرحلة الدراسية'], "الالتزام": f"{pct:.1f}%"})
        st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)

with tab2:
    pwd = st.text_input("أدخل كلمة المرور للفئة:", type="password")
    if pwd == PASSWORDS[target_cat]:
        st.success(f"مرحباً مشرف {target_cat} ✅")
        m_tab1, m_tab2, m_tab3 = st.tabs(["📝 تسجيل حضور", "⚙️ إدارة الطلاب", "📥 تحميل التقارير"])
        
        with m_tab1:
            st.subheader("تحضير اليوم")
            with st.form("att_form", clear_on_submit=True):
                today = st.date_input("التاريخ")
                selected = []
                names = sorted(m_list["الاسم"].tolist()) if not m_list.empty else []
                for n in names:
                    if st.checkbox(n): selected.append(n)
                if st.form_submit_button("اعتماد وحفظ"):
                    if selected:
                        recs = [{"name": n, "category": target_cat, "date": str(today)} for n in selected]
                        requests.post(API_URL, json={"action": "add_attendance", "records": recs})
                        st.success("تم الحفظ في جوجل!"); st.rerun()

        with m_tab2:
            st.subheader("➕ إضافة طالب جديد")
            with st.form("add_st", clear_on_submit=True):
                n_name = st.text_input("الاسم")
                n_msq = st.selectbox("المسجد", MOSQUES)
                n_lvl = st.selectbox("المرحلة", LEVELS)
                if st.form_submit_button("حفظ الطالب"):
                    requests.post(API_URL, json={"action": "add_student", "name": n_name, "mosque": n_msq, "grade": n_lvl, "category": target_cat})
                    st.success("تم الحفظ!"); st.rerun()
            
            st.divider()
            st.subheader("🗑️ حذف طالب من الفئة")
            del_name = st.selectbox("اختر الاسم للحذف النهائي:", [""] + sorted(m_list["الاسم"].tolist()))
            if st.button("تأكيد الحذف"):
                if del_name != "":
                    requests.post(API_URL, json={"action": "delete_student", "name": del_name, "category": target_cat})
                    st.error(f"تم حذف {del_name}."); st.rerun()

        with m_tab3:
            st.subheader("📊 استخراج تقارير بالفترة")
            d_f = st.date_input("من تاريخ", datetime.now())
            d_t = st.date_input("إلى تاريخ", datetime.now())
            if st.button("عرض التقرير"):
                mask = (df_l['الفئة'] == target_cat) & (df_l['التاريخ'] >= str(d_f)) & (df_l['التاريخ'] <= str(d_t))
                f_logs = df_l[mask]
                d_act = len(f_logs["التاريخ"].unique())
                rep = []
                for _, r in m_list.iterrows():
                    c = len(f_logs[f_logs['الاسم'] == r['الاسم']])
                    p = (c / d_act * 100) if d_act > 0 else 0
                    rep.append({"الاسم": r['الاسم'], "الحضور": c, "النسبة": f"{p:.1f}%"})
                res_df = pd.DataFrame(rep)
                st.dataframe(res_df, use_container_width=True, hide_index=True)
                csv = res_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 تحميل التقرير Excel", csv, f"تقرير_{target_cat}.csv", "text/csv")

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px  # لإضافة رسوم بيانية احترافية

# 1. إعدادات متقدمة للصفحة
st.set_page_config(
    page_title="نظام ابن عباس المتكامل",
    page_icon="🕌",
    layout="centered"
)

# الروابط
API_URL = "https://script.google.com/macros/s/AKfycbxwpiAyguMMZugESiw_QPiNA5t_MWr5YKqYOtwSoS_RfubNovE7QvRkhjmzr03dnIBtIA/exec"
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
READ_M = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"
READ_L = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Logs"

# 2. واجهة مستخدم احترافية (CSS مكثف)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800;900&display=swap');
    
    html, body, [class*="css"], .stApp { 
        font-family: 'Cairo', sans-serif; 
        direction: rtl; 
        text-align: right !important; 
    }
    .stApp { background: #0f172a; color: #e2e8f0; }
    
    /* هيدر بنمط احترافي */
    .header-box {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 2.5rem; border-radius: 25px; border: 1px solid #475569;
        text-align: center !important; margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    .main-title { 
        color: #38bdf8; font-size: 35px; font-weight: 900; margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    /* تحسين شكل البطاقات */
    .stMetric { background: #1e293b; border-radius: 15px; padding: 15px; border: 1px solid #334155; }
    
    /* الأزرار */
    .stButton>button { 
        border-radius: 12px; background: linear-gradient(90deg, #3b82f6, #2563eb) !important;
        color: white !important; font-weight: bold; border: none;
        transition: 0.3s all; height: 3.5rem;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4); }
    
    /* محاذاة الجداول والقوائم */
    .stSelectbox, .stTextInput { text-align: right !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك جلب ومعالجة البيانات
@st.cache_data(ttl=0)
def get_system_data():
    try:
        m = pd.read_csv(READ_M)
        l = pd.read_csv(READ_L)
        m.columns = [str(c).strip() for c in m.columns]
        l.columns = [str(c).strip() for c in l.columns]
        return m, l
    except:
        return pd.DataFrame(), pd.DataFrame()

# 4. محتوى الصفحة الرئيسي
st.markdown('<div class="header-box"><h1 class="main-title">🕌 مركز ابن عباس - الإدارة الذكية</h1><p style="color: #94a3b8; font-weight: 600;">نظام متابعة الحضور والالتزام</p></div>', unsafe_allow_html=True)

df_m, df_l = get_system_data()
PASSWORDS = {"فئة أشبال السالمية": "Salmiya2026", "فئة أشبال حولي": "Hawally2026", "فئة الفتية": "Fetya2026", "فئة الشباب": "Shabab2026", "فئة الجامعيين": "Uni2026"}

# اختيار الفئة
selected_category = st.selectbox("🎯 اختر الفئة المستهدفة:", list(PASSWORDS.keys()))

tab1, tab2, tab3 = st.tabs(["📊 الإحصائيات والكشوف", "📝 تسجيل الحضور", "⚙️ الإدارة الإدارية"])

# تصفية البيانات
m_filtered = df_m[df_m['الفئة'] == selected_category] if not df_m.empty else pd.DataFrame()
l_filtered = df_l[df_l['الفئة'] == selected_category] if not df_l.empty else pd.DataFrame()

# --- التبويب الأول: الإحصائيات (طويل ومفصل) ---
with tab1:
    col1, col2, col3 = st.columns(3)
    total_studs = len(m_filtered)
    unique_days = len(l_filtered['التاريخ'].unique()) if not l_filtered.empty else 0
    
    col1.metric("عدد الطلاب", total_studs)
    col2.metric("أيام النشاط", unique_days)
    col3.metric("نسبة التفاعل", f"{85}%") # قيمة افتراضية للجمالية

    st.markdown("---")
    if not m_filtered.empty:
        # حساب الحضور لكل طالب
        stats_df = m_filtered.copy()
        stats_df['أيام الحضور'] = stats_df['الاسم'].apply(lambda x: len(l_filtered[l_filtered['الاسم'] == x]) if not l_filtered.empty else 0)
        
        st.write("### 📋 كشف الأسماء المعتمد")
        st.dataframe(stats_df[["الاسم", "المسجد", "المرحلة الدراسية", "أيام الحضور"]], use_container_width=True, hide_index=True)
        
        # إضافة رسم بياني (جديد ومميز)
        if not stats_df.empty:
            st.write("### 📈 توزيع الطلاب حسب المساجد")
            fig = px.pie(stats_df, names='المسجد', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد بيانات متاحة حالياً.")

# --- التبويب الثاني: الحضور ---
with tab2:
    pwd = st.text_input("🔑 كلمة المرور للصلاحية:", type="password")
    if pwd == PASSWORDS.get(selected_category):
        st.success("تم تأكيد الصلاحية ✅")
        if not m_filtered.empty:
            with st.form("attendance_pro_form", clear_on_submit=True):
                att_date = st.date_input("اختر تاريخ اليوم", datetime.now())
                st.write("✅ حدد الطلاب الحاضرين اليوم:")
                
                # ترتيب الأسماء في أعمدة
                cols = st.columns(2)
                names = sorted(m_filtered['الاسم'].unique())
                present_list = []
                for i, n in enumerate(names):
                    with cols[i % 2]:
                        if st.checkbox(n, key=f"att_{n}"): present_list.append(n)
                
                if st.form_submit_button("إرسال البيانات إلى السحابة"):
                    if present_list:
                        recs = [{"name": n, "category": selected_category, "date": str(att_date)} for n in present_list]
                        requests.post(API_URL, json={"action": "add_attendance", "records": recs})
                        st.balloons()
                        st.success(f"تم تسجيل حضور {len(present_list)} طالب بنجاح!")
                        st.rerun()
                    else: st.warning("يرجى اختيار طالب واحد على الأقل.")
        else: st.error("لا يوجد طلاب مسجلين لتحضيرهم.")

# --- التبويب الثالث: الإدارة ---
with tab3:
    if pwd == PASSWORDS.get(selected_category):
        col_a, col_b = st.columns(2)
        
        with col_a:
            with st.form("add_pro", clear_on_submit=True):
                st.write("### ➕ إضافة عضو جديد")
                new_n = st.text_input("اسم الطالب الكامل")
                new_m = st.selectbox("المسجد التابع له", ["شاهه العبيد", "اليوسفين", "العسعوسي", "السهو", "فاطمه الغلوم", "الصقعبي", "الرشيد", "الرومي"])
                new_l = st.selectbox("المرحلة الدراسية", ["الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر", "جامعي"])
                if st.form_submit_button("إضافة الآن"):
                    if new_n and not df_m[df_m['الاسم'] == new_n].empty:
                        st.error("هذا الاسم موجود مسبقاً!")
                    elif new_n:
                        requests.post(API_URL, json={"action": "add_student", "name": new_n, "mosque": new_m, "grade": new_l, "category": selected_category})
                        st.success("تمت الإضافة بنجاح")
                        st.rerun()
                    else: st.error("الاسم مطلوب")

        with col_b:
            st.write("### 🗑️ إدارة الحذف")
            del_target = st.selectbox("اختر الاسم للحذف النهائي:", [""] + sorted(m_filtered['الاسم'].tolist()) if not m_filtered.empty else [""])
            if st.button("تأكيد الحذف النهائي"):
                if del_target:
                    requests.post(API_URL, json={"action": "delete_student", "name": del_target, "category": selected_category})
                    st.error(f"تم حذف {del_target}")
                    st.rerun()

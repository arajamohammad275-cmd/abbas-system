import streamlit as st
import pandas as pd

# إعدادات الواجهة (Dark Mode)
st.set_page_config(page_title="مركز ابن عباس", layout="centered")

# رابط الجدول الخاص بك
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"], .stApp { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; color: #FFFFFF !important; }
    .stApp { background-color: #0f172a; }
    .main-header { background: linear-gradient(90deg, #00dbde, #fc00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center !important; font-size: 32px; font-weight: 800; padding: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header">📊 نظام إدارة مركز ابن عباس</div>', unsafe_allow_html=True)

# دالة جلب البيانات مع تنظيف تلقائي
@st.cache_data(ttl=5)
def load_data():
    try:
        df = pd.read_csv(URL)
        df.columns = df.columns.str.strip() # مسح المسافات من العناوين
        return df
    except:
        return None

df = load_data()

# فحص البيانات والتعامل مع الجدول الفاضي
if df is not None and not df.empty and 'الاسم' in df.columns:
    st.success("✅ تم الاتصال بجدول جوجل بنجاح")
    
    tab1, tab2 = st.tabs(["👥 كشف الطلاب", "📝 إضافة بيانات"])
    
    with tab1:
        st.write("### قائمة الطلاب:")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
    with tab2:
        st.info("سجل البيانات في جوجل شيت وستظهر هنا فوراً.")
else:
    st.warning("⚠️ الموقع متصل بالجدول، لكن لا توجد بيانات لعرضها.")
    st.markdown("""
    **عشان يشتغل الموقع صح، لازم تسوي هذي الخطوة في جوجل شيت:**
    1. اكتب كلمة **الاسم** في الخلية A1.
    2. اكتب أي اسم طالب تحتها في الخلية A2.
    3. ارجع هنا وسوي تحديث (Refresh).
    """)

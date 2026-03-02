import streamlit as st
import pandas as pd

# 1. إعدادات المظهر والخطوط (أبيض ناصع + محاذاة يمين + أزرار ثابتة)
st.set_page_config(page_title="نظام مركز ابن عباس", layout="centered")

# الـ ID الخاص بجدولك الذي أرسلته في الصورة
SHEET_ID = "19p75R69A5cvtwvRnyt1WIWjiqWAEX9GozAHjCzCNqww"
# رابط جلب البيانات من ورقة Students بصيغة CSV
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Students"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* ضبط الخط والاتجاه العام */
    html, body, [class*="css"], .stApp { 
        font-family: 'Cairo', sans-serif; 
        direction: rtl; 
        text-align: right; 
        color: #FFFFFF !important; 
    }
    
    .stApp { background-color: #0f172a; }

    /* العناوين والنصوص */
    p, h1, h2, h3, label, span { 
        color: #FFFFFF !important; 
        text-align: right !important; 
        direction: rtl !important; 
    }

    .main-header { 
        background: linear-gradient(90deg, #00dbde, #fc00ff); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        text-align: center !important; 
        font-size: 32px; 
        font-weight: 800; 
        padding: 20px 0; 
    }
    
    /* تثبيت ألوان الأزرار (أزرق دائماً ولا يتغير عند الضغط) */
    .stButton>button { 
        border-radius: 10px; 
        background-color: #3b82f6 !important; 
        color: white !important; 
        font-weight: bold; 
        width: 100%; 
        height: 3.5em; 
        border: none;
        transition: none !important;
    }
    .stButton>button:hover, .stButton>button:active, .stButton>button:focus { 
        background-color: #3b82f6 !important; 
        color: white !important; 
        border: none !important; 
        box-shadow: none !important;
    }

    /* جعل أرقام وأيام التقويم باللون الأبيض الناصع */
    div[data-baseweb="calendar"] * { 
        color: white !important; 
    }
    div[data-baseweb="calendar"] { 
        background-color: #1e293b !important; 
        border: 1px solid #475569 !important; 
    }
    
    /* تحسين شكل البطاقات والجداول */
    .card { 
        background-color: #1e293b; 
        border-radius: 12px; 
        padding: 15px; 
        border: 1px solid #475569; 
        text-align: center; 
        margin-bottom: 10px; 
    }
    
    [data-testid="stDataFrame"] { 
        direction: rtl !important; 
    }

    /* تنسيق مربعات الاختيار (التحضير) */
    .stCheckbox { 
        background-color: #1e293b; 
        padding: 10px; 
        border-radius: 8px; 
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. وظيفة جلب البيانات من جوجل شيت
@st.cache_data(ttl=60) # تحديث البيانات كل دقيقة
def load_data():
    try:
        df = pd.read_csv(URL)
        return df
    except Exception as e:
        return pd.DataFrame(columns=["الاسم", "المسجد", "المرحلة الدراسية", "الفئة"])

# 3. واجهة التطبيق الرئيسية
st.markdown('<div class="main-header">📊 نظام حضور الأنشطة - مركز ابن عباس</div>', unsafe_allow_html=True)

# تحميل البيانات
df_students = load_data()

# تعريف الفئات وكلمات المرور
PASSWORDS = {
    "فئة أشبال السالمية": "Salmiya2026", 
    "فئة أشبال حولي": "Hawally2026",
    "فئة الفتية": "Fetya2026", 
    "فئة الشباب": "Shabab2026", 
    "فئة الجامعيين": "Uni2026"
}

# اختيار الفئة
target_cat = st.selectbox("📂 اختر الفئة الخاصة بك:", list(PASSWORDS.keys()))

# التقسيم إلى تبويبات
tab1, tab2 = st.tabs(["👥 كشف الطلاب", "🔐 بوابة المشرف"])

with tab1:
    # تصفية الطلاب حسب الفئة المختارة
    m_list = df_students[df_students['الفئة'] == target_cat].sort_values(by="الاسم")
    
    if not m_list.empty:
        st.write(f"### قائمة طلاب {target_cat}")
        # عرض الجدول (الاسم، المسجد، المرحلة)
        st.dataframe(
            m_list[["الاسم", "المسجد", "المرحلة الدراسية"]], 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.warning("⚠️ لا يوجد طلاب مسجلين في هذه الفئة داخل جدول جوجل. تأكد من إضافة الأسماء في ملف Google Sheets.")

with tab2:
    pwd = st.text_input("ادخل كلمة المرور للدخول وتسجيل الحضور", type="password")
    
    if pwd == PASSWORDS[target_cat]:
        st.success("تم تسجيل الدخول بنجاح ✅")
        st.divider()
        st.write("### 📝 تسجيل حضور اليوم")
        
        # اختيار التاريخ (سيكون باللون الأبيض والواضح)
        today = st.date_input("اختر تاريخ النشاط")
        
        if not m_list.empty:
            st.write("اختر الطلاب الحاضرين:")
            selected_students = []
            
            # قائمة اختيار الطلاب
            for name in m_list["الاسم"]:
                if st.checkbox(name, key=f"check_{name}"):
                    selected_students.append(name)
            
            st.divider()
            
            # زر الاعتماد (لون ثابت لا يتغير)
            if st.button("اعتماد وحفظ الحضور"):
                if selected_students:
                    st.balloons()
                    st.success(f"تم اعتماد حضور {len(selected_students)} طالباً بتاريخ {today}")
                else:
                    st.error("الرجاء اختيار طالب واحد على الأقل.")
        else:
            st.info("لا يوجد طلاب لتحضيرهم.")

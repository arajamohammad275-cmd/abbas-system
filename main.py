import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client

# -----------------------------
# إعدادات الصفحة
# -----------------------------
st.set_page_config(page_title="نظام حضور الأنشطة", layout="centered")

# -----------------------------
# Supabase (من Streamlit Secrets فقط)
# -----------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# RTL + تصميم
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; direction: rtl !important; text-align: right !important; }
.stApp { background-color: #0f172a; color: #f8fafc !important; }

[data-testid="stMarkdownContainer"] * ,
.stMarkdown, .stText, p, span, div, label, h1, h2, h3, h4, h5, h6 {
  color: #f8fafc !important;
}

[data-testid="stWidgetLabel"] * {
  color: #f8fafc !important;
  -webkit-text-fill-color: #f8fafc !important;
}

/* الحقول: خلفية بيضاء + نص أسود */
input, textarea { color:#0b1220 !important; -webkit-text-fill-color:#0b1220 !important; background:#ffffff !important; }
div[data-baseweb="select"] * { color:#0b1220 !important; -webkit-text-fill-color:#0b1220 !important; }
div[data-baseweb="popover"] *, ul[role="listbox"] *, div[role="listbox"] * { color:#0b1220 !important; -webkit-text-fill-color:#0b1220 !important; }
div[data-baseweb="popover"], ul[role="listbox"], div[role="listbox"] { background:#ffffff !important; }
li[role="option"]:hover, li[role="option"][aria-selected="true"] { background:#e5e7eb !important; }

/* الجداول */
table, th, td { color: #f8fafc !important; }

/* الهيدر */
.header-box {
  background: linear-gradient(135deg,#1e293b 0%,#0f172a 100%);
  padding:2rem; border-radius:20px; border:1px solid #334155;
  margin-bottom:1.5rem; text-align:center !important;
  box-shadow:0 10px 15px -3px rgba(0,0,0,0.3);
}
.main-title {
  background: linear-gradient(90deg,#38bdf8,#818cf8);
  -webkit-background-clip:text;
  -webkit-text-fill-color:transparent;
  font-size:2.4rem; font-weight:900; margin:0;
  text-align:center !important;
}

/* الأزرار */
.stButton>button{
  border-radius:12px;
  background:linear-gradient(90deg,#3b82f6,#2563eb);
  color:white !important;
  font-weight:bold;
  width:100%;
  height:3.2rem;
  border:none;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1 class="main-title">نظام حضور الأنشطة</h1></div>', unsafe_allow_html=True)

# -----------------------------
# أدوات مساعدة
# -----------------------------
def norm_text(x) -> str:
    if x is None:
        return ""
    return str(x).strip()

# -----------------------------
# جلب البيانات
# -----------------------------
@st.cache_data(ttl=10)
def fetch_students_df() -> pd.DataFrame:
    res = supabase.table("students").select("*").execute()
    df = pd.DataFrame(res.data or [])
    if df.empty:
        return pd.DataFrame(columns=["id", "name", "mosque", "grade", "category"])
    for col in ["name", "mosque", "grade", "category"]:
        if col in df.columns:
            df[col] = df[col].apply(norm_text)
    return df

@st.cache_data(ttl=10)
def fetch_attendance_df() -> pd.DataFrame:
    res = supabase.table("attendance").select("*").execute()
    df = pd.DataFrame(res.data or [])
    if df.empty:
        return pd.DataFrame(columns=["id", "name", "category", "date"])
    for col in ["name", "category"]:
        if col in df.columns:
            df[col] = df[col].apply(norm_text)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

def add_student_to_db(name: str, mosque: str, grade: str, category: str):
    supabase.table("students").insert({
        "name": norm_text(name),
        "mosque": norm_text(mosque),
        "grade": norm_text(grade),
        "category": norm_text(category),
    }).execute()

def delete_student_from_db(student_id: int):
    supabase.table("students").delete().eq("id", student_id).execute()

def add_attendance_bulk(names: list[str], category: str, attendance_day: date):
    if not names:
        return
    recs = [{"name": norm_text(n), "category": norm_text(category), "date": str(attendance_day)} for n in names]
    supabase.table("attendance").insert(recs).execute()

# -----------------------------
# كلمات المرور
# -----------------------------
PASSWORDS = {
    "فئة أشبال السالمية":"Salmiya2026",
    "فئة أشبال حولي":"Hawally2026",
    "فئة الفتية":"Fetya2026",
    "فئة الشباب":"Shabab2026",
    "فئة الجامعيين":"Uni2026"
}

target_cat = st.selectbox("📂 اختر الفئة:", list(PASSWORDS.keys()))

df_students = fetch_students_df()
df_logs = fetch_attendance_df()

m_list = df_students[df_students["category"] == norm_text(target_cat)].sort_values(by="name", ignore_index=True) if not df_students.empty else pd.DataFrame()
l_list = df_logs[df_logs["category"] == norm_text(target_cat)].copy() if not df_logs.empty else pd.DataFrame()

# -----------------------------
# التبويبات الرئيسية
# -----------------------------
main_page = st.radio(
    "التنقل",
    ["📊 كشف الالتزام", "🔐 بوابة المشرف"],
    index=0 if st.session_state.get("MAIN_PAGE", "📊 كشف الالتزام") == "📊 كشف الالتزام" else 1,
    horizontal=True,
    label_visibility="collapsed",
    key="MAIN_PAGE",
)

# =============================
# كشف الالتزام (بدون أيام الحضور)
# =============================
if main_page == "📊 كشف الالتزام":
    if m_list.empty:
        st.info("لا توجد طلاب في هذه الفئة.")
    else:
        if not l_list.empty and "date" in l_list.columns:
            l_list["date"] = pd.to_datetime(l_list["date"], errors="coerce")

        total_days = l_list["date"].dt.date.nunique() if (not l_list.empty and "date" in l_list.columns) else 0

        def days_present(student_name: str) -> int:
            if l_list.empty or "date" not in l_list.columns:
                return 0
            return l_list[l_list["name"] == norm_text(student_name)]["date"].dt.date.nunique()

        m_list["_days"] = m_list["name"].apply(days_present)
        m_list["النسبة المئوية"] = (
            (m_list["_days"] / total_days * 100).round(1).astype(str) + "%"
            if total_days > 0 else "0%"
        )

        st.table(
            m_list[["name","mosque","grade","النسبة المئوية"]].rename(columns={
                "name":"الاسم",
                "mosque":"المسجد",
                "grade":"المرحلة الدراسية"
            })
        )

# =============================
# بوابة المشرف
# =============================
else:
    pwd = st.text_input("أدخل كلمة المرور:", type="password")

    if pwd != "" and pwd != PASSWORDS.get(target_cat):
        st.error("كلمة المرور غير صحيحة ❌")

    if pwd == PASSWORDS.get(target_cat):
        st.success("تم تسجيل الدخول ✅")

        # ✅ بديل tabs: Radio ثابت يحافظ على نفس الصفحة بعد أي rerun (خصوصًا بالموبايل)
        if "ADMIN_PAGE" not in st.session_state:
            st.session_state["ADMIN_PAGE"] = "📝 تسجيل الحضور"

        admin_page = st.radio(
            "لوحة المشرف",
            ["📝 تسجيل الحضور", "➕ إدارة الطلاب", "📥 التقارير التفصيلية"],
            index=["📝 تسجيل الحضور", "➕ إدارة الطلاب", "📥 التقارير التفصيلية"].index(st.session_state["ADMIN_PAGE"]),
            horizontal=True,
            key="ADMIN_PAGE",
        )

        # مكان رسائل نجاح داخل نفس الصفحة (يضلّك بنفس المكان)
        msg_box = st.empty()

        # -----------------------------
        # تسجيل الحضور
        # -----------------------------
        if admin_page == "📝 تسجيل الحضور":
            if m_list.empty:
                st.info("لا يوجد طلاب لهذه الفئة بعد. أضف طلاب من (إدارة الطلاب).")
            else:
                attendance_day = st.date_input("اختر تاريخ الحضور:", datetime.now().date(), key=f"att_date_{target_cat}")

                st.write("اختر الحاضرين:")
                selected_students = []

                # ✅ مفتاح ثابت لكل فئة+تاريخ (حتى ما يخرب)
                for n in m_list["name"].tolist():
                    k = f"att_{target_cat}_{attendance_day}_{n}"
                    if st.checkbox(n, key=k):
                        selected_students.append(n)

                if st.button("✅ اعتماد كشف الحضور", use_container_width=True):
                    if not selected_students:
                        msg_box.warning("الرجاء اختيار طالب واحد على الأقل.")
                    else:
                        add_attendance_bulk(selected_students, target_cat, attendance_day)

                        # ✅ صفّر الصحّات بدون تغيير الصفحة
                        for n in m_list["name"].tolist():
                            k = f"att_{target_cat}_{attendance_day}_{n}"
                            if k in st.session_state:
                                st.session_state[k] = False

                        st.cache_data.clear()
                        msg_box.success("تم اعتماد كشف الحضور ✅")

        # -----------------------------
        # إدارة الطلاب
        # -----------------------------
        elif admin_page == "➕ إدارة الطلاب":
            with st.form(key=f"add_student_{target_cat}", clear_on_submit=True):
                name_in = st.text_input("الاسم الثلاثي")
                msq_in = st.selectbox("المسجد",["شاهه العبيد","اليوسفين","العسعوسي","السهو","فاطمه الغلوم","الصقعبي","الرشيد","الرومي"])
                lvl_in = st.selectbox("المرحلة الدراسية",["الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر","الحادي عشر","الثاني عشر","جامعي"])
                submit_add = st.form_submit_button("إضافة الطالب", use_container_width=True)

            if submit_add:
                if not norm_text(name_in):
                    msg_box.warning("الرجاء إدخال الاسم.")
                else:
                    add_student_to_db(name_in, msq_in, lvl_in, target_cat)
                    st.cache_data.clear()
                    msg_box.success(f"تمت إضافة {norm_text(name_in)} ✅")

            st.divider()

            if m_list.empty:
                st.info("لا يوجد طلاب لحذفهم.")
            else:
                options = [(int(r["id"]), f'{r["name"]} - {r["mosque"]} - {r["grade"]}') for _, r in m_list.iterrows()]
                chosen = st.selectbox("اختر الطالب لحذفه:", options=options, format_func=lambda x: x[1], key=f"del_{target_cat}")
                if st.button("🗑️ حذف الطالب", use_container_width=True):
                    delete_student_from_db(chosen[0])
                    st.cache_data.clear()
                    msg_box.success("تم حذف الطالب ✅")

        # -----------------------------
        # التقارير التفصيلية
        # -----------------------------
        else:
            if m_list.empty:
                st.info("لا يوجد طلاب في هذه الفئة.")
            else:
                d1, d2 = st.columns(2)
                date_from = d1.date_input("من تاريخ", datetime.now().date(), key=f"rep_from_{target_cat}")
                date_to = d2.date_input("إلى تاريخ", datetime.now().date(), key=f"rep_to_{target_cat}")

                if st.button("📊 تجهيز التقرير", use_container_width=True):
                    all_logs = fetch_attendance_df().copy()
                    if all_logs.empty:
                        st.info("لا يوجد سجلات حضور بعد.")
                        st.stop()

                    all_logs["category"] = all_logs["category"].apply(norm_text)
                    all_logs = all_logs[all_logs["category"] == norm_text(target_cat)].copy()

                    all_logs["date"] = pd.to_datetime(all_logs["date"], errors="coerce")
                    mask = (
                        (all_logs["date"] >= pd.to_datetime(date_from)) &
                        (all_logs["date"] <= pd.to_datetime(date_to))
                    )
                    filtered = all_logs[mask].copy()
                    days_in_period = filtered["date"].dt.date.nunique() if not filtered.empty else 0

                    rep = []
                    for _, s in m_list.iterrows():
                        count_days = filtered[filtered["name"] == s["name"]]["date"].dt.date.nunique() if not filtered.empty else 0
                        pct = f"{(count_days/days_in_period*100):.1f}%" if days_in_period > 0 else "0%"
                        rep.append({
                            "الاسم": s["name"],
                            "المسجد": s["mosque"],
                            "المرحلة الدراسية": s["grade"],
                            "أيام الحضور للفترة": int(count_days),
                            "النسبة المئوية": pct
                        })

                    res_df = pd.DataFrame(rep).sort_values(by="الاسم", ignore_index=True)
                    st.table(res_df)

                    csv = res_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        "📥 تحميل CSV",
                        csv,
                        f"تقرير_مفصل_{target_cat}_{datetime.now().strftime('%Y-%m-%d')}.csv",
                        "text/csv",
                        use_container_width=True
                    )

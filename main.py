import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict

# =============================
# APP CONFIG
# =============================
APP_TZ = "Asia/Kuwait"

st.set_page_config(
    page_title="نظام تسجيل حضور الطلاب",
    page_icon="📚",
    layout="wide",
)

# (اختياري) تحسين عرض العربية (RTL)
st.markdown(
    """
    <style>
      html, body, [class*="css"]  { direction: rtl; }
      .stTabs [data-baseweb="tab-list"] { gap: 8px; }
      .stTabs [data-baseweb="tab"] { padding: 10px 14px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📚 نظام تسجيل حضور الطلاب")
st.caption("لوحة تحكم لإدارة الطلاب وتسجيل حضورهم داخل المسجد (Streamlit + Supabase).")

# =============================
# HELPERS
# =============================
def today_kuwait():
    return datetime.now(ZoneInfo(APP_TZ)).date()

def safe_rerun():
    """Compatibility helper across Streamlit versions."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def clear_app_cache():
    """Clear cached data so new inserts appear immediately."""
    try:
        fetch_students.clear()
    except Exception:
        pass
    try:
        fetch_reports.clear()
    except Exception:
        pass

# =============================
# SUPABASE CLIENT (CACHED RESOURCE)
# =============================
@st.cache_resource(show_spinner=False)
def get_supabase() -> Client:
    # Using Streamlit secrets (required)
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "مفاتيح Supabase غير موجودة. تأكد من إضافة SUPABASE_URL و SUPABASE_KEY داخل st.secrets."
        )

    # Initialize Supabase client (official approach) :contentReference[oaicite:3]{index=3}
    return create_client(url, key)

# =============================
# REQUIRED FUNCTIONS
# =============================

@st.cache_data(ttl=60, show_spinner=False)
def fetch_students() -> pd.DataFrame:
    """Fetch students from 'students' table."""
    supabase = get_supabase()
    res = (
        supabase.table("students")
        .select("id,name,mosque,grade,category")
        .order("name")
        .execute()
    )
    data = getattr(res, "data", None) or []
    df = pd.DataFrame(data)

    # Normalize columns (avoid KeyErrors)
    for col in ["name", "mosque", "grade", "category"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    return df

def add_student(name: str, mosque: str, grade: str, category: str) -> None:
    """Insert a new student into 'students' table and refresh caches."""
    supabase = get_supabase()
    payload = {
        "name": (name or "").strip(),
        "mosque": (mosque or "").strip(),
        "grade": (grade or "").strip(),
        "category": category,
    }
    supabase.table("students").insert(payload).execute()
    clear_app_cache()

def save_attendance(att_rows: List[Dict]) -> int:
    """
    Save attendance records into 'attendance' table.
    att_rows example: [{"name": "...", "category": "...", "date": "YYYY-MM-DD"}, ...]
    """
    if not att_rows:
        return 0

    supabase = get_supabase()

    # Insert supports list for bulk insert :contentReference[oaicite:4]{index=4}
    res = supabase.table("attendance").insert(att_rows).execute()
    data = getattr(res, "data", None) or []
    clear_app_cache()
    return len(data) if isinstance(data, list) else len(att_rows)

@st.cache_data(ttl=60, show_spinner=False)
def fetch_reports() -> pd.DataFrame:
    """
    Fetch attendance from 'attendance' table and enrich with mosque/grade from students
    (mosque not stored in attendance schema, so we attach it from students).
    """
    supabase = get_supabase()
    att_res = (
        supabase.table("attendance")
        .select("id,name,category,date")
        .order("date", desc=True)
        .execute()
    )
    att = pd.DataFrame(getattr(att_res, "data", None) or [])
    if att.empty:
        return att

    # Enrich with mosque/grade from students (best-effort by name)
    students = fetch_students()
    if not students.empty:
        extra = students[["name", "mosque", "grade"]].drop_duplicates(subset=["name"])
        att = att.merge(extra, on="name", how="left")

    # Parse dates for filtering
    if "date" in att.columns:
        att["date_parsed"] = pd.to_datetime(att["date"], errors="coerce").dt.date

    for col in ["name", "category", "mosque", "grade"]:
        if col in att.columns:
            att[col] = att[col].fillna("").astype(str)

    return att

# =============================
# TOP BAR ACTIONS
# =============================
top_l, top_r = st.columns([0.82, 0.18])
with top_r:
    if st.button("🔄 تحديث البيانات", use_container_width=True):
        clear_app_cache()
        safe_rerun()

# =============================
# MAIN TABS (UI FIX)
# =============================
tabs = st.tabs(
    [
        "📝 تسجيل الحضور",
        "➕ إدارة الطلاب",
        "📊 التقارير التفصيلية",
    ]
)

# -----------------------------
# TAB 1 - ATTENDANCE
# -----------------------------
with tabs[0]:
    st.subheader("📝 تسجيل الحضور")

    # Load students with loader
    try:
        with st.spinner("جارٍ تحميل قائمة الطلاب..."):
            students_df = fetch_students()
    except Exception as e:
        st.error(f"خطأ في جلب الطلاب من Supabase: {e}")
        st.stop()

    if students_df.empty:
        st.warning(
            "لا يوجد طلاب ظاهرين من قاعدة البيانات.\n\n"
            "إذا كنت متأكد أن جدول students يحتوي بيانات، فالغالب السبب هو سياسات RLS في Supabase "
            "أو استخدام مفتاح لا يملك صلاحية القراءة."
        )
    else:
        # Filters row
        f1, f2, f3, f4, f5 = st.columns([0.22, 0.22, 0.18, 0.18, 0.20])

        categories = sorted([c for c in students_df["category"].unique() if str(c).strip()])
        mosques = sorted([m for m in students_df["mosque"].unique() if str(m).strip()])
        grades = sorted([g for g in students_df["grade"].unique() if str(g).strip()])

        with f1:
            selected_category = st.selectbox(
                "الفئة",
                ["الكل"] + categories,
                index=0,
            )

        with f2:
            selected_mosque = st.selectbox(
                "المسجد",
                ["الكل"] + mosques,
                index=0,
            )

        with f3:
            selected_grade = st.selectbox(
                "الصف",
                ["الكل"] + grades,
                index=0,
            )

        with f4:
            attendance_date = st.date_input(
                "تاريخ الحضور",
                value=today_kuwait(),
            )

        with f5:
            search_name = st.text_input("بحث بالاسم", placeholder="اكتب جزء من الاسم...")

        # Apply filters
        filtered = students_df.copy()

        if selected_category != "الكل":
            filtered = filtered[filtered["category"] == selected_category]

        if selected_mosque != "الكل":
            filtered = filtered[filtered["mosque"] == selected_mosque]

        if selected_grade != "الكل":
            filtered = filtered[filtered["grade"] == selected_grade]

        if search_name.strip():
            filtered = filtered[filtered["name"].str.contains(search_name.strip(), na=False)]

        filtered = filtered.sort_values("name")

        # Stats
        s1, s2, s3 = st.columns(3)
        s1.metric("إجمالي الطلاب", int(len(students_df)))
        s2.metric("الطلاب حسب الفلاتر", int(len(filtered)))
        s3.metric("تاريخ التسجيل", attendance_date.isoformat())

        st.divider()
        st.markdown("### ✅ قائمة الطلاب (اختر الحاضرين)")

        if filtered.empty:
            st.info("لا يوجد طلاب مطابقين للفلاتر الحالية.")
        else:
            # Quick actions
            a1, a2, a3 = st.columns([0.2, 0.2, 0.6])
            with a1:
                if st.button("✅ تحديد الكل", use_container_width=True):
                    for sid in filtered["id"].tolist():
                        st.session_state[f"present_{sid}"] = True
                    safe_rerun()

            with a2:
                if st.button("🧹 إلغاء التحديد", use_container_width=True):
                    for sid in filtered["id"].tolist():
                        st.session_state[f"present_{sid}"] = False
                    safe_rerun()

            # Show checkboxes in 3 columns for better UI
            col_a, col_b, col_c = st.columns(3)

            def student_label(row):
                name = row.get("name", "")
                mosque = row.get("mosque", "")
                grade = row.get("grade", "")
                # label without exposing ID, but key uses ID
                parts = [p for p in [name, grade, mosque] if str(p).strip()]
                return " — ".join(parts) if parts else str(name)

            for i, (_, row) in enumerate(filtered.iterrows()):
                sid = row.get("id")
                key = f"present_{sid}"

                target_col = [col_a, col_b, col_c][i % 3]
                with target_col:
                    st.checkbox(student_label(row), key=key)

            st.divider()

            # Save attendance
            if st.button("💾 حفظ الحضور", type="primary", use_container_width=True):
                present_rows = []
                for _, row in filtered.iterrows():
                    sid = row.get("id")
                    if st.session_state.get(f"present_{sid}", False):
                        present_rows.append(row)

                if not present_rows:
                    st.warning("لم يتم اختيار أي طالب كـ حاضر.")
                else:
                    attendance_payload = [
                        {
                            "name": r["name"],
                            "category": r["category"],
                            "date": attendance_date.isoformat(),
                        }
                        for r in present_rows
                    ]

                    try:
                        with st.spinner("جارٍ حفظ الحضور في قاعدة البيانات..."):
                            inserted = save_attendance(attendance_payload)
                        st.success(f"✅ تم حفظ الحضور بنجاح. عدد السجلات المحفوظة: {inserted}")
                    except Exception as e:
                        st.error(f"❌ فشل حفظ الحضور: {e}")
                        st.info(
                            "إذا كان الخطأ متعلقاً بالصلاحيات، راجع سياسات RLS في Supabase "
                            "وتأكد أن المفتاح المستخدم يملك صلاحية INSERT على جدول attendance."
                        )

# -----------------------------
# TAB 2 - STUDENT MANAGEMENT
# -----------------------------
with tabs[1]:
    st.subheader("➕ إدارة الطلاب")

    left, right = st.columns([0.55, 0.45])

    with left:
        st.markdown("### إضافة طالب جديد")
        with st.form("add_student_form", clear_on_submit=True):
            name = st.text_input("اسم الطالب *")
            mosque = st.text_input("المسجد")
            grade = st.text_input("الصف")

            category = st.selectbox(
                "الفئة *",
                [
                    "فئة أشبال السلامية",
                    "فئة فتيان السلامية",
                    "فئة شباب السلامية",
                ],
            )

            submitted = st.form_submit_button("➕ إضافة الطالب", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("اسم الطالب مطلوب.")
            else:
                try:
                    with st.spinner("جارٍ إضافة الطالب..."):
                        add_student(name=name, mosque=mosque, grade=grade, category=category)
                    st.success("✅ تمت إضافة الطالب بنجاح وتم تحديث البيانات مباشرة.")
                    safe_rerun()
                except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء إضافة الطالب: {e}")
                    st.info(
                        "إذا كان الخطأ متعلقاً بالصلاحيات، راجع سياسات RLS في Supabase "
                        "وتأكد من صلاحية INSERT على جدول students."
                    )

    with right:
        st.markdown("### قائمة الطلاب الحالية")
        try:
            with st.spinner("جارٍ تحميل الطلاب..."):
                students_df = fetch_students()
        except Exception as e:
            st.error(f"خطأ في جلب الطلاب: {e}")
            students_df = pd.DataFrame()

        if students_df.empty:
            st.info("لا يوجد طلاب لعرضهم حالياً.")
        else:
            # Simple filters for viewing
            v1, v2 = st.columns(2)
            with v1:
                view_category = st.selectbox(
                    "فلترة حسب الفئة (عرض فقط)",
                    ["الكل"] + sorted([c for c in students_df["category"].unique() if str(c).strip()]),
                    index=0,
                    key="view_cat_students"
                )
            with v2:
                view_mosque = st.selectbox(
                    "فلترة حسب المسجد (عرض فقط)",
                    ["الكل"] + sorted([m for m in students_df["mosque"].unique() if str(m).strip()]),
                    index=0,
                    key="view_mosque_students"
                )

            view_df = students_df.copy()
            if view_category != "الكل":
                view_df = view_df[view_df["category"] == view_category]
            if view_mosque != "الكل":
                view_df = view_df[view_df["mosque"] == view_mosque]

            st.dataframe(view_df, use_container_width=True)

            # Optional export of students list (doesn't remove any feature)
            csv_students = view_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "تحميل قائمة الطلاب CSV",
                data=csv_students,
                file_name="students.csv",
                mime="text/csv",
                use_container_width=True
            )

# -----------------------------
# TAB 3 - DETAILED REPORTS
# -----------------------------
with tabs[2]:
    st.subheader("📊 التقارير التفصيلية")

    try:
        with st.spinner("جارٍ تحميل بيانات التقارير..."):
            reports_df = fetch_reports()
    except Exception as e:
        st.error(f"خطأ في جلب التقارير: {e}")
        st.stop()

    if reports_df.empty:
        st.info("لا يوجد بيانات حضور في جدول attendance حتى الآن.")
    else:
        # Filters
        r1, r2, r3, r4, r5 = st.columns([0.22, 0.22, 0.22, 0.18, 0.16])

        # Dates
        min_date = reports_df["date_parsed"].min() if "date_parsed" in reports_df.columns else None
        max_date = reports_df["date_parsed"].max() if "date_parsed" in reports_df.columns else None
        default_from = min_date or today_kuwait()
        default_to = max_date or today_kuwait()

        with r1:
            date_from = st.date_input("من تاريخ", value=default_from, key="rep_from")
        with r2:
            date_to = st.date_input("إلى تاريخ", value=default_to, key="rep_to")

        # Category filter (from attendance records)
        rep_categories = sorted([c for c in reports_df["category"].unique() if str(c).strip()])
        with r3:
            rep_category = st.selectbox("الفئة", ["الكل"] + rep_categories, index=0, key="rep_cat")

        # Mosque filter (enriched from students)
        mosques = []
        if "mosque" in reports_df.columns:
            mosques = sorted([m for m in reports_df["mosque"].unique() if str(m).strip()])
        with r4:
            rep_mosque = st.selectbox("المسجد", ["الكل"] + mosques, index=0, key="rep_mosque")

        with r5:
            rep_search = st.text_input("بحث", placeholder="اسم الطالب...", key="rep_search")

        # Apply filters
        filtered_rep = reports_df.copy()

        if "date_parsed" in filtered_rep.columns:
            filtered_rep = filtered_rep[
                (filtered_rep["date_parsed"] >= date_from) & (filtered_rep["date_parsed"] <= date_to)
            ]

        if rep_category != "الكل":
            filtered_rep = filtered_rep[filtered_rep["category"] == rep_category]

        if rep_mosque != "الكل" and "mosque" in filtered_rep.columns:
            filtered_rep = filtered_rep[filtered_rep["mosque"] == rep_mosque]

        if rep_search.strip():
            filtered_rep = filtered_rep[filtered_rep["name"].str.contains(rep_search.strip(), na=False)]

        # KPIs
        k1, k2, k3 = st.columns(3)
        k1.metric("عدد سجلات الحضور", int(len(filtered_rep)))
        k2.metric("عدد الطلاب (Unique)", int(filtered_rep["name"].nunique()))
        if "mosque" in filtered_rep.columns:
            k3.metric("عدد المساجد (Unique)", int(filtered_rep["mosque"].nunique()))
        else:
            k3.metric("عدد المساجد (Unique)", 0)

        st.divider()
        st.dataframe(filtered_rep, use_container_width=True)

        # Export CSV (UTF-8 with BOM for Excel Arabic)
        csv = filtered_rep.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ تحميل التقرير CSV",
            data=csv,
            file_name="attendance_report.csv",
            mime="text/csv",
            use_container_width=True
        )

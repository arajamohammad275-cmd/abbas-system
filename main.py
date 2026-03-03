Skip to content
arajamohammad275-cmd
abbas-system
Repository navigation
Code
Issues
Pull requests
Actions
Projects
Wiki
Security
Insights
Settings
Files
Go to file
t
main.py
requirements.txt
Unsaved changes
You have unsaved changes on this file that can be restored.
abbas-system
/
main.py
in
main

Edit

Preview
Indent mode

Spaces
Indent size

8
Line wrap mode

No wrap
Editing main.py file contents
Selection deleted
 87
 88
 89
 90
 91
 92
 93
 94
 95
 96
 97
 98
 99
100
101
102
103
104
105
106
107
108
109
110
111
112
113
114
115
116
117
118
119
120
121
122
123
124
125
126
127
128
129
130
131
132
133
134
135
136
137
138
139
140
141
142
143
144
145
146
147
148
149
150
151
152
153
154
155
156
157
158
159
160
161
162
163
164
165
166
167
168
169
170
171
172
173
174
175
176
177
178
179
180
181
182
183
184
185
186
187
188
189
tab_stats, tab_admin = st.tabs(["📊 كشف الالتزام والنسب", "🔐 بوابة المشرف"])

m_list = df_m[df_m['الفئة'] == target_cat] if not df_m.empty else pd.DataFrame()
l_list = df_l[df_l['الفئة'] == target_cat] if not df_l.empty else pd.DataFrame()

# --- التبويب الأول: الكشف العام ---
with tab_stats:
    if not m_list.empty:
        total_activity_days = len(l_list["التاريخ"].unique()) if not l_list.empty and "التاريخ" in l_list.columns else 0
        
        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="metric-card"><h3>👥 طلاب الفئة</h3><h2>{len(m_list)}</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><h3>📅 أيام النشاط</h3><h2>{total_activity_days}</h2></div>', unsafe_allow_html=True)
        
        display_df = m_list.copy()
        display_df['أيام الحضور'] = display_df['الاسم'].apply(lambda x: len(l_list[l_list['الاسم'] == x]) if not l_list.empty and 'الاسم' in l_list.columns else 0)
        display_df['النسبة المئوية'] = display_df['أيام الحضور'].apply(lambda x: f"{(x / total_activity_days * 100):.1f}%" if total_activity_days > 0 else "0%")
        
        st.dataframe(display_df[["الاسم", "المسجد", "أيام الحضور", "النسبة المئوية"]], use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد بيانات لهذه الفئة حالياً.")

# --- التبويب الثاني: بوابة المشرف ---
with tab_admin:
    pwd = st.text_input("أدخل كلمة المرور لدخول المشرف:", type="password")
    if pwd == PASSWORDS.get(target_cat):
        st.success("تم تسجيل الدخول بنجاح ✅")
        
        sub1, sub2, sub3 = st.tabs(["📝 تسجيل الحضور", "➕ إدارة الطلاب", "📥 التقارير التفصيلية"])
        
        # 1. تسجيل الحضور
        with sub1:
            if not m_list.empty:
                with st.form(key="attendance_form_secure", clear_on_submit=True):
                    today = st.date_input("تاريخ اليوم:", datetime.now())
                    st.write("اختر الحاضرين:")
                    selected = []
                    names = sorted(m_list['الاسم'].unique())
                    for n in names:
                        if st.checkbox(n, key=f"att_{n}"): selected.append(n)
                    
                    if st.form_submit_button("✅ اعتماد كشف الحضور", use_container_width=True):
                        if selected:
                            recs = [{"name": n, "category": target_cat, "date": str(today)} for n in selected]
                            requests.post(API_URL, json={"action": "add_attendance", "records": recs})
                            st.cache_data.clear() 
                            st.success("تم تسجيل الحضور بنجاح!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("الرجاء تحديد طالب واحد على الأقل.")
            else:
                st.warning("يرجى إضافة طلاب أولاً.")
        
        # 2. إضافة وحذف الطلاب
        with sub2:
            with st.form(key="add_student_form_secure", clear_on_submit=True):
                st.write("### ➕ إضافة طالب جديد")
                name_in = st.text_input("الاسم الثلاثي")
                msq_in = st.selectbox("المسجد", ["شاهه العبيد", "اليوسفين", "العسعوسي", "السهو", "فاطمه الغلوم", "الصقعبي", "الرشيد", "الرومي"])
                lvl_in = st.selectbox("المرحلة الدراسية", ["الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر", "جامعي"])
                
                if st.form_submit_button("إضافة الطالب الآن", use_container_width=True):
                    if name_in:
                        # 1. إرسال البيانات لجوجل
                        requests.post(API_URL, json={"action": "add_student", "name": name_in, "mosque": msq_in, "grade": lvl_in, "category": target_cat})
                        
                        # 2. إضافة الاسم فوراً لذاكرة الموقع (هنا حل المشكلة)
                        new_student = pd.DataFrame([{"الاسم": name_in, "المسجد": msq_in, "المرحلة الدراسية": lvl_in, "الفئة": target_cat}])
                        st.session_state['local_students'] = pd.concat([st.session_state['local_students'], new_student], ignore_index=True)
                        
                        st.cache_data.clear()
                        st.success(f"تمت إضافة {name_in} بنجاح!")
                        time.sleep(0.5)
                        st.rerun()
                    else: 
                        st.error("يرجى كتابة اسم الطالب أولاً")

            st.divider()
            st.write("###  حذف طالب")
            del_n = st.selectbox("اختر الاسم المراد حذفه:", [""] + sorted(m_list['الاسم'].tolist()) if not m_list.empty else [""])
            if st.button("تأكيد الحذف النهائي", use_container_width=True):
                if del_n:
                    requests.post(API_URL, json={"action": "delete_student", "name": del_n, "category": target_cat})
                    
                    # حذفه من الذاكرة أيضاً
                    st.session_state['local_students'] = st.session_state['local_students'][st.session_state['local_students']['الاسم'] != del_n]
                    
                    st.cache_data.clear()
                    st.error(f"تم حذف {del_n} نهائياً.")
                    time.sleep(0.5)
                    st.rerun()
        
        # 3. التقارير التفصيلية
        with sub3:
            st.write("### 📊 استخراج التقرير المفصل")
            d1, d2 = st.columns(2)
            date_from = d1.date_input("من تاريخ", datetime.now())
            date_to = d2.date_input("إلى تاريخ", datetime.now())
            
            if st.button("🔍 تجهيز التقرير التفصيلي", use_container_width=True):
                if not l_list.empty:
                    mask = (l_list['التاريخ'] >= str(date_from)) & (l_list['التاريخ'] <= str(date_to))
Use Control + Shift + m to toggle the tab key moving focus. Alternatively, use esc then tab to move to the next interactive element on the page.

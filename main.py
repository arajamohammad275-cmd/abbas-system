        # 1. تسجيل الحضور + إضافة سريعة
        with sub1:

            st.write("### ⚡ تسجيل الحضور + إضافة طالب فوري")

            # ===== إضافة سريعة =====
            col1, col2 = st.columns([3,1])

            with col1:
                quick_name = st.text_input("اكتب اسم الطالب الجديد للإضافة الفورية")

            with col2:
                if st.button("➕ إضافة الآن"):
                    if quick_name:

                        # تحديث القائمة الحالية قبل الفحص
                        current_names = sorted(
                            pd.concat([
                                df_m_fetched,
                                st.session_state['local_students']
                            ])[
                                lambda x: x['الفئة'] == target_cat
                            ]['الاسم'].unique()
                        )

                        if quick_name in current_names:
                            st.warning("⚠️ الاسم موجود مسبقاً")
                        else:
                            # إرسال إلى Google Sheet
                            requests.post(API_URL, json={
                                "action": "add_student",
                                "name": quick_name,
                                "mosque": "غير محدد",
                                "grade": "غير محدد",
                                "category": target_cat
                            })

                            # إضافته للذاكرة فوراً
                            new_student = pd.DataFrame([{
                                "الاسم": quick_name,
                                "المسجد": "غير محدد",
                                "المرحلة الدراسية": "غير محدد",
                                "الفئة": target_cat
                            }])

                            st.session_state['local_students'] = pd.concat(
                                [st.session_state['local_students'], new_student],
                                ignore_index=True
                            )

                            st.success(f"✅ تمت إضافة {quick_name} فورياً")
                            time.sleep(0.5)
                            st.rerun()
                    else:
                        st.error("اكتب الاسم أولاً")

            st.divider()

            # ===== نموذج تسجيل الحضور =====
            # تحديث القائمة بعد الإضافة
            updated_df = pd.concat([
                df_m_fetched,
                st.session_state['local_students']
            ]).drop_duplicates(subset=['الاسم', 'الفئة'])

            m_list_updated = updated_df[updated_df['الفئة'] == target_cat]

            if not m_list_updated.empty:

                with st.form(key="attendance_form_secure", clear_on_submit=True):

                    today = st.date_input("تاريخ اليوم:", datetime.now())
                    st.write("اختر الحاضرين:")

                    selected = []
                    names = sorted(m_list_updated['الاسم'].unique())

                    for n in names:
                        if st.checkbox(n, key=f"att_{n}"):
                            selected.append(n)

                    if st.form_submit_button("✅ اعتماد كشف الحضور", use_container_width=True):

                        if selected:

                            recs = [{
                                "name": n,
                                "category": target_cat,
                                "date": str(today)
                            } for n in selected]

                            requests.post(API_URL, json={
                                "action": "add_attendance",
                                "records": recs
                            })

                            st.cache_data.clear()
                            st.success("تم تسجيل الحضور بنجاح ✅")
                            time.sleep(1)
                            st.rerun()

                        else:
                            st.warning("الرجاء تحديد طالب واحد على الأقل.")

            else:
                st.warning("لا يوجد طلاب حالياً، أضف طالب أولاً.")

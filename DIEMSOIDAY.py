if st.session_state['final_scores'] is not None:
    st.divider()
    st.download_button("💾 LƯU DỮ LIỆU (.JSON)", data=json.dumps(st.session_state['db']), file_name="matrix_data.json")

    df_final = pd.DataFrame(list(st.session_state['final_scores'].items()), columns=['Số', 'Tổng Điểm'])
    df_final['Trạng thái'] = df_final['Số'].apply(lambda x: "🔥 NỔ" if x in st.session_state['v_loto'] else "⏳ ĐỨT")
    df_final = df_final.sort_values(by='Tổng Điểm', ascending=False)
    
    st.subheader("📈 BẢNG TỔNG ĐIỂM 100 CON SỐ")
    
    # CÁCH HIỂN THỊ AN TOÀN - KHÔNG DÙNG MATPLOTLIB
    st.dataframe(
        df_final, 
        use_container_width=True, 
        height=600,
        column_config={
            "Tổng Điểm": st.column_config.NumberColumn(format="%.1f"),
            "Trạng thái": st.column_config.TextColumn()
        }
    )
    
    st.success(f"**Top 10 đề xuất:** {', '.join(df_final['Số'].head(10).tolist())}")

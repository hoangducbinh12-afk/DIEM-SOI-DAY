if st.session_state['final_scores'] is not None:
    st.divider()
    st.download_button("💾 LƯU DỮ LIỆU (.JSON)", 
                       data=json.dumps(st.session_state['db']), 
                       file_name="matrix_data.json")

    # 1. Tạo DataFrame từ kết quả tính toán
    df_final = pd.DataFrame(list(st.session_state['final_scores'].items()), columns=['Số', 'Tổng Điểm'])
    
    # 2. Xác định trạng thái Nổ/Đứt dựa trên 27 giải vừa nhập
    df_final['Trạng thái'] = df_final['Số'].apply(lambda x: "🔥 NỔ" if x in st.session_state['v_loto'] else "⏳ ĐỨT")
    
    # 3. QUAN TRỌNG: Sắp xếp bảng theo Tổng Điểm giảm dần
    # Con nào điểm cao nhất phải nằm trên cùng
    df_final = df_final.sort_values(by='Tổng Điểm', ascending=False).reset_index(drop=True)
    
    st.subheader("📈 BẢNG TỔNG ĐIỂM 100 CON SỐ (ĐÃ SẮP XẾP)")
    
    # Hiển thị bảng điểm
    st.dataframe(
        df_final, 
        use_container_width=True, 
        height=600,
        column_config={
            "Tổng Điểm": st.column_config.NumberColumn(format="%.1f"),
            "Trạng thái": st.column_config.TextColumn()
        }
    )
    
    # 4. LẤY TOP 10 THỰC SỰ (Dựa trên điểm số sau khi đã sort)
    st.divider()
    st.subheader("🏆 DÀN ĐỀ XUẤT NĂNG LƯỢNG CAO")
    
    # Lấy 10 con đứng đầu bảng (điểm cao nhất)
    top_10 = df_final.head(10)
    
    c1, c2 = st.columns(2)
    with c1:
        st.success("**🎯 Top 10 Tổng Lực (Cao nhất):**")
        st.write(", ".join(top_10['Số'].tolist()))
    
    with c2:
        # Lọc thêm 1 dàn Top 10 nhưng chỉ lấy những con đang "ĐỨT" (Lò xo đang nén cực mạnh)
        top_10_compressed = df_final[df_final['Trạng thái'] == "⏳ ĐỨT"].head(10)
        st.warning("**🚀 Top 10 Lò Xo Nén (Điểm cao & Chưa nổ):**")
        st.write(", ".join(top_10_compressed['Số'].tolist()))

    # 5. HIỂN THỊ CẢNH BÁO VÙNG NÉ
    st.error(f"**🚫 Vùng Né (10 số điểm thấp nhất):** {', '.join(df_final['Số'].tail(10).tolist())}")
    
    # 6. HIỂN THỊ LỊCH SỬ TRÚNG GIẢI
    st.divider()
    st.subheader("📜 LỊCH SỬ TRÚNG GIẢI")
    
    if st.session_state['v_loto']:
        # Tạo bảng lịch sử
        history_df = pd.DataFrame({
            "STT": [len(st.session_state['v_loto'])],
            "GĐB": [st.session_state['gdb_val']],
            "10 số cao nhất": [len([x for x in st.session_state['v_loto'] if x in df_final.head(10)['Số'].tolist()])],
            "10 số cao nhì": [len([x for x in st.session_state['v_loto'] if x in df_final.iloc[10:20]['Số'].tolist()])],
            "7 số cao ba": [len([x for x in st.session_state['v_loto'] if x in df_final.iloc[20:27]['Số'].tolist()])],
            "20 số điểm thấp": [len([x for x in st.session_state['v_loto'] if x in df_final.tail(20)['Số'].tolist()])]
        })
        
        # Hiển thị bảng lịch sử
        st.dataframe(history_df, use_container_width=True)

import streamlit as st
import pandas as pd
import json
import os

# --- CẤU HÌNH ---
DB_FILE = "wires_db.json"
TOTAL_WIRES = 107 * 107

# Giao diện
st.set_page_config(page_title="Matrix 11.449 - Admin Verify", layout="wide")

# Hàm hiển thị loto có tô màu ĐB
def highlight_gdb(val, gdb):
    color = 'red' if val == gdb else 'white'
    return f'background-color: {color}; color: {"white" if color=="red" else "black"}'

def main():
    st.title("⚡ MATRIX 11.449 - HỆ THỐNG KIỂM SOÁT DỮ LIỆU")
    
    # --- PHẦN 1: NHẬP LIỆU ---
    with st.sidebar:
        st.header("1. QUÉT DỮ LIỆU KỲ MỚI")
        gdb_full = st.text_input("Giải Đặc Biệt (5 số):", "00000")
        g1 = st.text_input("Giải Nhất (5 số):", "")
        # ... (Ở đây mày có thể thêm các ô nhập giải khác hoặc dùng 1 ô text area cho nhanh)
        all_raw = st.text_area("Nhập 27 số loto quét được (cách nhau dấu cách hoặc phẩy):")
        submit = st.button("XÁC NHẬN & KIỂM TRA")

    if submit and all_raw:
        loto_list = [s.strip()[-2:] for s in all_raw.replace(",", " ").split()]
        gdb_loto = gdb_full[-2:]
        
        # --- PHẦN 2: HIỂN THỊ ĐỐI SOÁT 27 GIẢI ---
        st.subheader("📊 KIỂM TRA 27 GIẢI LOTO")
        cols = st.columns(9)
        for i, loto in enumerate(loto_list):
            with cols[i % 9]:
                if loto == gdb_loto:
                    st.markdown(f"<div style='text-align:center; padding:10px; background-color:#ff4b4b; color:white; border-radius:5px; font-weight:bold;'>{loto}<br>(ĐB)</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:center; padding:10px; background-color:#f0f2f6; border-radius:5px;'>{loto}</div>", unsafe_allow_html=True)

        st.divider()

        # --- PHẦN 3: HIỂN THỊ 107 VỊ TRÍ BIT ---
        st.subheader("📍 CHI TIẾT 107 VỊ TRÍ BIT")
        st.info("Kiểm tra xem từng Bit đã được gán đúng số chưa trước khi tính điểm 11.449 dây.")
        
        # Giả lập mapping 107 bit từ 27 giải (Mày có thể điều chỉnh logic cắt bit ở đây)
        # Ví dụ: Bit 0-4 là giải ĐB, 5-9 là Giải nhất...
        bit_data = []
        for i in range(107):
            # Đây là nơi mày code logic lấy từng vị trí số trong bảng kết quả
            # Ví dụ tạm thời:
            val = loto_list[i % len(loto_list)] 
            bit_data.append({"Vị trí Bit": f"Bit {i}", "Giá trị": val})
        
        df_bits = pd.DataFrame(bit_data)
        
        # Hiển thị dạng bảng lưới cho dễ nhìn
        col_bits = st.columns(4)
        for j in range(4):
            with col_bits[j]:
                start_idx = j * 27
                end_idx = min((j+1) * 27, 107)
                st.table(df_bits.iloc[start_idx:end_idx])

        # --- PHẦN 4: NÚT LỆNH CHUẨN ---
        if st.button("DỮ LIỆU CHUẨN - BẮT ĐẦU TÍNH TOÁN MA TRẬN"):
            st.warning("Đang thực thi tính toán cho 11.449 sợi dây... Vui lòng chờ.")
            # Gọi hàm process_result() ở đây để cập nhật DB
            st.success("Hoàn tất! Kiểm tra Bảng Tổng Điểm ở phía dưới.")

if __name__ == "__main__":
    main()

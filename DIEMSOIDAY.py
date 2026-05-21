import streamlit as st
import pandas as pd
import json
import os
import cv2
import numpy as np
import easyocr
from PIL import Image

# --- CẤU HÌNH HỆ THỐNG ---
BIT_COUNT = 107
TOTAL_WIRES = BIT_COUNT * BIT_COUNT 

# Khởi tạo OCR Reader (tải model số)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

reader = load_ocr()

# --- 1. QUẢN LÝ DỮ LIỆU ---
def init_default_db():
    return {str(i): {"score": 10.0, "streak_win": 0, "streak_loss": 0} for i in range(TOTAL_WIRES)}

# --- 2. LOGIC TÍNH TOÁN ---
def update_matrix(db, loto_list, gdb_loto):
    num_scores = {f"{i:02d}": 0.0 for i in range(100)}
    for wire_id in range(TOTAL_WIRES):
        w_str = str(wire_id)
        wire = db[w_str]
        num_formed = f"{wire_id % 100:02d}"
        
        is_hit = num_formed in loto_list
        is_gdb = (num_formed == gdb_loto)
        hit_count = loto_list.count(num_formed)
        
        if is_hit:
            wire["streak_loss"] = 0
            wire["streak_win"] += 1
            if wire["streak_win"] <= 3:
                if is_gdb: wire["score"] += 5.0
                wire["score"] += hit_count
            else:
                wire["score"] -= 0.5
        else:
            wire["streak_win"] = 0
            wire["streak_loss"] += 1
            if wire["streak_loss"] >= 4:
                wire["score"] += 0.5
        
        num_scores[num_formed] += wire["score"]
    return db, num_scores

# --- 3. GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Matrix 11.449 System", layout="wide")

# Khởi tạo bộ nhớ tạm (Session State)
if 'db' not in st.session_state:
    st.session_state['db'] = init_default_db()

st.title("⚡ MATRIX 11.449 - HỆ THỐNG PHÂN TÍCH SIÊU ĐA TẦNG")

# --- SIDEBAR: UPLOAD & INPUT ---
with st.sidebar:
    st.header("📂 QUẢN LÝ ĐẦU VÀO")
    
    # 1. Upload JSON Database
    uploaded_json = st.file_uploader("Nạp file dữ liệu .json (Điểm cũ)", type=['json'])
    if uploaded_json:
        st.session_state['db'] = json.load(uploaded_json)
        st.success("Đã nạp điểm tích lũy từ file!")

    st.divider()
    
    # 2. Quét ảnh OCR
    uploaded_img = st.file_uploader("Quét ảnh bảng kết quả", type=['jpg', 'jpeg', 'png'])
    scanned_text = ""
    if uploaded_img:
        img = Image.open(uploaded_img)
        st.image(img, caption="Ảnh đang quét")
        if st.button("BẮT ĐẦU QUÉT OCR"):
            with st.spinner("Đang đọc số..."):
                img_np = np.array(img)
                results = reader.readtext(img_np, detail=0)
                # Lọc lấy các chuỗi số
                nums = [n for n in results if n.isdigit()]
                scanned_text = ", ".join(nums)
                st.session_state['raw_input'] = scanned_text

    # 3. Ô nhập liệu cuối cùng
    final_raw = st.text_area("Dữ liệu 27 giải (kiểm tra lại):", 
                             value=st.session_state.get('raw_input', ""), height=150)
    gdb_num = st.text_input("2 số cuối Đặc biệt:", value=st.session_state.get('v_gdb', ""))

    btn_verify = st.button("KIỂM TRA & HIỆN BIT")
    btn_calc = st.button("CHẠY MA TRẬN 11.449 DÂY")

# --- MÀN HÌNH CHÍNH ---
if btn_verify or 'v_loto' in st.session_state:
    if final_raw and gdb_num:
        loto_list = [x.strip()[-2:] for x in final_raw.replace(",", " ").split() if x]
        st.session_state['v_loto'] = loto_list
        st.session_state['v_gdb'] = gdb_num
        st.session_state['raw_input'] = final_raw

        # HIỂN THỊ 27 LOTO
        st.subheader("📊 BẢNG ĐỐI SOÁT 27 GIẢI LOTO")
        cols = st.columns(9)
        for i, val in enumerate(loto_list):
            with cols[i % 9]:
                is_db = (val == gdb_num)
                color = "#ff4b4b" if is_db else "#f0f2f6"
                txt_color = "white" if is_db else "black"
                st.markdown(f"<div style='text-align:center; padding:10px; background-color:{color}; color:{txt_color}; border-radius:5px;'>{val}</div>", unsafe_allow_html=True)

        # HIỂN THỊ 107 BIT
        st.divider()
        st.subheader("📍 TRÍCH XUẤT 107 VỊ TRÍ BIT")
        all_chars = "".join([x.strip() for x in final_raw.replace(",", " ").split() if x])
        bit_list = [all_chars[i] if i < len(all_chars) else "?" for i in range(107)]
        bit_df = pd.DataFrame({"Bit": [f"B{i}" for i in range(107)], "Số": bit_list})
        
        c1, c2, c3, c4 = st.columns(4)
        for i, col in enumerate([c1, c2, c3, c4]):
            col.dataframe(bit_df.iloc[i*27:(i+1)*27], use_container_width=True)

if btn_calc:
    if 'v_loto' in st.session_state:
        with st.spinner("Đang tính toán 11.449 sợi dây..."):
            new_db, scores = update_matrix(st.session_state['db'], st.session_state['v_loto'], st.session_state['v_gdb'])
            st.session_state['db'] = new_db
            
            st.success("Tính toán hoàn tất!")
            
            # Xuất file JSON để người dùng tải về máy lưu trữ
            st.download_button("TẢI VỀ FILE DỮ LIỆU MỚI (.JSON)", 
                               data=json.dumps(new_db), 
                               file_name="matrix_updated.json", 
                               mime="application/json")

            # Hiển thị kết quả
            df_final = pd.DataFrame(list(scores.items()), columns=['Số', 'Tổng Điểm']).sort_values(by='Tổng Điểm', ascending=False)
            st.subheader("📈 BẢNG TỔNG ĐIỂM 100 CON SỐ")
            st.dataframe(df_final.style.background_gradient(cmap='YlOrRd'), use_container_width=True)
    else:
        st.error("Vui lòng bấm 'Kiểm tra' trước khi tính toán.")

import streamlit as st
import pandas as pd
import json
import os
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Matrix V7.1 - Fixed", layout="wide")
TOTAL_POS = 107 

# Khởi tạo Session State bền vững
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "last_loto": [],
        "history": []
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""
if 'current_predictions' not in st.session_state: st.session_state['current_predictions'] = {}

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

# --- 2. HÀM XỬ LÝ LOGIC (TỐI ƯU HÓA) ---

def process_matrix(current_digits, current_loto):
    db = st.session_state['db']
    old_digits = db['last_digits']
    old_loto = set(db['last_loto']) # Dùng set để tìm kiếm cực nhanh
    wire_scores = np.array(db['wire_scores'])
    
    # 1. CẬP NHẬT ĐIỂM DÂY (Dựa trên KQ vừa nạp so với dự báo từ quá khứ)
    if old_digits and old_loto:
        # Vector hóa việc kiểm tra nổ số
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                num_past = old_digits[i] + old_digits[j]
                if num_past in old_loto:
                    wire_scores[i][j] += 1
                else:
                    wire_scores[i][j] = 0
    
    # 2. LỌC ÁNH XẠ ĐỘC NHẤT (ISOLATED SIGNAL) CHO KỲ TỚI
    new_preds = {}
    if current_digits:
        max_s = int(wire_scores.max())
        if max_s > 0:
            for s in range(1, max_s + 1):
                # Chỉ xử lý nếu có dây ở mức điểm này
                mask = (wire_scores == s)
                if not np.any(mask): continue
                
                coords = np.argwhere(mask)
                level_map = {}
                for r, c in coords:
                    num = current_digits[r] + current_digits[c]
                    level_map[num] = level_map.get(num, 0) + 1
                
                # Lọc duy nhất
                isolated = [n for n, count in level_map.items() if count == 1]
                if isolated:
                    new_preds[s] = sorted(isolated)

    # Cập nhật trạng thái
    st.session_state['db']['wire_scores'] = wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    st.session_state['current_predictions'] = new_preds

# --- 3. GIAO DIỆN ---

st.markdown("<h1 style='text-align: center; color: #00FFAA;'>💎 MATRIX V7.1: ISOLATED SIGNAL</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("📸 NHẬP DỮ LIỆU")
    uploaded_img = st.file_uploader("Quét ảnh bảng KQ", type=['jpg', 'png', 'jpeg'], key="uploader")
    if uploaded_img:
        if st.button("BẮT ĐẦU OCR"):
            with st.spinner("Đang trích xuất..."):
                reader = load_ocr()
                results = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
                nums = [n for n in results if n.isdigit() and 2 <= len(n) <= 5]
                if nums: st.session_state['raw_input'] = ", ".join(nums)
            st.rerun()

    st.session_state['raw_input'] = st.text_area("Dữ liệu 27 giải:", value=st.session_state['raw_input'], height=150)
    gdb_val = st.text_input("GĐB (Để đối soát):", max_chars=2)

    if st.button("🔥 CHẠY TRUY VẾT", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len(raw) >= 27:
            # Lấy 107 số và 27 nháy lô
            c_digits = "".join(raw)[:TOTAL_POS]
            c_loto = [s[-2:] for s in raw[:27]]
            
            # Xử lý
            process_matrix(c_digits, c_loto)
            
            # Ghi lịch sử
            st.session_state['db']['history'].insert(0, {"STT": len(st.session_state['db']['history'])+1, "GĐB": gdb_val})
            st.rerun()

    if st.button("🚨 RESET ALL"):
        st.session_state.clear()
        st.rerun()

# --- 4. HIỂN THỊ KẾT QUẢ (CHỐNG LỖI DOM) ---

c1, c2 = st.columns([2, 3])

with c1:
    st.subheader("🎯 DÀN ĐỘC NHẤT")
    preds = st.session_state.get('current_predictions', {})
    if not preds:
        if st.session_state['db']['last_digits']:
            st.warning("Ảnh 1 đã nạp. Chưa có dự báo. Hãy nạp Ảnh 2.")
        else:
            st.info("Hãy nạp KQ Ảnh 1 để khởi tạo.")
    else:
        # Sắp xếp mức điểm từ cao xuống thấp
        levels = sorted(preds.keys(), reverse=True)
        for lv in levels:
            # Dùng key động để tránh lỗi removeChild
            with st.expander(f"⭐ CẦU THÔNG {lv} KỲ", expanded=(lv == levels[0])):
                nums = preds[lv]
                st.write(f"Số quân: **{len(nums)}**")
                st.code(", ".join(nums))

with c2:
    st.subheader("📋 LỊCH SỬ")
    if st.session_state['db']['history']:
        st.dataframe(pd.DataFrame(st.session_state['db']['history']), use_container_width=True)
    
    st.divider()
    if st.session_state['db']['last_digits']:
        # Tải dữ liệu để dự phòng
        js = json.dumps(st.session_state['db'])
        st.download_button("💾 XUẤT DATA (.JSON)", js, file_name="matrix_data.json")

import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Matrix V8.6.1 - Predator Fix", layout="wide")
TOTAL_POS = 107 

# Khởi tạo đầy đủ các biến trong Session State để tránh lỗi KeyError
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "last_loto": [],
        "history": [],
        "last_predictions": {} 
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""
if 'gdb_ocr' not in st.session_state: st.session_state['gdb_ocr'] = ""
if 'loto_list_display' not in st.session_state: st.session_state['loto_list_display'] = []

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

# --- 2. LOGIC ĐIỀU HÀNH (THE PREDATOR ENGINE) ---

def process_matrix(current_digits, current_loto, gdb_val):
    # Lấy dữ liệu cũ
    old_scores = np.array(st.session_state['db']['wire_scores'], dtype=int)
    old_digits = st.session_state['db']['last_digits']
    old_preds = st.session_state['db']['last_predictions']
    
    # Ma trận mới để lưu điểm sau khi kiểm tra nổ
    new_wire_scores = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int)
    
    # --- BƯỚC A: ĐỐI SOÁT NHÁY (Dàn dự báo cũ vs KQ vừa nạp) ---
    hit_report = {"STT": len(st.session_state['db']['history']) + 1, "GĐB": gdb_val}
    if old_preds:
        for lv, data in old_preds.items():
            pred_nums = data['nums']
            found_hits = [n for n in pred_nums if n in current_loto]
            total_nhay = sum([current_loto.count(n) for n in found_hits])
            hit_report[f"Mức {lv}đ"] = f"{total_nhay} ({','.join(found_hits)})" if total_nhay > 0 else "0"

    # --- BƯỚC B: TRUY VẾT & RESET (KIỂM TRA CẦU THÔNG) ---
    # Dây chỉ được cộng điểm nếu Tọa độ kỳ trước nổ ở kỳ này
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                # Số được tạo ra từ tọa độ (i,j) của kỳ TRƯỚC
                num_from_past_pos = old_digits[i] + old_digits[j]
                
                # Nếu số đó nổ ở KỲ NÀY -> Dây sống và tăng điểm
                if num_from_past_pos in current_loto:
                    new_wire_scores[i][j] = old_scores[i][j] + 1
                # Không nổ -> Mặc định về 0 (Hard Reset)
    
    # --- BƯỚC C: TẠO DỰ BÁO CHO KỲ TIẾP THEO ---
    new_preds = {}
    max_s = int(new_wire_scores.max())
    if max_s > 0:
        for s in range(1, max_s + 1):
            coords = np.argwhere(new_wire_scores == s)
            total_w = len(coords)
            if total_w == 0: continue
            
            level_map = {}
            for r, c in coords:
                # Dự báo số sẽ nổ kỳ sau dựa trên tọa độ dây vừa xác nhận
                num_for_future = current_digits[r] + current_digits[c]
                level_map[num_for_future] = level_map.get(num_for_future, 0) + 1
            
            # Lọc ánh xạ độc nhất trong nội bộ mức điểm
            isolated = [n for n, count in level_map.items() if count == 1]
            new_preds[int(s)] = {"nums": sorted(isolated), "total_wires": int(total_w)}

    # Cập nhật Session State
    st.session_state['db']['wire_scores'] = new_wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    st.session_state['db']['last_predictions'] = new_preds
    st.session_state['db']['history'].insert(0, hit_report)

# --- 3. GIAO DIỆN ---
st.markdown("<h1 style='text-align: center; color: #00FFAA;'>⚡ MATRIX V8.6.1: PREDATOR FIXED</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("📸 NHẬP LIỆU")
    uploaded_img = st.file_uploader("Quét ảnh bảng KQ", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("BẮT ĐẦU QUÉT"):
        with st.spinner("Đang trích xuất dữ liệu..."):
            reader = load_ocr()
            res = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
            nums = [n for n in res if n.isdigit() and 2 <= len(n) <= 5]
            if nums: 
                st.session_state['raw_input'] = ", ".join(nums)
                st.session_state['gdb_ocr'] = nums[0][-2:]
                st.session_state['loto_list_display'] = [n[-2:] for n in nums[1:27]]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Bảng giải gốc:", value=st.session_state['raw_input'], height=150)
    
    st.subheader("🔍 ĐỐI SOÁT QUÉT")
    # Sử dụng .get() để an toàn tuyệt đối
    gdb_val = st.text_input("1. Giải Đặc Biệt:", value=st.session_state.get('gdb_ocr', ""), max_chars=2)
    loto_display = st.text_area("2. Danh sách 26 giải lô:", value=", ".join(st.session_state.get('loto_list_display', [])), height=100)

    if st.button("🔥 CHẠY TRUY VẾT", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        full_str = "".join(raw)
        if len(full_str) >= TOTAL_POS:
            process_matrix(full_str[:TOTAL_POS], [s[-2:] for s in raw[:27]], gdb_val)
            st.rerun()
        else:
            st.error(f"Dữ liệu không đủ {TOTAL_POS} ký tự!")

    if st.button("🚨 RESET ALL"):
        st.session_state.clear()
        st.rerun()

# --- 4. HIỂN THỊ KẾT QUẢ ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🎯 DÀN DỰ BÁO (CHO KỲ TIẾP)")
    preds = st.session_state['db'].get('last_predictions', {})
    if preds:
        for lv in sorted(preds.keys(), reverse=True):
            data = preds[lv]
            with st.expander(f"⭐ MỨC {lv} ĐIỂM (Dây: {data['total_wires']})", expanded=True):
                st.write(f"Số quân độc nhất: **{len(data['nums'])}**")
                st.code(", ".join(data['nums']) if data['nums'] else "Không có số độc nhất")
    else:
        st.info("Nạp kỳ 1 để lấy gốc tọa độ, kỳ 2 bắt đầu có điểm.")

with col2:
    st.subheader("📋 LỊCH SỬ ĐỐI SOÁT")
    if st.session_state['db']['history']:
        df_hist = pd.DataFrame(st.session_state['db']['history']).fillna("0")
        st.dataframe(df_hist, use_container_width=True)

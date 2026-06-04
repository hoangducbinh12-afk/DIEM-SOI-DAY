import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Matrix V8.1 - Hard Reset Engine", layout="wide")
TOTAL_POS = 107 

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "last_loto": [],
        "history": [],
        "last_predictions": {} 
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

# --- 2. LOGIC ĐIỀU HÀNH (KHẮC PHỤC LỖI RESET) ---

def process_matrix(current_digits, current_loto, gdb_val):
    # Lấy ma trận cũ ra dạng Numpy để tính toán
    wire_scores = np.array(st.session_state['db']['wire_scores'])
    old_digits = st.session_state['db']['last_digits']
    old_loto_set = set(st.session_state['db']['last_loto'])
    old_preds = st.session_state['db']['last_predictions']
    
    # --- BƯỚC A: ĐỐI SOÁT NHÁY KỲ VỪA NẠP ---
    hit_report = {"STT": len(st.session_state['db']['history']) + 1, "GĐB": gdb_val}
    if old_preds:
        for lv, data in old_preds.items():
            pred_nums = data['nums']
            found_hits = [n for n in pred_nums if n in current_loto]
            total_nhay = sum([current_loto.count(n) for n in found_hits])
            hit_report[f"Mức {lv}đ"] = f"{total_nhay} ({','.join(found_hits)})" if total_nhay > 0 else "0"

    # --- BƯỚC B: CẬP NHẬT ĐIỂM DÂY (HARD RESET) ---
    # Tạo một ma trận mới hoàn toàn bằng 0
    new_wire_scores = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int)
    
    if len(old_digits) >= TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                # Kiểm tra ánh xạ tạo ra từ tọa độ (i,j) của KỲ TRƯỚC
                num_past = old_digits[i] + old_digits[j]
                
                # NẾU NỔ: Lấy điểm cũ + 1. NẾU KHÔNG NỔ: Mặc định là 0 (đã khởi tạo ở new_wire_scores)
                if num_past in old_loto_set:
                    new_wire_scores[i][j] = wire_scores[i][j] + 1
                # (Không cần else vì new_wire_scores đã là 0 từ đầu)
    
    # Thay thế hoàn toàn ma trận cũ bằng ma trận mới
    wire_scores = new_wire_scores

    # --- BƯỚC C: CHIẾT XUẤT DÀN ĐỘC NHẤT ---
    new_preds = {}
    max_s = int(wire_scores.max())
    if max_s > 0:
        for s in range(1, max_s + 1):
            coords = np.argwhere(wire_scores == s)
            total_wires_at_s = len(coords)
            if total_wires_at_s == 0: continue
            
            level_map = {}
            for r, c in coords:
                num = current_digits[r] + current_digits[c]
                level_map[num] = level_map.get(num, 0) + 1
            
            isolated = [n for n, count in level_map.items() if count == 1]
            if isolated or total_wires_at_s > 0:
                new_preds[s] = {"nums": sorted(isolated), "total_wires": total_wires_at_s}

    # ĐỒNG BỘ LẠI SESSION STATE
    st.session_state['db']['wire_scores'] = wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    st.session_state['db']['last_predictions'] = new_preds
    st.session_state['db']['history'].insert(0, hit_report)

# --- 3. GIAO DIỆN ---
st.markdown("<h1 style='text-align: center; color: #00FFAA;'>⚡ MATRIX V8.1: HARD RESET</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("📸 NHẬP LIỆU")
    uploaded_img = st.file_uploader("Quét ảnh KQ", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("QUÉT OCR"):
        with st.spinner("Đang trích xuất..."):
            reader = load_ocr()
            res = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
            nums = [n for n in res if n.isdigit() and 2 <= len(n) <= 5]
            if nums: st.session_state['raw_input'] = ", ".join(nums)
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Bảng giải:", value=st.session_state['raw_input'], height=150)
    gdb_confirm = st.text_input("GĐB (Xác nhận):", max_chars=2)

    if st.button("🔥 CHẠY TRUY VẾT", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len("".join(raw)) >= TOTAL_POS:
            process_matrix("".join(raw)[:TOTAL_POS], [s[-2:] for s in raw[:27]], gdb_confirm)
            st.rerun()
    
    if st.button("🚨 RESET ALL"):
        st.session_state.clear()
        st.rerun()

col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("🎯 DÀN ĐỘC NHẤT")
    preds = st.session_state['db'].get('last_predictions', {})
    if preds:
        for lv in sorted(preds.keys(), reverse=True):
            data = preds[lv]
            # Chỉ hiện các mức điểm đang có dây
            if data['total_wires'] > 0:
                with st.expander(f"⭐ MỨC {lv} ĐIỂM (Dây: {data['total_wires']})", expanded=(lv == max(preds.keys()))):
                    st.write(f"Số quân độc nhất: **{len(data['nums'])}**")
                    st.code(", ".join(data['nums']) if data['nums'] else "Không có số độc nhất")
    else:
        st.info("Cần nạp ít nhất 2 kỳ.")

with col2:
    st.subheader("📋 LỊCH SỬ")
    if st.session_state['db']['history']:
        st.dataframe(pd.DataFrame(st.session_state['db']['history']).fillna("0"))

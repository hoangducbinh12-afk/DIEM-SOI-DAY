import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Matrix V8.6 - The Predator", layout="wide")
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

# --- 2. LOGIC ĐIỀU HÀNH (SỬA LỖI CỘNG DỒN) ---

def process_matrix(current_digits, current_loto, gdb_val):
    # Lấy dữ liệu cũ ra
    old_scores = np.array(st.session_state['db']['wire_scores'], dtype=int)
    old_digits = st.session_state['db']['last_digits']
    old_loto_set = set(st.session_state['db']['last_loto']) # Đây là loto kỳ trước đó nữa
    old_preds = st.session_state['db']['last_predictions']
    
    # Ma trận mới để lưu điểm sau khi 'chém'
    new_wire_scores = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int)
    
    # --- BƯỚC A: ĐỐI SOÁT NHÁY ---
    # (So dàn dự báo của kỳ trước với kết quả lô vừa nạp vào)
    hit_report = {"STT": len(st.session_state['db']['history']) + 1, "GĐB": gdb_val}
    if old_preds:
        for lv, data in old_preds.items():
            pred_nums = data['nums']
            found_hits = [n for n in pred_nums if n in current_loto]
            total_nhay = sum([current_loto.count(n) for n in found_hits])
            hit_report[f"Mức {lv}đ"] = f"{total_nhay} ({','.join(found_hits)})" if total_nhay > 0 else "0"

    # --- BƯỚC B: TRUY VẾT & RESET (QUAN TRỌNG) ---
    # Ta phải kiểm tra: Tọa độ của kỳ trước có nổ ở KỲ NÀY không?
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                # Số được tạo ra từ tọa độ (i,j) của kỳ TRƯỚC
                num_from_past_pos = old_digits[i] + old_digits[j]
                
                # Nếu số đó nổ ở KỲ NÀY -> Dây sống và tăng điểm
                if num_from_past_pos in current_loto:
                    new_wire_scores[i][j] = old_scores[i][j] + 1
                else:
                    # Không nổ -> Reset về 0 (Mặc định đã là 0)
                    new_wire_scores[i][j] = 0
    
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
                # Lấy số sẽ nổ kỳ sau dựa trên tọa độ dây vừa được xác nhận
                num_for_future = current_digits[r] + current_digits[c]
                level_map[num_for_future] = level_map.get(num_for_future, 0) + 1
            
            isolated = [n for n, count in level_map.items() if count == 1]
            new_preds[s] = {"nums": sorted(isolated), "total_wires": total_w}

    # Cập nhật Session
    st.session_state['db']['wire_scores'] = new_wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    st.session_state['db']['last_predictions'] = new_preds
    st.session_state['db']['history'].insert(0, hit_report)

# --- 3. GIAO DIỆN ---
st.markdown("<h1 style='text-align: center; color: #00FFAA;'>⚡ MATRIX V8.6: THE PREDATOR</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("📸 NHẬP LIỆU")
    uploaded_img = st.file_uploader("Quét ảnh bảng KQ", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("QUÉT OCR"):
        with st.spinner("Đang trích xuất..."):
            reader = load_ocr()
            res = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
            nums = [n for n in res if n.isdigit() and 2 <= len(n) <= 5]
            if nums: 
                st.session_state['raw_input'] = ", ".join(nums)
                st.session_state['gdb_ocr'] = nums[0][-2:]
                st.session_state['loto_list_display'] = [n[-2:] for n in nums[1:27]]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Bảng giải:", value=st.session_state['raw_input'], height=150)
    gdb_confirm = st.text_input("GĐB (Xác nhận):", value=st.session_state['gdb_ocr'], max_chars=2)
    loto_display = st.text_area("26 giải lô:", value=", ".join(st.session_state.get('loto_list_display', [])), height=100)

    if st.button("🔥 CHẠY PHÂN TÍCH", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len("".join(raw)) >= TOTAL_POS:
            process_matrix("".join(raw)[:TOTAL_POS], [s[-2:] for s in raw[:27]], gdb_confirm)
            st.rerun()
    
    st.button("🚨 RESET ALL", on_click=lambda: st.session_state.clear())

col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("🎯 DÀN DỰ BÁO (CHO KỲ TIẾP)")
    preds = st.session_state['db'].get('last_predictions', {})
    if preds:
        for lv in sorted(preds.keys(), reverse=True):
            data = preds[lv]
            with st.expander(f"⭐ MỨC {lv} ĐIỂM (Dây: {data['total_wires']})", expanded=True):
                st.code(", ".join(data['nums']) if data['nums'] else "Không có số độc nhất")
    else: st.info("Hãy nạp kỳ 1 để lấy gốc tọa độ.")

with col2:
    st.subheader("📋 LỊCH SỬ ĐỐI SOÁT")
    if st.session_state['db']['history']:
        st.dataframe(pd.DataFrame(st.session_state['db']['history']).fillna("0"))

import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Matrix V8.9 - Data Persistence", layout="wide")
TOTAL_POS = 107 

# Khởi tạo Session State
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

# --- 2. LOGIC ĐIỀU HÀNH ---

def process_matrix(current_digits, current_loto, gdb_val):
    old_scores = np.array(st.session_state['db']['wire_scores'], dtype=int)
    old_digits = st.session_state['db']['last_digits']
    old_preds = st.session_state['db']['last_predictions']
    
    new_wire_scores = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int)
    
    # --- A. ĐỐI SOÁT NHÁY & SOI GĐB ---
    hit_report = {"STT": len(st.session_state['db']['history']) + 1, "GĐB": gdb_val}
    gdb_win_levels = []
    
    if old_preds:
        # Chuyển key của old_preds sang int vì khi load từ JSON nó có thể bị biến thành string
        fixed_old_preds = {int(k): v for k, v in old_preds.items()}
        for lv in sorted(fixed_old_preds.keys(), reverse=True):
            data = fixed_old_preds[lv]
            pred_nums = data['nums']
            found_hits = [n for n in pred_nums if n in current_loto]
            total_nhay = sum([current_loto.count(n) for n in found_hits])
            hit_report[f"Mức {lv}đ"] = f"{total_nhay} ({','.join(found_hits)})" if total_nhay > 0 else "0"
            if gdb_val in pred_nums:
                gdb_win_levels.append(f"{lv}đ")
    
    hit_report["Trúng GĐB"] = ", ".join(gdb_win_levels) if gdb_win_levels else "0"

    # --- B. TRUY VẾT & RESET ---
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                num_from_past_pos = old_digits[i] + old_digits[j]
                if num_from_past_pos in current_loto:
                    new_wire_scores[i][j] = old_scores[i][j] + 1
    
    # --- C. TẠO DỰ BÁO CHO KỲ TIẾP THEO ---
    new_preds = {}
    max_s = int(new_wire_scores.max())
    if max_s > 0:
        for s in range(1, max_s + 1):
            coords = np.argwhere(new_wire_scores == s)
            total_w = len(coords)
            if total_w == 0: continue
            level_map = {}
            for r, c in coords:
                num_for_future = current_digits[r] + current_digits[c]
                level_map[num_for_future] = level_map.get(num_for_future, 0) + 1
            isolated = [n for n, count in level_map.items() if count == 1]
            new_preds[int(s)] = {"nums": sorted(isolated), "total_wires": int(total_w)}

    st.session_state['db']['wire_scores'] = new_wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    st.session_state['db']['last_predictions'] = new_preds
    st.session_state['db']['history'].insert(0, hit_report)

# --- 3. GIAO DIỆN ---
st.markdown("<h1 style='text-align: center; color: #00FFAA;'>⚡ MATRIX V8.9: DATA PERSISTENCE</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("💾 QUẢN LÝ DỮ LIỆU")
    # Ô TẢI FILE
    uploaded_file = st.file_uploader("Nạp file .json cũ", type=['json'])
    if uploaded_file is not None:
        if st.button("📥 PHỤC HỒI DỮ LIỆU"):
            data_load = json.load(uploaded_file)
            st.session_state['db'] = data_load
            st.success("Đã phục hồi ma trận và lịch sử!")
            st.rerun()
            
    # Ô XUẤT FILE
    if st.session_state['db']['last_digits']:
        data_json = json.dumps(st.session_state['db'], ensure_ascii=False)
        st.download_button("💾 LƯU DỮ LIỆU (.JSON)", data_json, file_name="matrix_data.json", mime="application/json")

    st.divider()
    st.header("📸 NHẬP KẾT QUẢ MỚI")
    uploaded_img = st.file_uploader("Quét ảnh bảng KQ", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("BẮT ĐẦU QUÉT"):
        with st.spinner("OCR..."):
            reader = load_ocr()
            res = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
            nums = [n for n in res if n.isdigit() and 2 <= len(n) <= 5]
            if nums: 
                st.session_state['raw_input'] = ", ".join(nums)
                st.session_state['gdb_ocr'] = nums[0][-2:]
                st.session_state['loto_list_display'] = [n[-2:] for n in nums[1:27]]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Bảng giải gốc:", value=st.session_state['raw_input'], height=100)
    gdb_confirm = st.text_input("GĐB (2 số cuối):", value=st.session_state.get('gdb_ocr', ""), max_chars=2)

    if st.button("🔥 CHẠY TRUY VẾT", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        full_str = "".join(raw)
        if len(full_str) >= TOTAL_POS:
            process_matrix(full_str[:TOTAL_POS], [s[-2:] for s in raw[:27]], gdb_confirm)
            st.rerun()

    st.button("🚨 RESET ALL", on_click=lambda: st.session_state.clear())

# --- 4. HIỂN THỊ ---
col1, col2 = st.columns([1, 2.5])

with col1:
    st.subheader("🎯 DÀN DỰ BÁO")
    preds = st.session_state['db'].get('last_predictions', {})
    if preds:
        # Khi load từ JSON, key bị biến thành string, cần ép lại int để sort
        sorted_keys = sorted([int(k) for k in preds.keys()], reverse=True)
        for lv in sorted_keys:
            data = preds[str(lv)] if str(lv) in preds else preds[lv]
            with st.expander(f"⭐ MỨC {lv}đ (Quân: {len(data['nums'])} | Dây: {data['total_wires']})", expanded=(lv == sorted_keys[0])):
                st.code(", ".join(data['nums']) if data['nums'] else "Không có số độc nhất")
    else: st.info("Nạp file hoặc quét kỳ 1 để bắt đầu.")

with col2:
    st.subheader("📋 LỊCH SỬ ĐỐI SOÁT")
    if st.session_state['db']['history']:
        df_hist = pd.DataFrame(st.session_state['db']['history']).fillna("0")
        cols = list(df_hist.columns)
        if "Trúng GĐB" in cols:
            cols.insert(2, cols.pop(cols.index("Trúng GĐB")))
            df_hist = df_hist[cols]
        st.dataframe(df_hist, use_container_width=True)

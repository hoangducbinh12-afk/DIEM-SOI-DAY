import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Matrix V8.2 - Ultimate Verification", layout="wide")
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
if 'gdb_ocr' not in st.session_state: st.session_state['gdb_ocr'] = ""
if 'loto_list_display' not in st.session_state: st.session_state['loto_list_display'] = []

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

# --- 2. LOGIC ĐIỀU HÀNH (HARD RESET + FULL VERIFICATION) ---

def process_matrix(current_digits, current_loto, gdb_val):
    # Lấy dữ liệu từ session
    wire_scores = np.array(st.session_state['db']['wire_scores'])
    old_digits = st.session_state['db']['last_digits']
    old_loto_set = set(st.session_state['db']['last_loto'])
    old_preds = st.session_state['db']['last_predictions']
    
    # --- A. ĐỐI SOÁT NHÁY (Dàn cũ vs KQ mới nạp) ---
    hit_report = {"STT": len(st.session_state['db']['history']) + 1, "GĐB": gdb_val}
    if old_preds:
        for lv, data in old_preds.items():
            pred_nums = data['nums']
            found_hits = []
            for n in pred_nums:
                count = current_loto.count(n)
                if count > 0:
                    found_hits.extend([n] * count)
            
            total_nhay = len(found_hits)
            hit_report[f"Mức {lv}đ"] = f"{total_nhay} ({','.join(found_hits)})" if total_nhay > 0 else "0"

    # --- B. CẬP NHẬT MA TRẬN (HARD RESET) ---
    new_wire_scores = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int)
    if len(old_digits) >= TOTAL_POS and old_loto_set:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                # Kiểm tra ánh xạ kỳ trước
                num_past = old_digits[i] + old_digits[j]
                if num_past in old_loto_set:
                    # Nếu nổ: Lấy điểm cũ + 1
                    new_wire_scores[i][j] = wire_scores[i][j] + 1
                # Không nổ mặc định là 0
    wire_scores = new_wire_scores

    # --- C. CHIẾT XUẤT DÀN ĐỘC NHẤT ---
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
            
            # Lọc độc nhất nội bộ mức điểm
            isolated = [n for n, count in level_map.items() if count == 1]
            if isolated or total_wires_at_s > 0:
                new_preds[s] = {"nums": sorted(isolated), "total_wires": total_wires_at_s}

    # ĐỒNG BỘ SESSION
    st.session_state['db']['wire_scores'] = wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    st.session_state['db']['last_predictions'] = new_preds
    st.session_state['db']['history'].insert(0, hit_report)

# --- 3. GIAO DIỆN ---
st.markdown("<h1 style='text-align: center; color: #00FFAA;'>⚡ MATRIX V8.2: ULTIMATE VERIFICATION</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("📸 NHẬP LIỆU & OCR")
    uploaded_img = st.file_uploader("Quét ảnh bảng KQ", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("BẮT ĐẦU QUÉT"):
        with st.spinner("Đang trích xuất..."):
            reader = load_ocr()
            res = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
            nums = [n for n in res if n.isdigit() and 2 <= len(n) <= 5]
            if nums: 
                st.session_state['raw_input'] = ", ".join(nums)
                st.session_state['gdb_ocr'] = nums[0][-2:]
                st.session_state['loto_list_display'] = [n[-2:] for n in nums[1:27]]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Dữ liệu thô (OCR):", value=st.session_state['raw_input'], height=150)
    
    st.subheader("🔍 ĐỐI SOÁT QUÉT")
    gdb_confirm = st.text_input("1. Giải Đặc Biệt (2 số cuối):", value=st.session_state['gdb_ocr'], max_chars=2)
    loto_display = st.text_area("2. Danh sách 26 giải lô:", value=", ".join(st.session_state['loto_list_display']), height=100)

    if st.button("🔥 CHẠY PHÂN TÍCH", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        full_str = "".join(raw)
        if len(full_str) >= TOTAL_POS:
            process_matrix(full_str[:TOTAL_POS], [s[-2:] for s in raw[:27]], gdb_confirm)
            st.rerun()
        else:
            st.error(f"Dữ liệu thiếu: mới có {len(full_str)} ký tự, cần đủ {TOTAL_POS}!")

    if st.button("🚨 LÀM MỚI TOÀN BỘ"):
        st.session_state.clear()
        st.rerun()

# --- 4. HIỂN THỊ ---
col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("🎯 DÀN ĐỘC NHẤT")
    preds = st.session_state['db'].get('last_predictions', {})
    if preds:
        for lv in sorted(preds.keys(), reverse=True):
            data = preds[lv]
            with st.expander(f"⭐ MỨC {lv} ĐIỂM (Dây: {data['total_wires']})", expanded=(lv == max(preds.keys()))):
                st.write(f"Số quân độc nhất: **{len(data['nums'])}**")
                st.code(", ".join(data['nums']) if data['nums'] else "Không có số độc nhất")
    else:
        st.info("Chưa có dàn. Cần nạp ít nhất 2 kỳ.")

with col2:
    st.subheader("📋 BÁO CÁO LỊCH SỬ")
    if st.session_state['db']['history']:
        df_hist = pd.DataFrame(st.session_state['db']['history']).fillna("0")
        st.dataframe(df_hist, use_container_width=True)
    
    st.divider()
    if st.session_state['db']['last_digits']:
        st.download_button("💾 XUẤT JSON", json.dumps(st.session_state['db']), "matrix_v82.json")

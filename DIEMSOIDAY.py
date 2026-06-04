import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Matrix V9.2 - Sniper 20", layout="wide")
TOTAL_POS = 107 

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "last_loto": [],
        "history": [],
        "last_predictions": {},
        "filtered_20": []
    }

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

# --- 2. LOGIC ĐIỀU HÀNH ---

def process_matrix(current_digits, current_loto, gdb_val):
    db = st.session_state['db']
    old_scores = np.array(db['wire_scores'], dtype=int)
    old_digits = db['last_digits']
    old_preds = db['last_predictions']
    old_filtered_20 = db.get('filtered_20', [])
    
    new_wire_scores = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int)
    
    # --- A. ĐỐI SOÁT NHÁY DÀN 20 QUÂN ---
    hit_report = {"STT": len(db['history']) + 1, "GĐB": gdb_val}
    if old_filtered_20:
        found_20 = [n for n in old_filtered_20 if n in current_loto]
        count_20 = sum([current_loto.count(n) for n in found_20])
        hit_report["Dàn 20q"] = f"{count_20} ({','.join(found_20)})" if count_20 > 0 else "0"

    # --- B. CẬP NHẬT ĐIỂM PREDATOR ---
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                num_past = old_digits[i] + old_digits[j]
                if num_past in current_loto:
                    new_wire_scores[i][j] = old_scores[i][j] + 1

    # --- C. CHIẾT XUẤT & ÉP DÀN SNIPER 20 ---
    new_preds = {}
    # Bảng tính toán độ nhiễu (Convergence Noise)
    noise_map = {str(i).zfill(2): 0 for i in range(100)}
    
    max_s = int(new_wire_scores.max())
    if max_s > 0:
        for s in range(1, max_s + 1):
            coords = np.argwhere(new_wire_scores == s)
            if len(coords) == 0: continue
            
            level_map = {}
            for r, c in coords:
                num = current_digits[r] + current_digits[c]
                level_map[num] = level_map.get(num, 0) + 1
                # Tính toán nhiễu giao thoa 1đ và 2đ
                if s == 1: noise_map[num] += 1
                if s == 2: noise_map[num] += 2 # Ưu tiên loại bỏ nhiễu ở mức 2đ
            
            isolated = [n for n, count in level_map.items() if count == 1]
            new_preds[int(s)] = {"nums": sorted(isolated), "total_wires": int(len(coords))}

    # ÉP DÀN 20:
    union_all = set()
    for lv in [2, 3, 4]:
        if lv in new_preds: union_all.update(new_preds[lv]['nums'])
    
    # Sắp xếp theo điểm Nhiễu (càng ít nhiễu càng ưu tiên giữ lại)
    # Nếu điểm nhiễu bằng nhau, ưu tiên con số có mức điểm cao nhất trong ma trận
    def get_max_level(num):
        for lv in [4, 3, 2]:
            if lv in new_preds and num in new_preds[lv]['nums']: return lv
        return 0

    sorted_for_20 = sorted(list(union_all), key=lambda x: (noise_map[x], -get_max_level(x)))
    
    final_20 = sorted(sorted_for_20[:20]) # Lấy 20 con "sạch" nhất

    # Lưu State
    st.session_state['db']['wire_scores'] = new_wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    st.session_state['db']['last_predictions'] = new_preds
    st.session_state['db']['filtered_20'] = final_20
    st.session_state['db']['history'].insert(0, hit_report)

# --- 3. GIAO DIỆN ---
st.title("⚡ MATRIX V9.2: SNIPER 20")

with st.sidebar:
    st.header("💾 DATA & OCR")
    uploaded_file = st.file_uploader("Nạp JSON", type=['json'])
    if uploaded_file and st.button("📥 PHỤC HỒI"):
        st.session_state['db'] = json.load(uploaded_file)
        st.rerun()
    
    if st.session_state['db']['last_digits']:
        st.download_button("💾 LƯU JSON", json.dumps(st.session_state['db']), "matrix_v92.json")

    uploaded_img = st.file_uploader("Quét ảnh KQ", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("QUÉT OCR"):
        reader = load_ocr()
        res = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
        nums = [n for n in res if n.isdigit() and 2 <= len(n) <= 5]
        if nums: 
            st.session_state['raw_input'] = ", ".join(nums)
            st.session_state['gdb_ocr'] = nums[0][-2:]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Dữ liệu thô:", value=st.session_state.get('raw_input', ""), height=100)
    gdb_confirm = st.text_input("GĐB:", value=st.session_state.get('gdb_ocr', ""), max_chars=2)

    if st.button("🔥 CHẠY SNIPER 20", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len("".join(raw)) >= TOTAL_POS:
            process_matrix("".join(raw)[:TOTAL_POS], [s[-2:] for s in raw[:27]], gdb_confirm)
            st.rerun()

# --- 4. HIỂN THỊ ---
c1, c2 = st.columns([1, 2.5])

with c1:
    st.subheader("🎯 DÀN SNIPER 20")
    f20 = st.session_state['db'].get('filtered_20', [])
    if f20:
        with st.container(border=True):
            st.write(f"Đã loại bỏ quân hội tụ nhiễu 1đ & 2đ")
            st.write(f"Số lượng: **{len(f20)}**")
            st.code(", ".join(f20))

    st.subheader("📊 CHI TIẾT MỨC ĐIỂM")
    preds = st.session_state['db'].get('last_predictions', {})
    if preds:
        for lv in sorted([int(k) for k in preds.keys()], reverse=True):
            data = preds[str(lv)] if str(lv) in preds else preds[lv]
            with st.expander(f"Mức {lv}đ ({len(data['nums'])}q)"):
                st.code(", ".join(data['nums']))

with c2:
    st.subheader("📋 LỊCH SỬ SNIPER")
    if st.session_state['db']['history']:
        df_hist = pd.DataFrame(st.session_state['db']['history']).fillna("0")
        # Đưa cột Dàn 20q lên đầu
        cols = list(df_hist.columns)
        if "Dàn 20q" in cols:
            cols.insert(2, cols.pop(cols.index("Dàn 20q")))
            df_hist = df_hist[cols]
        st.dataframe(df_hist, use_container_width=True)

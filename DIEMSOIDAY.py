import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Matrix V9.1 - Precision 27", layout="wide")
TOTAL_POS = 107 

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "last_loto": [],
        "history": [],
        "last_predictions": {},
        "filtered_27": [] # Lưu dàn 27 quân của kỳ trước để đối soát
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

# --- 2. LOGIC ĐIỀU HÀNH ---

def process_matrix(current_digits, current_loto, gdb_val):
    db = st.session_state['db']
    old_scores = np.array(db['wire_scores'], dtype=int)
    old_digits = db['last_digits']
    old_preds = db['last_predictions']
    old_filtered_27 = db.get('filtered_27', [])
    
    new_wire_scores = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int)
    
    # --- A. ĐỐI SOÁT NHÁY ---
    hit_report = {"STT": len(db['history']) + 1, "GĐB": gdb_val}
    
    # Đối soát dàn 27 quân tinh lọc của kỳ TRƯỚC
    if old_filtered_27:
        found_27 = [n for n in old_filtered_27 if n in current_loto]
        count_27 = sum([current_loto.count(n) for n in found_27])
        hit_report["Dàn 27q"] = f"{count_27} ({','.join(found_27)})" if count_27 > 0 else "0"

    # Đối soát các mức điểm gốc
    if old_preds:
        fixed_old_preds = {int(k): v for k, v in old_preds.items()}
        for lv in sorted(fixed_old_preds.keys(), reverse=True):
            nums = fixed_old_preds[lv]['nums']
            found = [n for n in nums if n in current_loto]
            count = sum([current_loto.count(n) for n in found])
            hit_report[f"{lv}đ"] = f"{count}" if count > 0 else "0"

    # --- B. CẬP NHẬT ĐIỂM (PREDATOR LOGIC) ---
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                num_past = old_digits[i] + old_digits[j]
                if num_past in current_loto:
                    new_wire_scores[i][j] = old_scores[i][j] + 1

    # --- C. CHIẾT XUẤT & ÉP DÀN 27 QUÂN ---
    new_preds = {}
    mapping_1d = {str(i).zfill(2): 0 for i in range(100)}
    
    max_s = int(new_wire_scores.max())
    if max_s > 0:
        for s in range(1, max_s + 1):
            coords = np.argwhere(new_wire_scores == s)
            if len(coords) == 0: continue
            
            level_map = {}
            for r, c in coords:
                num = current_digits[r] + current_digits[c]
                level_map[num] = level_map.get(num, 0) + 1
                if s == 1: mapping_1d[num] += 1 # Thống kê mật độ 1đ
            
            isolated = [n for n, count in level_map.items() if count == 1]
            new_preds[int(s)] = {"nums": sorted(isolated), "total_wires": int(len(coords))}

    # LOGIC ÉP DÀN 27:
    union_234 = set()
    for lv in [2, 3, 4]:
        if lv in new_preds: union_234.update(new_preds[lv]['nums'])
    
    # Sắp xếp các số trong dàn 234 theo mật độ dây 1đ tăng dần (ưu tiên con ít dây 1đ hơn)
    # Nếu bằng điểm 1đ thì ưu tiên số nhỏ hơn
    sorted_by_1d = sorted(list(union_234), key=lambda x: (mapping_1d[x], int(x)))
    
    # Lấy đủ 27 con đầu tiên (ít "nhiễu" nhất)
    # Nếu dàn gốc ít hơn 27 con thì lấy hết
    final_27 = sorted(sorted_by_1d[:27])

    # Cập nhật state
    st.session_state['db']['wire_scores'] = new_wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    st.session_state['db']['last_predictions'] = new_preds
    st.session_state['db']['filtered_27'] = final_27
    st.session_state['db']['history'].insert(0, hit_report)

# --- 3. GIAO DIỆN ---
st.title("⚡ MATRIX V9.1: PRECISION 27")

with st.sidebar:
    st.header("💾 DATA & OCR")
    uploaded_file = st.file_uploader("Nạp JSON", type=['json'])
    if uploaded_file and st.button("📥 PHỤC HỒI"):
        st.session_state['db'] = json.load(uploaded_file)
        st.rerun()
    
    if st.session_state['db']['last_digits']:
        st.download_button("💾 LƯU JSON", json.dumps(st.session_state['db']), "matrix_v91.json")

    uploaded_img = st.file_uploader("Quét ảnh KQ", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("QUÉT OCR"):
        reader = load_ocr()
        res = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
        nums = [n for n in res if n.isdigit() and 2 <= len(n) <= 5]
        if nums: 
            st.session_state['raw_input'] = ", ".join(nums)
            st.session_state['gdb_ocr'] = nums[0][-2:]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Dữ liệu thô:", value=st.session_state['raw_input'], height=100)
    gdb_confirm = st.text_input("GĐB:", value=st.session_state.get('gdb_ocr', ""), max_chars=2)

    if st.button("🔥 CHẠY TRUY VẾT", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len("".join(raw)) >= TOTAL_POS:
            process_matrix("".join(raw)[:TOTAL_POS], [s[-2:] for s in raw[:27]], gdb_confirm)
            st.rerun()
    st.button("🚨 RESET ALL", on_click=lambda: st.session_state.clear())

# --- 4. HIỂN THỊ ---
c1, c2 = st.columns([1, 2.5])

with c1:
    st.subheader("🎯 SIÊU DÀN 27 QUÂN")
    f27 = st.session_state['db'].get('filtered_27', [])
    if f27:
        with st.container(border=True):
            st.write(f"Dàn tinh lọc từ mức 2,3,4 (Loại bỏ 1đ nóng)")
            st.write(f"Số lượng: **{len(f27)}**")
            st.code(", ".join(f27))
    
    st.divider()
    st.subheader("📊 CHI TIẾT MỨC ĐIỂM")
    preds = st.session_state['db'].get('last_predictions', {})
    if preds:
        for lv in sorted([int(k) for k in preds.keys()], reverse=True):
            data = preds[str(lv)] if str(lv) in preds else preds[lv]
            with st.expander(f"Mức {lv}đ ({len(data['nums'])}q)"):
                st.code(", ".join(data['nums']))

with c2:
    st.subheader("📋 LỊCH SỬ & HIỆU QUẢ")
    if st.session_state['db']['history']:
        df_hist = pd.DataFrame(st.session_state['db']['history']).fillna("0")
        # Đưa dàn 27q lên đầu bảng
        cols = list(df_hist.columns)
        if "Dàn 27q" in cols:
            cols.insert(2, cols.pop(cols.index("Dàn 27q")))
            df_hist = df_hist[cols]
        st.dataframe(df_hist, use_container_width=True)

import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Matrix V7.8 - Full Transparency", layout="wide")
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

# --- 2. LOGIC NÂNG CẤP: ĐỘC NHẤT NỘI BỘ MỨC ĐIỂM ---

def process_matrix(current_digits, current_loto, gdb_val):
    db = st.session_state['db']
    old_digits = db['last_digits']
    old_loto_list = db['last_loto']
    old_loto_set = set(old_loto_list)
    old_preds = db['last_predictions']
    wire_scores = np.array(db['wire_scores'])
    
    # --- A. ĐỐI SOÁT NHÁY (Dựa trên dàn dự báo cũ) ---
    hit_report = {"STT": len(db['history']) + 1, "GĐB": gdb_val}
    if old_preds:
        for lv, pred_nums in old_preds.items():
            # Lấy danh sách những con nổ thực tế trong dàn
            found_hits = []
            for n in pred_nums:
                count = current_loto.count(n)
                if count > 0:
                    found_hits.extend([n] * count)
            
            total_nhay = len(found_hits)
            hit_report[f"Mức {lv}đ"] = f"{total_nhay} ({','.join(found_hits)})" if total_nhay > 0 else "0"

    # --- B. CẬP NHẬT MA TRẬN ĐẦU-ĐUÔI ---
    if len(old_digits) >= TOTAL_POS and old_loto_set:
        new_wire_scores = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int)
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                num_past = old_digits[i] + old_digits[j]
                if num_past in old_loto_set:
                    new_wire_scores[i][j] = wire_scores[i][j] + 1
                else:
                    new_wire_scores[i][j] = 0
        wire_scores = new_wire_scores

    # --- C. CHIẾT XUẤT DÀN (ĐỘC NHẤT TRONG TỪNG MỨC) ---
    new_preds = {}
    if len(current_digits) >= TOTAL_POS:
        max_s = int(wire_scores.max())
        for s in range(1, max_s + 1): # Duyệt qua từng mức điểm
            coords = np.argwhere(wire_scores == s)
            if len(coords) == 0: continue
            
            level_map = {}
            for r, c in coords:
                num = current_digits[r] + current_digits[c]
                level_map[num] = level_map.get(num, 0) + 1
            
            # CHỈ LỌC ĐỘC NHẤT NỘI BỘ MỨC S
            # (Nếu mức 1 có 39 và mức 7 có 39, cả hai đều giữ nếu chúng là duy nhất trong mức đó)
            isolated = [n for n, count in level_map.items() if count == 1]
            
            if isolated:
                new_preds[s] = sorted(isolated)

    # Cập nhật và lưu
    st.session_state['db']['wire_scores'] = wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    st.session_state['db']['last_predictions'] = new_preds
    st.session_state['db']['history'].insert(0, hit_report)

# --- 3. GIAO DIỆN ---
st.title("⚡ MATRIX V7.8: FULL TRANSPARENCY")

with st.sidebar:
    st.header("📸 NHẬP DỮ LIỆU")
    uploaded_img = st.file_uploader("Quét bảng KQ", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("QUÉT OCR"):
        with st.spinner("Đang trích xuất..."):
            reader = load_ocr()
            res = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
            nums = [n for n in res if n.isdigit() and 2 <= len(n) <= 5]
            if nums: st.session_state['raw_input'] = ", ".join(nums)
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Bảng giải:", value=st.session_state['raw_input'], height=150)
    gdb_confirm = st.text_input("GĐB (2 số cuối):", max_chars=2)

    if st.button("🔥 CHẠY TRUY VẾT", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        full_str = "".join(raw)
        if len(full_str) >= TOTAL_POS:
            process_matrix(full_str[:TOTAL_POS], [s[-2:] for s in raw[:27]], gdb_confirm)
            st.rerun()
        else:
            st.error(f"Dữ liệu mới có {len(full_str)} ký tự, cần đủ {TOTAL_POS}!")

    if st.button("🚨 RESET ALL"):
        st.session_state.clear()
        st.rerun()

col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("🎯 DÀN ĐỘC NHẤT NỘI BỘ")
    preds = st.session_state['db'].get('last_predictions', {})
    if preds:
        for lv in sorted(preds.keys(), reverse=True):
            with st.expander(f"⭐ MỨC {lv} ĐIỂM", expanded=True):
                st.write(f"Số lượng: {len(preds[lv])}")
                st.code(", ".join(preds[lv]))
    else:
        st.info("Chưa có dàn. Cần ít nhất 2 kỳ nạp.")

with col2:
    st.subheader("📋 LỊCH SỬ ĐỐI SOÁT")
    if st.session_state['db']['history']:
        # Sắp xếp lịch sử để nhìn mức cao trước
        df_hist = pd.DataFrame(st.session_state['db']['history']).fillna("0")
        st.dataframe(df_hist, use_container_width=True)
    
    st.divider()
    if st.session_state['db']['last_digits']:
        st.download_button("💾 XUẤT DATA (.JSON)", json.dumps(st.session_state['db']), "matrix_v78.json")

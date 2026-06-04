import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. KHỞI TẠO HỆ THỐNG ---
st.set_page_config(page_title="Matrix V7.6.1 - Vùng Điểm Chiến Thuật", layout="wide")
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

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

# --- 2. LOGIC ĐIỀU HÀNH ---

def process_matrix(current_digits, current_loto, gdb_val):
    db = st.session_state['db']
    old_digits = db['last_digits']
    old_loto_list = db['last_loto'] 
    old_loto_set = set(old_loto_list) 
    old_preds = db['last_predictions']
    wire_scores = np.array(db['wire_scores'])
    
    # --- A. ĐỐI SOÁT NHÁY CHI TIẾT THEO VÙNG ---
    hit_report = {"STT": len(db['history']) + 1, "GĐB": gdb_val}
    if old_preds:
        # Lấy danh sách tất cả mức điểm đang có để tạo cột bảng
        for lv, pred_nums in old_preds.items():
            hit_nums_in_res = []
            for n in pred_nums:
                count = current_loto.count(n)
                if count > 0:
                    hit_nums_in_res.extend([n] * count)
            
            total_hits = len(hit_nums_in_res)
            # Hiển thị: Tổng nháy (Danh sách các con nổ)
            hit_report[f"Mức {lv}đ"] = f"{total_hits} ({','.join(hit_nums_in_res)})" if total_hits > 0 else "0"

    # --- B. CẬP NHẬT MA TRẬN ĐẦU -> ĐUÔI (11.449 DÂY) ---
    if old_digits and old_loto_set:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                # Quy tắc Đầu i ghép Đuôi j
                num_past = old_digits[i] + old_digits[j]
                if num_past in old_loto_set:
                    wire_scores[i][j] += 1
                else:
                    wire_scores[i][j] = 0
    
    # --- C. CHIẾT XUẤT TÍN HIỆU ĐỘC NHẤT ---
    new_preds = {}
    if current_digits:
        res_list = []
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                sc = wire_scores[i][j]
                if sc > 0:
                    num_cur = current_digits[i] + current_digits[j]
                    res_list.append({"num": num_cur, "score": sc})
        
        if res_list:
            df = pd.DataFrame(res_list)
            # LỌC ĐỘC NHẤT: Chỉ giữ lại số được tạo bởi 1 dây duy nhất trên toàn ma trận
            counts = df['num'].value_counts()
            unique_list = counts[counts == 1].index.tolist()
            
            df_final = df[df['num'].isin(unique_list)]
            for s in sorted(df_final['score'].unique(), reverse=True):
                new_preds[int(s)] = sorted(df_final[df_final['score'] == s]['num'].tolist())

    # Lưu và đồng bộ dữ liệu
    st.session_state['db']['wire_scores'] = wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    st.session_state['db']['last_predictions'] = new_preds
    st.session_state['db']['history'].insert(0, hit_report)

# --- 3. GIAO DIỆN ---
st.markdown("<h1 style='text-align: center; color: #00FFAA;'>⚡ MATRIX V7.6.1: VÙNG ĐIỂM CHIẾN THUẬT</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("📸 NHẬP KQ KỲ MỚI")
    uploaded_img = st.file_uploader("Quét ảnh bảng kết quả", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("BẮT ĐẦU QUÉT OCR"):
        with st.spinner("Đang trích xuất dữ liệu..."):
            reader = load_ocr()
            res = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
            nums = [n for n in res if n.isdigit() and 2 <= len(n) <= 5]
            if nums: 
                st.session_state['raw_input'] = ", ".join(nums)
                st.session_state['gdb_ocr'] = nums[0][-2:]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("27 giải loto:", value=st.session_state['raw_input'], height=150)
    gdb_confirm = st.text_input("Xác nhận GĐB (2 số cuối):", value=st.session_state['gdb_ocr'], max_chars=2)

    if st.button("🔥 CHẠY ĐỐI SOÁT & TRUY VẾT", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len(raw) >= 27:
            process_matrix("".join(raw)[:TOTAL_POS], [s[-2:] for s in raw[:27]], gdb_confirm)
            st.rerun()
    
    st.divider()
    if st.button("🚨 XÓA HẾT DỮ LIỆU"):
        st.session_state.clear()
        st.rerun()

col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("🎯 DÀN ĐỘC NHẤT KỲ TỚI")
    preds = st.session_state['db'].get('last_predictions', {})
    if not preds:
        st.info("Nạp kỳ 1 để lấy tọa độ, kỳ 2 bắt đầu có dàn.")
    else:
        for lv in sorted(preds.keys(), reverse=True):
            with st.expander(f"⭐ VÙNG THÔNG {lv} KỲ", expanded=True):
                st.write(f"Số quân: {len(preds[lv])}")
                st.code(", ".join(preds[lv]))

with col2:
    st.subheader("📋 BÁO CÁO HIỆU QUẢ THEO VÙNG")
    if st.session_state['db']['history']:
        # Hiển thị bảng lịch sử, điền 0 vào những ô không có dữ liệu
        df_hist = pd.DataFrame(st.session_state['db']['history']).fillna("0")
        st.dataframe(df_hist, use_container_width=True)
    
    st.divider()
    if st.session_state['db']['last_digits']:
        st.download_button("💾 TẢI FILE MA TRẬN (.JSON)", json.dumps(st.session_state['db']), "matrix_v761.json")

st.caption("Lưu ý: 'Mức Xđ' là kết quả của dàn dự báo X điểm từ kỳ trước đối soát với kết quả vừa nạp.")

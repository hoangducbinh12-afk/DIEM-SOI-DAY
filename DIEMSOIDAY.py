import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Matrix V7.2 - Precision Check", layout="wide")
TOTAL_POS = 107 

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "last_loto": [],
        "history": [],
        "last_predictions": {} # Lưu dàn dự báo của kỳ trước để đối soát nháy
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""
if 'gdb_ocr' not in st.session_state: st.session_state['gdb_ocr'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

# --- 2. HÀM XỬ LÝ LOGIC ---

def process_matrix(current_digits, current_loto, gdb_val):
    db = st.session_state['db']
    old_digits = db['last_digits']
    old_loto = set(db['last_loto'])
    old_preds = db['last_predictions']
    wire_scores = np.array(db['wire_scores'])
    
    # --- BƯỚC A: ĐỐI SOÁT NHÁY (Dựa trên dàn cũ và KQ mới nạp) ---
    hit_report = {"STT": len(db['history']) + 1, "GĐB": gdb_val}
    if old_preds:
        for lv, nums in old_preds.items():
            # Đếm tổng số nháy nổ trong 27 giải
            count = sum([current_loto.count(n) for n in nums])
            hit_report[f"Dàn {lv}đ"] = f"{count} nháy"
    
    # --- BƯỚC B: CẬP NHẬT ĐIỂM DÂY ---
    if old_digits and old_loto:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                num_past = old_digits[i] + old_digits[j]
                if num_past in old_loto:
                    wire_scores[i][j] += 1
                else:
                    wire_scores[i][j] = 0
    
    # --- BƯỚC C: TẠO DÀN DỰ BÁO ĐỘC NHẤT CHO KỲ TỚI ---
    new_preds = {}
    if current_digits:
        max_s = int(wire_scores.max())
        if max_s > 0:
            for s in range(1, max_s + 1):
                mask = (wire_scores == s)
                if not np.any(mask): continue
                
                coords = np.argwhere(mask)
                level_map = {}
                # Kiểm tra từng sợi dây trong hạng cân s
                for r, c in coords:
                    num = current_digits[r] + current_digits[c]
                    level_map[num] = level_map.get(num, 0) + 1
                
                # CHỈ LẤY ÁNH XẠ ĐƯỢC TẠO THÀNH TỪ ĐÚNG 1 SỢI DÂY
                isolated = [n for n, count in level_map.items() if count == 1]
                if isolated:
                    new_preds[s] = sorted(isolated)

    # Lưu lại trạng thái
    st.session_state['db']['wire_scores'] = wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    st.session_state['db']['last_predictions'] = new_preds
    st.session_state['db']['history'].insert(0, hit_report)

# --- 3. GIAO DIỆN ---

st.markdown("<h1 style='text-align: center; color: #00FFAA;'>💎 MATRIX V7.2: PRECISION CHECK</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("📸 NHẬP DỮ LIỆU")
    uploaded_img = st.file_uploader("Quét ảnh bảng KQ", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("BẮT ĐẦU OCR"):
        with st.spinner("Đang trích xuất..."):
            reader = load_ocr()
            results = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
            nums = [n for n in results if n.isdigit() and 2 <= len(n) <= 5]
            if nums: 
                st.session_state['raw_input'] = ", ".join(nums)
                st.session_state['gdb_ocr'] = nums[0][-2:] # GĐB thường là số đầu tiên đọc được
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Dữ liệu 27 giải:", value=st.session_state['raw_input'], height=150)
    gdb_input = st.text_input("Xác nhận GĐB (2 số cuối):", value=st.session_state['gdb_ocr'], max_chars=2)

    if st.button("🔥 CHẠY TRUY VẾT & ĐỐI SOÁT", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len(raw) >= 27:
            c_digits = "".join(raw)[:TOTAL_POS]
            c_loto = [s[-2:] for s in raw[:27]]
            process_matrix(c_digits, c_loto, gdb_input)
            st.rerun()
        else:
            st.error("Chưa đủ 27 giải!")

    if st.button("🚨 RESET ALL"):
        st.session_state.clear()
        st.rerun()

# --- 4. HIỂN THỊ ---

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🎯 DÀN ĐỘC NHẤT (CHO KỲ TỚI)")
    preds = st.session_state['db'].get('last_predictions', {})
    if not preds:
        st.info("Nạp kỳ tiếp theo để bắt đầu tính nhịp thông.")
    else:
        for lv in sorted(preds.keys(), reverse=True):
            with st.expander(f"⭐ CẦU THÔNG {lv} KỲ", expanded=True):
                nums = preds[lv]
                st.write(f"Số lượng: **{len(nums)}**")
                st.code(", ".join(nums))

with col2:
    st.subheader("📋 LỊCH SỬ ĐỐI SOÁT NHÁY")
    if st.session_state['db']['history']:
        # Hiển thị bảng lịch sử với số nháy ăn được của từng dàn
        df_hist = pd.DataFrame(st.session_state['db']['history'])
        st.dataframe(df_hist, use_container_width=True)
    
    st.divider()
    if st.session_state['db']['last_digits']:
        js = json.dumps(st.session_state['db'])
        st.download_button("💾 XUẤT DATA (.JSON)", js, file_name="matrix_v72_data.json")

# Giải thích thuật toán
st.caption("Ghi chú: 'Dàn Xđ' trong lịch sử là dàn độc nhất được tạo ra từ kỳ TRƯỚC ĐÓ, đối soát với kết quả vừa nạp.")

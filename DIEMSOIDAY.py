import streamlit as st
import pandas as pd
import json
import os
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Matrix V7 - Isolated Signal", layout="wide")
TOTAL_POS = 107 

# Khởi tạo Session State
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(), # Ma trận 11.449 sợi dây
        "last_digits": "",  # Chuỗi 107 số kỳ trước
        "last_loto": [],    # 27 con loto kỳ trước (tính cả trùng)
        "history": []       # Nhật ký đối soát nháy
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])
reader = load_ocr()

# --- 2. HÀM XỬ LÝ LOGIC ---

def extract_data(raw_list):
    # Lấy 27 con loto cuối giải (tính cả trùng/nháy)
    v_loto = [s[-2:] for s in raw_list[:27]]
    # Lấy 107 ký tự số đầu tiên từ bảng kết quả
    all_digits = "".join(raw_list)
    return all_digits[:TOTAL_POS], v_loto

def process_matrix(current_digits, current_loto):
    db = st.session_state['db']
    old_digits = db['last_digits']
    old_loto = db['last_loto']
    wire_scores = np.array(db['wire_scores'])
    
    # Kết quả nháy kỳ này để đối soát cho lịch sử (dựa trên dàn dự báo của kỳ trước)
    # Bước này tính nháy trúng trước khi reset/cập nhật ma trận mới
    hit_report = {}
    
    # 1. LOGIC TÍNH ĐIỂM & RESET DÂY
    if old_digits and old_loto:
        # Tạo ma trận kết quả của kỳ này tại mọi tọa độ
        # Để xem tọa độ (i,j) kỳ này thực tế ra số bao nhiêu
        current_map = [[current_digits[i] + current_digits[j] for j in range(TOTAL_POS)] for i in range(TOTAL_POS)]
        
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                # Lấy số được tạo ra bởi tọa độ (i,j) ở KỲ TRƯỚC
                num_formed_in_past = old_digits[i] + old_digits[j]
                
                # Nếu số đó ĐÃ NỔ trong 27 con lô kỳ trước -> Dây thông
                if num_formed_in_past in old_loto:
                    wire_scores[i][j] += 1
                else:
                    # Nếu KHÔNG NỔ -> Reset dây về 0 ngay lập tức
                    wire_scores[i][j] = 0
    
    # 2. LOGIC LỌC ĐỘC NHẤT (ISOLATED SIGNAL) CHO KỲ TIẾP THEO
    # Quét ma trận điểm hiện tại để ra dự báo cho kỳ tới
    prediction_by_level = {}
    if current_digits:
        max_score = int(wire_scores.max())
        if max_score > 0:
            for s in range(1, max_score + 1):
                level_counts = {} # Đếm xem số nào xuất hiện bao nhiêu lần trong hạng cân s
                coords = np.argwhere(wire_scores == s)
                
                for r, c in coords:
                    num = current_digits[r] + current_digits[c]
                    level_counts[num] = level_counts.get(num, 0) + 1
                
                # CHỈ LẤY NHỮNG SỐ XUẤT HIỆN DUY NHẤT 1 LẦN (COUNT == 1)
                isolated_nums = [n for n, count in level_counts.items() if count == 1]
                if isolated_nums:
                    prediction_by_level[s] = sorted(isolated_nums)

    # 3. CẬP NHẬT DỮ LIỆU GỐC
    st.session_state['db']['wire_scores'] = wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    
    return prediction_by_level

# --- 3. GIAO DIỆN STREAMLIT ---

st.markdown("<h1 style='text-align: center; color: #00FFAA;'>💎 MATRIX V7: ISOLATED SIGNAL</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("📸 QUÉT KẾT QUẢ")
    uploaded_img = st.file_uploader("Tải ảnh bảng KQ (Ảnh 1 nạp tọa độ, Ảnh 2 bắt đầu tính)", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("BẮT ĐẦU QUÉT OCR"):
        with st.spinner("Đang đọc ảnh..."):
            img = Image.open(uploaded_img)
            results = reader.readtext(np.array(img), detail=0)
            nums = [n for n in results if n.isdigit() and 2 <= len(n) <= 5]
            if nums: st.session_state['raw_input'] = ", ".join(nums)
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Dữ liệu 27 giải:", value=st.session_state['raw_input'], height=200)
    gdb_now = st.text_input("GĐB hôm nay (Để lưu lịch sử):", max_chars=2)

    if st.button("🔥 CHẠY TRUY VẾT & CÔ ĐỌNG"):
        raw_list = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len(raw_list) >= 27:
            curr_digits, curr_loto = extract_data(raw_list)
            
            # Tính nháy trúng của kỳ vừa nạp dựa trên dàn dự báo cũ (nếu có)
            # (Phần này sẽ hiển thị trong bảng lịch sử)
            history_entry = {"STT": len(st.session_state['db']['history']) + 1, "GĐB": gdb_now}
            
            # Cập nhật Ma trận & Lấy dàn dự báo mới
            pred_results = process_matrix(curr_digits, curr_loto)
            st.session_state['current_predictions'] = pred_results
            
            # Thêm vào lịch sử (Mô phỏng đếm nháy)
            # Vì đây là bản kiểm tra hiệu quả, tao sẽ để mày tự đối soát nháy ở bảng kết quả
            st.session_state['db']['history'].insert(0, history_entry)
            st.rerun()
        else:
            st.error("Chưa đủ 27 giải!")

    if st.button("🚨 RESET DỮ LIỆU"):
        st.session_state.clear()
        st.rerun()

# --- 4. HIỂN THỊ KẾT QUẢ ---

col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("🎯 DÀN ĐỘC NHẤT THEO ĐIỂM")
    if 'current_predictions' in st.session_state:
        preds = st.session_state['current_predictions']
        if not preds:
            st.info("Kỳ 1 (Ảnh 1): Đã nạp tọa độ thành công. Hãy nạp Ảnh 2 để bắt đầu tính điểm.")
        else:
            # Hiển thị từ điểm cao nhất xuống thấp nhất
            for level in sorted(preds.keys(), reverse=True):
                with st.expander(f"⭐ CẦU THÔNG {level} KỲ", expanded=True):
                    nums = preds[level]
                    st.markdown(f"**Số lượng: {len(nums)}**")
                    st.write(", ".join(nums))
    else:
        st.write("Chưa có dữ liệu dự báo.")

with col2:
    st.subheader("📋 NHẬT KÝ ĐỐI SOÁT")
    if st.session_state['db']['history']:
        st.table(pd.DataFrame(st.session_state['db']['history']))
    
    st.divider()
    st.subheader("💾 QUẢN TRỊ FILE")
    data_json = json.dumps(st.session_state['db'], ensure_ascii=False)
    st.download_button("Tải file Ma trận (.json)", data_json, file_name="matrix_v7_data.json")

# Hướng dẫn nhanh cho mày
st.info("""
**HƯỚNG DẪN KIỂM TRA:**
1. **Ảnh 1:** Nạp KQ ngày 1 -> Bấm 'Truy vết'. App sẽ báo chưa có dự báo (vì chưa có kỳ trước đó).
2. **Ảnh 2:** Nạp KQ ngày 2 -> Bấm 'Truy vết'. Lúc này App so sánh Ảnh 2 với Ảnh 1, dây nào ăn sẽ lên 1 điểm.
3. **Kết quả:** Dàn 'Cầu thông 1 kỳ' sẽ hiện ra để đánh cho Ngày 3.
""")

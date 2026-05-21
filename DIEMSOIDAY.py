import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH & KHỞI TẠO BIẾN TRẠNG THÁI ---
BIT_COUNT = 107
TOTAL_WIRES = BIT_COUNT * BIT_COUNT 
DEFAULT_SCORE = 100.0

# Khởi tạo các biến trong session_state để không bị lỗi NameError
if 'db' not in st.session_state:
    st.session_state['db'] = {str(i): {"score": DEFAULT_SCORE, "streak_win": 0, "streak_loss": 0} for i in range(TOTAL_WIRES)}
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""
if 'gdb_val' not in st.session_state: st.session_state['gdb_val'] = ""
if 'final_scores' not in st.session_state: st.session_state['final_scores'] = None
if 'v_loto' not in st.session_state: st.session_state['v_loto'] = []

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

reader = load_ocr()

# --- 2. HÀM TÍNH TOÁN MA TRẬN ---
def update_matrix(db, loto_list, gdb_loto):
    new_db = json.loads(json.dumps(db))
    num_scores = {f"{i:02d}": 0.0 for i in range(100)}
    for wire_id in range(TOTAL_WIRES):
        w_str = str(wire_id)
        wire = new_db[w_str]
        num_formed = f"{wire_id % 100:02d}"
        
        is_hit = num_formed in loto_list
        is_gdb = (num_formed == gdb_loto)
        hit_count = loto_list.count(num_formed)
        
        if is_hit:
            wire["streak_loss"] = 0
            wire["streak_win"] += 1
            if wire["streak_win"] <= 3:
                if is_gdb: wire["score"] += 5.0
                wire["score"] += float(hit_count)
            else:
                wire["score"] -= 0.5
        else:
            wire["streak_win"] = 0
            wire["streak_loss"] += 1
            if wire["streak_loss"] >= 4:
                wire["score"] += 0.5
        
        num_scores[num_formed] += wire["score"]
    return new_db, num_scores

# --- 3. GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Matrix 11.449", layout="wide")
st.title("⚡ MATRIX 11.449 - HỆ THỐNG PHÂN TÍCH ĐA TẦNG")

with st.sidebar:
    st.header("📂 CÀI ĐẶT & QUÉT")
    
    if st.button("🚨 RESET ALL (Về 100đ)"):
        st.session_state['db'] = {str(i): {"score": DEFAULT_SCORE, "streak_win": 0, "streak_loss": 0} for i in range(TOTAL_WIRES)}
        st.session_state['final_scores'] = None
        st.session_state['v_loto'] = []
        st.rerun()

    uploaded_img = st.file_uploader("Quét ảnh bảng kết quả", type=['jpg', 'jpeg', 'png'])
    if uploaded_img:
        img = Image.open(uploaded_img)
        st.image(img, caption="Ảnh đang quét")
        if st.button("BẮT ĐẦU QUÉT OCR"):
            with st.spinner("Đang đọc số..."):
                img_np = np.array(img)
                results = reader.readtext(img_np, detail=0)
                nums = [n for n in results if n.isdigit() and 2 <= len(n) <= 5]
                if nums:
                    st.session_state['raw_input'] = ", ".join(nums)
                    st.session_state['gdb_val'] = nums[0][-2:]
                st.rerun()

    st.session_state['raw_input'] = st.text_area("Dữ liệu 27 giải:", value=st.session_state['raw_input'], height=100)
    st.session_state['gdb_val'] = st.text_input("2 số cuối Đặc biệt:", value=st.session_state['gdb_val'], max_chars=2)

    if st.button("XÁC NHẬN DỮ LIỆU"):
        if st.session_state['raw_input'] and st.session_state['gdb_val']:
            raw_list = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
            st.session_state['v_loto'] = [n[-2:] for n in raw_list[:27]]
            st.success("Đã xác nhận dữ liệu loto!")
        else:
            st.error("Thiếu dữ liệu!")

    if st.button("🔥 CHẠY MA TRẬN"):
        if st.session_state['v_loto']:
            with st.spinner("Đang xử lý 11.449 sợi dây..."):
                new_db, scores = update_matrix(st.session_state['db'], st.session_state['v_loto'], st.session_state['gdb_val'])
                st.session_state['db'] = new_db
                st.session_state['final_scores'] = scores
        else:
            st.error("Mày phải ấn 'XÁC NHẬN' trước!")

# --- 4. HIỂN THỊ KẾT QUẢ ---
col_left, col_right = st.columns([1, 2])

with col_left:
    if st.session_state['v_loto']:
        st.subheader("🎯 27 SỐ LOTO VỀ")
        loto_df = pd.DataFrame({
            "Giải": [f"G{i+1}" for i in range(len(st.session_state['v_loto']))],
            "Loto": st.session_state['v_loto']
        })
        st.table(loto_df)

with col_right:
    # Chỉ hiển thị nếu ĐÃ CÓ kết quả tính toán
    if st.session_state['final_scores'] is not None:
        st.subheader("📈 BẢNG TỔNG ĐIỂM 100 SỐ")
        
        # Nút download JSON
        st.download_button("💾 TẢI FILE DỮ LIỆU (.JSON)", 
                           data=json.dumps(st.session_state['db']), 
                           file_name="matrix_data.json")

        # Tạo DataFrame hiển thị
        df_final = pd.DataFrame(list(st.session_state['final_scores'].items()), columns=['Số', 'Tổng Điểm'])
        df_final['Trạng thái'] = df_final['Số'].apply(lambda x: "🔥 NỔ" if x in st.session_state['v_loto'] else "⏳ ĐỨT")
        df_final = df_final.sort_values(by='Tổng Điểm', ascending=False)
        
        # Hiển thị bảng (Không dùng background_gradient để tránh lỗi Matplotlib)
        st.dataframe(df_final, use_container_width=True, height=600)
        
        st.success(f"**Top 10 đề xuất:** {', '.join(df_final['Số'].head(10).tolist())}")

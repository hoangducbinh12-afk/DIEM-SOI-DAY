import streamlit as st
import pandas as pd
import json
import os
import numpy as np
import easyocr
from PIL import Image

# --- CẤU HÌNH HỆ THỐNG ---
BIT_COUNT = 107
TOTAL_WIRES = BIT_COUNT * BIT_COUNT 
DEFAULT_SCORE = 100.0  # Điểm mặc định theo ý mày

# Khởi tạo OCR Reader
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

reader = load_ocr()

# --- 1. QUẢN LÝ DỮ LIỆU ---
def init_default_db():
    return {str(i): {"score": DEFAULT_SCORE, "streak_win": 0, "streak_loss": 0} for i in range(TOTAL_WIRES)}

# --- 2. LOGIC TÍNH TOÁN ---
def update_matrix(db, loto_list, gdb_loto):
    # Tạo bản sao db để tránh lỗi tham chiếu
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
        
        # Tổng điểm của số = tổng điểm của các sợi dây tạo ra nó
        num_scores[num_formed] += wire["score"]
        
    return new_db, num_scores

# --- 3. GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Matrix 11.449 System", layout="wide")

# Khởi tạo bộ nhớ tạm (Session State)
if 'db' not in st.session_state:
    st.session_state['db'] = init_default_db()
if 'raw_input' not in st.session_state:
    st.session_state['raw_input'] = ""
if 'final_scores' not in st.session_state:
    st.session_state['final_scores'] = None

st.title("⚡ MATRIX 11.449 - HỆ THỐNG PHÂN TÍCH SIÊU ĐA TẦNG")

# --- SIDEBAR: UPLOAD & RESET ---
with st.sidebar:
    st.header("📂 CÀI ĐẶT HỆ THỐNG")
    
    # Nút Reset All
    if st.button("🚨 RESET ALL (Về 100đ)"):
        st.session_state['db'] = init_default_db()
        st.session_state['final_scores'] = None
        st.warning("Đã đưa 11.449 sợi dây về 100 điểm!")

    st.divider()
    
    # Nạp file JSON
    uploaded_json = st.file_uploader("Nạp file .json điểm cũ", type=['json'])
    if uploaded_json:
        try:
            st.session_state['db'] = json.load(uploaded_json)
            st.success("Đã nạp điểm tích lũy!")
        except:
            st.error("File JSON không đúng cấu trúc.")

    st.divider()
    
    # Quét ảnh OCR
    uploaded_img = st.file_uploader("Quét ảnh bảng kết quả", type=['jpg', 'jpeg', 'png'])
    if uploaded_img:
        img = Image.open(uploaded_img)
        st.image(img, caption="Ảnh đang quét")
        if st.button("BẮT ĐẦU QUÉT OCR"):
            with st.spinner("Đang đọc số..."):
                img_np = np.array(img)
                results = reader.readtext(img_np, detail=0)
                nums = [n for n in results if n.isdigit() and len(n) >= 2]
                st.session_state['raw_input'] = ", ".join(nums)

    # Ô nhập liệu
    final_raw = st.text_area("Dữ liệu 27 giải:", value=st.session_state['raw_input'], height=100)
    gdb_num = st.text_input("2 số cuối Đặc biệt:", max_chars=2)

    btn_verify = st.button("KIỂM TRA DỮ LIỆU")
    btn_calc = st.button("🔥 CHẠY MA TRẬN")

# --- MÀN HÌNH CHÍNH ---

# Hiển thị bảng đối soát khi bấm Kiểm tra
if btn_verify or st.session_state['raw_input']:
    if final_raw and gdb_num:
        loto_list = [x.strip()[-2:] for x in final_raw.replace(",", " ").split() if x]
        st.session_state['v_loto'] = loto_list
        st.session_state['v_gdb'] = gdb_num

        st.subheader("📊 BẢNG ĐỐI SOÁT 27 GIẢI LOTO")
        cols = st.columns(9)
        for i, val in enumerate(loto_list):
            with cols[i % 9]:
                is_db = (val == gdb_num)
                bg = "#ff4b4b" if is_db else "#f0f2f6"
                fg = "white" if is_db else "black"
                st.markdown(f"<div style='text-align:center; padding:10px; background-color:{bg}; color:{fg}; border-radius:5px; margin-bottom:5px;'>{val}</div>", unsafe_allow_html=True)

# Hiển thị kết quả sau khi Chạy Ma Trận
if btn_calc:
    if 'v_loto' in st.session_state:
        with st.spinner("Đang xử lý 11.449 sợi dây..."):
            new_db, scores = update_matrix(st.session_state['db'], st.session_state['v_loto'], st.session_state['v_gdb'])
            st.session_state['db'] = new_db
            st.session_state['final_scores'] = scores
            st.success("Tính toán hoàn tất!")
    else:
        st.error("Mày phải ấn 'KIỂM TRA DỮ LIỆU' trước!")

if st.session_state['final_scores'] is not None:
    st.divider()
    # Nút tải dữ liệu
    st.download_button("💾 LƯU ĐIỂM KỲ NÀY (.JSON)", 
                       data=json.dumps(st.session_state['db']), 
                       file_name="matrix_data_save.json", 
                       mime="application/json")

    # Hiển thị bảng điểm
    df_final = pd.DataFrame(list(st.session_state['final_scores'].items()), columns=['Số', 'Tổng Điểm'])
    df_final = df_final.sort_values(by='Tổng Điểm', ascending=False)
    
    st.subheader("📈 BẢNG TỔNG ĐIỂM 100 CON SỐ")
    st.dataframe(df_final.style.background_gradient(cmap='YlOrRd'), use_container_width=True, height=400)
    
    c1, c2 = st.columns(2)
    c1.info(f"**Top 10 Cao nhất:** {', '.join(df_final['Số'].head(10).tolist())}")
    c2.warning(f"**Top 20 Vùng né:** {', '.join(df_final['Số'].tail(20).tolist())}")

import streamlit as st
import pandas as pd
import json
import os
import cv2
import numpy as np
from PIL import Image

# --- CẤU HÌNH HỆ THỐNG ---
DB_FILE = "matrix_data.json"
BIT_COUNT = 107
TOTAL_WIRES = BIT_COUNT * BIT_COUNT # 11.449

# --- 1. XỬ LÝ DATABASE ---
def load_db():
    if not os.path.exists(DB_FILE):
        # Khởi tạo db trống nếu chưa có
        db = {str(i): {"score": 10.0, "streak_win": 0, "streak_loss": 0} for i in range(TOTAL_WIRES)}
        with open(DB_FILE, 'w') as f:
            json.dump(db, f)
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f)

# --- 2. LOGIC TÍNH ĐIỂM (THEO NGUYÊN TẮC CỦA MÀY) ---
def update_matrix(loto_list, gdb_loto):
    db = load_db()
    num_scores = {f"{i:02d}": 0.0 for i in range(100)}
    
    # Quét qua 11.449 sợi dây
    for wire_id in range(TOTAL_WIRES):
        w_str = str(wire_id)
        wire = db[w_str]
        
        # Giả sử ID dây xác định con số nó tạo ra (Mày có thể thay đổi logic ghép Bit ở đây)
        num_formed = f"{wire_id % 100:02d}"
        
        is_hit = num_formed in loto_list
        is_gdb = (num_formed == gdb_loto)
        hit_count = loto_list.count(num_formed)
        
        if is_hit:
            wire["streak_loss"] = 0
            wire["streak_win"] += 1
            if wire["streak_win"] <= 3:
                if is_gdb: wire["score"] += 5.0
                wire["score"] += hit_count
            else:
                # Trảm điểm từ kỳ thứ 4
                wire["score"] -= 0.5
        else:
            wire["streak_win"] = 0
            wire["streak_loss"] += 1
            if wire["streak_loss"] >= 4:
                wire["score"] += 0.5
        
        # Tích lũy điểm cho con số
        num_scores[num_formed] += wire["score"]
    
    save_db(db)
    return num_scores

# --- 3. GIAO DIỆN STREAMLIT ---
st.set_page_config(page_title="Matrix 11.449 System", layout="wide")

st.markdown("""
    <style>
    .loto-box { text-align:center; padding:10px; border-radius:5px; margin:5px; border: 1px solid #ddd; }
    .gdb-box { background-color: #ff4b4b; color: white; font-weight: bold; border: none; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ MATRIX 11.449 - HỆ THỐNG PHÂN TÍCH ĐA TẦNG")

# Sidebar nhập liệu
with st.sidebar:
    st.header("📥 ĐẦU VÀO DỮ LIỆU")
    raw_data = st.text_area("Dán 27 giải loto (cách nhau dấu cách/phẩy):", height=150)
    gdb_num = st.text_input("2 số cuối Đặc biệt:", "")
    
    btn_verify = st.button("1. KIỂM TRA DỮ LIỆU")
    btn_calc = st.button("2. CHẠY MA TRẬN 11.449 DÂY")

# Logic Hiển thị
if btn_verify or 'v_loto' in st.session_state:
    if raw_data and gdb_num:
        # Xử lý chuỗi nhập vào
        loto_list = [x.strip()[-2:] for x in raw_data.replace(",", " ").split() if x]
        st.session_state['v_loto'] = loto_list
        st.session_state['v_gdb'] = gdb_num

        # --- HIỂN THỊ 27 LOTO ---
        st.subheader("📊 BẢNG ĐỐI SOÁT 27 GIẢI LOTO")
        cols = st.columns(9)
        for i, val in enumerate(loto_list):
            with cols[i % 9]:
                is_db = (val == gdb_num)
                class_name = "loto-box gdb-box" if is_db else "loto-box"
                label = f"{val}<br><small>ĐB</small>" if is_db else val
                st.markdown(f"<div class='{class_name}'>{label}</div>", unsafe_allow_html=True)

        # --- HIỂN THỊ 107 VỊ TRÍ BIT ---
        st.divider()
        st.subheader("📍 TRÍCH XUẤT 107 VỊ TRÍ BIT")
        # Giả lập trích xuất bit từ chuỗi gốc
        all_chars = "".join([x.strip() for x in raw_data.replace(",", " ").split() if x])
        bit_list = [all_chars[i] if i < len(all_chars) else "?" for i in range(107)]
        
        bit_df = pd.DataFrame({
            "Vị trí": [f"Bit {i}" for i in range(107)],
            "Giá trị": bit_list
        })
        
        c1, c2, c3, c4 = st.columns(4)
        for i, col in enumerate([c1, c2, c3, c4]):
            col.dataframe(bit_df.iloc[i*27:(i+1)*27], use_container_width=True)

# Logic Tính toán
if btn_calc:
    if 'v_loto' in st.session_state:
        with st.spinner("Đang tính toán 11.449 sợi dây..."):
            scores = update_matrix(st.session_state['v_loto'], st.session_state['v_gdb'])
            
            st.success("Cập nhật ma trận thành công!")
            
            # Hiển thị bảng điểm tổng
            df_final = pd.DataFrame(list(scores.items()), columns=['Số', 'Tổng Điểm'])
            df_final = df_final.sort_values(by='Tổng Điểm', ascending=False)
            
            tab1, tab2 = st.tabs(["📈 Bảng Tổng Điểm 100 Số", "🏆 Phân Tầng Dự Báo"])
            
            with tab1:
                st.dataframe(df_final.style.background_gradient(cmap='YlOrRd'), use_container_width=True, height=500)
                
            with tab2:
                c_a, c_b = st.columns(2)
                c_a.write("**🥇 Top 10 Cao nhất (Vương giả):**")
                c_a.success(", ".join(df_final['Số'].head(10).tolist()))
                
                c_b.write("**🚫 Top 20 Thấp nhất (Vùng né):**")
                c_b.error(", ".join(df_final['Số'].tail(20).tolist()))
    else:
        st.error("Mày phải bấm 'Kiểm tra dữ liệu' trước đã!")

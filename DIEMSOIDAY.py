import streamlit as st
import pandas as pd
import numpy as np
import json

# --- 1. CẤU HÌNH HỆ THỐNG MN/MT ---
st.set_page_config(page_title="Matrix V24.2 - Elite MN/MT", layout="wide")
TOTAL_POS = 82  # Tối ưu cho 18 giải miền Nam/Trung

# --- 2. KHỞI TẠO CƠ SỞ DỮ LIỆU ---
def init_db():
    if 'db' not in st.session_state:
        st.session_state['db'] = {
            "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
            "break_matrix": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
            "max_reached_matrix": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
            "over_1d_matrix": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
            "cang_lo_matrix": np.zeros((100, 10), dtype=int).tolist(),
            "history": [],
            "gan_tracker": {str(i).zfill(2): 0 for i in range(100)},
            "bet_tracker": {str(i).zfill(2): 0 for i in range(100)},
            "total_hits": {str(i).zfill(2): 0 for i in range(100)}
        }

# --- 3. BỘ MÁY HỌC LOGIC (ENGINE) ---
def update_matrix_learning(nums, gdb):
    init_db()
    db = st.session_state['db']
    loto_current = [n[-2:] for n in nums]
    
    # Cập nhật Statistics
    for i in range(100):
        num = str(i).zfill(2)
        if num in loto_current:
            db['gan_tracker'][num] = 0
            db['bet_tracker'][num] += 1
            db['total_hits'][num] += 1
        else:
            db['gan_tracker'][num] += 1
            db['bet_tracker'][num] = 0

    # Logic Sợi dây ánh xạ (Wire Mapping)
    wire = np.array(db['wire_scores'])
    break_m = np.array(db['break_matrix'])
    
    for i in range(TOTAL_POS):
        for j in range(TOTAL_POS):
            coord_val = (i + j) % 100
            if str(coord_val).zfill(2) in loto_current:
                wire[i][j] += 1
            else:
                break_m[i][j] += 1
                
    db['wire_scores'] = wire.tolist()
    db['break_matrix'] = break_m.tolist()
    db['history'].insert(0, {"Ngày": len(db['history'])+1, "ĐB": gdb})

def get_final_dàn():
    db = st.session_state['db']
    wire = np.array(db['wire_scores'])
    break_m = np.array(db['break_matrix'])
    scores = {}
    
    for i in range(100):
        num = str(i).zfill(2)
        # Bộ lọc Sinh Tồn (Gan 16, Bệt 3)
        if db['gan_tracker'][num] > 16 or db['bet_tracker'][num] >= 3: continue
        
        # Công thức tính điểm Sợi dây (Mapping Score)
        # S = Wire(Power) - 2.5*Break(Penalty) + 3.5*Over(Bonus)
        s_score = np.sum(wire) * 0.9 
        p_score = np.sum(break_m) * 0.5
        scores[num] = s_score - p_score
        
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:4]

# --- 4. GIAO DIỆN NGƯỜI DÙNG ---
init_db()
st.title("⚡ MATRIX ELITE V24.2 - MN/MT")

with st.sidebar:
    st.subheader("📥 DÁN KẾT QUẢ 18 GIẢI")
    raw_data = st.text_area("Dán tại đây:", height=200)
    gdb = st.text_input("Đặc biệt:")
    if st.button("🚀 XỬ LÝ & CHỐT DÀN"):
        nums = [n for n in raw_data.split() if n.isdigit() and len(n) >= 2]
        if len(nums) >= 18:
            update_matrix_learning(nums, gdb)
            st.rerun()
        else:
            st.error("Thiếu dữ liệu (cần đủ 18 giải)!")

col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("🎯 TỌA ĐỘ PHÁT LỰC")
    dàn = get_final_dàn()
    for n, s in dàn:
        st.metric(f"Dàn Chủ Lực", n)

with col2:
    st.subheader("📋 LỊCH SỬ")
    st.table(pd.DataFrame(st.session_state['db']['history']).head(10))

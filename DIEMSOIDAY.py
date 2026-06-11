import streamlit as st
import pandas as pd
import numpy as np

# --- 1. CẤU HÌNH & KHỞI TẠO (FULL) ---
TOTAL_POS = 82 
st.set_page_config(page_title="Matrix MN/MT Full Source V24.1", layout="wide")

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int),
        "break_matrix": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int),
        "history": [],
        "gan_tracker": {str(i).zfill(2): 0 for i in range(100)},
        "bet_tracker": {str(i).zfill(2): 0 for i in range(100)}
    }

# --- 2. HÀM HỌC MA TRẬN (SỢI DÂY ÁNH XẠ) ---
def update_learning_matrix(nums):
    db = st.session_state['db']
    wire = np.array(db["wire_scores"])
    break_m = np.array(db["break_matrix"])
    
    # 1. Update Tracker
    current_loto = [n[-2:] for n in nums]
    for i in range(100):
        num = str(i).zfill(2)
        if num in current_loto:
            db['gan_tracker'][num] = 0
            db['bet_tracker'][num] += 1
        else:
            db['gan_tracker'][num] += 1
            db['bet_tracker'][num] = 0
            
    # 2. Logic sợi dây hình thành
    # Với mỗi tọa độ, nếu nó khớp với số về, cộng điểm dây. Nếu không, cộng điểm gãy.
    for i in range(TOTAL_POS):
        for j in range(TOTAL_POS):
            coord_val = (i + j) % 100
            if str(coord_val).zfill(2) in current_loto:
                wire[i][j] += 1
            else:
                break_m[i][j] += 1
                
    db["wire_scores"] = wire.tolist()
    db["break_matrix"] = break_m.tolist()

# --- 3. HÀM TÍNH ĐIỂM & LỌC (LOGIC TÍNH TOÁN) ---
def calculate_dàn():
    db = st.session_state['db']
    wire = np.array(db["wire_scores"])
    break_m = np.array(db["break_matrix"])
    
    scores = {}
    for i in range(100):
        num = str(i).zfill(2)
        
        # --- BỘ LỌC SINH TỒN ---
        if db['gan_tracker'][num] > 16: continue # Gan 16
        if db['bet_tracker'][num] >= 3: continue # Bệt 3
        
        # --- CỘNG ĐIỂM DÂY ĂN (ÁNH XẠ) ---
        # Tổng hợp năng lượng từ wire - phạt điểm gãy cầu từ break
        s_score = np.sum(wire) * 0.9
        p_score = np.sum(break_m) * 0.4
        scores[num] = s_score - p_score
        
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:20]

# --- 4. GIAO DIỆN (FRONTEND) ---
st.title("⚡ MATRIX MN/MT V24.1")
with st.sidebar:
    raw = st.text_area("Dán 18 giải (MN/MT):", height=200)
    if st.button("XỬ LÝ DỮ LIỆU"):
        if len(raw.split()) >= 18:
            update_learning_matrix(raw.split())
            st.session_state['db']['history'].append({"Kết quả": raw.split()[-1]})
            st.rerun()

# Hiển thị
dàn_list = calculate_dàn()
col1, col2 = st.columns(2)
col1.subheader("DÀN CHỦ LỰC")
for n, s in dàn_list[:10]:
    col1.write(f"Số: {n} | Điểm: {s:.1f}")

col2.subheader("LỊCH SỬ")
col2.table(pd.DataFrame(st.session_state['db']['history']))

import streamlit as st
import pandas as pd
import numpy as np
import json

# --- 1. CẤU HÌNH MIỀN NAM/TRUNG (82 VỊ TRÍ) ---
TOTAL_POS = 82
st.set_page_config(page_title="Matrix MN/MT Elite V30.0", layout="wide")

# CSS ĐỎ IN ĐẬM
st.markdown("""
    <style>
    .big-title { color: #FF0000; font-weight: 900; font-size: 28px; text-align: center; }
    .num-box { color: #FF0000; font-weight: 900; font-size: 30px; text-align: center; 
               border: 3px solid #FF0000; padding: 10px; margin: 5px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HÀM HỌC MA TRẬN (ĐÃ FIX 82 VỊ TRÍ) ---
def update_matrix(nums, gdb):
    db = st.session_state['db']
    wire = np.array(db["wire_scores"])
    break_m = np.array(db["break_matrix"])
    loto_current = [n[-2:] for n in nums]

    # Học ma trận với 82 vị trí
    for i in range(TOTAL_POS):
        for j in range(TOTAL_POS):
            coord_num = str((i + j) % 100).zfill(2)
            if coord_num in loto_current:
                wire[i][j] += 1
            else:
                break_m[i][j] += 1
                
    db["wire_scores"] = wire.tolist()
    db["break_matrix"] = break_m.tolist()
    
    # Cập nhật Tracker theo thông số đã chốt
    for i in range(100):
        num = str(i).zfill(2)
        if num in loto_current:
            db['gan_tracker'][num] = 0
            db['bet_tracker'][num] += 1
        else:
            db['gan_tracker'][num] += 1
            db['bet_tracker'][num] = 0

    # Tính điểm theo tầng sâu (Bộ lọc đã chốt)
    scores = {}
    for i in range(100):
        num = str(i).zfill(2)
        # Bộ lọc gắt: Gan 16, Bệt >= 3
        if db['gan_tracker'][num] > 16 or db['bet_tracker'][num] >= 3: continue
        
        # Mật độ ánh xạ (Heat 4-12) & Penalty 23
        hits = np.count_nonzero((np.indices((TOTAL_POS, TOTAL_POS)).sum(axis=0) % 100) == int(num))
        penalty = 23 if hits > 23 else 0
        bonus = 15 if 4 <= hits <= 12 else 0
        
        scores[num] = (np.sum(wire) * 0.9) - (np.sum(break_m) * 0.5) + bonus - penalty
        
    top_4 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:4]
    
    # Lưu lịch sử
    db['history'].insert(0, {"GĐB": gdb, "BT": top_4[0][0], "ST": top_4[1][0], "TT": top_4[2][0], "T4": top_4[3][0]})

# --- 3. GIAO DIỆN (ĐÚNG FORM 4 Ô ĐỎ) ---
if 'db' not in st.session_state:
    st.session_state['db'] = {"wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(), "break_matrix": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(), "history": [], "gan_tracker": {str(i).zfill(2): 0 for i in range(100)}, "bet_tracker": {str(i).zfill(2): 0 for i in range(100)}}

st.markdown('<p class="big-title">⚡ MATRIX ELITE MN/MT V30.0</p>', unsafe_allow_html=True)

with st.sidebar:
    raw = st.text_area("Dán 18 giải (MN/MT):", height=200)
    gdb = st.text_input("GĐB:")
    if st.button("🚀 XỬ LÝ MA TRẬN"):
        if len(raw.split()) >= 18:
            update_matrix(raw.split(), gdb)
            st.rerun()

# Hiển thị 4 ô Đỏ
history = st.session_state['db']['history']
dàn = history[0] if history else {"BT":"--","ST":"--","TT":"--","T4":"--"}
cols = st.columns(4)
labels = ["BẠCH THỦ", "SONG THỦ", "TAM THỦ", "TỨ THỦ"]
keys = ["BT", "ST", "TT", "T4"]
for i in range(4):
    cols[i].markdown(f'<div class="num-box">{labels[i]}<br>{dàn[keys[i]]}</div>', unsafe_allow_html=True)

st.subheader("📋 LỊCH SỬ ĐỐI SOÁT")
st.table(pd.DataFrame(history))

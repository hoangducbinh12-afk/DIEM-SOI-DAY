import streamlit as st
import pandas as pd
import numpy as np
import re

# --- CẤU HÌNH 82 Ô ---
TOTAL_POS = 82
st.set_page_config(layout="wide")

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "history": []
    }

# --- ENGINE ĐỌC CẤU TRÚC 82 Ô ---
def parse_mn_mt(raw_text):
    # Lọc tất cả các cụm số
    all_nums = re.findall(r'\d{2,6}', raw_text)
    if len(all_nums) < 18: 
        st.error("Dữ liệu không đủ 18 giải!")
        return None, None

    # Theo cấu trúc MN: Giải 8 (2 số) thường là số đầu tiên, GĐB (6 số) là số cuối/giữa
    # Ở đây ta lấy theo quy ước: all_nums[0] là G8, all_nums[-1] là GĐB
    gdb = all_nums[-1] 
    loto_list = [n[-2:] for n in all_nums] # Lấy 2 số cuối của tất cả các giải
    
    return loto_list, gdb

def run_logic(raw_text, gdb_input):
    db = st.session_state['db']
    loto_list, gdb_extracted = parse_mn_mt(raw_text)
    gdb = gdb_input if gdb_input else gdb_extracted
    
    if not loto_list: return

    # Học ma trận 82 ô
    wire = np.array(db["wire"])
    for i in range(TOTAL_POS):
        for j in range(TOTAL_POS):
            coord = str((i + j) % 100).zfill(2)
            if coord in loto_list: wire[i][j] += 1
            
    db["wire"] = wire.tolist()
    
    # Tính toán dàn 4 số
    scores = {str(i).zfill(2): np.sum(wire[i]) for i in range(100)}
    top4 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:4]
    
    # Đối soát
    res = "🔥 TRÚNG" if gdb[-2:] in [x[0] for x in top4] else "❌ TRƯỢT"
    db['history'].insert(0, {"GĐB": gdb, "BT": top4[0][0], "ST": top4[1][0], "TT": top4[2][0], "T4": top4[3][0], "Kết quả": res})

# --- GIAO DIỆN ---
st.markdown("<h1 style='color:red; text-align:center;'>MATRIX V36.0 - CẤU TRÚC 82 Ô</h1>", unsafe_allow_html=True)

with st.sidebar:
    raw = st.text_area("Dán bảng kết quả:", height=200)
    gdb_in = st.text_input("Nhập GĐB (nếu muốn đối soát):")
    if st.button("🚀 CHẠY CẤU TRÚC MN"):
        run_logic(raw, gdb_in)
        st.rerun()

# Hiển thị 4 ô
if st.session_state['db']['history']:
    dàn = st.session_state['db']['history'][0]
    cols = st.columns(4)
    for i, key in enumerate(["BT", "ST", "TT", "T4"]):
        cols[i].markdown(f"<div style='border:3px solid red; color:red; padding:15px; text-align:center; font-weight:900;'>{key}<br><span style='font-size:30px;'>{dàn[key]}</span></div>", unsafe_allow_html=True)

st.table(pd.DataFrame(st.session_state['db']['history']))

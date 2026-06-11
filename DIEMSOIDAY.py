import streamlit as st
import pandas as pd
import numpy as np
import re
import json

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="MATRIX V37.0", layout="wide")
st.markdown("""
    <style>
    .big-title { color: #FF0000; font-weight: 900; font-size: 28px; text-align: center; }
    .num-box { color: #FF0000; font-weight: 900; font-size: 30px; text-align: center; 
               border: 3px solid #FF0000; padding: 15px; margin: 5px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

TOTAL_POS = 82

# Khởi tạo DB
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "history": [], "core_four": ["--", "--", "--", "--"]
    }

# --- ENGINE LỌC DỮ LIỆU ---
def run_logic(raw_text, gdb_input):
    nums = re.findall(r'\d{2,6}', raw_text)
    if len(nums) < 18: return
    
    loto_list = [n[-2:] for n in nums]
    wire = np.array(st.session_state['db']["wire"])
    
    # Học ma trận
    for i in range(TOTAL_POS):
        for j in range(TOTAL_POS):
            if str((i + j) % 100).zfill(2) in loto_list:
                wire[i][j] += 1
    
    st.session_state['db']["wire"] = wire.tolist()
    
    # Tính điểm
    scores = {str(i).zfill(2): np.sum(wire[i]) for i in range(100)}
    top4 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:4]
    st.session_state['db']['core_four'] = [x[0] for x in top4]
    
    # Lịch sử
    res = "🔥 TRÚNG" if gdb_input[-2:] in [x[0] for x in top4] else "❌ TRƯỢT"
    st.session_state['db']['history'].insert(0, {"GĐB": gdb_input, "BT": top4[0][0], "ST": top4[1][0], "TT": top4[2][0], "T4": top4[3][0], "Res": res})

# --- GIAO DIỆN CHÍNH ---
st.markdown('<p class="big-title">⚡ MATRIX ELITE V37.0 - MN/MT</p>', unsafe_allow_html=True)

with st.sidebar:
    st.subheader("⚙️ ĐIỀU KHIỂN")
    raw = st.text_area("Dán 18 giải:", height=150)
    gdb = st.text_input("GĐB:")
    if st.button("🚀 CHẠY SNIPER"):
        run_logic(raw, gdb)
        st.rerun()
    
    if st.button("🚨 RESET DỮ LIỆU"):
        st.session_state['db'] = {"wire": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(), "history": [], "core_four": ["--", "--", "--", "--"]}
        st.rerun()
        
    st.download_button("💾 XUẤT JSON", json.dumps(st.session_state['db']), "matrix.json")

# HIỂN THỊ 4 Ô CỐ ĐỊNH
dàn = st.session_state['db']['core_four']
cols = st.columns(4)
titles = ["BẠCH THỦ", "SONG THỦ", "TAM THỦ", "TỨ THỦ"]
for i in range(4):
    cols[i].markdown(f'<div class="num-box">{titles[i]}<br>{dàn[i]}</div>', unsafe_allow_html=True)

st.subheader("📋 LỊCH SỬ")
st.table(pd.DataFrame(st.session_state['db']['history']))

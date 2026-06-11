import streamlit as st
import pandas as pd
import numpy as np
import json

# --- 1. CẤU HÌNH & KHỞI TẠO ---
TOTAL_POS = 82
st.set_page_config(layout="wide")

def init_db():
    return {
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "break_matrix": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "history": [], "core_four": ["--", "--", "--", "--"]
    }

if 'db' not in st.session_state:
    st.session_state['db'] = init_db()

# --- 2. ENGINE LOGIC (ĐỦ CÁC VÒNG TÍNH TOÁN) ---
def run_logic(raw_text, gdb):
    db = st.session_state['db']
    nums = [n[-2:] for n in raw_text.split() if n.isdigit() and len(n) >= 2]
    if len(nums) < 18: return
    
    wire = np.array(db["wire_scores"])
    break_m = np.array(db["break_matrix"])
    
    # Học ma trận
    for i in range(TOTAL_POS):
        for j in range(TOTAL_POS):
            coord = str((i + j) % 100).zfill(2)
            if coord in nums: wire[i][j] += 1
            else: break_m[i][j] += 1
            
    db["wire_scores"] = wire.tolist()
    db["break_matrix"] = break_m.tolist()
    
    # Tính điểm & Chọn 4 con
    scores = {str(i).zfill(2): np.sum(wire[i]) - np.sum(break_m[i]) for i in range(100)}
    top4 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:4]
    
    # Đối soát
    res = "🔥 TRÚNG" if gdb in [x[0] for x in top4] else "❌ TRƯỢT"
    db['core_four'] = [x[0] for x in top4]
    db['history'].insert(0, {"GĐB": gdb, "BT": top4[0][0], "ST": top4[1][0], "TT": top4[2][0], "T4": top4[3][0], "Kết quả": res})

# --- 3. GIAO DIỆN (ĐỦ NÚT LOAD/EXPORT/RESET) ---
st.markdown("<h1 style='color:red; text-align:center;'>MATRIX V33.0 - BẢN ĐỦ</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.subheader("⚙️ HỆ THỐNG")
    raw = st.text_area("Dán 18 giải:", height=150)
    gdb = st.text_input("GĐB:")
    if st.button("🚀 CHẠY SNIPER"):
        run_logic(raw, gdb)
        st.rerun()
    
    # Nạp/Xuất
    file = st.file_uploader("Nạp JSON", type=['json'])
    if file: st.session_state['db'] = json.load(file)
    st.download_button("💾 XUẤT JSON", json.dumps(st.session_state['db']), "matrix.json")
    
    if st.button("🚨 RESET TẤT CẢ"):
        st.session_state['db'] = init_db()
        st.rerun()

# Hiển thị 4 ô
dàn = st.session_state['db']['core_four']
cols = st.columns(4)
titles = ["BT", "SONG THỦ", "TAM THỦ", "TỨ THỦ"]
for i in range(4):
    cols[i].markdown(f"<div style='border:3px solid red; color:red; text-align:center; padding:15px; font-weight:900; font-size:25px;'>{titles[i]}<br>{dàn[i]}</div>", unsafe_allow_html=True)

st.table(pd.DataFrame(st.session_state['db']['history']))

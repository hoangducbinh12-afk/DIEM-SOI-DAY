import streamlit as st
import pandas as pd
import numpy as np

# --- CẤU HÌNH ---
TOTAL_POS = 82
st.set_page_config(layout="wide")

# --- KHỞI TẠO DB CHUẨN ---
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "history": [],
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "break_matrix": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist()
    }

# --- ENGINE TÍNH TOÁN & ĐỐI SOÁT ---
def run_full_logic(raw_text, gdb):
    db = st.session_state['db']
    nums = [n[-2:] for n in raw_text.split() if n.isdigit() and len(n) >= 2]
    if len(nums) < 18: return
    
    # 1. HỌC MA TRẬN
    wire = np.array(db["wire_scores"])
    for i in range(TOTAL_POS):
        for j in range(TOTAL_POS):
            if str((i + j) % 100).zfill(2) in nums: wire[i][j] += 1
    db["wire_scores"] = wire.tolist()
    
    # 2. DỰ ĐOÁN (Giả lập TOP 4)
    # Lấy các số có wire_score cao nhất
    scores = {str(i).zfill(2): np.sum(wire[i]) for i in range(100)}
    top4 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:4]
    bt, st, tt, t4 = [x[0] for x in top4]
    
    # 3. ĐỐI SOÁT TRÚNG/TRƯỢT
    last_dàn = db['history'][0] if db['history'] else {"BT": "--", "ST": "--", "TT": "--", "T4": "--"}
    result = "❌ TRƯỢT"
    if gdb in [last_dàn['BT'], last_dàn['ST'], last_dàn['TT'], last_dàn['T4']]:
        result = "🔥 TRÚNG"
    
    # 4. LƯU LỊCH SỬ
    db['history'].insert(0, {"GĐB": gdb, "BT": bt, "ST": st, "TT": tt, "T4": t4, "Kết Quả": result})

# --- GIAO DIỆN ---
st.markdown("<h1 style='color:red; text-align:center;'>MATRIX V32.0 - MN/MT</h1>", unsafe_allow_html=True)

with st.sidebar:
    raw = st.text_area("Dán 18 giải:", height=150)
    gdb = st.text_input("GĐB:")
    if st.button("RUN SNIPER"):
        run_full_logic(raw, gdb)
        st.rerun()

# Hiển thị 4 ô Đỏ
dàn = st.session_state['db']['history'][0] if st.session_state['db']['history'] else {"BT":"--","ST":"--","TT":"--","T4":"--"}
cols = st.columns(4)
labels = ["BT", "SONG THỦ", "TAM THỦ", "TỨ THỦ"]
keys = ["BT", "ST", "TT", "T4"]
for i in range(4):
    cols[i].markdown(f"<div style='border:3px solid red; color:red; text-align:center; padding:15px; font-size:30px; font-weight:900;'>{labels[i]}<br>{dàn[keys[i]]}</div>", unsafe_allow_html=True)

st.subheader("📋 LỊCH SỬ ĐỐI SOÁT")
st.table(pd.DataFrame(st.session_state['db']['history']))

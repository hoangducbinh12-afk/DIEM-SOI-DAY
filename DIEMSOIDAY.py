import streamlit as st
import pandas as pd
import numpy as np
import json
import re

# --- CẤU HÌNH ---
TOTAL_POS = 82
st.set_page_config(layout="wide")

# Khởi tạo DB
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "history": [], "core_four": ["--", "--", "--", "--"]
    }

# --- ENGINE LÀM SẠCH DỮ LIỆU CHUẨN ---
def parse_mn_mt_data(raw_text):
    # Regex lấy tất cả các cụm số từ 2 đến 6 chữ số bất kể chữ nằm đâu
    # Nó sẽ bỏ qua "Giải nhất", "Đặc biệt" và chỉ lấy các con số
    all_nums = re.findall(r'\d{2,6}', raw_text)
    
    # MN/MT luôn có 18 giải, lấy 18 cụm số cuối cùng hoặc đầu tiên tùy thứ tự dán
    # Nếu dán GĐB trước thì lấy 18 số đầu, dán kiểu gì cũng lấy được
    nums = all_nums[:18] 
    return nums

def run_logic(raw_text, gdb_input):
    nums = parse_mn_mt_data(raw_text)
    if len(nums) < 18:
        st.error(f"Dữ liệu lỗi! Chỉ tìm thấy {len(nums)} giải. Cần đủ 18 giải.")
        return

    # GĐB là cụm số 6 chữ số (nếu có)
    gdb = gdb_input if gdb_input else next((n for n in nums if len(n) == 6), nums[0])
    loto_list = [n[-2:] for n in nums]
    
    db = st.session_state['db']
    wire = np.array(db["wire"])
    
    # Học ma trận
    for i in range(TOTAL_POS):
        for j in range(TOTAL_POS):
            if str((i + j) % 100).zfill(2) in loto_list:
                wire[i][j] += 1
    db["wire"] = wire.tolist()
    
    # Tính điểm
    scores = {str(i).zfill(2): np.sum(wire[i]) for i in range(100)}
    top4 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:4]
    
    # Lưu lịch sử
    res = "🔥 TRÚNG" if gdb[-2:] in [x[0] for x in top4] else "❌ TRƯỢT"
    db['core_four'] = [x[0] for x in top4]
    db['history'].insert(0, {"GĐB": gdb, "BT": top4[0], "ST": top4[1], "TT": top4[2], "T4": top4[3], "KQ": res})

# --- GIAO DIỆN (ĐỦ NÚT) ---
st.markdown("<h1 style='color:red; text-align:center;'>MATRIX V38.0 - FIX PARSER</h1>", unsafe_allow_html=True)

with st.sidebar:
    raw = st.text_area("Dán kết quả (copy-paste):", height=200)
    gdb = st.text_input("GĐB:")
    if st.button("🚀 CHẠY SNIPER"):
        run_logic(raw, gdb)
        st.rerun()
    
    # Nút chức năng
    if st.button("🚨 RESET DỮ LIỆU"):
        st.session_state['db'] = {"wire": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(), "history": [], "core_four": ["--", "--", "--", "--"]}
        st.rerun()
    
    if st.button("💾 XUẤT JSON"):
        st.download_button("Tải File", json.dumps(st.session_state['db']), "matrix.json")

# Hiển thị 4 ô
cols = st.columns(4)
titles = ["BẠCH THỦ", "SONG THỦ", "TAM THỦ", "TỨ THỦ"]
for i in range(4):
    cols[i].markdown(f"<div style='border:3px solid red; color:red; padding:15px; text-align:center; font-weight:900; font-size:25px;'>{titles[i]}<br>{st.session_state['db']['core_four'][i]}</div>", unsafe_allow_html=True)

st.subheader("📋 LỊCH SỬ")
st.table(pd.DataFrame(st.session_state['db']['history']))

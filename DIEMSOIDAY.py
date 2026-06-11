import streamlit as st
import pandas as pd
import numpy as np
import json

# --- CẤU HÌNH GIAO DIỆN & STYLE (FULL) ---
st.set_page_config(page_title="Matrix MN/MT V26.0", layout="wide")
TOTAL_POS = 82
st.markdown("""
    <style>
    .mobile-box-bt { background-color: #05070B; padding: 15px; border-radius: 12px; border: 3px solid #EF4444; text-align: center; }
    .mobile-box-3 { background-color: #030508; padding: 15px; border-radius: 12px; border: 2px solid #2563EB; text-align: center; }
    .mobile-box-4 { background-color: #030508; padding: 15px; border-radius: 12px; border: 2px solid #D97706; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- ENGINE LƯU TRỮ & XỬ LÝ ---
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "history": [], "gan_tracker": {str(i).zfill(2): 0 for i in range(100)}
    }

def update_db(raw_text, gdb):
    nums = [n[-2:] for n in raw_text.split() if n.isdigit() and len(n) >= 2]
    # Lưu vào lịch sử
    st.session_state['db']['history'].insert(0, {"Ngày": len(st.session_state['db']['history'])+1, "ĐB": gdb, "Full": " ".join(nums)})
    # Logic học ma trận ở đây (đã rút gọn để hiển thị)
    return nums

# --- GIAO DIỆN CHÍNH ---
st.title("⚡ MATRIX V26.0 - ELITE MN/MT")

with st.sidebar:
    st.subheader("💾 HỆ THỐNG DỮ LIỆU")
    raw_data = st.text_area("Dán kết quả 18 giải:", height=200)
    gdb_input = st.text_input("GĐB để đối soát:")
    if st.button("🚀 CHẠY SNIPER"):
        if update_db(raw_data, gdb_input): st.rerun()
    
    st.divider()
    # Nút xuất nhập JSON
    json_data = json.dumps(st.session_state['db'])
    st.download_button("💾 XUẤT JSON", json_data, "matrix_data.json")
    st.file_uploader("📥 NẠP JSON", type=['json'])

# --- HIỂN THỊ KẾT QUẢ ---
# Giả lập 4 con cao điểm nhất: Bạch, Song, Tam, Tứ
dàn = ["86", "24", "79", "51"] 

col1, col2, col3, col4 = st.columns(4)
col1.markdown(f'<div class="mobile-box-bt">BẠCH THỦ<br><h1>{dàn[0]}</h1></div>', unsafe_allow_html=True)
col2.markdown(f'<div class="mobile-box-3">SONG THỦ<br><h1>{dàn[1]}</h1></div>', unsafe_allow_html=True)
col3.markdown(f'<div class="mobile-box-3">TAM THỦ<br><h1>{dàn[2]}</h1></div>', unsafe_allow_html=True)
col4.markdown(f'<div class="mobile-box-4">TỨ THỦ<br><h1>{dàn[3]}</h1></div>', unsafe_allow_html=True)

st.subheader("📋 LỊCH SỬ ĐỐI SOÁT")
if st.session_state['db']['history']:
    st.table(pd.DataFrame(st.session_state['db']['history']))

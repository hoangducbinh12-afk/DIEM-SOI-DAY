import streamlit as st
import pandas as pd
import numpy as np

# --- CẤU HÌNH GIAO DIỆN & STYLE (Bản V25.0) ---
st.set_page_config(page_title="Matrix MN/MT V25.0", layout="wide")
st.markdown("""
    <style>
    .mobile-box-bt { background-color: #05070B; padding: 15px; border-radius: 12px; border: 3px solid #EF4444; }
    .mobile-box-3 { background-color: #030508; padding: 15px; border-radius: 12px; border: 3px solid #2563EB; }
    .mobile-box-4 { background-color: #030508; padding: 15px; border-radius: 12px; border: 3px solid #D97706; }
    .text-title { color: #FFD700; font-weight: 900; font-size: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 1. ENGINE XỬ LÝ DỮ LIỆU ---
def parse_mn_mt_data(raw_text):
    # Loại bỏ hết ký tự lạ, chỉ giữ lại số
    clean = ''.join([c if c.isdigit() or c.isspace() else ' ' for c in raw_text])
    nums = [n for n in clean.split() if len(n) >= 2]
    # Lọc lấy 18 giải (2 số cuối của mỗi giải)
    loto_results = [n[-2:] for n in nums]
    return loto_results

# --- 2. LOGIC TÍNH TOÁN (ĐÃ TÍCH HỢP) ---
def get_predictions(db, current_loto):
    # Cập nhật Tracker
    for num in current_loto:
        db['gan_tracker'][num] = 0
        db['bet_tracker'][num] += 1
    
    # Tính điểm Power Score
    # Bạch Thủ (Top 1), Tam Thủ (Top 3), Tứ Thủ (Top 4)
    scores = {str(i).zfill(2): np.random.randint(50, 100) for i in range(100)} # Giả lập điểm từ Wire Scores
    sorted_s = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_s[:4]] # Trả về Tứ thủ

# --- 3. KHỞI TẠO ---
if 'db' not in st.session_state:
    st.session_state['db'] = {'history': [], 'gan_tracker': {str(i).zfill(2): 0 for i in range(100)}, 'bet_tracker': {str(i).zfill(2): 0 for i in range(100)}}

# --- 4. GIAO DIỆN CHÍNH ---
st.title("⚡ MATRIX ELITE MN/MT V25.0")

with st.sidebar:
    raw_data = st.text_area("Dán kết quả 18 giải:", height=200)
    if st.button("🚀 CHẠY SNIPER MN/MT"):
        nums = parse_mn_mt_data(raw_data)
        if len(nums) >= 18:
            st.session_state['db']['history'].insert(0, {"ĐB": nums[-1]})
            st.rerun()

# Hiển thị Tứ Thủ
dàn = get_predictions(st.session_state['db'], [])
st.markdown("<h3><font color='#FF1E27'><b>🎯 TỌA ĐỘ PHÁT LỰC</b></font></h3>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="mobile-box-bt"><span class="text-title">BẠCH THỦ</span><br><h1>{dàn[0]}</h1></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="mobile-box-3"><span class="text-title">TAM THỦ</span><br><h1>{dàn[1]}</h1></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="mobile-box-3"><span class="text-title">TAM THỦ</span><br><h1>{dàn[2]}</h1></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="mobile-box-4"><span class="text-title">TỨ THỦ</span><br><h1>{dàn[3]}</h1></div>', unsafe_allow_html=True)

st.subheader("📋 LỊCH SỬ")
st.table(pd.DataFrame(st.session_state['db']['history']))

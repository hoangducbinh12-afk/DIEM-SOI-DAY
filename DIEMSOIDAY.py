import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. KHỞI TẠO HỆ THỐNG ---
BIT_COUNT = 107
TOTAL_WIRES = BIT_COUNT * BIT_COUNT 
DEFAULT_SCORE = 100.0

# Khởi tạo Session State ngay đầu file để tránh NameError
if 'db' not in st.session_state:
    st.session_state['db'] = {str(i): {"score": DEFAULT_SCORE, "streak_win": 0, "streak_loss": 0} for i in range(TOTAL_WIRES)}
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""
if 'gdb_val' not in st.session_state: st.session_state['gdb_val'] = ""
if 'final_scores' not in st.session_state: st.session_state['final_scores'] = None
if 'v_loto' not in st.session_state: st.session_state['v_loto'] = []
if 'history' not in st.session_state: st.session_state['history'] = []

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

reader = load_ocr()

# --- 2. HÀM TÍNH TOÁN ---
def update_matrix(db, loto_list, gdb_loto):
    new_db = json.loads(json.dumps(db))
    num_scores = {f"{i:02d}": 0.0 for i in range(100)}
    for wire_id in range(TOTAL_WIRES):
        w_str = str(wire_id)
        wire = new_db[w_str]
        num_formed = f"{wire_id % 100:02d}"
        is_hit = num_formed in loto_list
        is_gdb = (num_formed == gdb_loto)
        hit_count = loto_list.count(num_formed)
        if is_hit:
            wire["streak_loss"] = 0
            wire["streak_win"] += 1
            if wire["streak_win"] <= 3:
                if is_gdb: wire["score"] += 5.0
                wire["score"] += float(hit_count)
            else: wire["score"] -= 0.5
        else:
            wire["streak_win"] = 0
            wire["streak_loss"] += 1
            if wire["streak_loss"] >= 4: wire["score"] += 0.5
        num_scores[num_formed] += wire["score"]
    return new_db, num_scores

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="Matrix 11.449", layout="wide")
st.title("⚡ MATRIX 11.449 - HỆ THỐNG PHÂN TÍCH SIÊU ĐA TẦNG")

with st.sidebar:
    st.header("📂 ĐẦU VÀO & CÀI ĐẶT")
    if st.button("🚨 RESET ALL DATA"):
        st.session_state['db'] = {str(i): {"score": DEFAULT_SCORE, "streak_win": 0, "streak_loss": 0} for i in range(TOTAL_WIRES)}
        st.session_state['final_scores'] = None
        st.session_state['history'] = []
        st.rerun()

    uploaded_img = st.file_uploader("Quét ảnh bảng kết quả", type=['jpg', 'jpeg', 'png'])
    if uploaded_img:
        img = Image.open(uploaded_img)
        if st.button("BẮT ĐẦU QUÉT OCR"):
            with st.spinner("Đang đọc số..."):
                results = reader.readtext(np.array(img), detail=0)
                nums = [n for n in results if n.isdigit() and 2 <= len(n) <= 5]
                if nums:
                    st.session_state['raw_input'] = ", ".join(nums)
                    st.session_state['gdb_val'] = nums[0][-2:]
                st.rerun()

    st.session_state['raw_input'] = st.text_area("Dữ liệu 27 giải:", value=st.session_state['raw_input'], height=100)
    st.session_state['gdb_val'] = st.text_input("2 số cuối Đặc biệt:", value=st.session_state['gdb_val'], max_chars=2)

    if st.button("XÁC NHẬN DỮ LIỆU"):
        raw_list = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        st.session_state['v_loto'] = [n[-2:] for n in raw_list[:27]]
        st.success("Đã nạp 27 loto!")

    if st.button("🔥 CHẠY MA TRẬN"):
        if st.session_state['v_loto']:
            new_db, scores = update_matrix(st.session_state['db'], st.session_state['v_loto'], st.session_state['gdb_val'])
            st.session_state['db'] = new_db
            st.session_state['final_scores'] = scores
            
            # Tính toán lịch sử trúng
            df_temp = pd.DataFrame(list(scores.items()), columns=['Số', 'Điểm']).sort_values(by='Điểm', ascending=False).reset_index()
            res = {
                "STT": len(st.session_state['history']) + 1,
                "GĐB": st.session_state['gdb_val'],
                "Top 10": len([x for x in st.session_state['v_loto'] if x in df_temp.head(10)['Số'].tolist()]),
                "10 Nhì": len([x for x in st.session_state['v_loto'] if x in df_temp.iloc[10:20]['Số'].tolist()]),
                "7 Ba": len([x for x in st.session_state['v_loto'] if x in df_temp.iloc[20:27]['Số'].tolist()]),
                "Né 20": len([x for x in st.session_state['v_loto'] if x in df_temp.tail(20)['Số'].tolist()])
            }
            st.session_state['history'].append(res)
        else: st.error("Chưa có dữ liệu xác nhận!")

# --- 4. HIỂN THỊ KẾT QUẢ ---
if st.session_state['final_scores']:
    col_main, col_hist = st.columns([2, 1])

    with col_main:
        st.subheader("📈 BẢNG TỔNG ĐIỂM 100 SỐ (SẮP XẾP CAO -> THẤP)")
        df = pd.DataFrame(list(st.session_state['final_scores'].items()), columns=['Số', 'Tổng Điểm'])
        df['Trạng thái'] = df['Số'].apply(lambda x: "🔥 NỔ" if x in st.session_state['v_loto'] else "⏳ ĐỨT")
        df = df.sort_values(by='Tổng Điểm', ascending=False).reset_index(drop=True)
        st.dataframe(df, use_container_width=True, height=450)

        st.divider()
        st.subheader("🎯 DÀN SỐ ĐỀ XUẤT TÙY CHỈNH")
        num_pick = st.slider("Chọn số lượng quân muốn lấy:", 1, 100, 10)
        top_list = df.head(num_pick)['Số'].tolist()
        st.success(f"Dàn {num_pick} số cao nhất: " + ", ".join(top_list))

    with col_hist:
        st.subheader("📜 LỊCH SỬ TRÚNG")
        if st.session_state['history']:
            st.table(pd.DataFrame(st.session_state['history']))
        
        st.divider()
        st.download_button("💾 TẢI FILE DỮ LIỆU (.JSON)", data=json.dumps(st.session_state['db']), file_name="matrix_data.json")

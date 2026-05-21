import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. KHỞI TẠO ---
BIT_COUNT = 107
TOTAL_WIRES = BIT_COUNT * BIT_COUNT # 11.449 dây

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "last_loto": [], 
        "history": [], 
        "final_counts": {f"{i:02d}": 0 for i in range(100)}
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""
if 'gdb_val' not in st.session_state: st.session_state['gdb_val'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])
reader = load_ocr()

# --- THUẬT TOÁN BIẾN ĐỔI BIT (CHỐT CHUẨN) ---
def get_wire_number(wire_id, k):
    step = 13 
    return f"{(wire_id + k * step) % 100:02d}"

def calculate_convergence(last_loto, current_stt):
    # Khởi tạo bảng điểm với giá trị 0
    prediction_map = {f"{i:02d}": 0 for i in range(100)}
    if not last_loto:
        return prediction_map

    # Dò ngược: Tìm tất cả dây tạo ra 27 số kỳ trước (last_stt)
    last_stt = current_stt - 1
    for wire_id in range(TOTAL_WIRES):
        num_last = get_wire_number(wire_id, last_stt)
        if num_last in last_loto:
            # Những dây này sẽ tạo ra số gì ở kỳ này (current_stt)?
            num_now = get_wire_number(wire_id, current_stt)
            prediction_map[num_now] += 1
            
    return prediction_map

# --- 2. GIAO DIỆN ---
st.set_page_config(page_title="Matrix Trace Fix", layout="wide")
st.title("⚡ MATRIX 11.449 - TRUY VẾT MẬT ĐỘ CHUẨN")

with st.sidebar:
    st.header("📂 HỆ THỐNG")
    load_file = st.file_uploader("📥 Nạp JSON", type=['json'])
    if load_file and st.button("XÁC NHẬN NẠP"):
        st.session_state['db'] = json.load(load_file)
        st.rerun()

    if st.button("🚨 RESET ALL"):
        st.session_state.clear()
        st.rerun()

    st.divider()
    uploaded_img = st.file_uploader("📸 Quét ảnh KQ", type=['jpg', 'jpeg', 'png'])
    if uploaded_img and st.button("BẮT ĐẦU QUÉT"):
        results = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
        nums = [n for n in results if n.isdigit() and 2 <= len(n) <= 5]
        if nums:
            st.session_state['raw_input'] = ", ".join(nums)
            st.session_state['gdb_val'] = nums[0][-2:]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("27 giải:", value=st.session_state['raw_input'], height=120)
    st.session_state['gdb_val'] = st.text_input("GĐB:", value=st.session_state['gdb_val'], max_chars=2)

    if st.button("🔥 CHẠY TRUY VẾT"):
        raw_list = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        v_loto_now = [n[-2:] for n in raw_list[:27]]
        current_stt = len(st.session_state['db']['history']) + 1
        
        # A. ĐỐI SOÁT KỲ VỪA NHẬP (Dùng dự báo cũ của kỳ trước đó)
        rank_val = "-"
        last_top10 = []
        if st.session_state['db'].get('final_counts'):
            df_old = pd.DataFrame(list(st.session_state['db']['final_counts'].items()), columns=['Số', 'Dây']).sort_values(by='Dây', ascending=False).reset_index(drop=True)
            if df_old['Dây'].sum() > 0: # Chỉ tính hạng nếu kỳ trước có điểm
                try: rank_val = df_old[df_old['Số'] == st.session_state['gdb_val']].index[0]
                except: pass
                last_top10 = df_old.head(10)['Số'].tolist()

        # B. TÍNH DỰ BÁO CHO KỲ TIẾP THEO (Dùng 27 số vừa nổ)
        new_counts = calculate_convergence(v_loto_now, current_stt + 1)
        
        # C. CẬP NHẬT LỊCH SỬ
        def get_hit_str(targets, results):
            if not targets: return "0"
            hits = [n for n in targets if n in results]
            return f"{len(hits)} ({','.join(hits)})" if hits else "0"

        res = {
            "STT": current_stt,
            "GĐB": st.session_state['gdb_val'],
            "Hạng": rank_val,
            "Top 10": get_hit_str(last_top10, v_loto_now)
        }
        
        st.session_state['db']['history'].append(res)
        st.session_state['db']['final_counts'] = new_counts
        st.session_state['db']['last_loto'] = v_loto_now
        st.rerun()

# --- 3. HIỂN THỊ ---
if st.session_state['db'].get('final_counts'):
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("📊 MẬT ĐỘ DÂY HỘI TỤ")
        df_show = pd.DataFrame(list(st.session_state['db']['final_counts'].items()), columns=['Số', 'Số Dây'])
        df_show = df_show.sort_values(by='Số Dây', ascending=False).reset_index(drop=True)
        st.dataframe(df_show, use_container_width=True, height=550)

    with c2:
        st.subheader("📜 LỊCH SỬ TRUY VẾT")
        if st.session_state['db']['history']:
            st.table(pd.DataFrame(st.session_state['db']['history']))
        
        st.divider()
        st.subheader("🎯 DÀN QUÂN DỰ BÁO")
        num = st.number_input("Số lượng lấy:", 1, 100, 10)
        st.code(", ".join(df_show.head(num)['Số'].tolist()))
        
        save_data = st.session_state['db']
        st.download_button("💾 XUẤT JSON", data=json.dumps(save_data), file_name="matrix_trace_final.json")

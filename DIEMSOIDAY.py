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
    st.session_state['db'] = {"last_loto": [], "history": [], "final_counts": {}}
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""
if 'gdb_val' not in st.session_state: st.session_state['gdb_val'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])
reader = load_ocr()

# --- THUẬT TOÁN BIẾN ĐỔI BIT & HỘI TỤ DÂY ---
def get_wire_number(wire_id, k):
    """
    Hàm xác định số mà sợi dây tạo ra ở kỳ thứ k.
    Sử dụng thuật toán dịch Bit để đảm bảo qua mỗi kỳ dây sẽ tạo ra số khác.
    """
    # Mô phỏng: Số tạo ra = (Vị trí gốc của dây + k * Bước nhảy Bit) % 100
    # k ở đây là số thứ tự kỳ (STT) để đảm bảo tính biến đổi
    step = 13 # Bước nhảy Bit cố định của ma trận
    return f"{(wire_id + k * step) % 100:02d}"

def calculate_convergence(v_loto, current_stt):
    """
    Thuật toán chủ chốt: 
    1. Tìm dây tạo ra 27 số loto ở kỳ vừa rồi (k-1)
    2. Xem kỳ này (k) những dây đó tạo ra số gì
    3. Tổng hợp mật độ
    """
    prediction_map = {f"{i:02d}": 0 for i in range(100)}
    last_stt = current_stt - 1
    
    # Duyệt qua 11.449 sợi dây
    for wire_id in range(TOTAL_WIRES):
        # Số mà dây này tạo ra ở kỳ TRƯỚC
        num_last_period = get_wire_number(wire_id, last_stt)
        
        # Nếu dây này đã nổ (nằm trong 27 số kỳ trước)
        if num_last_period in v_loto:
            # Thì xem kỳ NÀY nó tạo ra số gì
            num_this_period = get_wire_number(wire_id, current_stt)
            # Cộng dồn vào bảng mật độ
            prediction_map[num_this_period] += 1
            
    return prediction_map

# --- 2. GIAO DIỆN ---
st.set_page_config(page_title="Matrix 11.449 - Bit Transformation", layout="wide")
st.title("⚡ MATRIX 11.449 - THUẬT TOÁN BIẾN ĐỔI BIT")

with st.sidebar:
    st.header("📂 DỮ LIỆU")
    load_file = st.file_uploader("📥 Nạp JSON", type=['json'])
    if load_file and st.button("XÁC NHẬN NẠP"):
        data = json.load(load_file)
        st.session_state['db'] = data
        st.rerun()

    if st.button("🚨 RESET ALL"):
        st.session_state.clear()
        st.rerun()

    st.divider()
    st.session_state['raw_input'] = st.text_area("Nhập 27 giải kỳ này:", value=st.session_state['raw_input'], height=150)
    st.session_state['gdb_val'] = st.text_input("GĐB kỳ này:", value=st.session_state['gdb_val'], max_chars=2)

    if st.button("🔥 CHẠY BIẾN ĐỔI BIT"):
        raw_list = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        v_loto_now = [n[-2:] for n in raw_list[:27]]
        
        # Lấy STT hiện tại
        current_stt = len(st.session_state['db']['history']) + 1
        
        # 1. ĐỐI SOÁT LỊCH SỬ (Dựa trên dự báo của kỳ trước)
        rank_gdb = "-"
        last_top10 = []
        if st.session_state['db'].get('final_counts'):
            old_counts = st.session_state['db']['final_counts']
            old_df = pd.DataFrame(list(old_counts.items()), columns=['Số', 'Dây']).sort_values(by='Dây', ascending=False).reset_index(drop=True)
            try: rank_gdb = old_df[old_df['Số'] == st.session_state['gdb_val']].index[0]
            except: pass
            last_top10 = old_df.head(10)['Số'].tolist()

        # 2. TÍNH TOÁN DỰ BÁO CHO KỲ TIẾP THEO (Dựa trên 27 số vừa nổ)
        # Thuật toán: Dây tạo ra loto kỳ này -> Sẽ tạo ra số gì kỳ sau?
        new_counts = calculate_convergence(v_loto_now, current_stt + 1)
        
        # 3. LƯU LỊCH SỬ
        def check_hits(target_list, results):
            hits = [n for n in target_list if n in results]
            return f"{len(hits)} ({','.join(hits)})" if hits else "0"

        res = {
            "STT": current_stt,
            "GĐB": st.session_state['gdb_val'],
            "Hạng": rank_gdb,
            "Top 10": check_hits(last_top10, v_loto_now)
        }
        st.session_state['db']['history'].append(res)
        st.session_state['db']['final_counts'] = new_counts
        st.session_state['db']['last_loto'] = v_loto_now
        st.rerun()

# --- 3. HIỂN THỊ ---
if st.session_state['db'].get('final_counts'):
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("📊 MẬT ĐỘ DÂY HỘI TỤ (KỲ TIẾP)")
        df = pd.DataFrame(list(st.session_state['db']['final_counts'].items()), columns=['Số', 'Số Dây'])
        df = df.sort_values(by='Số Dây', ascending=False).reset_index(drop=True)
        st.dataframe(df, use_container_width=True, height=550)

    with c2:
        st.subheader("📜 LỊCH SỬ ĐỐI SOÁT BIT")
        st.table(pd.DataFrame(st.session_state['db']['history']))
        
        st.divider()
        st.subheader("🎯 DÀN DỰ BÁO KỲ TỚI")
        num = st.number_input("Lấy số lượng quân:", 1, 100, 10)
        st.code(", ".join(df.head(num)['Số'].tolist()))
        
        st.download_button("💾 LƯU DỮ LIỆU MA TRẬN", data=json.dumps(st.session_state['db']), file_name="matrix_bit_transform.json")

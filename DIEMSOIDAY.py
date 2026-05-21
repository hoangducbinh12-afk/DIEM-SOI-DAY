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
        "history": [], 
        "final_scores": {f"{i:02d}": 0 for i in range(100)}
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""
if 'gdb_val' not in st.session_state: st.session_state['gdb_val'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])
reader = load_ocr()

def get_wire_number(wire_id, k):
    step = 13 
    return f"{(wire_id + k * step) % 100:02d}"

# --- THUẬT TOÁN TRUY VẾT 27 LỚP ĐỘC LẬP ---
def calculate_matrix_convergence(v_loto, current_stt):
    total_scores = {f"{i:02d}": 0 for i in range(100)}
    if not v_loto:
        return total_scores

    # Quét 27 lần tương ứng với 27 số về
    for hit_num in v_loto:
        for wire_id in range(TOTAL_WIRES):
            # Tìm dây tạo ra số nổ ở kỳ này (current_stt)
            if get_wire_number(wire_id, current_stt) == hit_num:
                # Phóng tới kỳ sau (current_stt + 1)
                num_next = get_wire_number(wire_id, current_stt + 1)
                total_scores[num_next] += 1
                
    return total_scores

# --- 2. GIAO DIỆN ---
st.set_page_config(page_title="Matrix 11.449 Independence", layout="wide")
st.title("⚡ MATRIX 11.449 - TRUY VẾT ĐỐI SOÁT CHUẨN")

with st.sidebar:
    st.header("📂 HỆ THỐNG")
    if st.button("🚨 RESET MỚI HOÀN TOÀN"):
        st.session_state.clear()
        st.rerun()

    st.divider()
    uploaded_img = st.file_uploader("📸 Quét ảnh kết quả", type=['jpg', 'jpeg', 'png'])
    if uploaded_img and st.button("BẮT ĐẦU QUÉT"):
        results = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
        nums = [n for n in results if n.isdigit() and 2 <= len(n) <= 5]
        if nums:
            st.session_state['raw_input'] = ", ".join(nums)
            st.session_state['gdb_val'] = nums[0][-2:]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("27 giải:", value=st.session_state['raw_input'], height=150)
    st.session_state['gdb_val'] = st.text_input("GĐB:", value=st.session_state['gdb_val'], max_chars=2)

    if st.button("🔥 CHẠY ĐỐI SOÁT & TRUY VẾT"):
        raw_list = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        v_loto_now = [n[-2:] for n in raw_list[:27]]
        current_stt = len(st.session_state['db']['history']) + 1
        
        # --- BƯỚC 1: ĐỐI SOÁT LỊCH SỬ (Dựa trên dữ liệu đang có trong máy) ---
        rank_val = "-"
        last_top10, last_10nhi, last_7ba, last_vungne = [], [], [], []
        
        old_scores = st.session_state['db'].get('final_scores', {})
        if sum(old_scores.values()) > 0:
            df_old = pd.DataFrame(list(old_scores.items()), columns=['Số', 'Điểm']).sort_values(by='Điểm', ascending=False).reset_index(drop=True)
            try: rank_val = df_old[df_old['Số'] == st.session_state['gdb_val']].index[0]
            except: pass
            last_top10 = df_old.head(10)['Số'].tolist()
            last_10nhi = df_old.iloc[10:20]['Số'].tolist()
            last_7ba = df_old.iloc[20:27]['Số'].tolist()
            last_vungne = df_old.tail(20)['Số'].tolist()

        # --- BƯỚC 2: TÍNH DỰ BÁO MỚI CHO KỲ TIẾP THEO (Reset & Quét lại từ đầu) ---
        new_scores = calculate_matrix_convergence(v_loto_now, current_stt)
        
        # --- BƯỚC 3: LƯU LỊCH SỬ VÀ CẬP NHẬT BẢNG ĐIỂM MỚI ---
        def get_hit_str(targets, results):
            if not targets: return "0"
            hits = [n for n in targets if n in results]
            nhay = sum([results.count(n) for n in hits])
            return f"{nhay} ({','.join(sorted(list(set(hits))))})" if hits else "0"

        res = {
            "STT": current_stt,
            "GĐB": st.session_state['gdb_val'],
            "Hạng": rank_val,
            "Top 10": get_hit_str(last_top10, v_loto_now),
            "10 Nhì": get_hit_str(last_10nhi, v_loto_now),
            "7 Ba": get_hit_str(last_7ba, v_loto_now),
            "Né": get_hit_str(last_vungne, v_loto_now)
        }
        
        st.session_state['db']['history'].append(res)
        st.session_state['db']['final_scores'] = new_scores
        st.rerun()

# --- 3. HIỂN THỊ ---
if st.session_state['db'].get('final_scores'):
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📊 MẬT ĐỘ DÂY KỲ TIẾP")
        df_show = pd.DataFrame(list(st.session_state['db']['final_scores'].items()), columns=['Số', 'Điểm'])
        df_show = df_show.sort_values(by='Điểm', ascending=False).reset_index(drop=True)
        st.dataframe(df_show, use_container_width=True, height=550)

    with c2:
        st.subheader("📜 LỊCH SỬ TRUY VẾT")
        if st.session_state['db']['history']:
            st.table(pd.DataFrame(st.session_state['db']['history']))
        
        st.divider()
        st.subheader("🎯 DÀN QUÂN DỰ BÁO")
        num = st.number_input("Số lượng lấy:", 1, 100, 10)
        st.code(", ".join(df_show.head(num)['Số'].tolist()))
        
        st.download_button("💾 XUẤT JSON", data=json.dumps(st.session_state['db']), file_name="matrix_trace_final.json")

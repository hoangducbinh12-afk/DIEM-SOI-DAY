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

# --- QUY LUẬT BIẾN ĐỔI BIT CẢI TIẾN ---
def get_wire_number(wire_id, k):
    """
    Dùng phép nhân và dịch chuyển để đảm bảo tính phân tán của dây qua từng kỳ.
    """
    # Công thức này giúp 115 dây của cùng 1 số sẽ 'tỏa' ra nhiều hướng ở kỳ sau
    prime_step = 131  # Dùng số nguyên tố để tăng độ phủ
    return f"{((wire_id * prime_step) + k) % 100:02d}"

# --- THUẬT TOÁN TRUY VẾT 27 LỚP ---
def calculate_matrix_convergence(v_loto, current_stt):
    # Khởi tạo bảng điểm đủ 100 số
    total_scores = {f"{i:02d}": 0 for i in range(100)}
    
    if not v_loto:
        return total_scores

    # Quét toàn bộ 11.449 sợi dây
    for wire_id in range(TOTAL_WIRES):
        # Tìm số mà dây này tạo ra ở kỳ VỪA NHẬP (STT hiện tại)
        num_at_current = get_wire_number(wire_id, current_stt)
        
        # Nếu dây này là dây "thắng" (nằm trong 27 số vừa về)
        if num_at_current in v_loto:
            # Phóng tới kỳ TIẾP THEO (STT + 1)
            num_at_next = get_wire_number(wire_id, current_stt + 1)
            # Cộng dồn mật độ hội tụ
            total_scores[num_at_next] += 1
                
    return total_scores

# --- 2. GIAO DIỆN ---
st.set_page_config(page_title="Matrix 11.449 - Final Trace", layout="wide")
st.title("⚡ MATRIX 11.449 - TRUY VẾT HỘI TỤ BIT")

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

    st.session_state['raw_input'] = st.text_area("27 giải kỳ này:", value=st.session_state['raw_input'], height=150)
    st.session_state['gdb_val'] = st.text_input("GĐB kỳ này:", value=st.session_state['gdb_val'], max_chars=2)

    if st.button("🔥 CHẠY ĐỐI SOÁT & TRUY VẾT"):
        raw_list = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        v_loto_now = [n[-2:] for n in raw_list[:27]]
        current_stt = len(st.session_state['db']['history']) + 1
        
        # --- BƯỚC 1: ĐỐI SOÁT LỊCH SỬ ---
        rank_val = "-"
        last_top10, last_10nhi, last_vungne = [], [], []
        old_scores = st.session_state['db'].get('final_scores', {})
        
        if sum(old_scores.values()) > 0:
            df_old = pd.DataFrame(list(old_scores.items()), columns=['Số', 'Điểm']).sort_values(by='Điểm', ascending=False).reset_index(drop=True)
            try: rank_val = df_old[df_old['Số'] == st.session_state['gdb_val']].index[0]
            except: pass
            last_top10 = df_old.head(10)['Số'].tolist()
            last_10nhi = df_old.iloc[10:20]['Số'].tolist()
            last_vungne = df_old.tail(20)['Số'].tolist()

        # --- BƯỚC 2: TRUY VẾT MỚI (Reset điểm cũ, tính lại từ đầu) ---
        new_scores = calculate_matrix_convergence(v_loto_now, current_stt)
        
        # --- BƯỚC 3: CẬP NHẬT LỊCH SỬ ---
        def get_hit_str(targets, results):
            if not targets: return "0"
            hits = [n for n in targets if n in results]
            nhay = sum([results.count(n) for n in hits])
            return f"{nhay} ({','.join(sorted(list(set(hits))))})" if hits else "0"

        res = {
            "STT": current_stt,
            "GĐB": st.session_state['gdb_val'],
            "Hạng GĐB": rank_val,
            "Top 10": get_hit_str(last_top10, v_loto_now),
            "10 Nhì": get_hit_str(last_10nhi, v_loto_now),
            "Né": get_hit_str(last_vungne, v_loto_now)
        }
        
        st.session_state['db']['history'].append(res)
        st.session_state['db']['final_scores'] = new_scores
        st.rerun()

# --- 3. HIỂN THỊ ---
if st.session_state['db'].get('final_scores'):
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📊 TỔNG DÂY HỘI TỤ (KỲ TIẾP)")
        # Lấy bảng điểm mới nhất
        score_data = st.session_state['db']['final_scores']
        df_show = pd.DataFrame(list(score_data.items()), columns=['Số', 'Số Dây'])
        # Sắp xếp và Reset index để Hạng (Rank) chuẩn từ 0-99
        df_show = df_show.sort_values(by='Số Dây', ascending=False).reset_index(drop=True)
        st.dataframe(df_show, use_container_width=True, height=600)

    with c2:
        st.subheader("📜 LỊCH SỬ TRUY VẾT")
        if st.session_state['db']['history']:
            st.table(pd.DataFrame(st.session_state['db']['history']))
        
        st.divider()
        st.subheader("🎯 DÀN QUÂN DỰ BÁO")
        num = st.number_input("Số lượng lấy:", 1, 100, 10)
        st.code(", ".join(df_show.head(num)['Số'].tolist()))
        
        st.download_button("💾 XUẤT JSON", data=json.dumps(st.session_state['db']), file_name="matrix_trace_final.json")

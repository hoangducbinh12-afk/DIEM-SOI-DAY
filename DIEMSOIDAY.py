import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. KHỞI TẠO ---
BIT_COUNT = 107
TOTAL_WIRES = BIT_COUNT * BIT_COUNT # 11.449 dây

# Khởi tạo kho lưu trữ nếu chưa có
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "last_loto": [],      # Lưu 27 số của kỳ vừa nhập để làm trạm phát cho kỳ sau
        "history": [],        # Lưu lịch sử đối soát
        "final_counts": {f"{i:02d}": 0 for i in range(100)} # Mặc định bằng 0
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""
if 'gdb_val' not in st.session_state: st.session_state['gdb_val'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])
reader = load_ocr()

# --- THUẬT TOÁN BIẾN ĐỔI BIT ---
def get_wire_number(wire_id, k):
    """
    Xác định con số sợi dây tạo ra tại kỳ thứ k.
    Công thức dịch Bit: (Vị trí gốc + STT kỳ * Bước nhảy) % 100
    """
    step = 13 # Bước nhảy ma trận
    return f"{(wire_id + k * step) % 100:02d}"

def calculate_convergence(last_loto, current_stt):
    """
    Truy vết: Lấy 27 số kỳ trước, tìm dây tạo ra chúng, 
    xem kỳ này các dây đó hội tụ về số nào.
    """
    prediction_map = {f"{i:02d}": 0 for i in range(100)}
    if not last_loto:
        return prediction_map # Nếu chưa có kỳ trước thì trả về toàn 0

    last_stt = current_stt - 1
    # Duyệt 11.449 sợi dây
    for wire_id in range(TOTAL_WIRES):
        # Số mà dây này tạo ra ở kỳ TRƯỚC
        num_last_period = get_wire_number(wire_id, last_stt)
        
        # Nếu số đó nằm trong danh sách 27 số đã về kỳ trước
        if num_last_period in last_loto:
            # Xem kỳ NÀY dây đó tạo ra số gì
            num_this_period = get_wire_number(wire_id, current_stt)
            prediction_map[num_this_period] += 1
            
    return prediction_map

# --- 2. GIAO DIỆN ---
st.set_page_config(page_title="Matrix 11.449 - Bit Trace", layout="wide")
st.title("⚡ MATRIX 11.449 - TRUY VẾT BIẾN ĐỔI BIT")

with st.sidebar:
    st.header("📂 DỮ LIỆU ĐẦU VÀO")
    
    # Nạp file JSON
    load_file = st.file_uploader("📥 Nạp dữ liệu (.json)", type=['json'])
    if load_file and st.button("XÁC NHẬN NẠP"):
        st.session_state['db'] = json.load(load_file)
        st.success("Đã khôi phục ma trận!")
        st.rerun()

    if st.button("🚨 RESET ALL"):
        st.session_state.clear()
        st.rerun()

    st.divider()
    # NÚT QUÉT ẢNH ĐÃ QUAY TRỞ LẠI
    uploaded_img = st.file_uploader("📸 Quét ảnh kết quả", type=['jpg', 'jpeg', 'png'])
    if uploaded_img and st.button("BẮT ĐẦU QUÉT OCR"):
        with st.spinner("Đang đọc bảng kết quả..."):
            img_pil = Image.open(uploaded_img)
            results = reader.readtext(np.array(img_pil), detail=0)
            nums = [n for n in results if n.isdigit() and 2 <= len(n) <= 5]
            if nums:
                st.session_state['raw_input'] = ", ".join(nums)
                st.session_state['gdb_val'] = nums[0][-2:]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("27 giải kỳ này:", value=st.session_state['raw_input'], height=120)
    st.session_state['gdb_val'] = st.text_input("GĐB kỳ này:", value=st.session_state['gdb_val'], max_chars=2)

    if st.button("🔥 CHẠY TRUY VẾT KỲ MỚI"):
        # Xử lý input
        raw_list = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        v_loto_now = [n[-2:] for n in raw_list[:27]]
        current_stt = len(st.session_state['db']['history']) + 1
        
        # 1. ĐỐI SOÁT (Dựa trên dự báo của kỳ trước đã lưu trong final_counts)
        rank_val = "-"
        last_top10 = []
        if st.session_state['db'].get('final_counts'):
            df_old = pd.DataFrame(list(st.session_state['db']['final_counts'].items()), columns=['Số', 'Dây'])
            df_old = df_old.sort_values(by='Dây', ascending=False).reset_index(drop=True)
            try: rank_val = df_old[df_old['Số'] == st.session_state['gdb_val']].index[0]
            except: pass
            last_top10 = df_old.head(10)['Số'].tolist()

        # 2. TRUY VẾT DÂY CHO KỲ TIẾP THEO
        # Dùng 27 số vừa nổ (v_loto_now) để tìm dàn cho kỳ (current_stt + 1)
        new_counts = calculate_convergence(v_loto_now, current_stt + 1)
        
        # 3. LƯU LỊCH SỬ
        def get_hit_str(targets, results):
            hits = [n for n in targets if n in results]
            if not hits: return "0"
            return f"{sum([results.count(n) for n in hits])} ({','.join(hits)})"

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
        st.dataframe(df_show, use_container_width=True, height=500)

    with c2:
        st.subheader("📜 LỊCH SỬ TRUY VẾT BIT")
        st.table(pd.DataFrame(st.session_state['db']['history']))
        
        st.divider()
        st.subheader("🎯 DÀN DỰ BÁO KỲ TIẾP THEO")
        num = st.number_input("Số lượng quân:", 1, 100, 10)
        st.code(", ".join(df_show.head(num)['Số'].tolist()))
        
        st.download_button("💾 XUẤT JSON", data=json.dumps(st.session_state['db']), file_name="matrix_trace_bit.json")

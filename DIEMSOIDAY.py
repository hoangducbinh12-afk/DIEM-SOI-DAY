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

if 'db' not in st.session_state:
    st.session_state['db'] = {str(i): {"score": DEFAULT_SCORE, "streak_win": 0, "streak_loss": 0} for i in range(TOTAL_WIRES)}
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""
if 'gdb_val' not in st.session_state: st.session_state['gdb_val'] = ""
if 'final_counts' not in st.session_state: st.session_state['final_counts'] = None
if 'v_loto' not in st.session_state: st.session_state['v_loto'] = []
if 'history' not in st.session_state: st.session_state['history'] = []

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])
reader = load_ocr()

# --- THUẬT TOÁN ĐẾM DÂY HỘI TỤ (CHÍNH XÁC) ---
def trace_and_count_wires(db, loto_list):
    actual_db = db.get('matrix', db) if isinstance(db.get('matrix'), dict) else db
    new_matrix = json.loads(json.dumps(actual_db))
    
    # 1. Cập nhật trạng thái thắng/thua cho từng dây dựa trên KQ kỳ vừa nhập
    for wire_id in range(TOTAL_WIRES):
        w_str = str(wire_id)
        wire = new_matrix[w_str]
        num_formed = f"{wire_id % 100:02d}"
        
        if num_formed in loto_list:
            wire["streak_loss"] = 0
            wire["streak_win"] += 1
        else:
            wire["streak_win"] = 0
            wire["streak_loss"] += 1
            
    # 2. Đếm số dây đang "SỐNG" (streak_win > 0) hội tụ về từng số 00-99
    wire_counts = {f"{i:02d}": 0 for i in range(100)}
    for wire_id in range(TOTAL_WIRES):
        w_str = str(wire_id)
        wire = new_matrix[w_str]
        num_formed = f"{wire_id % 100:02d}"
        if wire["streak_win"] > 0:
            wire_counts[num_formed] += 1
            
    return new_matrix, wire_counts

# --- 2. GIAO DIỆN ---
st.set_page_config(page_title="Matrix Trace Pro", layout="wide")
st.title("⚡ MATRIX 11.449 - TRUY VẾT MẬT ĐỘ DÂY")

with st.sidebar:
    st.header("📂 DỮ LIỆU")
    load_file = st.file_uploader("📥 Nạp JSON", type=['json'])
    if load_file and st.button("XÁC NHẬN NẠP"):
        data = json.load(load_file)
        st.session_state['db'] = data.get('matrix', data)
        st.session_state['history'] = data.get('history', [])
        st.session_state['final_counts'] = data.get('last_counts', None)
        st.success("Đã nạp dữ liệu!")
        st.rerun()

    if st.button("🚨 RESET ALL"):
        st.session_state.clear()
        st.rerun()

    st.divider()
    uploaded_img = st.file_uploader("📸 Quét ảnh", type=['jpg', 'jpeg', 'png'])
    if uploaded_img and st.button("QUÉT OCR"):
        results = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
        nums = [n for n in results if n.isdigit() and 2 <= len(n) <= 5]
        if nums:
            st.session_state['raw_input'] = ", ".join(nums)
            st.session_state['gdb_val'] = nums[0][-2:]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("27 giải:", value=st.session_state['raw_input'], height=100)
    st.session_state['gdb_val'] = st.text_input("GĐB:", value=st.session_state['gdb_val'], max_chars=2)

    if st.button("🔥 CHẠY TRUY VẾT DÂY"):
        raw_list = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        v_loto = [n[-2:] for n in raw_list[:27]]
        st.session_state['v_loto'] = v_loto
        
        # Lấy bảng đếm hiện tại (trước khi update) để tính Rank cho lịch sử
        rank_val = "-"
        if st.session_state['final_counts']:
            old_df = pd.DataFrame(list(st.session_state['final_counts'].items()), columns=['Số', 'Dây']).sort_values(by='Dây', ascending=False).reset_index(drop=True)
            try: rank_val = old_df[old_df['Số'] == st.session_state['gdb_val']].index[0]
            except: pass
            old_top10 = old_df.head(10)['Số'].tolist()
            old_10nhi = old_df.iloc[10:20]['Số'].tolist()
            old_vungne = old_df.tail(20)['Số'].tolist()
        else:
            old_top10, old_10nhi, old_vungne = [], [], []

        # Chạy cập nhật ma trận và đếm dây
        new_matrix, counts = trace_and_count_wires(st.session_state['db'], v_loto)
        st.session_state['db'] = new_matrix
        st.session_state['final_counts'] = counts # Gán để bảng nhảy số ngay
        
        # Đếm nháy cho lịch sử
        def get_hits(target_nums, result_list):
            if not target_nums: return "0"
            hits = [n for n in target_nums if n in result_list]
            nhay = sum([result_list.count(n) for n in hits])
            no = sorted(list(set(hits)))
            return f"{nhay} ({','.join(no)})" if nhay > 0 else "0"

        # Cập nhật lịch sử trúng
        res = {
            "STT": len(st.session_state['history']) + 1,
            "GĐB": st.session_state['gdb_val'],
            "Hạng GĐB": rank_val,
            "Top 10": get_hits(old_top10, v_loto),
            "10 Nhì": get_hits(old_10nhi, v_loto),
            "Vùng Né": get_hits(old_vungne, v_loto)
        }
        st.session_state['history'].append(res)
        st.rerun() # Ép giao diện vẽ lại để nhảy số lượng dây mới

# --- 3. HIỂN THỊ ---
if st.session_state['final_counts']:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📊 XẾP HẠNG MẬT ĐỘ DÂY")
        df_display = pd.DataFrame(list(st.session_state['final_counts'].items()), columns=['Số', 'Số Dây Nối'])
        df_display['TT'] = df_display['Số'].apply(lambda x: "🔥" if x in st.session_state['v_loto'] else "⏳")
        # Ép sắp xếp theo số dây nối
        df_display = df_display.sort_values(by='Số Dây Nối', ascending=False).reset_index(drop=True)
        st.dataframe(df_display, use_container_width=True, height=550)

    with c2:
        st.subheader("📜 LỊCH SỬ TRUY VẾT")
        if st.session_state['history']:
            # Đảo ngược để STT mới nhất ở dưới hoặc trên tùy ý, ở đây để mặc định append
            st.table(pd.DataFrame(st.session_state['history']))
        
        st.divider()
        st.subheader("🎯 LẤY QUÂN")
        num_pick = st.number_input("Số lượng lấy:", 1, 100, 10)
        st.code(", ".join(df_display.head(num_pick)['Số'].tolist()))
        
        save_data = {
            "matrix": st.session_state['db'], 
            "history": st.session_state['history'], 
            "last_counts": st.session_state['final_counts']
        }
        st.download_button("💾 XUẤT JSON", data=json.dumps(save_data), file_name="matrix_trace_v2.json")

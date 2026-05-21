import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. KHỞI TẠO ---
TOTAL_POS = 107 
TOTAL_WIRES = TOTAL_POS * TOTAL_POS 

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "last_digits": "",    
        "last_loto": [],      
        "history": [], 
        "final_scores": {f"{i:02d}": 0 for i in range(100)}
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""
if 'gdb_val' not in st.session_state: st.session_state['gdb_val'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])
reader = load_ocr()

def extract_data(raw_list):
    v_loto = [s[-2:] for s in raw_list[:27]]
    all_digits = "".join(raw_list)
    return all_digits[:TOTAL_POS], v_loto

def calculate_convergence(old_digits, old_loto, current_digits):
    scores = {f"{i:02d}": 0 for i in range(100)}
    if not old_digits or not old_loto:
        return scores
    for win_num in old_loto:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                if (old_digits[i] + old_digits[j]) == win_num:
                    formed_new = current_digits[i] + current_digits[j]
                    scores[formed_new] += 1
    return scores

# --- 2. GIAO DIỆN ---
st.set_page_config(page_title="Matrix Trace Pro V4", layout="wide")
st.title("⚡ MATRIX 11.449 - TRUY VẾT & PHÂN LỚP CHI TIẾT")

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

    st.session_state['raw_input'] = st.text_area("Nhập 27 giải:", value=st.session_state['raw_input'], height=150)
    st.session_state['gdb_val'] = st.text_input("GĐB kỳ này:", value=st.session_state['gdb_val'], max_chars=2)

    if st.button("🔥 CHẠY ĐỐI SOÁT & TRUY VẾT"):
        raw_list = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len(raw_list) < 27:
            st.error("Phải nhập đủ 27 giải!")
        else:
            curr_digits, curr_loto = extract_data(raw_list)
            
            # --- BƯỚC 1: ĐỐI SOÁT LỊCH SỬ THEO PHÂN LỚP MỚI ---
            old_scores = st.session_state['db']['final_scores']
            df_old = pd.DataFrame(list(old_scores.items()), columns=['Số', 'Điểm']).sort_values(by='Điểm', ascending=False).reset_index(drop=True)
            
            rank_val = "-"
            # Danh sách các nhóm hạng
            groups = {
                "Top 4": [], "Top 10": [], "Top 15": [], "Top 20": [], 
                "Top 27": [], "Né": [], "Loại": [], "Cao": []
            }
            
            if df_old['Điểm'].sum() > 0:
                try: rank_val = df_old[df_old['Số'] == st.session_state['gdb_val']].index[0]
                except: pass
                groups["Top 4"]  = df_old.iloc[0:4]['Số'].tolist()
                groups["Top 10"] = df_old.iloc[4:10]['Số'].tolist()
                groups["Top 15"] = df_old.iloc[10:15]['Số'].tolist()
                groups["Top 20"] = df_old.iloc[15:20]['Số'].tolist()
                groups["Top 27"] = df_old.iloc[20:27]['Số'].tolist()
                groups["Né"]     = df_old.iloc[80:90]['Số'].tolist()
                groups["Loại"]   = df_old.iloc[90:95]['Số'].tolist()
                groups["Cao"]    = df_old.iloc[95:100]['Số'].tolist()

            def get_hit_str(targets, results):
                if not targets: return "0"
                hits = [n for n in targets if n in results]
                nhay = sum([results.count(n) for n in hits])
                return f"{nhay} ({','.join(sorted(list(set(hits))))})" if hits else "0"

            res = {
                "STT": len(st.session_state['db']['history']) + 1,
                "GĐB": st.session_state['gdb_val'],
                "Hạng": rank_val,
                "Top 4": get_hit_str(groups["Top 4"], curr_loto),
                "Top 10": get_hit_str(groups["Top 10"], curr_loto),
                "Top 15": get_hit_str(groups["Top 15"], curr_loto),
                "Top 20": get_hit_str(groups["Top 20"], curr_loto),
                "Top 27": get_hit_str(groups["Top 27"], curr_loto),
                "Né (80-89)": get_hit_str(groups["Né"], curr_loto),
                "Loại (90-94)": get_hit_str(groups["Loại"], curr_loto),
                "Cao (95-99)": get_hit_str(groups["Cao"], curr_loto)
            }

            # --- BƯỚC 2: TÍNH TOÁN DÀN ĐIỂM CHO KỲ TIẾP ---
            new_scores = calculate_convergence(
                st.session_state['db']['last_digits'], 
                st.session_state['db']['last_loto'], 
                curr_digits
            )
            
            st.session_state['db']['history'].append(res)
            st.session_state['db']['final_scores'] = new_scores
            st.session_state['db']['last_digits'] = curr_digits
            st.session_state['db']['last_loto'] = curr_loto
            st.rerun()

# --- 3. HIỂN THỊ ---
if st.session_state['db'].get('final_scores'):
    c1, c2 = st.columns([1, 3]) # Mở rộng cột lịch sử tối đa
    with c1:
        st.subheader("📊 DỰ BÁO KỲ TIẾP")
        df_show = pd.DataFrame(list(st.session_state['db']['final_scores'].items()), columns=['Số', 'Điểm'])
        df_show = df_show.sort_values(by='Điểm', ascending=False).reset_index(drop=True)
        st.dataframe(df_show, use_container_width=True, height=600)

    with c2:
        st.subheader("📜 LỊCH SỬ PHÂN LỚP")
        if st.session_state['db']['history']:
            st.table(pd.DataFrame(st.session_state['db']['history']))
        
        st.divider()
        st.subheader("🎯 LẤY DÀN NHANH")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            num = st.number_input("Số lượng quân đầu bảng:", 1, 100, 4)
            st.code(", ".join(df_show.head(num)['Số'].tolist()))
        
        st.download_button("💾 LƯU DỮ LIỆU", data=json.dumps(st.session_state['db']), file_name="matrix_trace_v4.json")

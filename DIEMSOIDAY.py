import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. KHỞI TẠO ---
# 107 vị trí chữ số từ 27 giải (MB chuẩn)
# GĐB(5), G1(5), G2(10), G3(30), G4(16), G5(24), G6(9), G7(8) = 107
TOTAL_POS = 107 
TOTAL_WIRES = TOTAL_POS * TOTAL_POS # 11.449 dây

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "last_digits": "",    # 107 chữ số kỳ trước
        "last_loto": [],      # 27 con loto kỳ trước
        "history": [], 
        "final_scores": {f"{i:02d}": 0 for i in range(100)}
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""
if 'gdb_val' not in st.session_state: st.session_state['gdb_val'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])
reader = load_ocr()

# --- HÀM TRÍCH XUẤT 107 CHỮ SỐ ---
def extract_data(raw_list):
    # Lấy loto (2 số cuối của mỗi giải)
    v_loto = [s[-2:] for s in raw_list[:27]]
    # Lấy chuỗi 107 chữ số (ghép tất cả các giải lại)
    all_digits = "".join(raw_list)
    return all_digits[:TOTAL_POS], v_loto

# --- THUẬT TOÁN TRUY VẾT VỊ TRÍ TĨNH ---
def calculate_convergence(old_digits, old_loto, current_digits):
    scores = {f"{i:02d}": 0 for i in range(100)}
    if not old_digits or not old_loto:
        return scores

    # Duyệt qua 27 con loto đã về ở kỳ trước (Nguồn phát)
    for win_num in old_loto:
        # Tìm tất cả các cặp vị trí (i, j) đã tạo ra win_num ở kỳ trước
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                # Kết hợp chữ số tại vị trí i và j ở kỳ TRƯỚC
                formed_old = old_digits[i] + old_digits[j]
                
                if formed_old == win_num:
                    # Nếu đúng dây này đã ăn, xem kỳ NÀY nó tạo ra số gì
                    formed_new = current_digits[i] + current_digits[j]
                    scores[formed_new] += 1
    return scores

# --- 2. GIAO DIỆN ---
st.set_page_config(page_title="Matrix 11.449 Trace", layout="wide")
st.title("⚡ MATRIX 11.449 - TRUY VẾT VỊ TRÍ TĨNH")

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

    if st.button("🔥 CHẠY TRUY VẾT"):
        raw_list = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len(raw_list) < 27:
            st.error("Phải nhập đủ 27 giải!")
        else:
            curr_digits, curr_loto = extract_data(raw_list)
            
            # 1. TÍNH ĐIỂM HỘI TỤ CHO KỲ NÀY (Dựa trên Kỳ Trước)
            new_scores = calculate_convergence(
                st.session_state['db']['last_digits'], 
                st.session_state['db']['last_loto'], 
                curr_digits
            )
            
            # 2. ĐỐI SOÁT LỊCH SỬ (Bảng điểm mới tính vs Kết quả vừa nhập)
            df_new = pd.DataFrame(list(new_scores.items()), columns=['Số', 'Điểm']).sort_values(by='Điểm', ascending=False).reset_index(drop=True)
            
            rank_val = "-"
            if sum(new_scores.values()) > 0:
                try: rank_val = df_new[df_new['Số'] == st.session_state['gdb_val']].index[0]
                except: pass

            def get_hit_str(targets, results):
                hits = [n for n in targets if n in results]
                nhay = sum([results.count(n) for n in hits])
                return f"{nhay} ({','.join(sorted(list(set(hits))))})" if hits else "0"

            res = {
                "STT": len(st.session_state['db']['history']) + 1,
                "GĐB": st.session_state['gdb_val'],
                "Hạng": rank_val,
                "Top 10": get_hit_str(df_new.head(10)['Số'].tolist(), curr_loto),
                "10 Nhì": get_hit_str(df_new.iloc[10:20]['Số'].tolist(), curr_loto),
                "7 Ba": get_hit_str(df_new.iloc[20:27]['Số'].tolist(), curr_loto),
                "Né": get_hit_str(df_new.tail(20)['Số'].tolist(), curr_loto)
            }
            
            # 3. CẬP NHẬT TRẠNG THÁI
            st.session_state['db']['history'].append(res)
            st.session_state['db']['final_scores'] = new_scores
            st.session_state['db']['last_digits'] = curr_digits
            st.session_state['db']['last_loto'] = curr_loto
            st.rerun()

# --- 3. HIỂN THỊ ---
if st.session_state['db'].get('final_scores'):
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📊 TỔNG DÂY HỘI TỤ")
        df_show = pd.DataFrame(list(st.session_state['db']['final_scores'].items()), columns=['Số', 'Điểm'])
        df_show = df_show.sort_values(by='Điểm', ascending=False).reset_index(drop=True)
        st.dataframe(df_show, use_container_width=True, height=600)

    with c2:
        st.subheader("📜 LỊCH SỬ TRUY VẾT")
        if st.session_state['db']['history']:
            st.table(pd.DataFrame(st.session_state['db']['history']))
        
        st.divider()
        st.subheader("🎯 DÀN QUÂN THEO MẬT ĐỘ")
        num = st.number_input("Số lượng lấy:", 1, 100, 10)
        st.code(", ".join(df_show.head(num)['Số'].tolist()))

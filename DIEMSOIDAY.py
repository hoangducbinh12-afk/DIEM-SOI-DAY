import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. KHỞI TẠO HỆ THỐNG ---
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

# --- THUẬT TOÁN TRUY VẾT HỘI TỤ (GIỮ NGUYÊN LOGIC CHUẨN) ---
def calculate_convergence(old_digits, old_loto, current_digits):
    scores = {f"{i:02d}": 0 for i in range(100)}
    if not old_digits or not old_loto:
        return scores

    current_matrix = [[current_digits[i] + current_digits[j] for j in range(TOTAL_POS)] for i in range(TOTAL_POS)]
    
    for win_num in old_loto:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                if (old_digits[i] + old_digits[j]) == win_num:
                    formed_new = current_matrix[i][j]
                    scores[formed_new] += 1
    return scores

# --- 2. GIAO DIỆN ---
st.set_page_config(page_title="Matrix Ultra V6", layout="wide")
st.markdown("<h2 style='text-align: center; color: #00FFAA;'>⚡ MATRIX 11.449 - SIÊU PHÂN LỚP V6</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.header("📂 HỆ THỐNG")
    if st.button("🚨 RESET TOÀN BỘ"):
        st.session_state.clear()
        st.rerun()

    st.divider()
    uploaded_img = st.file_uploader("📸 Quét ảnh KQ", type=['jpg', 'jpeg', 'png'])
    if uploaded_img and st.button("BẮT ĐẦU OCR"):
        with st.spinner("Đang trích xuất..."):
            img_np = np.array(Image.open(uploaded_img))
            results = reader.readtext(img_np, detail=0)
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
            
            # --- BƯỚC 1: ĐỐI SOÁT LỊCH SỬ THEO 16 PHÂN VÙNG ---
            old_scores = st.session_state['db']['final_scores']
            df_old = pd.DataFrame(list(old_scores.items()), columns=['Số', 'Điểm']).sort_values(by='Điểm', ascending=False).reset_index(drop=True)
            
            rank_val = "-"
            # Định nghĩa các vùng hạng (Slicing)
            slices = {
                "T5": (0, 5), "T10": (5, 10), "T15": (10, 15), "T20": (15, 20),
                "T25": (20, 25), "T30": (25, 30), "T35": (30, 35), "T40": (35, 40),
                "T45": (40, 45), "T50": (45, 50), "T60": (50, 60), "T70": (60, 70),
                "T80": (70, 80), "T90": (80, 90), "T95": (90, 95), "Cao": (95, 100)
            }
            
            groups_data = {}
            if sum(old_scores.values()) > 0:
                try: rank_val = df_old[df_old['Số'] == st.session_state['gdb_val']].index[0]
                except: pass
                for key, (start, end) in slices.items():
                    groups_data[key] = df_old.iloc[start:end]['Số'].tolist()

            def get_hit(targets, results):
                if not targets: return "0"
                hits = [n for n in targets if n in results]
                count = sum([results.count(n) for n in hits])
                return f"{count}({','.join(sorted(list(set(hits))))})" if count > 0 else "0"

            res = {
                "STT": len(st.session_state['db']['history']) + 1,
                "GĐB": st.session_state['gdb_val'],
                "Hạng": rank_val,
                "T5": get_hit(groups_data.get("T5"), curr_loto),
                "T10": get_hit(groups_data.get("T10"), curr_loto),
                "T15": get_hit(groups_data.get("T15"), curr_loto),
                "T20": get_hit(groups_data.get("T20"), curr_loto),
                "T25": get_hit(groups_data.get("T25"), curr_loto),
                "T30": get_hit(groups_data.get("T30"), curr_loto),
                "T35": get_hit(groups_data.get("T35"), curr_loto),
                "T40": get_hit(groups_data.get("T40"), curr_loto),
                "T45": get_hit(groups_data.get("T45"), curr_loto),
                "T50": get_hit(groups_data.get("T50"), curr_loto),
                "T60": get_hit(groups_data.get("T60"), curr_loto),
                "T70": get_hit(groups_data.get("T70"), curr_loto),
                "T80": get_hit(groups_data.get("T80"), curr_loto),
                "T90": get_hit(groups_data.get("T90"), curr_loto),
                "T95": get_hit(groups_data.get("T95"), curr_loto),
                "Cao": get_hit(groups_data.get("Cao"), curr_loto),
            }

            # --- BƯỚC 2: TÍNH DỰ BÁO MỚI ---
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
    c1, c2 = st.columns([1, 4]) # Ép bảng lịch sử rộng ra để chứa 16 cột
    with c1:
        st.subheader("📊 DỰ BÁO TIẾP")
        score_df = pd.DataFrame(list(st.session_state['db']['final_scores'].items()), columns=['Số', 'Điểm'])
        score_df = score_df.sort_values(by='Điểm', ascending=False).reset_index(drop=True)
        st.dataframe(score_df, use_container_width=True, height=600)

    with c2:
        st.subheader("📜 LỊCH SỬ SIÊU PHÂN LỚP")
        if st.session_state['db']['history']:
            # Hiển thị bảng lịch sử (Streamlit sẽ tự tạo thanh cuộn ngang nếu quá dài)
            st.dataframe(pd.DataFrame(st.session_state['db']['history']), use_container_width=True)
        
        st.divider()
        st.subheader("🎯 LẤY DÀN NHANH")
        n = st.number_input("Số quân đầu bảng:", 1, 100, 5)
        st.code(", ".join(score_df.head(n)['Số'].tolist()))
        st.download_button("💾 XUẤT JSON", data=json.dumps(st.session_state['db']), file_name="matrix_v6.json")

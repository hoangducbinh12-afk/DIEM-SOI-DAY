import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. KHỞI TẠO HỆ THỐNG ---
TOTAL_POS = 107 
TOTAL_WIRES = TOTAL_POS * TOTAL_POS # 11.449 dây

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

# --- HÀM TRÍCH XUẤT 107 VỊ TRÍ ---
def extract_data(raw_list):
    # Lấy 27 loto cuối giải
    v_loto = [s[-2:] for s in raw_list[:27]]
    # Ghép chuỗi 107 chữ số từ bảng kết quả
    all_digits = "".join(raw_list)
    return all_digits[:TOTAL_POS], v_loto

# --- THUẬT TOÁN TRUY VẾT HỘI TỤ (BẢN CHUẨN CỦA MÀY) ---
def calculate_convergence(old_digits, old_loto, current_digits):
    # Khởi tạo bảng 100 số
    scores = {f"{i:02d}": 0 for i in range(100)}
    if not old_digits or not old_loto:
        return scores

    # Mảng 2 chiều lưu giá trị cặp (i, j) của kỳ hiện tại để dùng nhiều lần (tối ưu tốc độ)
    current_matrix = [[current_digits[i] + current_digits[j] for j in range(TOTAL_POS)] for i in range(TOTAL_POS)]
    
    # QUÉT ĐỦ 27 SỐ (CÓ TÍNH NHÁY)
    for win_num in old_loto:
        # Với mỗi nháy nổ, duyệt toàn bộ 11.449 tọa độ
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                # Nếu tọa độ này kỳ trước tạo ra số nổ
                if (old_digits[i] + old_digits[j]) == win_num:
                    # Lấy số mà tọa độ này tạo ra ở kỳ này
                    formed_new = current_matrix[i][j]
                    # CỘNG DỒN ĐIỂM (Càng nhiều nháy, điểm hội tụ càng cao)
                    scores[formed_new] += 1
    return scores

# --- 2. GIAO DIỆN NGƯỜI DÙNG ---
st.set_page_config(page_title="Matrix 11.449 - Ultra Trace", layout="wide")
st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>⚡ MATRIX 11.449 - TRUY VẾT HỘI TỤ V5</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.header("📂 QUẢN LÝ DỮ LIỆU")
    if st.button("🚨 RESET TOÀN BỘ MÁY"):
        st.session_state.clear()
        st.rerun()

    st.divider()
    # Công cụ OCR
    uploaded_img = st.file_uploader("📸 Quét ảnh kết quả", type=['jpg', 'jpeg', 'png'])
    if uploaded_img and st.button("BẮT ĐẦU PHÂN TÍCH ẢNH"):
        with st.spinner("Đang trích xuất dữ liệu..."):
            img_np = np.array(Image.open(uploaded_img))
            results = reader.readtext(img_np, detail=0)
            nums = [n for n in results if n.isdigit() and 2 <= len(n) <= 5]
            if nums:
                st.session_state['raw_input'] = ", ".join(nums)
                st.session_state['gdb_val'] = nums[0][-2:]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Nhập 27 giải loto:", value=st.session_state['raw_input'], height=150)
    st.session_state['gdb_val'] = st.text_input("Con GĐB kỳ này:", value=st.session_state['gdb_val'], max_chars=2)

    if st.button("🔥 CHẠY ĐỐI SOÁT & TRUY VẾT"):
        raw_list = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len(raw_list) < 27:
            st.error("Lỗi: Phải nhập đủ 27 giải kết quả!")
        else:
            curr_digits, curr_loto = extract_data(raw_list)
            
            # --- BƯỚC 1: ĐỐI SOÁT DÀN ĐIỂM CŨ (Của hôm qua) ---
            old_scores = st.session_state['db']['final_scores']
            df_old = pd.DataFrame(list(old_scores.items()), columns=['Số', 'Điểm']).sort_values(by='Điểm', ascending=False).reset_index(drop=True)
            
            rank_gdb = "-"
            groups = {k: [] for k in ["T4", "T10", "T15", "T20", "T27", "Né", "Loại", "Cao"]}
            
            if sum(old_scores.values()) > 0:
                try: rank_gdb = df_old[df_old['Số'] == st.session_state['gdb_val']].index[0]
                except: pass
                # Phân lớp theo yêu cầu của mày
                groups["T4"]  = df_old.iloc[0:4]['Số'].tolist()
                groups["T10"] = df_old.iloc[4:10]['Số'].tolist()
                groups["T15"] = df_old.iloc[10:15]['Số'].tolist()
                groups["T20"] = df_old.iloc[15:20]['Số'].tolist()
                groups["T27"] = df_old.iloc[20:27]['Số'].tolist()
                groups["Né"]  = df_old.iloc[80:90]['Số'].tolist()
                groups["Loại"]= df_old.iloc[90:95]['Số'].tolist()
                groups["Cao"] = df_old.iloc[95:100]['Số'].tolist()

            def check_hit(targets, results):
                if not targets: return "0"
                hits = [n for n in targets if n in results]
                count = sum([results.count(n) for n in hits])
                return f"{count} ({','.join(sorted(list(set(hits))))})" if count > 0 else "0"

            # Lưu vào lịch sử
            history_entry = {
                "STT": len(st.session_state['db']['history']) + 1,
                "GĐB": st.session_state['gdb_val'],
                "Hạng": rank_gdb,
                "Top 4": check_hit(groups["T4"], curr_loto),
                "Top 10": check_hit(groups["T10"], curr_loto),
                "Top 15": check_hit(groups["T15"], curr_loto),
                "Top 20": check_hit(groups["T20"], curr_loto),
                "Top 27": check_hit(groups["T27"], curr_loto),
                "Né(80-89)": check_hit(groups["Né"], curr_loto),
                "Loại(90-94)": check_hit(groups["Loại"], curr_loto),
                "Cao(95-99)": check_hit(groups["Cao"], curr_loto)
            }

            # --- BƯỚC 2: TÍNH DÀN ĐIỂM MỚI (Cho ngày mai) ---
            # Dùng 107 số hôm qua và 27 loto hôm qua để 'phóng' tới kết quả hôm nay
            new_scores = calculate_convergence(
                st.session_state['db']['last_digits'], 
                st.session_state['db']['last_loto'], 
                curr_digits
            )
            
            # --- BƯỚC 3: CẬP NHẬT DỮ LIỆU ---
            st.session_state['db']['history'].append(history_entry)
            st.session_state['db']['final_scores'] = new_scores
            st.session_state['db']['last_digits'] = curr_digits
            st.session_state['db']['last_loto'] = curr_loto
            st.rerun()

# --- 3. HIỂN THỊ KẾT QUẢ ---
if st.session_state['db'].get('final_scores'):
    c1, c2 = st.columns([1, 3.2]) # Tối ưu không gian cho bảng lịch sử rộng
    
    with c1:
        st.subheader("📊 DỰ BÁO KỲ TIẾP")
        score_df = pd.DataFrame(list(st.session_state['db']['final_scores'].items()), columns=['Số', 'Điểm'])
        score_df = score_df.sort_values(by='Điểm', ascending=False).reset_index(drop=True)
        st.dataframe(score_df, use_container_width=True, height=600)

    with c2:
        st.subheader("📜 LỊCH SỬ ĐỐI SOÁT CHI TIẾT")
        if st.session_state['db']['history']:
            st.table(pd.DataFrame(st.session_state['db']['history']))
        
        st.divider()
        st.subheader("🎯 TRÍCH XUẤT QUÂN")
        pick_num = st.number_input("Lấy số lượng quân đầu bảng:", 1, 100, 4)
        st.code(", ".join(score_df.head(pick_num)['Số'].tolist()))
        
        # Cho phép tải dữ liệu về để lưu lại chuỗi truy vết
        st.download_button("💾 XUẤT FILE JSON", data=json.dumps(st.session_state['db']), file_name="matrix_full_v5.json")

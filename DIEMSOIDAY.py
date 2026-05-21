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
if 'final_scores' not in st.session_state: st.session_state['final_scores'] = None
if 'v_loto' not in st.session_state: st.session_state['v_loto'] = []
if 'history' not in st.session_state: st.session_state['history'] = []

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

reader = load_ocr()

def update_matrix(db, loto_list, gdb_loto):
    new_db = json.loads(json.dumps(db))
    num_scores = {f"{i:02d}": 0.0 for i in range(100)}
    for wire_id in range(TOTAL_WIRES):
        w_str = str(wire_id)
        wire = new_db[w_str]
        num_formed = f"{wire_id % 100:02d}"
        is_hit = num_formed in loto_list
        is_gdb = (num_formed == gdb_loto)
        if is_hit:
            wire["streak_loss"] = 0
            wire["streak_win"] += 1
            if wire["streak_win"] <= 3:
                if is_gdb: wire["score"] += 5.0
                wire["score"] += float(loto_list.count(num_formed))
            else: wire["score"] -= 0.5
        else:
            wire["streak_win"] = 0
            wire["streak_loss"] += 1
            if wire["streak_loss"] >= 4: wire["score"] += 0.5
        num_scores[num_formed] += wire["score"]
    return new_db, num_scores

# --- 2. GIAO DIỆN ---
st.set_page_config(page_title="Matrix 11.449", layout="wide")
st.title("⚡ MATRIX 11.449 - DÒNG ĐIỆN MA TRẬN")

with st.sidebar:
    st.header("📂 ĐẦU VÀO")
    if st.button("🚨 RESET ALL DATA"):
        st.session_state['db'] = {str(i): {"score": DEFAULT_SCORE, "streak_win": 0, "streak_loss": 0} for i in range(TOTAL_WIRES)}
        st.session_state['final_scores'] = None
        st.session_state['history'] = []
        st.rerun()

    uploaded_img = st.file_uploader("Quét ảnh kết quả", type=['jpg', 'jpeg', 'png'])
    if uploaded_img and st.button("BẮT ĐẦU QUÉT OCR"):
        img_pil = Image.open(uploaded_img)
        results = reader.readtext(np.array(img_pil), detail=0)
        nums = [n for n in results if n.isdigit() and 2 <= len(n) <= 5]
        if nums:
            st.session_state['raw_input'] = ", ".join(nums)
            st.session_state['gdb_val'] = nums[0][-2:]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Dữ liệu 27 giải:", value=st.session_state['raw_input'], height=100)
    st.session_state['gdb_val'] = st.text_input("GĐB:", value=st.session_state['gdb_val'], max_chars=2)

    if st.button("XÁC NHẬN & CHẠY"):
        raw_list = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        v_loto = [n[-2:] for n in raw_list[:27]]
        st.session_state['v_loto'] = v_loto
        
        new_db, scores = update_matrix(st.session_state['db'], v_loto, st.session_state['gdb_val'])
        st.session_state['db'] = new_db
        st.session_state['final_scores'] = scores
        
        # Logic đếm NHÁY và chi tiết
        df_temp = pd.DataFrame(list(scores.items()), columns=['Số', 'Điểm']).sort_values(by='Điểm', ascending=False)
        
        def get_hit_info(target_nums, result_list):
            hits_in_set = [num for num in target_nums if num in result_list]
            total_nhay = sum([result_list.count(num) for num in hits_in_set])
            list_no = sorted(list(set(hits_in_set)))
            return f"{total_nhay} ({','.join(list_no)})"

        res = {
            "STT": len(st.session_state['history']) + 1,
            "GĐB": st.session_state['gdb_val'],
            "Top 10": get_hit_info(df_temp.head(10)['Số'].tolist(), v_loto),
            "10 Nhì": get_hit_info(df_temp.iloc[10:20]['Số'].tolist(), v_loto),
            "7 Ba": get_hit_info(df_temp.iloc[20:27]['Số'].tolist(), v_loto),
            "20 Né": get_hit_info(df_temp.tail(20)['Số'].tolist(), v_loto)
        }
        # XẾP DƯỚI LÊN TRÊN: Kỳ mới nhất thêm vào cuối danh sách
        st.session_state['history'].append(res)

# --- 3. HIỂN THỊ ---
if st.session_state['final_scores']:
    c_left, c_right = st.columns([1.2, 1.8])

    with c_left:
        st.subheader("📊 BẢNG 100 SỐ (CAO -> THẤP)")
        df_display = pd.DataFrame(list(st.session_state['final_scores'].items()), columns=['Số', 'Điểm'])
        df_display['TT'] = df_display['Số'].apply(lambda x: "🔥" if x in st.session_state['v_loto'] else "⏳")
        df_display = df_display.sort_values(by='Điểm', ascending=False).reset_index(drop=True)
        st.dataframe(df_display, use_container_width=True, height=450)

    with c_right:
        st.subheader("📜 LỊCH SỬ ĐỐI SOÁT (Mới nhất ở dưới)")
        # Hiển thị bảng lịch sử (Mặc định xếp từ dưới lên theo thứ tự append)
        st.table(pd.DataFrame(st.session_state['history']))
        
        st.divider()
        st.subheader("🎯 LẤY QUÂN")
        num_pick = st.number_input("Lấy bao nhiêu số:", 1, 100, 10)
        st.code(", ".join(df_display.head(num_pick)['Số'].tolist()))
        st.download_button("💾 XUẤT JSON", data=json.dumps(st.session_state['db']), file_name="matrix_data.json")

import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Matrix V10.0 - The Balance", layout="wide")
TOTAL_POS = 107 

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "last_loto": [],
        "history": [],
        "last_predictions": {},
        "core_four": [],
        "gan_tracker": {str(i).zfill(2): 0 for i in range(100)},
        "bet_tracker": {str(i).zfill(2): 0 for i in range(100)}
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

# --- 2. LOGIC TÍNH TOÁN CÂN BẰNG ---

def update_trackers(current_loto):
    for i in range(100):
        num = str(i).zfill(2)
        if num in current_loto:
            st.session_state['db']['gan_tracker'][num] = 0
            st.session_state['db']['bet_tracker'][num] += 1
        else:
            st.session_state['db']['gan_tracker'][num] += 1
            st.session_state['db']['bet_tracker'][num] = 0

def get_balanced_four(new_wire_scores, current_digits):
    mapping_1d = {str(i).zfill(2): 0 for i in range(100)}
    coords_1 = np.argwhere(new_wire_scores == 1)
    for r, c in coords_1:
        num = current_digits[r] + current_digits[c]
        mapping_1d[num] += 1

    gan_list = [n for n, d in st.session_state['db']['gan_tracker'].items() if d > 10]
    bet_list = [n for n, s in st.session_state['db']['bet_tracker'].items() if s >= 3]
    blacklist = set(gan_list + bet_list)

    # Phân loại quân số theo mức điểm
    levels = {s: [] for s in range(1, 11)}
    max_s = int(new_wire_scores.max())
    for s in range(1, max_s + 1):
        coords = np.argwhere(new_wire_scores == s)
        for r, c in coords:
            num = current_digits[r] + current_digits[c]
            if num not in blacklist:
                levels[s].append(num)

    final_4 = []
    
    # 1. Lấy 2 con từ mức "Nổ Đậm" (3đ hoặc 4đ)
    for s in [4, 3, 5]:
        candidates = [n for n in levels[s] if n not in final_4]
        # Ưu tiên con có 3-10 dây 1đ (vùng nhiệt ổn định)
        candidates = sorted(candidates, key=lambda x: abs(mapping_1d[x] - 6))
        final_4.extend(candidates[:2])
        if len(final_4) >= 2: break

    # 2. Lấy 1 con từ mức "Đang lên" (2đ) nhưng cực sạch
    candidates_2 = [n for n in levels[2] if n not in final_4]
    candidates_2 = sorted(candidates_2, key=lambda x: mapping_1d[x]) # Càng ít dây 1đ càng tốt
    if candidates_2: final_4.append(candidates_2[0])

    # 3. Lấy 1 con từ mức "Cực cao" (Max điểm)
    candidates_max = [n for n in levels[max_s] if n not in final_4]
    if candidates_max: final_4.append(candidates_max[0])

    # 4. Fallback nếu vẫn thiếu
    if len(final_4) < 4:
        all_remain = []
        for s in range(max_s, 0, -1):
            all_remain.extend([n for n in levels[s] if n not in final_4])
        final_4.extend(all_remain[:(4-len(final_4))])

    return final_4[:4]

def process_matrix(current_digits, current_loto, gdb_val):
    db = st.session_state['db']
    update_trackers(current_loto)
    old_scores = np.array(db['wire_scores'], dtype=int)
    old_digits = db['last_digits']
    old_core_4 = db.get('core_four', [])
    old_preds = db.get('last_predictions', {})

    new_wire_scores = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int)
    
    hit_report = {"STT": len(db['history']) + 1, "GĐB": gdb_val}
    if old_core_4:
        found_4 = [n for n in old_core_4 if n in current_loto]
        count_4 = sum([current_loto.count(n) for n in found_4])
        hit_report["Dàn 4q"] = f"{count_4} ({','.join(found_4) if found_4 else '0'})"
        if count_4 >= 2 or gdb_val in old_core_4: hit_report["Kết quả"] = "WIN 🔥"
        elif count_4 == 1: hit_report["Kết quả"] = "✅"
        else: hit_report["Kết quả"] = "❌"

    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                if (old_digits[i] + old_digits[j]) in current_loto:
                    new_wire_scores[i][j] = old_scores[i][j] + 1

    # Tạo dự báo cho hiển thị
    new_preds = {}
    max_s = int(new_wire_scores.max())
    for s in range(1, max_s + 1):
        coords = np.argwhere(new_wire_scores == s)
        l_map = {}
        for r, c in coords:
            n = current_digits[r] + current_digits[c]
            l_map[n] = l_map.get(n, 0) + 1
        new_preds[int(s)] = {"nums": sorted([n for n, count in l_map.items() if count == 1])}

    st.session_state['db']['wire_scores'] = new_wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    st.session_state['db']['last_predictions'] = new_preds
    st.session_state['db']['core_four'] = get_balanced_four(new_wire_scores, current_digits)
    st.session_state['db']['history'].insert(0, hit_report)

# --- 3. GIAO DIỆN ---
st.markdown("<h1 style='text-align: center; color: #00FFAA;'>⚡ MATRIX V10.0: THE BALANCE</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("💾 DATA")
    uploaded_file = st.file_uploader("Nạp JSON", type=['json'])
    if uploaded_file and st.button("📥 Phục hồi"):
        st.session_state['db'] = json.load(uploaded_file)
        st.rerun()
    if st.session_state['db']['last_digits']:
        st.download_button("💾 Lưu JSON", json.dumps(st.session_state['db']), "matrix_v10.json")
    
    st.divider()
    uploaded_img = st.file_uploader("Quét KQ", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("OCR"):
        reader = load_ocr()
        res = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
        nums = [n for n in res if n.isdigit() and 2 <= len(n) <= 5]
        if nums: 
            st.session_state['raw_input'] = ", ".join(nums)
            st.session_state['gdb_ocr'] = nums[0][-2:]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Chuỗi giải:", value=st.session_state.get('raw_input', ""), height=100)
    gdb_val = st.text_input("GĐB:", value=st.session_state.get('gdb_ocr', ""), max_chars=2)

    if st.button("🔥 CHẠY BALANCE", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len("".join(raw)) >= TOTAL_POS:
            process_matrix("".join(raw)[:TOTAL_POS], [s[-2:] for s in raw[:27]], gdb_val)
            st.rerun()
    st.button("🚨 RESET ALL", on_click=lambda: st.session_state.clear())

c1, c2 = st.columns([1, 2.5])
with c1:
    st.markdown("""
        <div style="background-color: #FFD700; padding: 20px; border-radius: 15px; text-align: center; border: 3px solid #000;">
            <h3 style="color: #000; margin-bottom: 5px;">🎯 TỨ THỦ CÂN BẰNG</h3>
    """, unsafe_allow_html=True)
    c4 = st.session_state['db'].get('core_four', [])
    if c4:
        st.markdown(f"<h1 style='color: #000; font-size: 45px; font-weight: bold;'>{' - '.join(c4)}</h1>", unsafe_allow_html=True)
    else: st.info("Chờ nạp dữ liệu...")
    st.markdown("</div>", unsafe_allow_html=True)
    
    with st.expander("📊 Chi tiết mức điểm"):
        preds = st.session_state['db'].get('last_predictions', {})
        for lv in sorted([int(k) for k in preds.keys()], reverse=True):
            data = preds[str(lv)] if str(lv) in preds else preds[lv]
            st.write(f"**{lv}đ:** {', '.join(data['nums'])}")

with c2:
    st.subheader("📋 LỊCH SỬ ĐỐI SOÁT")
    if st.session_state['db']['history']:
        df = pd.DataFrame(st.session_state['db']['history']).fillna("0")
        cols = list(df.columns)
        for c in ["Kết quả", "Dàn 4q"]:
            if c in cols: cols.insert(2, cols.pop(cols.index(c)))
        st.dataframe(df[cols], use_container_width=True)

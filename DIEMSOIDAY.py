import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Matrix V9.7 - Original Hybrid", layout="wide")
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

# --- 2. LOGIC TÍNH TOÁN ---

def update_trackers(current_loto):
    """Cập nhật Lô Gan và Lô Bệt"""
    for i in range(100):
        num = str(i).zfill(2)
        if num in current_loto:
            st.session_state['db']['gan_tracker'][num] = 0
            st.session_state['db']['bet_tracker'][num] += 1
        else:
            st.session_state['db']['gan_tracker'][num] += 1
            st.session_state['db']['bet_tracker'][num] = 0

def get_power_score_4(new_wire_scores, current_digits):
    mapping_1d = {str(i).zfill(2): 0 for i in range(100)}
    coords_1 = np.argwhere(new_wire_scores == 1)
    for r, c in coords_1:
        num = current_digits[r] + current_digits[c]
        mapping_1d[num] += 1

    # BỘ LỌC CHẶN NGAY TỪ ĐẦU
    gan_list = [n for n, d in st.session_state['db']['gan_tracker'].items() if d > 10]
    bet_list = [n for n, s in st.session_state['db']['bet_tracker'].items() if s >= 3]
    blacklist = set(gan_list + bet_list)

    power_map = {str(i).zfill(2): 0 for i in range(100)}
    max_s = int(new_wire_scores.max())
    
    for s in range(1, max_s + 1):
        coords = np.argwhere(new_wire_scores == s)
        for r, c in coords:
            num = current_digits[r] + current_digits[c]
            
            # NẾU NẰM TRONG DANH SÁCH CHẶN THÌ KHÔNG TÍNH ĐIỂM
            if num in blacklist: continue
            
            base = s ** 2
            bonus = 10 if 3 <= mapping_1d[num] <= 12 else 0
            power_map[num] += (base + bonus)

    sorted_p = sorted(power_map.items(), key=lambda x: x[1], reverse=True)
    final = [item[0] for item in sorted_p[:4] if item[1] > 0]
    
    # Fallback nếu thiếu quân (vẫn phải tránh blacklist)
    if len(final) < 4:
        for s in range(max_s, 0, -1):
            coords = np.argwhere(new_wire_scores == s)
            for r, c in coords:
                n = current_digits[r] + current_digits[c]
                if n not in final and n not in blacklist:
                    final.append(n)
                if len(final) >= 4: break
            if len(final) >= 4: break
            
    return final[:4]

def process_matrix(current_digits, current_loto, gdb_val):
    db = st.session_state['db']
    update_trackers(current_loto)
    
    old_scores = np.array(db['wire_scores'], dtype=int)
    old_digits = db['last_digits']
    old_preds = db['last_predictions']
    old_core_4 = db.get('core_four', [])
    
    new_wire_scores = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int)
    
    # --- A. ĐỐI SOÁT ---
    hit_report = {"STT": len(db['history']) + 1, "GĐB": gdb_val}
    if old_core_4:
        found_4 = [n for n in old_core_4 if n in current_loto]
        count_4 = sum([current_loto.count(n) for n in found_4])
        hit_report["Dàn 4q"] = f"{count_4} ({','.join(found_4) if found_4 else '0'})"
        if count_4 >= 2 or gdb_val in old_core_4: hit_report["Kết quả"] = "WIN 🔥"
        elif count_4 == 1: hit_report["Kết quả"] = "✅"
        else: hit_report["Kết quả"] = "❌"

    if old_preds:
        for lv, data in {int(k):v for k,v in old_preds.items()}.items():
            nums = data['nums']
            found = [n for n in nums if n in current_loto]
            hit_report[f"{lv}đ"] = f"{sum([current_loto.count(n) for n in found])}"

    # --- B. CẬP NHẬT ĐIỂM ---
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                if (old_digits[i] + old_digits[j]) in current_loto:
                    new_wire_scores[i][j] = old_scores[i][j] + 1

    # --- C. DỰ BÁO ---
    new_preds = {}
    max_s = int(new_wire_scores.max())
    if max_s > 0:
        for s in range(1, max_s + 1):
            coords = np.argwhere(new_wire_scores == s)
            if len(coords) == 0: continue
            l_map = {}
            for r, c in coords:
                n = current_digits[r] + current_digits[c]
                l_map[n] = l_map.get(n, 0) + 1
            new_preds[int(s)] = {"nums": sorted([n for n, c in l_map.items() if c == 1]), "total_wires": int(len(coords))}

    st.session_state['db']['wire_scores'] = new_wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    st.session_state['db']['last_predictions'] = new_preds
    st.session_state['db']['core_four'] = get_power_score_4(new_wire_scores, current_digits)
    st.session_state['db']['history'].insert(0, hit_report)

# --- 3. GIAO DIỆN ---
st.markdown("<h1 style='text-align: center; color: #00FFAA;'>⚡ MATRIX V9.7: SNIPER HYBRID</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("💾 DỮ LIỆU")
    uploaded_file = st.file_uploader("Nạp JSON", type=['json'])
    if uploaded_file and st.button("📥 Phục hồi"):
        st.session_state['db'] = json.load(uploaded_file)
        st.rerun()
    if st.session_state['db']['last_digits']:
        st.download_button("💾 Lưu JSON", json.dumps(st.session_state['db']), "matrix_v97.json")
    
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

    if st.button("🔥 CHẠY SNIPER", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len("".join(raw)) >= TOTAL_POS:
            process_matrix("".join(raw)[:TOTAL_POS], [s[-2:] for s in raw[:27]], gdb_val)
            st.rerun()
    st.button("🚨 RESET ALL", on_click=lambda: st.session_state.clear())

c1, c2 = st.columns([1, 2.5])
with c1:
    st.markdown("""
        <div style="background-color: #FFD700; padding: 20px; border-radius: 15px; text-align: center; border: 3px solid #000;">
            <h3 style="color: #000; margin-bottom: 5px;">🎯 SNIPER TỨ THỦ</h3>
    """, unsafe_allow_html=True)
    c4 = st.session_state['db'].get('core_four', [])
    if c4:
        st.markdown(f"<h1 style='color: #000; font-size: 45px; font-weight: bold;'>{' - '.join(c4)}</h1>", unsafe_allow_html=True)
    else: st.info("Chờ nạp kỳ 2...")
    st.markdown("</div>", unsafe_allow_html=True)
    
    gan_list = [n for n, d in st.session_state['db']['gan_tracker'].items() if d > 10]
    bet_list = [n for n, s in st.session_state['db']['bet_tracker'].items() if s >= 3]
    with st.expander("🚫 DANH SÁCH ĐANG CHẶN"):
        st.write(f"Gan > 10 kỳ: {', '.join(gan_list)}")
        st.write(f"Bệt >= 3 kỳ: {', '.join(bet_list)}")

with c2:
    st.subheader("📋 BÁO CÁO LỊCH SỬ")
    if st.session_state['db']['history']:
        df = pd.DataFrame(st.session_state['db']['history']).fillna("0")
        cols = list(df.columns)
        for c in ["Kết quả", "Dàn 4q"]:
            if c in cols: cols.insert(2, cols.pop(cols.index(c)))
        st.dataframe(df[cols], use_container_width=True)

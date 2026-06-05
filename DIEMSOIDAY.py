import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="MATRIX V9.3.8 - TAM THỦ PRO", layout="wide")
TOTAL_POS = 107 

# Custom CSS: Giữ nguyên phong cách Vàng - Đen rực rỡ
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #262730; color: white; border: 1px solid #444; }
    .stButton>button:hover { border-color: #FFD700; color: #FFD700; }
    .report-card { background-color: #FFD700; padding: 20px; border-radius: 15px; text-align: center; border: 3px solid #000000; box-shadow: 0px 4px 15px rgba(0,0,0,0.5); }
    .metric-text { color: #000000; font-size: 50px; font-weight: 900; letter-spacing: 5px; margin: 0; }
    .section-header { color: #FFD700; border-bottom: 2px solid #FFD700; padding-bottom: 5px; margin-bottom: 15px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "last_loto": [],
        "history": [],
        "last_predictions": {},
        "core_four": []
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

# --- 2. LOGIC SNIPER (GIỮ NGUYÊN THUẬT TOÁN GỐC) ---

def get_power_score_4(new_wire_scores, current_digits):
    mapping_1d = {str(i).zfill(2): 0 for i in range(100)}
    coords_1 = np.argwhere(new_wire_scores == 1)
    for r, c in coords_1:
        num = current_digits[r] + current_digits[c]
        mapping_1d[num] += 1

    power_map = {str(i).zfill(2): 0 for i in range(100)}
    max_s = int(new_wire_scores.max())
    
    for s in range(2, max_s + 1):
        coords = np.argwhere(new_wire_scores == s)
        for r, c in coords:
            num = current_digits[r] + current_digits[c]
            base_score = s ** 2
            heat_bonus = 15 if 5 <= mapping_1d[num] <= 15 else 0
            heat_penalty = -30 if mapping_1d[num] > 30 else 0
            power_map[num] += (base_score + heat_bonus + heat_penalty)

    sorted_power = sorted(power_map.items(), key=lambda x: x[1], reverse=True)
    final_4 = [item[0] for item in sorted_power[:4] if item[1] > 0]
    
    if not final_4 and max_s >= 1:
        fallback = []
        for s in range(max_s, 0, -1):
            coords = np.argwhere(new_wire_scores == s)
            for r, c in coords:
                num = current_digits[r] + current_digits[c]
                if num not in fallback: fallback.append(num)
                if len(fallback) >= 4: break
            if len(fallback) >= 4: break
        final_4 = fallback[:4]
    return final_4

def process_matrix(current_digits, current_loto, gdb_val):
    db = st.session_state['db']
    old_scores = np.array(db['wire_scores'], dtype=int)
    old_digits = db['last_digits']
    old_preds = db['last_predictions']
    old_core_4 = db.get('core_four', [])
    
    new_wire_scores = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int)
    
    # --- A. ĐỐI SOÁT LỊCH SỬ (THÊM CỘT TAM THỦ) ---
    hit_report = {"STT": len(db['history']) + 1, "GĐB": gdb_val}
    
    if old_core_4:
        # Đối soát Tứ Thủ gốc
        found_4 = [n for n in old_core_4 if n in current_loto]
        count_4 = sum([current_loto.count(n) for n in found_4])
        hit_report["Dàn 4q"] = f"{count_4} ({','.join(found_4) if found_4 else '0'})"
        
        # ĐỐI SOÁT TAM THỦ (Lấy 3 con đầu tiên từ trái sang)
        old_tam_thu = old_core_4[:3]
        found_3 = [n for n in old_tam_thu if n in current_loto]
        count_3 = sum([current_loto.count(n) for n in found_3])
        hit_report["Dàn 3q"] = f"{count_3} ({','.join(found_3) if found_3 else '0'})"
        
        # Chấm điểm kết quả dựa trên Tứ Thủ
        if count_4 >= 2 or gdb_val in old_core_4:
            hit_report["Kết quả"] = "THẮNG 🔥"
        elif count_4 == 1:
            hit_report["Kết quả"] = "✅"
        else:
            hit_report["Kết quả"] = "❌"

    if old_preds:
        fixed_preds = {int(k): v for k, v in old_preds.items()}
        for lv in sorted(fixed_preds.keys(), reverse=True):
            nums = fixed_preds[lv]['nums']
            found = [n for n in nums if n in current_loto]
            hit_report[f"{lv}đ"] = f"{sum([current_loto.count(n) for n in found])}"

    # --- B. CẬP NHẬT ĐIỂM MA TRẬN ---
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                num_past = old_digits[i] + old_digits[j]
                if num_past in current_loto:
                    new_wire_scores[i][j] = old_scores[i][j] + 1

    # --- C. TẠO DỰ BÁO MỚI ---
    new_preds = {}
    max_s = int(new_wire_scores.max())
    if max_s > 0:
        for s in range(1, max_s + 1):
            coords = np.argwhere(new_wire_scores == s)
            if len(coords) == 0: continue
            level_map = {}
            for r, c in coords:
                num = current_digits[r] + current_digits[c]
                level_map[num] = level_map.get(num, 0) + 1
            isolated = [n for n, count in level_map.items() if count == 1]
            new_preds[int(s)] = {"nums": sorted(isolated), "total_wires": int(len(coords))}

    st.session_state['db']['wire_scores'] = new_wire_scores.tolist()
    st.session_state['db']['last_digits'] = current_digits
    st.session_state['db']['last_loto'] = current_loto
    st.session_state['db']['last_predictions'] = new_preds
    st.session_state['db']['core_four'] = get_power_score_4(new_wire_scores, current_digits)
    st.session_state['db']['history'].insert(0, hit_report)

# --- 3. GIAO DIỆN ---
st.markdown("<h1 style='text-align: center; color: #FFD700;'>⚡ MATRIX SNIPER V9.3.8</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("💾 DỮ LIỆU")
    uploaded_file = st.file_uploader("Nạp JSON", type=['json'])
    if uploaded_file and st.button("📥 PHỤC HỒI"):
        st.session_state['db'] = json.load(uploaded_file)
        st.rerun()
    if st.session_state['db']['last_digits']:
        st.download_button("💾 LƯU JSON", json.dumps(st.session_state['db']), "matrix_v938.json")
    
    st.divider()
    st.header("📸 QUÉT ẢNH")
    uploaded_img = st.file_uploader("Chọn ảnh", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("QUÉT OCR"):
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

# --- 4. KHU VỰC HIỂN THỊ ---
c1, c2 = st.columns([1, 2.5])

with c1:
    st.markdown("""
        <div class="report-card">
            <h3 style="color: #000000; margin-bottom: 5px;">🎯 TỨ THỦ CORE 4</h3>
    """, unsafe_allow_html=True)
    c4 = st.session_state['db'].get('core_four', [])
    if c4:
        st.markdown(f"<p class='metric-text'>{' - '.join(c4)}</p>", unsafe_allow_html=True)
        # Gợi ý Tam Thủ nhanh dưới ô Tứ Thủ cho mày dễ nhìn
        st.markdown(f"<p style='color: #333; font-weight: bold; margin-top: 5px;'>👉 Tam thủ rút gọn: <span style='color: red; font-size: 20px;'>{', '.join(c4[:3])}</span></p>", unsafe_allow_html=True)
    else:
        st.write("Đang tính toán...")
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("<h2 class='section-header'>📊 CHI TIẾT DÂY</h2>", unsafe_allow_html=True)
    preds = st.session_state['db'].get('last_predictions', {})
    if preds:
        sorted_keys = sorted([int(k) for k in preds.keys()], reverse=True)
        for lv in sorted_keys:
            data = preds[str(lv)] if str(lv) in preds else preds[lv]
            with st.expander(f"Mức {lv}đ ({len(data['nums'])}q)"):
                st.code(", ".join(data['nums']))

with c2:
    st.markdown("<h2 class='section-header'>📋 LỊCH SỬ KẾT QUẢ</h2>", unsafe_allow_html=True)
    if st.session_state['db']['history']:
        df_hist = pd.DataFrame(st.session_state['db']['history']).fillna("0")
        
        # Đưa các cột quan trọng lên đầu bảng: STT -> Kết quả -> Dàn 3q -> Dàn 4q -> GĐB
        cols = list(df_hist.columns)
        important = ["Kết quả", "Dàn 3q", "Dàn 4q", "GĐB", "STT"]
        for col in reversed(important):
            if col in cols: cols.insert(0, cols.pop(cols.index(col)))
        
        if "Kết quả" in df_hist.columns:
            st.dataframe(
                df_hist[cols].style.map(
                    lambda x: 'color: #FFD700; font-weight: bold' if x == "THẮNG 🔥" else 
                              ('color: #00FFBB' if x == "✅" else ('color: #FF4B4B' if x == "❌" else '')),
                    subset=["Kết quả"]
                ),
                use_container_width=True,
                height=600
            )
        else:
            st.dataframe(df_hist[cols], use_container_width=True)

import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Matrix V9.4.1 - Ultimate Sniper", layout="wide")
TOTAL_POS = 107 

# Custom CSS: Thiết kế giao diện Cyber Deep trầm sang trọng, phóng to chữ hết cỡ
st.markdown("""
    <style>
    .main { background-color: #0A0D14; }
    .stButton>button { width: 100%; border-radius: 6px; height: 3em; background-color: #161B26; color: #F0F4F8; border: 1px solid #2D3748; font-weight: bold; }
    .stButton>button:hover { border-color: #F59E0B; color: #F59E0B; }
    
    /* Khung hiển thị Tứ thủ & Tam thủ được thiết kế lại sang trọng, dịu mắt */
    .result-box-4 { background-color: #111827; padding: 25px; border-radius: 15px; text-align: center; border: 3px solid #D97706; margin-bottom: 20px; box-shadow: 0px 4px 20px rgba(217,119,6,0.15); }
    .result-box-3 { background-color: #111827; padding: 25px; border-radius: 15px; text-align: center; border: 3px solid #2563EB; margin-bottom: 20px; box-shadow: 0px 4px 20px rgba(37,99,235,0.15); }
    
    /* Cỡ chữ được phóng to cực đại theo yêu cầu */
    .big-text-4 { color: #FBBF24; font-size: 65px; font-weight: 900; letter-spacing: 6px; margin: 0; line-height: 1.1; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
    .big-text-3 { color: #60A5FA; font-size: 55px; font-weight: 900; letter-spacing: 6px; margin: 0; line-height: 1.1; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
    
    .section-header { color: #94A3B8; border-bottom: 2px solid #1E293B; padding-bottom: 6px; margin-bottom: 20px; font-weight: bold; letter-spacing: 1px; }
    .stExpander { border: 1px solid #1E293B; background-color: #0A0D14; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "last_loto": [],
        "history": [],
        "last_predictions": {},
        "core_four": [],
        "gan_tracker": {str(i).zfill(2): 0 for i in range(100)},
        "bet_tracker": {str(i).zfill(2): 0 for i in range(100)},
        "total_hits": {str(i).zfill(2): 0 for i in range(100)}
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

# --- 2. THUẬT TOÁN ĐỐI SOÁT VÀ LỌC MA TRẬN ---

def check_and_fix_db_structure():
    """Đảm bảo không bị lỗi KeyError khi người dùng nạp file cấu trúc cũ"""
    db = st.session_state['db']
    if "gan_tracker" not in db or not db["gan_tracker"]:
        db["gan_tracker"] = {str(i).zfill(2): 0 for i in range(100)}
    if "bet_tracker" not in db or not db["bet_tracker"]:
        db["bet_tracker"] = {str(i).zfill(2): 0 for i in range(100)}
    if "total_hits" not in db or not db["total_hits"]:
        db["total_hits"] = {str(i).zfill(2): 0 for i in range(100)}

def update_statistics(current_loto):
    check_and_fix_db_structure()
    db = st.session_state['db']
    for i in range(100):
        num = str(i).zfill(2)
        db['total_hits'][num] += current_loto.count(num)
        if num in current_loto:
            db['gan_tracker'][num] = 0
            db['bet_tracker'][num] += 1
        else:
            db['gan_tracker'][num] += 1
            db['bet_tracker'][num] = 0

def get_filtered_power_score_4(new_wire_scores, current_digits):
    check_and_fix_db_structure()
    db = st.session_state['db']
    
    mapping_1d = {str(i).zfill(2): 0 for i in range(100)}
    coords_1 = np.argwhere(new_wire_scores == 1)
    for r, c in coords_1:
        num = current_digits[r] + current_digits[c]
        mapping_1d[num] += 1

    # Hệ thống 4 lưới lọc cấm địa
    gan_blacklist = [n for n, days in db['gan_tracker'].items() if days > 12]
    bet_blacklist = [n for n, streak in db['bet_tracker'].items() if streak >= 2]
    
    sorted_hits = sorted(db['total_hits'].items(), key=lambda x: (x[1], int(x[0])))
    bottom_20 = [item[0] for item in sorted_hits[:20]]
    
    high_level_blacklist = set()
    max_s = int(new_wire_scores.max())
    if max_s >= 5:
        for s in range(5, max_s + 1):
            coords_high = np.argwhere(new_wire_scores == s)
            for r, c in coords_high:
                high_level_blacklist.add(current_digits[r] + current_digits[c])

    final_blacklist = set(gan_blacklist + bet_blacklist + bottom_20 + list(high_level_blacklist))

    power_map = {str(i).zfill(2): 0 for i in range(100)}
    for s in range(2, max_s + 1):
        coords = np.argwhere(new_wire_scores == s)
        for r, c in coords:
            num = current_digits[r] + current_digits[c]
            if num in final_blacklist: continue
            
            base_score = s ** 2
            heat_bonus = 15 if 5 <= mapping_1d[num] <= 15 else 0
            heat_penalty = -30 if mapping_1d[num] > 30 else 0
            power_map[num] += (base_score + heat_bonus + heat_penalty)

    sorted_power = sorted(power_map.items(), key=lambda x: x[1], reverse=True)
    final_4 = [item[0] for item in sorted_power[:4] if item[1] > 0]
    
    if len(final_4) < 4:
        for s in range(max_s, 0, -1):
            coords = np.argwhere(new_wire_scores == s)
            for r, c in coords:
                num = current_digits[r] + current_digits[c]
                if num not in final_4 and num not in final_blacklist:
                    final_4.append(num)
                if len(final_4) >= 4: break
            if len(final_4) >= 4: break
            
    return final_4[:4]

def process_matrix(current_digits, current_loto, gdb_val):
    db = st.session_state['db']
    update_statistics(current_loto)
    
    old_scores = np.array(db['wire_scores'], dtype=int)
    old_digits = db['last_digits']
    old_preds = db['last_predictions']
    old_core_4 = db.get('core_four', [])
    
    new_wire_scores = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int)
    
    # --- A. ĐỐI SOÁT LỊCH SỬ VỚI LOGIC PHÂN TÁCH MỚI ---
    hit_report = {"STT": len(db['history']) + 1, "GĐB": gdb_val}
    if old_core_4:
        # 1. Đối soát riêng cho Tam thủ (3 con đầu)
        old_tam_thu = old_core_4[:3]
        found_3 = [n for n in old_tam_thu if n in current_loto]
        count_3 = sum([current_loto.count(n) for n in found_3])
        hit_report["Dàn 3q"] = f"{count_3} ({','.join(found_3) if found_3 else '0'})"
        
        # 2. Đối soát cho Tứ thủ gốc
        found_4 = [n for n in old_core_4 if n in current_loto]
        count_4 = sum([current_loto.count(n) for n in found_4])
        hit_report["Dàn 4q"] = f"{count_4} ({','.join(found_4) if found_4 else '0'})"
        
        # 3. CHẤM ĐIỂM KẾT QUẢ THEO TIÊU CHUẨN MỚI CỦA MÀY
        if count_3 >= 1 or gdb_val in old_tam_thu:
            hit_report["Kết quả"] = "Win 🔥"  # Chỉ cần ăn ở Tam Thủ hoặc dính Đề Tam Thủ là WIN
        elif count_4 >= 1:
            hit_report["Kết quả"] = "✅"      # Tam thủ trượt nhưng ăn ở con thứ 4 của Tứ thủ
        else:
            hit_report["Kết quả"] = "❌"      # Trắng bảng hoàn toàn

    if old_preds:
        fixed_preds = {int(k): v for k, v in old_preds.items()}
        for lv in sorted(fixed_preds.keys(), reverse=True):
            nums = fixed_preds[lv]['nums']
            found = [n for n in nums if n in current_loto]
            hit_report[f"{lv}đ"] = f"{sum([current_loto.count(n) for n in found])}"

    # --- B. CẬP NHẬT ĐIỂM ---
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                num_past = old_digits[i] + old_digits[j]
                if num_past in current_loto:
                    new_wire_scores[i][j] = old_scores[i][j] + 1

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
    st.session_state['db']['core_four'] = get_filtered_power_score_4(new_wire_scores, current_digits)
    st.session_state['db']['history'].insert(0, hit_report)

# --- 3. GIAO DIỆN ---
st.markdown("<h1 style='text-align: center; color: #E2E8F0; font-weight: bold;'>⚡ MATRIX PRO V9.4.1</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<h3 style='color: #94A3B8;'>💾 DỮ LIỆU CONTROL</h3>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Nạp JSON cấu trúc", type=['json'])
    if uploaded_file and st.button("📥 PHỤC HỒI HỆ THỐNG"):
        st.session_state['db'] = json.load(uploaded_file)
        check_and_fix_db_structure()
        st.rerun()
    if st.session_state['db']['last_digits']:
        st.download_button("💾 XUẤT FILE MA TRẬN", json.dumps(st.session_state['db']), "matrix_v941.json")
    
    st.divider()
    st.markdown("<h3 style='color: #94A3B8;'>📸 CAMERA QUÉT ảnh</h3>", unsafe_allow_html=True)
    uploaded_img = st.file_uploader("Chọn ảnh kết quả", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("QUÉT OCR"):
        reader = load_ocr()
        res = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
        nums = [n for n in res if n.isdigit() and 2 <= len(n) <= 5]
        if nums: 
            st.session_state['raw_input'] = ", ".join(nums)
            st.session_state['gdb_ocr'] = nums[0][-2:]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Bảng kết quả thô:", value=st.session_state.get('raw_input', ""), height=100)
    gdb_val = st.text_input("Đặc biệt (2 số):", value=st.session_state.get('gdb_ocr', ""), max_chars=2)

    if st.button("🔥 CHẠY ASSASSIN SNIPER", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len("".join(raw)) >= TOTAL_POS:
            process_matrix("".join(raw)[:TOTAL_POS], [s[-2:] for s in raw[:27]], gdb_val)
            st.rerun()
    st.button("🚨 XÓA BẢNG TẠM", on_click=lambda: st.session_state.clear())

# --- 4. KHU VỰC HIỂN THỊ CHÍNH ---
c1, c2 = st.columns([1.3, 2.2])

with c1:
    st.markdown("<h2 class='section-header'>🎯 TỌA ĐỘ PHÁT LỰC</h2>", unsafe_allow_html=True)
    c4 = st.session_state['db'].get('core_four', [])
    
    if c4:
        # Khung Tứ Thủ chữ vàng to khổng lồ (65px)
        st.markdown(f"""
            <div class="result-box-4">
                <p style="color: #94A3B8; font-size: 14px; font-weight: bold; margin-bottom: 5px;">🎯 TỨ THỦ CHIẾN THUẬT</p>
                <p class="big-text-4">{' - '.join(c4)}</p>
            </div>
            """, unsafe_allow_html=True)
            
        # Khung Tam Thủ chữ xanh to khổng lồ (55px)
        st.markdown(f"""
            <div class="result-box-3">
                <p style="color: #94A3B8; font-size: 14px; font-weight: bold; margin-bottom: 5px;">🔥 TAM THỦ CHỦ LỰC</p>
                <p class="big-text-3">{' - '.join(c4[:3])}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Hệ thống đang tích lũy xung nhịp. Hãy nạp kỳ tiếp theo.")

    st.divider()
    check_and_fix_db_structure()
    with st.expander("🚫 Hệ thống chặn quân tự động"):
        gan_list = [n for n, days in st.session_state['db']['gan_tracker'].items() if days > 12]
        bet_list = [n for n, streak in st.session_state['db']['bet_tracker'].items() if streak >= 2]
        st.write(f"**Lô Gan (>12 ngày):** {', '.join(gan_list) if gan_list else 'Trống'}")
        st.write(f"**Lô Bệt (>=2 ngày):** {', '.join(bet_list) if bet_list else 'Trống'}")

    st.markdown("<h2 class='section-header'>📊 ĐIỂM SỐ SỢI DÂY</h2>", unsafe_allow_html=True)
    preds = st.session_state['db'].get('last_predictions', {})
    if preds:
        sorted_keys = sorted([int(k) for k in preds.keys()], reverse=True)
        for lv in sorted_keys:
            data = preds[str(lv)] if str(lv) in preds else preds[lv]
            with st.expander(f"Mức {lv}đ ({len(data['nums'])} quân)"):
                st.code(", ".join(data['nums']))

with c2:
    st.markdown("<h2 class='section-header'>📋 BẢNG THỐNG KÊ LỊCH SỬ ĐỐI SOÁT</h2>", unsafe_allow_html=True)
    if st.session_state['db']['history']:
        df_hist = pd.DataFrame(st.session_state['db']['history']).fillna("0")
        cols = list(df_hist.columns)
        important = ["Kết quả", "Dàn 3q", "Dàn 4q", "GĐB", "STT"]
        for col in reversed(important):
            if col in cols: cols.insert(0, cols.pop(cols.index(col)))
        
        if "Kết quả" in df_hist.columns:
            st.dataframe(
                df_hist[cols].style.map(
                    lambda x: 'color: #F59E0B; font-weight: bold' if x == "Win 🔥" else 
                              ('color: #10B981' if x == "✅" else ('color: #EF4444' if x == "❌" else '')),
                    subset=["Kết quả"]
                ),
                use_container_width=True,
                height=650
            )
        else:
            st.dataframe(df_hist[cols], use_container_width=True)

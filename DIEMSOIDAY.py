import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH HỆ THỐNG MÀN HÌNH ---
st.set_page_config(page_title="Matrix V13.6 - SDI Fixed", layout="wide")
TOTAL_POS = 107 

# Custom CSS chuẩn Mobile: Tiêu đề dòng TO/ĐẬM - Số THU NHỎ vừa vặn, sang trọng
st.markdown("""
    <style>
    .main { background-color: #0A0D14; padding: 10px; }
    .stButton>button { width: 100%; border-radius: 6px; height: 3.5em; background-color: #161B26; color: #F0F4F8; border: 1px solid #2D3748; font-weight: bold; }
    .stButton>button:hover { border-color: #FFD700; color: #FFD700; }
    
    .mobile-box-bt { background-color: #05070B; padding: 10px 5px; border-radius: 12px; text-align: center; border: 3px solid #EF4444; margin-bottom: 12px; }
    .mobile-box-st { background-color: #04060A; padding: 10px 5px; border-radius: 12px; text-align: center; border: 3px solid #A855F7; margin-bottom: 12px; }
    .mobile-box-3 { background-color: #030508; padding: 10px 5px; border-radius: 12px; text-align: center; border: 3px solid #2563EB; margin-bottom: 12px; }
    .mobile-box-3c { background-color: #020406; padding: 10px 5px; border-radius: 12px; text-align: center; border: 3px solid #10B981; margin-bottom: 12px; }
    .mobile-box-4 { background-color: #030508; padding: 10px 5px; border-radius: 12px; text-align: center; border: 3px solid #D97706; margin-bottom: 15px; }
    
    .title-text-bt { color: #FF5555 !important; font-size: 16px !important; font-weight: 900 !important; font-family: sans-serif; }
    .title-text-st { color: #A855F7 !important; font-size: 16px !important; font-weight: 900 !important; font-family: sans-serif; }
    .title-text-3 { color: #2563EB !important; font-size: 15px !important; font-weight: 900 !important; font-family: sans-serif; }
    .title-text-3c { color: #10B981 !important; font-size: 15px !important; font-weight: 900 !important; font-family: sans-serif; }
    .title-text-4 { color: #D97706 !important; font-size: 15px !important; font-weight: 900 !important; font-family: sans-serif; }
    
    .mobile-text-bt { color: #FF1E27 !important; font-size: 9.5vw !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 2px; margin: 0; line-height: 1.1; white-space: nowrap !important; }
    .mobile-text-st { color: #A855F7 !important; font-size: 8.0vw !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 1px; margin: 0; line-height: 1.1; white-space: nowrap !important; }
    .mobile-text-3 { color: #FF1E27 !important; font-size: 7.5vw !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 1px; margin: 0; line-height: 1.1; white-space: nowrap !important; }
    .mobile-text-3c { color: #10B981 !important; font-size: 5.2vw !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 1px; margin: 0; line-height: 1.2; }
    .mobile-text-4 { color: #FFD700 !important; font-size: 5.5vw !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 1px; margin: 0; line-height: 1.1; white-space: nowrap !important; }
    </style>
    """, unsafe_allow_html=True)

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "wire_scores": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "break_matrix": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "max_reached_matrix": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "over_1d_matrix": np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "cang_lo_matrix": np.zeros((100, 10), dtype=int).tolist(),
        "last_digits": "",
        "last_loto": [],
        "history": [],
        "last_predictions": {},
        "core_four": [],
        "bach_thu": "",
        "song_thu": "", 
        "loto_3c": [], 
        "gan_tracker": {str(i).zfill(2): 0 for i in range(100)},
        "bet_tracker": {str(i).zfill(2): 0 for i in range(100)},
        "total_hits": {str(i).zfill(2): 0 for i in range(100)}
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

def check_and_fix_db_structure():
    db = st.session_state['db']
    for key in ["gan_tracker", "bet_tracker", "total_hits"]:
        if key not in db or not db[key]: db[key] = {str(i).zfill(2): 0 for i in range(100)}
    if "break_matrix" not in db: db["break_matrix"] = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist()
    if "max_reached_matrix" not in db: db["max_reached_matrix"] = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist()
    if "over_1d_matrix" not in db: db["over_1d_matrix"] = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int).tolist()
    if "cang_lo_matrix" not in db: db["cang_lo_matrix"] = np.zeros((100, 10), dtype=int).tolist()

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

# --- GIỮ NGUYÊN 100% THUẬT TOÁN RA DÀN GỐC V9.4.7 ---
def get_filtered_power_score_4(new_wire_scores, current_digits):
    check_and_fix_db_structure()
    db = st.session_state['db']
    
    mapping_1d = {str(i).zfill(2): 0 for i in range(100)}
    coords_1 = np.argwhere(new_wire_scores == 1)
    for r, c in coords_1:
        num = current_digits[r] + current_digits[c]
        mapping_1d[num] += 1

    gan_blacklist = [n for n, days in db['gan_tracker'].items() if days > 12]
    bet_blacklist = [n for n, streak in db['bet_tracker'].items() if streak >= 2]
    bottom_20 = [item[0] for item in sorted(db['total_hits'].items(), key=lambda x: (x[1], int(x[0])))[:20]]
    
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

def process_matrix(current_digits, current_loto, gdb_val, raw_full_list):
    check_and_fix_db_structure()
    db = st.session_state['db']
    update_statistics(current_loto)
    
    old_scores = np.array(db['wire_scores'], dtype=int)
    old_digits = db['last_digits']
    old_core_4 = db.get('core_four', [])
    old_bt = db.get('bach_thu', "")
    old_st = db.get('song_thu', "")
    old_l3c = db.get('loto_3c', [])
    
    new_wire_scores = np.zeros((TOTAL_POS, TOTAL_POS), dtype=int)
    break_arr = np.array(db["break_matrix"], dtype=int)
    max_reached_arr = np.array(db["max_reached_matrix"], dtype=int)
    over_1d_arr = np.array(db["over_1d_matrix"], dtype=int)
    cang_lo_arr = np.array(db["cang_lo_matrix"], dtype=int)
    
    # --- ĐỐI SOÁT LỊCH SỬ KỲ TRƯỚC PHÂN TẦNG ---
    hit_report = {"STT": len(db['history']) + 1, "GĐB": gdb_val, "Bạch Thủ": old_bt if old_bt else "Trống"}
    current_3c_real = [s[-3:] for s in raw_full_list if len(s) >= 3]
    
    # 1. Đối soát Song Thủ độc lập
    if old_st and " - " in old_st:
        st_list = [n.strip() for n in old_st.split("-")]
        found_st = [n for n in st_list if n in current_loto]
        count_st = sum([current_loto.count(n) for n in found_st])
        hit_report["Song Thủ"] = f"🎯 Win ST ({count_st}nh)" if count_st >= 1 else "❌"
    else:
        hit_report["Song Thủ"] = "Trống"
        
    # 2. Đối soát 3 Càng tự động
    win_3c_flag = False
    if old_l3c:
        predicted_3c_nums = []
        for pair in old_l3c:
            for part in pair.split("-"):
                predicted_3c_nums.append(part.strip())
        for num_3c in predicted_3c_nums:
            if num_3c in current_3c_real:
                win_3c_flag = True
                break
    hit_report["3 Càng"] = "👑 Win3Cang" if win_3c_flag else "❌"
    
    # 3. Đối soát dàn 2 số tổng quát
    if old_core_4:
        old_tam_thu = old_core_4[:3]
        found_3 = [n for n in old_tam_thu if n in current_loto]
        count_3 = sum([current_loto.count(n) for n in found_3])
        found_4 = [n for n in old_core_4 if n in current_loto]
        count_4 = sum([current_loto.count(n) for n in found_4])
        
        hit_report["Dàn 3q"] = f"{count_3} ({','.join(found_3) if found_3 else '0'})"
        hit_report["Dàn 4q"] = f"{count_4} ({','.join(found_4) if found_4 else '0'})"
        
        if old_bt and old_bt in current_loto: hit_report["Result"] = "🔥 Win BT 🔥"
        elif count_3 >= 1 or gdb_val in old_tam_thu: hit_report["Result"] = "🎯 Win Tam Thủ"
        elif count_4 >= 1: hit_report["Result"] = "✅ Ăn Lót"
        else: hit_report["Result"] = "❌ Loss"

    # Tích lũy ma trận bộ nhớ Càng - Lô vĩnh viễn
    for single_s in raw_full_list:
        if len(single_s) >= 3:
            real_cang = int(single_s[-3])
            real_loto = single_s[-2:]
            idx_loto = int(real_loto)
            if 0 <= idx_loto < 100 and 0 <= real_cang < 10:
                cang_lo_arr[idx_loto][real_cang] += 1

    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                num_past = old_digits[i] + old_digits[j]
                if num_past in current_loto:
                    new_wire_scores[i][j] = old_scores[i][j] + 1
                    if new_wire_scores[i][j] > max_reached_arr[i][j]: max_reached_arr[i][j] = new_wire_scores[i][j]
                    if new_wire_scores[i][j] >= 2: over_1d_arr[i][j] += 1
                else:
                    if old_scores[i][j] >= 1: break_arr[i][j] += 1
                    new_wire_scores[i][j] = 0

    # 🛠️ VÁ LỖI CHÍ MẠNG: Khởi tạo biến new_preds rỗng để tránh NameError vĩnh viễn
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

    db['wire_scores'] = new_wire_scores.tolist()
    db['break_matrix'] = break_arr.tolist()
    db['max_reached_matrix'] = max_reached_arr.tolist()
    db['over_1d_matrix'] = over_1d_arr.tolist()
    db['cang_lo_matrix'] = cang_lo_arr.tolist()
    db['last_digits'] = current_digits
    db['last_loto'] = current_loto
    db['last_predictions'] = new_preds
    
    # Bốc dàn 4 con chuẩn gốc V9.4.7
    calculated_4 = get_filtered_power_score_4(new_wire_scores, current_digits)
    db['core_four'] = calculated_4
    
    # --- 🧠 THUẬT TOÁN ĐỘNG LƯỢNG CHUỖI SDI AI ĐỘC LẬP VÒNG NGOÀI ---
    total_history_count = len(db['history'])
    sdi_map = {str(i).zfill(2): 1.0 for i in range(100)}
    
    if total_history_count >= 4:
        try:
            hist_gdb_1 = str(db['history'][0]['GĐB'])[-2:]
            hist_gdb_2 = str(db['history'][1]['GĐB'])[-2:]
            hist_gdb_3 = str(db['history'][2]['GĐB'])[-2:]
            
            chain_match_counts = {str(i).zfill(2): 0 for i in range(100)}
            total_chain_occurrences = 0
            
            for idx in range(len(db['history']) - 3):
                p_gdb_1 = str(db['history'][idx+1]['GĐB'])[-2:]
                p_gdb_2 = str(db['history'][idx+2]['GĐB'])[-2:]
                p_gdb_3 = str(db['history'][idx+3]['GĐB'])[-2:]
                
                if p_gdb_1 == hist_gdb_1 and p_gdb_2 == hist_gdb_2 and p_gdb_3 == hist_gdb_3:
                    total_chain_occurrences += 1
                    target_num = str(db['history'][idx]['GĐB'])[-2:]
                    if target_num in chain_match_counts:
                        chain_match_counts[target_num] += 1
            
            if total_chain_occurrences > 0:
                for idx_s in range(100):
                    num_str = str(idx_s).zfill(2)
                    p_conditional = chain_match_counts[num_str] / total_chain_occurrences
                    p_base = max(1, db['total_hits'][num_str]) / max(1, sum(db['total_hits'].values()))
                    if p_base > 0 and p_conditional > 0:
                        sdi_map[num_str] = round(p_conditional / p_base, 2)
        except:
            pass

    tam_thu = calculated_4[:3]
    if tam_thu:
        mapping_1d = {str(i).zfill(2): 0 for i in range(100)}
        coords_1 = np.argwhere(new_wire_scores == 1)
        for r, c in coords_1:
            mapping_1d[current_digits[r] + current_digits[c]] += 1
            
        bt_scores = {}
        top_leader_num = tam_thu[0]
        temp_3c_list = []
        
        for num in tam_thu:
            score_ai = 100
            if num == top_leader_num: score_ai += 50.0
            score_ai += sdi_map[num] * 15.0 
            
            wire_coordinates = []
            for r in range(TOTAL_POS):
                for c in range(TOTAL_POS):
                    if current_digits[r] + current_digits[c] == num:
                        score_ai -= break_arr[r][c] * 2.5
                        score_ai += over_1d_arr[r][c] * 3.5
                        if int(new_wire_scores[r][c]) >= 2:
                            wire_coordinates.append((r, c))
            
            if 5 <= mapping_1d.get(num, 0) <= 15: score_ai += 30
            elif mapping_1d.get(num, 0) > 30: score_ai -= 25
            if db['bet_tracker'][num] == 0: score_ai += 20
            elif db['bet_tracker'][num] == 1: score_ai += 25.0
            bt_scores[num] = score_ai
            
            # Tra cứu ma trận bộ nhớ Càng-Lô Twin Shield
            idx_num = int(num)
            cang_scores_ai = {str(k): 0.0 for k in range(10)}
            for c_idx in range(10):
                cang_scores_ai[str(c_idx)] += float(cang_lo_arr[idx_num][c_idx]) * 15.0
            for r_coord, c_coord in wire_coordinates:
                for adj in [r_coord - 1, r_coord + 1, c_coord - 1, c_coord + 1]:
                    if 0 <= adj < TOTAL_POS:
                        cang_scores_ai[current_digits[adj]] += 5.0
                        
            sorted_càng = sorted(cang_scores_ai.items(), key=lambda x: x[1], reverse=True)
            càng_1 = sorted_càng[0][0]
            càng_2 = str((int(càng_1) + 5) % 10)
            temp_3c_list.append(f"{càng_1}{num} - {càng_2}{num}")
            
        db['bach_thu'] = max(bt_scores, key=bt_scores.get)
        db['loto_3c'] = temp_3c_list
        
        # Trích xuất cặp Song Thủ SDI mạnh nhất toàn cục an toàn
        sorted_sdi_global = sorted(sdi_map.items(), key=lambda x: x[1], reverse=True)
        valid_st_candidates = [item[0] for item in sorted_sdi_global if db['gan_tracker'][item[0]] <= 12]
        if len(valid_st_candidates) >= 2:
            db['song_thu'] = f"{valid_st_candidates[0]} - {valid_st_candidates[1]}"
        else:
            db['song_thu'] = " - ".join(calculated_4[:2])
    else:
        db['bach_thu'] = ""
        db['song_thu'] = ""
        db['loto_3c'] = []
        
    db['history'].insert(0, hit_report)

# --- 4. GIAO DIỆN CHÍNH STREAMLIT MOBILE V13.6 ---
st.markdown("<h2 style='text-align: center; color: #E2E8F0; font-weight: bold; font-size: 1.5rem;'>⚡ MATRIX MASTER V13.6</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 💾 DATA SYSTEM")
    uploaded_file = st.file_uploader("Nạp JSON", type=['json'])
    if uploaded_file and st.button("📥 PHỤC HỒI MA TRẬN"):
        st.session_state['db'] = json.load(uploaded_file)
        check_and_fix_db_structure()
        st.rerun()
    if st.session_state['db']['last_digits']:
        st.download_button("💾 XUẤT FILE JSON", json.dumps(st.session_state['db']), "matrix_v136.json")
    
    st.divider()
    st.markdown("### 📸 OCR CAMERA")
    uploaded_img = st.file_uploader("Chọn ảnh kết quả", type=['jpg', 'png', 'jpeg'])
    if uploaded_img and st.button("QUÉT ẢNH"):
        reader = load_ocr()
        res = reader.readtext(np.array(Image.open(uploaded_img)), detail=0)
        nums = [n for n in res if n.isdigit() and 2 <= len(n) <= 5]
        if nums: 
            st.session_state['raw_input'] = ", ".join(nums)
            st.session_state['gdb_ocr'] = nums[0][-2:]
        st.rerun()

    st.session_state['raw_input'] = st.text_area("Bảng kết quả thô:", value=st.session_state.get('raw_input', ""), height=100)
    gdb_val = st.text_input("Đặc biệt (2 số):", value=st.session_state.get('gdb_ocr', ""), max_chars=2)

    if st.button("🔥 CHẠY SNIPER MOBILE", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len("".join(raw)) >= TOTAL_POS:
            process_matrix("".join(raw)[:TOTAL_POS], [s[-2:] for s in raw[:27]], gdb_val, raw)
            st.rerun()
    st.button("🚨 XÓA BẢNG TẠM", on_click=lambda: st.session_state.clear())

# --- BẢNG DỰ ĐOÁN KỲ TIẾP THEO ---
st.markdown("<h3><font color='#FF1E27'><b>🎯 TỌA ĐỘ PHÁT LỰC</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #FF1E27; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

c4 = st.session_state['db'].get('core_four', [])
bt = st.session_state['db'].get('bach_thu', "")
st_sdi = st.session_state['db'].get('song_thu', "")
l3c = st.session_state['db'].get('loto_3c', [])

if c4:
    if bt:
        st.markdown(f"""<div class="mobile-box-bt"><span class="title-text-bt">👑 BẠCH THỦ ASSASSIN AI</span><br><p class="mobile-text-bt"><b>{bt}</b></p></div>""", unsafe_allow_html=True)
    if st_sdi:
        st.markdown(f"""<div class="mobile-box-st"><span class="title-text-st">⚔️ SONG THỦ ĐỘNG LỰC SDI</span><br><p class="mobile-text-st"><b>{st_sdi}</b></p></div>""", unsafe_allow_html=True)
    tam_thu_str = ' - '.join(c4[:3])
    st.markdown(f"""<div class="mobile-box-3"><span class="title-text-3">🔥 TAM THỦ CHỦ LỰC GỐC</span><br><p class="mobile-text-3"><b>{tam_thu_str}</b></p></div>""", unsafe_allow_html=True)
    if l3c and len(l3c) == 3:
        st.markdown(f"""
            <div class="mobile-box-3c">
                <span class="title-text-3c">🔮 3 CÀNG MEMORY TWIN SHIELD</span><br>
                <p class="mobile-text-3c">
                    <b>Lo1: {l3c[0]}</b><br>
                    <b>Lo2: {l3c[1]}</b><br>
                    <b>Lo3: {l3c[2]}</b>
                </p>
            </div>
            """, unsafe_allow_html=True)
    tu_thu_str = ' - '.join(c4)
    st.markdown(f"""<div class="mobile-box-4"><span class="title-text-4">🎯 TỨ THỦ CHIẾN THUẬT</span><br><p class="mobile-text-4"><b>{tu_thu_str}</b></p></div>""", unsafe_allow_html=True)
else:
    st.info("Đang chờ tích lũy xung nhịp kỳ kế tiếp.")

check_and_fix_db_structure()
with st.expander("🚫 Hệ thống chặn số tự động"):
    gan_list = [n for n, days in st.session_state['db']['gan_tracker'].items() if days > 12]
    bet_list = [n for n, streak in st.session_state['db']['bet_tracker'].items() if streak >= 2]
    st.write(f"**Lô Gan (>12 ngày):** {', '.join(gan_list) if gan_list else 'Trống'}")
    st.write(f"**Lô Bệt (>=2 ngày):** {', '.join(bet_list) if bet_list else 'Trống'}")

# --- BẢNG LỊCH SỬ ĐỐI SOÁT WIN/LOSS HAI TRỤC ---
st.markdown("<h3><font color='#FF1E27'><b>📋 LỊCH SỬ ĐỐI SOÁT KẾT QUẢ</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #FF1E27; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

if st.session_state['db']['history']:
    df_hist = pd.DataFrame(st.session_state['db']['history']).fillna("0")
    cols = list(df_hist.columns)
    important = ["Result", "Bạch Thủ", "Song Thủ", "3 Càng", "Dàn 3q", "Dàn 4q", "GĐB", "STT"]
    for col in reversed(important):
        if col in cols: cols.insert(0, cols.pop(cols.index(col)))
    
    if "Result" in df_hist.columns:
        st.dataframe(
            df_hist[cols].style.map(
                lambda x: 'color: #FF1E27; font-weight: 900' if x == "🔥 Win BT 🔥" else 
                          ('color: #F59E0B; font-weight: bold' if x == "🎯 Win Tam Thủ" else 
                          ('color: #10B981; font-weight: bold' if x == "✅ Ăn Lót" else 
                          ('color: #718096' if x == "❌ Loss" else ''))),
                subset=["Result"]
            ).map(
                lambda x: 'color: #A855F7; font-weight: 900' if "🎯 Win ST" in str(x) else 'color: #4A5568',
                subset=["Song Thủ"]
            ).map(
                lambda x: 'color: #10B981; font-weight: 900' if x == "👑 Win3Cang" else 'color: #4A5568',
                subset=["3 Càng"]
            ),
            use_container_width=True, height=550
        )
else:
    st.dataframe(pd.DataFrame(columns=["Result", "Bạch Thủ", "Song Thủ", "3 Càng", "Dàn 3q", "Dàn 4q", "GĐB", "STT"]), use_container_width=True, height=150)

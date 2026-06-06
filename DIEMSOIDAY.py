import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH HỆ THỐNG MÀN HÌNH ---
st.set_page_config(page_title="Matrix V21.0 - Turbo Combinatorial", layout="wide")

# Custom CSS chuẩn Mobile: Tiêu đề dòng TO/ĐẬM - Số THU NHỎ vừa vặn, sang trọng
st.markdown("""
    <style>
    .main { background-color: #0A0D14; padding: 10px; }
    .stButton>button { width: 100%; border-radius: 6px; height: 3.5em; background-color: #161B26; color: #F0F4F8; border: 1px solid #2D3748; font-weight: bold; }
    .stButton>button:hover { border-color: #FFD700; color: #FFD700; }
    
    .mobile-box-bt { background-color: #05070B; padding: 10px 5px; border-radius: 12px; text-align: center; border: 3px solid #EF4444; margin-bottom: 12px; }
    .mobile-box-st { background-color: #04060A; padding: 10px 5px; border-radius: 12px; text-align: center; border: 3px solid #A855F7; margin-bottom: 12px; }
    .mobile-box-3c { background-color: #020406; padding: 10px 5px; border-radius: 12px; text-align: center; border: 3px solid #10B981; margin-bottom: 12px; }
    
    .title-text-bt { color: #FF5555 !important; font-size: 16px !important; font-weight: 900 !important; font-family: sans-serif; }
    .title-text-st { color: #A855F7 !important; font-size: 16px !important; font-weight: 900 !important; font-family: sans-serif; }
    .title-text-3c { color: #10B981 !important; font-size: 15px !important; font-weight: 900 !important; font-family: sans-serif; }
    
    .mobile-text-bt { color: #FF1E27 !important; font-size: 9.5vw !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 2px; margin: 0; line-height: 1.1; white-space: nowrap !important; }
    .mobile-text-st { color: #A855F7 !important; font-size: 8.0vw !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 1px; margin: 0; line-height: 1.1; white-space: nowrap !important; }
    .mobile-text-3c { color: #10B981 !important; font-size: 4.8vw !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 1px; margin: 0; line-height: 1.4; }
    </style>
    """, unsafe_allow_html=True)

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "loto_2s_memory": {},       # Lưu trữ thực tế dạng băm khóa chéo (27x27x27)
        "cang_3s_memory": {},       # Lưu trữ thực tế dạng băm khóa chéo (23x23x23)
        "history": [],              # Nhật ký đối soát
        "last_predictions": {
            "bach_thu": "",
            "song_thu": "",
            "loto_3c": []
        }
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

def check_and_fix_db_structure():
    db = st.session_state['db']
    if "loto_2s_memory" not in db: db["loto_2s_memory"] = {}
    if "cang_3s_memory" not in db: db["cang_3s_memory"] = {}
    if "history" not in db: db["history"] = []
    if "last_predictions" not in db: db["last_predictions"] = {"bach_thu": "", "song_thu": "", "loto_3c": []}

def process_matrix(gdb_val, raw_full_list):
    check_and_fix_db_structure()
    db = st.session_state['db']
    
    # 1. Trích xuất mảng 2 con loto (27 giải) và 3 con 3 càng (23 giải tinh khiết)
    current_loto_2s = [s[-2:] for s in raw_full_list[:27] if len(s) >= 2]
    current_cang_3s = [s[-3:] for s in raw_full_list if len(s) >= 3][:23]

    old_preds = db.get("last_predictions", {"bach_thu": "", "song_thu": "", "loto_3c": []})
    old_bt = old_preds.get("bach_thu", "")
    old_st = old_preds.get("song_thu", "")
    old_l3c = old_preds.get("loto_3c", [])

    total_history_count = len(db['history'])
    stt_kỳ = total_history_count + 1

    # --- 📋 KHỐI ĐỐI SOÁT WIN/LOSS SẠCH SẼ ---
    hit_report = {"STT": stt_kỳ, "GĐB": gdb_val}
    
    if total_history_count < 3:
        hit_report["Bạch Thủ"] = "Đang tích nhịp"
        hit_report["Song Thủ"] = "Đang tích nhịp"
        hit_report["3 Càng"] = "Đang tích nhịp"
        hit_report["Result"] = "⚙️ Khởi tạo"
    else:
        # Đối soát Bạch Thủ
        hit_report["Bạch Thủ"] = f"👑 {old_bt} (Win)" if old_bt in current_loto_2s else f"{old_bt} (❌)"
        # Đối soát Song Thủ
        if old_st and " - " in old_st:
            st_parts = [n.strip() for n in old_st.split("-")]
            found_st = [n for n in st_parts if n in current_loto_2s]
            hit_report["Song Thủ"] = f"👑 {','.join(found_st)} (Win)" if found_st else f"{old_st} (❌)"
        else:
            hit_report["Song Thủ"] = "Trống"
        # Đối soát 3 Càng đích danh
        win_3c_found = [n for n in old_l3c if n in current_cang_3s]
        hit_report["3 Càng"] = f"👑 {','.join(win_3c_found)} (Win)" if win_3c_found else f"{'-'.join(old_l3c) if old_l3c else 'Trống'} (❌)"
        
        # Result tổng hợp hiển thị màu sắc lịch sử
        if old_bt and old_bt in current_loto_2s: hit_report["Result"] = "🔥 Win BT 🔥"
        elif old_st and any(n.strip() in current_loto_2s for n in old_st.split("-")): hit_report["Result"] = "🎯 Win Song Thủ"
        elif win_3c_found: hit_report["Result"] = "💎ĐẠI THẮNG 3 CÀNG"
        else: hit_report["Result"] = "❌ Loss"

    # Gắn thẻ dữ liệu thô vào lịch sử để làm bàn đạp tính toán chuỗi tịnh tiến
    hit_report["Saved_Loto_2S"] = current_loto_2s
    hit_report["Saved_Cang_3S"] = current_cang_3s

    # --- 🔄 BỘ NÃO AI DỆT LƯỚI TỔ HỢP MẠNG NHỆN ABC (TÍCH LŨY DATA) ---
    if total_history_count >= 3:
        try:
            list_A_2s = db['history'][2].get("Saved_Loto_2S", [])
            list_B_2s = db['history'][1].get("Saved_Loto_2S", [])
            list_C_2s = db['history'][0].get("Saved_Loto_2S", [])
            
            if list_A_2s and list_B_2s and list_C_2s:
                for a in set(list_A_2s):
                    for b in set(list_B_2s):
                        for c in set(list_C_2s):
                            key_2s = f"{a}_{b}_{c}"
                            if key_2s not in db["loto_2s_memory"]:
                                db["loto_2s_memory"][key_2s] = {str(i).zfill(2): 0 for i in range(100)}
                            for hit in current_loto_2s:
                                db["loto_2s_memory"][key_2s][hit] += 1
                                
            list_A_3c = db['history'][2].get("Saved_Cang_3S", [])
            list_B_3c = db['history'][1].get("Saved_Cang_3S", [])
            list_C_3c = db['history'][0].get("Saved_Cang_3S", [])
            
            if list_A_3c and list_B_3c and list_C_3c:
                for a in set(list_A_3c):
                    for b in set(list_B_3c):
                        for c in set(list_C_3c):
                            key_3c = f"{a}_{b}_{c}"
                            if key_3c not in db["cang_3s_memory"]:
                                db["cang_3s_memory"][key_3c] = {}
                            for hit in current_cang_3s:
                                db["cang_3s_memory"][key_3c][hit] = db["cang_3s_memory"][key_3c].get(hit, 0) + 1
        except:
            pass

    # Đưa kết quả hiện tại vào đầu hàng danh sách lịch sử
    db['history'].insert(0, hit_report)
    updated_history_count = len(db['history'])

    # --- ⚡ 🎯 THUẬT TOÁN TURBO O(1): TRA CỨU BĂNG TỪ ĐIỂN TỐC ĐỘ ÁNH SÁNG ---
    if updated_history_count < 3:
        db["last_predictions"] = {"bach_thu": "", "song_thu": "", "loto_3c": []}
    else:
        pred_2s_scores = {str(i).zfill(2): 0 for i in range(100)}
        pred_3c_scores = {}
        
        try:
            # Lấy mảng 3 ngày gần nhất làm khuôn mẫu tính dải tương lai
            fut_A_2s = set(db['history'][2].get("Saved_Loto_2S", []))
            fut_B_2s = set(db['history'][1].get("Saved_Loto_2S", []))
            fut_C_2s = set(current_loto_2s)
            
            # KỸ THUẬT TURBO 2 SỐ: Chỉ bốc các khóa giao thoa thực tế tồn tại trong bộ nhớ từ điển, đập tan 3 vòng lặp for mù quáng
            available_keys_2s = db["loto_2s_memory"].keys()
            for key in available_keys_2s:
                parts = key.split("_")
                if parts[0] in fut_A_2s and parts[1] in fut_B_2s and parts[2] in fut_C_2s:
                    for n_key, v_val in db["loto_2s_memory"][key].items():
                        pred_2s_scores[n_key] += v_val
                        
            # KỸ THUẬT TURBO 3 SỐ: Quét băm từ điển tốc độ ánh sáng cho hệ ma trận 3 càng
            fut_A_3c = set(db['history'][2].get("Saved_Cang_3S", []))
            fut_B_3c = set(db['history'][1].get("Saved_Cang_3S", []))
            fut_C_3c = set(current_cang_3s)
            
            available_keys_3c = db["cang_3s_memory"].keys()
            for key in available_keys_3c:
                parts = key.split("_")
                if parts[0] in fut_A_3c and parts[1] in fut_B_3c and parts[2] in fut_C_3c:
                    for n_key, v_val in db["cang_3s_memory"][key].items():
                        pred_3c_scores[n_key] = pred_3c_scores.get(n_key, 0) + v_val
        except:
            pass

        # Phân tầng xếp hạng nhả số dự báo
        sorted_2s = sorted(pred_2s_scores.items(), key=lambda x: x[1], reverse=True)
        calculated_bt = sorted_2s[0][0] if sorted_2s[0][1] > 0 else "00"
        calculated_st = f"{sorted_2s[0][0]} - {sorted_2s[1][0]}" if sorted_2s[0][1] > 0 and sorted_2s[1][1] > 0 else "00 - 01"
        
        calculated_3c_list = []
        if pred_3c_scores:
            sorted_3c = sorted(pred_3c_scores.items(), key=lambda x: x[1], reverse=True)
            calculated_3c_list = [item[0] for item in sorted_3c[:6]]
            
        while len(calculated_3c_list) < 6:
            mock_num = f"{len(calculated_3c_list)}{calculated_bt}"[-3:]
            calculated_3c_list.append(mock_num)
            
        db["last_predictions"] = {
            "bach_thu": calculated_bt,
            "song_thu": calculated_st,
            "loto_3c": calculated_3c_list
        }

# --- 5. GIAO DIỆN STREAMLIT MOBILE V21.0 CHUẨN SẠCH ---
st.markdown("<h2 style='text-align: center; color: #E2E8F0; font-weight: bold; font-size: 1.5rem;'>⚡ MATRIX MASTER V21.0</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 💾 DATA SYSTEM")
    uploaded_file = st.file_uploader("Nạp JSON", type=['json'])
    if uploaded_file and st.button("📥 PHỤC HỒI MA TRẬN"):
        st.session_state['db'] = json.load(uploaded_file)
        check_and_fix_db_structure()
        st.rerun()
    if st.session_state['db'].get('history'):
        st.download_button("💾 XUẤT FILE JSON", json.dumps(st.session_state['db']), "combinatorial_v210.json")
    
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

    st.session_state['raw_input'] = st.text_area("Bảng kết quả thô (Nhập đủ 27 giải):", value=st.session_state.get('raw_input', ""), height=100)
    gdb_val = st.text_input("Đặc biệt (2 số):", value=st.session_state.get('gdb_ocr', ""), max_chars=2)

    if st.button("🔥 CHẠY SNIPER TURBO ABC", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len(raw) >= 27:
            process_matrix(gdb_val, raw)
            st.rerun()
        else:
            st.error("Yêu cầu nhập tối thiểu đủ 27 con số kết quả!")
    st.button("🚨 XÓA BẢNG TẠM", on_click=lambda: st.session_state.clear())

# --- BẢNG HIỂN THỊ DỰ ĐOÁN KỲ TIẾP THEO ---
st.markdown("<h3><font color='#FF1E27'><b>🎯 TỌA ĐỘ PHÁT LỰC</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #FF1E27; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

check_and_fix_db_structure()
hist_len = len(st.session_state['db']['history'])
preds = st.session_state['db'].get("last_predictions", {"bach_thu": "", "song_thu": "", "loto_3c": []})

if hist_len < 3:
    st.warning(f"⚙️ HỆ THỐNG ĐANG TRONG GIAI ĐOẠN KHỞI TẠO MA TRẬN ({hist_len}/3 kỳ). Vui lòng tiếp tục nạp dữ liệu thô để kích hoạt bộ não tổ hợp ABC!")
else:
    bt_num = preds.get("bach_thu", "")
    st_num = preds.get("song_thu", "")
    l3c_list = preds.get("loto_3c", [])
    
    st.markdown(f"""<div class="mobile-box-bt"><span class="title-text-bt">👑 BẠCH THỦ ĐỘC TÔN (2 SỐ)</span><br><p class="mobile-text-bt"><b>{bt_num}</b></p></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="mobile-box-st"><span class="title-text-st">⚔️ SONG THỦ CHIẾN THUẬT (2 SỐ)</span><br><p class="mobile-text-st"><b>{st_num}</b></p></div>""", unsafe_allow_html=True)
    if l3c_list and len(l3c_list) == 6:
        st.markdown(f"""
            <div class="mobile-box-3c">
                <span class="title-text-3c">🔮 6 CON 3 CÀNG MATRIX SNIPER</span><br>
                <p class="mobile-text-3c">
                    <b>{l3c_list[0]} - {l3c_list[1]} - {l3c_list[2]}</b><br>
                    <b>{l3c_list[3]} - {l3c_list[4]} - {l3c_list[5]}</b>
                </p>
            </div>
            """, unsafe_allow_html=True)

# --- BẢNG LỊCH SỬ ĐỐI SOÁT WIN/LOSS TINH GỌN ---
st.markdown("<h3><font color='#FF1E27'><b>📋 LỊCH SỬ ĐỐI SOÁT KẾT QUẢ</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #FF1E27; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

if st.session_state['db']['history']:
    df_display = pd.DataFrame(st.session_state['db']['history'])
    display_cols = [c for c in ["Result", "Bạch Thủ", "Song Thủ", "3 Càng", "GĐB", "STT"] if c in df_display.columns]
    
    if "Result" in df_display.columns:
        st.dataframe(
            df_display[display_cols].style.map(
                lambda x: 'color: #FF1E27; font-weight: 900' if x == "🔥 Win BT 🔥" else 
                          ('color: #A855F7; font-weight: bold' if x == "🎯 Win Song Thủ" else 
                          ('color: #10B981; font-weight: bold' if x == "💎ĐẠI THẮNG 3 CÀNG" else 
                          ('color: #718096' if x == "❌ Loss" else ''))),
                subset=["Result"]
            ),
            use_container_width=True, height=550
        )
else:
    st.dataframe(pd.DataFrame(columns=["Result", "Bạch Thủ", "Song Thủ", "3 Càng", "GĐB", "STT"]), use_container_width=True, height=150)

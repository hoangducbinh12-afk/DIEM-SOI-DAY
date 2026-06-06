import streamlit as st
import pandas as pd
import json
import numpy as np
import easyocr
from PIL import Image

# --- 1. CẤU HÌNH HỆ THỐNG MÀN HÌNH ---
st.set_page_config(page_title="Matrix V20.0 - Combinatorial Master", layout="wide")

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
        "loto_2s_memory": {},       # Ma trận tổ hợp chéo 2 số (27 x 27 x 27)
        "cang_3s_memory": {},       # Ma trận tổ hợp chéo 3 số (23 x 23 x 23)
        "history": [],              # Nhật ký lưu trữ đối soát kết quả
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
    
    # Chuẩn hóa tập 27 con lô thô (lấy 2 số cuối)
    current_loto_2s = [s[-2:] for s in raw_full_list[:27] if len(s) >= 2]
    # Chuẩn hóa tập 23 con 3 càng tinh khiết (bỏ 4 giải 7 cuối bảng)
    current_cang_3s = [s[-3:] for s in raw_full_list if len(s) >= 3 and raw_full_list.index(single_s) < 23] if len(raw_full_list) >= 23 else [s[-3:] for s in raw_full_list if len(s) >= 3]
    # Sửa lỗi lấy chỉ số chuẩn xác của 23 giải đầu bảng (loại trừ giải 7 có độ dài < 3 chữ số)
    current_cang_3s = [s[-3:] for s in raw_full_list if len(s) >= 3][:23]

    old_preds = db.get("last_predictions", {"bach_thu": "", "song_thu": "", "loto_3c": []})
    old_bt = old_preds.get("bach_thu", "")
    old_st = old_preds.get("song_thu", "")
    old_l3c = old_preds.get("loto_3c", [])

    total_history_count = len(db['history'])
    stt_kỳ = total_history_count + 1

    # --- 📋 KHỐI ĐỐI SOÁT KẾT QUẢ WIN / LOSS (TỪ KỲ THỨ 4 TRỞ ĐI MỚI CHẠY) ---
    hit_report = {"STT": stt_kỳ, "GĐB": gdb_val}
    
    if total_history_count < 3:
        hit_report["Bạch Thủ"] = "Đang tích nhịp"
        hit_report["Song Thủ"] = "Đang tích nhịp"
        hit_report["3 Càng"] = "Đang tích nhịp"
        hit_report["Result"] = "⚙️ Khởi tạo"
    else:
        # Đối soát Bạch Thủ
        hit_report["Bạch Thủ"] = f"{old_bt} (❌)" if old_bt else "Trống"
        if old_bt and old_bt in current_loto_2s:
            hit_report["Bạch Thủ"] = f"👑 {old_bt} (Win)"
            
        # Đối soát Song Thủ
        if old_st and " - " in old_st:
            st_parts = [n.strip() for n in old_st.split("-")]
            found_st = [n for n in st_parts if n in current_loto_2s]
            if len(found_st) > 0:
                hit_report["Song Thủ"] = f"👑 {','.join(found_st)} (Win)"
            else:
                hit_report["Song Thủ"] = f"{old_st} (❌)"
        else:
            hit_report["Song Thủ"] = "Trống"
            
        # Đối soát Dàn 6 con 3 Càng đích danh
        win_3c_found = [num_3c for num_3c in old_l3c if num_3c in current_cang_3s]
        if len(win_3c_found) > 0:
            hit_report["3 Càng"] = f"👑 {','.join(win_3c_found)} (Win)"
        else:
            hit_report["3 Càng"] = f"{'-'.join(old_l3c) if old_l3c else 'Trống'} (❌)"
            
        # Trả trạng thái Result tổng quát
        if old_bt and old_bt in current_loto_2s:
            hit_report["Result"] = "🔥 Win BT 🔥"
        elif old_st and any(n.strip() in current_loto_2s for n in old_st.split("-")):
            hit_report["Result"] = "🎯 Win Song Thủ"
        elif len(win_3c_found) > 0:
            hit_report["Result"] = "💎ĐẠI THẮNG 3 CÀNG"
        else:
            hit_report["Result"] = "❌ Loss"

    # Lưu mảng thô động phục vụ dệt lưới
    hit_report["Saved_Loto_2S"] = current_loto_2s
    hit_report["Saved_Cang_3S"] = current_cang_3s

    # --- 🔄 BỘ NÃO AI DỆT LƯỚI TỔ HỢP MẠNG NHỆN (TÍCH LŨY DATA) ---
    if total_history_count >= 3:
        try:
            # 1. Học tổ hợp chéo 2 số (27 x 27 x 27)
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
                                
            # 2. Học tổ hợp chéo 3 số đích danh (23 x 23 x 23)
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

    # --- 🎯 PHẦN AI QUÉT KHÓA TỔ HỢP ĐƯA RA DỰ ĐOÁN CHO KỲ TIẾP THEO ---
    # Đẩy báo cáo vào lịch sử trước để làm bàn đạp cho chuỗi chuyển tiếp mới
    db['history'].insert(0, hit_report)
    updated_history_count = len(db['history'])

    if updated_history_count < 3:
        # Thời kỳ khởi tạo 3 ngày đầu -> Khóa predictions
        db["last_predictions"] = {"bach_thu": "", "song_thu": "", "loto_3c": []}
    else:
        # KÍCH HOẠT KỲ THỨ 4: Tính toán dải số động cho tương lai
        pred_2s_scores = {str(i).zfill(2): 0 for i in range(100)}
        pred_3c_scores = {}
        
        try:
            # Tra cứu khóa tổ hợp 2 số cho tương lai dựa trên 3 ngày gần nhất (kể cả ngày vừa nạp)
            fut_A_2s = db['history'][2].get("Saved_Loto_2S", [])
            fut_B_2s = db['history'][1].get("Saved_Loto_2S", [])
            fut_C_2s = current_loto_2s
            
            for a in set(fut_A_2s):
                for b in set(fut_B_2s):
                    for c in set(fut_C_2s):
                        f_key_2s = f"{a}_{b}_{c}"
                        if f_key_2s in db["loto_2s_memory"]:
                            for n_key, v_val in db["loto_2s_memory"][f_key_2s].items():
                                pred_2s_scores[n_key] += v_val
                                
            # Tra cứu khóa tổ hợp 3 số cho tương lai dựa trên 3 ngày gần nhất
            fut_A_3c = db['history'][2].get("Saved_Cang_3S", [])
            fut_B_3c = db['history'][1].get("Saved_Cang_3S", [])
            fut_C_3c = current_cang_3s
            
            for a in set(fut_A_3c):
                for b in set(fut_B_3c):
                    for c in set(fut_C_3c):
                        f_key_3c = f"{a}_{b}_{c}"
                        if f_key_3c in db["cang_3s_memory"]:
                            for n_key, v_val in db["cang_3s_memory"][f_key_3c].items():
                                pred_3c_scores[n_key] = pred_3c_scores.get(n_key, 0) + v_val
        except:
            pass

        # 1. Nhặt Bạch Thủ (Thằng nổ nhiều nhất sau lưới tổ hợp 2 số)
        sorted_2s = sorted(pred_2s_scores.items(), key=lambda x: x[1], reverse=True)
        calculated_bt = sorted_2s[0][0] if sorted_2s[0][1] > 0 else "00"
        
        # 2. Nhặt Song Thủ (Cặp đôi nổ bạt mạng nhiều nhất sau tổ hợp)
        calculated_st = f"{sorted_2s[0][0]} - {sorted_2s[1][0]}" if sorted_2s[0][1] > 0 and sorted_2s[1][1] > 0 else "00 - 01"
        
        # 3. Nhặt TOP 6 CON 3 CÀNG ĐÍCH DANH (Quét tự do từ tổ hợp 23 giải)
        calculated_3c_list = []
        if pred_3c_scores:
            sorted_3c = sorted(pred_3c_scores.items(), key=lambda x: x[1], reverse=True)
            calculated_3c_list = [item[0] for item in sorted_3c[:6]]
            
        # Nếu chưa đủ nhịp nổ trùng khớp tổ hợp, AI nhặt ngẫu biến bọc lót theo càng phổ thông
        while len(calculated_3c_list) < 6:
            mock_num = f"{len(calculated_3c_list)}{calculated_bt}"[-3:]
            calculated_3c_list.append(mock_num)
            
        # Đồng bộ vào bộ nhớ predictions để dành đối soát cho ngày mai
        db["last_predictions"] = {
            "bach_thu": calculated_bt,
            "song_thu": calculated_st,
            "loto_3c": calculated_3c_list
        }

# --- 5. GIAO DIỆN CHÍNH STREAMLIT MOBILE V20.0 ---
st.markdown("<h2 style='text-align: center; color: #E2E8F0; font-weight: bold; font-size: 1.5rem;'>⚡ MATRIX MASTER V20.0</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 💾 DATA SYSTEM")
    uploaded_file = st.file_uploader("Nạp JSON", type=['json'])
    if uploaded_file and st.button("📥 PHỤC HỒI MA TRẬN"):
        st.session_state['db'] = json.load(uploaded_file)
        check_and_fix_db_structure()
        st.rerun()
    if st.session_state['db'].get('history'):
        st.download_button("💾 XUẤT FILE JSON", json.dumps(st.session_state['db']), "combinatorial_v200.json")
    
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

    if st.button("🔥 CHẠY SNIPER TỔ HỢP ABC", type="primary"):
        raw = [x.strip() for x in st.session_state['raw_input'].replace(",", " ").split() if x]
        if len(raw) >= 27:
            process_matrix(gdb_val, raw)
            st.rerun()
        else:
            st.error("Yêu cầu nhập tối thiểu đủ 27 con số kết quả!")
    st.button("🚨 XÓA BẢNG TẠM", on_click=lambda: st.session_state.clear())

# --- BẢNG HIỂN THỊ KẾT QUẢ DỰ ĐOÁN KỲ TIẾP THEO ---
st.markdown("<h3><font color='#FF1E27'><b>🎯 TỌA ĐỘ PHÁT LỰC</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #FF1E27; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

check_and_fix_db_structure()
hist_len = len(st.session_state['db']['history'])
preds = st.session_state['db'].get("last_predictions", {"bach_thu": "", "song_thu": "", "loto_3c": []})

if hist_len < 3:
    st.warning(f"⚙️ HỆ THỐNG ĐANG TRONG GIAI ĐOẠN KHỞI TẠO MA TRẬN ({hist_len}/3 kỳ). Vui lòng tiếp tục nhập dữ liệu thô để kích hoạt bộ não tổ hợp ABC!")
else:
    bt_num = preds.get("bach_thu", "")
    st_num = preds.get("song_thu", "")
    l3c_list = preds.get("loto_3c", [])
    
    # 1. Hộp Bạch Thủ Độc Tôn 2 Số
    st.markdown(f"""<div class="mobile-box-bt"><span class="title-text-bt">👑 BẠCH THỦ ĐỘC TÔN (2 SỐ)</span><br><p class="mobile-text-bt"><b>{bt_num}</b></p></div>""", unsafe_allow_html=True)
    # 2. Hộp Song Thủ Chiến Thuật 2 Số
    st.markdown(f"""<div class="mobile-box-st"><span class="title-text-st">⚔️ SONG THỦ CHIẾN THUẬT (2 SỐ)</span><br><p class="mobile-text-st"><b>{st_num}</b></p></div>""", unsafe_allow_html=True)
    # 3. Hộp Dàn 6 Con 3 Càng Matrix Sniper
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
    # Format hiển thị loại trừ dải list lưu trữ thô ẩn để bảng sạch sẽ
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

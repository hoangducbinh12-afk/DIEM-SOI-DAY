import streamlit as st
import cv2
import numpy as np
import easyocr
from PIL import Image

# Khởi tạo máy quét EasyOCR (chọn tiếng Anh/Số để quét nhanh)
reader = easyocr.Reader(['en'])

def scan_image(image):
    # Chuyển đổi ảnh từ PIL sang OpenCV format
    img_array = np.array(image.convert('RGB'))
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Tiền xử lý ảnh để tăng độ chính xác
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    # Tăng độ tương phản (Thresholding)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    # Quét văn bản
    results = reader.readtext(thresh, detail=0)
    
    # Lọc ra những chuỗi chỉ có số và có độ dài phù hợp (2, 3, 5 số)
    clean_numbers = []
    for item in results:
        # Loại bỏ các ký tự lạ, chỉ giữ lại số
        num_only = "".join(filter(str.isdigit, item))
        if len(num_only) in [2, 3, 4, 5]:
            clean_numbers.append(num_only)
            
    return clean_numbers

# --- GIAO DIỆN STREAMLIT BỔ SUNG ---
def main():
    st.sidebar.header("📷 QUÉT BẢNG KẾT QUẢ")
    uploaded_file = st.sidebar.file_uploader("Chọn ảnh bảng kết quả...", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.sidebar.image(image, caption='Ảnh đã tải lên', use_column_width=True)
        
        if st.sidebar.button("BẮT ĐẦU QUÉT ẢNH"):
            with st.spinner('Hệ thống đang đọc dữ liệu từ ảnh...'):
                scanned_data = scan_image(image)
                
                if scanned_data:
                    st.sidebar.success(f"Đã tìm thấy {len(scanned_data)} cụm số!")
                    # Đổ dữ liệu quét được vào ô text area để người dùng kiểm tra lại
                    st.session_state['raw_data'] = ", ".join(scanned_data)
                else:
                    st.sidebar.error("Không đọc được số nào. Hãy thử ảnh rõ nét hơn!")

    # Hiển thị lại dữ liệu trong ô nhập liệu
    raw_input = st.sidebar.text_area("Dữ liệu sau quét (Mày có thể sửa tay):", 
                                    value=st.session_state.get('raw_data', ""))
    
    # ... (Các phần logic hiển thị 27 giải và 107 Bit bên dưới giữ nguyên)

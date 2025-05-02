import streamlit as st
import cv2
import numpy as np
from PIL import Image
import os
from streamlit_drawable_canvas import st_canvas
from glob import glob

def normalize_image(image):
    """이미지를 원본 비율을 유지하면서 긴 쪽을 640으로 맞춤"""
    if image.width > image.height:
        new_width = 640
        new_height = int(image.height * (640 / image.width))
    else:
        new_height = 640
        new_width = int(image.width * (640 / image.height))
    
    resized_img = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return resized_img

def preprocess_for_layout(img_np):
    # 그레이스케일 변환
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    # Canny Edge
    edges = cv2.Canny(gray, 80, 200)
    # 형태학적 팽창/침식으로 작은 윤곽선(텍스트 등) 제거
    kernel = np.ones((7, 7), np.uint8)  # 블록 크기 조정 가능
    morph = cv2.dilate(edges, kernel, iterations=1)
    morph = cv2.erode(morph, kernel, iterations=2)
    return morph

def main():
    """
    메인 애플리케이션 진입점
    """
    st.title("PPT 레이아웃 ROI 기반 유사 영역 탐색기 (레이아웃 블록 중심)")
    
    # 이미지 업로드
    uploaded_file = st.file_uploader("이미지를 업로드하세요", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        # 이미지 로드 및 정규화
        image = Image.open(uploaded_file)
        normalized_image = normalize_image(image)
        image_np = np.array(normalized_image)
        w, h = normalized_image.size
        
        # 원본 이미지와 정규화된 이미지 표시
        col1, col2 = st.columns(2)
        with col1:
            st.write("원본 이미지")
            st.image(image, use_column_width=True)
        with col2:
            st.write("정규화된 이미지 (긴 쪽 640px)")
            st.image(normalized_image, use_column_width=True)
        
        st.write("마우스로 드래그하여 ROI 영역을 그려주세요.")
        canvas_result = st_canvas(
            fill_color="rgba(0, 255, 0, 0.3)",  # 반투명 녹색
            stroke_width=2,
            stroke_color="#00FF00",
            background_image=normalized_image,
            update_streamlit=True,
            height=h,
            width=w,
            drawing_mode="rect",
            key="canvas",
        )
        
        if canvas_result.json_data is not None and len(canvas_result.json_data["objects"]) > 0:
            obj = canvas_result.json_data["objects"][-1]  # 마지막 그린 사각형
            left = int(obj["left"])
            top = int(obj["top"])
            width_rect = int(obj["width"])
            height_rect = int(obj["height"])
            x1, y1 = left, top
            x2, y2 = left + width_rect, top + height_rect
            st.info(f"선택된 영역: ({x1}, {y1}) ~ ({x2}, {y2})")
            
            if st.button("유사 영역 찾기"):
                # ROI 커널 전처리 (레이아웃 블록만 남기기)
                roi_kernel = image_np[y1:y2, x1:x2]
                roi_kernel_edge = preprocess_for_layout(roi_kernel)
                kernel_h, kernel_w = roi_kernel_edge.shape[:2]
                slide_imgs = sorted(glob(os.path.join("output_images", "*.png")))
                all_results = []
                for slide_path in slide_imgs:
                    slide_img = cv2.imread(slide_path)
                    if slide_img is None or slide_img.shape[0] < kernel_h or slide_img.shape[1] < kernel_w:
                        continue
                    # 슬라이드도 레이아웃 전처리
                    slide_edge = preprocess_for_layout(cv2.cvtColor(slide_img, cv2.COLOR_BGR2RGB))
                    res = cv2.matchTemplate(slide_edge, roi_kernel_edge, cv2.TM_CCOEFF_NORMED)
                    top_idx = np.argmax(res)
                    y, x = np.unravel_index(top_idx, res.shape)
                    score = float(res[y, x])
                    crop = slide_img[y:y+kernel_h, x:x+kernel_w]
                    all_results.append({
                        'slide': os.path.basename(slide_path),
                        'score': score,
                        'crop': crop
                    })
                all_results.sort(key=lambda x: x['score'], reverse=True)
                top3 = all_results[:3]
                st.subheader("유사도 상위 3개 결과 (레이아웃 블록 기반)")
                for idx, item in enumerate(top3, 1):
                    st.markdown(f"**{idx}. {item['slide']} (유사도: {item['score']:.4f})**")
                    st.image(item['crop'], channels="BGR", use_column_width=True)

if __name__ == "__main__":
    main() 
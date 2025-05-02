import cv2
import numpy as np
import os
import json
from glob import glob

# 경로 설정
ROI_INFO_PATH = 'roi/roi_20250502_221642_info.json'
ROI_DIR = 'roi/'
SLIDES_DIR = 'output_images/'
OUTPUT_DIR = 'top_matches/'

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ROI 정보 로드
with open(ROI_INFO_PATH, 'r', encoding='utf-8') as f:
    roi_info = json.load(f)
roi_img_path = os.path.join(ROI_DIR, roi_info['roi_filename'])
x1, y1, x2, y2 = roi_info['x1'], roi_info['y1'], roi_info['x2'], roi_info['y2']

# ROI 커널 생성 (이미지는 이미 640x640 정규화 상태)
roi_img = cv2.imread(roi_img_path)
roi_kernel = roi_img[y1:y2, x1:x2]
kernel_h, kernel_w = roi_kernel.shape[:2]

# 슬라이드 이미지 목록
slide_imgs = sorted(glob(os.path.join(SLIDES_DIR, '*.png')))

all_results = []

for slide_path in slide_imgs:
    slide_img = cv2.imread(slide_path)
    if slide_img is None or slide_img.shape[0] < kernel_h or slide_img.shape[1] < kernel_w:
        continue  # 커널보다 작은 이미지는 스킵

    # 템플릿 매칭 (정규화된 상관계수)
    res = cv2.matchTemplate(slide_img, roi_kernel, cv2.TM_CCOEFF_NORMED)
    # 상위 3개 위치 추출
    top3_idx = np.argpartition(res.flatten(), -3)[-3:]
    top3_idx = top3_idx[np.argsort(res.flatten()[top3_idx])[::-1]]  # 내림차순 정렬

    for idx in top3_idx:
        y, x = np.unravel_index(idx, res.shape)
        score = float(res[y, x])
        coord = {'x1': int(x), 'y1': int(y), 'x2': int(x+kernel_w), 'y2': int(y+kernel_h)}
        crop = slide_img[y:y+kernel_h, x:x+kernel_w]
        all_results.append({
            'slide': os.path.basename(slide_path),
            'score': score,
            'coord': coord,
            'crop': crop,
            'slide_path': slide_path
        })

# 전체에서 유사도 기준 상위 3개만 추출
all_results.sort(key=lambda x: x['score'], reverse=True)
top3 = all_results[:3]

result_json = []
for idx, item in enumerate(top3, 1):
    crop_img = item['crop']
    crop_name = f'{idx}.png'
    crop_path = os.path.join(OUTPUT_DIR, crop_name)
    cv2.imwrite(crop_path, crop_img)
    result_json.append({
        'slide': item['slide'],
        'score': item['score'],
        'coord': item['coord'],
        'crop_img': crop_name
    })

# 결과 json 저장
with open(os.path.join(OUTPUT_DIR, 'result.json'), 'w', encoding='utf-8') as f:
    json.dump(result_json, f, ensure_ascii=False, indent=2)

print('완료! top_matches 폴더에서 결과를 확인하세요.') 